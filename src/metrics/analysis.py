"""
Basic Analysis Module for Multi-Location Inventory Balancing Recommender.

Generates summary reports:
- Branch shortage summary
- Product shortage summary
- Branch surplus summary
- Service urgency shortage summary
"""

from pathlib import Path
from typing import Dict, Optional, Union
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"


def generate_branch_shortage_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Group shortage metrics by Branch."""
    shortage_df = df[df["Shortage_Units"] > 0]
    
    group_cols = ["Branch_ID"]
    if "Branch_Name" in df.columns:
        group_cols.append("Branch_Name")
        
    summary = shortage_df.groupby(group_cols).agg(
        Total_Shortage_Units=("Shortage_Units", "sum"),
        Shortage_Records_Count=("Shortage_Units", "count"),
        Total_Purchase_Cost=("Baseline_Purchase_Cost", "sum") if "Baseline_Purchase_Cost" in df.columns else ("Purchase_Cost", "sum")
    ).reset_index()
    
    return summary.sort_values(by="Total_Shortage_Units", ascending=False)


def generate_product_shortage_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Group shortage metrics by Product."""
    shortage_df = df[df["Shortage_Units"] > 0]
    
    group_cols = ["Product_ID"]
    if "Product_Name" in df.columns:
        group_cols.append("Product_Name")
        
    summary = shortage_df.groupby(group_cols).agg(
        Total_Shortage_Units=("Shortage_Units", "sum"),
        Shortage_Records_Count=("Shortage_Units", "count"),
        Total_Purchase_Cost=("Baseline_Purchase_Cost", "sum") if "Baseline_Purchase_Cost" in df.columns else ("Purchase_Cost", "sum")
    ).reset_index()
    
    return summary.sort_values(by="Total_Shortage_Units", ascending=False)


def generate_branch_surplus_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Group surplus metrics by Branch."""
    surplus_df = df[df["Surplus_Units"] > 0]
    
    group_cols = ["Branch_ID"]
    if "Branch_Name" in df.columns:
        group_cols.append("Branch_Name")
        
    summary = surplus_df.groupby(group_cols).agg(
        Total_Surplus_Units=("Surplus_Units", "sum"),
        Surplus_Records_Count=("Surplus_Units", "count")
    ).reset_index()
    
    return summary.sort_values(by="Total_Surplus_Units", ascending=False)


def generate_urgency_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Group shortage metrics by Service_Urgency."""
    shortage_df = df[df["Shortage_Units"] > 0]
    
    summary = shortage_df.groupby("Service_Urgency").agg(
        Total_Shortage_Units=("Shortage_Units", "sum"),
        Shortage_Records_Count=("Shortage_Units", "count"),
        Total_Purchase_Cost=("Baseline_Purchase_Cost", "sum") if "Baseline_Purchase_Cost" in df.columns else ("Purchase_Cost", "sum")
    ).reset_index()
    
    urgency_order = {"Critical": 1, "High": 2, "Medium": 3, "Low": 4}
    summary["Priority"] = summary["Service_Urgency"].map(urgency_order)
    summary = summary.sort_values(by="Priority").drop(columns=["Priority"])
    
    return summary


def run_analysis(
    baseline_df: pd.DataFrame,
    output_dir: Optional[Union[str, Path]] = None
) -> Dict[str, pd.DataFrame]:
    """
    Generate all four Phase 2 basic analysis CSV summary files.
    """
    out_dir = Path(output_dir) if output_dir else OUTPUTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    
    branch_shortage = generate_branch_shortage_summary(baseline_df)
    product_shortage = generate_product_shortage_summary(baseline_df)
    branch_surplus = generate_branch_surplus_summary(baseline_df)
    urgency_summary = generate_urgency_summary(baseline_df)
    
    branch_shortage.to_csv(out_dir / "branch_shortage_summary.csv", index=False)
    product_shortage.to_csv(out_dir / "product_shortage_summary.csv", index=False)
    branch_surplus.to_csv(out_dir / "branch_surplus_summary.csv", index=False)
    urgency_summary.to_csv(out_dir / "urgency_summary.csv", index=False)
    
    return {
        "branch_shortage": branch_shortage,
        "product_shortage": product_shortage,
        "branch_surplus": branch_surplus,
        "urgency_summary": urgency_summary
    }
