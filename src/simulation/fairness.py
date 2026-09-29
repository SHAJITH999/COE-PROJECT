"""
Fairness Tracking and Evaluation Module for Multi-Location Inventory Balancing Recommender.

Tracks donor branch contributions to prevent over-reliance on single donor branches.
Reports utilization, max/min contributions, and contribution imbalance.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"


class FairnessTracker:
    """
    Tracks cumulative donor contributions to enable fairness-aware tie-breaking.
    """
    def __init__(self):
        self.units_supplied: Dict[str, float] = {}
        self.transfers_count: Dict[str, int] = {}
        
    def record_transfer(self, branch_id: str, quantity: float):
        self.units_supplied[branch_id] = self.units_supplied.get(branch_id, 0.0) + quantity
        self.transfers_count[branch_id] = self.transfers_count.get(branch_id, 0) + 1
        
    def get_supplied_units(self, branch_id: str) -> float:
        return self.units_supplied.get(branch_id, 0.0)
        
    def get_transfers_count(self, branch_id: str) -> int:
        return self.transfers_count.get(branch_id, 0)


def calculate_fairness_metrics(recs_df: pd.DataFrame, inventory_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate donor contribution fairness metrics across all branch locations.
    """
    all_branches = sorted(inventory_df["Branch_ID"].unique().tolist())
    total_branches_count = len(all_branches)
    
    if not recs_df.empty:
        transfers = recs_df[
            (recs_df["Recommendation_Type"].isin(["TRANSFER", "PARTIAL_TRANSFER", "PARTIAL_TRANSFER_AND_PURCHASE"])) &
            (recs_df["Shortage_Avoided"] > 0) &
            (recs_df["Source_Branch"] != "")
        ]
        
        branch_stats = transfers.groupby("Source_Branch").agg(
            Total_Units_Supplied=("Shortage_Avoided", "sum"),
            Number_Of_Transfers=("Shortage_Avoided", "count")
        ).reset_index()
    else:
        branch_stats = pd.DataFrame(columns=["Source_Branch", "Total_Units_Supplied", "Number_Of_Transfers"])
        
    # Ensure all branches represented
    active_donors = set(branch_stats["Source_Branch"]) if not branch_stats.empty else set()
    donor_utilization_pct = (len(active_donors) / max(1, total_branches_count)) * 100.0
    
    if not branch_stats.empty:
        max_contrib = float(branch_stats["Total_Units_Supplied"].max())
        min_contrib = float(branch_stats["Total_Units_Supplied"].min())
        imbalance = max_contrib - min_contrib
    else:
        max_contrib = 0.0
        min_contrib = 0.0
        imbalance = 0.0
        
    metrics = [
        {"Metric": "Total Distributor Branches", "Value": total_branches_count},
        {"Metric": "Active Donor Branches", "Value": len(active_donors)},
        {"Metric": "Donor Branch Utilization (%)", "Value": round(donor_utilization_pct, 2)},
        {"Metric": "Maximum Donor Contribution (Units)", "Value": round(max_contrib, 2)},
        {"Metric": "Minimum Active Donor Contribution (Units)", "Value": round(min_contrib, 2)},
        {"Metric": "Donor Contribution Imbalance (Units)", "Value": round(imbalance, 2)}
    ]
    
    return pd.DataFrame(metrics)
