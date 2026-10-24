
import numpy as np
from scipy.optimize import minimize

# Illustrative promotional budget
total_budget = 10000

# Cost per offer in rupees (illustrative assumptions)
cost_bogo = 100
cost_discount = 80

# Estimated response rates (illustrative assumptions)
response_bogo = 0.45
response_discount = 0.53

# Maximum number of offers for each type
max_bogo = 100
max_discount = 100

# Objective: maximize expected completed offers
# scipy minimizes, so use negative expected completions
def objective(x):
    bogo, discount = x
    return -(response_bogo * bogo + response_discount * discount)

# Budget constraint
def budget_constraint(x):
    bogo, discount = x
    return total_budget - (cost_bogo * bogo + cost_discount * discount)

# Decision variables: number of BOGO and discount offers
bounds = [
    (0, max_bogo),
    (0, max_discount)
]

constraints = [
    {"type": "ineq", "fun": budget_constraint}
]

initial_guess = [0, 0]

result = minimize(
    objective,
    initial_guess,
    method="SLSQP",
    bounds=bounds,
    constraints=constraints
)

if result.success:
    bogo, discount = result.x

    # Round down to whole offers
    bogo = int(np.floor(bogo))
    discount = int(np.floor(discount))

    total_cost = cost_bogo * bogo + cost_discount * discount
    expected_completions = (
        response_bogo * bogo
        + response_discount * discount
    )

    print("Budget Allocation Optimization")
    print("--------------------------------")
    print("Total budget: Rs.", total_budget)
    print("BOGO offers:", bogo)
    print("Discount offers:", discount)
    print("Total budget used: Rs.", total_cost)
    print("Remaining budget: Rs.", total_budget - total_cost)
    print("Expected completed offers:", round(expected_completions, 2))
else:
    print("Optimization failed:", result.message)

    
    # Validation checks
    assert total_cost <= total_budget, "Budget limit exceeded"
    assert 0 <= bogo <= max_bogo, "Invalid BOGO offer count"
    assert 0 <= discount <= max_discount, "Invalid discount offer count"

    print("\nValidation checks passed!")

if result.success:
    assert total_cost <= total_budget, "Budget limit exceeded"
    assert 0 <= bogo <= max_bogo, "Invalid BOGO offer count"
    assert 0 <= discount <= max_discount, "Invalid discount offer count"
    print("\nValidation checks passed!")
