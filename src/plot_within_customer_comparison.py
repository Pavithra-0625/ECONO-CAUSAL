
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

    plt.figure(figsize=(9, 5))

    bars = plt.bar(
        categories.keys(),
        categories.values(),
    )

    plt.title("Within-Customer Offer Completion Comparison")
    plt.xlabel("Comparison result")
    plt.ylabel("Number of customers")
    plt.grid(axis="y", alpha=0.3)

    plt.bar_label(bars, padding=3, fmt="%d")
    plt.tight_layout()

    output_file = PLOT_DIR / "within_customer_comparison.png"
    plt.savefig(output_file, dpi=300)
    plt.close()

    print("Customers compared:", len(df))
    print("Plot saved to:", output_file)
    print("Note: Descriptive comparison, not proof of causal effect.")


if __name__ == "__main__":
    main()
