
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# -----------------------------------------
# 1. Configuration
# -----------------------------------------
INPUT_FILE = "outputs/econml_effect_estimates.csv"
OUTPUT_DIR = "outputs"
PLOT_DIR = os.path.join(OUTPUT_DIR, "plots")

TOTAL_BUDGET = 200000
COST_PER_DISCOUNT = 100
MAX_CUSTOMERS = TOTAL_BUDGET // COST_PER_DISCOUNT

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(PLOT_DIR, exist_ok=True)

# -----------------------------------------
# 2. Load EconML predictions
# -----------------------------------------
df = pd.read_csv(INPUT_FILE)

required_columns = [
    "person",
    "estimated_treatment_effect"
]

missing = [col for col in required_columns if col not in df.columns]

if missing:
    raise ValueError(f"Missing required columns: {missing}")

df["estimated_treatment_effect"] = pd.to_numeric(
    df["estimated_treatment_effect"], errors="coerce"
)

df = df.dropna(
    subset=["person", "estimated_treatment_effect"]
).copy()

if df.empty:
    raise ValueError("No valid EconML predictions found.")

# -----------------------------------------
# 3. Aggregate predictions by customer
# -----------------------------------------
# Each customer receives at most one allocation.
customer_df = (
    df.groupby("person")
    .agg(
        mean_predicted_effect=("estimated_treatment_effect", "mean"),
        number_of_offer_records=("estimated_treatment_effect", "count")
    )
    .reset_index()
)

# -----------------------------------------
# 4. Rank customers
# -----------------------------------------
customer_df = customer_df.sort_values(
    "mean_predicted_effect",
    ascending=False
).reset_index(drop=True)

customer_df["rank"] = np.arange(1, len(customer_df) + 1)

# Allocate only to customers with positive predicted effects.
eligible = customer_df[
    customer_df["mean_predicted_effect"] > 0
].copy()

# -----------------------------------------
# 5. Apply budget constraints
# -----------------------------------------
allocated_count = min(len(eligible), MAX_CUSTOMERS)

selected_ids = set(
    eligible.head(allocated_count)["person"]
)

customer_df["discount_allocated"] = (
    customer_df["person"].isin(selected_ids)
).astype(int)

customer_df["discount_cost"] = (
    customer_df["discount_allocated"] * COST_PER_DISCOUNT
)

customer_df["expected_incremental_completions"] = (
    customer_df["mean_predicted_effect"]
    * customer_df["discount_allocated"]
)

# -----------------------------------------
# 6. Create allocation matrix
# -----------------------------------------
customer_df["allocation_status"] = np.where(
    customer_df["discount_allocated"] == 1,
    "Discount Allocated",
    np.where(
        customer_df["mean_predicted_effect"] <= 0,
        "Not Eligible - Non-positive Effect",
        "Not Allocated - Budget Limit"
    )
)

customer_df.to_csv(
    os.path.join(OUTPUT_DIR, "optimized_discount_allocation.csv"),
    index=False
)

# -----------------------------------------
# 7. Calculate optimization summary
# -----------------------------------------
total_spend = int(customer_df["discount_cost"].sum())
remaining_budget = TOTAL_BUDGET - total_spend

allocated = customer_df[
    customer_df["discount_allocated"] == 1
]

summary = pd.DataFrame([{
    "total_budget": TOTAL_BUDGET,
    "cost_per_discount": COST_PER_DISCOUNT,
    "maximum_possible_customers": MAX_CUSTOMERS,
    "total_unique_customers": len(customer_df),
    "positive_effect_customers": len(eligible),
    "customers_allocated": len(allocated),
    "customers_not_allocated": len(customer_df) - len(allocated),
    "total_budget_used": total_spend,
    "remaining_budget": remaining_budget,
    "budget_utilization_percentage": (
        total_spend / TOTAL_BUDGET * 100
    ),
    "mean_predicted_effect_allocated": (
        allocated["mean_predicted_effect"].mean()
        if len(allocated) else 0
    ),
    "sum_predicted_effects_allocated": (
        allocated["mean_predicted_effect"].sum()
    )
}])

summary.to_csv(
    os.path.join(OUTPUT_DIR, "optimization_summary.csv"),
    index=False
)

# -----------------------------------------
# 8. Plot allocation results
# -----------------------------------------
plt.figure(figsize=(9, 5))

labels = ["Allocated", "Not Allocated"]
counts = [
    len(allocated),
    len(customer_df) - len(allocated)
]

plt.bar(labels, counts)
plt.title("Customer Discount Allocation")
plt.ylabel("Number of Unique Customers")
plt.tight_layout()

plt.savefig(
    os.path.join(PLOT_DIR, "optimization_allocation.png"),
    dpi=300
)
plt.close()

# -----------------------------------------
# 9. Plot predicted treatment effects
# -----------------------------------------
plt.figure(figsize=(9, 5))

plt.plot(
    np.arange(1, len(customer_df) + 1),
    customer_df["mean_predicted_effect"],
    label="Customer predicted effect"
)

plt.axhline(
    y=0,
    linestyle="--",
    label="Zero effect"
)

plt.axvline(
    x=allocated_count,
    linestyle=":",
    label="Allocation cutoff"
)

plt.title("Customer Ranking by Predicted Treatment Effect")
plt.xlabel("Customer Rank")
plt.ylabel("Mean Predicted Treatment Effect")
plt.legend()
plt.tight_layout()

plt.savefig(
    os.path.join(PLOT_DIR, "optimization_effect_ranking.png"),
    dpi=300
)
plt.close()

# -----------------------------------------
# 10. Display results
# -----------------------------------------
print("\n===== TASK 3: OPTIMIZATION RESULTS =====")
print(summary.to_string(index=False))

print("\n===== TOP 10 ALLOCATED CUSTOMERS =====")
print(
    allocated.head(10)[
        ["person", "mean_predicted_effect", "rank", "discount_cost"]
    ].to_string(index=False)
)

print("\nGenerated files:")
print("outputs/optimized_discount_allocation.csv")
print("outputs/optimization_summary.csv")
print("outputs/plots/optimization_allocation.png")
print("outputs/plots/optimization_effect_ranking.png")

print("\nOptimization completed successfully.")
