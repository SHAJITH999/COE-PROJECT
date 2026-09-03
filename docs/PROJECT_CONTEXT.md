# Project Context: Multi-Location Inventory Balancing Recommender

## Project Objective
Develop a Multi-Location Inventory Balancing Recommender system for a multi-branch distributor to optimize stock distribution across branch locations prior to placing new purchase orders with suppliers.

## Problem Statement
A multi-branch distributor experiences stock shortages at certain branch locations while simultaneously holding surplus stock at others. The system must evaluate and recommend branch-to-branch inventory transfers while accounting for safety stock, transfer lead times, transfer costs, vehicle capacity limitations, service urgency levels, inter-branch fairness, network disruptions, and human approval workflows.

## Datasets
- `inventory_demand.csv`: Branch-level inventory positions, actual demand, forecast demand, safety stock, purchase costs, service urgency, and supplier lead times.
- `transfer_routes.csv`: Inter-branch transport network specs, distances, transfer times, transfer costs, vehicle capacities, and route status.
- `recommendations_sample.csv`: Ground-truth/reference recommendations covering transfer vs. purchase actions, quantities, costs, and approval statuses.

## Technology Stack
- **Python**: 3.13
- **Data Engineering**: Pandas, NumPy
- **Machine Learning / Optimization**: Scikit-learn
- **Backend API**: FastAPI, SQLite
- **User Interface**: Streamlit
- **Testing**: Pytest

## Six Project Phases
1. **Phase 1**: Foundation + Data Engineering (COMPLETE)
2. **Phase 2**: Baseline + Inventory Intelligence (COMPLETE)
3. **Phase 3**: Optimization & Recommender Engine (COMPLETE)
4. **Phase 4**: Safety + Fairness + Service + Disruption Experiments (COMPLETE)
5. **Phase 5**: FastAPI Service & Streamlit Dashboard
6. **Phase 6**: Evaluation, Benchmarking & Documentation

## Current Phase Details (Phase 4)
- **Safety Validation**: Strictly enforces 0 safety stock violations across all recommendations.
- **Fairness & Service**: Multi-objective priority hierarchy balancing safety, service urgency, route feasibility, cost/time, and donor contribution fairness.
- **Disruption Experiments**: Evaluated system performance under NORMAL, DELAY, CAPACITY_LOSS, and URGENT_DEMAND operating scenarios.
- **Experimental Findings**: Achieved **>60% shortage avoidance** and **>INR 500M cost savings** across all disruption scenarios while guaranteeing **0 safety violations**.

## Important Constraints
- Preserve raw datasets in `data/raw/` without modification.
- Maintain modular structure using `pathlib` for all file path operations.
- Do not implement logic for Phase 5 or beyond during Phase 4.
