"""
Forecast Features & Inventory Intelligence Module.

Calculates demand gap, stock coverage ratio, and safety stock gaps
based on demand forecasts and current inventory positions.
"""

from typing import Union
import numpy as np
import pandas as pd


def calculate_stock_coverage_ratio(
    inventory_position: Union[float, pd.Series, np.ndarray],
    forecast_demand: Union[float, pd.Series, np.ndarray]
) -> Union[float, pd.Series, np.ndarray]:
    """
    Calculate Stock_Coverage_Ratio = Inventory_Position / Forecast_Demand.
    Returns 0.0 when Forecast_Demand is 0.
    """
    if isinstance(forecast_demand, pd.Series):
        return np.where(forecast_demand == 0, 0.0, inventory_position / forecast_demand)
    elif isinstance(forecast_demand, np.ndarray):
        return np.where(forecast_demand == 0, 0.0, inventory_position / forecast_demand)
    else:
        return 0.0 if forecast_demand == 0 else float(inventory_position / forecast_demand)


def calculate_demand_gap(
    forecast_demand: Union[float, pd.Series, np.ndarray],
    inventory_position: Union[float, pd.Series, np.ndarray]
) -> Union[float, pd.Series, np.ndarray]:
    """
    Calculate Demand_Gap = Forecast_Demand - Inventory_Position.
    Positive value indicates demand exceeds available position.
    """
    return forecast_demand - inventory_position


def calculate_safety_stock_gap(
    inventory_position: Union[float, pd.Series, np.ndarray],
    safety_stock: Union[float, pd.Series, np.ndarray]
) -> Union[float, pd.Series, np.ndarray]:
    """
    Calculate Safety_Stock_Gap = Inventory_Position - Safety_Stock.
    Negative value indicates inventory has breached safety stock floor.
    """
    return inventory_position - safety_stock
