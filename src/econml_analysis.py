
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = ROOT / "outputs" / "causal_features_dataset.csv"
OUTPUT_FILE = ROOT / "outputs" / "propensity_scores.csv"


def main():
    df = pd.read_csv(INPUT_FILE)

    # Keep offers with a fully observed validity window.
    df = df[
        df["full_validity_window_observed"].astype(bool)
    ].copy()

    # Identify missing customer profiles.
    df["profile_missing"] = df["age"].isna().astype(int)

    features = [
        "age",
        "income",
        "gender",
        "profile_missing",
    ]

    df = df.dropna(subset=["treatment_discount"]).copy()

    X = df[features]
    treatment = df["treatment_discount"].astype(int)

    numeric_pipeline = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
    )

    categorical_pipeline = make_pipeline(
        SimpleImputer(strategy="most_frequent"),
        OneHotEncoder(handle_unknown="ignore"),
    )

    preprocess = ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, ["age", "income"]),
            ("categorical", categorical_pipeline, ["gender"]),
            ("indicator", "passthrough", ["profile_missing"]),
        ]
    )

    model = make_pipeline(
        preprocess,
        LogisticRegression(max_iter=1000),
    )

    model.fit(X, treatment)
    df["propensity_score"] = model.predict_proba(X)[:, 1]

    print("Rows used:", len(df))

    print("\nPropensity-score summary by treatment:")
    print(
        df.groupby("treatment_discount")["propensity_score"]
        .agg(["count", "min", "max", "mean"])
        .round(4)
        .to_string()
    )

    print("\nPropensity-score summary by profile status:")
    print(
        df.groupby("profile_missing")["propensity_score"]
        .agg(["count", "min", "max", "mean"])
        .rename(index={0: "Available", 1: "Missing"})
        .round(4)
        .to_string()
    )

    # Calculate the common propensity-score range.
    low = max(
        df.loc[treatment == 0, "propensity_score"].min(),
        df.loc[treatment == 1, "propensity_score"].min(),
    )

    high = min(
        df.loc[treatment == 0, "propensity_score"].max(),
        df.loc[treatment == 1, "propensity_score"].max(),
    )

    print(f"\nCommon range: {low:.4f} to {high:.4f}")

    if low >= high:
        print("Warning: no common propensity-score range.")
    else:
        outside = (
            (df["propensity_score"] < low)
            | (df["propensity_score"] > high)
        )
        print("Rows outside common range:", int(outside.sum()))

    # Save scores for further validation and visualization.
    df[
        [
            "person",
            "offer_type",
            "treatment_discount",
            "profile_missing",
            "propensity_score",
        ]
    ].to_csv(OUTPUT_FILE, index=False)

    print(f"\nPropensity scores saved to: {OUTPUT_FILE}")
    print("Note: Overlap is a diagnostic, not proof of causal validity.")


if __name__ == "__main__":
    main()
