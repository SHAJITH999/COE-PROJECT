"""
Unit tests for Phase 5: FastAPI endpoints and Human Approval Workflow.
"""

import json
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.db import (
    init_db, seed_recommendations, record_decision,
    get_approval_status, get_all_approvals, is_high_impact
)


# ─── Isolated DB fixture ──────────────────────────────────────────────────────
@pytest.fixture
def tmp_db(tmp_path):
    """Provide a fresh temporary DB path for each test."""
    return tmp_path / "test_approvals.db"


# ─── DB / Approval logic tests (no API server needed) ─────────────────────────

def test_init_db_creates_table(tmp_db):
    """init_db must create the approvals table."""
    init_db(tmp_db)
    assert tmp_db.exists()


def test_seed_and_get_status(tmp_db):
    """Seeded recommendations must have PENDING status."""
    init_db(tmp_db)
    seed_recommendations([{"Recommendation_ID": "REC00001", "Service_Urgency": "Low",
                            "Recommended_Quantity": 5, "Estimated_Cost": 100.0}], db_path=tmp_db)
    rec = get_approval_status("REC00001", db_path=tmp_db)
    assert rec is not None
    assert rec["status"] == "PENDING"


def test_approve_recommendation(tmp_db):
    """Approving a recommendation must change its status to APPROVED."""
    init_db(tmp_db)
    seed_recommendations([{"Recommendation_ID": "REC00002", "Service_Urgency": "Low",
                            "Recommended_Quantity": 3, "Estimated_Cost": 50.0}], db_path=tmp_db)
    result = record_decision("REC00002", "APPROVED", db_path=tmp_db)
    assert result is True
    rec = get_approval_status("REC00002", db_path=tmp_db)
    assert rec["status"] == "APPROVED"


def test_reject_recommendation(tmp_db):
    """Rejecting a recommendation must change its status to REJECTED."""
    init_db(tmp_db)
    seed_recommendations([{"Recommendation_ID": "REC00003", "Service_Urgency": "Low",
                            "Recommended_Quantity": 3, "Estimated_Cost": 50.0}], db_path=tmp_db)
    record_decision("REC00003", "REJECTED", db_path=tmp_db)
    rec = get_approval_status("REC00003", db_path=tmp_db)
    assert rec["status"] == "REJECTED"


def test_override_with_reason(tmp_db):
    """Override must persist the override reason."""
    init_db(tmp_db)
    seed_recommendations([{"Recommendation_ID": "REC00004", "Service_Urgency": "Low",
                            "Recommended_Quantity": 3, "Estimated_Cost": 50.0}], db_path=tmp_db)
    record_decision("REC00004", "OVERRIDDEN", override_reason="Manual adjustment", db_path=tmp_db)
    rec = get_approval_status("REC00004", db_path=tmp_db)
    assert rec["status"] == "OVERRIDDEN"
    assert rec["override_reason"] == "Manual adjustment"


def test_invalid_recommendation_id_returns_none(tmp_db):
    """Non-existent recommendation ID must return None."""
    init_db(tmp_db)
    rec = get_approval_status("DOES_NOT_EXIST", db_path=tmp_db)
    assert rec is None


def test_high_impact_critical_urgency():
    """Critical urgency recommendations must be flagged as high-impact."""
    rec = {"Service_Urgency": "Critical", "Recommended_Quantity": 5, "Estimated_Cost": 100.0}
    assert is_high_impact(rec) is True


def test_high_impact_large_quantity():
    """Recommendations with quantity >= threshold must be flagged high-impact."""
    rec = {"Service_Urgency": "Low", "Recommended_Quantity": 100, "Estimated_Cost": 100.0}
    assert is_high_impact(rec) is True


def test_high_impact_large_cost():
    """Recommendations with cost >= threshold must be flagged high-impact."""
    rec = {"Service_Urgency": "Low", "Recommended_Quantity": 3, "Estimated_Cost": 100000.0}
    assert is_high_impact(rec) is True


def test_low_impact_recommendation_not_flagged():
    """Low-risk recommendations must NOT be flagged high-impact."""
    rec = {"Service_Urgency": "Low", "Recommended_Quantity": 3, "Estimated_Cost": 100.0}
    assert is_high_impact(rec) is False


# ─── FastAPI TestClient tests ─────────────────────────────────────────────────
@pytest.fixture(scope="module")
def api_client():
    """Create a FastAPI TestClient for endpoint testing."""
    from src.api.app import app
    with TestClient(app) as client:
        yield client


def test_health_endpoint(api_client):
    """GET /health must return 200 with healthy status."""
    response = api_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_metrics_endpoint(api_client):
    """GET /metrics must return 200 with valid metric keys."""
    response = api_client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "baseline_metrics" in data
    assert "recommender_metrics" in data
    assert "experiment_summary" in data


def test_recommend_endpoint_normal(api_client):
    """POST /recommend must return 200 with recommendations list."""
    response = api_client.post("/recommend", json={"scenario": "NORMAL"})
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data
    assert "total_recommendations" in data
    assert isinstance(data["recommendations"], list)


