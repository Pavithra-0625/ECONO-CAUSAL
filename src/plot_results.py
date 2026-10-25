
import matplotlib.pyplot as plt
import os

os.makedirs("plots", exist_ok=True)

offer_types = ["BOGO", "Discount"]
completion_rates = [45.02, 52.83]

plt.figure(figsize=(8, 5))
bars = plt.bar(offer_types, completion_rates)

plt.title("Offer Completion Rate Comparison")
plt.xlabel("Offer Type")
plt.ylabel("Completion Rate (%)")
plt.ylim(0, 60)
plt.grid(axis="y", linestyle="--", alpha=0.4)

for bar, rate in zip(bars, completion_rates):
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 1,
        f"{rate:.2f}%",
        ha="center"
    )

plt.tight_layout()
plt.savefig("plots/offer_completion_rate.png", dpi=300)
plt.show()


import pandas as pd

# Load EconML treatment effect estimates
df = pd.read_csv("outputs/econml_effect_estimates.csv")

effects = df["estimated_treatment_effect"]

plt.figure(figsize=(8, 5))
plt.hist(effects, bins=20, edgecolor="black")

plt.title("Distribution of EconML Treatment Effect Estimates")
plt.xlabel("Estimated Treatment Effect")
plt.ylabel("Number of Observations")
plt.axvline(
    effects.mean(),
    linestyle="--",
    label=f"Mean = {effects.mean():.4f}"
)

plt.legend()
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()

plt.savefig("plots/econml_effect_distribution.png", dpi=300)
plt.show()

print("Mean treatment effect:", round(effects.mean(), 4))
print("Number of estimates:", len(effects))


# Plot 3: Offer completion comparison

offer_types = ["BOGO", "Discount"]
completed = [7433, 4523]
not_completed = [9078, 4039]

plt.figure(figsize=(8, 5))

x = range(len(offer_types))

plt.bar(x, completed, label="Completed")
plt.bar(
    x,
    not_completed,
    bottom=completed,
    label="Not Completed"
)

plt.xticks(list(x), offer_types)
plt.title("Offer Outcomes by Offer Type")
plt.xlabel("Offer Type")
plt.ylabel("Number of Offers")
plt.legend()
plt.tight_layout()

plt.savefig("plots/offer_outcomes.png", dpi=300)
plt.show()


# Plot 4: Illustrative budget allocation

offer_types = ["BOGO", "Discount"]
allocated_offers = [19, 99]

plt.figure(figsize=(8, 5))

bars = plt.bar(offer_types, allocated_offers)

plt.title("Budget Optimizer: Offer Allocation")
plt.xlabel("Offer Type")
plt.ylabel("Number of Offers Allocated")

for bar, count in zip(bars, allocated_offers):
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 2,
        str(count),
        ha="center"
    )

plt.grid(axis="y", linestyle="--", alpha=0.4)
plt.tight_layout()

plt.savefig("plots/budget_allocation.png", dpi=300)
plt.show()

print("Total budget: Rs. 10,000")
print("Budget used: Rs. 9,820")
print("Expected completions: 61.02")
