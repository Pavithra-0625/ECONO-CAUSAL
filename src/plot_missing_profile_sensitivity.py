from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = ROOT / "outputs" / "missing_profile_sensitivity.csv"
PLOT_DIR = ROOT / "plots"


def main():
    df = pd.read_csv(INPUT_FILE)
    PLOT_DIR.mkdir(parents=True, exist_ok=True)

    df["completion_rate_pct"] = df["completion_rate"] * 100

    pivot = df.pivot(
        index="profile_status",
        columns="offer_type",
        values="completion_rate_pct",
    )

    ax = pivot[["bogo", "discount"]].plot(
        kind="bar",
        figsize=(9, 5),
        rot=0,
    )

    ax.set_title("Offer Completion Rates by Profile Status")
    ax.set_xlabel("Demographic Profile Status")
    ax.set_ylabel("Completion Rate (%)")
    ax.legend(["BOGO", "Discount"], title="Offer Type")
    ax.set_ylim(0, 70)
    ax.grid(axis="y", alpha=0.3)

    for container in ax.containers:
        ax.bar_label(container, fmt="%.2f%%", padding=3)

    plt.tight_layout()

    output_file = PLOT_DIR / "missing_profile_sensitivity.png"
    plt.savefig(output_file, dpi=300)
    plt.close()

    print(f"Plot successfully saved to: {output_file}")


if __name__ == "__main__":
    main()
