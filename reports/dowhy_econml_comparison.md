
# DoWhy and EconML Comparison Report

## 1. Objective

The objective of this analysis is to compare the treatment-effect estimates obtained using DoWhy and EconML for evaluating Discount offers against BOGO offers.

Both models use:
- Treatment: `treatment_discount`
- Outcome: `outcome_completed`

## 2. DoWhy Analysis

### Methodology

- Framework: DoWhy
- Estimation method: Propensity Score Matching
- Estimator: `backdoor.propensity_score_matching`
- Confounders: Age, income, and gender
- Missing demographic records: Removed using complete-case filtering.

### Results

| Metric | Value |
|---|---:|
| Estimated treatment effect | 0.0909 |
| Effect in percentage points | +9.09 pp |

The estimated effect suggests a positive difference in completion probability for Discount offers relative to BOGO offers.

### Limitation

The placebo refutation test was skipped because the installed DoWhy version failed when the placebo treatment contained only one class.

The estimate is exploratory and may be affected by unmeasured confounding and repeated customer observations.

## 3. EconML Analysis

### Methodology

- Framework: EconML
- Estimator: SparseLinearDML
- Outcome model: Random Forest Regressor
- Treatment model: Random Forest Classifier
- Treatment: `treatment_discount`
- Outcome: `outcome_completed`
- Candidate features: Age, income, and gender
- Missing values: Median/mode imputation
- Validation split: GroupShuffleSplit by customer

### Results

| Metric | Value |
|---|---:|
| Total eligible records | 25,073 |
| Training records | 18,780 |
| Test records | 6,293 |
| Mean estimated effect | 0.0866 |
| Median estimated effect | 0.0858 |
| Standard deviation | 0.0352 |

The mean estimated treatment effect is approximately +8.66 percentage points.

These are exploratory model estimates and do not independently establish causal validity.

## 4. Comparison of DoWhy and EconML

| Component | DoWhy | EconML |
|---|---|---|
| Method | Propensity Score Matching | SparseLinearDML |
| Treatment | Discount vs BOGO | Discount vs BOGO |
| Outcome | Offer completion | Offer completion |
| Confounders/features | Age, income, gender | Age, income, gender |
| Missing data | Complete-case filtering | Imputation |
| Estimate | +9.09 pp | +8.66 pp |
| Output | Overall estimate | Individual test-record estimates |

## 5. Interpretation

Both approaches produce positive estimated treatment effects in favor of Discount offers.

The DoWhy estimate is approximately +9.09 percentage points, while the EconML mean estimate is approximately +8.66 percentage points.

The estimates are numerically close, with a difference of approximately 0.43 percentage points.

However, numerical agreement between two models does not prove that the estimates are unbiased or causal.

The models also use different missing-data strategies and estimation procedures. Their analysis samples and assumptions are therefore not identical.

## 6. Important Limitations

1. Unmeasured confounding may remain.
2. Repeated observations from the same customer may not be independent.
3. DoWhy uses complete-case filtering, while EconML uses imputation.
4. The placebo refutation test was not completed.
5. Model agreement does not establish causal validity.
6. Statistical uncertainty and sensitivity to modeling assumptions require further investigation.

## 7. Conclusion

Both DoWhy and EconML produced positive exploratory estimates for Discount offers relative to BOGO offers.

The results are consistent with the descriptive and within-customer findings observed in the project.

However, further validation is necessary before interpreting these estimates as confirmed causal effects.

The comparison provides complementary evidence from two causal machine-learning approaches and supports further investigation of dynamic pricing and offer allocation strategies.