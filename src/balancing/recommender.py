"""
Recommender Engine Module for Multi-Location Inventory Balancing Recommender.

Generates stock transfer and purchase recommendations before new purchase,
calculates proposed network costs, shortage avoidance metrics, and evidence strings.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from src.data.loader import load_transfer_routes
from src.balancing.shortage_detector import detect_shortages
from src.balancing.donor_selector import DonorPoolState, find_and_rank_donors

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"


def generate_recommendations(
    inventory_df: pd.DataFrame,
    routes_df: pd.DataFrame,
    baseline_metrics_df: Optional[pd.DataFrame] = None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate core multi-location transfer and purchase recommendations.
    
    Returns:
        Tuple of (recommendations_df, recommendation_metrics_df).
    """
    donor_pool_state = DonorPoolState(inventory_df)
    shortage_records = detect_shortages(inventory_df)
    
    recommendations = []
    rec_counter = 1
    
    for _, shortage in shortage_records.iterrows():
        date = str(shortage["Date"])
        dest_branch = str(shortage["Branch_ID"])
        product_id = str(shortage["Product_ID"])
        urgency = str(shortage["Service_Urgency"])
        unit_purchase_cost = float(shortage.get("Purchase_Cost", 0.0))
        
        shortage_before = float(shortage["Shortage_Units"])
        remaining_shortage = shortage_before
        
        # Rank feasible donors
        feasible_donors = find_and_rank_donors(
            inventory_df, routes_df, dest_branch, product_id, date, urgency, donor_pool_state
        )
        
        transfers_made = 0
        
        for donor in feasible_donors:
            if remaining_shortage <= 0:
                break
                
            source_branch = donor["Source_Branch"]
            avail_surplus = donor["Available_Surplus"]
            capacity = donor["Vehicle_Capacity"]
            transfer_time = donor["Transfer_Time_Hours"]
            cost_per_unit = donor["Transfer_Cost_Per_Unit"]
            
            transfer_qty = min(remaining_shortage, avail_surplus, capacity)
            
            if transfer_qty <= 0:
                continue
                
            # Inter-branch transfer leg recommendation.
            # All successful transfer allocations are recorded as 'TRANSFER'.
            # If remaining shortage cannot be fulfilled by transfers, subsequent leg is recorded as 'PARTIAL_TRANSFER_AND_PURCHASE'.
            rec_type = "TRANSFER"
            
            coverage_desc = (
                f"Full shortage satisfied ({int(transfer_qty)} units)"
                if transfer_qty == shortage_before
                else f"Partial transfer leg covering {int(transfer_qty)} of {int(shortage_before)} shortage units"
            )
            
            evidence = (
                f"{coverage_desc}; Source {source_branch} has {int(avail_surplus)} usable surplus units; "
                f"safety stock protected; route feasible; transfer time {transfer_time}h; "
                f"capacity {int(capacity)} units."
            )
            
            est_cost = transfer_qty * cost_per_unit
            
            recommendations.append({
                "Recommendation_ID": f"REC{rec_counter:05d}",
                "Date": date,
                "Source_Branch": source_branch,
                "Destination_Branch": dest_branch,
                "Product_ID": product_id,
                "Recommended_Quantity": round(transfer_qty, 2),
                "Recommendation_Type": rec_type,
                "Service_Urgency": urgency,
                "Transfer_Time_Hours": round(transfer_time, 2),
                "Estimated_Cost": round(est_cost, 2),
                "Shortage_Before": round(shortage_before, 2),
                "Shortage_Avoided": round(transfer_qty, 2),
                "Remaining_Shortage": round(remaining_shortage - transfer_qty, 2),
                "Purchase_Quantity": 0.0,
                "Evidence": evidence,
                "Approval_Status": "PENDING"
            })
            
            rec_counter += 1
            donor_pool_state.deduct_surplus(date, source_branch, product_id, transfer_qty)
            remaining_shortage -= transfer_qty
            transfers_made += 1
            
        # If remaining shortage > 0, generate PURCHASE recommendation
        if remaining_shortage > 0:
            purchase_cost = remaining_shortage * unit_purchase_cost
            rec_type = "PURCHASE" if transfers_made == 0 else "PARTIAL_TRANSFER_AND_PURCHASE"
            evidence = (
                "No feasible network transfer can cover remaining shortage"
                if transfers_made == 0
                else f"Partial network transfer completed; remaining shortage of {int(remaining_shortage)} units requires purchase."
            )
            
            recommendations.append({
                "Recommendation_ID": f"REC{rec_counter:05d}",
                "Date": date,
                "Source_Branch": "",
                "Destination_Branch": dest_branch,
                "Product_ID": product_id,
                "Recommended_Quantity": round(remaining_shortage, 2),
                "Recommendation_Type": rec_type,
                "Service_Urgency": urgency,
                "Transfer_Time_Hours": 0.0,
                "Estimated_Cost": round(purchase_cost, 2),
                "Shortage_Before": round(shortage_before, 2),
                "Shortage_Avoided": 0.0,
                "Remaining_Shortage": round(remaining_shortage, 2),
                "Purchase_Quantity": round(remaining_shortage, 2),
                "Evidence": evidence,
                "Approval_Status": "PENDING"
            })
            
            rec_counter += 1
            
    recs_df = pd.DataFrame(recommendations)
    
    # Calculate Aggregate Metrics
    total_shortage_before = float(shortage_records["Shortage_Units"].sum()) if not shortage_records.empty else 0.0
    
    if not recs_df.empty:
        transfer_recs = recs_df[recs_df["Recommendation_Type"].isin(["TRANSFER", "PARTIAL_TRANSFER_AND_PURCHASE"]) & (recs_df["Shortage_Avoided"] > 0)]
        purchase_recs = recs_df[recs_df["Purchase_Quantity"] > 0]
        
        total_shortage_avoided = float(recs_df["Shortage_Avoided"].sum())
        total_transfer_quantity = float(transfer_recs["Recommended_Quantity"].sum()) if not transfer_recs.empty else 0.0
        total_transfer_cost = float(transfer_recs["Estimated_Cost"].sum()) if not transfer_recs.empty else 0.0
        
        total_purchase_quantity = float(purchase_recs["Purchase_Quantity"].sum()) if not purchase_recs.empty else 0.0
        remaining_purchase_cost = float(purchase_recs["Estimated_Cost"].sum()) if not purchase_recs.empty else 0.0
        
        remaining_shortage = total_shortage_before - total_shortage_avoided
        num_transfers = int(len(transfer_recs))
        num_purchase_only = int(len(recs_df[recs_df["Recommendation_Type"] == "PURCHASE"]))
    else:
        total_shortage_avoided = 0.0
        total_transfer_quantity = 0.0
        total_transfer_cost = 0.0
        total_purchase_quantity = 0.0
        remaining_purchase_cost = 0.0
        remaining_shortage = 0.0
        num_transfers = 0
        num_purchase_only = 0
        
    total_proposed_cost = total_transfer_cost + remaining_purchase_cost
    
    # Baseline shortage reference comparison
    total_baseline_shortage = total_shortage_before
    if baseline_metrics_df is not None and not baseline_metrics_df.empty:
        base_shortage_match = baseline_metrics_df[baseline_metrics_df["Metric"] == "Total Shortage Units"]
        if not base_shortage_match.empty:
            total_baseline_shortage = float(base_shortage_match.iloc[0]["Value"])
            
    avoidance_pct = (total_shortage_avoided / total_baseline_shortage * 100.0) if total_baseline_shortage > 0 else 0.0
    
    metrics = [
        {"Metric": "Total Shortage Before Transfers", "Value": round(total_shortage_before, 2)},
        {"Metric": "Total Shortage Avoided", "Value": round(total_shortage_avoided, 2)},
        {"Metric": "Total Transfer Quantity", "Value": round(total_transfer_quantity, 2)},
        {"Metric": "Total Transfer Cost", "Value": round(total_transfer_cost, 2)},
        {"Metric": "Remaining Shortage", "Value": round(remaining_shortage, 2)},
        {"Metric": "Total Purchase Quantity", "Value": round(total_purchase_quantity, 2)},
        {"Metric": "Remaining Purchase Cost", "Value": round(remaining_purchase_cost, 2)},
        {"Metric": "Total Proposed Cost", "Value": round(total_proposed_cost, 2)},
        {"Metric": "Number of Transfers", "Value": num_transfers},
        {"Metric": "Number of Purchase-Only Recommendations", "Value": num_purchase_only},
        {"Metric": "Shortage Avoidance Percentage (%)", "Value": round(avoidance_pct, 2)}
    ]
    
    metrics_df = pd.DataFrame(metrics)
    return recs_df, metrics_df


def run_recommender_pipeline(
    intel_path: Optional[Union[str, Path]] = None,
    routes_path: Optional[Union[str, Path]] = None,
    output_dir: Optional[Union[str, Path]] = None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Run complete Phase 3 recommendation pipeline and export output files.
    """
    in_intel = Path(intel_path) if intel_path else PROCESSED_DATA_DIR / "inventory_intelligence.csv"
    out_dir = Path(output_dir) if output_dir else OUTPUTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    
    if not in_intel.exists():
        raise FileNotFoundError(f"Input file not found: {in_intel.resolve()}")
        
    inventory_df = pd.read_csv(in_intel)
    routes_df = load_transfer_routes()
    
    # Load baseline metrics for comparison if present
    baseline_metrics_path = out_dir / "baseline_metrics.csv"
    baseline_metrics_df = pd.read_csv(baseline_metrics_path) if baseline_metrics_path.exists() else None
    
    recs_df, metrics_df = generate_recommendations(inventory_df, routes_df, baseline_metrics_df)
    
    recs_df.to_csv(out_dir / "transfer_recommendations.csv", index=False)
    metrics_df.to_csv(out_dir / "recommendation_metrics.csv", index=False)
    
    return recs_df, metrics_df
