
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = ROOT / "outputs" / "propensity_scores.csv"
PLOT_DIR = ROOT / "plots"


def main():
    df = pd.read_csv(INPUT_FILE)

    # Create the output directory if it does not exist.
    PLOT_DIR.mkdir(parents=True, exist_ok=True)

    # Plot propensity-score distributions by offer type.
    plt.figure(figsize=(9, 5))

    for treatment, label in [(0, "BOGO"), (1, "Discount")]:
        scores = df.loc[
            df["treatment_discount"] == treatment,
            "propensity_score",
        ]
        plt.hist(
            scores,
            bins=20,
            alpha=0.6,
            label=label,
        )

    plt.title("Propensity Score Distribution by Offer Type")
    plt.xlabel("Estimated Propensity Score")
    plt.ylabel("Number of Records")
    plt.legend()
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()

    output_file = PLOT_DIR / "propensity_score_overlap.png"
    plt.savefig(output_file, dpi=300)
    plt.close()

    print("Propensity-score plot saved to:", output_file)


if __name__ == "__main__":
    main()
