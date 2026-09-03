"""
Disruption Scenario Generation Module for Multi-Location Inventory Balancing Recommender.

Generates four experimental scenarios in memory without modifying raw datasets:
- NORMAL: Baseline operating environment
- DELAY: Increased transfer times on key transport routes
- CAPACITY_LOSS: Reduced vehicle capacity on key transport routes
- URGENT_DEMAND: Increased forecast demand for critical items/branches
"""

from typing import Dict, Tuple
import pandas as pd

from src.data.loader import load_inventory_demand, load_transfer_routes
from src.data.pipeline import process_inventory_data
from src.metrics.intelligence import (
    calculate_inventory_status,
    calculate_stock_coverage_ratio,
    calculate_demand_gap,
    calculate_safety_stock_gap
)


def create_scenario_datasets(
    scenario_name: str
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate inventory and routes dataframes for a specific disruption scenario.
    
    Scenarios:
    - 'NORMAL': Unmodified data
    - 'DELAY': +3.0 hours transfer time on all routes
    - 'CAPACITY_LOSS': 50% reduction in vehicle capacity on all routes
    - 'URGENT_DEMAND': +25% increase in forecast demand for Critical/High items
    
    Returns:
        Tuple of (inventory_intelligence_df, routes_df)
    """
    inv_raw = load_inventory_demand()
    routes_raw = load_transfer_routes()
    
    inv_df = inv_raw.copy()
    routes_df = routes_raw.copy()
    
    name_clean = str(scenario_name).upper().strip()
    
    if name_clean == "NORMAL":
        pass  # Unmodified
        
    elif name_clean == "DELAY":
        # Increase transfer time by 3.0 hours
        routes_df["Transfer_Time_Hours"] = routes_df["Transfer_Time_Hours"] + 3.0
        
    elif name_clean == "CAPACITY_LOSS":
        # Reduce vehicle capacity by 50% (capped at minimum 1)
        routes_df["Vehicle_Capacity"] = (routes_df["Vehicle_Capacity"] * 0.5).astype(int).clip(lower=1)
        
    elif name_clean == "URGENT_DEMAND":
        # Increase forecast demand by 25% for Critical and High urgency items
        urgent_mask = inv_df["Service_Urgency"].isin(["Critical", "High"])
        inv_df.loc[urgent_mask, "Forecast_Demand"] = (inv_df.loc[urgent_mask, "Forecast_Demand"] * 1.25).astype(int)
        
    else:
        raise ValueError(f"Unknown scenario name: '{scenario_name}'")
        
    # Process inventory calculations
    inv_proc = process_inventory_data(inv_df)
    
    # Calculate intelligence fields
    inv_proc["Inventory_Status"] = calculate_inventory_status(inv_proc["Shortage_Units"], inv_proc["Surplus_Units"])
    inv_proc["Stock_Coverage_Ratio"] = calculate_stock_coverage_ratio(inv_proc["Inventory_Position"], inv_proc["Forecast_Demand"])
    inv_proc["Demand_Gap"] = calculate_demand_gap(inv_proc["Forecast_Demand"], inv_proc["Inventory_Position"])
    inv_proc["Safety_Stock_Gap"] = calculate_safety_stock_gap(inv_proc["Inventory_Position"], inv_proc["Safety_Stock"])
    
    return inv_proc, routes_df
