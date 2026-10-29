# Causal Validation Report — EconoCausal

## 1. Objective

To validate the treatment and outcome definitions, examine customer-level offer distribution, and identify important considerations for causal analysis of Starbucks promotional offers.

## 2. Dataset Overview

- Total offer records: 25,073
- Unique customers: 14,808
- BOGO offer records: 16,511
- Discount offer records: 8,562
- Records with full validity windows observed: 25,073

## 3. Treatment and Outcome Definitions

- **Treatment:** `treatment_discount`
  - 0 = BOGO offer
  - 1 = Discount offer
- **Outcome:** `outcome_completed`
  - 0 = Offer not completed
  - 1 = Offer completed

## 4. Descriptive Completion Results

| Offer Type | Not Completed | Completed | Completion Rate |
|---|---:|---:|---:|
| BOGO | 9,078 | 7,433 | 45.02% |
| Discount | 4,039 | 4,523 | 52.83% |

Discount offers have a completion rate approximately 7.81 percentage points higher than BOGO offers in this dataset.

This is a descriptive association and does not establish that discount offers cause higher completion.

## 5. Repeated Customer Offers

| Metric | Result |
|---|---:|
| Customers with one offer | 6,759 |
| Customers with two offers | 6,004 |
| Customers with three offers | 1,874 |
| Customers with four offers | 171 |
| Customers with multiple offers | 8,049 |
| Average offers per customer | 1.69 |
| Maximum offers per customer | 4 |

Approximately 54.4% of customers received multiple offers. Therefore, offer records from the same customer may be statistically dependent. Causal analysis should account for repeated customer observations where appropriate.

## 6. Initial Limitations

1. The completion-rate difference is descriptive and should not be interpreted as a confirmed causal effect.
2. Customer characteristics may not capture every factor influencing offer assignment and completion.
3. Repeated observations from the same customer may affect statistical uncertainty.
4. The validity-window check confirms that all 25,073 records meet the dataset's existing validity-window flag; it does not independently validate every aspect of outcome construction.
5. Additional checks are needed to assess treatment overlap, model assumptions, and the robustness of estimated effects.

The propensity-overlap diagnostic was run on 25,073 offer records.

BOGO records: 16,511

Discount records: 8,562

BOGO mean propensity score: 0.341

Discount mean propensity score: 0.342

Estimated common propensity-score range: 0.334–0.348

Records outside the common range: 1

The estimated propensity scores show substantial overlap between BOGO and discount offer records under the current model.
 ## 7. Propensity-Score Overlap Assessment

However, the propensity model uses a limited set of demographic characteristics. Overlap alone does not establish that treatment assignment is free from confounding or that the causal estimates are unbiased. Further model validation is required.

## 8. EconML Effect Estimate Summary

The existing EconML analysis produced 6,293 estimated treatment effects.

Metric

Estimated Value

Number of estimates

6,293

Mean estimated effect

0.0885

Median estimated effect

0.0968

Standard deviation

0.0333

Minimum estimated effect

-0.0413

Maximum estimated effect

0.1519

The mean estimated effect is approximately +8.85 percentage points, and the median is approximately +9.68 percentage points, assuming the effects are on the probability scale.

These estimates suggest a positive modeled effect of discount offers relative to BOGO offers. However, they are exploratory and do not prove causality. Unmeasured confounding, repeated customer observations, model assumptions, and statistical uncertainty may affect the results. Statistical significance has not been established by this summary alone.

## 9. Robustness Analysis

### 9.1 Within-Customer Comparison

Of 25,073 offer records from 14,808 unique customers, 4,059 customers received both BOGO and Discount offers.

- Discount completion rate higher: 1,027 customers
- BOGO completion rate higher: 585 customers
- Equal completion rates: 2,447 customers
- Mean within-customer difference: +9.73 percentage points
- Median within-customer difference: 0 percentage points

### 9.2 Paired Sign Test

Among the 1,612 customers with unequal completion rates, 1,027 favored Discount and 585 favored BOGO.

- Share favoring Discount among non-tied customers: 63.71%
- 95% confidence interval: 61.31%–66.06%
- Two-sided p-value: approximately 2.10 × 10^-28

This test indicates that positive and negative customer-level differences are not equally frequent. It does not establish a causal effect.

### 9.3 Equal-Offer-Count Comparison

A subset of 2,755 customers received equal numbers of BOGO and Discount offers.

- Discount completion rate higher: 616 customers
- BOGO completion rate higher: 325 customers
- Equal completion rates: 1,814 customers
- Mean within-customer difference: +10.53 percentage points
- Median within-customer difference: 0 percentage points

The positive mean difference remains in this subset. Equal offer counts do not control for offer timing, offer characteristics, exposure conditions, or unmeasured confounding.

### 9.4 Propensity-Score Overlap

The demographic propensity model showed substantial overlap between treatment groups, with a common range of approximately 0.334–0.348 and one record outside that range. Overlap is a diagnostic, not proof that treatment assignment is unconfounded.

### 9.5 Limitations and Remaining Work

- The DoWhy and EconML estimates are exploratory and depend on modeling assumptions.
- Repeated offers from the same customer may be dependent.
- Equal offer counts do not guarantee comparable exposure or timing.
- The paired sign test does not measure causal effect size.
- Further validation of confounding, treatment assignment, and model assumptions is required before making causal claims.

Remaining work includes reviewing model assumptions, documenting uncertainty, and preparing the final results dashboard.

## 10. Conclusion

The dataset contains 25,073 offer records from 14,808 unique customers. Discount offers have a higher observed completion rate than BOGO offers in the overall descriptive comparison. The within-customer analysis and equal-offer-count subset also show positive mean differences favoring Discount.

The paired sign test finds an imbalance between positive and negative customer-level differences among non-tied customers. However, these analyses do not establish that Discount offers cause higher completion. Differences in timing, offer exposure, repeated observations, and unmeasured confounding remain potential limitations. Further causal validation is required before drawing causal conclusions.
