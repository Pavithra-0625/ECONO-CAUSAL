
# Within-Customer Robustness Analysis

## 1. Objective

To compare BOGO and Discount offer completion rates among customers who received both offer types, and to examine whether the observed difference remains among customers who received equal numbers of each offer type.

## 2. Dataset

- Total offer records: 25,073
- Unique customers: 14,808
- Customers receiving both BOGO and Discount offers: 4,059
- Customers receiving equal numbers of both offer types: 2,755

## 3. Results

### 3.1 All Customers Receiving Both Offer Types

| Comparison | Number of customers |
|---|---:|
| Discount completion rate higher | 1,027 |
| BOGO completion rate higher | 585 |
| Equal completion rates | 2,447 |
| Total | 4,059 |

The mean within-customer difference in completion rates was +9.73 percentage points in favor of Discount. The median difference was 0 percentage points.

### 3.2 Customers With Equal Offer Counts

| Comparison | Number of customers |
|---|---:|
| Discount completion rate higher | 616 |
| BOGO completion rate higher | 325 |
| Equal completion rates | 1,814 |
| Total | 2,755 |

The mean within-customer difference was +10.53 percentage points in favor of Discount. The median difference was 0 percentage points.

### 3.3 Paired Sign Test

For the 1,612 customers with unequal completion rates:

- Customers favoring Discount: 1,027
- Customers favoring BOGO: 585
- Share favoring Discount: 63.71%
- 95% confidence interval: 61.31%–66.06%
- Two-sided p-value: approximately 2.10 × 10⁻²⁸

The sign test indicates that positive and negative customer-level differences are not equally frequent among customers with unequal rates.

## 4. Interpretation

The observed within-customer comparison favors Discount offers on average. The mean difference remains positive when restricting the analysis to customers who received equal numbers of BOGO and Discount offers.

However, the median difference is zero in both analyses, indicating that many customers have equal observed completion rates. The equal-count restriction reduces one source of imbalance but does not control for offer timing, offer characteristics, exposure conditions, or other confounding factors.

## 5. Limitations

1. Customers may receive offers at different times and under different conditions.
2. Equal offer counts do not guarantee comparable offer exposure.
3. Repeated observations from the same customer may be dependent.
4. The paired sign test evaluates the balance of positive and negative differences; it does not establish a causal effect.
5. These results should be treated as exploratory evidence rather than proof that Discount offers cause higher completion.

## 6. Conclusion

The within-customer and equal-offer-count comparisons show a positive mean completion-rate difference for Discount offers. Further validation is needed to account for offer timing, exposure differences, and potential confounding before making causal claims.
