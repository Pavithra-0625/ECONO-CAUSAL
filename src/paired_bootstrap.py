
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = ROOT / "outputs" / "causal_features_dataset.csv"
OUTPUT_FILE = ROOT / "outputs" / "paired_bootstrap_results.csv"


def main():
    df = pd.read_csv(INPUT_FILE)

    # Keep fully observed offer windows.
    df = df[
        df["full_validity_window_observed"].astype(bool)
    ].copy()

    # Select customers who received both offer types.
    types_per_customer = df.groupby("person")["offer_type"].nunique()
    paired_ids = types_per_customer[types_per_customer == 2].index
    paired = df[df["person"].isin(paired_ids)].copy()

    # Compute one difference per customer.
    rates = paired.pivot_table(
        index="person",
        columns="offer_type",
        values="outcome_completed",
        aggfunc="mean",
    ).dropna(subset=["bogo", "discount"])

    differences = (
        rates["discount"] - rates["bogo"]
    ).to_numpy()

    # Bootstrap customers, keeping each customer's offers together.
    rng = np.random.default_rng(42)
    n_customers = len(differences)
    n_bootstrap = 2000

    bootstrap_means = np.empty(n_bootstrap)

    for i in range(n_bootstrap):
        sample = rng.choice(
            differences,
            size=n_customers,
            replace=True,
        )
        bootstrap_means[i] = sample.mean()

    mean_difference = differences.mean()
    lower = np.quantile(bootstrap_means, 0.025)
    upper = np.quantile(bootstrap_means, 0.975)

    results = pd.DataFrame({
        "metric": [
            "customers",
            "mean_difference",
            "ci_95_lower",
            "ci_95_upper",
        ],
        "value": [
            n_customers,
            mean_difference,
            lower,
            upper,
        ],
    })
    results.to_csv(OUTPUT_FILE, index=False)

    print("Customer-level bootstrap completed.")
    print("Customers:", n_customers)
    print(f"Mean difference: {mean_difference * 100:.2f} percentage points")
    print(
        "95% bootstrap confidence interval: "
        f"{lower * 100:.2f} to {upper * 100:.2f} percentage points"
    )
    print(f"Saved results to: {OUTPUT_FILE}")
    print("Interpretation: descriptive uncertainty, not causal proof.")


if __name__ == "__main__":
    main()
