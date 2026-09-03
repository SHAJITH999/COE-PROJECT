# Purchase-Only Baseline Methodology & Specification

## Overview
The **Purchase-Only Baseline** models the traditional, simple operating strategy of a distributor facing multi-branch inventory imbalances. Under this strategy, any location experiencing an inventory shortage orders new inventory directly from external suppliers.

## Operational Strategy
- **Trigger**: When a branch's `Shortage_Units > 0`.
- **Action**: Place a purchase order for `Purchase_Quantity = Shortage_Units`.
- **No Stock Transfers**: Inter-branch transfers are completely ignored (`transfer_routes.csv` is not evaluated).

### Rationale for Excluding Transfers in Baseline
The baseline represents a benchmark strategy to evaluate the economic and operational value of introducing network stock balancing in later project phases. Ignoring transfers provides a clear upper-bound reference for purchasing costs and inventory investment against which optimization models can be benchmarked.

---

## Formulas & Calculation Logic

### 1. Inventory Position & Shortage
$$\text{Inventory\_Position} = \text{Current\_Stock} + \text{Incoming\_Stock} - \text{Reserved\_Stock}$$
$$\text{Shortage\_Units} = \max(0, \text{Forecast\_Demand} + \text{Safety\_Stock} - \text{Inventory\_Position})$$
$$\text{Surplus\_Units} = \max(0, \text{Inventory\_Position} - \text{Forecast\_Demand} - \text{Safety\_Stock})$$

### 2. Purchase Decision
$$\text{Purchase\_Quantity} = \begin{cases} \text{Shortage\_Units} & \text{if } \text{Shortage\_Units} > 0 \\ 0 & \text{otherwise} \end{cases}$$

$$\text{Purchase\_Cost} = \text{Purchase\_Quantity} \times \text{Purchase\_Cost\_Per\_Unit}$$

### 3. Service Level
$$\text{Service\_Level} = \text{clip}\left(1 - \frac{\sum \text{Shortage\_Units}}{\sum \text{Forecast\_Demand}}, 0.0, 1.0\right)$$

---

## Forecast Evaluation Metrics
The existing forecast demand column (`Forecast_Demand`) is evaluated against actual historical demand (`Actual_Demand`) using standard error metrics:

1. **Mean Absolute Error (MAE)**:
   $$\text{MAE} = \frac{1}{N} \sum_{i=1}^{N} | \text{Actual}_i - \text{Forecast}_i |$$

2. **Root Mean Squared Error (RMSE)**:
   $$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^{N} (\text{Actual}_i - \text{Forecast}_i)^2}$$

3. **Mean Absolute Percentage Error (MAPE)**:
   $$\text{MAPE} = \frac{100\%}{M} \sum_{i \in \{i \mid \text{Actual}_i \neq 0\}} \frac{| \text{Actual}_i - \text{Forecast}_i |}{\text{Actual}_i}$$
   *Zero-Handling Policy*: Records where $\text{Actual\_Demand} = 0$ are excluded from the MAPE calculation to prevent division-by-zero distortion.

---

## Baseline Limitations
1. **High Purchasing Expenses**: Ignores existing surplus stock sitting at nearby branch locations.
2. **Longer Lead Times**: Subject to full supplier lead times (`Supplier_Lead_Time_Days`) rather than faster inter-branch transit times.
3. **Imbalanced Network Stock**: Does not mitigate holding cost or obsolescence risk for surplus stock remaining at non-shortage branches.
