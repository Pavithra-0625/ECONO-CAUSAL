
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = ROOT / "outputs" / "causal_features_dataset.csv"
PLOT_DIR = ROOT / "plots"


def main():
    df = pd.read_csv(INPUT_FILE)
    PLOT_DIR.mkdir(parents=True, exist_ok=True)

    # Calculate paired completion rates by customer and offer type.
    rates = (
        df.groupby(["person", "offer_type"])["outcome_completed"]
        .agg(["count", "mean"])
        .unstack("offer_type")
    )

    paired = rates.dropna(
        subset=[("mean", "bogo"), ("mean", "discount")]
    ).copy()

    paired["difference_pp"] = (
        paired[("mean", "discount")]
        - paired[("mean", "bogo")]
    ) * 100

    # Subset with equal numbers of offers of each type.
    equal_counts = paired[
        paired[("count", "bogo")] == paired[("count", "discount")]
    ]

    labels = ["All paired customers", "Equal offer counts"]
    means = [
        paired["difference_pp"].mean(),
        (
            equal_counts[("mean", "discount")]
            - equal_counts[("mean", "bogo")]
        ).mean() * 100,
    ]

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(labels, means)

    ax.axhline(0, linewidth=1)
    ax.set_title("Discount–BOGO Completion Difference")
    ax.set_ylabel("Mean difference (percentage points)")
    ax.grid(axis="y", alpha=0.3)
    ax.bar_label(bars, fmt="%.2f", padding=4)
    fig.tight_layout()

    output_file = PLOT_DIR / "equal_offer_count_comparison.png"
    fig.savefig(output_file, dpi=300)
    plt.close(fig)

    print("All paired customers:", len(paired))
    print("Equal-count customers:", len(equal_counts))
    print("All paired mean difference (pp):", round(means[0], 2))
    print("Equal-count mean difference (pp):", round(means[1], 2))
    print("Plot saved to:", output_file)
    print("Note: Descriptive robustness comparison, not causal proof.")


if __name__ == "__main__":
    main()
