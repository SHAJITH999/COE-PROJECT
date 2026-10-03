"""
Transfer Feasibility Module for Multi-Location Inventory Balancing Recommender.

Validates route existence, route status, vehicle capacity, and transfer time bounds.
"""

from pathlib import Path
from typing import Dict, Optional, Tuple, Union
import pandas as pd

# Optional max transfer time thresholds in hours by recipient service urgency
MAX_TRANSFER_TIME_HOURS: Dict[str, float] = {
    "Critical": 24.0,
    "High": 48.0,
    "Medium": 72.0,
    "Low": 96.0
}


def get_route_info(
    routes_df: pd.DataFrame,
    source_branch: str,
    dest_branch: str
) -> Optional[pd.Series]:
    """
    Find matching route record from source_branch to dest_branch.
    Uses cached lookup dict for performance when available.
    """
    # Fast path: use cached dict in routes_df.attrs if available
    cache = routes_df.attrs.get("_route_lookup_cache") if hasattr(routes_df, "attrs") else None
    if cache is None and isinstance(routes_df, pd.DataFrame):
        try:
            cache = {}
            for _, r in routes_df.iterrows():
                cache[(str(r["Source_Branch"]), str(r["Destination_Branch"]))] = r
            if hasattr(routes_df, "attrs"):
                routes_df.attrs["_route_lookup_cache"] = cache
        except Exception:
            cache = None

    if cache is not None:
        return cache.get((str(source_branch), str(dest_branch)))

    matches = routes_df[
        (routes_df["Source_Branch"] == source_branch) &
        (routes_df["Destination_Branch"] == dest_branch)
    ]
    if matches.empty:
        return None
    return matches.iloc[0]


def is_route_feasible(
    route_info: Optional[pd.Series],
    service_urgency: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Evaluate if a route is feasible for stock transfer.
    
    Checks:
    1. Route existence
    2. Route status (must not be 'Unavailable' or 'Disabled')
    3. Vehicle capacity > 0
    4. Transfer time within service urgency deadline
    
    Returns:
        Tuple of (is_feasible: bool, reason: str)
    """
    if route_info is None:
        return False, "Route does not exist between source and destination"
        
    status = str(route_info.get("Route_Status", "Available")).strip().lower()
    # Route is rejected if unavailable or closed by logistics
    if status in ["unavailable", "disabled", "closed"]:
        return False, f"Route status is '{route_info.get('Route_Status')}'"
        
    capacity = float(route_info.get("Vehicle_Capacity", 0))
    # Route is rejected if it lacks vehicle capacity
    if capacity <= 0:
        return False, "Vehicle capacity is zero or negative"
        
    transfer_time = float(route_info.get("Transfer_Time_Hours", 0))
    if transfer_time < 0:
        return False, "Transfer time is invalid"
        
    if service_urgency in MAX_TRANSFER_TIME_HOURS:
        max_allowed = MAX_TRANSFER_TIME_HOURS[service_urgency]
        # Max allowed transfer time is dictated by the destination's Service Urgency 
        # to ensure stock arrives before critical SLA deadlines.
        if transfer_time > max_allowed:
            return False, f"Transfer time {transfer_time}h exceeds urgency limit {max_allowed}h"
            
    return True, "Route is feasible"
