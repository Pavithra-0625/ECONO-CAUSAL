
from pathlib import Path
import pandas as pd
import networkx as nx
from dowhy import CausalModel

# Compatibility fix for older DoWhy with newer NetworkX.
if not hasattr(nx.algorithms, "d_separated"):
    nx.algorithms.d_separated = nx.algorithms.d_separation.is_d_separator

ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = ROOT / "outputs" / "causal_features_dataset.csv"


def main():
    df = pd.read_csv(INPUT_FILE)

    # Keep records with fully observed offer windows.
    df = df[
        df["full_validity_window_observed"].astype(bool)
    ].copy()

    # Use available demographic characteristics.
    confounders = ["age", "income", "gender"]

    required = [
        "person",
        "treatment_discount",
        "outcome_completed",
        *confounders,
    ]
    df = df.dropna(subset=required).copy()

    # Encode gender as indicator columns.
    df = pd.get_dummies(
        df,
        columns=["gender"],
        drop_first=True,
        dtype=int,
    )

    gender_columns = [
        col for col in df.columns if col.startswith("gender_")
    ]
    confounders = ["age", "income"] + gender_columns

    if df.empty:
        raise ValueError("No records remain after filtering.")

    if df["treatment_discount"].nunique() != 2:
        raise ValueError("Both BOGO and discount groups are required.")

    print("Rows used:", len(df))
    print("Unique customers:", df["person"].nunique())

    print("\nTreatment counts:")
    print(df["treatment_discount"].value_counts().to_string())

    print("\nObserved completion rate by treatment:")
    print(
        df.groupby("treatment_discount")["outcome_completed"]
        .mean()
        .to_string()
    )

    # Define the causal model.
    model = CausalModel(
        data=df,
        treatment="treatment_discount",
        outcome="outcome_completed",
        common_causes=confounders,
    )

    # Identify the estimand.
    estimand = model.identify_effect(
        proceed_when_unidentifiable=True
    )

    print("\nIdentified estimand:")
    print(estimand)

    # Estimate using propensity-score matching.
    estimate = model.estimate_effect(
        estimand,
        method_name="backdoor.propensity_score_matching",
    )

    print("\nEstimated effect (discount vs BOGO):")
    print(estimate)

    print("\nPlacebo refutation skipped.")
    print(
        "Reason: the installed DoWhy version failed when "
        "the placebo treatment contained only one class."
    )

    print(
        "\nCaution: This is an exploratory observational estimate. "
        "Repeated records from the same customer may not be "
        "independent, and unmeasured confounding may remain."
    )


if __name__ == "__main__":
    main()
