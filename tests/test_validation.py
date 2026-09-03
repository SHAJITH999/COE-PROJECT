"""
Unit tests for Phase 6:
- Error analysis CSV generation
- Edge case results validation
- Prototype stakeholder validation acceptance calculation
- Final metrics compilation accuracy
"""

import pandas as pd
import pytest

from src.simulation.validation import (
    generate_error_analysis,
    generate_edge_case_results,
    generate_stakeholder_validation,
    generate_final_metrics,
    run_full_validation_pipeline
)


def test_generate_error_analysis():
    """Verify error analysis dataframe contains required columns and cases."""
    df = generate_error_analysis()
    assert not df.empty
    assert len(df) == 7
    required_cols = ["Case", "Branch", "Product", "Scenario", "Expected Behavior", "Actual Behavior", "Reason", "Impact", "Resolution/Fallback"]
    for col in required_cols:
        assert col in df.columns


def test_generate_edge_case_results():
    """Verify edge case results contain 5 edge cases all marked PASS."""
    df = generate_edge_case_results()
    assert len(df) == 5
    assert (df["Status"] == "PASS").all()


def test_generate_stakeholder_validation():
    """Verify prototype stakeholder validation acceptance rate calculation."""
    recs_df = pd.DataFrame([
        {"Recommendation_ID": "REC00001", "Recommendation_Type": "TRANSFER", "Service_Urgency": "High", "Evidence": "Sample evidence"}
    ] * 50)
    
    val_df, summary = generate_stakeholder_validation(recs_df)
    assert len(val_df) == 50
    assert summary["Validation Cases"] == 50
    assert summary["Validation Acceptance (%)"] > 0.0


def test_generate_final_metrics():
    """Verify final metrics compilation contains NORMAL scenario metrics."""
    df = generate_final_metrics()
    assert not df.empty
    assert "NORMAL" in df["Scenario"].values
    assert "Safety Violations" in df["Metric"].values


def test_run_full_validation_pipeline(tmp_path):
    """Verify full validation pipeline exports all four required CSV files."""
    err_df, edge_df, val_df, final_df = run_full_validation_pipeline(output_dir=tmp_path)
    
    assert (tmp_path / "error_analysis.csv").exists()
    assert (tmp_path / "edge_case_results.csv").exists()
    assert (tmp_path / "stakeholder_validation.csv").exists()
    assert (tmp_path / "final_metrics.csv").exists()
