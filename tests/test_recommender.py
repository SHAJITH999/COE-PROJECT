"""
Unit tests for Phase 3 Core Multi-Location Transfer Recommender:
- Successful full transfer
- Partial transfer
- No donor available (purchase fallback)
- Safety stock protection (donor never drops below safety stock)
- Vehicle capacity limit enforcement
- Route availability constraints
- Transfer time service urgency limits
- Same-product matching
- Transfer & purchase cost calculations
- Remaining purchase quantity calculation
- Recommendation evidence generation
"""

import pandas as pd
import pytest

from src.balancing.shortage_detector import detect_shortages
from src.balancing.transfer_feasibility import is_route_feasible, get_route_info
from src.balancing.donor_selector import DonorPoolState, find_and_rank_donors
from src.balancing.recommender import generate_recommendations


@pytest.fixture
def sample_routes():
    return pd.DataFrame([
        {
            "Source_Branch": "B001",
            "Source_City": "Chennai",
            "Destination_Branch": "B002",
            "Destination_City": "Coimbatore",
            "Distance_KM": 500,
            "Transfer_Time_Hours": 6.0,
            "Transfer_Cost_Per_Unit": 10.0,
            "Vehicle_Capacity": 100,
            "Route_Status": "Available"
        },
        {
            "Source_Branch": "B003",
            "Source_City": "Madurai",
            "Destination_Branch": "B002",
            "Destination_City": "Coimbatore",
            "Distance_KM": 200,
            "Transfer_Time_Hours": 3.0,
            "Transfer_Cost_Per_Unit": 5.0,
            "Vehicle_Capacity": 50,
            "Route_Status": "Available"
        },
        {
            "Source_Branch": "B004",
            "Source_City": "Salem",
            "Destination_Branch": "B002",
            "Destination_City": "Coimbatore",
            "Distance_KM": 160,
            "Transfer_Time_Hours": 2.5,
            "Transfer_Cost_Per_Unit": 4.0,
            "Vehicle_Capacity": 100,
            "Route_Status": "Unavailable"
        }
    ])


def test_successful_full_transfer(sample_routes):
    """Test full transfer satisfying recipient shortage completely."""
    inv_df = pd.DataFrame([
        # Recipient shortage: Shortage_Units = 20
        {
            "Date": "2026-07-01", "Branch_ID": "B002", "Product_ID": "P001",
            "Shortage_Units": 20.0, "Surplus_Units": 0.0, "Service_Urgency": "High",
            "Purchase_Cost": 100.0, "Forecast_Demand": 30.0, "Safety_Stock": 5.0, "Inventory_Position": 15.0
        },
        # Donor B001: Usable Surplus = 50
        {
            "Date": "2026-07-01", "Branch_ID": "B001", "Product_ID": "P001",
            "Shortage_Units": 0.0, "Surplus_Units": 50.0, "Service_Urgency": "Low",
            "Purchase_Cost": 100.0, "Forecast_Demand": 20.0, "Safety_Stock": 10.0, "Inventory_Position": 80.0
        }
    ])
    
    recs, metrics = generate_recommendations(inv_df, sample_routes)
    
    assert len(recs) == 1
    row = recs.iloc[0]
    assert row["Recommendation_Type"] == "TRANSFER"
    assert row["Source_Branch"] == "B001"
    assert row["Destination_Branch"] == "B002"
    assert row["Recommended_Quantity"] == 20.0
    assert row["Shortage_Avoided"] == 20.0
    assert row["Remaining_Shortage"] == 0.0
    assert row["Purchase_Quantity"] == 0.0


