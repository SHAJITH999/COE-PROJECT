"""
Data Processing Pipeline Module for Multi-Location Inventory Balancing Recommender.

Calculates basic inventory position, shortage units, and surplus units:
- Inventory_Position = Current_Stock + Incoming_Stock - Reserved_Stock
- Shortage_Units = max(0, Forecast_Demand + Safety_Stock - Inventory_Position)
- Surplus_Units = max(0, Inventory_Position - Forecast_Demand - Safety_Stock)

Outputs processed datasets to data/processed/ directory.
"""

from pathlib import Path
from typing import Optional, Tuple, Union
import numpy as np
import pandas as pd

from src.data.loader import load_inventory_demand, load_transfer_routes

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"


def calculate_inventory_position(
    current_stock: Union[int, float, np.ndarray, pd.Series],
    incoming_stock: Union[int, float, np.ndarray, pd.Series],
    reserved_stock: Union[int, float, np.ndarray, pd.Series]
) -> Union[int, float, np.ndarray, pd.Series]:
    """
    Calculate Inventory Position.
    
    Formula: Current_Stock + Incoming_Stock - Reserved_Stock
    """
    return current_stock + incoming_stock - reserved_stock


def calculate_shortage_units(
    forecast_demand: Union[int, float, np.ndarray, pd.Series],
    safety_stock: Union[int, float, np.ndarray, pd.Series],
    inventory_position: Union[int, float, np.ndarray, pd.Series]
) -> Union[int, float, np.ndarray, pd.Series]:
    """
    Calculate Shortage Units.
    
    Formula: max(0, Forecast_Demand + Safety_Stock - Inventory_Position)
    """
    diff = forecast_demand + safety_stock - inventory_position
    if isinstance(diff, (pd.Series, np.ndarray)):
        return np.maximum(0, diff)
    return max(0, diff)


def calculate_surplus_units(
    inventory_position: Union[int, float, np.ndarray, pd.Series],
    forecast_demand: Union[int, float, np.ndarray, pd.Series],
    safety_stock: Union[int, float, np.ndarray, pd.Series]
) -> Union[int, float, np.ndarray, pd.Series]:
    """
    Calculate Surplus Units.
    
    Formula: max(0, Inventory_Position - Forecast_Demand - Safety_Stock)
    """
    diff = inventory_position - forecast_demand - safety_stock
    if isinstance(diff, (pd.Series, np.ndarray)):
        return np.maximum(0, diff)
    return max(0, diff)


def process_inventory_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process raw inventory demand dataset by calculating Inventory_Position,
    Shortage_Units, and Surplus_Units.
    
    Args:
        df: Input raw inventory_demand DataFrame.
        
    Returns:
        DataFrame with new calculated columns.
    """
    processed_df = df.copy()
    
    processed_df["Inventory_Position"] = calculate_inventory_position(
        processed_df["Current_Stock"],
        processed_df["Incoming_Stock"],
        processed_df["Reserved_Stock"]
    )
    
    processed_df["Shortage_Units"] = calculate_shortage_units(
        processed_df["Forecast_Demand"],
        processed_df["Safety_Stock"],
        processed_df["Inventory_Position"]
    )
    
    processed_df["Surplus_Units"] = calculate_surplus_units(
        processed_df["Inventory_Position"],
        processed_df["Forecast_Demand"],
        processed_df["Safety_Stock"]
    )
    
    return processed_df


def process_routes_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process raw transfer routes dataset.
    
    Args:
        df: Input raw transfer_routes DataFrame.
        
    Returns:
        Copy of routes DataFrame.
    """
    return df.copy()


def run_pipeline(
    raw_dir: Optional[Union[str, Path]] = None,
    processed_dir: Optional[Union[str, Path]] = None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Run data processing pipeline: load raw datasets, calculate inventory metrics,
    and save processed CSV files to data/processed/.
    """
    out_dir = Path(processed_dir) if processed_dir else PROCESSED_DATA_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    
    inv_raw = load_inventory_demand(raw_dir)
    routes_raw = load_transfer_routes(raw_dir)
    
    inv_processed = process_inventory_data(inv_raw)
    routes_processed = process_routes_data(routes_raw)
    
    inv_processed.to_csv(out_dir / "inventory_processed.csv", index=False)
    routes_processed.to_csv(out_dir / "routes_processed.csv", index=False)
    
    return inv_processed, routes_processed
