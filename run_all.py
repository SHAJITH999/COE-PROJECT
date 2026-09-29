#!/usr/bin/env python3
"""
Top-Level Complete End-to-End Pipeline Runner.

Executes the complete workflow:
1. Data preparation & validation
2. Demand forecasting & inventory intelligence
3. Transfer & purchase recommendation generation
4. Disruption scenario simulation (NORMAL, DELAY, CAPACITY_LOSS, URGENT_DEMAND)
5. Evaluation & comparative baseline metrics
6. Final validation & error/edge case reporting
7. Pytest test suite execution

Provides deterministic execution, clear stage status (PASS/FAIL),
stops on failure, and returns appropriate exit codes.
"""

import sys
import time
import subprocess
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))


def print_header():
    print("=" * 60)
    print("      COE INVENTORY BALANCING REBALANCING PIPELINE")
    print("=" * 60)
    print(f"Working Directory: {PROJECT_ROOT}\n")


def stage_status(stage_num: int, total_stages: int, name: str, status: str, duration: float):
    dots = "." * max(2, (38 - len(name)))
    print(f"[{stage_num}/{total_stages}] {name} {dots} {status} ({duration:.2f}s)")


def run_pipeline_end_to_end() -> bool:
    print_header()
    total_stages = 6
    start_all = time.time()
    
    # Ensure required directories exist
    (PROJECT_ROOT / "outputs").mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "data" / "processed").mkdir(parents=True, exist_ok=True)
    
    # ── Stage 1: Data Preparation & Validation ──
    t0 = time.time()
    try:
        from src.data.loader import load_all_raw_data
        from src.data.validator import generate_validation_report
        from src.data.pipeline import run_pipeline
        
        raw_datasets = load_all_raw_data()
        val_report = generate_validation_report(raw_datasets)
        val_report.to_csv(PROJECT_ROOT / "outputs" / "data_validation_report.csv", index=False)
        run_pipeline()
        stage_status(1, total_stages, "Data preparation", "PASS", time.time() - t0)
    except Exception as e:
        stage_status(1, total_stages, "Data preparation", "FAIL", time.time() - t0)
        print(f"\nERROR in Stage 1: {e}")
        return False
        
    # ── Stage 2: Forecasting & Intelligence ──
    t0 = time.time()
    try:
        from src.metrics.intelligence import generate_inventory_intelligence
        from src.metrics.baseline import run_baseline_analysis
        
        intel_df = generate_inventory_intelligence()
        baseline_df, results_out, metrics_out = run_baseline_analysis()
        stage_status(2, total_stages, "Forecasting & Intelligence", "PASS", time.time() - t0)
    except Exception as e:
        stage_status(2, total_stages, "Forecasting & Intelligence", "FAIL", time.time() - t0)
        print(f"\nERROR in Stage 2: {e}")
        return False

    # ── Stage 3: Recommendation Generation ──
    t0 = time.time()
    try:
        from src.balancing.recommender import run_recommender_pipeline
        
        recs_df, rec_metrics = run_recommender_pipeline()
        stage_status(3, total_stages, "Recommender", "PASS", time.time() - t0)
    except Exception as e:
        stage_status(3, total_stages, "Recommender", "FAIL", time.time() - t0)
        print(f"\nERROR in Stage 3: {e}")
        return False

    # ── Stage 4: Disruption Simulation ──
    t0 = time.time()
    try:
        from src.simulation.runner import run_all_phase4_experiments
        
        summary_df, safety_df, fairness_df = run_all_phase4_experiments()
        stage_status(4, total_stages, "Simulation", "PASS", time.time() - t0)
    except Exception as e:
        stage_status(4, total_stages, "Simulation", "FAIL", time.time() - t0)
        print(f"\nERROR in Stage 4: {e}")
        return False

    # ── Stage 5: Evaluation & Metrics ──
    t0 = time.time()
    try:
        from src.metrics.analysis import run_analysis
        
        baseline_path = PROJECT_ROOT / "outputs" / "baseline_results.csv"
        if baseline_path.exists():
            base_df = pd.read_csv(baseline_path)
            run_analysis(base_df)
        stage_status(5, total_stages, "Evaluation & Metrics", "PASS", time.time() - t0)
    except Exception as e:
        stage_status(5, total_stages, "Evaluation & Metrics", "FAIL", time.time() - t0)
        print(f"\nERROR in Stage 5: {e}")
        return False

    # ── Stage 6: Validation ──
    t0 = time.time()
    try:
        from src.simulation.validation import run_full_validation_pipeline
        
        err_df, edge_df, val_df, final_df = run_full_validation_pipeline()
        stage_status(6, total_stages, "Validation", "PASS", time.time() - t0)
    except Exception as e:
        stage_status(6, total_stages, "Validation", "FAIL", time.time() - t0)
        print(f"\nERROR in Stage 6: {e}")
        return False

    # ── Stage 7: Test Suite Execution ──
    print("\nRunning test suite...")
    test_start = time.time()
    pytest_cmd = [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=short"]
    test_proc = subprocess.run(pytest_cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
    test_time = time.time() - test_start
    
    print(test_proc.stdout.strip())
    if test_proc.stderr:
        # Filter warnings from stderr display
        err_lines = [l for l in test_proc.stderr.splitlines() if "Warning" not in l]
        if err_lines:
            print("\n".join(err_lines))
            
    if test_proc.returncode != 0:
        print("\nTEST SUITE FAILED!")
        return False
        
    print(f"\nAll tests passed in {test_time:.2f}s.")
    total_time = time.time() - start_all
    print("=" * 60)
    print(f"PIPELINE COMPLETED SUCCESSFULLY in {total_time:.2f}s")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = run_pipeline_end_to_end()
    sys.exit(0 if success else 1)
