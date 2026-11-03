
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = ROOT / "outputs" / "econml_effect_estimates.csv"
OUTPUT_DIR = ROOT / "outputs"
PLOT_DIR = OUTPUT_DIR / "plots"

RANDOM_SEED = 42
RANDOM_SIMULATIONS = 200

OUTPUT_DIR.mkdir(exist_ok=True)
PLOT_DIR.mkdir(exist_ok=True)


def load_data():

    df = pd.read_csv(INPUT_FILE)

    required = [
        "person",
        "treatment_discount",
        "outcome_completed",
        "estimated_treatment_effect"
    ]

    missing = [col for col in required if col not in df.columns]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df = df.dropna(subset=required).copy()

    df["treatment_discount"] = df["treatment_discount"].astype(int)
    df["outcome_completed"] = df["outcome_completed"].astype(int)

    if set(df["treatment_discount"].unique()) != {0, 1}:
        raise ValueError("Both BOGO and Discount groups are required.")

    if not df["outcome_completed"].isin([0, 1]).all():
        raise ValueError("Outcome must contain only 0 and 1.")

    return df


def calculate_qini_gain(df):

    total_treated = (df["treatment_discount"] == 1).sum()
    total_control = (df["treatment_discount"] == 0).sum()

    if total_treated == 0 or total_control == 0:
        raise ValueError("Both treatment groups must have observations.")

    treated_count = 0
    control_count = 0
    treated_responses = 0
    control_responses = 0

    rows = []

    n = len(df)

    checkpoints = set(
        np.linspace(1, n, min(200, n), dtype=int)
    )

    for i, row in df.iterrows():

        if row["treatment_discount"] == 1:
            treated_count += 1
            treated_responses += row["outcome_completed"]

        else:
            control_count += 1
            control_responses += row["outcome_completed"]

        if (i + 1) in checkpoints:

            qini_gain = (
                treated_responses
                - control_responses * (total_treated / total_control)
            )

            rows.append({
                "ranked_fraction": (i + 1) / n,
                "observations": i + 1,
                "treated_count": treated_count,
                "control_count": control_count,
                "treated_responses": treated_responses,
                "control_responses": control_responses,
                "qini_gain": qini_gain
            })

    return pd.DataFrame(rows)


