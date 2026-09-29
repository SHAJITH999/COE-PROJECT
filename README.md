# Multi-Location Inventory Balancing Recommender

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/pytest-67%20passed-brightgreen.svg)]()
[![Safety Invariant](https://img.shields.io/badge/safety%20violations-0-brightgreen.svg)]()
[![Shortage Avoidance](https://img.shields.io/badge/shortage%20avoided-67.13%25-blue.svg)]()
[![Modeled Savings](https://img.shields.io/badge/cost%20savings-INR%20566M+-success.svg)]()

A multi-location inventory balancing recommender system designed for multi-branch distributor networks. It identifies regional stock shortages and transferable surpluses, prioritizing internal inter-branch transfers before placing expensive external purchase orders with suppliers.

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Problem Statement](#2-problem-statement)
3. [Solution Architecture](#3-solution-architecture)
4. [System Architecture Diagram](#4-system-architecture-diagram)
5. [Repository Structure](#5-repository-structure)
6. [Dataset & Data Engineering](#6-dataset--data-engineering)
7. [Demand Forecasting Architecture](#7-demand-forecasting-architecture)
8. [Recommendation Algorithm](#8-recommendation-algorithm)
9. [Safety Stock Protection](#9-safety-stock-protection)
10. [Donor Fairness Methodology](#10-donor-fairness-methodology)
11. [Explainability & Evidence Generation](#11-explainability--evidence-generation)
12. [Human Approval & Audit Trail](#12-human-approval--audit-trail)
13. [REST API Service](#13-rest-api-service)
14. [Interactive Streamlit Dashboard](#14-interactive-streamlit-dashboard)
15. [Disruption Scenarios](#15-disruption-scenarios)
16. [Purchase-Only Baseline Model](#16-purchase-only-baseline-model)
17. [Experimental Results & Verification](#17-experimental-results--verification)
18. [Edge and Failure Cases](#18-edge-and-failure-cases)
19. [Testing & Verification](#19-testing--verification)
20. [Stakeholder Validation](#20-stakeholder-validation)
21. [System Limitations](#21-system-limitations)
22. [Installation Guide](#22-installation-guide)
23. [One-Command Pipeline Execution](#23-one-command-pipeline-execution)
24. [Manual Verification Commands](#24-manual-verification-commands)

---

## 1. Project Overview
In multi-branch distribution networks, branch locations frequently experience localized stockouts while sister branches hold idle transferable surplus. Traditional distribution systems handle localized shortages by issuing new external purchase orders to suppliers, triggering long procurement lead times (3–10 days) and unnecessary working capital expenditures.

The **Multi-Location Inventory Balancing Recommender** solves this by evaluating inter-branch transit feasibility, transportation costs, vehicle capacities, service urgency thresholds, donor safety stock floors, and network fairness to generate optimal lateral stock transfer recommendations.

---

## 2. Problem Statement
- **Fragmented Network Visibility**: Branch managers place siloed supplier purchase orders unaware of surplus in neighboring cities.
- **Uncontrolled Expedited Freight**: Emergency orders incur high unit costs and supplier expedite fees.
- **Secondary Stockout Risk**: Careless stock transfers risk compromising donor safety stock, inducing secondary downstream stockouts.
- **Governance Gaps**: Automated algorithms lack operator accountability and audit trails for manual overrides.

---

## 3. Solution Architecture
The system is built as a modular 7-tier pipeline:
1. **Data Engineering Layer**: Ingests, validates, cleans raw datasets, and calculates net inventory positions, shortages, and surpluses.
2. **Forecasting & Intelligence Layer**: Computes forecast quality metrics (MAE, RMSE, MAPE) and generates stock coverage ratios and demand gaps.
3. **Balancing & Recommender Engine**: Identifies candidate donors, verifies route constraints (time, cost, capacity, status), and produces deterministic transfer legs (`TRANSFER`) and purchase fallbacks (`PURCHASE` / `PARTIAL_TRANSFER_AND_PURCHASE`).
4. **Safety & Fairness Invariants**: Enforces that donor stock never breaches $\text{Forecast\_Demand} + \text{Safety\_Stock}$, and balances cumulative donor burdens.
5. **Human-in-the-Loop Governance**: SQLite-backed approval engine enforcing human confirmation for high-impact recommendations and mandatory justifications for overrides.
6. **API & Interface Layer**: FastAPI REST endpoints and an interactive Streamlit operations dashboard.
7. **Disruption Simulation & Experimentation**: Evaluates network resilience across four operational scenarios (`NORMAL`, `DELAY`, `CAPACITY_LOSS`, `URGENT_DEMAND`).

---

## 4. System Architecture Diagram

```
                 [ Raw Inventory Demand & Transfer Routes ]
                                     │
                                     ▼
                     [ Data Validation & Cleansing ]
                                     │
                  ┌──────────────────┴──────────────────┐
                  ▼                                     ▼
        [ Inventory Position ]               [ Demand Forecasting ]
    (Current + In - Reserved)              (MAE: 1.87, MAPE: 6.33%)
                  └──────────────────┬──────────────────┘
                                     ▼
                         [ Shortage & Surplus Gap ]
                                     │
                                     ▼
                        [ Donor Selection Engine ]
               ┌─────────────────────┼─────────────────────┐
               ▼                     ▼                     ▼
     [ Safety Invariant ]  [ Feasibility Matrix ]  [ Urgency & Fairness ]
    (Surplus > Fcast+SS)   (Time, Cost, Capacity)  (Critical -> Low)
               └─────────────────────┬─────────────────────┘
                                     │
                                     ▼
                       [ Recommender Allocation ]
              ┌──────────────────────┴──────────────────────┐
              ▼                                             ▼
     [ Transfer Leg (TRANSFER) ]             [ Purchase Fallback (PURCHASE) ]
              └──────────────────────┬──────────────────────┘
                                     │
                                     ▼
                       [ Human Approval & Audit ]
                   (Approve / Reject / Override + Reason)
                                     │
                    ┌────────────────┴────────────────┐
                    ▼                                 ▼
             [ FastAPI REST ]                [ Streamlit UI ]
             (Port: 8000)                    (Port: 8501)
```

---

## 5. Repository Structure
```
COE PROJECT/
├── .gitignore                      # Cleaned ignore rules (DBs, binaries, shortcuts)
├── README.md                       # Comprehensive system documentation
├── requirements.txt                # Production and testing dependencies
├── run_all.py                      # One-command complete reproducible pipeline
├── run_phase1.py                   # Data pipeline runner
├── run_phase2.py                   # Intelligence & baseline runner
├── run_phase3.py                   # Recommender engine runner
├── run_phase4.py                   # Disruption simulation runner
├── run_phase6.py                   # End-to-end validation runner
├── dashboard/
│   └── app.py                      # Streamlit 4-page interactive dashboard
├── data/
│   ├── raw/                        # Immutable raw datasets
│   │   ├── inventory_demand.csv
│   │   ├── recommendations_sample.csv
│   │   └── transfer_routes.csv
│   └── processed/                  # Generated intermediate datasets
│       ├── inventory_intelligence.csv
│       ├── inventory_processed.csv
│       └── routes_processed.csv
├── docs/                           # Architectural, experimental, and audit docs
│   ├── PROJECT_CONTEXT.md
│   ├── STATUS.md
│   ├── api.md
│   ├── baseline.md
│   ├── dashboard.md
│   ├── demo_script.md
│   ├── final_checklist.md
│   ├── final_report.md
│   ├── forecasting.md              # Traceability and forecasting architecture
│   ├── human_approval.md           # Governance and audit specification
│   ├── limitations.md              # Technical and operational boundary conditions
│   ├── phase4_experiment.md        # Verified reproducible experimental results
│   ├── requirements_traceability.md
│   └── stakeholder_validation.md   # Stakeholder validation protocol
├── outputs/                        # Pipeline outputs and audit records
│   ├── approvals.db                # SQLite human approval audit trail
│   ├── baseline_metrics.csv
│   ├── baseline_results.csv
│   ├── experiment_summary.csv      # Scenario comparison summary
│   ├── scenario_results.csv
│   ├── safety_metrics.csv
│   ├── fairness_metrics.csv
│   └── transfer_recommendations.csv
├── src/
│   ├── api/                        # REST API and SQLite governance
│   │   ├── app.py
│   │   └── db.py
│   ├── balancing/                  # Recommendation engine
│   │   ├── donor_selector.py       # Deterministic donor pool ranking
│   │   ├── recommender.py          # Core allocation algorithm
│   │   ├── shortage_detector.py    # Shortage detection logic
│   │   └── transfer_feasibility.py # Route feasibility constraints
│   ├── data/                       # Ingestion, validation, transformation
│   │   ├── loader.py
│   │   ├── pipeline.py
│   │   └── validator.py
│   ├── forecasting/                # Modular forecasting architecture
│   │   ├── features.py             # Demand gap and coverage ratios
│   │   ├── forecast.py             # Horizon and surge adjustments
│   │   └── validation.py           # MAE, RMSE, MAPE evaluations
│   ├── metrics/                    # Comparative analytics & baseline
│   │   ├── analysis.py
│   │   ├── baseline.py
│   │   └── intelligence.py
│   └── simulation/                 # Disruption experiment runners
│       ├── fairness.py
│       ├── runner.py
│       ├── safety.py
│       ├── scenarios.py
│       └── validation.py
└── tests/                          # 67 Automated unit and regression tests
    ├── test_api.py                 # API endpoints & approval governance (24 tests)
    ├── test_baseline.py            # Baseline purchase model & metrics (9 tests)
    ├── test_edge_cases.py          # 6 Mandatory operational edge cases (6 tests)
    ├── test_inventory.py           # Inventory position & shortages (8 tests)
    ├── test_recommender.py         # Allocation & constraint rules (10 tests)
    ├── test_simulation.py          # Disruption scenarios & fairness (5 tests)
    └── test_validation.py          # Validation pipeline checks (5 tests)
```

---

## 6. Dataset & Data Engineering
- **`inventory_demand.csv`**: 7,200 records across 8 branch locations (`B001`–`B008`) and 10 SKUs (`P001`–`P010`) covering 90 calendar days (`2026-07-01` to `2026-09-28`).
- **`transfer_routes.csv`**: 56 directed inter-branch transit routes with transit hours (1.6h–9.3h), unit transfer costs (INR 5.22–13.32), vehicle capacities (100–300 units), and availability status.

### Inventory Equations
$$\text{Inventory\_Position} = \text{Current\_Stock} + \text{Incoming\_Stock} - \text{Reserved\_Stock}$$
$$\text{Shortage\_Units} = \max(0, \text{Forecast\_Demand} + \text{Safety\_Stock} - \text{Inventory\_Position})$$
$$\text{Surplus\_Units} = \max(0, \text{Inventory\_Position} - \text{Forecast\_Demand} - \text{Safety\_Stock})$$

---

## 7. Demand Forecasting Architecture
Forecasting responsibilities are refactored into `src/forecasting/` to separate demand intelligence from inventory rebalancing:
- **Quality Metrics**: Evaluates historical demand accuracy across 7,200 observations:
  - **MAE**: **1.8679 units**
  - **RMSE**: **2.7436 units**
  - **MAPE**: **6.3258%**
- **Forecast Horizon**: 1-day ahead rolling operational rebalancing window.
- **Downstream Traceability**: Documented in [`docs/forecasting.md`](docs/forecasting.md).

---

## 8. Recommendation Algorithm
Shortages are resolved deterministically:
1. **Shortage Prioritization**: Shortages are processed in descending order of urgency (`Critical` $\rightarrow$ `High` $\rightarrow$ `Medium` $\rightarrow$ `Low`).
2. **Donor Candidate Filtering**: Identifies candidate branches with $\text{Surplus\_Units} > 0$ on the same observation date for the identical SKU.
3. **Route Feasibility Filtering**: Checks that route exists, is not disabled, vehicle capacity $> 0$, and transit time satisfies urgency deadlines ($\le 24\text{h}$ for Critical, $\le 48\text{h}$ for High, $\le 72\text{h}$ for Medium, $\le 96\text{h}$ for Low).
4. **Multi-Attribute Donor Ranking**:
   - Shortest transit time (`Transfer_Time_Hours`)
   - Lowest freight cost per unit (`Transfer_Cost_Per_Unit`)
   - Largest available surplus (`Available_Surplus`)
   - Lexicographical branch ID tie-breaker
5. **Transfer Leg Sizing**:
   $$\text{Transfer\_Quantity} = \min(\text{Remaining\_Shortage}, \text{Donor\_Surplus}, \text{Vehicle\_Capacity})$$
6. **Purchase Fallback**: If network surplus is exhausted, remaining shortage triggers a purchase order (`PARTIAL_TRANSFER_AND_PURCHASE` or `PURCHASE`).

---

## 9. Safety Stock Protection
- **Invariant**: A donor branch's inventory position must never drop below $\text{Forecast\_Demand} + \text{Safety\_Stock}$.
- **Result**: Zero safety violations across all 7,200 records in all four disruption scenarios ($\text{Safety\_Violations} = 0$).

---

## 10. Donor Fairness Methodology
To avoid overburdening a single geographically central donor branch:
- Cumulative transferred units and transfer frequency per branch are monitored via `src.simulation.fairness.FairnessTracker`.
- In baseline execution, all 8 branches (100.0%) actively contribute as donors, maintaining network load distribution.

---

## 11. Explainability & Evidence Generation
Every recommendation produces structured evidence detailing:
- **WHO**: Source and destination branches.
- **WHAT**: Product ID and recommended transfer quantity.
- **WHY**: Recipient shortage size and donor available surplus.
- **WHY THIS ROUTE**: Transit lead time, freight cost per unit, and route vehicle capacity.
- **SAFETY**: Explicit proof that donor safety stock remains protected.
- **COVERAGE**: Declares whether the transfer satisfies the shortage fully or partially.

---

## 12. Human Approval & Audit Trail
- **High-Impact Thresholds**: Flagged when urgency is `Critical`, transfer quantity $\ge 20$ units, or estimated cost $\ge \text{INR 50,000}$.
- **Decision Actions**:
  - `APPROVE`: Authorizes recommendation for execution.
  - `REJECT`: Declines recommendation; routes to local handling.
  - `OVERRIDE`: Modifies decision; **strictly requires a non-empty human justification string**.
- **Audit Persistence**: Stored in `outputs/approvals.db` with full original recommendation JSON, decision, override reason, and UTC timestamp.

---

## 13. REST API Service
Built with FastAPI. Start the server with:
```bash
uvicorn src.api.app:app --port 8000
```
Interactive Swagger UI: `http://localhost:8000/docs`

### Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health status and UTC timestamp |
| `GET` | `/metrics` | Baseline and recommender performance metrics |
| `POST` | `/recommend` | Generate recommendations for a scenario (`NORMAL`, `DELAY`, etc.) |
| `POST` | `/simulate` | Run baseline vs. proposed disruption experiment |
| `POST` | `/approve` | Approve a recommendation (checks high-impact flag) |
| `POST` | `/reject` | Reject a recommendation |
| `POST` | `/override` | Override a recommendation (**requires `override_reason`**) |

---

## 14. Interactive Streamlit Dashboard
Launch the dashboard:
```bash
streamlit run dashboard/app.py
```
Dashboard opens at: `http://localhost:8501`

### Pages
1. **Network Overview**: Network KPIs, shortage/surplus distribution, and financial summary.
2. **Recommendations**: Filterable recommendations with interactive **Approve**, **Reject**, and **Override** governance buttons.
3. **Disruption Simulation**: Live simulator for testing `DELAY`, `CAPACITY_LOSS`, and `URGENT_DEMAND`.
4. **Experiment Results**: Comparative performance metrics, safety metrics, and fairness tables.

---

## 15. Disruption Scenarios
The system is evaluated under 4 simulated operational environments:
1. **`NORMAL`**: Standard operating baseline conditions.
2. **`DELAY`**: +3.0 hours transit delay across all transportation routes.
3. **`CAPACITY_LOSS`**: 50% vehicle capacity reduction across all routes.
4. **`URGENT_DEMAND`**: +25% forecast demand surge on `Critical` and `High` urgency SKUs.

---

## 16. Purchase-Only Baseline Model
The benchmark against which the recommender is measured:
- Resolves all shortages strictly through external supplier purchase orders.
- Purchase quantity = $\text{Shortage\_Units}$.
- Incurs full purchase price, zero transfer utilization, and extended supplier lead times.

---

## 17. Experimental Results & Verification
All results below reflect **actual, verified, reproducible execution** from `python run_all.py`:

| Scenario | Baseline Shortage | Proposed Shortage | Shortage Avoided | Avoidance % | Baseline Cost (INR) | Proposed Cost (INR) | Net Savings (INR) | Service Level | Safety Violations |
|---|---|---|---|---|---|---|---|---|---|
| **NORMAL** | 38,134.0 | 12,534.0 | 25,600.0 | **67.13%** | 836,298,974.13 | 270,257,614.70 | **INR 566,041,359.43** | 0.9406 | **0** |
| **DELAY** | 38,134.0 | 12,534.0 | 25,600.0 | **67.13%** | 836,298,974.13 | 270,257,614.70 | **INR 566,041,359.43** | 0.9406 | **0** |
| **CAPACITY_LOSS** | 38,134.0 | 12,534.0 | 25,600.0 | **67.13%** | 836,298,974.13 | 270,257,614.70 | **INR 566,041,359.43** | 0.9406 | **0** |
| **URGENT_DEMAND** | 55,345.0 | 25,043.0 | 30,302.0 | **54.75%** | 1,212,468,916.20 | 543,087,980.12 | **INR 669,380,936.08** | 0.8902 | **0** |

---

## 18. Edge and Failure Cases
The recommender is hardened against 6 mandatory operational failure modes (verified in `tests/test_edge_cases.py`):
1. **No Network Surplus**: 0 units transferred; entire shortage gracefully falls back to purchase order with explicit evidence.
2. **Surplus Smaller Than Shortage**: Transfers partial surplus (e.g. 18 of 50 units); remainder (32 units) routed to purchase.
3. **Safety Stock Boundary**: Transfer strictly capped at safe available units; donor stock never breaches safety stock.
4. **Urgency Transfer-Time Limit**: Routes exceeding service deadline (e.g. 28h transit for 24h Critical SKU) are rejected.
5. **Vehicle Capacity Bottleneck**: Single transfer capped at vehicle limit (e.g. 25 units); balance scheduled for purchase.
6. **Competing Branches**: Higher urgency recipient (Critical) receives donor surplus first; lower urgency (Low) receives remainder.

---

## 19. Testing & Verification
The test suite consists of **67 automated tests** spanning all system modules:

```bash
$ pytest
============================== 67 passed, 1 warning in 14.25s ==============================
```

### Test Breakdown by Module
- `tests/test_api.py`: **24 passed** (FastAPI endpoints, HTTP codes, approval/rejection/override workflows, audit persistence)
- `tests/test_recommender.py`: **10 passed** (Full/partial transfer logic, capacity constraints, safety constraints)
- `tests/test_baseline.py`: **9 passed** (Purchase-only baseline calculations, service level, forecast metrics)
- `tests/test_inventory.py`: **8 passed** (Inventory positions, scalar/series shortage and surplus calculations)
- `tests/test_edge_cases.py`: **6 passed** (Explicit edge case tests: Cases 1 through 6)
- `tests/test_simulation.py`: **5 passed** (Scenario generation, safety violation invariants, fairness metrics)
- `tests/test_validation.py`: **5 passed** (Data validation pipeline, sample recommendation checks)

---

## 20. Stakeholder Validation
- **Automated Prototype Simulation**: **COMPLETED** (50 representative cases evaluated in `outputs/stakeholder_validation.csv` with 92.0% acceptance).
- **Live Human Stakeholder Review**: **PENDING MANUAL VERIFICATION** (Evaluation protocol and field questionnaire documented in [`docs/stakeholder_validation.md`](docs/stakeholder_validation.md)).

---

## 21. System Limitations
Detailed in [`docs/limitations.md`](docs/limitations.md):
- 8-branch regional scope (Tamil Nadu network).
- Pre-computed demand signals from upstream ERP.
- Linear freight and purchase cost modeling.
- Local SQLite audit storage (production requires PostgreSQL/Oracle).
- Single-period operational planning horizon (1-day step).

---

## 22. Installation Guide

### Prerequisites
- Python 3.10+ (tested on Python 3.13)
- pip

```bash
# 1. Clone repository
git clone <repo-url>
cd "COE PROJECT"

# 2. Install dependencies
pip install -r requirements.txt
```

---

## 23. One-Command Pipeline Execution
Execute the entire pipeline end-to-end with validation and the complete test suite:
```bash
python run_all.py
```

### Expected Output
```
============================================================
      COE INVENTORY BALANCING REBALANCING PIPELINE
============================================================
Working Directory: C:\COE PROJECT

[1/6] Data preparation ...................... PASS (0.26s)
[2/6] Forecasting & Intelligence ............ PASS (0.31s)
[3/6] Recommender ........................... PASS (0.85s)
[4/6] Simulation ............................ PASS (3.48s)
[5/6] Evaluation & Metrics .................. PASS (0.10s)
[6/6] Validation ............................ PASS (0.12s)

Running test suite...
67 passed, 1 warning in 14.25s

All tests passed in 15.61s.
============================================================
PIPELINE COMPLETED SUCCESSFULLY in 20.74s
============================================================
```

---

## 24. Manual Verification Commands

### Execute Individual Pipeline Phases
```bash
# Phase 1: Data Preparation & Validation
python run_phase1.py

# Phase 2: Demand Intelligence & Baseline Purchase Model
python run_phase2.py

# Phase 3: Transfer Recommender Engine
python run_phase3.py

# Phase 4: Disruption Simulation Experiments
python run_phase4.py

# Phase 6: Final Validation & Edge Case Reporting
python run_phase6.py
```

### Run Automated Tests
```bash
# Run complete test suite (67 tests)
pytest

# Run specific modules
pytest tests/test_edge_cases.py
pytest tests/test_api.py
pytest tests/test_recommender.py
```

### Launch Interactive Services
```bash
# Launch FastAPI backend service
uvicorn src.api.app:app --port 8000

# Launch Streamlit interactive dashboard
streamlit run dashboard/app.py
```
