# Final Demonstration Guide (5-10 Minute Script)

This script guides a step-by-step 5-10 minute demonstration of the **Multi-Location Inventory Balancing Recommender** prototype.

---

## Prerequisites & Launch Commands
Before starting the demo, launch both services:

```bash
# Terminal 1: REST API
uvicorn src.api.app:app --reload --port 8000

# Terminal 2: Streamlit Dashboard
streamlit run dashboard/app.py
```

---

## Demonstration Script

### Step 1: Explain the Problem (1 min)
- **Action**: Open `docs/PROJECT_CONTEXT.md` or Streamlit **Network Overview** page (`http://localhost:8501`).
- **Talking Point**: "A distributor has 8 branches. Location B001 has a shortage of refrigerators while B004 has surplus stock. Buying new stock from suppliers costs INR 836M. Our system transfers stock between branches before buying new inventory."

### Step 2: Show Shortage vs. Surplus (1 min)
- **Action**: In Streamlit **Network Overview**, highlight the KPI cards:
  - Total Shortage Records: 3,463
  - Total Surplus Records: 3,493
- **Talking Point**: "Notice that surplus units exist across the network at the same time shortages occur."

### Step 3: Run Recommendations & Evidence (2 min)
- **Action**: Navigate to the **Recommendations** page in Streamlit.
- **Action**: Expand recommendation `REC00001`.
- **Talking Point**: "Look at REC00001: Branch B001 needs 84 units of P006. Source B004 has 20 usable surplus units. The recommender creates a 20-unit transfer because route B004 $\rightarrow$ B001 takes 7.1 hours and capacity is 150 units. Safety stock at B004 is completely protected."

### Step 4: Show Human Approval & Override (2 min)
- **Action**: On recommendation `REC00001`, click **Approve**. Show status change to `APPROVED`.
- **Action**: On recommendation `REC00004` (Partial Transfer and Purchase), enter `Override Reason`: *"Manual bulk supplier contract discount active"*. Click **Override**.
- **Talking Point**: "Every recommendation is audited. Overrides require a mandatory written reason, preventing unverified manual changes."

### Step 5: Run Disruption Simulation (2 min)
- **Action**: Navigate to **Disruption Simulation** page.
- **Action**: Select **Capacity Loss (-50%)** scenario and click **Run Simulation**.
- **Talking Point**: "Even when fleet capacity is cut by 50%, the recommender adapts, achieving **62.03% shortage avoidance** while maintaining **0 safety stock violations**."

### Step 6: Compare Baseline vs. Proposed (1 min)
- **Action**: Navigate to **Experiment Results** page.
- **Talking Point**: "Across all scenarios, the system reduces total operating costs from INR 836M to INR 270M — saving over **INR 566 Million (67.68% cost reduction)** and boosting service level from 81.9% to 94.0%."

### Step 7: Address System Limitations (1 min)
- **Action**: Open `docs/limitations.md`.
- **Talking Point**: "This prototype uses static transit times and linear costs. Future work includes live ERP integration and multi-period dynamic programming."
