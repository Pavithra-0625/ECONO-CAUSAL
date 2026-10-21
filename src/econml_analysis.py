
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from econml.dml import SparseLinearDML
from sklearn.model_selection import GroupShuffleSplit

ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = ROOT / "outputs" / "causal_features_dataset.csv"


def main():
    df = pd.read_csv(INPUT_FILE)

    # Retain records whose complete offer window was observed.
    df = df[
        df["full_validity_window_observed"].astype(bool)
    ].copy()

    # Required treatment, outcome, and customer identifier.
    df = df.dropna(
        subset=["person", "treatment_discount", "outcome_completed"]
    ).copy()

    # Demographics are pre-treatment candidate features.
    features = ["age", "income", "gender"]
    X = df[features]
    T = df["treatment_discount"].astype(int).to_numpy()
    Y = df["outcome_completed"].astype(float).to_numpy()
    groups = df["person"].to_numpy()

    # Split by customer so a customer cannot appear in both sets.
    splitter = GroupShuffleSplit(
        n_splits=1, test_size=0.25, random_state=42
    )
    train_idx, test_idx = next(splitter.split(X, Y, groups))

    X_train = X.iloc[train_idx]
    T_train = T[train_idx]
    Y_train = Y[train_idx]

    print("Total records:", len(df))
    print("Unique customers:", df["person"].nunique())
    print("Training records:", len(train_idx))
    print("Test records:", len(test_idx))
    print("Training treatment counts:", np.bincount(T_train))

    # Preprocess numeric and categorical features.
    numeric_pipeline = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
    )
    categorical_pipeline = make_pipeline(
        SimpleImputer(strategy="most_frequent"),
        OneHotEncoder(handle_unknown="ignore"),
    )
    preprocess = ColumnTransformer(
        [
            ("numeric", numeric_pipeline, ["age", "income"]),
            ("categorical", categorical_pipeline, ["gender"]),
        ]
    )

    X_train_processed = preprocess.fit_transform(X_train)

    if len(np.unique(T_train)) != 2:
        raise ValueError(
            "Training split must contain both BOGO and discount records."
        )

    # Use separate nuisance models for outcome and treatment.
    model_y = RandomForestRegressor(
        n_estimators=100, min_samples_leaf=10, random_state=42
    )
    model_t = RandomForestClassifier(
        n_estimators=100, min_samples_leaf=10, random_state=42
    )

    # LinearDML estimates a conditional treatment effect.
    dml = SparseLinearDML(
    model_y=model_y,
    model_t=model_t,
    discrete_treatment=True,
    cv=2,
    random_state=42,
)
    with warnings.catch_warnings():
        warnings.simplefilter("default")
        dml.fit(Y_train, T_train, X=X_train_processed)

    # Estimate effects for the held-out customers.
    X_test_processed = preprocess.transform(X.iloc[test_idx])
    effects = dml.effect(X_test_processed)

    print("\nEconML SparseLinearDML completed.")
    print(
        "Mean estimated treatment effect:",
        round(float(np.mean(effects)), 4),
    )
    print(
        "Median estimated treatment effect:",
        round(float(np.median(effects)), 4),
    )

    # Save exploratory treatment-effect estimates.
    results = pd.DataFrame({
        "estimated_treatment_effect": effects
    })

    results_file = ROOT / "outputs" / "econml_effect_estimates.csv"
    results.to_csv(results_file, index=False)

    print(f"Effect estimates saved to: {results_file}")
    print(
        "Interpretation: exploratory estimate; "
        "not confirmed causal evidence."
    )
if __name__ == "__main__":
    main()
