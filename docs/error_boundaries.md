# Error Boundaries and Edge Cases

This document describes how the system safely handles operational edge cases and invalid conditions during inventory balancing. Each boundary acts to prevent unsafe or unfeasible transfers.

## 1. No Eligible Donor Surplus
**INPUT**: Destination branch reports a shortage, but no other branch in the network has surplus for the requested SKU.
**VALIDATION / DECISION**: The Recommender checks the `DonorPoolState` across all routes. Donor surplus is 0.
**VALID RESULT OR SAFE FAILURE**: `PURCHASE` fallback recommendation.
**EXPLANATION / ERROR**: The system outputs "No feasible network transfer can cover remaining shortage". The exact purchase quantity and cost are calculated for the required shortage.

## 2. Insufficient Donor Surplus
**INPUT**: Network surplus is non-zero, but strictly smaller than the destination's shortage.
**VALIDATION / DECISION**: Transfer quantity is clamped by `min(remaining_shortage, avail_surplus, capacity)`.
**VALID RESULT OR SAFE FAILURE**: `PARTIAL_TRANSFER` followed by `PARTIAL_TRANSFER_AND_PURCHASE`.
**EXPLANATION / ERROR**: The system transfers all available surplus to minimize cost, then routes the remainder as a purchase. Evidence clearly separates the transfer leg and the final purchase leg.

## 3. Donor Safety Stock Constraint
**INPUT**: A donor has physical inventory, but transferring it would drop their position below `Forecast_Demand + Safety_Stock`.
**VALIDATION / DECISION**: `avail_surplus` calculation subtracts both forecast and safety stock. Transfer cannot exceed this safe bound.
**VALID RESULT OR SAFE FAILURE**: Transfer is capped or completely rejected to protect the donor.
**EXPLANATION / ERROR**: "Safety stock protected". Secondary stockouts are strictly prevented.

## 4. Transfer Time Exceeds Urgency Limit
**INPUT**: Route transfer time is longer than the SLA limit imposed by the shortage's Service Urgency (e.g. Critical $\le$ 24h, High $\le$ 48h).
**VALIDATION / DECISION**: `is_route_feasible` checks `transfer_time <= max_hours`. Route is marked unfeasible.
**VALID RESULT OR SAFE FAILURE**: Route rejected; system evaluates next donor or falls back to `PURCHASE`.
**EXPLANATION / ERROR**: No recommendation generated for the rejected route. Final fallback explicitly cites "No feasible network transfer".

## 5. Insufficient Route Capacity
**INPUT**: Transporter/vehicle capacity on a route is smaller than the required transfer quantity.
**VALIDATION / DECISION**: Quantity is bounded by `Vehicle_Capacity` limit.
**VALID RESULT OR SAFE FAILURE**: Generates a `PARTIAL_TRANSFER` up to the capacity limit. The remaining shortage is either handled by another donor or routed to `PURCHASE`.
**EXPLANATION / ERROR**: Evidence specifies "capacity {limit} units".

## 6. Competing Shortages for Limited Surplus
**INPUT**: Multiple branches experience shortages for the same SKU on the same day, competing for a limited donor pool.
**VALIDATION / DECISION**: Recommender processes shortage records in order of Service Urgency (Critical -> Low).
**VALID RESULT OR SAFE FAILURE**: The branch with the higher urgency secures the transfer. The donor's pool state is deducted. Lower urgency branches fall back to `PURCHASE`.
**EXPLANATION / ERROR**: Ensures critical service disruptions are mitigated first before fulfilling low-priority internal balancing.

## 7. Disruption / Scenario Conditions
**INPUT**: The system is triggered with a disruption scenario like `DELAY` or `CAPACITY_LOSS`.
**VALIDATION / DECISION**: Scenario runner injects +3.0h to transfer times, or halves vehicle capacities, or scales critical demand.
**VALID RESULT OR SAFE FAILURE**: Recommender adapts automatically. If a route becomes too slow, it falls back to purchase. If capacity drops, it generates multiple partial transfers or purchases.
**EXPLANATION / ERROR**: Evaluated in `outputs/scenario_results.csv`, showing dynamic recalculation of transfer costs and purchase spikes under stress.
