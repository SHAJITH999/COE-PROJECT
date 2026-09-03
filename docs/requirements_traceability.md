# Requirements Traceability Matrix

This matrix maps every original project requirement to its implementation code, API/Dashboard evidence, validation method, and final verification status.

| Requirement | Implementation Module | Evidence File / API / UI | Validation Method | Status |
|---|---|---|---|---|
| **Transfer Before Purchase** | `src/balancing/recommender.py` | `outputs/transfer_recommendations.csv`, `POST /recommend` | Evaluated against baseline; 25,600 units transferred before purchase | **PASS** |
| **Multi-Location Balancing** | `src/balancing/donor_selector.py` | `outputs/fairness_metrics.csv`, Network Overview Dashboard | 8/8 branch locations actively balanced across network | **PASS** |
| **Safety Stock Protection** | `src/simulation/safety.py` | `outputs/safety_metrics.csv`, `validate_transfer_safety()` | Checked every transfer; zero safety stock violations recorded | **PASS** |
| **Service Urgency Prioritization** | `src/balancing/shortage_detector.py` | `tests/test_recommender.py`, Recommendations Page Filter | Urgency priority order (`Critical` $\rightarrow$ `High` $\rightarrow$ `Medium` $\rightarrow$ `Low`) enforced | **PASS** |
| **Fairness Balancing** | `src/simulation/fairness.py` | `outputs/fairness_metrics.csv`, Experiment Results Dashboard | Tracked units supplied; 100% active donor utilization | **PASS** |
| **Disruption Scenarios** | `src/simulation/scenarios.py` | `outputs/scenario_results.csv`, `POST /simulate` | Evaluated across `NORMAL`, `DELAY`, `CAPACITY_LOSS`, `URGENT_DEMAND` | **PASS** |
| **Baseline Benchmarking** | `src/metrics/baseline.py` | `outputs/baseline_metrics.csv`, `docs/baseline.md` | Calculated purchase-only baseline (INR 836.3M) reference | **PASS** |
| **Human Approval Workflow** | `src/api/db.py`, `src/api/app.py` | `outputs/approvals.db`, `POST /approve`, Recommendations UI | Human approval statuses (`PENDING`, `APPROVED`, `REJECTED`, `OVERRIDDEN`) | **PASS** |
| **Override Reason Capture** | `src/api/app.py`, `dashboard/app.py` | `POST /override`, Recommendations UI input box | Enforced non-empty override reason (HTTP 400 validation) | **PASS** |
| **High-Impact Policy** | `src/api/db.py` | `is_high_impact()`, Dashboard warning banner | Flagged Critical urgency / quantity $\ge 20$ / cost $\ge 50$k | **PASS** |
| **REST API** | `src/api/app.py` | `http://localhost:8000/docs` (Swagger UI) | Tested `/health`, `/recommend`, `/simulate`, `/metrics`, `/approve`, `/reject`, `/override` | **PASS** |
| **Interactive Dashboard** | `dashboard/app.py` | `http://localhost:8501` (Streamlit Dashboard) | Multi-page layout (Overview, Recommendations, Simulation, Results) | **PASS** |
| **Measurable Experiment** | `src/simulation/runner.py` | `outputs/experiment_summary.csv` | Measured Shortage Avoided %, Purchase Avoided %, Cost Savings | **PASS** |
| **Edge Case Handling** | `src/simulation/validation.py` | `outputs/edge_case_results.csv` | Evaluated 5 edge cases (No donor, Safety limit, Delay, Capacity, Surge) | **PASS** |
| **Error Analysis** | `src/simulation/validation.py` | `outputs/error_analysis.csv` | Documented 7 realistic failure/edge cases and resolutions | **PASS** |
| **Prototype Validation Dataset** | `src/simulation/validation.py` | `outputs/stakeholder_validation.csv` | Internal prototype review dataset (90.0% acceptance rate) | **PASS** |
| **Automated Testing Suite** | `tests/` | Pytest test execution logs | 56/56 unit tests passed cleanly | **PASS** |
