# Phase 4 Experimental Specification & Disruption Evaluation Report

## Overview
Phase 4 evaluates the **Multi-Location Inventory Balancing Recommender** across four distinct operational scenarios to measure decision safety, service urgency prioritization, donor contribution fairness, and resilience under transportation network disruptions.

---

## Decision Priority & Multi-Objective Hierarchy

When allocating stock transfers across the distribution network, decisions adhere strictly to the following priority hierarchy:

$$\text{Safety Stock Protection} \longrightarrow \text{Service Urgency} \longrightarrow \text{Route Feasibility} \longrightarrow \text{Cost \& Lead Time} \longrightarrow \text{Fairness Tie-Breaking}$$

1. **Safety Stock Protection**: A donor branch's inventory position must never drop below $\text{Forecast\_Demand} + \text{Safety\_Stock}$.
2. **Service Urgency**: Recipient shortages are processed in order of urgency (`Critical` $\rightarrow$ `High` $\rightarrow$ `Medium` $\rightarrow$ `Low`).
3. **Route Feasibility**: Transfers must utilize active routes (`Route_Status` $\neq$ `Unavailable`) with sufficient `Vehicle_Capacity` and compliant `Transfer_Time_Hours`.
4. **Cost & Lead Time**: Prioritizes routes with lower transfer times and lower freight costs per unit.
5. **Fairness**: Tie-breaking mechanism preferring feasible donors with lower prior contribution counts.

---

## Disruption Scenario Definitions

1. **`NORMAL`**: Standard operating conditions using baseline inventory demand and route data.
2. **`DELAY`**: Models network congestion by increasing transit lead times by +3.0 hours on all inter-branch routes.
3. **`CAPACITY_LOSS`**: Models fleet reduction or vehicle availability constraints by reducing vehicle capacity by 50% across all routes.
4. **`URGENT_DEMAND`**: Models demand surges by scaling forecast demand by +25% for `Critical` and `High` service urgency SKUs.

---

## Experimental Evaluation Metrics

- **Shortage Avoided (%)**:
  $$\text{Shortage Avoided \%} = \frac{\text{Baseline Shortage} - \text{Proposed Shortage}}{\text{Baseline Shortage}} \times 100\%$$

- **Purchase Avoided (%)**:
  $$\text{Purchase Avoided \%} = \frac{\text{Baseline Purchase Qty} - \text{Proposed Purchase Qty}}{\text{Baseline Purchase Qty}} \times 100\%$$

- **Cost Difference (Savings)**:
  $$\text{Cost Difference} = \text{Baseline Purchase Cost} - \text{Proposed Total Operating Cost}$$

- **Service Level Improvement**:
  $$\text{Service Improvement} = \text{Proposed Service Level} - \text{Baseline Service Level}$$

- **Safety Violations**: Enforced strictly at $\mathbf{0}$.

---

## Experimental Results Summary

The table below summarizes experimental findings across all four scenarios:

| Scenario | Baseline Shortage | Proposed Shortage | Shortage Avoided (%) | Baseline Cost (INR) | Proposed Cost (INR) | Net Savings (INR) | Baseline Service Level | Proposed Service Level | Safety Violations |
|---|---|---|---|---|---|---|---|---|---|
| **NORMAL** | 38,134.0 | 12,534.0 | **67.13%** | 836,298,974.13 | 270,257,614.70 | **INR 566,041,359.43** | 0.8192 | **0.9406** | **0** |
| **DELAY** | 38,134.0 | 12,534.0 | **67.13%** | 836,298,974.13 | 270,257,614.70 | **INR 566,041,359.43** | 0.8192 | **0.9406** | **0** |
| **CAPACITY_LOSS** | 38,134.0 | 14,482.0 | **62.03%** | 836,298,974.13 | 312,852,709.80 | **INR 523,446,264.33** | 0.8192 | **0.9313** | **0** |
| **URGENT_DEMAND** | 45,959.0 | 18,344.0 | **60.09%** | 1,006,206,750.38 | 398,591,010.50 | **INR 607,615,739.88** | 0.8184 | **0.9275** | **0** |

---

## Key Findings & Limitations
1. **Safety Guarantee**: Across all scenarios, zero safety stock violations occurred ($\text{Safety\_Violations} = 0$).
2. **Resilience**: The system maintains robust shortage avoidance ($>60\%$) and cost savings ($>\text{INR 500M}$) even under 50% vehicle capacity loss and 25% demand surges.
3. **Limitations**: Route disruption scenarios currently apply uniform scaling; future work in Phase 5/6 can evaluate dynamic real-time traffic delays per route.
