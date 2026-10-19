
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = ROOT / "outputs" / "causal_analysis_dataset.csv"
OUTPUT_FILE = ROOT / "outputs" / "paired_offer_analysis.csv"


def main():
    df = pd.read_csv(INPUT_FILE)

    # Select customers who received both BOGO and discount offers.
    customer_types = df.groupby("person")["offer_type"].nunique()
    paired_ids = customer_types[customer_types == 2].index
    paired = df[df["person"].isin(paired_ids)].copy()

    # Calculate each customer's completion rate for both offer types.
    rates = paired.pivot_table(
        index="person",
        columns="offer_type",
        values="outcome_completed",
        aggfunc="mean",
    ).dropna(subset=["bogo", "discount"])

    rates["difference_discount_minus_bogo"] = (
        rates["discount"] - rates["bogo"]
    )
    rates.to_csv(OUTPUT_FILE)

    print("Paired offer analysis completed.")
    print(f"Customers included: {len(rates):,}")
    print(f"BOGO mean completion rate: {rates['bogo'].mean() * 100:.2f}%")
    print(f"Discount mean completion rate: {rates['discount'].mean() * 100:.2f}%")
    print(
        "Mean within-customer difference: "
        f"{rates['difference_discount_minus_bogo'].mean() * 100:.2f} "
        "percentage points"
    )
    print(f"Saved to: {OUTPUT_FILE}")
    print("Interpretation: descriptive comparison, not a causal estimate.")


if __name__ == "__main__":
    main()