def test_partial_transfer_and_purchase_fallback(sample_routes):
    """Test partial transfer when donor surplus is less than shortage."""
    inv_df = pd.DataFrame([
        # Recipient shortage = 40
        {
            "Date": "2026-07-01", "Branch_ID": "B002", "Product_ID": "P001",
            "Shortage_Units": 40.0, "Surplus_Units": 0.0, "Service_Urgency": "High",
            "Purchase_Cost": 100.0, "Forecast_Demand": 50.0, "Safety_Stock": 10.0, "Inventory_Position": 20.0
        },
        # Donor B001: Usable surplus = 15
        {
            "Date": "2026-07-01", "Branch_ID": "B001", "Product_ID": "P001",
            "Shortage_Units": 0.0, "Surplus_Units": 15.0, "Service_Urgency": "Low",
            "Purchase_Cost": 100.0, "Forecast_Demand": 20.0, "Safety_Stock": 10.0, "Inventory_Position": 45.0
        }
    ])
    
    recs, metrics = generate_recommendations(inv_df, sample_routes)
    
    # Expect 1 TRANSFER (15 units) and 1 PURCHASE (25 units)
    assert len(recs) == 2
    
    transfer_rec = recs[recs["Recommendation_Type"] == "TRANSFER"].iloc[0]
    assert transfer_rec["Recommended_Quantity"] == 15.0
    assert transfer_rec["Remaining_Shortage"] == 25.0
    
    purchase_rec = recs[recs["Recommendation_Type"] == "PARTIAL_TRANSFER_AND_PURCHASE"].iloc[0]
    assert purchase_rec["Purchase_Quantity"] == 25.0
    assert purchase_rec["Recommended_Quantity"] == 25.0


def test_no_donor_available(sample_routes):
    """Test fallback to purchase when no donor exists."""
    inv_df = pd.DataFrame([
        {
            "Date": "2026-07-01", "Branch_ID": "B002", "Product_ID": "P001",
            "Shortage_Units": 30.0, "Surplus_Units": 0.0, "Service_Urgency": "High",
            "Purchase_Cost": 150.0, "Forecast_Demand": 50.0, "Safety_Stock": 10.0, "Inventory_Position": 30.0
        }
    ])
    
    recs, metrics = generate_recommendations(inv_df, sample_routes)
    
    assert len(recs) == 1
    row = recs.iloc[0]
    assert row["Recommendation_Type"] == "PURCHASE"
    assert row["Purchase_Quantity"] == 30.0
    assert row["Source_Branch"] == ""
    assert row["Shortage_Avoided"] == 0.0


def test_donor_cannot_violate_safety_stock(sample_routes):
    """Verify donor available surplus protects safety stock."""
    inv_df = pd.DataFrame([
        # Recipient shortage = 30
        {
            "Date": "2026-07-01", "Branch_ID": "B002", "Product_ID": "P001",
            "Shortage_Units": 30.0, "Surplus_Units": 0.0, "Service_Urgency": "Medium",
            "Purchase_Cost": 100.0
        },
        # Donor B001 has Surplus_Units = 10 (protected above safety stock)
        {
            "Date": "2026-07-01", "Branch_ID": "B001", "Product_ID": "P001",
            "Shortage_Units": 0.0, "Surplus_Units": 10.0, "Service_Urgency": "Low",
            "Purchase_Cost": 100.0
        }
    ])
    
    donor_state = DonorPoolState(inv_df)
    # Available surplus must equal Surplus_Units = 10.0
    avail = donor_state.get_available_surplus("2026-07-01", "B001", "P001")
    assert avail == 10.0
    
    recs, metrics = generate_recommendations(inv_df, sample_routes)
    t_rec = recs[recs["Recommendation_Type"] == "TRANSFER"].iloc[0]
    assert t_rec["Recommended_Quantity"] == 10.0  # Cannot transfer more than 10.0


def test_transfer_cannot_exceed_capacity(sample_routes):
    """Verify transfer is capped by Vehicle_Capacity."""
    # Route B003 -> B002 has capacity 50
    inv_df = pd.DataFrame([
        # Recipient shortage = 80
        {
            "Date": "2026-07-01", "Branch_ID": "B002", "Product_ID": "P001",
            "Shortage_Units": 80.0, "Surplus_Units": 0.0, "Service_Urgency": "High",
            "Purchase_Cost": 100.0
        },
        # Donor B003: Surplus_Units = 100
        {
            "Date": "2026-07-01", "Branch_ID": "B003", "Product_ID": "P001",
            "Shortage_Units": 0.0, "Surplus_Units": 100.0, "Service_Urgency": "Low",
            "Purchase_Cost": 100.0
        }
    ])
    
    recs, metrics = generate_recommendations(inv_df, sample_routes)
    t_rec = recs[recs["Recommendation_Type"] == "TRANSFER"].iloc[0]
    # Capped at Vehicle_Capacity = 50
    assert t_rec["Recommended_Quantity"] == 50.0


