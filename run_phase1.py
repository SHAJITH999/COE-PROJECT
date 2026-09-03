"""
Phase 1 Execution & Verification Entry Point.

Executes data loading, dataset validation, validation report generation,
and processed inventory/routes data calculation pipeline.
"""

from pathlib import Path
import sys

from src.data.loader import load_all_raw_data
from src.data.validator import generate_validation_report
from src.data.pipeline import run_pipeline


def main():
    print("=" * 60)
    print("  MULTI-LOCATION INVENTORY BALANCING RECOMMENDER - PHASE 1  ")
    print("=" * 60)
    
    # 1. Load Raw Datasets
    print("\n[1/3] Loading raw datasets from data/raw/...")
    datasets = load_all_raw_data()
    for name, df in datasets.items():
        print(f"  - Loaded '{name}': {len(df)} rows, {len(df.columns)} columns")
        
    # 2. Validate Data & Generate Validation Report
    print("\n[2/3] Validating datasets and generating validation report...")
    report_df = generate_validation_report(datasets)
    report_path = Path("outputs/data_validation_report.csv")
    print(f"  - Validation report successfully generated at: {report_path.resolve()}")
    print("\nValidation Summary Report:")
    print("-" * 60)
    print(report_df.to_string(index=False))
    print("-" * 60)
    
    # 3. Execute Processed Data Pipeline
    print("\n[3/3] Running processed data pipeline...")
    inv_proc, routes_proc = run_pipeline()
    inv_out = Path("data/processed/inventory_processed.csv")
    routes_out = Path("data/processed/routes_processed.csv")
    print(f"  - Processed inventory saved to: {inv_out.resolve()}")
    print(f"    New fields calculated: Inventory_Position, Shortage_Units, Surplus_Units")
    print(f"  - Processed routes saved to: {routes_out.resolve()}")
    
    print("\n" + "=" * 60)
    print("  PHASE 1 PIPELINE EXECUTED SUCCESSFULLY  ")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
