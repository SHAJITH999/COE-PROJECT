"""
Unit tests for basic inventory calculations in Phase 1:
- Inventory_Position
- Shortage_Units
- Surplus_Units
"""

import numpy as np
import pandas as pd
import pytest

from src.data.pipeline import (
    calculate_inventory_position,
    calculate_shortage_units,
    calculate_surplus_units,
    process_inventory_data,
)


def test_calculate_inventory_position_scalar():
    """Test Inventory_Position calculation with scalar values."""
    # Standard case: 100 + 20 - 10 = 110
    assert calculate_inventory_position(100, 20, 10) == 110
    
    # Zero values
    assert calculate_inventory_position(0, 0, 0) == 0
    
    # Reserved stock exceeding current + incoming
    assert calculate_inventory_position(10, 5, 20) == -5


def test_calculate_inventory_position_series():
    """Test Inventory_Position calculation with pandas Series."""
    current = pd.Series([100, 50, 0])
    incoming = pd.Series([20, 10, 5])
    reserved = pd.Series([10, 5, 10])
    
    expected = pd.Series([110, 55, -5])
    result = calculate_inventory_position(current, incoming, reserved)
    pd.testing.assert_series_equal(result, expected)


def test_calculate_shortage_units_scalar():
    """Test Shortage_Units calculation with scalar values."""
    # Shortage case: Demand (50) + Safety (10) = 60 required; Position = 40 -> Shortage = 20
    assert calculate_shortage_units(50, 10, 40) == 20
    
    # No shortage case (Surplus exists): Required = 60; Position = 80 -> Shortage = 0
    assert calculate_shortage_units(50, 10, 80) == 0
    
    # Exact balance case: Required = 60; Position = 60 -> Shortage = 0
    assert calculate_shortage_units(50, 10, 60) == 0
    
    # Negative position case: Required = 60; Position = -10 -> Shortage = 70
    assert calculate_shortage_units(50, 10, -10) == 70


def test_calculate_shortage_units_series():
    """Test Shortage_Units calculation with pandas Series."""
    forecast = pd.Series([50, 50, 50, 50])
    safety = pd.Series([10, 10, 10, 10])
    pos = pd.Series([40, 80, 60, -10])
    
    expected = pd.Series([20, 0, 0, 70])
    result = calculate_shortage_units(forecast, safety, pos)
    pd.testing.assert_series_equal(result, expected)


def test_calculate_surplus_units_scalar():
    """Test Surplus_Units calculation with scalar values."""
    # Surplus case: Position = 100; Required = 50 + 10 = 60 -> Surplus = 40
    assert calculate_surplus_units(100, 50, 10) == 40
    
    # Shortage case: Position = 40; Required = 60 -> Surplus = 0
    assert calculate_surplus_units(40, 50, 10) == 0
    
    # Exact balance case: Position = 60; Required = 60 -> Surplus = 0
    assert calculate_surplus_units(60, 50, 10) == 0


def test_calculate_surplus_units_series():
    """Test Surplus_Units calculation with pandas Series."""
    pos = pd.Series([100, 40, 60])
    forecast = pd.Series([50, 50, 50])
    safety = pd.Series([10, 10, 10])
    
    expected = pd.Series([40, 0, 0])
    result = calculate_surplus_units(pos, forecast, safety)
    pd.testing.assert_series_equal(result, expected)


def test_shortage_and_surplus_mutual_exclusivity():
    """Verify that shortage and surplus cannot both be positive for any row."""
    forecast = pd.Series([50, 60, 70, 80])
    safety = pd.Series([10, 15, 20, 25])
    pos = pd.Series([40, 100, 90, 50])  # mix of shortage and surplus
    
    shortages = calculate_shortage_units(forecast, safety, pos)
    surpluses = calculate_surplus_units(pos, forecast, safety)
    
    # Both cannot be strictly positive at the same time
    both_positive = (shortages > 0) & (surpluses > 0)
    assert not both_positive.any()


def test_process_inventory_data_pipeline():
    """Test end-to-end processing of sample DataFrame."""
    df = pd.DataFrame({
        "Current_Stock": [79, 10],
        "Incoming_Stock": [3, 6],
        "Reserved_Stock": [1, 2],
        "Forecast_Demand": [60, 20],
        "Safety_Stock": [18, 5]
    })
    
    # Row 0: Pos = 79+3-1 = 81. Req = 60+18 = 78. Shortage = max(0, 78-81) = 0. Surplus = max(0, 81-78) = 3.
    # Row 1: Pos = 10+6-2 = 14. Req = 20+5 = 25. Shortage = max(0, 25-14) = 11. Surplus = max(0, 14-25) = 0.
    
    processed = process_inventory_data(df)
    
    assert list(processed["Inventory_Position"]) == [81, 14]
    assert list(processed["Shortage_Units"]) == [0, 11]
    assert list(processed["Surplus_Units"]) == [3, 0]