def test_route_unavailable_rejection(sample_routes):
    """Verify unavailable route is rejected."""
    # Route B004 -> B002 is 'Unavailable'
    inv_df = pd.DataFrame([
        {
            "Date": "2026-07-01", "Branch_ID": "B002", "Product_ID": "P001",
            "Shortage_Units": 20.0, "Surplus_Units": 0.0, "Service_Urgency": "High",
            "Purchase_Cost": 100.0
        },
        {
            "Date": "2026-07-01", "Branch_ID": "B004", "Product_ID": "P001",
            "Shortage_Units": 0.0, "Surplus_Units": 50.0, "Service_Urgency": "Low",
            "Purchase_Cost": 100.0
        }
    ])
    
    recs, metrics = generate_recommendations(inv_df, sample_routes)
    # B004 should be rejected due to Route_Status = 'Unavailable' -> fallback to PURCHASE
    assert len(recs) == 1
    assert recs.iloc[0]["Recommendation_Type"] == "PURCHASE"


def test_transfer_time_service_urgency(sample_routes):
    """Verify transfer time feasibility under service urgency."""
    route_info = sample_routes.iloc[0]  # 6.0 hours
    # Critical allows up to 24h -> True
    feasible, _ = is_route_feasible(route_info, "Critical")
    assert feasible is True


def test_same_product_matching(sample_routes):
    """Verify donor is matched ONLY for the same Product_ID."""
    inv_df = pd.DataFrame([
        # Recipient needs P001
        {
            "Date": "2026-07-01", "Branch_ID": "B002", "Product_ID": "P001",
            "Shortage_Units": 20.0, "Surplus_Units": 0.0, "Service_Urgency": "High",
            "Purchase_Cost": 100.0
        },
        # Donor has surplus for P002 (different product)
        {
            "Date": "2026-07-01", "Branch_ID": "B001", "Product_ID": "P002",
            "Shortage_Units": 0.0, "Surplus_Units": 50.0, "Service_Urgency": "Low",
            "Purchase_Cost": 100.0
        }
    ])
    
    recs, metrics = generate_recommendations(inv_df, sample_routes)
    # Should not match P002 donor for P001 recipient
    assert recs.iloc[0]["Recommendation_Type"] == "PURCHASE"


def test_transfer_cost_calculation(sample_routes):
    """Verify transfer cost = Recommended_Quantity * Transfer_Cost_Per_Unit."""
    inv_df = pd.DataFrame([
        {
            "Date": "2026-07-01", "Branch_ID": "B002", "Product_ID": "P001",
            "Shortage_Units": 10.0, "Surplus_Units": 0.0, "Service_Urgency": "High",
            "Purchase_Cost": 100.0
        },
        {
            "Date": "2026-07-01", "Branch_ID": "B001", "Product_ID": "P001",
            "Shortage_Units": 0.0, "Surplus_Units": 50.0, "Service_Urgency": "Low",
            "Purchase_Cost": 100.0
        }
    ])
    
    recs, metrics = generate_recommendations(inv_df, sample_routes)
    t_rec = recs.iloc[0]
    # Qty = 10, Route cost per unit = 10.0 -> Estimated_Cost = 100.0
    assert t_rec["Estimated_Cost"] == 100.0


def test_evidence_string_generation(sample_routes):
    """Verify non-empty explainability evidence string is generated."""
    inv_df = pd.DataFrame([
        {
            "Date": "2026-07-01", "Branch_ID": "B002", "Product_ID": "P001",
            "Shortage_Units": 10.0, "Surplus_Units": 0.0, "Service_Urgency": "High",
            "Purchase_Cost": 100.0
        },
        {
            "Date": "2026-07-01", "Branch_ID": "B001", "Product_ID": "P001",
            "Shortage_Units": 0.0, "Surplus_Units": 50.0, "Service_Urgency": "Low",
            "Purchase_Cost": 100.0
        }
    ])
    
    recs, metrics = generate_recommendations(inv_df, sample_routes)
    evidence = str(recs.iloc[0]["Evidence"])
    assert len(evidence) > 0
    assert "safety stock protected" in evidence.lower()
