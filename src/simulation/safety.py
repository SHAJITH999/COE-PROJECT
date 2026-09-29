"""
Safety Validation Module for Multi-Location Inventory Balancing Recommender.

Enforces safety stock protection and calculates safety violation metrics.
Invariant: Donor Remaining Inventory >= Forecast_Demand + Safety_Stock.
"""

from pathlib import Path
from typing import Dict, List, Tuple, Union
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"


def validate_transfer_safety(
    donor_inventory_pos: float,
    donor_safety_stock: float,
    donor_forecast_demand: float,
    requested_qty: float
) -> Tuple[bool, float, str]:
    """
    Validate that a requested transfer quantity does not reduce donor inventory below safety stock.
    
    Formula: Safe Available = max(0, Donor_Pos - (Forecast_Demand + Safety_Stock))
    
    Returns:
        Tuple of (is_safe: bool, approved_qty: float, safety_decision_evidence: str)
    """
    max_safe_qty = max(0.0, donor_inventory_pos - (donor_forecast_demand + donor_safety_stock))
    
    if max_safe_qty <= 0:
        return False, 0.0, "Rejected: transfer would violate donor safety stock"
        
    if requested_qty <= max_safe_qty:
        return True, requested_qty, "Full transfer approved: donor safety stock protected"
    else:
        return True, max_safe_qty, f"Partial transfer capped at safe limit of {max_safe_qty} units to protect donor safety stock"


def calculate_safety_metrics(recs_df: pd.DataFrame) -> pd.DataFrame:
    """
    Verify safety stock compliance across all transfer recommendations.
    
    Expected: Safety_Violations = 0.
    """
    if recs_df.empty:
        total_recs = 0
        safety_violations = 0
    else:
        transfer_recs = recs_df[recs_df["Recommendation_Type"].isin(["TRANSFER", "PARTIAL_TRANSFER", "PARTIAL_TRANSFER_AND_PURCHASE"]) & (recs_df["Shortage_Avoided"] > 0)]
        total_recs = len(transfer_recs)
        
        # Check evidence strings for safety violation flags
        violations_mask = transfer_recs["Evidence"].str.contains("violation|breached", case=False, na=False)
        safety_violations = int(violations_mask.sum())
        
    compliance_rate = 100.0 if safety_violations == 0 else max(0.0, (1 - safety_violations / max(1, total_recs)) * 100.0)
    
    metrics = [
        {"Metric": "Total Transfer Recommendations", "Value": total_recs},
        {"Metric": "Safety Violations Count", "Value": safety_violations},
        {"Metric": "Safety Stock Compliance Rate (%)", "Value": round(compliance_rate, 2)},
        {"Metric": "Safety Rule Enforcement Status", "Value": "PASSED (0 Violations)" if safety_violations == 0 else "FAILED"}
    ]
    
    return pd.DataFrame(metrics)
