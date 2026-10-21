
from pathlib import Path
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = ROOT / "outputs" / "causal_features_dataset.csv"


def main():
    df = pd.read_csv(INPUT_FILE)

    df = df[
        df["full_validity_window_observed"].astype(bool)
    ].copy()

    features = ["age", "income", "gender"]
    df = df.dropna(subset=["treatment_discount"]).copy()

    X = df[features]
    treatment = df["treatment_discount"].astype(int)

    numeric_features = ["age", "income"]
    categorical_features = ["gender"]

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
            ("numeric", numeric_pipeline, numeric_features),
            ("categorical", categorical_pipeline, categorical_features),
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
        .round(3)
        .to_string()
    )

    print("\nScores outside common range:")
    low = max(
        df.loc[treatment == 0, "propensity_score"].min(),
        df.loc[treatment == 1, "propensity_score"].min(),
    )
    high = min(
        df.loc[treatment == 0, "propensity_score"].max(),
        df.loc[treatment == 1, "propensity_score"].max(),
    )
    print(f"Common range: {low:.3f} to {high:.3f}")

    if low >= high:
        print("Warning: no common propensity-score range.")
    else:
        outside = (
            (df["propensity_score"] < low)
            | (df["propensity_score"] > high)
        )
        print("Rows outside common range:", int(outside.sum()))

    print(
        "\nNote: This is a diagnostic, not proof of causal validity. "
        "The score model may need refinement."
    )


if __name__ == "__main__":
    main()
