
from pathlib import Path
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
PLOT_DIR = ROOT / "plots"


def main():
    PLOT_DIR.mkdir(parents=True, exist_ok=True)

    # Previously obtained exploratory treatment-effect estimates.
    methods = ["DoWhy", "EconML"]
    effects = [9.09, 8.66]

    fig, ax = plt.subplots(figsize=(8, 5))

    bars = ax.bar(methods, effects, width=0.5)

    ax.set_title("DoWhy vs EconML: Treatment Effect Comparison")
    ax.set_xlabel("Causal ML Method")
    ax.set_ylabel("Estimated Treatment Effect (percentage points)")
    ax.set_ylim(0, 11)
    ax.grid(axis="y", alpha=0.3)

    ax.bar_label(bars, labels=[f"+{v:.2f} pp" for v in effects], padding=5)

    fig.text(
        0.5, 0.01,
        "Exploratory estimates; not confirmed causal effects.",
        ha="center",
        fontsize=9
    )

    fig.tight_layout(rect=[0, 0.06, 1, 1])

    output_file = PLOT_DIR / "dowhy_econml_comparison.png"
    fig.savefig(output_file, dpi=300)
    plt.close(fig)

    print("DoWhy estimate: +9.09 percentage points")
    print("EconML estimate: +8.66 percentage points")
    print("Difference: 0.43 percentage points")
    print("Plot successfully saved to:", output_file)


if __name__ == "__main__":
    main()
