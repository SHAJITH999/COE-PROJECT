"""
FastAPI Application for Multi-Location Inventory Balancing Recommender.

Exposes existing Phase 3/4 business logic via REST endpoints.
Handles human approval, rejection, and override workflows with SQLite persistence.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import json
from datetime import datetime

import pandas as pd
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel

from src.data.loader import load_transfer_routes
from src.balancing.recommender import generate_recommendations
from src.metrics.baseline import (
    calculate_baseline_purchases,
    calculate_service_level,
    evaluate_forecast_quality,
)
from src.simulation.scenarios import create_scenario_datasets
from src.simulation.runner import run_single_scenario_experiment
from src.api.db import (
    init_db, seed_recommendations, record_decision,
    get_approval_status, get_all_approvals, is_high_impact, DB_PATH
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

app = FastAPI(
    title="Inventory Balancing Recommender API",
    description="Multi-Location Inventory Balancing & Transfer Recommender System",
    version="1.0.0"
)


# ── Pydantic Schemas ─────────────────────────────────────────────────────────

class RecommendRequest(BaseModel):
    scenario: str = "NORMAL"


class SimulateRequest(BaseModel):
    scenario: str  # NORMAL | DELAY | CAPACITY_LOSS | URGENT_DEMAND


class ApproveRequest(BaseModel):
    recommendation_id: str


class RejectRequest(BaseModel):
    recommendation_id: str


class OverrideRequest(BaseModel):
    recommendation_id: str
    override_reason: str


# ── Helpers ──────────────────────────────────────────────────────────────────

def _load_intelligence_df() -> pd.DataFrame:
    intel_path = PROCESSED_DATA_DIR / "inventory_intelligence.csv"
    if not intel_path.exists():
        raise HTTPException(status_code=503, detail="Inventory intelligence data not found. Run Phase 2 pipeline first.")
    return pd.read_csv(intel_path)


def _load_baseline_metrics() -> Optional[pd.DataFrame]:
    path = OUTPUTS_DIR / "baseline_metrics.csv"
    return pd.read_csv(path) if path.exists() else None


def _recs_to_list(recs_df: pd.DataFrame, include_approvals: bool = True) -> List[Dict]:
    records = recs_df.to_dict(orient="records")
    if include_approvals and DB_PATH.exists():
        for rec in records:
            rec_id = str(rec.get("Recommendation_ID", ""))
            approval = get_approval_status(rec_id)
            if approval:
                rec["Approval_Status"] = approval["status"]
                rec["Is_High_Impact"] = approval["is_high_impact"]
    return records


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Inventory Balancing Recommender API",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/recommend")
def recommend(req: RecommendRequest = Body(default=RecommendRequest())):
    """
    Generate transfer and purchase recommendations for a given scenario.
    Calls existing Phase 3 recommender engine without duplicating logic.
    """
    try:
        inv_df, routes_df = create_scenario_datasets(req.scenario)
        baseline_metrics = _load_baseline_metrics()
        recs_df, metrics_df = generate_recommendations(inv_df, routes_df, baseline_metrics)
        # Seed approval records in DB
        recs_list = recs_df.to_dict(orient="records")
        seed_recommendations(recs_list)
        return {
            "scenario": req.scenario,
            "total_recommendations": len(recs_df),
            "recommendations": _recs_to_list(recs_df),
            "metrics": metrics_df.to_dict(orient="records")
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {e}")


@app.post("/simulate")
def simulate(req: SimulateRequest):
    """
    Run baseline vs proposed experiment for a given disruption scenario.
    Reuses Phase 4 simulation runner logic.
    """
    valid_scenarios = ["NORMAL", "DELAY", "CAPACITY_LOSS", "URGENT_DEMAND"]
    if req.scenario.upper() not in valid_scenarios:
        raise HTTPException(status_code=400, detail=f"Invalid scenario. Must be one of: {valid_scenarios}")
    try:
        metrics, recs_df, rec_metrics_df = run_single_scenario_experiment(req.scenario.upper())
        return {
            "scenario": req.scenario.upper(),
            "experiment_metrics": metrics,
            "recommendation_metrics": rec_metrics_df.to_dict(orient="records")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {e}")


@app.get("/metrics")
def get_metrics():
    """Return baseline and recommender summary metrics."""
    baseline_path = OUTPUTS_DIR / "baseline_metrics.csv"
    rec_metrics_path = OUTPUTS_DIR / "recommendation_metrics.csv"
    experiment_path = OUTPUTS_DIR / "experiment_summary.csv"

    baseline_metrics = pd.read_csv(baseline_path).to_dict(orient="records") if baseline_path.exists() else []
    rec_metrics = pd.read_csv(rec_metrics_path).to_dict(orient="records") if rec_metrics_path.exists() else []
    experiment_summary = pd.read_csv(experiment_path).to_dict(orient="records") if experiment_path.exists() else []

    return {
        "baseline_metrics": baseline_metrics,
        "recommender_metrics": rec_metrics,
        "experiment_summary": experiment_summary
    }


@app.post("/approve")
def approve(req: ApproveRequest):
    """Approve a recommendation. Returns 404 if recommendation ID does not exist."""
    approval = get_approval_status(req.recommendation_id)
    if approval is None:
        raise HTTPException(status_code=404, detail=f"Recommendation '{req.recommendation_id}' not found.")
    if approval["is_high_impact"]:
        # High-impact: confirmation proceeds but flag is recorded in response
        pass
    updated = record_decision(req.recommendation_id, "APPROVED")
    if not updated:
        raise HTTPException(status_code=404, detail=f"Could not update recommendation '{req.recommendation_id}'.")
    return {
        "recommendation_id": req.recommendation_id,
        "status": "APPROVED",
        "is_high_impact": approval["is_high_impact"],
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/reject")
def reject(req: RejectRequest):
    """Reject a recommendation."""
    approval = get_approval_status(req.recommendation_id)
    if approval is None:
        raise HTTPException(status_code=404, detail=f"Recommendation '{req.recommendation_id}' not found.")
    record_decision(req.recommendation_id, "REJECTED")
    return {
        "recommendation_id": req.recommendation_id,
        "status": "REJECTED",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/override")
def override(req: OverrideRequest):
    """
    Override a recommendation with a mandatory override reason.
    Returns 400 if override_reason is empty.
    """
    if not req.override_reason or not req.override_reason.strip():
        raise HTTPException(status_code=400, detail="override_reason is required and cannot be empty.")
    approval = get_approval_status(req.recommendation_id)
    if approval is None:
        raise HTTPException(status_code=404, detail=f"Recommendation '{req.recommendation_id}' not found.")
    record_decision(req.recommendation_id, "OVERRIDDEN", override_reason=req.override_reason.strip())
    return {
        "recommendation_id": req.recommendation_id,
        "status": "OVERRIDDEN",
        "override_reason": req.override_reason.strip(),
        "timestamp": datetime.utcnow().isoformat()
    }
