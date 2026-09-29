"""
Inventory Intelligence Module for Multi-Location Inventory Balancing Recommender.

Augments processed inventory data with inventory status, stock coverage ratio,
demand gap, and safety stock gap metrics.
"""

from pathlib import Path
from typing import Optional, Union
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"


def calculate_inventory_status(shortage_units: pd.Series, surplus_units: pd.Series) -> pd.Series:
    """
    Determine Inventory_Status for each record.
    
    Status logic:
    - SHORTAGE if Shortage_Units > 0
    - SURPLUS if Surplus_Units > 0
    - BALANCED otherwise
    """
    conditions = [
        shortage_units > 0,
        surplus_units > 0
    ]
    choices = ["SHORTAGE", "SURPLUS"]
    return pd.Series(np.select(conditions, choices, default="BALANCED"), index=shortage_units.index)


# Import demand features from dedicated forecasting architecture
from src.forecasting.features import (
    calculate_stock_coverage_ratio,
    calculate_demand_gap,
    calculate_safety_stock_gap,
)


def generate_inventory_intelligence(
    input_path: Optional[Union[str, Path]] = None,
    output_path: Optional[Union[str, Path]] = None
) -> pd.DataFrame:
    """
    Load inventory_processed.csv, add intelligence metrics, and save to inventory_intelligence.csv.
    """
    in_file = Path(input_path) if input_path else PROCESSED_DATA_DIR / "inventory_processed.csv"
    out_file = Path(output_path) if output_path else PROCESSED_DATA_DIR / "inventory_intelligence.csv"
    
    if not in_file.exists():
        raise FileNotFoundError(f"Input file not found at: {in_file.resolve()}")
        
    df = pd.read_csv(in_file)
    
    df["Inventory_Status"] = calculate_inventory_status(df["Shortage_Units"], df["Surplus_Units"])
    df["Stock_Coverage_Ratio"] = calculate_stock_coverage_ratio(df["Inventory_Position"], df["Forecast_Demand"])
    df["Demand_Gap"] = calculate_demand_gap(df["Forecast_Demand"], df["Inventory_Position"])
    df["Safety_Stock_Gap"] = calculate_safety_stock_gap(df["Inventory_Position"], df["Safety_Stock"])
    
    out_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_file, index=False)
    
    return df
