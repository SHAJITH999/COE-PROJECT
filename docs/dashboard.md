# Streamlit Dashboard User Guide

## Starting the Dashboard
```bash
streamlit run dashboard/app.py
```
Opens at `http://localhost:8501`

## Pages

### 1. Network Overview
- System-wide KPIs: Branches, Products, Shortage & Surplus records, Transfer count, Cost.
- Inventory Status Distribution table.
- Recommendation Metrics Summary.

### 2. Recommendations
- Select scenario from dropdown.
- Filter by Service Urgency and Recommendation Type.
- Each recommendation expands to show full details, evidence, and action buttons.
- **Approve**: Marks recommendation as APPROVED.
- **Reject**: Marks recommendation as REJECTED.
- **Override**: Requires a non-empty Override Reason text field.
- High-impact recommendations are flagged with a warning banner.

### 3. Disruption Simulation
- Select scenario: Normal Day, Transfer Delay, Capacity Loss, Urgent Demand.
- Click "Run Simulation" to compare baseline vs proposed metrics.
- Displays KPI metrics, recommendation metrics table, and first 20 recommendations.

### 4. Experiment Results
- Loads pre-generated experiment summary from `outputs/experiment_summary.csv`.
- Displays comparative metrics per scenario.
- Includes Safety Metrics and Fairness Metrics panels.
