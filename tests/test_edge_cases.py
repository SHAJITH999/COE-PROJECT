"""
Edge and Failure Cases Test Suite for Multi-Location Inventory Balancing Recommender.

Tests the 6 mandatory operational failure and constraint scenarios:
- CASE 1: No network surplus (graceful purchase fallback)
- CASE 2: Network surplus smaller than shortage (partial transfer + purchase remainder)
- CASE 3: Transfer would breach donor safety stock (transfer capped/rejected, donor protected)
- CASE 4: Transfer arrives after projected deadline (transit time exceeds urgency constraint)
- CASE 5: Vehicle capacity smaller than required quantity (transfer capped at vehicle limit)
- CASE 6: Multiple competing branches for same surplus (prioritizes by urgency/fairness)
"""

import pandas as pd
import pytest

from src.balancing.recommender import generate_recommendations
from src.balancing.donor_selector import DonorPoolState, find_and_rank_donors
from src.balancing.transfer_feasibility import is_route_feasible, get_route_info


@pytest.fixture
def base_routes():
    """Provides standard route configuration between branches B001, B002, B003."""
    return pd.DataFrame([
        {
            "Source_Branch": "B001", "Source_City": "Chennai",
            "Destination_Branch": "B002", "Destination_City": "Coimbatore",
            "Distance_KM": 505, "Transfer_Time_Hours": 9.0,
            "Transfer_Cost_Per_Unit": 12.0, "Vehicle_Capacity": 100,
            "Route_Status": "Available"
        },
        {
            "Source_Branch": "B001", "Source_City": "Chennai",
            "Destination_Branch": "B003", "Destination_City": "Madurai",
            "Distance_KM": 460, "Transfer_Time_Hours": 8.0,
            "Transfer_Cost_Per_Unit": 11.0, "Vehicle_Capacity": 100,
            "Route_Status": "Available"
        },
        {
            "Source_Branch": "B002", "Source_City": "Coimbatore",
            "Destination_Branch": "B003", "Destination_City": "Madurai",
            "Distance_KM": 215, "Transfer_Time_Hours": 4.0,
            "Transfer_Cost_Per_Unit": 7.0, "Vehicle_Capacity": 100,
            "Route_Status": "Available"
        }
    ])


def test_edge_case_1_no_network_surplus(base_routes):
    """
    CASE 1: No network surplus available.
    Expected: Zero internal transfer recommendations; entire shortage routed to PURCHASE.
    """
    inv_df = pd.DataFrame([
        {
            "Date": "2026-07-01", "Branch_ID": "B002", "Product_ID": "P001",
            "Shortage_Units": 30.0, "Surplus_Units": 0.0, "Service_Urgency": "High",
            "Purchase_Cost": 150.0, "Forecast_Demand": 40.0, "Safety_Stock": 10.0,
            "Inventory_Position": 20.0
        },
        # Other branch has no surplus
        {
            "Date": "2026-07-01", "Branch_ID": "B001", "Product_ID": "P001",
            "Shortage_Units": 0.0, "Surplus_Units": 0.0, "Service_Urgency": "Low",
            "Purchase_Cost": 150.0, "Forecast_Demand": 20.0, "Safety_Stock": 5.0,
            "Inventory_Position": 25.0
        }
    ])
    recs, metrics = generate_recommendations(inv_df, base_routes)
    
    assert len(recs) == 1
    rec = recs.iloc[0]
    assert rec["Recommendation_Type"] == "PURCHASE"
    assert rec["Recommended_Quantity"] == 30.0
    assert rec["Shortage_Avoided"] == 0.0
    assert rec["Purchase_Quantity"] == 30.0
    assert "no feasible network transfer" in rec["Evidence"].lower()


