"""
Phase 4 Execution & Verification Entry Point.

Executes disruption experiments (NORMAL, DELAY, CAPACITY_LOSS, URGENT_DEMAND),
evaluates safety and fairness metrics, and generates comparison reports.
"""

from pathlib import Path
import pandas as pd

from src.simulation.runner import run_all_phase4_experiments


def main():
    print("=" * 60)
    print("  MULTI-LOCATION INVENTORY BALANCING RECOMMENDER - PHASE 4  ")
    print("=" * 60)
    
    print("\n[1/2] Running disruption scenario experiments (NORMAL, DELAY, CAPACITY_LOSS, URGENT_DEMAND)...")
    summary_df, safety_df, fairness_df = run_all_phase4_experiments()
    
    print("  - Generated outputs/scenario_results.csv")
    print("  - Generated outputs/normal_day_results.csv")
    print("  - Generated outputs/delay_results.csv")
    print("  - Generated outputs/capacity_loss_results.csv")
    print("  - Generated outputs/urgent_demand_results.csv")
    print("  - Generated outputs/fairness_metrics.csv")
    print("  - Generated outputs/safety_metrics.csv")
    print("  - Generated outputs/experiment_summary.csv")
    
    print("\n[2/2] Phase 4 Experiment Summary:")
    print("-" * 60)
    exp_summary_path = Path("outputs/experiment_summary.csv")
    exp_summary_df = pd.read_csv(exp_summary_path)
    print(exp_summary_df.to_string(index=False))
    print("-" * 60)
    
    print("\nSafety Rules Status:")
    print(safety_df.to_string(index=False))
    print("-" * 60)
    
    print("\nFairness Metrics Status:")
    print(fairness_df.to_string(index=False))
    print("-" * 60)
    
    print("\n" + "=" * 60)
    print("  PHASE 4 DISRUPTION EXPERIMENTS EXECUTED SUCCESSFULLY  ")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
