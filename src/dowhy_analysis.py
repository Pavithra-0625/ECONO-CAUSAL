
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import networkx as nx

from dowhy import CausalModel
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbors


# Compatibility fix for older DoWhy with newer NetworkX.
if not hasattr(nx.algorithms, "d_separated"):
    nx.algorithms.d_separated = nx.algorithms.d_separation.is_d_separator


ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = ROOT / "outputs" / "causal_features_dataset.csv"
OUTPUT_FILE = ROOT / "outputs" / "dowhy_refutation_results.csv"

RANDOM_SEED = 42
NUM_SIMULATIONS = 10
PLACEBO_SIMULATIONS = 200
SUBSET_FRACTION = 0.80


# --------------------------------------------------
# 1. Prepare data
# --------------------------------------------------

def load_data():

    df = pd.read_csv(INPUT_FILE)

    required = [
        "person",
        "treatment_discount",
        "outcome_completed",
        "full_validity_window_observed",
        "age",
        "income",
        "gender",
    ]

    missing = [c for c in required if c not in df.columns]

    if missing:
        raise ValueError(f"Missing columns: {missing}")

    observed = df["full_validity_window_observed"]

    if observed.dtype != bool:
        observed = observed.astype(str).str.strip().str.lower().isin(
            ["true", "1", "yes"]
        )

    df = df.loc[observed].copy()

    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df["income"] = pd.to_numeric(df["income"], errors="coerce")

    df = df.dropna(
        subset=[
            "person",
            "treatment_discount",
            "outcome_completed",
            "age",
            "income",
            "gender",
        ]
    ).copy()

    df["treatment_discount"] = df["treatment_discount"].astype(int)
    df["outcome_completed"] = df["outcome_completed"].astype(int)

    if set(df["treatment_discount"].unique()) != {0, 1}:
        raise ValueError("Both treatment groups are required.")

    if not df["outcome_completed"].isin([0, 1]).all():
        raise ValueError("Outcome must contain only 0 and 1.")

    df = pd.get_dummies(
        df,
        columns=["gender"],
        drop_first=True,
        dtype=int,
    )

    confounders = [
        "age",
        "income",
    ] + [
        c for c in df.columns if c.startswith("gender_")
    ]

    if not confounders:
        raise ValueError("No confounder columns available.")

    print("Rows used:", len(df))
    print("Unique customers:", df["person"].nunique())

    print("\nTreatment counts:")
    print(df["treatment_discount"].value_counts())

    return df, confounders


# --------------------------------------------------
# 2. Custom propensity-score matching
# --------------------------------------------------

def custom_psm(data, features, treatment_column="treatment_discount"):

    data = data.copy()

    treatment = data[treatment_column].to_numpy()
    outcome = data["outcome_completed"].to_numpy()

    treated_indices = np.where(treatment == 1)[0]
    control_indices = np.where(treatment == 0)[0]

    if len(treated_indices) == 0 or len(control_indices) == 0:
        raise ValueError("Both treatment groups are needed for matching.")

    X = data[features].astype(float)

    propensity_model = make_pipeline(
        StandardScaler(),
        LogisticRegression(
            max_iter=2000,
            random_state=RANDOM_SEED,
        ),
    )

    propensity_model.fit(X, treatment)

    propensity_scores = propensity_model.predict_proba(X)[:, 1]

    treated_scores = propensity_scores[treated_indices]
    control_scores = propensity_scores[control_indices]

    matcher = NearestNeighbors(n_neighbors=1)

    matcher.fit(control_scores.reshape(-1, 1))

    _, matched_positions = matcher.kneighbors(
        treated_scores.reshape(-1, 1)
    )

    matched_control_indices = control_indices[
        matched_positions[:, 0]
    ]

    differences = (
        outcome[treated_indices] -
        outcome[matched_control_indices]
    )

    return float(np.mean(differences))


# --------------------------------------------------
# 3. Original DoWhy PSM estimate
# --------------------------------------------------

def original_dowhy_psm(df, confounders):

    model = CausalModel(
        data=df,
        treatment="treatment_discount",
        outcome="outcome_completed",
        common_causes=confounders,
    )

    estimand = model.identify_effect(
        proceed_when_unidentifiable=True
    )

    estimate = model.estimate_effect(
        estimand,
        method_name="backdoor.propensity_score_matching",
    )

    return float(estimate.value)


# --------------------------------------------------
# 4. Random common cause test
# --------------------------------------------------

def random_common_cause_test(df, confounders, rng):

    results = []

    unique_customers = df["person"].unique()

    for simulation in range(NUM_SIMULATIONS):

        random_values = rng.normal(
            size=len(unique_customers)
        )

        random_map = dict(
            zip(unique_customers, random_values)
        )

        test_data = df.copy()

        test_data["random_customer_confounder"] = (
            test_data["person"].map(random_map)
        )

        features = confounders + [
            "random_customer_confounder"
        ]

        effect = custom_psm(test_data, features)

        results.append({
            "test": "Random Common Cause",
            "simulation": simulation + 1,
            "effect": effect,
        })

        print(
            f"Random Common Cause {simulation + 1}: "
            f"{effect:.4f}"
        )

    return results


