"""
Unit tests for Phase 2:
- Inventory Intelligence & Status
- Purchase-Only Baseline Model calculations
- Service Level calculations
- Forecast Evaluation Metrics (MAE, RMSE, MAPE)
"""

import numpy as np
import pandas as pd
import pytest

from src.data.pipeline import (
    calculate_inventory_position,
    calculate_shortage_units,
    calculate_surplus_units,
)
from src.metrics.intelligence import (
    calculate_inventory_status,
    calculate_stock_coverage_ratio,
    calculate_demand_gap,
    calculate_safety_stock_gap,
)
from src.metrics.baseline import (
    calculate_baseline_purchases,
    calculate_service_level,
    evaluate_forecast_quality,
)


def test_shortage_and_surplus_consistency():
    """Verify shortage and surplus calculation consistency with deterministic input."""
    # Test case 1: Shortage exists
    # Stock = 10, Reserved = 2, Incoming = 2 -> Pos = 10
    # Forecast = 20, Safety = 5 -> Required = 25 -> Shortage = 15, Surplus = 0
    pos = calculate_inventory_position(10, 2, 2)
    shortage = calculate_shortage_units(20, 5, pos)
    surplus = calculate_surplus_units(pos, 20, 5)
    
    assert pos == 10
    assert shortage == 15
    assert surplus == 0
    
    # Test case 2: Surplus exists
    # Stock = 50, Reserved = 0, Incoming = 10 -> Pos = 60
    # Forecast = 30, Safety = 10 -> Required = 40 -> Shortage = 0, Surplus = 20
    pos2 = calculate_inventory_position(50, 10, 0)
    shortage2 = calculate_shortage_units(30, 10, pos2)
    surplus2 = calculate_surplus_units(pos2, 30, 10)
    
    assert pos2 == 60
    assert shortage2 == 0
    assert surplus2 == 20


def test_inventory_status_calculation():
    """Test Inventory_Status classification."""
    shortage = pd.Series([10, 0, 0])
    surplus = pd.Series([0, 15, 0])
    
    status = calculate_inventory_status(shortage, surplus)
    assert list(status) == ["SHORTAGE", "SURPLUS", "BALANCED"]


def test_purchase_quantity_equals_shortage_quantity():
    """Verify that Purchase_Quantity equals Shortage_Units in baseline."""
    df = pd.DataFrame({
        "Shortage_Units": [15, 0, 8],
        "Purchase_Cost": [100.0, 50.0, 200.0]
    })
    
    result = calculate_baseline_purchases(df)
    assert list(result["Purchase_Quantity"]) == [15.0, 0.0, 8.0]


def test_purchase_cost_calculation():
    """Verify Purchase_Cost = Purchase_Quantity * Unit Purchase Cost."""
    df = pd.DataFrame({
        "Shortage_Units": [10, 5],
        "Purchase_Cost": [250.0, 100.0]
    })
    
    result = calculate_baseline_purchases(df)
    assert list(result["Baseline_Purchase_Cost"]) == [2500.0, 500.0]


def test_no_purchase_when_no_shortage():
    """Verify Purchase_Quantity and Purchase_Cost are 0 when Shortage_Units is 0."""
    df = pd.DataFrame({
        "Shortage_Units": [0, 0],
        "Purchase_Cost": [500.0, 300.0]
    })
    
    result = calculate_baseline_purchases(df)
    assert list(result["Purchase_Quantity"]) == [0.0, 0.0]
    assert list(result["Baseline_Purchase_Cost"]) == [0.0, 0.0]


def test_service_level_calculation():
    """Test Service Level calculation formula and clipping bounds [0, 1]."""
    # Total shortage = 20, Total demand = 100 -> SL = 1 - 0.2 = 0.8
    assert calculate_service_level(20.0, 100.0) == 0.8
    
    # Zero shortage -> SL = 1.0
    assert calculate_service_level(0.0, 100.0) == 1.0
    
    # Shortage exceeds demand -> SL clipped to 0.0
    assert calculate_service_level(150.0, 100.0) == 0.0
    
    # Zero demand edge case -> SL = 1.0
    assert calculate_service_level(0.0, 0.0) == 1.0


def test_mae_calculation():
    """Test MAE calculation."""
    actual = pd.Series([10.0, 20.0, 30.0])
    forecast = pd.Series([12.0, 18.0, 35.0])
    # Absolute errors: |10-12|=2, |20-18|=2, |30-35|=5 -> MAE = (2+2+5)/3 = 3.0
    
    metrics = evaluate_forecast_quality(actual, forecast)
    assert metrics["Forecast MAE"] == 3.0


def test_rmse_calculation():
    """Test RMSE calculation."""
    actual = pd.Series([10.0, 20.0])
    forecast = pd.Series([13.0, 16.0])
    # Squared errors: (10-13)^2 = 9, (20-16)^2 = 16 -> Mean = 12.5 -> RMSE = sqrt(12.5) ≈ 3.5355
    
    metrics = evaluate_forecast_quality(actual, forecast)
    assert pytest.approx(metrics["Forecast RMSE"], 0.0001) == 3.5355


def test_mape_handling_zero_actual_demand():
    """Test MAPE handling when some actual demand values are zero."""
    actual = pd.Series([0.0, 10.0, 20.0])
    forecast = pd.Series([5.0, 12.0, 18.0])
    
    # Row 0: Actual = 0 -> Excluded from MAPE
    # Row 1: Actual = 10, Forecast = 12 -> Abs error = 2 -> APE = 2/10 = 0.2 (20%)
    # Row 2: Actual = 20, Forecast = 18 -> Abs error = 2 -> APE = 2/20 = 0.1 (10%)
    # Mean MAPE = (20% + 10%) / 2 = 15.0%
    
    metrics = evaluate_forecast_quality(actual, forecast)
    assert metrics["Forecast MAPE (%)"] == 15.0
