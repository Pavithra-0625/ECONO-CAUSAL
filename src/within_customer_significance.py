
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest

ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = ROOT / "outputs" / "causal_features_dataset.csv"
OUTPUT_FILE = ROOT / "outputs" / "within_customer_significance.csv"


def main():
    df = pd.read_csv(INPUT_FILE)

    # Keep offers with a fully observed validity window.
    df = df[
        df["full_validity_window_observed"].astype(bool)
    ].copy()

    # Calculate each customer's completion rate by offer type.
    rates = (
        df.groupby(["person", "offer_type"])["outcome_completed"]
        .mean()
        .unstack()
    )

    # Retain customers with both offer types.
    paired = rates.dropna(subset=["bogo", "discount"]).copy()

    paired["difference_pp"] = (
        paired["discount"] - paired["bogo"]
    ) * 100

    discount_higher = int((paired["difference_pp"] > 0).sum())
    bogo_higher = int((paired["difference_pp"] < 0).sum())
    equal = int((paired["difference_pp"] == 0).sum())

    # Sign test excludes ties.
    non_tied = discount_higher + bogo_higher

    print("Customers with both offer types:", len(paired))
    print("Discount completion rate higher:", discount_higher)
    print("BOGO completion rate higher:", bogo_higher)
    print("Equal completion rates:", equal)

    if non_tied == 0:
        print("\nNo non-tied customer comparisons; test not applicable.")
        return

    result = binomtest(
        discount_higher,
        n=non_tied,
        p=0.5,
        alternative="two-sided",
    )

    ci = result.proportion_ci(confidence_level=0.95)

    print("\nPaired sign test:")
    print("Non-tied customers:", non_tied)
    print("Share favoring Discount:", round(discount_higher / non_tied, 4))
    print("95% CI for share:", round(ci.low, 4), "to", round(ci.high, 4))
    print("Two-sided p-value:", f"{result.pvalue:.6g}")

    print(
        "\nInterpretation: this tests the balance of positive and negative "
        "customer-level differences, not a causal effect. Customers' "
        "offer counts, timing, and exposure may differ."
    )

    summary = pd.DataFrame([{
        "customers_with_both_types": len(paired),
        "discount_higher": discount_higher,
        "bogo_higher": bogo_higher,
        "equal": equal,
        "non_tied_customers": non_tied,
        "share_favoring_discount": discount_higher / non_tied,
        "ci_95_lower": ci.low,
        "ci_95_upper": ci.high,
        "p_value": result.pvalue,
    }])

    summary.to_csv(OUTPUT_FILE, index=False)
    print("\nSaved results to:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
