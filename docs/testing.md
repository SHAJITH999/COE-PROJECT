# Unit Test & Validation Documentation

This document describes the testing structure for the Multi-Location Inventory Balancing Recommender project.

## 1. Test Framework and Execution
The project uses **pytest** as its testing framework.
The test suite can be executed as a standalone process or as the final stage of the end-to-end pipeline (`run_all.py`).

**Command:**
```bash
pytest tests/ -v
```

The test suite consists of 68 tests that run automatically, validating core business rules, edge cases, and API functionality.

## 2. Test Modules and Coverage

### `test_api.py`
Validates the FastAPI implementation and human approval workflow.
- Database initialization and table creation
- API health and metric endpoints (`/health`, `/metrics`)
- Recommender simulation endpoints (`/recommend`, `/simulate`)
- Human approval endpoints (`/approve`, `/reject`, `/override`)
- Audit trail persistence and constraint validation (e.g., mandatory override reasons)
- Flagging of high-impact recommendations (large cost, quantity, or critical urgency)

### `test_baseline.py`
Validates the purchase-only baseline engine and forecast evaluation metrics.
- Consistency of calculated shortage and surplus limits
- Accurate calculation of required purchase quantity and total purchase cost
- Service level calculations
- Forecasting metrics: MAE, RMSE, and zero-demand handling in MAPE

### `test_edge_cases.py`
Ensures error boundaries and constraints operate correctly under restrictive situations.
- **Edge Case 1:** No network surplus available
- **Edge Case 2:** Donor surplus is smaller than the shortage
- **Edge Case 3:** Donor safety stock protection (stock cannot drop below safety levels)
- **Edge Case 4:** Transfer time exceeds the urgency-based time limit
- **Edge Case 5:** Vehicle capacity is smaller than the required shortage
- **Edge Case 6:** Competing branches prioritizing transfers based on service urgency

### `test_inventory.py`
Validates the underlying data processing pipeline logic.
- Scalar and Series logic for inventory position calculations
- Shortage and surplus unit formulas (ensuring zero-floored outputs)
- Mutual exclusivity of shortages and surpluses on the same item/branch
- Overall data processing pipeline integrity

### `test_recommender.py`
Validates the core recommendation classification and donor selection logic.
- Full shortage fulfillment yielding `TRANSFER`
- Partial fulfillment scenarios yielding `PARTIAL_TRANSFER`
- Insufficient inventory forcing a `PARTIAL_TRANSFER_AND_PURCHASE` fallback
- Multi-leg partial transfers completing without purchase
- Safety stock and capacity constraints

### `test_simulation.py`
Validates phase 4 disruption scenario simulations.
- Scenario manipulations (e.g., `URGENT_DEMAND` surge scaling, `DELAY` additions)
- Route capacity capping limits
- Enforcement of supply constraints and bounds during simulation

### `test_validation.py`
Validates the generation of metrics, limits, and final internal testing outcomes.
- Evaluates prototype validation logic against test thresholds and mock data checks

## 3. Real Test Results
- **Tests Executed:** 68 tests across 7 modules.
- **Result:** **100% PASS** with no failures. All core rules and API workflows are verified by automated testing.