def test_simulate_endpoint(api_client):
    """POST /simulate must return 200 with experiment metrics."""
    response = api_client.post("/simulate", json={"scenario": "DELAY"})
    assert response.status_code == 200
    data = response.json()
    assert "experiment_metrics" in data
    assert data["scenario"] == "DELAY"


def test_simulate_invalid_scenario(api_client):
    """POST /simulate with unknown scenario must return 400."""
    response = api_client.post("/simulate", json={"scenario": "INVALID_SCENARIO"})
    assert response.status_code == 400


def test_approve_endpoint(api_client):
    """POST /approve must return 200 for a valid seeded recommendation."""
    # First generate recommendations to seed DB
    api_client.post("/recommend", json={"scenario": "NORMAL"})
    # Fetch any rec ID from the DB
    from src.api.db import get_all_approvals
    all_recs = get_all_approvals()
    if not all_recs:
        pytest.skip("No recommendations seeded — run pipeline first.")
    rec_id = all_recs[0]["recommendation_id"]
    response = api_client.post("/approve", json={"recommendation_id": rec_id})
    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"


def test_reject_endpoint(api_client):
    """POST /reject must return 200 for a valid recommendation."""
    from src.api.db import get_all_approvals
    all_recs = get_all_approvals()
    if len(all_recs) < 2:
        pytest.skip("Not enough recommendations seeded.")
    rec_id = all_recs[1]["recommendation_id"]
    response = api_client.post("/reject", json={"recommendation_id": rec_id})
    assert response.status_code == 200
    assert response.json()["status"] == "REJECTED"


def test_override_endpoint_with_reason(api_client):
    """POST /override with reason must return 200."""
    from src.api.db import get_all_approvals
    all_recs = get_all_approvals()
    if len(all_recs) < 3:
        pytest.skip("Not enough recommendations seeded.")
    rec_id = all_recs[2]["recommendation_id"]
    response = api_client.post("/override", json={
        "recommendation_id": rec_id,
        "override_reason": "Seasonal adjustment required"
    })
    assert response.status_code == 200
    assert response.json()["status"] == "OVERRIDDEN"


def test_override_endpoint_empty_reason(api_client):
    """POST /override with empty reason must return 400."""
    from src.api.db import get_all_approvals
    all_recs = get_all_approvals()
    if not all_recs:
        pytest.skip("No recommendations seeded.")
    rec_id = all_recs[0]["recommendation_id"]
    response = api_client.post("/override", json={
        "recommendation_id": rec_id,
        "override_reason": ""
    })
    assert response.status_code == 400


def test_approve_invalid_id(api_client):
    """POST /approve with non-existent ID must return 404."""
    response = api_client.post("/approve", json={"recommendation_id": "INVALID_ID_XYZ"})
    assert response.status_code == 404


def test_reject_invalid_id(api_client):
    """POST /reject with non-existent ID must return 404."""
    response = api_client.post("/reject", json={"recommendation_id": "INVALID_ID_XYZ"})
    assert response.status_code == 404


def test_override_invalid_id(api_client):
    """POST /override with non-existent ID must return 404."""
    response = api_client.post("/override", json={
        "recommendation_id": "INVALID_ID_XYZ",
        "override_reason": "Testing invalid ID"
    })
    assert response.status_code == 404


def test_recommend_invalid_scenario(api_client):
    """POST /recommend with unknown scenario must return 400."""
    response = api_client.post("/recommend", json={"scenario": "INVALID_SCENARIO_123"})
    assert response.status_code == 400


def test_audit_trail_retrieval_and_preservation(tmp_db):
    """Verify original recommendation and decision audit trail are fully preserved."""
    init_db(tmp_db)
    original_rec = {
        "Recommendation_ID": "REC_AUDIT_01",
        "Source_Branch": "B001",
        "Destination_Branch": "B002",
        "Product_ID": "P001",
        "Recommended_Quantity": 25.0,
        "Estimated_Cost": 350.0,
        "Service_Urgency": "High"
    }
    seed_recommendations([original_rec], db_path=tmp_db)
    
    # 1. Check initial pending status
    status_before = get_approval_status("REC_AUDIT_01", db_path=tmp_db)
    assert status_before is not None
    assert status_before["status"] == "PENDING"
    assert status_before["is_high_impact"] is True  # Quantity >= 20 threshold
    
    # 2. Record human override
    reason = "Logistics supervisor rerouted via alternate hub"
    success = record_decision("REC_AUDIT_01", "OVERRIDDEN", override_reason=reason, db_path=tmp_db)
    assert success is True
    
    # 3. Retrieve audit record
    audit = get_approval_status("REC_AUDIT_01", db_path=tmp_db)
    assert audit["status"] == "OVERRIDDEN"
    assert audit["override_reason"] == reason
    assert audit["timestamp"] is not None
    
    # 4. Check all approvals listing
    all_approvals = get_all_approvals(db_path=tmp_db)
    assert len(all_approvals) >= 1
    matched = [a for a in all_approvals if a["recommendation_id"] == "REC_AUDIT_01"]
    assert len(matched) == 1
    assert matched[0]["status"] == "OVERRIDDEN"

