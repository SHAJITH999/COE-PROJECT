# System Limitations & Operational Boundary Conditions

## Executive Overview
This document honestly details the technical, operational, algorithmic, and infrastructure boundaries of the **Multi-Location Inventory Balancing Recommender**. The system is designed as an intelligent decision-support recommender for multi-branch distributors to prioritize internal inventory rebalancing before external procurement.

---

## 1. Dataset Limitations
- **Network Scope**: The dataset models an 8-branch regional network (`B001`–`B008` in Tamil Nadu, India) and 10 SKUs across Electronics, Appliances, and Networking. Enterprise supply chains typically encompass dozens of distribution centers, hundreds of retail branches, and tens of thousands of SKUs.
- **Time Horizon**: Covers a 90-day operational quarter (`2026-07-01` to `2026-09-28`). Seasonality patterns spanning multi-year macroeconomic cycles (e.g. monsoon effects, festival surges) are limited to the quarterly window.
- **Single-Echelon Architecture**: Balances stock strictly across peer retail/distribution branches without modeling intermediate regional cross-docks or central mother-warehouses.

---

## 2. Demand Forecasting Assumptions
- **Pre-computed Demand Signals**: `Forecast_Demand` and `Actual_Demand` are supplied in daily records. While the system evaluates forecast accuracy (MAE = 1.87, RMSE = 2.74, MAPE = 6.33%) and scales demand under disruption scenarios, it relies on upstream ERP demand engines rather than training custom neural or time-series models on raw sales receipts.
- **Stationarity**: Forecast errors assume roughly independent normal distributions without modeling promotional cannibalization or price elasticity.
- **Forecast Horizon**: 1-day ahead planning interval. Multi-echelon replenishment lead times exceeding supplier review intervals are handled via static safety stocks.

---

## 3. Disruption Scenarios (Synthetic Stress Testing)
- **Uniform Scaling**: Disruption scenarios (`DELAY` = +3.0h transit time, `CAPACITY_LOSS` = 50% vehicle capacity reduction, `URGENT_DEMAND` = +25% critical demand surge) apply uniform transformations across affected routes/SKUs. Real-world disruptions often manifest as localized bottlenecks (e.g. a specific highway closure or single-supplier plant shutdown).
- **Capacity Sizing**: In the current dataset, single-branch daily SKU shortages rarely exceed 50 units. Because baseline vehicle capacities are 100–300 units, a 50% capacity reduction still accommodates most single-transfer legs, preserving aggregate shortage avoidance (~67.13%). Capacity constraints become active when vehicle capacities drop below typical order sizes (verified in edge case tests).

---

## 4. Transfer Time & Logistics Assumptions
- **Static Route Matrix**: Transit lead times (`Transfer_Time_Hours`) and per-unit transfer costs are fixed per route pair. The system does not integrate real-time GPS, telematics, or live road congestion APIs.
- **Aggregate Capacity Metrics**: Vehicle capacity is modeled as total units without 3D cubing, volumetric weight ($kg/m^3$), pallet stacking constraints, or temperature-controlled cold-chain segregation.
- **Linear Transit Times**: Transfer times do not account for loading/unloading dock turnaround times or driver hours-of-service regulations.

---

## 5. Financial & Cost Assumptions
- **Linear Freight Costing**: Freight cost is modeled linearly as $\text{Quantity} \times \text{Cost\_Per\_Unit}$. It does not reflect tiered Less-Than-Truckload (LTL) vs. Full-Truckload (FTL) rate cards, demurrage charges, fuel escalators, or toll tariffs.
- **Constant Supplier Purchase Pricing**: Supplier unit purchase prices are assumed invariant to order volume (no volume tiered rebates or minimum order quantities [MOQs]).
- **Holding & Opportunity Costs**: The financial model compares freight cost vs. purchase cost. It does not model holding cost differentials or working capital interest on donor inventory.

---

## 6. Fairness Methodology
- **Cumulative Contribution Balancing**: Fairness is tracked via total units supplied and transfer counts per donor branch, breaking ties in favor of less-utilized donors.
- **Holding Equity**: Does not balance inventory carrying cost burdens across independently franchised branches.

---

## 7. Service Urgency Assumptions
- **Service Deadlines**: Categorized into 4 discrete buckets (`Critical` $\le$ 24h, `High` $\le$ 48h, `Medium` $\le$ 72h, `Low` $\le$ 96h). Customer-level contractual Service Level Agreements (SLAs) with penalty clauses are not modeled.

---

## 8. Human Approval & Governance
- **Local SQLite Persistence**: Approval decisions, override reasons, and audit trails are persisted in `outputs/approvals.db`. In production, this requires an enterprise ACID RDBMS (PostgreSQL, Oracle) with role-based access control (RBAC) and SSO.
- **Workflow Scope**: Human confirmation is triggered via UI/API rather than bi-directional enterprise ERP workflow webhooks (e.g. SAP IDoc, Oracle Fusion).

---

## 9. Real-World ERP Integration Requirements
To deploy in live operations, the following components must be built:
1. **ERP Connectors**: Automated ingestion from SAP/NetSuite/Dynamics inventory tables (`MARD`, `MARA`, `VBAP`).
2. **WMS Integration**: Automated generation of pick-pack-ship transfer orders and receiving Goods Receipts (GRN).
3. **Authentication**: OAuth2 / SAML single sign-on for audit accountability.
4. **Asynchronous Task Queue**: Celery / Redis queue for streaming live rebalancing recommendations.

---

## 10. Scalability & Computational Complexity
- **Optimized Deterministic Engine**: Candidate branch lookup is indexed $O(1)$ per `(Date, Product_ID)`, reducing pipeline runtime from >80 seconds to <2 seconds across 7,200 records.
- **Scalability Limit**: For ultra-large enterprise graphs (>10,000 locations, >100,000 SKUs), linear programming / mixed-integer linear programming (MILP solvers like HiGHS or Gurobi) or distributed PySpark graph execution is recommended.
