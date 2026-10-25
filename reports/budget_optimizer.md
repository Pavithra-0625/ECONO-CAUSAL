# EconoCausal — Budget Allocation Optimizer

## 1. Objective

The objective of the budget allocation optimizer is to distribute a limited promotional budget between BOGO and discount offers while maximizing the expected number of completed offers.

## 2. Tools Used

- Python
- NumPy
- SciPy
- SciPy optimization method: SLSQP

## 3. Input Parameters

The initial prototype uses illustrative values for testing.

| Parameter | BOGO | Discount |
|---|---:|---:|
| Cost per offer | ₹100 | ₹80 |
| Assumed response rate | 45% | 53% |
| Maximum offers | 100 | 100 |

Total available budget: ₹10,000.

These values are assumptions for the prototype and are not verified business costs or proven causal effects.

## 4. Optimization Objective

The optimizer maximizes expected completed offers:

Expected completions = (BOGO response rate × BOGO offers) + (Discount response rate × Discount offers).

Since SciPy's `minimize` function minimizes an objective, the program minimizes the negative of expected completions.

## 5. Constraints

The optimizer applies the following constraints:

1. Total promotional spending must not exceed ₹10,000.
2. BOGO offer allocation must be between 0 and 100.
3. Discount offer allocation must be between 0 and 100.
4. The final allocation must use whole numbers of offers.

## 6. Example Results

| Metric | Result |
|---|---:|
| Total budget | ₹10,000 |
| BOGO offers allocated | 19 |
| Discount offers allocated | 99 |
| Total spending | ₹9,820 |
| Remaining budget | ₹180 |
| Expected completed offers | 61.02 |

These results were produced using the illustrative assumptions defined in the prototype.

## 7. Validation

The program includes assertion checks to verify that:

- Total spending does not exceed the budget.
- BOGO offer allocation stays within its permitted range.
- Discount offer allocation stays within its permitted range.

The checks passed during the test run.

## 8. Limitations

1. The response rates and costs are illustrative assumptions.
2. The optimizer does not yet use verified business costs or experimentally validated treatment effects.
3. The current model considers only two offer types.
4. The prototype does not yet account for inventory, customer segments, or other business constraints.
5. Further testing is required before using the allocation for real business decisions.

## 9. Future Improvements

- Incorporate validated business costs and response estimates.
- Evaluate whether causal estimates are reliable enough to inform allocation.
- Add customer-segment and operational constraints.
- Compare optimized allocation against baseline strategies.
- Integrate the optimizer into the project dashboard.

## 10. Conclusion

A first version of the SciPy budget allocation optimizer has been implemented and tested. It demonstrates how a constrained
