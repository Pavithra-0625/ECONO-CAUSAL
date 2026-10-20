
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

CAUSAL_FILE = ROOT / "outputs" / "causal_analysis_dataset.csv"
PROFILE_FILE = ROOT / "outputs" / "profile_clean.csv"
OUTPUT_FILE = ROOT / "outputs" / "causal_features_dataset.csv"


def main():
    causal = pd.read_csv(CAUSAL_FILE)
    profile = pd.read_csv(PROFILE_FILE)

    # Remove demographic columns already present in the causal dataset.
    demographic_cols = [
        "age",
        "gender",
        "income",
        "became_member_on",
    ]
    causal = causal.drop(
        columns=[c for c in demographic_cols if c in causal.columns]
    )

    # Keep one profile row per customer.
    profile = profile[
        ["id", "age", "gender", "income", "became_member_on"]
    ].copy()

    # Merge customer profiles without changing the number of causal rows.
    merged = causal.merge(
        profile,
        left_on="person",
        right_on="id",
        how="left",
        validate="many_to_one",
    )

    print("Original causal rows:", len(causal))
    print("Merged rows:", len(merged))
    print("Unique customers:", merged["person"].nunique())

    print("\nMissing demographic values:")
    print(
        merged[["age", "gender", "income"]]
        .isna()
        .sum()
        .to_string()
    )

    print("\nTreatment and outcome means:")
    print(
        merged.groupby("offer_type")[
            ["treatment_discount", "outcome_completed"]
        ].mean().to_string()
    )

    merged.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSaved dataset to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
