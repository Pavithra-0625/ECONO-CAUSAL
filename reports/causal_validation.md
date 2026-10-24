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

## 9. Next Steps

- Review propensity-score overlap.
- Compare descriptive findings with initial DoWhy and EconML estimates.
- Document assumptions and limitations of the causal models.
- Develop a budget-allocation optimization component with explicit assumptions and tests.

## 10. Conclusion

The dataset contains 25,073 offer records from 14,808 unique customers. Discount offers have a higher observed completion rate than BOGO offers. Because many customers received multiple offers and unmeasured confounding may remain, further validation is required before drawing causal conclusions.
