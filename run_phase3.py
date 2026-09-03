"""
Phase 3 Execution & Verification Entry Point.

Executes core multi-location stock transfer recommendation engine,
generates recommendations and recommendation metrics, and compares against
Phase 2 purchase-only baseline.
"""

from pathlib import Path
import pandas as pd

from src.balancing.recommender import run_recommender_pipeline


def main():
    print("=" * 60)
    print("  MULTI-LOCATION INVENTORY BALANCING RECOMMENDER - PHASE 3  ")
    print("=" * 60)
    
    print("\n[1/2] Executing Core Transfer Recommender Engine...")
    recs_df, metrics_df = run_recommender_pipeline()
    
    recs_path = Path("outputs/transfer_recommendations.csv")
    metrics_path = Path("outputs/recommendation_metrics.csv")
    
    print(f"  - Generated recommendations at: {recs_path.resolve()}")
    print(f"    Total recommendation records: {len(recs_df)}")
    print(f"  - Generated recommendation metrics at: {metrics_path.resolve()}")
    
    print("\n[2/2] Recommendation Summary Metrics vs Baseline:")
    print("-" * 60)
    print(metrics_df.to_string(index=False))
    print("-" * 60)
    
    # Load Phase 2 baseline metrics if available for comparative breakdown
    baseline_path = Path("outputs/baseline_metrics.csv")
    if baseline_path.exists():
        base_df = pd.read_csv(baseline_path)
        base_cost_match = base_df[base_df["Metric"] == "Total Purchase Cost"]
        if not base_cost_match.empty:
            base_cost = float(base_cost_match.iloc[0]["Value"])
            prop_cost_match = metrics_df[metrics_df["Metric"] == "Total Proposed Cost"]
            prop_cost = float(prop_cost_match.iloc[0]["Value"]) if not prop_cost_match.empty else 0.0
            
            savings = base_cost - prop_cost
            savings_pct = (savings / base_cost * 100.0) if base_cost > 0 else 0.0
            
            print("\nBaseline Financial Comparison:")
            print(f"  - Phase 2 Baseline Purchase Cost: INR {base_cost:,.2f}")
            print(f"  - Phase 3 Total Proposed Cost:    INR {prop_cost:,.2f}")
            print(f"  - Financial Savings Achieved:     INR {savings:,.2f} ({savings_pct:.2f}% cost reduction)")
            print("-" * 60)
            
    print("\n" + "=" * 60)
    print("  PHASE 3 PIPELINE EXECUTED SUCCESSFULLY  ")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
