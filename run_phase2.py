"""
Phase 2 Execution & Verification Entry Point.

Executes inventory intelligence generation, purchase-only baseline execution,
forecast evaluation, baseline metrics generation, and summary analysis reports.
"""

from pathlib import Path
import pandas as pd

from src.metrics.intelligence import generate_inventory_intelligence
from src.metrics.baseline import run_baseline_analysis
from src.metrics.analysis import run_analysis


def main():
    print("=" * 60)
    print("  MULTI-LOCATION INVENTORY BALANCING RECOMMENDER - PHASE 2  ")
    print("=" * 60)
    
    # 1. Inventory Intelligence Layer
    print("\n[1/3] Generating inventory intelligence dataset...")
    intel_df = generate_inventory_intelligence()
    intel_path = Path("data/processed/inventory_intelligence.csv")
    print(f"  - Generated intelligence dataset at: {intel_path.resolve()}")
    print(f"  - Total records: {len(intel_df)}")
    print(f"  - Status distribution:")
    print(intel_df["Inventory_Status"].value_counts().to_string(header=False))
    
    # 2. Purchase-Only Baseline & Metrics Evaluation
    print("\n[2/3] Executing Purchase-Only Baseline model & metrics...")
    baseline_df, results_out, metrics_out = run_baseline_analysis()
    print("  - Generated baseline results at: outputs/baseline_results.csv")
    print("  - Generated forecast metrics at: outputs/forecast_metrics.csv")
    print("  - Generated baseline summary metrics at: outputs/baseline_metrics.csv")
    print("\nBaseline Summary Metrics:")
    print("-" * 60)
    print(metrics_out.to_string(index=False))
    print("-" * 60)
    
    # 3. Summary Analysis Reports
    print("\n[3/3] Generating summary analysis reports...")
    summaries = run_analysis(baseline_df)
    print("  - outputs/branch_shortage_summary.csv")
    print("  - outputs/product_shortage_summary.csv")
    print("  - outputs/branch_surplus_summary.csv")
    print("  - outputs/urgency_summary.csv")
    
    print("\n" + "=" * 60)
    print("  PHASE 2 PIPELINE EXECUTED SUCCESSFULLY  ")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