# --------------------------------------------------
# 5. Data subset test
# --------------------------------------------------

def data_subset_test(df, confounders, rng):

    results = []

    customers = df["person"].unique()

    for simulation in range(NUM_SIMULATIONS):

        selected_count = max(
            2,
            int(len(customers) * SUBSET_FRACTION)
        )

        selected_customers = rng.choice(
            customers,
            size=selected_count,
            replace=False,
        )

        subset = df[
            df["person"].isin(selected_customers)
        ].copy()

        effect = custom_psm(subset, confounders)

        results.append({
            "test": "Data Subset",
            "simulation": simulation + 1,
            "effect": effect,
        })

        print(
            f"Data Subset {simulation + 1}: "
            f"{effect:.4f}"
        )

    return results


# --------------------------------------------------
# 6. Placebo treatment permutation test
# --------------------------------------------------

def placebo_test(df, confounders, rng):

    results = []

    for simulation in range(PLACEBO_SIMULATIONS):

        placebo_data = df.copy()

        placebo_data["placebo_treatment"] = rng.permutation(
            placebo_data["treatment_discount"].to_numpy()
        )

        effect = custom_psm(
            placebo_data,
            confounders,
            treatment_column="placebo_treatment",
        )

        results.append({
            "test": "Placebo Treatment",
            "simulation": simulation + 1,
            "effect": effect,
        })

        print(
            f"Placebo Treatment {simulation + 1}: "
            f"{effect:.4f}"
        )

    return results


# --------------------------------------------------
# 7. Main execution
# --------------------------------------------------

def main():

    rng = np.random.default_rng(RANDOM_SEED)

    df, confounders = load_data()

    print("\nConfounders:", confounders)

    print("\nCalculating original DoWhy PSM estimate...")

    with warnings.catch_warnings():
        warnings.simplefilter("default")

        original_effect = original_dowhy_psm(
            df,
            confounders,
        )

    print(
        "\nOriginal DoWhy PSM effect:",
        round(original_effect, 4),
    )

    print("\nCalculating custom PSM baseline...")

    custom_baseline = custom_psm(df, confounders)

    print(
        "Custom PSM ATT:",
        round(custom_baseline, 4),
    )

    # Random Common Cause
    print("\nStarting Random Common Cause test...")

    results = random_common_cause_test(
        df,
        confounders,
        rng,
    )

    # Data Subset
    print("\nStarting Data Subset test...")

    results.extend(
        data_subset_test(
            df,
            confounders,
            rng,
        )
    )

    # Placebo Treatment
    print("\nStarting Placebo Treatment test...")

    results.extend(
        placebo_test(
            df,
            confounders,
            rng,
        )
    )

    results_df = pd.DataFrame(results)

    results_df["original_dowhy_psm_effect"] = original_effect
    results_df["custom_psm_baseline"] = custom_baseline

    # --------------------------------------------------
    # 8. Empirical placebo p-value
    # --------------------------------------------------

    placebo_effects = results_df.loc[
        results_df["test"] == "Placebo Treatment",
        "effect",
    ].to_numpy()

    placebo_p_value = (
        1 + np.sum(
            np.abs(placebo_effects) >= abs(custom_baseline)
        )
    ) / (len(placebo_effects) + 1)

    results_df["placebo_empirical_p_value"] = np.nan

    results_df.loc[
        results_df["test"] == "Placebo Treatment",
        "placebo_empirical_p_value",
    ] = placebo_p_value

    # --------------------------------------------------
    # 9. Save results
    # --------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    results_df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    # --------------------------------------------------
    # 10. Summary
    # --------------------------------------------------

    print("\n" + "=" * 55)
    print("ROBUSTNESS TEST SUMMARY")
    print("=" * 55)

    print(
        "\nOriginal DoWhy PSM:",
        round(original_effect, 4),
    )

    print(
        "Custom PSM baseline:",
        round(custom_baseline, 4),
    )

    summary = results_df.groupby("test")["effect"].agg(
        ["mean", "std", "min", "max"]
    )

    print("\nSimulation results:")
    print(summary.round(4))

    print(
        "\nPlacebo empirical p-value:",
        round(placebo_p_value, 4),
    )

    print("\nNumber of simulations:")
    print("Random Common Cause:", NUM_SIMULATIONS)
    print("Data Subset:", NUM_SIMULATIONS)
    print("Placebo Treatment:", PLACEBO_SIMULATIONS)

    print("\nSaved results to:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()