def main():

    print("\nLoading EconML treatment-effect estimates...")

    df = load_data()

    print("Total offer records:", len(df))
    print("Unique customers:", df["person"].nunique())

    print("\nTreatment counts:")
    print(df["treatment_discount"].value_counts())

    # Rank records by predicted treatment effect.
    df = df.sort_values(
        "estimated_treatment_effect",
        ascending=False
    ).reset_index(drop=True)

    df["rank"] = np.arange(1, len(df) + 1)

    df["targeted_percentage"] = (
        df["rank"] / len(df) * 100
    )

    # Save ranked treatment-effect estimates.
    df.to_csv(
        OUTPUT_DIR / "uplift_ranked_customers.csv",
        index=False
    )

    # Calculate uplift and Qini-style gain.
    curve = calculate_qini_gain(df)

    curve.to_csv(
        OUTPUT_DIR / "uplift_curve_data.csv",
        index=False
    )

    total_treated = (df["treatment_discount"] == 1).sum()
    total_control = (df["treatment_discount"] == 0).sum()

    treated_rate = df.loc[
        df["treatment_discount"] == 1,
        "outcome_completed"
    ].mean()

    control_rate = df.loc[
        df["treatment_discount"] == 0,
        "outcome_completed"
    ].mean()

    final_gain = (
        df.loc[df["treatment_discount"] == 1, "outcome_completed"].sum()
        - df.loc[df["treatment_discount"] == 0, "outcome_completed"].sum()
        * (total_treated / total_control)
    )

    # Random targeting comparison using 200 shuffled rankings.
    rng = np.random.default_rng(RANDOM_SEED)

    fractions = np.arange(0.1, 1.01, 0.1)

    comparison_rows = []

    score_order = np.arange(len(df))

    for fraction in fractions:

        k = max(1, int(len(df) * fraction))

        top_group = df.iloc[:k]

        t = top_group["treatment_discount"].to_numpy()
        y = top_group["outcome_completed"].to_numpy()

        selected_treated = t == 1
        selected_control = t == 0

        gain = (
            y[selected_treated].sum()
            - y[selected_control].sum()
            * (total_treated / total_control)
        )

        random_gains = []

        for _ in range(RANDOM_SIMULATIONS):

            shuffled = rng.permutation(score_order[:])

            random_group = df.iloc[shuffled[:k]]

            rt = random_group["treatment_discount"].to_numpy()
            ry = random_group["outcome_completed"].to_numpy()

            random_gains.append(
                ry[rt == 1].sum()
                - ry[rt == 0].sum()
                * (total_treated / total_control)
            )

        comparison_rows.append({
            "targeted_percentage": fraction * 100,
            "targeted_qini_gain": gain,
            "random_mean_gain": np.mean(random_gains),
            "random_lower_95": np.percentile(random_gains, 2.5),
            "random_upper_95": np.percentile(random_gains, 97.5)
        })

    comparison = pd.DataFrame(comparison_rows)

    comparison.to_csv(
        OUTPUT_DIR / "targeting_comparison.csv",
        index=False
    )

    # Uplift curve.
    plt.figure(figsize=(9, 5))

    plt.plot(
        curve["ranked_fraction"] * 100,
        curve["qini_gain"],
        label="EconML effect ranking"
    )

    plt.plot(
        [0, 100],
        [0, final_gain],
        linestyle="--",
        label="Random targeting reference"
    )

    plt.xlabel("Top-ranked offer records targeted (%)")
    plt.ylabel("Cumulative Qini gain")
    plt.title("Uplift Curve Using EconML Treatment Effects")
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()

    plt.savefig(
        PLOT_DIR / "uplift_curve.png",
        dpi=150
    )

    plt.close()

    # Qini curve with random-targeting reference.
    plt.figure(figsize=(9, 5))

    plt.plot(
        curve["ranked_fraction"] * 100,
        curve["qini_gain"],
        label="EconML ranking"
    )

    plt.plot(
        [0, 100],
        [0, final_gain],
        linestyle="--",
        label="Random targeting"
    )

    plt.xlabel("Population ranked by predicted treatment effect (%)")
    plt.ylabel("Cumulative Qini gain")
    plt.title("Qini Curve – EconML Model")
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()

    plt.savefig(
        PLOT_DIR / "qini_curve.png",
        dpi=150
    )

    plt.close()

    # Targeted vs random comparison.
    plt.figure(figsize=(9, 5))

    plt.plot(
        comparison["targeted_percentage"],
        comparison["targeted_qini_gain"],
        marker="o",
        label="EconML targeted ranking"
    )

    plt.plot(
        comparison["targeted_percentage"],
        comparison["random_mean_gain"],
        marker="s",
        linestyle="--",
        label="Random targeting mean"
    )

    plt.fill_between(
        comparison["targeted_percentage"],
        comparison["random_lower_95"],
        comparison["random_upper_95"],
        alpha=0.2,
        label="Random targeting 95% simulation range"
    )

    plt.xlabel("Percentage of offer records targeted")
    plt.ylabel("Cumulative Qini gain")
    plt.title("Targeted vs Random Customer Selection")
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()

    plt.savefig(
        PLOT_DIR / "targeting_comparison.png",
        dpi=150
    )

    plt.close()

    # Summary
    summary = pd.DataFrame([{
        "total_offer_records": len(df),
        "unique_customers": df["person"].nunique(),
        "discount_records": total_treated,
        "bogo_records": total_control,
        "discount_completion_rate": treated_rate,
        "bogo_completion_rate": control_rate,
        "mean_predicted_effect": df["estimated_treatment_effect"].mean(),
        "median_predicted_effect": df["estimated_treatment_effect"].median(),
        "positive_effect_count": (
            df["estimated_treatment_effect"] > 0
        ).sum(),
        "negative_effect_count": (
            df["estimated_treatment_effect"] < 0
        ).sum(),
        "final_qini_gain": final_gain,
        "random_simulations": RANDOM_SIMULATIONS
    }])

    summary.to_csv(
        OUTPUT_DIR / "uplift_analysis_summary.csv",
        index=False
    )

    print("\n======================================")
    print("UPLIFT ANALYSIS COMPLETED")
    print("======================================")

    print("\nMean predicted treatment effect:")
    print(round(df["estimated_treatment_effect"].mean(), 4))

    print("\nPositive treatment effects:")
    print((df["estimated_treatment_effect"] > 0).sum())

    print("\nNegative treatment effects:")
    print((df["estimated_treatment_effect"] < 0).sum())

    print("\nObserved completion rates:")
    print("Discount:", round(treated_rate, 4))
    print("BOGO:", round(control_rate, 4))

    print("\nTargeting comparison:")
    print(comparison.round(4).to_string(index=False))

    print("\nGenerated files:")
    print("outputs/uplift_ranked_customers.csv")
    print("outputs/uplift_curve_data.csv")
    print("outputs/targeting_comparison.csv")
    print("outputs/uplift_analysis_summary.csv")
    print("outputs/plots/uplift_curve.png")
    print("outputs/plots/qini_curve.png")
    print("outputs/plots/targeting_comparison.png")

    print(
        "\nResearch caution: This is an exploratory observational "
        "ranking evaluation at offer-record level. Customers may "
        "appear multiple times. It is not a randomized Qini estimate."
    )


if __name__ == "__main__":
    main()
