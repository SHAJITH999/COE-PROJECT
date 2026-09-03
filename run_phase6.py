"""
Phase 6 Execution & Final End-to-End Validation Entry Point.

Executes full end-to-end validation pipeline across all project phases,
generates error analysis, edge case verification, stakeholder validation,
and final comparative metrics report.
"""

from pathlib import Path
import pandas as pd

from src.simulation.validation import run_full_validation_pipeline


def main():
    print("=" * 60)
    print("  MULTI-LOCATION INVENTORY BALANCING RECOMMENDER - PHASE 6  ")
    print("=" * 60)
    
    print("\n[1/3] Running full end-to-end validation & error analysis...")
    err_df, edge_df, val_df, final_df = run_full_validation_pipeline()
    
    print("  - Generated outputs/error_analysis.csv")
    print("  - Generated outputs/edge_case_results.csv")
    print("  - Generated outputs/stakeholder_validation.csv")
    print("  - Generated outputs/final_metrics.csv")
    
    print("\n[2/3] Edge Case Validation Results:")
    print("-" * 60)
    print(edge_df[["Edge_Case", "Scenario", "Expected_Outcome", "Status"]].to_string(index=False))
    print("-" * 60)
    
    print("\n[3/3] Final Comparative Metrics Summary (NORMAL Scenario):")
    print("-" * 60)
    norm_metrics = final_df[final_df["Scenario"] == "NORMAL"]
    print(norm_metrics[["Metric", "Baseline", "Proposed", "Improvement"]].to_string(index=False))
    print("-" * 60)
    
    val_cases = len(val_df)
    accepted = len(val_df[val_df["Reviewer_Decision"] == "ACCEPTED"])
    acc_pct = (accepted / max(1, val_cases)) * 100.0
    print(f"\nStakeholder Prototype Review Acceptance: {accepted}/{val_cases} ({acc_pct:.1f}%)")
    
    print("\n" + "=" * 60)
    print("  PHASE 6 FINAL VALIDATION EXECUTED SUCCESSFULLY  ")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
