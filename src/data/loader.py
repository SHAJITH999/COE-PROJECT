"""
Data Loading Module for Multi-Location Inventory Balancing Recommender.

Provides pathlib-based data loading functions for raw datasets without hardcoded absolute paths.
Raises clear FileNotFoundError exceptions if files are missing.
"""

from pathlib import Path
from typing import Dict, Optional, Union
import pandas as pd

# Dynamically resolve project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def get_raw_data_dir(custom_path: Optional[Union[str, Path]] = None) -> Path:
    """
    Get the path to the raw data directory.
    
    Args:
        custom_path: Optional custom directory path override.
        
    Returns:
        Path object pointing to raw data directory.
    """
    if custom_path:
        return Path(custom_path)
    return RAW_DATA_DIR


def load_inventory_demand(data_dir: Optional[Union[str, Path]] = None) -> pd.DataFrame:
    """
    Load inventory_demand.csv from raw data directory.
    
    Args:
        data_dir: Optional directory path override.
        
    Returns:
        pandas DataFrame containing inventory and demand data.
        
    Raises:
        FileNotFoundError: If the dataset file does not exist.
    """
    target_dir = get_raw_data_dir(data_dir)
    file_path = target_dir / "inventory_demand.csv"
    
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(
            f"Required dataset 'inventory_demand.csv' not found at: {file_path.resolve()}"
        )
    
    return pd.read_csv(file_path)


def load_transfer_routes(data_dir: Optional[Union[str, Path]] = None) -> pd.DataFrame:
    """
    Load transfer_routes.csv from raw data directory.
    
    Args:
        data_dir: Optional directory path override.
        
    Returns:
        pandas DataFrame containing transfer route details.
        
    Raises:
        FileNotFoundError: If the dataset file does not exist.
    """
    target_dir = get_raw_data_dir(data_dir)
    file_path = target_dir / "transfer_routes.csv"
    
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(
            f"Required dataset 'transfer_routes.csv' not found at: {file_path.resolve()}"
        )
    
    return pd.read_csv(file_path)


def load_recommendations_sample(data_dir: Optional[Union[str, Path]] = None) -> pd.DataFrame:
    """
    Load recommendations_sample.csv from raw data directory.
    
    Args:
        data_dir: Optional directory path override.
        
    Returns:
        pandas DataFrame containing sample recommendation data.
        
    Raises:
        FileNotFoundError: If the dataset file does not exist.
    """
    target_dir = get_raw_data_dir(data_dir)
    file_path = target_dir / "recommendations_sample.csv"
    
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(
            f"Required dataset 'recommendations_sample.csv' not found at: {file_path.resolve()}"
        )
    
    return pd.read_csv(file_path)


def load_all_raw_data(data_dir: Optional[Union[str, Path]] = None) -> Dict[str, pd.DataFrame]:
    """
    Load all raw datasets into a dictionary.
    
    Args:
        data_dir: Optional directory path override.
        
    Returns:
        Dictionary mapping dataset name to pandas DataFrame.
    """
    return {
        "inventory_demand": load_inventory_demand(data_dir),
        "transfer_routes": load_transfer_routes(data_dir),
        "recommendations_sample": load_recommendations_sample(data_dir),
    }
