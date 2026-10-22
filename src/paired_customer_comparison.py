
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = ROOT / "outputs" / "causal_features_dataset.csv"
OUTPUT_FILE = ROOT / "outputs" / "paired_customer_comparison.csv"


def main():
    df = pd.read_csv(INPUT_FILE)

    # Keep records with fully observed offer windows.
    df = df[
        df["full_validity_window_observed"].astype(bool)
    ].copy()

    # Find customers who received both BOGO and discount offers.
    offer_types = df.groupby("person")["offer_type"].nunique()
    paired_ids = offer_types[offer_types == 2].index
    paired = df[df["person"].isin(paired_ids)].copy()

    # Calculate each customer's completion rate for each offer type.
    rates = paired.pivot_table(
        index="person",
        columns="offer_type",
        values="outcome_completed",
        aggfunc="mean",
    ).dropna(subset=["bogo", "discount"])

    rates["difference_discount_minus_bogo"] = (
        rates["discount"] - rates["bogo"]
    )

    # Save customer-level results.
    rates.to_csv(OUTPUT_FILE)

    print("Paired customer comparison completed.")
    print("Customers included:", len(rates))

    print(
        "Mean BOGO customer completion rate:",
        f"{rates['bogo'].mean() * 100:.2f}%"
    )
    print(
        "Mean discount customer completion rate:",
        f"{rates['discount'].mean() * 100:.2f}%"
    )
    print(
        "Mean within-customer difference:",
        f"{rates['difference_discount_minus_bogo'].mean() * 100:.2f}",
        "percentage points"
    )
    print(
        "Median within-customer difference:",
        f"{rates['difference_discount_minus_bogo'].median() * 100:.2f}",
        "percentage points"
    )

    print(f"Saved results to: {OUTPUT_FILE}")
    print("Interpretation: descriptive comparison, not causal proof.")


if __name__ == "__main__":
    main()