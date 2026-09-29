"""
Demand Forecasting Module for Multi-Location Inventory Balancing Recommender.

Provides utilities for:
- Demand forecast extraction and validation
- Forecast horizon inspection
- Scenario demand surge scaling (e.g. URGENT_DEMAND)
- Demand forecast summarization across branches and categories
"""

from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd


def extract_forecast_demand(df: pd.DataFrame) -> pd.Series:
    """
    Extract and validate the Forecast_Demand series from an inventory dataframe.
    
    Args:
        df: DataFrame containing a 'Forecast_Demand' column.
        
    Returns:
        pd.Series containing non-negative float/int forecast demand values.
        
    Raises:
        KeyError: If 'Forecast_Demand' column is missing.
        ValueError: If negative demand forecasts are found.
    """
    if "Forecast_Demand" not in df.columns:
        raise KeyError("DataFrame must contain 'Forecast_Demand' column.")
    
    forecast = pd.to_numeric(df["Forecast_Demand"], errors="coerce").fillna(0.0)
    if (forecast < 0).any():
        raise ValueError("Forecast_Demand contains negative values, which is invalid.")
    return forecast


def get_forecast_horizon(df: pd.DataFrame) -> Dict[str, Union[str, int]]:
    """
    Inspect the forecast planning horizon from the dataset dates.
    
    The system operates on daily planning horizons across all branches.
    """
    if "Date" not in df.columns or df["Date"].dropna().empty:
        return {
            "horizon_type": "Daily Operational",
            "start_date": "N/A",
            "end_date": "N/A",
            "total_days": 1
        }
    
    dates = pd.to_datetime(df["Date"].dropna())
    min_date = dates.min().strftime("%Y-%m-%d")
    max_date = dates.max().strftime("%Y-%m-%d")
    total_days = int((dates.max() - dates.min()).days) + 1
    
    return {
        "horizon_type": "Daily Operational Rebalancing",
        "start_date": min_date,
        "end_date": max_date,
        "total_days": total_days,
        "planning_interval": "1-day step"
    }


def scale_forecast_for_scenario(
    df: pd.DataFrame,
    urgency_levels: Optional[List[str]] = None,
    scale_factor: float = 1.25
) -> pd.DataFrame:
    """
    Scale forecast demand for specified service urgency levels during surge simulations.
    
    Used by the URGENT_DEMAND disruption scenario.
    """
    if urgency_levels is None:
        urgency_levels = ["Critical", "High"]
        
    scaled_df = df.copy()
    if "Service_Urgency" in scaled_df.columns and "Forecast_Demand" in scaled_df.columns:
        mask = scaled_df["Service_Urgency"].isin(urgency_levels)
        scaled_df.loc[mask, "Forecast_Demand"] = (
            scaled_df.loc[mask, "Forecast_Demand"] * scale_factor
        ).astype(int)
    return scaled_df


def get_demand_summary(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate summary statistics for actual vs. forecast demand across the network.
    """
    summary = {}
    if "Forecast_Demand" in df.columns:
        summary["total_forecast_demand"] = float(df["Forecast_Demand"].sum())
        summary["mean_forecast_demand"] = float(df["Forecast_Demand"].mean())
    if "Actual_Demand" in df.columns:
        summary["total_actual_demand"] = float(df["Actual_Demand"].sum())
        summary["mean_actual_demand"] = float(df["Actual_Demand"].mean())
    return summary
