"""
Forecast Validation and Quality Evaluation Module.

Evaluates demand forecasting accuracy:
- Mean Absolute Error (MAE)
- Root Mean Squared Error (RMSE)
- Mean Absolute Percentage Error (MAPE)
- Forecast Bias (Mean Error)
- Categorical evaluation across product lines
"""

from typing import Dict, Union
import numpy as np
import pandas as pd


def evaluate_forecast_quality(actual: pd.Series, forecast: pd.Series) -> Dict[str, float]:
    """
    Evaluate forecast quality metrics: MAE, RMSE, MAPE.
    
    Zero handling for MAPE:
    - Excludes records where actual_demand == 0 to avoid division by zero.
    
    Returns:
        Dict with keys: 'Forecast MAE', 'Forecast RMSE', 'Forecast MAPE (%)'.
    """
    actual_s = pd.Series(actual).astype(float)
    forecast_s = pd.Series(forecast).astype(float)
    
    errors = actual_s - forecast_s
    mae = float(np.abs(errors).mean())
    rmse = float(np.sqrt(np.mean(errors ** 2)))
    
    # Non-zero actuals for MAPE
    nz_mask = actual_s != 0
    if nz_mask.sum() > 0:
        mape = float(np.mean(np.abs(errors[nz_mask] / actual_s[nz_mask])) * 100.0)
    else:
        mape = 0.0
        
    return {
        "Forecast MAE": round(mae, 4),
        "Forecast RMSE": round(rmse, 4),
        "Forecast MAPE (%)": round(mape, 4)
    }


def calculate_forecast_bias(actual: pd.Series, forecast: pd.Series) -> float:
    """
    Calculate forecast bias: Mean(Forecast - Actual).
    
    Positive indicates over-forecasting, negative indicates under-forecasting.
    """
    actual_s = pd.Series(actual).astype(float)
    forecast_s = pd.Series(forecast).astype(float)
    return float(np.mean(forecast_s - actual_s))


def evaluate_forecast_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute forecast evaluation metrics partitioned by Product_Category.
    """
    if "Product_Category" not in df.columns or "Actual_Demand" not in df.columns or "Forecast_Demand" not in df.columns:
        return pd.DataFrame()
        
    results = []
    for cat, group in df.groupby("Product_Category"):
        metrics = evaluate_forecast_quality(group["Actual_Demand"], group["Forecast_Demand"])
        metrics["Product_Category"] = cat
        metrics["Record_Count"] = len(group)
        metrics["Forecast_Bias"] = round(calculate_forecast_bias(group["Actual_Demand"], group["Forecast_Demand"]), 4)
        results.append(metrics)
        
    return pd.DataFrame(results)
