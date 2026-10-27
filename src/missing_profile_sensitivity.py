
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = ROOT / "outputs" / "causal_features_dataset.csv"
OUTPUT_FILE = ROOT / "outputs" / "missing_profile_sensitivity.csv"


def main():
    df = pd.read_csv(INPUT_FILE)

    # Keep offers with a fully observed validity window.
    df = df[
        df["full_validity_window_observed"].astype(bool)
    ].copy()

    # Identify whether demographic information is missing.
    df["profile_status"] = df["age"].isna().map({
        True: "Missing",
        False: "Available",
    })

    # Calculate counts and completion rates by group.
    summary = (
        df.groupby(["profile_status", "offer_type"], observed=True)
        ["outcome_completed"]
        .agg(
            total_offers="count",
            completed_offers="sum",
            completion_rate="mean",
        )
        .reset_index()
    )

    summary["completion_rate_pct"] = (
        summary["completion_rate"] * 100
    ).round(2)

    print("Completion rates by profile status and offer type:")
    print(summary.to_string(index=False))

    # Calculate Discount minus BOGO within each profile group.
    rates = summary.pivot(
        index="profile_status",
        columns="offer_type",
        values="completion_rate",
    )

    if {"discount", "bogo"}.issubset(rates.columns):
        rates["difference_percentage_points"] = (
            rates["discount"] - rates["bogo"]
        ) * 100

        print("\nDiscount minus BOGO (percentage points):")
        print(rates["difference_percentage_points"].round(2).to_string())
    else:
        print("\nWarning: Expected offer types 'discount' and 'bogo' were not both found.")

    # Save the summary for future reporting and visualization.
    summary.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSensitivity summary saved to: {OUTPUT_FILE}")

    print(
        "\nInterpretation: These are descriptive comparisons, "
        "not confirmed causal effects."
    )


if __name__ == "__main__":
    main()


from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = ROOT / "outputs" / "missing_profile_sensitivity.csv"
PLOT_DIR = ROOT / "plots"


def main():
    df = pd.read_csv(INPUT_FILE)

    PLOT_DIR.mkdir(parents=True, exist_ok=True)

    # Convert completion rates to percentages.
    df["completion_rate_pct"] = df["completion_rate"] * 100

    # Arrange the data for grouped bars.
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

    ax.set_title("Offer Completion Rates by Demographic Profile Status")
    ax.set_xlabel("Demographic Profile Status")
    ax.set_ylabel("Completion Rate (%)")
    ax.legend(["BOGO", "Discount"], title="Offer Type")
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()

    output_file = PLOT_DIR / "missing_profile_sensitivity.png"
    plt.savefig(output_file, dpi=300)
    plt.close()

    print("Sensitivity plot saved to:", output_file)


if __name__ == "__main__":
    main()


from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = ROOT / "outputs" / "missing_profile_sensitivity.csv"
PLOT_DIR = ROOT / "plots"


def main():
    df = pd.read_csv(INPUT_FILE)

    PLOT_DIR.mkdir(parents=True, exist_ok=True)

    pivot = df.pivot(
        index="profile_status",
        columns="offer_type",
        values="completion_rate_pct"
    )

    ax = pivot[["bogo", "discount"]].plot(
        kind="bar",
        figsize=(9, 5),
        color=["steelblue", "orange"],
        rot=0
    )

    ax.set_title("Offer Completion Rates by Profile Status")
    ax.set_xlabel("Demographic Profile Status")
    ax.set_ylabel("Completion Rate (%)")
    ax.legend(["BOGO", "Discount"])

    for container in ax.containers:
        ax.bar_label(container, fmt="%.2f%%", padding=3)

    ax.set_ylim(0, 70)
    plt.tight_layout()

    output_file = PLOT_DIR / "missing_profile_sensitivity.png"
    plt.savefig(output_file, dpi=300)
    plt.close()

    print("Plot successfully saved to:", output_file)


if __name__ == "__main__":
    main()
