# Module 1: Causal Inference Engine – Validation Report

## 1. Introduction

The objective of Module 1 is to estimate the causal effect of different promotional offers (BOGO and Discount) on customer offer completion using causal inference techniques.

The analysis uses Double Machine Learning (DML) with EconML and Propensity Score Matching (PSM) with DoWhy.

## 2. Dataset Description

The analysis uses the prepared Starbucks customer-offer dataset.

| Parameter | Value |
|---|---:|
| Eligible offer records | 25,073 |
| Unique customers | 14,808 |
| Treatment variable | treatment_discount |
| Outcome variable | outcome_completed |
| Confounders | Age, Income, Gender |
| Treatment 0 | BOGO |
| Treatment 1 | Discount |

The analysis retains records for which the complete offer validity window was observed.

DoWhy excludes records with missing confounder values, resulting in 21,861 records and 12,895 unique customers. EconML uses imputation and retains 25,073 records.

## 3. EconML – Double Machine Learning

LinearDML was implemented to estimate the treatment effect of Discount compared with BOGO.

### Results

| Metric | Result |
|---|---:|
| Training records | 18,780 |
| Testing records | 6,293 |
| Test customers | 3,702 |
| Estimated ATE | 0.0829 |
| 95% Confidence Interval | 0.0686 – 0.0972 |
| Median ITE | 0.0925 |
| ITE Standard Deviation | 0.0389 |
| Positive ITE customers | 3,589 |
| Negative ITE customers | 113 |

The estimated Average Treatment Effect (ATE) is approximately 8.29 percentage points.

Approximately 96.95% of the held-out customer estimates have positive individual treatment effects.

The individual treatment effects were saved in `outputs/econml_effect_estimates.csv`.

## 4. DoWhy – Propensity Score Matching

DoWhy was used to define the causal model and estimate the treatment effect using propensity score matching.

### Results

| Method | Estimated Effect |
|---|---:|
| DoWhy PSM | 0.0909 |
| Custom PSM ATT | 0.0788 |

The DoWhy estimate is approximately 9.09 percentage points, while the custom matching implementation estimates approximately 7.88 percentage points.

These estimates come from different matching implementations and should be interpreted separately.

## 5. Robustness and Refutation Diagnostics

Additional custom diagnostics were performed to examine the stability of the estimated effect.

| Diagnostic | Simulations | Mean Effect |
|---|---:|---:|
| Random common-cause test | 10 | 0.0884 |
| Data-subset test | 10 | 0.0904 |
| Placebo treatment test | 200 | 0.0011 |

### Placebo Test

The treatment assignment was randomly permuted 200 times.

- Mean placebo effect: 0.0011
- Standard deviation: 0.0116
- Empirical p-value: 0.005

The placebo estimates were close to zero compared with the original estimated effect.

**Note:** These are custom robustness diagnostics, not successful executions of DoWhy's native refutation methods. The random common-cause and subset tests used only 10 simulations each and are preliminary.

## 6. Propensity Score Overlap

A logistic regression model was used to estimate propensity scores based on demographic confounders.

The estimated average propensity scores were approximately:

- BOGO group: 0.341
- Discount group: 0.342

The common propensity-score range was approximately 0.334–0.348.

This indicates substantial overlap in the estimated scores, although overlap alone does not establish that all causal assumptions are satisfied.

## 7. Key Findings

1. LinearDML estimated an average treatment effect of approximately 8.29 percentage points.
2. DoWhy PSM estimated an effect of approximately 9.09 percentage points.
3. The custom PSM implementation estimated an ATT of approximately 7.88 percentage points.
4. Most held-out individual treatment-effect estimates were positive.
5. The placebo test produced effects close to zero on average.
6. Additional robustness checks showed estimates broadly close to the original DoWhy estimate.

## 8. Limitations

- The analysis uses age, income and gender as measured confounders.
- Unmeasured confounding may still affect the estimates.
- Propensity-score overlap does not prove causal identification.
- The custom matching implementation uses nearest-neighbour matching with replacement and does not apply a caliper restriction.
- The random common-cause and data-subset tests use only 10 simulations.
- The placebo test uses 200 permutations.
- The EconML preprocessing workflow should be further reviewed to ensure preprocessing is performed appropriately within cross-validation folds.

Therefore, the estimates should be interpreted under the stated assumptions rather than as definitive proof of causality.

## 9. Conclusion

Module 1 has implemented the main causal estimation workflow using EconML and DoWhy. Double Machine Learning, Propensity Score Matching, propensity-score overlap analysis and additional robustness diagnostics have been performed.

The results suggest a positive estimated effect of Discount offers compared with BOGO offers on offer completion.

Further validation of causal assumptions and robustness is required before using these estimates for business decisions or personalized discount optimization.

## 10. Output Files

- `outputs/econml_effect_estimates.csv`
- `outputs/dowhy_refutation_results.csv`

Key implementation scripts:

- `src/econml_analysis.py`
- `src/dowhy_analysis.py`
- `src/propensity_overlap.py`
