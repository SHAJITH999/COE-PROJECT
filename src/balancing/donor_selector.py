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
    Also indexes (Date, Product_ID) candidate branches for fast deterministic retrieval.
    """
    def __init__(self, inventory_df: pd.DataFrame):
        self.surplus_map: Dict[Tuple[str, str, str], float] = {}
        self.branch_map: Dict[Tuple[str, str], List[str]] = {}
        for _, row in inventory_df.iterrows():
            d = str(row["Date"])
            b = str(row["Branch_ID"])
            p = str(row["Product_ID"])
            key = (d, b, p)
            # Usable surplus protects Forecast_Demand + Safety_Stock
            # This ensures that transferring stock does not cause a secondary stockout at the donor branch.
            surplus = float(row.get("Surplus_Units", 0))
            self.surplus_map[key] = max(0.0, surplus)
            dp_key = (d, p)
            if dp_key not in self.branch_map:
                self.branch_map[dp_key] = []
            if b not in self.branch_map[dp_key]:
                self.branch_map[dp_key].append(b)

    def get_available_surplus(self, date: str, branch_id: str, product_id: str) -> float:
        return self.surplus_map.get((str(date), str(branch_id), str(product_id)), 0.0)

    def deduct_surplus(self, date: str, branch_id: str, product_id: str, quantity: float):
        key = (str(date), str(branch_id), str(product_id))
        current = self.surplus_map.get(key, 0.0)
        self.surplus_map[key] = max(0.0, current - quantity)

    def get_candidate_branches(self, date: str, product_id: str, exclude_branch: str) -> List[str]:
        branches = self.branch_map.get((str(date), str(product_id)), [])
        return [b for b in branches if b != str(exclude_branch)]


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
    if hasattr(donor_pool_state, "get_candidate_branches"):
        candidate_branches = donor_pool_state.get_candidate_branches(date, product_id, dest_branch)
    else:
        candidates = inventory_df[
            (inventory_df["Date"] == date) &
            (inventory_df["Product_ID"] == product_id) &
            (inventory_df["Branch_ID"] != dest_branch)
        ]
        candidate_branches = [str(b) for b in candidates["Branch_ID"].unique()]
    
    feasible_donors = []
    
    for source_branch in candidate_branches:
        avail_surplus = donor_pool_state.get_available_surplus(date, source_branch, product_id)
        
        # Skip donor if their available surplus is exhausted or would breach safety stock limits
        if avail_surplus <= 0:
            continue
            
        route_info = get_route_info(routes_df, source_branch, dest_branch)
        feasible, reason = is_route_feasible(route_info, service_urgency)
        
        if not feasible or route_info is None:
            continue
            
        transfer_time = float(route_info["Transfer_Time_Hours"])
        cost_per_unit = float(route_info["Transfer_Cost_Per_Unit"])
        vehicle_capacity = float(route_info["Vehicle_Capacity"])
        
        feasible_donors.append({
            "Source_Branch": source_branch,
            "Source_City": route_info.get("Source_City", "") if hasattr(route_info, "get") else "",
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
