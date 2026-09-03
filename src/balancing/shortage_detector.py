"""
Shortage Detector Module for Multi-Location Inventory Balancing Recommender.

Detects and prioritizes shortage records from processed inventory data.
"""

from pathlib import Path
from typing import Dict
import pandas as pd

URGENCY_PRIORITY: Dict[str, int] = {
    "Critical": 1,
    "High": 2,
    "Medium": 3,
    "Low": 4
}


def detect_shortages(inventory_df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect shortage records (Shortage_Units > 0) and order them by urgency, quantity, and date.
    
    Args:
        inventory_df: DataFrame containing inventory intelligence/processed data.
        
    Returns:
        DataFrame of shortage records sorted deterministically.
    """
    shortages = inventory_df[inventory_df["Shortage_Units"] > 0].copy()
    
    if shortages.empty:
        return shortages
        
    shortages["_Urgency_Priority"] = shortages["Service_Urgency"].map(URGENCY_PRIORITY).fillna(5)
    
    # Sort deterministically
    shortages.sort_values(
        by=["_Urgency_Priority", "Shortage_Units", "Date", "Branch_ID", "Product_ID"],
        ascending=[True, False, True, True, True],
        inplace=True
    )
    
    shortages.drop(columns=["_Urgency_Priority"], inplace=True)
    return shortages