def test_edge_case_2_surplus_smaller_than_shortage(base_routes):
    """
    CASE 2: Network surplus is smaller than shortage.
    Expected: Partial transfer covering available surplus, remaining shortage routed to PURCHASE.
    """
    inv_df = pd.DataFrame([
        {
            "Date": "2026-07-01", "Branch_ID": "B002", "Product_ID": "P001",
            "Shortage_Units": 50.0, "Surplus_Units": 0.0, "Service_Urgency": "High",
            "Purchase_Cost": 100.0, "Forecast_Demand": 60.0, "Safety_Stock": 10.0,
            "Inventory_Position": 20.0
        },
        # Donor has only 18 units of usable surplus
        {
            "Date": "2026-07-01", "Branch_ID": "B001", "Product_ID": "P001",
            "Shortage_Units": 0.0, "Surplus_Units": 18.0, "Service_Urgency": "Low",
            "Purchase_Cost": 100.0, "Forecast_Demand": 30.0, "Safety_Stock": 10.0,
            "Inventory_Position": 58.0
        }
    ])
    recs, metrics = generate_recommendations(inv_df, base_routes)
    
    assert len(recs) == 2
    transfer_rec = recs[recs["Recommendation_Type"] == "PARTIAL_TRANSFER"].iloc[0]
    purchase_rec = recs[recs["Recommendation_Type"] == "PARTIAL_TRANSFER_AND_PURCHASE"].iloc[0]
    
    assert transfer_rec["Recommended_Quantity"] == 18.0
    assert transfer_rec["Shortage_Avoided"] == 18.0
    assert transfer_rec["Remaining_Shortage"] == 32.0
    
    assert purchase_rec["Purchase_Quantity"] == 32.0
    assert purchase_rec["Recommended_Quantity"] == 32.0


def test_edge_case_3_donor_safety_stock_protection(base_routes):
    """
    CASE 3: Transfer must never breach donor safety stock.
    Expected: Transfer quantity is strictly bounded by Surplus_Units (Position - Forecast - Safety).
    """
    inv_df = pd.DataFrame([
        {
            "Date": "2026-07-01", "Branch_ID": "B002", "Product_ID": "P001",
            "Shortage_Units": 40.0, "Surplus_Units": 0.0, "Service_Urgency": "High",
            "Purchase_Cost": 100.0
        },
        # Donor inventory position = 100, forecast = 60, safety stock = 25 -> Usable surplus = 15
        {
            "Date": "2026-07-01", "Branch_ID": "B001", "Product_ID": "P001",
            "Shortage_Units": 0.0, "Surplus_Units": 15.0, "Service_Urgency": "Low",
            "Purchase_Cost": 100.0
        }
    ])
    
    donor_pool = DonorPoolState(inv_df)
    avail_surplus = donor_pool.get_available_surplus("2026-07-01", "B001", "P001")
    assert avail_surplus == 15.0  # Exactly 15 units above safety floor
    
    recs, _ = generate_recommendations(inv_df, base_routes)
    transfer_rec = recs[recs["Recommendation_Type"] == "PARTIAL_TRANSFER"].iloc[0]
    assert transfer_rec["Recommended_Quantity"] == 15.0
    assert "safety stock protected" in transfer_rec["Evidence"].lower()


def test_edge_case_4_transfer_time_exceeds_urgency_limit():
    """
    CASE 4: Transfer arrives after urgency deadline.
    Expected: Route is rejected due to urgency constraint; falls back to purchase.
    """
    slow_routes = pd.DataFrame([
        {
            "Source_Branch": "B001", "Source_City": "Chennai",
            "Destination_Branch": "B002", "Destination_City": "Coimbatore",
            "Distance_KM": 505, "Transfer_Time_Hours": 28.0,  # 28h > 24h Critical limit
            "Transfer_Cost_Per_Unit": 10.0, "Vehicle_Capacity": 100,
            "Route_Status": "Available"
        }
    ])
    inv_df = pd.DataFrame([
        {
            "Date": "2026-07-01", "Branch_ID": "B002", "Product_ID": "P001",
            "Shortage_Units": 20.0, "Surplus_Units": 0.0, "Service_Urgency": "Critical",
            "Purchase_Cost": 100.0
        },
        {
            "Date": "2026-07-01", "Branch_ID": "B001", "Product_ID": "P001",
            "Shortage_Units": 0.0, "Surplus_Units": 50.0, "Service_Urgency": "Low",
            "Purchase_Cost": 100.0
        }
    ])
    
    recs, _ = generate_recommendations(inv_df, slow_routes)
    # Since 28h exceeds 24h Critical urgency threshold, transfer cannot be scheduled
    assert len(recs) == 1
    assert recs.iloc[0]["Recommendation_Type"] == "PURCHASE"
    assert recs.iloc[0]["Purchase_Quantity"] == 20.0


