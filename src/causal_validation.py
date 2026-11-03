from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbors

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "outputs" / "causal_features_dataset.csv"
OUT = ROOT / "outputs"
PLOTS = OUT / "plots"

OUT.mkdir(exist_ok=True)
PLOTS.mkdir(exist_ok=True)

def numeric_smd(a, b):
    pooled = np.sqrt((np.var(a, ddof=1) + np.var(b, ddof=1)) / 2)
    if pooled == 0:
        return 0.0
    return (np.mean(a) - np.mean(b)) / pooled

def main():

    df = pd.read_csv(INPUT)

    df = df[
        df["full_validity_window_observed"].astype(bool)
    ].copy()

    df = df.dropna(
        subset=["treatment_discount", "outcome_completed"]
    )

    df["treatment_discount"] = df["treatment_discount"].astype(int)

    numeric = ["age", "income"]
    categorical = ["gender"]

    X = df[numeric + categorical]
    treatment = df["treatment_discount"]

    preprocess = ColumnTransformer([
        ("num", Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler())
        ]), numeric),

        ("cat", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore"))
        ]), categorical)
    ])

    model = Pipeline([
        ("preprocess", preprocess),
        ("logistic", LogisticRegression(max_iter=2000))
    ])

    model.fit(X, treatment)

    df["propensity_score"] = model.predict_proba(X)[:, 1]

    # Common support
    control = df[df.treatment_discount == 0]
    treated = df[df.treatment_discount == 1]

    lower = max(
        control.propensity_score.min(),
        treated.propensity_score.min()
    )

    upper = min(
        control.propensity_score.max(),
        treated.propensity_score.max()
    )

    df = df[
        df.propensity_score.between(lower, upper)
    ].copy()

    control = df[df.treatment_discount == 0].copy()
    treated = df[df.treatment_discount == 1].copy()

    # 1:1 nearest-neighbour matching with replacement
    nn = NearestNeighbors(n_neighbors=1)
    nn.fit(control[["propensity_score"]])

    distances, indices = nn.kneighbors(
        treated[["propensity_score"]]
    )

    matched_control = control.iloc[indices.ravel()].reset_index(drop=True)
    matched_treated = treated.reset_index(drop=True)

    matched = pd.DataFrame({
        "treated_customer": matched_treated["person"],
        "control_customer": matched_control["person"],
        "treated_outcome": matched_treated["outcome_completed"],
        "control_outcome": matched_control["outcome_completed"],
        "propensity_distance": distances.ravel()
    })

    matched["outcome_difference"] = (
        matched["treated_outcome"] -
        matched["control_outcome"]
    )

    matched.to_csv(
        OUT / "psm_matched_pairs.csv",
        index=False
    )

    # Covariate balance
    balance = []

    for col in numeric:
        before = numeric_smd(
            df.loc[df.treatment_discount == 1, col].dropna(),
            df.loc[df.treatment_discount == 0, col].dropna()
        )

        after = numeric_smd(
            matched_treated[col].dropna(),
            matched_control[col].dropna()
        )

        balance.append({
            "covariate": col,
            "SMD_before": before,
            "SMD_after": after
        })

    for level in sorted(df.gender.dropna().unique()):

        before_t = (
            df.loc[df.treatment_discount == 1, "gender"] == level
        ).mean()

        before_c = (
            df.loc[df.treatment_discount == 0, "gender"] == level
        ).mean()

        after_t = (matched_treated.gender == level).mean()
        after_c = (matched_control.gender == level).mean()

        def binary_smd(p1, p0):
            denominator = np.sqrt(
                (p1 * (1-p1) + p0 * (1-p0)) / 2
            )
            return 0 if denominator == 0 else (p1-p0)/denominator

        balance.append({
            "covariate": f"gender_{level}",
            "SMD_before": binary_smd(before_t, before_c),
            "SMD_after": binary_smd(after_t, after_c)
        })

    balance_df = pd.DataFrame(balance)

    balance_df.to_csv(
        OUT / "psm_covariate_balance.csv",
        index=False
    )

    # Bootstrap confidence interval on matched pairs
    rng = np.random.default_rng(42)
    differences = matched["outcome_difference"].to_numpy()

    bootstrap = [
        rng.choice(
            differences,
            size=len(differences),
            replace=True
        ).mean()
        for _ in range(1000)
    ]

    att = differences.mean()
    ci_low, ci_high = np.percentile(bootstrap, [2.5, 97.5])

    summary = pd.DataFrame([{
        "eligible_records": len(df),
        "matched_pairs": len(matched),
        "unique_treated_customers": matched_treated.person.nunique(),
        "matched_ATT": att,
        "CI_95_lower": ci_low,
        "CI_95_upper": ci_high,
        "common_support_lower": lower,
        "common_support_upper": upper
    }])

    summary.to_csv(
        OUT / "causal_validation_summary.csv",
        index=False
    )

    # Balance plot
    plt.figure(figsize=(9, 5))

    positions = np.arange(len(balance_df))

    plt.scatter(
        balance_df["SMD_before"],
        positions,
        label="Before matching"
    )

    plt.scatter(
        balance_df["SMD_after"],
        positions,
        label="After matching"
    )

    plt.axvline(0, linewidth=1)
    plt.axvline(0.1, linestyle="--")
    plt.axvline(-0.1, linestyle="--")

    plt.yticks(positions, balance_df["covariate"])
    plt.xlabel("Standardized Mean Difference")
    plt.title("Covariate Balance Before and After Matching")
    plt.legend()
    plt.tight_layout()

    plt.savefig(
        PLOTS / "psm_covariate_balance.png",
        dpi=150
    )

    print("\nCAUSAL VALIDATION COMPLETED")
    print("\nMatched ATT:")
    print(f"{att:.4f}")

    print("\n95% Bootstrap Confidence Interval:")
    print(f"{ci_low:.4f} to {ci_high:.4f}")

    print("\nCovariate Balance:")
    print(balance_df.to_string(index=False))

    print("\nFiles saved:")
    print("outputs/psm_matched_pairs.csv")
    print("outputs/psm_covariate_balance.csv")
    print("outputs/causal_validation_summary.csv")
    print("outputs/plots/psm_covariate_balance.png")

    print(
        "\nNote: Observational matching cannot remove "
        "unmeasured confounding. Bootstrap resampling "
        "here is at matched-pair level, not customer level."
    )

if __name__ == "__main__":
    main()
