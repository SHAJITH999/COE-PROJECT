"""
Streamlit Multi-Page Dashboard for Multi-Location Inventory Balancing Recommender.

Pages:
  1. Network Overview
  2. Recommendations (with Approve / Reject / Override)
  3. Disruption Simulation
  4. Experiment Results
"""

import json
import time
from pathlib import Path

import pandas as pd
import streamlit as st

# ── Import backend modules directly (no API call needed for local dev) ────────
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.loader import load_transfer_routes
from src.balancing.recommender import generate_recommendations
from src.metrics.baseline import calculate_baseline_purchases, calculate_service_level
from src.simulation.scenarios import create_scenario_datasets
from src.simulation.runner import run_single_scenario_experiment
from src.simulation.safety import calculate_safety_metrics
from src.simulation.fairness import calculate_fairness_metrics
from src.api.db import (
    init_db, seed_recommendations, record_decision,
    get_approval_status, get_all_approvals, DB_PATH
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

st.set_page_config(
    page_title="Inventory Balancing Recommender",
    page_icon="📦",
    layout="wide"
)

# ── Sidebar navigation ────────────────────────────────────────────────────────
st.sidebar.title("📦 Inventory Balancing")
page = st.sidebar.radio(
    "Navigate to",
    ["Network Overview", "Recommendations", "Disruption Simulation", "Experiment Results"]
)

# ── Initialise DB ─────────────────────────────────────────────────────────────
init_db()


# ── Cached data loaders ───────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_intelligence():
    path = PROCESSED_DATA_DIR / "inventory_intelligence.csv"
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_recommendations(scenario: str = "NORMAL"):
    inv_df, routes_df = create_scenario_datasets(scenario)
    baseline_metrics = None
    baseline_path = OUTPUTS_DIR / "baseline_metrics.csv"
    if baseline_path.exists():
        baseline_metrics = pd.read_csv(baseline_path)
    recs_df, metrics_df = generate_recommendations(inv_df, routes_df, baseline_metrics)
    seed_recommendations(recs_df.to_dict(orient="records"))
    return recs_df, metrics_df


@st.cache_data(show_spinner=False)
def load_experiment_summary():
    path = OUTPUTS_DIR / "experiment_summary.csv"
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


# ── Status badge helper ───────────────────────────────────────────────────────
STATUS_COLORS = {
    "PENDING": "🟡",
    "APPROVED": "🟢",
    "REJECTED": "🔴",
    "OVERRIDDEN": "🔵",
}


def status_badge(status: str) -> str:
    return f"{STATUS_COLORS.get(status, '⚪')} {status}"


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1: NETWORK OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
if page == "Network Overview":
    st.title("📊 Network Overview")
    st.caption("System-wide inventory health and recommendation summary.")

    intel_df = load_intelligence()

    if intel_df.empty:
        st.warning("Run Phase 2 pipeline first to generate inventory intelligence data.")
        st.stop()

    recs_df, metrics_df = load_recommendations("NORMAL")
    metrics_map = dict(zip(metrics_df["Metric"], metrics_df["Value"])) if not metrics_df.empty else {}

    # KPI Row 1
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🏪 Branches", intel_df["Branch_ID"].nunique())
    col2.metric("📦 Products", intel_df["Product_ID"].nunique())
    col3.metric("⚠️ Shortage Records", int((intel_df["Shortage_Units"] > 0).sum()))
    col4.metric("📈 Surplus Records", int((intel_df["Surplus_Units"] > 0).sum()))

    # KPI Row 2
    col5, col6, col7, col8 = st.columns(4)
    transfer_recs = len(recs_df[recs_df["Shortage_Avoided"] > 0]) if not recs_df.empty else 0
    service_level = metrics_map.get("Shortage Avoidance Percentage (%)", 0)
    avoidance_pct = metrics_map.get("Shortage Avoidance Percentage (%)", 0)
    proposed_cost = metrics_map.get("Total Proposed Cost", 0)

    col5.metric("🔄 Transfer Recommendations", transfer_recs)
    col6.metric("🚫 Purchase Avoided (%)", f"{avoidance_pct:.1f}%")
    col7.metric("📉 Shortage Avoidance", f"{avoidance_pct:.1f}%")
    col8.metric("💰 Total Proposed Cost", f"INR {proposed_cost:,.0f}")

    st.markdown("---")
    st.subheader("Inventory Status Distribution")
    if "Inventory_Status" in intel_df.columns:
        status_counts = intel_df["Inventory_Status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        st.dataframe(status_counts, use_container_width=True, hide_index=True)

    st.subheader("Recommendation Metrics Summary")
    if not metrics_df.empty:
        st.dataframe(metrics_df, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 2: RECOMMENDATIONS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "Recommendations":
    st.title("📋 Transfer & Purchase Recommendations")
    st.caption("Review, approve, reject, or override individual recommendations.")

    scenario_choice = st.selectbox("Select Scenario", ["NORMAL", "DELAY", "CAPACITY_LOSS", "URGENT_DEMAND"])

    with st.spinner("Loading recommendations..."):
        recs_df, _ = load_recommendations(scenario_choice)

    if recs_df.empty:
        st.info("No recommendations generated.")
        st.stop()

    # Merge DB approval statuses
    approvals = {a["recommendation_id"]: a for a in get_all_approvals()}

    # Display filters
    filter_col1, filter_col2 = st.columns(2)
    urgency_filter = filter_col1.multiselect(
        "Filter by Urgency", ["Critical", "High", "Medium", "Low"], default=["Critical", "High", "Medium", "Low"]
    )
    type_filter = filter_col2.multiselect(
        "Filter by Type", ["TRANSFER", "PARTIAL_TRANSFER", "PARTIAL_TRANSFER_AND_PURCHASE", "PURCHASE"],
        default=["TRANSFER", "PARTIAL_TRANSFER", "PARTIAL_TRANSFER_AND_PURCHASE", "PURCHASE"]
    )

    filtered_df = recs_df[
        recs_df["Service_Urgency"].isin(urgency_filter) &
        recs_df["Recommendation_Type"].isin(type_filter)
    ].copy()

    st.write(f"Showing **{len(filtered_df)}** of {len(recs_df)} recommendations")

    for _, row in filtered_df.head(50).iterrows():
        rec_id = str(row["Recommendation_ID"])
        db_rec = approvals.get(rec_id, {})
        current_status = db_rec.get("status", "PENDING")
        high_impact = db_rec.get("is_high_impact", False)

        label = f"{status_badge(current_status)} | `{rec_id}` | **{row['Recommendation_Type']}** | {row['Service_Urgency']} urgency"
        with st.expander(label, expanded=False):
            c1, c2 = st.columns(2)
            c1.write(f"**Source Branch:** {row.get('Source_Branch', 'N/A')}")
            c1.write(f"**Destination Branch:** {row['Destination_Branch']}")
            c1.write(f"**Product ID:** {row['Product_ID']}")
            c1.write(f"**Quantity:** {row['Recommended_Quantity']}")
            c2.write(f"**Transfer Time:** {row['Transfer_Time_Hours']}h")
            c2.write(f"**Estimated Cost:** INR {row['Estimated_Cost']:,.2f}")
            c2.write(f"**Shortage Avoided:** {row['Shortage_Avoided']}")
            c2.write(f"**Purchase Quantity:** {row['Purchase_Quantity']}")

            st.caption("**Evidence:**")
            st.info(str(row.get("Evidence", "")))

            if high_impact:
                st.warning("⚠️ High-Impact Recommendation — requires human confirmation.")

            act_col1, act_col2, act_col3 = st.columns(3)
            if act_col1.button("✅ Approve", key=f"approve_{rec_id}"):
                record_decision(rec_id, "APPROVED")
                st.success(f"Recommendation {rec_id} APPROVED.")
                st.rerun()
            if act_col2.button("❌ Reject", key=f"reject_{rec_id}"):
                record_decision(rec_id, "REJECTED")
                st.warning(f"Recommendation {rec_id} REJECTED.")
                st.rerun()

            override_reason = st.text_input("Override Reason (required for override):", key=f"override_reason_{rec_id}")
            if act_col3.button("🔄 Override", key=f"override_{rec_id}"):
                if not override_reason.strip():
                    st.error("Override reason cannot be empty.")
                else:
                    record_decision(rec_id, "OVERRIDDEN", override_reason=override_reason.strip())
                    st.info(f"Recommendation {rec_id} OVERRIDDEN. Reason: {override_reason.strip()}")
                    st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 3: DISRUPTION SIMULATION
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "Disruption Simulation":
    st.title("⚡ Disruption Simulation")
    st.caption("Evaluate system performance under different disruption scenarios.")

    scenario = st.selectbox(
        "Select Disruption Scenario",
        {
            "NORMAL": "Normal Day — Baseline operating conditions",
            "DELAY": "Transfer Delay — +3h increase in transit time",
            "CAPACITY_LOSS": "Capacity Loss — 50% vehicle capacity reduction",
            "URGENT_DEMAND": "Urgent Demand — +25% demand surge for Critical/High items",
        }.keys(),
        format_func=lambda s: {
            "NORMAL": "🟢 Normal Day",
            "DELAY": "🟡 Transfer Delay (+3h)",
            "CAPACITY_LOSS": "🔴 Capacity Loss (-50%)",
            "URGENT_DEMAND": "🟠 Urgent Demand (+25%)",
        }[s]
    )

    if st.button("▶ Run Simulation", type="primary"):
        with st.spinner(f"Running {scenario} simulation..."):
            metrics, recs_df, rec_metrics_df = run_single_scenario_experiment(scenario)

        st.success(f"Simulation complete: **{scenario}**")
        st.markdown("### Comparative Metrics")

        m_cols = st.columns(4)
        m_cols[0].metric("Baseline Shortage", int(metrics["Baseline Shortage"]))
        m_cols[1].metric("Proposed Shortage", int(metrics["Proposed Shortage"]),
                         delta=f"-{int(metrics['Shortage Avoided'])} avoided", delta_color="normal")
        m_cols[2].metric("Shortage Avoided", f"{metrics['Shortage Avoided (%)']:.1f}%")
        m_cols[3].metric("Safety Violations", int(metrics["Safety Violations"]),
                         delta_color="inverse" if metrics["Safety Violations"] > 0 else "normal")

        m2_cols = st.columns(4)
        m2_cols[0].metric("Baseline Cost (INR)", f"{metrics['Baseline Cost']:,.0f}")
        m2_cols[1].metric("Proposed Cost (INR)", f"{metrics['Proposed Cost']:,.0f}")
        m2_cols[2].metric("Cost Savings (INR)", f"{metrics['Cost Difference']:,.0f}")
        m2_cols[3].metric("Service Level", f"{metrics['Proposed Service Level']:.4f}",
                          delta=f"+{metrics['Service Improvement']:.4f}", delta_color="normal")

        st.markdown("### Recommendation Metrics")
        st.dataframe(rec_metrics_df, use_container_width=True, hide_index=True)

        st.markdown("### Recommendations Preview (first 20)")
        st.dataframe(recs_df.head(20), use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 4: EXPERIMENT RESULTS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "Experiment Results":
    st.title("🔬 Experiment Results")
    st.caption("Baseline vs. proposed system comparison across all four disruption scenarios.")

    summary_df = load_experiment_summary()

    if summary_df.empty:
        st.warning("Run Phase 4 pipeline first to generate experiment summary data.")
        st.stop()

    st.markdown("### Experiment Summary Table")
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### Key Performance Comparisons")

    for _, row in summary_df.iterrows():
        sc = row.get("Scenario", "")
        avoidance = float(row.get("Shortage Avoided", 0))
        baseline_shortage = float(row.get("Baseline Shortage", 1))
        avoidance_pct = avoidance / baseline_shortage * 100 if baseline_shortage > 0 else 0.0

        cost_diff = float(row.get("Cost Difference", 0))
        baseline_sl = float(row.get("Baseline Service Level", 0))
        proposed_sl = float(row.get("Proposed Service Level", 0))
        safety_v = int(row.get("Safety Violations", 0))

        with st.expander(f"📌 Scenario: **{sc}**", expanded=(sc == "NORMAL")):
            cols = st.columns(5)
            cols[0].metric("Shortage Avoided", f"{avoidance_pct:.1f}%")
            cols[1].metric("Cost Savings", f"INR {cost_diff:,.0f}")
            cols[2].metric("Baseline SL", f"{baseline_sl:.4f}")
            cols[3].metric("Proposed SL", f"{proposed_sl:.4f}", delta=f"+{proposed_sl - baseline_sl:.4f}")
            cols[4].metric("Safety Violations", safety_v)

    st.markdown("---")
    # Fairness & Safety from stored CSV files
    col_a, col_b = st.columns(2)

    safety_path = OUTPUTS_DIR / "safety_metrics.csv"
    fairness_path = OUTPUTS_DIR / "fairness_metrics.csv"

    with col_a:
        st.subheader("🛡️ Safety Metrics")
        if safety_path.exists():
            st.dataframe(pd.read_csv(safety_path), use_container_width=True, hide_index=True)

    with col_b:
        st.subheader("⚖️ Fairness Metrics")
        if fairness_path.exists():
            st.dataframe(pd.read_csv(fairness_path), use_container_width=True, hide_index=True)
