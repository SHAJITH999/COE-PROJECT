"""
Baseline Purchase Model and Metrics Engine for Multi-Location Inventory Balancing Recommender.

Implements:
1. Purchase-only baseline model (Shortage -> Purchase, ignoring transfer routes)
2. Forecast quality evaluation (MAE, RMSE, MAPE)
3. Aggregate baseline performance metrics and service level calculations
"""

from pathlib import Path
from typing import Dict, Optional, Tuple, Union
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"


def calculate_baseline_purchases(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate baseline purchase quantities and total purchase costs for each record.
    
    Strategy:
    - Purchase_Quantity = Shortage_Units (if Shortage_Units > 0 else 0)
    - Purchase_Cost = Purchase_Quantity * Purchase_Cost (unit price)
    """
    results_df = df.copy()
    
    # Ensure numeric types
    shortage = results_df["Shortage_Units"].fillna(0)
    unit_cost = results_df["Purchase_Cost"].fillna(0)
    
    results_df["Purchase_Quantity"] = shortage.astype(float)
    results_df["Baseline_Purchase_Cost"] = results_df["Purchase_Quantity"] * unit_cost
    
    return results_df


def calculate_service_level(total_shortage: float, total_forecast_demand: float) -> float:
    """
    Calculate Service Level.
    
    Formula: 1 - (Total Shortage Units / Total Forecast Demand)
    Bounded strictly to [0.0, 1.0].
    """
    if total_forecast_demand <= 0:
        return 1.0
    service_level = 1.0 - (total_shortage / total_forecast_demand)
    return float(np.clip(service_level, 0.0, 1.0))


def evaluate_forecast_quality(actual: pd.Series, forecast: pd.Series) -> Dict[str, float]:
    """
    Evaluate existing forecast quality metrics (MAE, RMSE, MAPE).
    
    Zero handling for MAPE:
    - Records with actual_demand == 0 are excluded to prevent division by zero.
    """
    errors = actual - forecast
    mae = float(np.mean(np.abs(errors)))
    rmse = float(np.sqrt(np.mean(errors ** 2)))
    
    # MAPE calculation avoiding division by zero
    non_zero_mask = actual != 0
    if non_zero_mask.sum() > 0:
        mape = float(np.mean(np.abs(errors[non_zero_mask] / actual[non_zero_mask])) * 100.0)
    else:
        mape = 0.0
        
    return {
        "Forecast MAE": round(mae, 4),
        "Forecast RMSE": round(rmse, 4),
        "Forecast MAPE (%)": round(mape, 4)
    }


def compute_baseline_summary(df: pd.DataFrame, forecast_metrics: Dict[str, float]) -> pd.DataFrame:
    """
    Compute comprehensive baseline summary metrics.
    """
    total_forecast_demand = float(df["Forecast_Demand"].sum())
    total_actual_demand = float(df["Actual_Demand"].sum())
    total_shortage_units = float(df["Shortage_Units"].sum())
    total_purchase_quantity = float(df["Purchase_Quantity"].sum())
    total_purchase_cost = float(df["Baseline_Purchase_Cost"].sum())
    total_surplus_units = float(df["Surplus_Units"].sum())
    
    shortage_records = df[df["Shortage_Units"] > 0]
    num_shortage_records = int(len(shortage_records))
    
    affected_branches = int(shortage_records["Branch_ID"].nunique()) if num_shortage_records > 0 else 0
    affected_products = int(shortage_records["Product_ID"].nunique()) if num_shortage_records > 0 else 0
    
    service_level = calculate_service_level(total_shortage_units, total_forecast_demand)
    
    avg_shortage_per_affected = float(shortage_records["Shortage_Units"].mean()) if num_shortage_records > 0 else 0.0
    max_shortage = float(df["Shortage_Units"].max()) if not df["Shortage_Units"].empty else 0.0
    
    metrics = [
        {"Metric": "Total Forecast Demand", "Value": round(total_forecast_demand, 2)},
        {"Metric": "Total Actual Demand", "Value": round(total_actual_demand, 2)},
        {"Metric": "Total Shortage Units", "Value": round(total_shortage_units, 2)},
        {"Metric": "Total Purchase Quantity", "Value": round(total_purchase_quantity, 2)},
        {"Metric": "Total Purchase Cost", "Value": round(total_purchase_cost, 2)},
        {"Metric": "Total Surplus Units", "Value": round(total_surplus_units, 2)},
        {"Metric": "Number of Shortage Records", "Value": num_shortage_records},
        {"Metric": "Affected Branches", "Value": affected_branches},
        {"Metric": "Affected Products", "Value": affected_products},
        {"Metric": "Service Level", "Value": round(service_level, 4)},
        {"Metric": "Average Shortage per Affected Record", "Value": round(avg_shortage_per_affected, 2)},
        {"Metric": "Maximum Shortage", "Value": round(max_shortage, 2)},
        {"Metric": "Forecast MAE", "Value": forecast_metrics["Forecast MAE"]},
        {"Metric": "Forecast RMSE", "Value": forecast_metrics["Forecast RMSE"]},
        {"Metric": "Forecast MAPE (%)", "Value": forecast_metrics["Forecast MAPE (%)"]}
    ]
    
    return pd.DataFrame(metrics)


def run_baseline_analysis(
    input_path: Optional[Union[str, Path]] = None,
    output_dir: Optional[Union[str, Path]] = None
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Run complete baseline purchase model and metric calculations.
    """
    in_file = Path(input_path) if input_path else PROCESSED_DATA_DIR / "inventory_intelligence.csv"
    out_dir = Path(output_dir) if output_dir else OUTPUTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    
    if not in_file.exists():
        raise FileNotFoundError(f"Input inventory intelligence file not found at: {in_file.resolve()}")
        
    df = pd.read_csv(in_file)
    
    # 1. Apply baseline purchase model
    df_baseline = calculate_baseline_purchases(df)
    
    # Select columns for outputs/baseline_results.csv
    cols_baseline_results = [
        "Date", "Branch_ID", "Product_ID", "Forecast_Demand", "Actual_Demand",
        "Inventory_Position", "Safety_Stock", "Shortage_Units", "Surplus_Units",
        "Inventory_Status", "Purchase_Quantity", "Baseline_Purchase_Cost", "Service_Urgency"
    ]
    
    # Rename Baseline_Purchase_Cost to Purchase_Cost for output matching spec
    df_results_output = df_baseline[cols_baseline_results].copy()
    df_results_output.rename(columns={"Baseline_Purchase_Cost": "Purchase_Cost"}, inplace=True)
    
    df_results_output.to_csv(out_dir / "baseline_results.csv", index=False)
    
    # 2. Evaluate Forecast Quality
    forecast_metrics_dict = evaluate_forecast_quality(df_baseline["Actual_Demand"], df_baseline["Forecast_Demand"])
    forecast_df = pd.DataFrame([
        {"Metric": k, "Value": v} for k, v in forecast_metrics_dict.items()
    ])
    forecast_df.to_csv(out_dir / "forecast_metrics.csv", index=False)
    
    # 3. Compute Summary Baseline Metrics
    baseline_metrics_df = compute_baseline_summary(df_baseline, forecast_metrics_dict)
    baseline_metrics_df.to_csv(out_dir / "baseline_metrics.csv", index=False)
    
    return df_baseline, df_results_output, baseline_metrics_df
