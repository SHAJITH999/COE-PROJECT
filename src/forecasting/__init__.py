"""
src.forecasting package.

Modular architecture for demand forecast handling, validation metrics,
and forecast-derived inventory intelligence features.
"""

from src.forecasting.forecast import (
    extract_forecast_demand,
    get_forecast_horizon,
    scale_forecast_for_scenario,
    get_demand_summary,
)
from src.forecasting.validation import (
    evaluate_forecast_quality,
    calculate_forecast_bias,
    evaluate_forecast_by_category,
)
from src.forecasting.features import (
    calculate_stock_coverage_ratio,
    calculate_demand_gap,
    calculate_safety_stock_gap,
)

__all__ = [
    "extract_forecast_demand",
    "get_forecast_horizon",
    "scale_forecast_for_scenario",
    "get_demand_summary",
    "evaluate_forecast_quality",
    "calculate_forecast_bias",
    "evaluate_forecast_by_category",
    "calculate_stock_coverage_ratio",
    "calculate_demand_gap",
    "calculate_safety_stock_gap",
]
