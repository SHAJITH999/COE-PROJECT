"""
Data Validation Module for Multi-Location Inventory Balancing Recommender.

Validates raw datasets against schema, data quality, and domain constraint rules:
- Required columns exist
- Reasonable data types
- Missing values and duplicate rows
- Negative stock, demand, and safety stock values
- Invalid transfer times, transfer costs, and vehicle capacities
- Invalid service urgency levels and branch/product identifiers

Generates validation metrics and exports outputs/data_validation_report.csv.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

VALID_SERVICE_URGENCIES = {"Low", "Medium", "High", "Critical"}

REQUIRED_COLUMNS_INVENTORY = [
    "Date", "Branch_ID", "Branch_Name", "State",
    "Product_ID", "Product_Name", "Product_Category",
    "Current_Stock", "Reserved_Stock", "Incoming_Stock",
    "Actual_Demand", "Forecast_Demand", "Safety_Stock",
    "Purchase_Cost", "Service_Urgency", "Supplier_Lead_Time_Days"
]

REQUIRED_COLUMNS_ROUTES = [
    "Source_Branch", "Source_City",
    "Destination_Branch", "Destination_City",
    "Distance_KM", "Transfer_Time_Hours",
    "Transfer_Cost_Per_Unit", "Vehicle_Capacity", "Route_Status"
]

REQUIRED_COLUMNS_RECOMMENDATIONS = [
    "Recommendation_ID", "Date", "Source_Branch", "Destination_Branch",
    "Product_ID", "Recommended_Quantity", "Recommendation_Type",
    "Service_Urgency", "Estimated_Cost", "Shortage_Avoided",
    "Approval_Status", "Evidence", "Override_Reason",
    "Transfer_Time_Hours", "Vehicle_Capacity"
]


def validate_inventory_demand(df: pd.DataFrame) -> Tuple[Dict[str, Union[str, int]], List[str]]:
    """
    Validate inventory_demand dataframe.
    
    Returns:
        Tuple of (metrics dict, list of issue strings).
    """
    issues = []
    
    # 1. Required columns check
    missing_cols = [c for c in REQUIRED_COLUMNS_INVENTORY if c not in df.columns]
    if missing_cols:
        issues.append(f"Missing required columns: {missing_cols}")
    
    # 2. Basic statistics
    num_rows = len(df)
    num_cols = len(df.columns)
    missing_values = int(df.isnull().sum().sum())
    duplicate_rows = int(df.duplicated().sum())
    
    num_branches = int(df["Branch_ID"].nunique()) if "Branch_ID" in df.columns else 0
    num_products = int(df["Product_ID"].nunique()) if "Product_ID" in df.columns else 0
    
    if "Date" in df.columns and not df["Date"].dropna().empty:
        date_min = str(df["Date"].min())
        date_max = str(df["Date"].max())
        date_range = f"{date_min} to {date_max}"
    else:
        date_range = "N/A"
        
    # 3. Domain constraint checks (flag invalid rows)
    invalid_mask = pd.Series(False, index=df.index)
    
    # Negative stock checks
    for col in ["Current_Stock", "Reserved_Stock", "Incoming_Stock"]:
        if col in df.columns:
            invalid_mask |= (df[col] < 0) | df[col].isnull()
            
    # Negative demand checks
    for col in ["Actual_Demand", "Forecast_Demand"]:
        if col in df.columns:
            invalid_mask |= (df[col] < 0) | df[col].isnull()
            
    # Negative safety stock check
    if "Safety_Stock" in df.columns:
        invalid_mask |= (df["Safety_Stock"] < 0) | df["Safety_Stock"].isnull()
        
    # Service urgency check
    if "Service_Urgency" in df.columns:
        invalid_mask |= ~df["Service_Urgency"].isin(VALID_SERVICE_URGENCIES)
        
    # Identifiers check
    if "Branch_ID" in df.columns:
        invalid_mask |= df["Branch_ID"].isnull() | (df["Branch_ID"].astype(str).str.strip() == "")
    if "Product_ID" in df.columns:
        invalid_mask |= df["Product_ID"].isnull() | (df["Product_ID"].astype(str).str.strip() == "")
        
    invalid_records = int(invalid_mask.sum())
    if invalid_records > 0:
        issues.append(f"Found {invalid_records} invalid records violating domain constraints.")
        
    status = "PASS" if len(issues) == 0 and missing_values == 0 and duplicate_rows == 0 else (
        "PASS" if invalid_records == 0 else "FAIL"
    )
    
    metrics = {
        "dataset": "inventory_demand",
        "num_rows": num_rows,
        "num_columns": num_cols,
        "num_branches": num_branches,
        "num_products": num_products,
        "date_range": date_range,
        "missing_values": missing_values,
        "duplicate_rows": duplicate_rows,
        "invalid_records": invalid_records,
        "data_quality_status": status,
    }
    
    return metrics, issues


def validate_transfer_routes(df: pd.DataFrame) -> Tuple[Dict[str, Union[str, int]], List[str]]:
    """
    Validate transfer_routes dataframe.
    
    Returns:
        Tuple of (metrics dict, list of issue strings).
    """
    issues = []
    
    # 1. Required columns check
    missing_cols = [c for c in REQUIRED_COLUMNS_ROUTES if c not in df.columns]
    if missing_cols:
        issues.append(f"Missing required columns: {missing_cols}")
        
    num_rows = len(df)
    num_cols = len(df.columns)
    missing_values = int(df.isnull().sum().sum())
    duplicate_rows = int(df.duplicated().sum())
    
    # Branches (union of source and destination)
    branches = set()
    if "Source_Branch" in df.columns:
        branches.update(df["Source_Branch"].dropna().unique())
    if "Destination_Branch" in df.columns:
        branches.update(df["Destination_Branch"].dropna().unique())
    num_branches = len(branches)
    
    num_products = 0  # Routes do not contain product information
    date_range = "N/A"
    
    # Domain constraint checks
    invalid_mask = pd.Series(False, index=df.index)
    
    if "Transfer_Time_Hours" in df.columns:
        invalid_mask |= (df["Transfer_Time_Hours"] < 0) | df["Transfer_Time_Hours"].isnull()
    if "Transfer_Cost_Per_Unit" in df.columns:
        invalid_mask |= (df["Transfer_Cost_Per_Unit"] < 0) | df["Transfer_Cost_Per_Unit"].isnull()
    if "Vehicle_Capacity" in df.columns:
        invalid_mask |= (df["Vehicle_Capacity"] <= 0) | df["Vehicle_Capacity"].isnull()
        
    if "Source_Branch" in df.columns:
        invalid_mask |= df["Source_Branch"].isnull() | (df["Source_Branch"].astype(str).str.strip() == "")
    if "Destination_Branch" in df.columns:
        invalid_mask |= df["Destination_Branch"].isnull() | (df["Destination_Branch"].astype(str).str.strip() == "")
        
    invalid_records = int(invalid_mask.sum())
    if invalid_records > 0:
        issues.append(f"Found {invalid_records} invalid records violating route constraints.")
        
    status = "PASS" if len(issues) == 0 and missing_values == 0 and duplicate_rows == 0 else (
        "PASS" if invalid_records == 0 else "FAIL"
    )
    
    metrics = {
        "dataset": "transfer_routes",
        "num_rows": num_rows,
        "num_columns": num_cols,
        "num_branches": num_branches,
        "num_products": num_products,
        "date_range": date_range,
        "missing_values": missing_values,
        "duplicate_rows": duplicate_rows,
        "invalid_records": invalid_records,
        "data_quality_status": status,
    }
    
    return metrics, issues


def validate_recommendations_sample(df: pd.DataFrame) -> Tuple[Dict[str, Union[str, int]], List[str]]:
    """
    Validate recommendations_sample dataframe.
    
    Returns:
        Tuple of (metrics dict, list of issue strings).
    """
    issues = []
    
    missing_cols = [c for c in REQUIRED_COLUMNS_RECOMMENDATIONS if c not in df.columns]
    if missing_cols:
        issues.append(f"Missing required columns: {missing_cols}")
        
    num_rows = len(df)
    num_cols = len(df.columns)
    missing_values = int(df.isnull().sum().sum())
    duplicate_rows = int(df.duplicated().sum())
    
    branches = set()
    if "Source_Branch" in df.columns:
        branches.update(df["Source_Branch"].dropna().unique())
    if "Destination_Branch" in df.columns:
        branches.update(df["Destination_Branch"].dropna().unique())
    num_branches = len(branches)
    
    num_products = int(df["Product_ID"].nunique()) if "Product_ID" in df.columns else 0
    
    if "Date" in df.columns and not df["Date"].dropna().empty:
        date_min = str(df["Date"].min())
        date_max = str(df["Date"].max())
        date_range = f"{date_min} to {date_max}"
    else:
        date_range = "N/A"
        
    invalid_mask = pd.Series(False, index=df.index)
    if "Recommended_Quantity" in df.columns:
        invalid_mask |= (df["Recommended_Quantity"] < 0)
    if "Estimated_Cost" in df.columns:
        invalid_mask |= (df["Estimated_Cost"] < 0)
        
    invalid_records = int(invalid_mask.sum())
    status = "PASS" if len(issues) == 0 and invalid_records == 0 else "FAIL"
    
    metrics = {
        "dataset": "recommendations_sample",
        "num_rows": num_rows,
        "num_columns": num_cols,
        "num_branches": num_branches,
        "num_products": num_products,
        "date_range": date_range,
        "missing_values": missing_values,
        "duplicate_rows": duplicate_rows,
        "invalid_records": invalid_records,
        "data_quality_status": status,
    }
    
    return metrics, issues


def generate_validation_report(
    datasets: Dict[str, pd.DataFrame],
    output_path: Optional[Union[str, Path]] = None
) -> pd.DataFrame:
    """
    Validate all datasets and write data_validation_report.csv.
    
    Args:
        datasets: Dict containing pandas DataFrames for 'inventory_demand', 'transfer_routes', 'recommendations_sample'.
        output_path: Optional output CSV file path override.
        
    Returns:
        DataFrame containing validation summary report.
    """
    report_rows = []
    
    if "inventory_demand" in datasets:
        inv_metrics, _ = validate_inventory_demand(datasets["inventory_demand"])
        report_rows.append(inv_metrics)
        
    if "transfer_routes" in datasets:
        routes_metrics, _ = validate_transfer_routes(datasets["transfer_routes"])
        report_rows.append(routes_metrics)
        
    if "recommendations_sample" in datasets:
        recs_metrics, _ = validate_recommendations_sample(datasets["recommendations_sample"])
        report_rows.append(recs_metrics)
        
    report_df = pd.DataFrame(report_rows)
    
    if output_path:
        out_file = Path(output_path)
    else:
        out_file = OUTPUTS_DIR / "data_validation_report.csv"
        
    out_file.parent.mkdir(parents=True, exist_ok=True)
    report_df.to_csv(out_file, index=False)
    
    return report_df
