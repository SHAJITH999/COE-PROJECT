# Demand Forecasting Architecture & Auditability Guide

## 1. Executive Summary
This document provides complete architectural traceability and auditability for demand forecasting within the **Multi-Location Inventory Balancing Recommender**. It traces how `Forecast_Demand` is sourced, calculated, evaluated, stored, and consumed by downstream inventory balancing engines.

---

## 2. Source Data
- **File**: `data/raw/inventory_demand.csv` (7,200 records across 8 distribution branches and 10 SKUs).
- **Temporal Granularity**: Daily operational records from `2026-07-01` to `2026-09-28` (90 planning days).
- **Core Demand Attributes**:
  - `Date`: Observation date (ISO 8601 `YYYY-MM-DD`).
  - `Branch_ID`: Receiving distributor branch location (`B001` to `B008`).
  - `Product_ID`: Stock Keeping Unit (`P001` to `P010`).
  - `Actual_Demand`: Historical fulfilled/observed customer orders for the period.
  - `Forecast_Demand`: Projected demand generated for the planning period.
  - `Safety_Stock`: Mandated buffer inventory floor.
  - `Service_Urgency`: SKU criticality classification (`Critical`, `High`, `Medium`, `Low`).

---

## 3. Forecast Definition & Calculation
`Forecast_Demand` represents the expected item demand for a specific SKU at a specific branch for a single 24-hour operational planning window.

### Mathematical Invariants
- `Forecast_Demand >= 0` for all records.
- Integer unit representation.

### Disruption Simulation (Demand Surge)
In operational stress testing (`URGENT_DEMAND` scenario), surge demand is simulated using `src.forecasting.forecast.scale_forecast_for_scenario`:
$$\text{Forecast\_Demand}_{\text{surge}} = \lfloor 1.25 \times \text{Forecast\_Demand}_{\text{baseline}} \rfloor \quad \forall \, \text{SKUs} \in \{\text{Critical}, \text{High}\}$$
This models an unexpected 25% demand acceleration in critical service lines.

---

## 4. Forecast Horizon
- **Planning Interval**: 1-day step (rolling operational rebalancing).
- **Total Historical Horizon**: 90 consecutive calendar days.
- **Decision Window**: Daily morning batch execution prior to supplier order cutoffs, enabling internal network balancing before external procurement.

---

## 5. Forecast Quality & Evaluation Metrics
Forecast accuracy is audited in `src/forecasting/validation.py` by comparing `Actual_Demand` ($A_t$) against `Forecast_Demand` ($F_t$):

1. **Mean Absolute Error (MAE)**:
   $$\text{MAE} = \frac{1}{N} \sum_{t=1}^N |A_t - F_t| = 1.8679 \text{ units}$$

2. **Root Mean Squared Error (RMSE)**:
   $$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{t=1}^N (A_t - F_t)^2} = 2.7436 \text{ units}$$

3. **Mean Absolute Percentage Error (MAPE)**:
   $$\text{MAPE} = \frac{100\%}{N_{\text{nz}}} \sum_{t: A_t > 0} \frac{|A_t - F_t|}{A_t} = 6.3258\%$$

Zero-demand actuals are safely filtered out to prevent division by zero.

---

## 6. Where `Forecast_Demand` is Stored
1. **Raw Stage**: `data/raw/inventory_demand.csv`
2. **Processed Stage**: `data/processed/inventory_processed.csv` (includes `Inventory_Position`, `Shortage_Units`, `Surplus_Units`)
3. **Intelligence Stage**: `data/processed/inventory_intelligence.csv` (includes `Stock_Coverage_Ratio`, `Demand_Gap`, `Safety_Stock_Gap`)
4. **Audit Metrics**: `outputs/forecast_metrics.csv`

---

## 7. Downstream Consumption by the Recommender
The recommender consumes `Forecast_Demand` through two strict mechanisms:

1. **Shortage Detection**:
   $$\text{Target Position} = \text{Forecast\_Demand} + \text{Safety\_Stock}$$
   $$\text{Shortage\_Units} = \max(0, \text{Target Position} - \text{Inventory\_Position})$$
   Any positive shortage triggers transfer evaluation.

2. **Donor Safety Stock Invariant**:
   A donor branch may ONLY transfer units that exceed its own forecast demand and safety stock buffer:
   $$\text{Surplus\_Units} = \max(0, \text{Inventory\_Position} - \text{Forecast\_Demand} - \text{Safety\_Stock})$$
   This guarantees that no stock transfer creates a secondary stockout at the donor branch.

3. **Coverage Ratio & Demand Gap**:
   - $\text{Stock\_Coverage\_Ratio} = \frac{\text{Inventory\_Position}}{\text{Forecast\_Demand}}$
   - $\text{Demand\_Gap} = \text{Forecast\_Demand} - \text{Inventory\_Position}$

---

## 8. Module Architecture (`src/forecasting/`)
- `__init__.py`: Package entry point and API exports.
- `forecast.py`: Forecast extraction, validation, horizon inspection, and scenario scaling.
- `validation.py`: MAE, RMSE, MAPE evaluation and bias calculations.
- `features.py`: Demand gap, stock coverage ratio, and safety stock gap metrics.

---

## 9. Limitations & Reproducibility
- **Stationarity Assumption**: Current baseline uses static historical-projected demand pairs; external macro disruptions (e.g. weather, economic shocks) require dynamic exogenous regressors.
- **Granularity**: 1-day batch horizon; real-time intraday demand adjustments require continuous streaming integration.
- **Reproducibility**: All calculations are 100% deterministic and reproducible via `python run_phase2.py` or `python run_all.py`.
