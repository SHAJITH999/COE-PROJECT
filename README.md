# Multi-Location Inventory Balancing Recommender

A multi-branch inventory rebalancing system that recommends inter-branch stock transfers before new purchases, with safety stock protection, service urgency prioritization, donor fairness evaluation, disruption experiment simulation, a REST API, and an interactive human approval dashboard.

---

## Installation

```bash
pip install -r requirements.txt
```

---

## Running the Pipelines

```bash
# Phase 1: Data Engineering
python run_phase1.py

# Phase 2: Baseline + Inventory Intelligence
python run_phase2.py

# Phase 3: Transfer Recommender
python run_phase3.py

# Phase 4: Disruption Experiments
python run_phase4.py
```

---

## Running the API

```bash
uvicorn src.api.app:app --reload --port 8000
```

API documentation (Swagger UI): `http://localhost:8000/docs`

---

## Running the Dashboard

```bash
streamlit run dashboard/app.py
```

Dashboard opens at: `http://localhost:8501`

---

## Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific phase tests
python -m pytest tests/test_inventory.py
python -m pytest tests/test_baseline.py
python -m pytest tests/test_recommender.py
python -m pytest tests/test_simulation.py
python -m pytest tests/test_api.py
```

---

## Project Documentation

| Document | Description |
|---|---|
| [docs/PROJECT_CONTEXT.md](docs/PROJECT_CONTEXT.md) | Project overview and phase roadmap |
| [docs/STATUS.md](docs/STATUS.md) | Phase completion status |
| [docs/baseline.md](docs/baseline.md) | Purchase-only baseline methodology |
| [docs/phase4_experiment.md](docs/phase4_experiment.md) | Disruption experiment specs and results |
| [docs/api.md](docs/api.md) | REST API reference |
| [docs/dashboard.md](docs/dashboard.md) | Streamlit dashboard user guide |
| [docs/human_approval.md](docs/human_approval.md) | Human approval workflow and audit trail |
