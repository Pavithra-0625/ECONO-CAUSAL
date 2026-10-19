
"""Initial data checks for EconoCausal."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = ROOT / "outputs" / "customer_offer_dataset.csv"
OUTPUT_FILE = ROOT / "outputs" / "causal_analysis_dataset.csv"


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {INPUT_FILE}. Run the customer-offer script first."
        )

    df = pd.read_csv(INPUT_FILE)

    # Keep only BOGO and discount offer records with complete observation windows.
    df = df[
        df["offer_type"].isin(["bogo", "discount"])
        & df["full_validity_window_observed"].eq(True)
    ].copy()

    # Encode treatment: discount = 1, BOGO = 0.
    df["treatment_discount"] = df["offer_type"].eq("discount").astype(int)

    # Outcome: whether the offer was completed during the observed window.
    df["outcome_completed"] = pd.to_numeric(
        df["completed_within_observed_window"], errors="coerce"
    )

    df = df.dropna(subset=["treatment_discount", "outcome_completed"])

    df.to_csv(OUTPUT_FILE, index=False)

    print("Initial causal analysis dataset created.")
    print(f"Rows: {len(df):,}")
    print(f"Unique customers: {df['person'].nunique():,}")
    print("\nTreatment counts (0=BOGO, 1=discount):")
    print(df["treatment_discount"].value_counts().sort_index().to_string())
    print("\nCompletion rate by treatment (%):")
    print(
        (df.groupby("treatment_discount")["outcome_completed"].mean() * 100)
        .round(2)
        .rename(index={0: "BOGO", 1: "Discount"})
        .to_string()
    )
    print(f"\nSaved to: {OUTPUT_FILE}")
    print(
        "\nNote: These are descriptive comparisons. They are not causal estimates."
    )


if __name__ == "__main__":
    main()
