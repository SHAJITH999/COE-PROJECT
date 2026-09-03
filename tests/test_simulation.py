"""
Unit tests for Phase 4:
- Safety stock protection & 0 safety violations guarantee
- Urgency prioritization
- Fairness metric calculation
- Disruption scenario generation (DELAY, CAPACITY_LOSS, URGENT_DEMAND)
- Baseline vs Proposed comparative metrics (Shortage Avoided %, Purchase Avoided %, Cost Difference, Service Improvement)
"""

import pandas as pd
import pytest

from src.simulation.safety import validate_transfer_safety, calculate_safety_metrics
from src.simulation.fairness import FairnessTracker, calculate_fairness_metrics
from src.simulation.scenarios import create_scenario_datasets
from src.simulation.runner import run_single_scenario_experiment, run_all_phase4_experiments


def test_safety_stock_protection():
    """Verify validate_transfer_safety caps or rejects transfers violating donor safety stock."""
    # Donor pos = 100, Forecast = 60, Safety = 20 -> Max safe available = 100 - (60+20) = 20
    is_safe, approved_qty, evidence = validate_transfer_safety(100.0, 20.0, 60.0, 15.0)
    assert is_safe is True
    assert approved_qty == 15.0
    
    # Request exceeding safe capacity (30 requested > 20 safe)
    is_safe2, approved_qty2, evidence2 = validate_transfer_safety(100.0, 20.0, 60.0, 30.0)
    assert is_safe2 is True
    assert approved_qty2 == 20.0  # Capped at 20.0
    
    # Donor at exact safety threshold (Pos = 80, Req = 60+20 = 80 -> Max safe = 0)
    is_safe3, approved_qty3, evidence3 = validate_transfer_safety(80.0, 20.0, 60.0, 10.0)
    assert is_safe3 is False
    assert approved_qty3 == 0.0


def test_zero_safety_violations_guarantee():
    """Verify calculate_safety_metrics returns 0 safety violations."""
    recs_df = pd.DataFrame([
        {"Recommendation_Type": "TRANSFER", "Shortage_Avoided": 20.0, "Evidence": "Source B001 surplus 50; safety stock protected"},
        {"Recommendation_Type": "PURCHASE", "Shortage_Avoided": 0.0, "Evidence": "No feasible network transfer"}
    ])
    
    safety_df = calculate_safety_metrics(recs_df)
    violations_row = safety_df[safety_df["Metric"] == "Safety Violations Count"]
    assert float(violations_row.iloc[0]["Value"]) == 0.0


def test_fairness_metric_calculation():
    """Test fairness tracker and metric calculation."""
    tracker = FairnessTracker()
    tracker.record_transfer("B001", 50.0)
    tracker.record_transfer("B001", 30.0)
    tracker.record_transfer("B002", 20.0)
    
    assert tracker.get_supplied_units("B001") == 80.0
    assert tracker.get_transfers_count("B001") == 2
    assert tracker.get_supplied_units("B002") == 20.0
    
    inv_df = pd.DataFrame([
        {"Branch_ID": "B001"}, {"Branch_ID": "B002"}, {"Branch_ID": "B003"}
    ])
    recs_df = pd.DataFrame([
        {"Source_Branch": "B001", "Shortage_Avoided": 80.0, "Recommendation_Type": "TRANSFER"},
        {"Source_Branch": "B002", "Shortage_Avoided": 20.0, "Recommendation_Type": "TRANSFER"}
    ])
    
    fairness_df = calculate_fairness_metrics(recs_df, inv_df)
    active_donors = float(fairness_df[fairness_df["Metric"] == "Active Donor Branches"].iloc[0]["Value"])
    assert active_donors == 2.0


def test_disruption_scenario_generation():
    """Verify disruption scenario dataframe transformations."""
    # NORMAL
    inv_norm, routes_norm = create_scenario_datasets("NORMAL")
    # DELAY
    inv_del, routes_del = create_scenario_datasets("DELAY")
    # CAPACITY_LOSS
    inv_cap, routes_cap = create_scenario_datasets("CAPACITY_LOSS")
    # URGENT_DEMAND
    inv_urg, routes_urg = create_scenario_datasets("URGENT_DEMAND")
    
    # DELAY transfer time increases by 3 hours
    assert routes_del["Transfer_Time_Hours"].iloc[0] == routes_norm["Transfer_Time_Hours"].iloc[0] + 3.0
    
    # CAPACITY_LOSS vehicle capacity reduced by 50%
    assert routes_cap["Vehicle_Capacity"].iloc[0] == int(routes_norm["Vehicle_Capacity"].iloc[0] * 0.5)
    
    # URGENT_DEMAND increases forecast demand for Critical/High items
    crit_mask = inv_norm["Service_Urgency"].isin(["Critical", "High"])
    if crit_mask.sum() > 0:
        idx = inv_norm[crit_mask].index[0]
        assert inv_urg.loc[idx, "Forecast_Demand"] > inv_norm.loc[idx, "Forecast_Demand"]


def test_baseline_vs_proposed_comparative_metrics():
    """Test single scenario experiment metrics calculation."""
    metrics, recs_df, _ = run_single_scenario_experiment("NORMAL")
    
    assert "Baseline Shortage" in metrics
    assert "Proposed Shortage" in metrics
    assert "Shortage Avoided (%)" in metrics
    assert "Purchase Avoided (%)" in metrics
    assert "Cost Difference" in metrics
    assert "Service Improvement" in metrics
    assert metrics["Safety Violations"] == 0
    assert metrics["Shortage Avoided (%)"] >= 0.0
    assert metrics["Cost Difference"] >= 0.0
