# Multi-Location Inventory Balancing Recommender — Final Comprehensive Report

## 1. Executive Summary
This project implements an end-to-end **Multi-Location Inventory Balancing Recommender** for a multi-branch distributor operating across 8 branch locations and 10 product lines. By prioritizing inter-branch stock transfers prior to external purchases, the system avoids **25,600 shortage units (67.13%)** and reduces operating purchase expenses from **INR 836,298,974.13** (baseline) to **INR 270,257,614.70**, achieving net financial savings of **INR 566,041,359.43 (67.68%)** while guaranteeing **zero safety stock violations**.

## 2. Problem Statement
Multi-branch distributors frequently experience stock shortages at specific branch locations while holding surplus stock at nearby regional branches. Traditional operating models rely exclusively on external purchase orders, incurring high purchasing costs and long supplier lead times. The objective of this system is to rebalance inventory across branches before placing purchase orders, subject to safety stock limits, route feasibility, vehicle capacity, service urgency, fairness, network disruptions, and human approval.

## 3. Dataset Overview
- `inventory_demand.csv`: 7,200 records covering branch inventory positions, actual demand, forecast demand, safety stock, purchase costs, service urgency, and supplier lead times.
- `transfer_routes.csv`: 56 route legs detailing transit times, distances, unit transfer costs, vehicle capacities, and route availability statuses.
- `recommendations_sample.csv`: 52 reference recommendation cases.

## 4. System Architecture
Modular Python architecture built across 6 phases:
- Data Layer (`src/data/`): Data loading, schema validation, and inventory position processing.
- Metrics Layer (`src/metrics/`): Inventory status intelligence (`SHORTAGE`, `SURPLUS`, `BALANCED`), baseline purchasing engine, forecast quality evaluation (MAE, RMSE, MAPE).
- Recommender Core (`src/balancing/`): Deterministic donor ranking engine, safety stock validator, transfer feasibility checker.
- Simulation Core (`src/simulation/`): Disruption scenario generator (`NORMAL`, `DELAY`, `CAPACITY_LOSS`, `URGENT_DEMAND`), safety/fairness evaluation.
- Application Layer (`src/api/`, `dashboard/`): FastAPI REST API endpoints, Streamlit 4-page UI, SQLite human approval persistence.

## 5. Baseline Purchase Model (Phase 2)
The purchase-only baseline orders new inventory for all detected shortages without evaluating stock transfers.
- Baseline Shortage Units: 38,134.0
- Baseline Purchase Cost: INR 836,298,974.13
- Baseline Service Level: 81.92%
- Forecast Quality: MAE = 1.8679, RMSE = 2.7436, MAPE = 6.3258%

## 6. Transfer Recommender Engine (Phase 3)
Prioritizes inter-branch stock transfers before purchasing.
- Identifies matching donors on the same date for the same product.
- Ranks donors deterministically by:
  1. Transfer feasibility
  2. Shortest transfer time
  3. Lowest transfer cost per unit
  4. Greater available surplus
  5. Lexicographical branch ID.

## 7. Safety Validation (Phase 4)
Enforces the invariant: Donor Remaining Inventory $\ge \text{Forecast\_Demand} + \text{Safety\_Stock}$.
- All recommended transfers are capped or rejected if safety stock would be breached.
- **Safety Violations = 0** across all 3,780 transfer recommendations.

## 8. Fairness Balancing (Phase 4)
Tracks cumulative donor branch contributions (`Total_Units_Supplied` and `Transfers_Count`).
- Active Donor Utilization: **100.0%** (all 8 branch locations utilized as donors).

## 9. Service Urgency Prioritization (Phase 4)
Configurable priority hierarchy (`Critical` $\rightarrow$ `High` $\rightarrow$ `Medium` $\rightarrow$ `Low`) ensuring high-urgency shortages receive network donor stock first.

## 10. Disruption Scenarios (Phase 4)
Evaluated performance under 4 simulated operational conditions:
1. `NORMAL`: Unmodified baseline data.
2. `DELAY`: +3.0 hours transfer lead time across routes.
3. `CAPACITY_LOSS`: 50% vehicle capacity reduction across routes.
4. `URGENT_DEMAND`: +25% demand surge for Critical/High urgency items.

## 11. REST API Service (Phase 5)
FastAPI application exposing endpoints:
- `GET /health`
- `POST /recommend`
- `POST /simulate`
- `GET /metrics`
- `POST /approve`, `POST /reject`, `POST /override`

## 12. Streamlit Dashboard (Phase 5)
4-page web interface:
1. Network Overview (KPIs, inventory status, metrics summary)
2. Recommendations (filterable table with evidence & approval controls)
3. Disruption Simulation (interactive scenario launcher)
4. Experiment Results (comparative baseline vs. proposed graphs/tables)

## 13. Human Approval Workflow (Phase 5)
Tracks decisions (`PENDING`, `APPROVED`, `REJECTED`, `OVERRIDDEN`) in SQLite (`outputs/approvals.db`). Enforces mandatory `override_reason` text for overrides and flags high-impact recommendations.

## 14. Experimental Methodology
Evaluated baseline vs. proposed system across all 4 disruption scenarios measuring shortage avoided, purchase avoided, cost savings, service level improvement, and safety violations.

## 15. Results Summary
- **NORMAL**: Shortage Avoided = **67.13%**, Cost Savings = **INR 566.04M**, Service Level = **94.06%**, Safety Violations = **0**.
- **DELAY**: Shortage Avoided = **67.13%**, Cost Savings = **INR 566.04M**, Service Level = **94.06%**, Safety Violations = **0**.
- **CAPACITY_LOSS**: Shortage Avoided = **62.03%**, Cost Savings = **INR 523.45M**, Service Level = **93.13%**, Safety Violations = **0**.
- **URGENT_DEMAND**: Shortage Avoided = **60.09%**, Cost Savings = **INR 607.62M**, Service Level = **92.75%**, Safety Violations = **0**.

## 16. Error & Edge Case Analysis
Evaluated 7 error/edge cases including network surplus exhaustion, safety stock capping, route delay bounds, vehicle capacity capping, and competitive donor stock allocation (`outputs/error_analysis.csv` and `outputs/edge_case_results.csv`).

## 17. Stakeholder Prototype Validation
Conducted internal prototype review of 50 representative recommendation cases (`outputs/stakeholder_validation.csv`), achieving a **90.0% validation acceptance rate**.

## 18. Limitations
Documented in detail in [docs/limitations.md](docs/limitations.md). Key limits include static dataset scope, linear cost assumptions, simplified vehicle volumetric constraints, and prototype SQLite storage.

## 19. Conclusion
The system successfully proves that multi-location inventory balancing dramatically reduces purchasing costs (by >67%) and improves customer service levels (from 81.9% to >92%) while guaranteeing 100% safety stock compliance under severe network disruptions.

## 20. Future Improvements
- Integration with live ERP/WMS databases via Webhooks.
- Multi-period rolling horizon dynamic programming.
- Advanced volumetric fleet optimization (pallets/$m^3$).
- Machine learning demand forecast enhancement.