def test_edge_case_5_vehicle_capacity_smaller_than_shortage():
    """
    CASE 5: Route vehicle capacity is smaller than required shortage quantity.
    Expected: Transfer quantity is limited to vehicle capacity; remaining shortage purchased.
    """
    small_capacity_routes = pd.DataFrame([
        {
            "Source_Branch": "B001", "Source_City": "Chennai",
            "Destination_Branch": "B002", "Destination_City": "Coimbatore",
            "Distance_KM": 505, "Transfer_Time_Hours": 6.0,
            "Transfer_Cost_Per_Unit": 10.0, "Vehicle_Capacity": 25,  # Capacity = 25
            "Route_Status": "Available"
        }
    ])
    inv_df = pd.DataFrame([
        {
            "Date": "2026-07-01", "Branch_ID": "B002", "Product_ID": "P001",
            "Shortage_Units": 70.0, "Surplus_Units": 0.0, "Service_Urgency": "Medium",
            "Purchase_Cost": 100.0
        },
        # Donor has 80 units surplus (more than vehicle capacity)
        {
            "Date": "2026-07-01", "Branch_ID": "B001", "Product_ID": "P001",
            "Shortage_Units": 0.0, "Surplus_Units": 80.0, "Service_Urgency": "Low",
            "Purchase_Cost": 100.0
        }
    ])
    recs, _ = generate_recommendations(inv_df, small_capacity_routes)
    
    assert len(recs) == 2
    transfer_rec = recs[recs["Recommendation_Type"] == "PARTIAL_TRANSFER"].iloc[0]
    purchase_rec = recs[recs["Recommendation_Type"] == "PARTIAL_TRANSFER_AND_PURCHASE"].iloc[0]
    
    # Capped at Vehicle_Capacity = 25
    assert transfer_rec["Recommended_Quantity"] == 25.0
    assert purchase_rec["Purchase_Quantity"] == 45.0  # 70 - 25 = 45


def test_edge_case_6_competing_branches_prioritize_urgency(base_routes):
    """
    CASE 6: Multiple branches compete for the same donor surplus.
    Expected: Higher urgency recipient receives stock first; lower urgency recipient receives remainder.
    """
    inv_df = pd.DataFrame([
        # Recipient 1: Critical urgency, shortage = 20
        {
            "Date": "2026-07-01", "Branch_ID": "B002", "Product_ID": "P001",
            "Shortage_Units": 20.0, "Surplus_Units": 0.0, "Service_Urgency": "Critical",
            "Purchase_Cost": 100.0
        },
        # Recipient 2: Low urgency, shortage = 20
        {
            "Date": "2026-07-01", "Branch_ID": "B003", "Product_ID": "P001",
            "Shortage_Units": 20.0, "Surplus_Units": 0.0, "Service_Urgency": "Low",
            "Purchase_Cost": 100.0
        },
        # Single Donor B001 has only 20 surplus total
        {
            "Date": "2026-07-01", "Branch_ID": "B001", "Product_ID": "P001",
            "Shortage_Units": 0.0, "Surplus_Units": 20.0, "Service_Urgency": "Low",
            "Purchase_Cost": 100.0
        }
    ])
    
    recs, _ = generate_recommendations(inv_df, base_routes)
    
    # B002 (Critical) should receive the 20 transfer units
    b002_recs = recs[recs["Destination_Branch"] == "B002"]
    assert len(b002_recs) == 1
    assert b002_recs.iloc[0]["Recommendation_Type"] == "TRANSFER"
    assert b002_recs.iloc[0]["Recommended_Quantity"] == 20.0
    
    # B003 (Low) finds donor surplus exhausted -> falls back to PURCHASE
    b003_recs = recs[recs["Destination_Branch"] == "B003"]
    assert len(b003_recs) == 1
    assert b003_recs.iloc[0]["Recommendation_Type"] == "PURCHASE"
    assert b003_recs.iloc[0]["Purchase_Quantity"] == 20.0
