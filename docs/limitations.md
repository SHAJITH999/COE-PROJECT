# System Limitations & Boundary Conditions Report

## Executive Disclaimer
This system is an **academic/proof-of-concept prototype** designed to evaluate multi-location inventory balancing algorithms, safety stock constraints, disruption resilience, REST API integration, and human-in-the-loop approval workflows. **It is NOT certified for production deployment in enterprise ERP/WMS environments without further infrastructure development.**

---

## 1. Dataset & Scope Limitations
- **Static Historical Scope**: The dataset covers an 8-branch, 10-product distribution network over a single quarter (`2026-07-01` to `2026-09-28`). Real-world distributor networks often encompass hundreds of locations and thousands of active SKUs.
- **Synthetically Modeled Demand**: Demand and forecast figures are based on realistic synthetic data rather than live POS/ERP feeds.

## 2. Transportation & Logistics Assumptions
- **Static Route Characteristics**: Transit lead times (`Transfer_Time_Hours`) and cost per unit (`Transfer_Cost_Per_Unit`) are treated as fixed parameters per route leg (modified only during scenario simulations).
- **Simplified Vehicle Capacity**: Vehicle capacity is modeled as a total unit count limit per transfer leg without accounting for volumetric dimensions ($m^3$), weight limits ($kg$), pallet constraints, or cold-chain requirements.
- **No Live Fleet Tracking**: The system lacks real-time GPS or Telematics integration; route delays are evaluated via static scenario adjustments.

## 3. Financial & Cost Assumptions
- **Linear Transfer Pricing**: Freight transfer cost is modeled linearly as $\text{Quantity} \times \text{Cost\_Per\_Unit}$ without tier-based freight discounts, minimum load charges, or fuel surcharge escalations.
- **Unit Purchase Cost Invariance**: Unit purchase costs from external suppliers are assumed constant across order volumes.

## 4. Modeling & Algorithmic Simplifications
- **Fairness Metric Scope**: Fairness is evaluated via total donor units supplied and transfer counts across branch locations, rather than multi-attribute holding-cost equity or inventory depreciation risk.
- **Single-Period Optimization Horizon**: Recommendation decisions are generated deterministically per date without multi-period stochastic rolling-horizon optimization.

## 5. System Infrastructure Limitations
- **Local SQLite Audit Storage**: Approval and override audit trails are persisted in a local SQLite database (`outputs/approvals.db`) rather than an enterprise distributed database (e.g., PostgreSQL).
- **Manual Approval Workflow**: The human-in-the-loop workflow relies on manual operator decisions through the Streamlit UI or REST API rather than automated ERP workflow triggers.
