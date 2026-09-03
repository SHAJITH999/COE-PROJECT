"""
Donor Selector Module for Multi-Location Inventory Balancing Recommender.

Finds and ranks potential donor branches holding usable surplus while protecting safety stock.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd

from src.balancing.transfer_feasibility import get_route_info, is_route_feasible


class DonorPoolState:
    """
    Tracks dynamic remaining available surplus per (Date, Branch_ID, Product_ID)
    during recommendation generation to ensure safety stock is never violated.
    """
    def __init__(self, inventory_df: pd.DataFrame):
        self.surplus_map: Dict[Tuple[str, str, str], float] = {}
        for _, row in inventory_df.iterrows():
            key = (str(row["Date"]), str(row["Branch_ID"]), str(row["Product_ID"]))
            # Usable surplus protects Forecast_Demand + Safety_Stock
            surplus = float(row.get("Surplus_Units", 0))
            self.surplus_map[key] = max(0.0, surplus)

    def get_available_surplus(self, date: str, branch_id: str, product_id: str) -> float:
        return self.surplus_map.get((str(date), str(branch_id), str(product_id)), 0.0)

    def deduct_surplus(self, date: str, branch_id: str, product_id: str, quantity: float):
        key = (str(date), str(branch_id), str(product_id))
        current = self.surplus_map.get(key, 0.0)
        self.surplus_map[key] = max(0.0, current - quantity)


def find_and_rank_donors(
    inventory_df: pd.DataFrame,
    routes_df: pd.DataFrame,
    dest_branch: str,
    product_id: str,
    date: str,
    service_urgency: str,
    donor_pool_state: DonorPoolState
) -> List[Dict]:
    """
    Find feasible donor branches on the same date for the same product and rank them.
    
    Ranking order (deterministic):
    1. Shortest Transfer_Time_Hours
    2. Lowest Transfer_Cost_Per_Unit
    3. Greater available surplus
    4. Lexicographical Source_Branch ID
    
    Returns:
        List of dicts containing donor details and route info.
    """
    candidates = inventory_df[
        (inventory_df["Date"] == date) &
        (inventory_df["Product_ID"] == product_id) &
        (inventory_df["Branch_ID"] != dest_branch)
    ].copy()
    
    feasible_donors = []
    
    for _, row in candidates.iterrows():
        source_branch = str(row["Branch_ID"])
        avail_surplus = donor_pool_state.get_available_surplus(date, source_branch, product_id)
        
        if avail_surplus <= 0:
            continue
            
        route_info = get_route_info(routes_df, source_branch, dest_branch)
        feasible, reason = is_route_feasible(route_info, service_urgency)
        
        if not feasible:
            continue
            
        transfer_time = float(route_info["Transfer_Time_Hours"])
        cost_per_unit = float(route_info["Transfer_Cost_Per_Unit"])
        vehicle_capacity = float(route_info["Vehicle_Capacity"])
        
        feasible_donors.append({
            "Source_Branch": source_branch,
            "Source_City": route_info.get("Source_City", ""),
            "Available_Surplus": avail_surplus,
            "Transfer_Time_Hours": transfer_time,
            "Transfer_Cost_Per_Unit": cost_per_unit,
            "Vehicle_Capacity": vehicle_capacity,
            "Route_Info": route_info
        })
        
    # Sort deterministically according to spec
    feasible_donors.sort(key=lambda d: (
        d["Transfer_Time_Hours"],
        d["Transfer_Cost_Per_Unit"],
        -d["Available_Surplus"],
        d["Source_Branch"]
    ))
    
    return feasible_donors
