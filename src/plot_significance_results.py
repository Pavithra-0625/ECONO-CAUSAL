
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = ROOT / "outputs" / "within_customer_comparison.csv"
PLOT_DIR = ROOT / "plots"


def main():
    df = pd.read_csv(INPUT_FILE)
    PLOT_DIR.mkdir(parents=True, exist_ok=True)

    differences = df["discount_minus_bogo_pp"]

    categories = {
        "Discount higher": int((differences > 0).sum()),
        "BOGO higher": int((differences < 0).sum()),
        "Equal rates": int((differences == 0).sum()),
    }

    fig, ax = plt.subplots(figsize=(9, 5))

    bars = ax.bar(categories.keys(), categories.values())

    ax.set_title("Within-Customer Completion Rate Comparison")
    ax.set_xlabel("Comparison result")
    ax.set_ylabel("Number of customers")
    ax.grid(axis="y", alpha=0.3)

    ax.bar_label(bars, padding=4, fmt="%d")
    fig.tight_layout()

    output_file = PLOT_DIR / "significance_results.png"
    fig.savefig(output_file, dpi=300)
    plt.close(fig)

    print("Customers compared:", len(df))
    print("Plot saved to:", output_file)
    print(
        "Note: This plot summarizes descriptive differences; "
        "the paired sign test is a separate statistical analysis."
    )


if __name__ == "__main__":
    main()
