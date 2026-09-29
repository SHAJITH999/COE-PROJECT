# Stakeholder Validation Report & Evaluation Protocol

## 1. Validation Status
- **Automated Prototype Simulation**: COMPLETED (`outputs/stakeholder_validation.csv`)
- **Live Human Stakeholder Review**: **PENDING MANUAL VERIFICATION**
  *(In accordance with project quality guidelines, live feedback from external human operators cannot be automated and is explicitly recorded as pending manual verification).*

---

## 2. Validation Objectives
Evaluate the operational suitability, explainability, dashboard ergonomics, and human approval workflow with distribution inventory managers and logistics planners.

Evaluators are tasked with testing 5 specific business workflows:
1. **Identify a Shortage**: Spot critical and high-urgency stockouts on the Network Overview page.
2. **Review a Transfer Recommendation**: Examine donor selection, route selection, and cost breakdown.
3. **Inspect Explainability Evidence**: Verify WHY the source branch was selected and WHY donor safety stock is protected.
4. **Execute Governance Action**: Perform Approve, Reject, and Override actions (verifying that override requires a mandatory justification).
5. **Run Disruption Simulations**: Trigger and inspect delay, capacity loss, and demand surge scenarios.

---

## 3. Prototype Review Simulation Results
Under automated prototype testing across 50 representative recommendation cases (`outputs/stakeholder_validation.csv`):
- **Total Cases Sampled**: 50 recommendations (Critical, High, Medium, and Low SKUs)
- **Accepted / Approved**: 46 cases (92.0%)
- **Needs Override**: 2 cases (4.0%) — Triggered by simulated operational batching preferences.
- **Rejected**: 2 cases (4.0%) — Simulated seasonal deferral.
- **Safety Invariant**: 100% of transfer recommendations strictly respected donor safety stock limits.

---

## 4. Human Stakeholder Evaluation Protocol (Manual Verification Guide)

For human evaluators conducting manual acceptance testing:

### Reviewer Profile
- **Target Roles**: Branch Logistics Planner, Central Inventory Controller, Warehouse Operations Manager.
- **System Interface**: Streamlit Dashboard (`http://localhost:8501`) or FastAPI Swagger UI (`http://localhost:8000/docs`).

### Evaluation Checklist

| ID | Task | Verification Question | Expected Human Finding | Evaluator Status |
|---|---|---|---|---|
| **T1** | Shortage Identification | Are shortages by branch and product clearly differentiated by urgency? | Critical shortages highlighted; coverage ratio displayed. | [ ] Pending Manual Review |
| **T2** | Recommendation Review | Is the recommended transfer quantity understandable vs. purchase fallback? | Shows exact donor surplus, transit hours, freight cost. | [ ] Pending Manual Review |
| **T3** | Explainability Evidence | Does the evidence string provide clear answers to Who, What, Why, and Safety? | Mentions donor surplus, transit route, and safety stock preservation. | [ ] Pending Manual Review |
| **T4** | Approval & Override | Can the user approve, reject, or override? Does override enforce a reason? | Empty override reasons are rejected with HTTP 400 / UI validation error. | [ ] Pending Manual Review |
| **T5** | Disruption Resilience | Can the operator simulate delay or capacity loss and view cost impacts? | Metrics update reactively; safety violations remain 0. | [ ] Pending Manual Review |

---

## 5. Stakeholder Feedback Template (For Field Collection)
```markdown
### Stakeholder Review Form
- **Reviewer Name / Role**: [Fill during manual testing]
- **Date / Session**: [Fill during manual testing]
- **Task 1 (Shortages)**: [ ] Clear  [ ] Confusing  — Comments:
- **Task 2 (Recommendations)**: [ ] Clear  [ ] Confusing  — Comments:
- **Task 3 (Evidence / Explainability)**: [ ] Sufficient  [ ] Insufficient — Comments:
- **Task 4 (Approval Workflow)**: [ ] Intuitive  [ ] Cumbersome — Comments:
- **Task 5 (Simulation Usability)**: [ ] Useful  [ ] Needs Improvement — Comments:
- **Identified Confusions / Edge Cases**:
- **Suggested Improvements**:
```

---

## 6. Audit & Traceability
All governance actions recorded during manual or automated testing are stored in SQLite database (`outputs/approvals.db`) with:
- Full original recommendation payload
- Human decision (`APPROVED`, `REJECTED`, `OVERRIDDEN`)
- Mandatory override justification string
- UTC timestamp
- High-impact review flag
