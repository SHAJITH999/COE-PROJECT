/**
 * Enterprise Stock Balancing Dashboard Logic
 * Connects directly to FastAPI backend endpoints:
 * - /api/dashboard/overview
 * - /api/recommendations
 * - /api/transfers
 * - /api/transfers/create
 * - /api/branches
 * - /api/search
 * - /approve, /reject, /override
 */

// Global State
const state = {
  currentScenario: "NORMAL",
  currentRegion: "ALL",
  currentMovementRange: "7d",
  overviewData: null,
  recommendations: [],
  transfers: [],
  branches: [],
  activeView: "dashboard",
  recViewMode: "cards",
  recLoading: false,
  recError: null,
  movementChart: null,
  categoryChart: null,
};

// DOM Ready Init
document.addEventListener("DOMContentLoaded", () => {
  initDateDisplay();
  setupNavigation();
  setupEventListeners();
  handleHashNavigation();
  loadAllData();
});

// ── Hash Routing ──
window.addEventListener("hashchange", handleHashNavigation);

function handleHashNavigation() {
  const hash = (window.location.hash || "").replace(/^#\/?/, "").toLowerCase();
  const validViews = ["dashboard", "recommendations", "branches", "transfers", "stock-overview", "reports", "settings"];
  if (hash && validViews.includes(hash)) {
    switchView(hash);
  } else if (!hash) {
    switchView("dashboard");
  }
}

// ── Date Display ──
function initDateDisplay() {
  const dateEl = document.getElementById("headerCurrentDate");
  if (dateEl) {
    const now = new Date();
    dateEl.textContent = now.toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric"
    }) + " | Day 90";
  }
}

// ── Navigation ──
function setupNavigation() {
  const navItems = document.querySelectorAll(".nav-item");
  navItems.forEach(item => {
    item.addEventListener("click", (e) => {
      e.preventDefault();
      const targetView = item.getAttribute("data-view");
      if (targetView) {
        switchView(targetView);
      }
    });
  });

  // Mobile menu toggle
  const mobileBtn = document.getElementById("mobileMenuBtn");
  const sidebar = document.getElementById("sidebar");
  if (mobileBtn && sidebar) {
    mobileBtn.addEventListener("click", () => {
      sidebar.classList.toggle("mobile-open");
    });
  }
}

function switchView(viewName) {
  state.activeView = viewName;
  
  // Sync URL hash
  const currentHash = (window.location.hash || "").replace(/^#\/?/, "").toLowerCase();
  if (currentHash !== viewName) {
    window.location.hash = `#/${viewName}`;
  }
  
  // Update nav active classes
  document.querySelectorAll(".nav-item").forEach(item => {
    if (item.getAttribute("data-view") === viewName) {
      item.classList.add("active");
    } else {
      item.classList.remove("active");
    }
  });

  // Update panels
  document.querySelectorAll(".view-panel").forEach(panel => {
    if (panel.id === `view-${viewName}`) {
      panel.classList.add("active");
    } else {
      panel.classList.remove("active");
    }
  });

  // Load view-specific data if needed
  if (viewName === "transfers") {
    loadTransfersView();
  } else if (viewName === "branches") {
    loadBranchesView();
  } else if (viewName === "recommendations") {
    renderFullRecommendationsView();
    renderRecommendationsFeed();
  }

  // Close mobile sidebar if open
  const sidebar = document.getElementById("sidebar");
  if (sidebar) sidebar.classList.remove("mobile-open");
}

// ── Event Listeners ──
function setupEventListeners() {
  // Scenario selector
  const scenarioSelect = document.getElementById("headerScenarioSelect");
  if (scenarioSelect) {
    scenarioSelect.addEventListener("change", (e) => {
      state.currentScenario = e.target.value;
      showToast(`Switched operational scenario to ${state.currentScenario}`, "info");
      loadAllData();
    });
  }

  // Region / Branch filter
  const regionSelect = document.getElementById("sidebarRegionSelect");
  if (regionSelect) {
    regionSelect.addEventListener("change", async (e) => {
      state.currentRegion = e.target.value;
      const recBranchSelect = document.getElementById("recFilterBranch");
      if (recBranchSelect) {
        recBranchSelect.value = state.currentRegion;
      }
      try {
        await fetchOverviewData();
      } catch (err) {
        console.error("Failed to load overview data for region:", err);
      }
      renderAllComponents();
      if (state.activeView === "recommendations") {
        renderFullRecommendationsView();
      }
    });
  }

  // Recommendation details modal backdrop close
  const recDetailsModal = document.getElementById("recDetailsModal");
  if (recDetailsModal) {
    recDetailsModal.addEventListener("click", (e) => {
      if (e.target === recDetailsModal) closeRecDetailsModal();
    });
  }

  // Refresh Button
  const refreshBtn = document.getElementById("headerRefreshBtn");
  if (refreshBtn) {
    refreshBtn.addEventListener("click", () => {
      showToast("Refreshing inventory data from backend...", "info");
      loadAllData();
    });
  }

  // Stock Movement Range Tabs (7d, 30d, 90d)
  document.querySelectorAll(".chart-tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".chart-tab-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      state.currentMovementRange = btn.getAttribute("data-range");
      updateMovementChart();
    });
  });

  // Alerts Drawer toggle
  const alertsBtn = document.getElementById("headerAlertsBtn");
  const alertsDrawer = document.getElementById("alertsDrawer");
  const closeAlertsBtn = document.getElementById("closeAlertsBtn");
  if (alertsBtn && alertsDrawer) {
    alertsBtn.addEventListener("click", () => alertsDrawer.classList.toggle("open"));
  }
  if (closeAlertsBtn && alertsDrawer) {
    closeAlertsBtn.addEventListener("click", () => alertsDrawer.classList.remove("open"));
  }

  // Global Search
  const searchInput = document.getElementById("globalSearchInput");
  const searchDropdown = document.getElementById("searchResultsDropdown");
  if (searchInput && searchDropdown) {
    let debounceTimer;
    searchInput.addEventListener("input", (e) => {
      clearTimeout(debounceTimer);
      const query = e.target.value.trim();
      if (query.length < 2) {
        searchDropdown.classList.remove("open");
        return;
      }
      debounceTimer = setTimeout(() => executeSearch(query), 200);
    });

    document.addEventListener("click", (e) => {
      if (!searchInput.contains(e.target) && !searchDropdown.contains(e.target)) {
        searchDropdown.classList.remove("open");
      }
    });
  }

  // Create Transfer Modal Form Submit
  const transferForm = document.getElementById("createTransferForm");
  if (transferForm) {
    transferForm.addEventListener("submit", handleCreateTransferSubmit);
  }

  // Override Modal Form Submit
  const overrideForm = document.getElementById("overrideForm");
  if (overrideForm) {
    overrideForm.addEventListener("submit", handleOverrideSubmit);
  }

  // Backdrop click closes modals
  document.querySelectorAll(".modal-backdrop").forEach(backdrop => {
    backdrop.addEventListener("click", (e) => {
      if (e.target === backdrop) {
        backdrop.classList.remove("open");
      }
    });
  });
}

// ── Connection Status Indicator ──
function updateConnectionStatus(connected) {
  const statusPill = document.getElementById("systemStatusIndicator");
  if (!statusPill) return;
  if (connected) {
    statusPill.innerHTML = '<span class="status-dot"></span><span>System Online</span>';
    statusPill.classList.remove("offline");
  } else {
    statusPill.innerHTML = '<span class="status-dot" style="background:#ef4444;"></span><span style="color:#ef4444;">System Offline</span>';
    statusPill.classList.add("offline");
  }
}

// ── Overview KPI Cards ──
function renderOverviewKPIs() {
  if (!state.overviewData || !state.overviewData.kpis) return;
  const kpis = state.overviewData.kpis;

  const totalStockEl = document.getElementById("kpiTotalStock");
  if (totalStockEl) {
    totalStockEl.textContent = (kpis.total_stock !== undefined ? kpis.total_stock.toLocaleString() : "0") + " units";
  }

  const pendingEl = document.getElementById("kpiPendingTransfers");
  if (pendingEl) {
    pendingEl.textContent = (kpis.pending_transfers !== undefined ? kpis.pending_transfers.toLocaleString() : "0");
  }

  const branchesEl = document.getElementById("kpiActiveBranches");
  if (branchesEl) {
    branchesEl.textContent = kpis.active_branches !== undefined ? kpis.active_branches : "8";
  }

  const shortageEl = document.getElementById("kpiShortageAlerts");
  if (shortageEl) {
    shortageEl.textContent = (kpis.shortage_alerts !== undefined ? kpis.shortage_alerts.toLocaleString() : "0");
  }

  const stockSubtextEl = document.querySelector(".kpi-card.blue .kpi-subtext");
  if (stockSubtextEl && kpis.subtext) {
    stockSubtextEl.textContent = kpis.subtext;
  }

  const savingsEl = document.getElementById("kpiCostSavings");
  if (savingsEl && kpis.modeled_savings_inr !== undefined) {
    savingsEl.textContent = Number(kpis.modeled_savings_inr).toLocaleString();
  }

  const avoidanceEl = document.getElementById("kpiShortageAvoidance");
  if (avoidanceEl && kpis.shortage_avoidance_pct !== undefined) {
    avoidanceEl.textContent = kpis.shortage_avoidance_pct + "%";
  }
}

// ── Master Component Orchestrator ──
function renderAllComponents() {
  renderOverviewKPIs();
  renderMovementChart();
  renderCategoryChart();
  renderBranchCards();
  renderInventoryHealth();
  renderAlerts();
  renderRecommendationsFeed();
  updateRecSummaryCards();
  loadTransfersView();
}

// ── API Data Loaders ──
async function loadAllData() {
  try {
    updateConnectionStatus(true);
    await Promise.all([
      fetchOverviewData(),
      fetchRecommendationsData()
    ]);
    renderAllComponents();
  } catch (error) {
    console.error("Failed to load dashboard data:", error);
    updateConnectionStatus(false);
    showToast("Backend connection error. Click retry to reconnect.", "error");
  }
}

async function fetchOverviewData() {
  const branchParam = (state.currentRegion && state.currentRegion !== "ALL") ? `?branch_id=${state.currentRegion}` : "";
  const res = await fetch(`/api/dashboard/overview${branchParam}`);
  if (!res.ok) throw new Error("Overview API returned " + res.status);
  state.overviewData = await res.json();
}

async function fetchRecommendationsData() {
  state.recLoading = true;
  state.recError = null;
  if (state.activeView === "recommendations") {
    renderFullRecommendationsView();
  }

  try {
    const url = `/api/recommendations?scenario=${state.currentScenario}&limit=300`;
    const res = await fetch(url);
    if (!res.ok) {
      let errDetail = `Server responded with status ${res.status}`;
      try {
        const errJson = await res.json();
        if (errJson.detail) errDetail = errJson.detail;
      } catch (_) {}
      throw new Error(errDetail);
    }
    const data = await res.json();
    state.recommendations = data.recommendations || [];
    state.recLoading = false;
    populateRecDateFilter(data.available_dates || []);
  } catch (err) {
    console.error("Recommendations fetch error:", err);
    state.recError = err.message || "Failed to load transfer recommendations from API";
    state.recLoading = false;
  } finally {
    renderRecommendationsFeed();
    if (state.activeView === "recommendations") {
      renderFullRecommendationsView();
    }
  }
}

function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function populateRecDateFilter(availableDates) {
  const dateSelect = document.getElementById("recFilterDate");
  if (!dateSelect) return;
  const currentVal = dateSelect.value;
  dateSelect.innerHTML = '<option value="ALL">All Dates</option>';
  
  const dates = availableDates && availableDates.length > 0
    ? availableDates 
    : [...new Set((state.recommendations || []).map(r => r.date))].filter(Boolean).sort().reverse();

  dates.forEach((d, idx) => {
    const opt = document.createElement("option");
    opt.value = d;
    opt.textContent = idx === 0 ? `${d} (Latest)` : d;
    dateSelect.appendChild(opt);
  });
  if (currentVal && dates.includes(currentVal)) {
    dateSelect.value = currentVal;
  }
}

function getFilteredRecommendations() {
  let recs = state.recommendations || [];

  // 1. Branch / Hub Filter (syncs with Active Network Focus)
  const branchFilter = document.getElementById("recFilterBranch")?.value || state.currentRegion || "ALL";
  if (branchFilter && branchFilter !== "ALL") {
    recs = recs.filter(r => 
      (r.shortage && r.shortage.branch_id === branchFilter) || 
      (r.surplus && r.surplus.branch_id === branchFilter)
    );
  }

  // 2. Product Filter
  const prodFilter = document.getElementById("recFilterProduct")?.value || "ALL";
  if (prodFilter && prodFilter !== "ALL") {
    recs = recs.filter(r => r.shortage && r.shortage.product_id === prodFilter);
  }

  // 3. Priority Filter
  const priorityFilter = document.getElementById("recFilterPriority")?.value || "ALL";
  if (priorityFilter && priorityFilter !== "ALL") {
    recs = recs.filter(r => (r.priority || "").toLowerCase() === priorityFilter.toLowerCase());
  }

  // 4. Status Filter
  const statusFilter = document.getElementById("recFilterStatus")?.value || "ALL";
  if (statusFilter && statusFilter !== "ALL") {
    recs = recs.filter(r => (r.status || "").toUpperCase() === statusFilter.toUpperCase());
  }

  // 5. Date Filter
  const dateFilter = document.getElementById("recFilterDate")?.value || "ALL";
  if (dateFilter && dateFilter !== "ALL") {
    recs = recs.filter(r => r.date === dateFilter);
  }

  // 6. Search Filter
  const searchFilter = (document.getElementById("recFilterSearch")?.value || "").trim().toLowerCase();
  if (searchFilter) {
    recs = recs.filter(r => {
      const q = [
        r.recommendation_id,
        r.shortage?.branch_name,
        r.shortage?.branch_id,
        r.shortage?.city,
        r.surplus?.branch_name,
        r.surplus?.branch_id,
        r.surplus?.city,
        r.shortage?.product_name,
        r.shortage?.product_id,
        r.priority,
        r.status,
        r.recommendation?.evidence
      ].filter(Boolean).join(" ").toLowerCase();
      return q.includes(searchFilter);
    });
  }

  return recs;
}

function updateRecSummaryCards(filteredRecs) {
  const recs = filteredRecs || getFilteredRecommendations();
  
  const activeEl = document.getElementById("summaryActiveRecs");
  const critEl = document.getElementById("summaryCriticalShortages");
  const pendEl = document.getElementById("summaryPendingApproval");
  const unitsEl = document.getElementById("summaryPotentialUnits");
  const subtextEl = document.getElementById("summaryActiveRecsSubtext");

  const branchFilter = document.getElementById("recFilterBranch")?.value || state.currentRegion || "ALL";

  if (activeEl) activeEl.textContent = recs.length;
  if (critEl) critEl.textContent = recs.filter(r => r.priority === "Critical").length;
  if (pendEl) pendEl.textContent = recs.filter(r => r.status === "PENDING").length;
  if (unitsEl) {
    const totalUnits = recs.reduce((sum, r) => sum + (r.recommendation?.recommended_quantity || 0), 0);
    unitsEl.textContent = `${Math.round(totalUnits).toLocaleString()} Units`;
  }
  if (subtextEl) {
    if (branchFilter && branchFilter !== "ALL") {
      subtextEl.textContent = `Active focus: Hub ${branchFilter}`;
    } else {
      subtextEl.textContent = "Across all 8 network distribution hubs";
    }
  }
}

// ── Render Full Recommendations View (VIEW 2: #/recommendations) ──
function renderFullRecommendationsView() {
  const container = document.getElementById("fullRecommendationsContainer");
  if (!container) return;

  // Sync Branch dropdown with state.currentRegion if needed
  const branchSelect = document.getElementById("recFilterBranch");
  if (branchSelect && branchSelect.value !== state.currentRegion) {
    branchSelect.value = state.currentRegion || "ALL";
  }

  // 1. Loading State
  if (state.recLoading) {
    container.innerHTML = `
      <div style="background:#ffffff; border:1px solid var(--slate-200); border-radius:var(--radius-xl); padding:56px 24px; text-align:center; box-shadow:var(--shadow-sm);">
        <div class="spinner" style="width:40px; height:40px; border:3px solid var(--slate-200); border-top-color:var(--blue-600); margin:0 auto 16px;"></div>
        <p style="font-size:1.1rem; font-weight:700; color:var(--slate-900); margin-bottom:6px;">Loading transfer recommendations...</p>
        <p style="font-size:0.88rem; color:var(--slate-500); max-width:520px; margin:0 auto;">
          Analyzing branch stock positions, donor surplus eligibility, safety stock invariant floors, and transfer route constraints...
        </p>
      </div>
    `;
    return;
  }

  // 2. Error State
  if (state.recError) {
    container.innerHTML = `
      <div style="background:#ffffff; border:1px solid var(--red-200); border-left:5px solid var(--red-600); border-radius:var(--radius-xl); padding:40px 24px; text-align:center; box-shadow:var(--shadow-sm);">
        <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" style="color:var(--red-600); margin:0 auto 12px; display:block;"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        <p style="font-weight:700; font-size:1.15rem; color:var(--slate-900); margin-bottom:6px;">Unable to load transfer recommendations.</p>
        <p style="font-size:0.88rem; color:var(--slate-600); max-width:520px; margin:0 auto 20px;">
          ${escapeHtml(state.recError)}
        </p>
        <button class="btn btn-primary" onclick="reloadRecommendationsView()">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>
          Retry Connection
        </button>
      </div>
    `;
    return;
  }

  const recs = getFilteredRecommendations();
  updateRecSummaryCards(recs);

  // 3. Empty State
  if (recs.length === 0) {
    container.innerHTML = `
      <div style="background:#ffffff; border:1px dashed var(--slate-300); border-radius:var(--radius-xl); padding:56px 24px; text-align:center; color:var(--slate-600); box-shadow:var(--shadow-sm);">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin:0 auto 14px; display:block; color:var(--slate-400);"><circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/></svg>
        <p style="font-weight:700; font-size:1.15rem; color:var(--slate-900); margin-bottom:6px;">No active transfer recommendations</p>
        <p style="font-size:0.88rem; color:var(--slate-500); max-width:480px; margin:0 auto 20px;">
          No stock-balancing recommendations are currently available for the selected filter. All regional branches are balanced within safe thresholds.
        </p>
        <div style="display:flex; justify-content:center; gap:10px;">
          <button class="btn btn-outline-primary btn-sm" onclick="resetRecFilters()">Clear Filters</button>
          <button class="btn btn-secondary btn-sm" onclick="reloadRecommendationsView()">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>
            Refresh Recommendations
          </button>
        </div>
      </div>
    `;
    return;
  }

  // 4. Render Table or Cards
  if (state.recViewMode === "table") {
    container.innerHTML = renderRecommendationsTableHtml(recs);
  } else {
    container.innerHTML = renderRecommendationsCardsHtml(recs);
  }
}

// ── Render 3-Box Flow Cards HTML ──
function renderRecommendationsCardsHtml(recs) {
  return `
    <div class="recommendations-container">
      ${recs.map(r => {
        const priorityClass = (r.priority || "medium").toLowerCase();
        const statusClass = (r.status || "pending").toLowerCase();
        const isApproved = r.status === "APPROVED";
        const isRejected = r.status === "REJECTED";

        return `
          <div class="rec-card ${priorityClass}" id="full-card-${r.recommendation_id}">
            <!-- Header -->
            <div class="rec-card-header">
              <div class="rec-id-group">
                <span class="rec-id-badge">${r.recommendation_id}</span>
                <span class="status-badge ${priorityClass}">${r.priority} Priority</span>
                ${r.is_high_impact ? `<span class="high-impact-pill">⚠️ High Impact (Requires Confirmation)</span>` : ""}
                <span class="status-badge ${statusClass}" id="status-badge-${r.recommendation_id}">${r.status}</span>
              </div>
              <div style="font-size:0.8rem; color:#64748b; font-weight:500;">
                Route: ${r.surplus.city} ➔ ${r.shortage.city} • Date: ${r.date}
              </div>
            </div>

            <!-- 3-Box Flow Grid -->
            <div class="rec-flow-grid">
              <!-- Shortage Box -->
              <div class="flow-box shortage">
                <div class="flow-box-header">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                  1. Shortage Detected (Recipient)
                </div>
                <div class="flow-box-title">${r.shortage.branch_name} (${r.shortage.branch_id})</div>
                <div class="flow-box-meta">
                  <div>Product: <span class="flow-highlight">${r.shortage.product_name} (${r.shortage.product_id})</span></div>
                  <div>Current Stock: <span class="flow-highlight">${r.shortage.current_stock} units</span></div>
                  <div>Required Stock Floor: <span class="flow-highlight">${r.shortage.required_stock} units</span> (Demand + Safety)</div>
                  <div>Shortage Deficit: <span class="flow-deficit-pill">-${r.shortage.deficit} units</span></div>
                </div>
              </div>

              <!-- Surplus Box -->
              <div class="flow-box surplus">
                <div class="flow-box-header">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><path d="M8 12h8"/><path d="M12 8v8"/></svg>
                  2. Transferable Surplus Found (Donor)
                </div>
                <div class="flow-box-title">${r.surplus.branch_name} (${r.surplus.branch_id})</div>
                <div class="flow-box-meta">
                  <div>Product: <span class="flow-highlight">${r.surplus.product_name}</span></div>
                  <div>Available Surplus: <span class="flow-surplus-pill">+${r.surplus.available_surplus} units</span></div>
                  <div>Safety Stock Protected: <span class="flow-highlight">100% Invariant (0 Violations)</span></div>
                  <div>Donor Secondary Stockout: <span style="color:#16a34a; font-weight:600;">Zero Risk</span></div>
                </div>
              </div>

              <!-- Recommendation Box -->
              <div class="flow-box recommendation">
                <div class="flow-box-header">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="13 17 18 12 13 7"/><polyline points="6 17 11 12 6 7"/></svg>
                  3. Balancing Transfer Action
                </div>
                <div class="flow-box-title">Move <span class="flow-transfer-pill">${r.recommendation.recommended_quantity} Units</span> from ${r.recommendation.source_city} ➔ ${r.recommendation.dest_city}</div>
                <div class="flow-box-meta">
                  <div>Transit Lead Time: <span class="flow-highlight">${r.recommendation.transfer_time_hours} hrs</span> (${r.recommendation.distance_km} km)</div>
                  <div>Estimated Freight Cost: <span class="flow-highlight">₹${r.recommendation.estimated_cost.toFixed(2)}</span> (vs external order)</div>
                  <div>Fulfillment: <span style="color:#15803d; font-weight:700;">100% Internal Network Balancing</span></div>
                </div>
              </div>
            </div>

            <!-- Evidence Bar -->
            <div class="rec-evidence-bar">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="flex-shrink:0; margin-top:2px; color:#2563eb;"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
              <div>
                <strong>Rebalancing Evidence:</strong> ${escapeHtml(r.recommendation.evidence)}
                ${r.override_reason ? `<div style="margin-top:4px; color:#7c3aed; font-weight:600;">Manual Override Reason: "${escapeHtml(r.override_reason)}"</div>` : ""}
              </div>
            </div>

            <!-- Action Footer -->
            <div class="rec-actions-bar">
              <div style="display:flex; gap:8px;">
                <button class="btn btn-outline-primary btn-sm" onclick="openRecDetailsModal('${r.recommendation_id}')">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
                  View Details & Audit
                </button>
                <button class="btn btn-primary btn-sm" onclick="openCreateTransferModal('${r.recommendation_id}')">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
                  Create Transfer
                </button>
              </div>

              <div class="rec-governance-buttons">
                <button class="btn btn-success btn-sm" onclick="executeApprove('${r.recommendation_id}')" ${isApproved ? "disabled" : ""}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                  ${isApproved ? "Approved" : "Approve"}
                </button>
                <button class="btn btn-danger btn-sm" onclick="executeReject('${r.recommendation_id}')" ${isRejected ? "disabled" : ""}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                  ${isRejected ? "Rejected" : "Reject"}
                </button>
                <button class="btn btn-secondary btn-sm" onclick="openOverrideModal('${r.recommendation_id}')">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m3 11 18-5v12L3 14v-3z"/></svg>
                  Override
                </button>
              </div>
            </div>
          </div>
        `;
      }).join("")}
    </div>
  `;
}

// ── Render Audit Table HTML ──
function renderRecommendationsTableHtml(recs) {
  return `
    <div class="data-table-wrapper" style="background:#ffffff;">
      <table class="data-table">
        <thead>
          <tr>
            <th>Rec ID</th>
            <th>Date</th>
            <th>Source (Donor)</th>
            <th>Destination (Shortage)</th>
            <th>Product / SKU</th>
            <th>Surplus</th>
            <th>Deficit</th>
            <th>Transfer Qty</th>
            <th>Priority</th>
            <th>Status</th>
            <th style="min-width: 190px;">Actions</th>
          </tr>
        </thead>
        <tbody>
          ${recs.map(r => {
            const priorityClass = (r.priority || "medium").toLowerCase();
            const statusClass = (r.status || "pending").toLowerCase();
            const isApproved = r.status === "APPROVED";
            const isRejected = r.status === "REJECTED";

            return `
              <tr id="table-row-${r.recommendation_id}">
                <td>
                  <span class="rec-id-badge" style="font-size:0.75rem;">${r.recommendation_id}</span>
                  ${r.is_high_impact ? `<span title="High Impact" style="color:#dc2626; margin-left:2px;">⚠️</span>` : ""}
                </td>
                <td style="font-size:0.78rem; color:#64748b; white-space:nowrap;">${r.date}</td>
                <td>
                  <strong>${r.surplus.city}</strong>
                  <div style="font-size:0.75rem; color:#64748b;">${r.surplus.branch_id}</div>
                </td>
                <td>
                  <strong>${r.shortage.city}</strong>
                  <div style="font-size:0.75rem; color:#64748b;">${r.shortage.branch_id}</div>
                </td>
                <td>
                  <div>${r.shortage.product_name}</div>
                  <div style="font-size:0.75rem; color:#64748b;">${r.shortage.product_id}</div>
                </td>
                <td>
                  <span class="flow-surplus-pill" style="font-size:0.75rem;">+${r.surplus.available_surplus}</span>
                </td>
                <td>
                  <span class="flow-deficit-pill" style="font-size:0.75rem;">-${r.shortage.deficit}</span>
                </td>
                <td>
                  <span class="flow-transfer-pill" style="font-size:0.75rem;">${r.recommendation.recommended_quantity}</span>
                </td>
                <td>
                  <span class="status-badge ${priorityClass}">${r.priority}</span>
                </td>
                <td>
                  <span class="status-badge ${statusClass}" id="table-status-badge-${r.recommendation_id}">${r.status}</span>
                </td>
                <td>
                  <div class="table-action-group">
                    <button class="table-btn btn-view" title="View details & safety audit" onclick="openRecDetailsModal('${r.recommendation_id}')">
                      View
                    </button>
                    <button class="table-btn btn-approve" title="Approve recommendation" onclick="executeApprove('${r.recommendation_id}')" ${isApproved ? "disabled" : ""}>
                      Approve
                    </button>
                    <button class="table-btn btn-reject" title="Reject recommendation" onclick="executeReject('${r.recommendation_id}')" ${isRejected ? "disabled" : ""}>
                      Reject
                    </button>
                    <button class="table-btn btn-override" title="Manual supervisor override" onclick="openOverrideModal('${r.recommendation_id}')">
                      Override
                    </button>
                  </div>
                </td>
              </tr>
            `;
          }).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function setRecViewMode(mode) {
  state.recViewMode = mode;
  const cardsBtn = document.getElementById("recViewCardsBtn");
  const tableBtn = document.getElementById("recViewTableBtn");
  
  if (cardsBtn && tableBtn) {
    if (mode === "cards") {
      cardsBtn.className = "btn btn-sm btn-primary";
      tableBtn.className = "btn btn-sm btn-secondary";
    } else {
      cardsBtn.className = "btn btn-sm btn-secondary";
      tableBtn.className = "btn btn-sm btn-primary";
    }
  }
  renderFullRecommendationsView();
}

function applyRecFilters() {
  renderFullRecommendationsView();
}

function onRecFilterBranchChange() {
  const branchSelect = document.getElementById("recFilterBranch");
  if (branchSelect) {
    state.currentRegion = branchSelect.value;
    const sidebarSelect = document.getElementById("sidebarRegionSelect");
    if (sidebarSelect) sidebarSelect.value = state.currentRegion;
    fetchOverviewData().then(() => {
      renderAllComponents();
      renderFullRecommendationsView();
    }).catch(() => {
      renderAllComponents();
      renderFullRecommendationsView();
    });
  }
}

function resetRecFilters() {
  const searchInput = document.getElementById("recFilterSearch");
  const branchSelect = document.getElementById("recFilterBranch");
  const prodSelect = document.getElementById("recFilterProduct");
  const prioritySelect = document.getElementById("recFilterPriority");
  const statusSelect = document.getElementById("recFilterStatus");
  const dateSelect = document.getElementById("recFilterDate");

  if (searchInput) searchInput.value = "";
  if (branchSelect) branchSelect.value = "ALL";
  if (prodSelect) prodSelect.value = "ALL";
  if (prioritySelect) prioritySelect.value = "ALL";
  if (statusSelect) statusSelect.value = "ALL";
  if (dateSelect) dateSelect.value = "ALL";

  state.currentRegion = "ALL";
  const sidebarSelect = document.getElementById("sidebarRegionSelect");
  if (sidebarSelect) sidebarSelect.value = "ALL";

  fetchOverviewData().then(() => {
    renderAllComponents();
    renderFullRecommendationsView();
  }).catch(() => {
    renderAllComponents();
    renderFullRecommendationsView();
  });
}

function reloadRecommendationsView() {
  fetchRecommendationsData().then(renderFullRecommendationsView);
}

// ── Recommendation Details & Safety Audit Modal ──
function openRecDetailsModal(recId) {
  const rec = state.recommendations.find(r => r.recommendation_id === recId);
  if (!rec) return;

  const modal = document.getElementById("recDetailsModal");
  if (!modal) return;

  const titleEl = document.getElementById("recDetailsModalTitle");
  const idEl = document.getElementById("recDetailsModalId");
  const statusEl = document.getElementById("recDetailsModalStatus");
  const bodyEl = document.getElementById("recDetailsModalBody");
  const actionsEl = document.getElementById("recDetailsModalActions");

  if (idEl) idEl.textContent = rec.recommendation_id;
  if (statusEl) {
    statusEl.className = `status-badge ${rec.status.toLowerCase()}`;
    statusEl.textContent = rec.status;
  }
  if (titleEl) {
    titleEl.textContent = `Balancing Transfer: ${rec.surplus.city} ➔ ${rec.shortage.city}`;
  }

  const isApproved = rec.status === "APPROVED";
  const isRejected = rec.status === "REJECTED";

  if (bodyEl) {
    bodyEl.innerHTML = `
      <!-- Top Badges -->
      <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin-bottom:16px;">
        <span class="status-badge ${rec.priority.toLowerCase()}">${rec.priority} Priority</span>
        ${rec.is_high_impact ? `<span class="high-impact-pill">⚠️ High Impact (Requires Mandatory Supervisor Oversight)</span>` : ""}
        <span style="font-size:0.82rem; color:var(--slate-500); margin-left:auto;">Date: ${rec.date} • Created: ${rec.timestamp || "Active"}</span>
      </div>

      <!-- 3-Box Flow Grid inside Modal -->
      <div class="rec-flow-grid" style="margin-bottom:16px;">
        <!-- Shortage Box -->
        <div class="flow-box shortage">
          <div class="flow-box-header">1. Shortage Deficit (Recipient)</div>
          <div class="flow-box-title">${rec.shortage.branch_name}</div>
          <div class="flow-box-meta">
            <div>Branch ID: <span class="flow-highlight">${rec.shortage.branch_id} (${rec.shortage.city})</span></div>
            <div>Current Stock: <span class="flow-highlight">${rec.shortage.current_stock} units</span></div>
            <div>Required Floor: <span class="flow-highlight">${rec.shortage.required_stock} units</span> (Demand + Safety)</div>
            <div>Shortage Deficit: <span class="flow-deficit-pill">-${rec.shortage.deficit} units</span></div>
          </div>
        </div>

        <!-- Surplus Box -->
        <div class="flow-box surplus">
          <div class="flow-box-header">2. Donor Surplus (Source)</div>
          <div class="flow-box-title">${rec.surplus.branch_name}</div>
          <div class="flow-box-meta">
            <div>Branch ID: <span class="flow-highlight">${rec.surplus.branch_id} (${rec.surplus.city})</span></div>
            <div>Available Surplus: <span class="flow-surplus-pill">+${rec.surplus.available_surplus} units</span></div>
            <div>Safety Invariant: <span style="color:#16a34a; font-weight:700;">Protected (0 Violations)</span></div>
            <div>Secondary Stockout Risk: <span class="flow-highlight">Zero Risk</span></div>
          </div>
        </div>

        <!-- Recommendation Box -->
        <div class="flow-box recommendation">
          <div class="flow-box-header">3. Balancing Recommendation</div>
          <div class="flow-box-title">${rec.recommendation.recommended_quantity} Units Lateral Transfer</div>
          <div class="flow-box-meta">
            <div>Route: <span class="flow-highlight">${rec.surplus.city} ➔ ${rec.shortage.city}</span></div>
            <div>Transit Time: <span class="flow-highlight">${rec.recommendation.transfer_time_hours} hrs (${rec.recommendation.distance_km} km)</span></div>
            <div>Freight Cost: <span class="flow-highlight">₹${rec.recommendation.estimated_cost.toFixed(2)}</span> (vs external purchase)</div>
            <div>Product SKU: <span class="flow-highlight">${rec.shortage.product_name} (${rec.shortage.product_id})</span></div>
          </div>
        </div>
      </div>

      <!-- Algorithmic Evidence Bar -->
      <div class="rec-evidence-bar" style="margin-bottom:16px;">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="flex-shrink:0; margin-top:2px; color:#2563eb;"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
        <div>
          <strong>Rebalancing Evidence & Route Feasibility:</strong> ${escapeHtml(rec.recommendation.evidence)}
        </div>
      </div>

      <!-- Safety & Governance Audit Record -->
      <div class="rec-audit-box">
        <div class="rec-audit-title">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
          Safety Invariant & Human-in-the-Loop Audit Trail
        </div>
        <div class="rec-audit-grid">
          <div><strong>Recommendation Status:</strong> <span class="status-badge ${rec.status.toLowerCase()}">${rec.status}</span></div>
          <div><strong>Logged Decision:</strong> ${rec.audit?.decision || rec.status}</div>
          <div><strong>Authorized Operator:</strong> ${rec.operator || "Logistics Operations Supervisor"}</div>
          <div><strong>Audit Timestamp:</strong> ${rec.timestamp || rec.date}</div>
          <div><strong>Override Status:</strong> ${rec.audit?.override_status || (rec.status === "OVERRIDDEN" ? "YES" : "NO")}</div>
          <div><strong>Safety Invariant Guarantee:</strong> <span style="color:#16a34a; font-weight:600;">Stock &ge; Forecast + Safety Stock</span></div>
        </div>
        ${rec.override_reason ? `
          <div style="margin-top:12px; padding:10px 14px; background:#faf5ff; border:1px solid #e9d5ff; border-radius:6px; font-size:0.82rem; color:#6d28d9;">
            <strong>Supervisor Override Justification:</strong> "${escapeHtml(rec.override_reason)}"
          </div>
        ` : ""}
      </div>
    `;
  }

  if (actionsEl) {
    actionsEl.innerHTML = `
      <button class="btn btn-success btn-sm" onclick="executeApproveFromModal('${rec.recommendation_id}')" ${isApproved ? "disabled" : ""}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
        ${isApproved ? "Approved" : "Approve"}
      </button>
      <button class="btn btn-danger btn-sm" onclick="executeRejectFromModal('${rec.recommendation_id}')" ${isRejected ? "disabled" : ""}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        ${isRejected ? "Rejected" : "Reject"}
      </button>
      <button class="btn btn-secondary btn-sm" onclick="closeRecDetailsModal(); openOverrideModal('${rec.recommendation_id}');">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m3 11 18-5v12L3 14v-3z"/></svg>
        Override
      </button>
      <button class="btn btn-primary btn-sm" onclick="closeRecDetailsModal(); openCreateTransferModal('${rec.recommendation_id}');">
        Create Transfer
      </button>
    `;
  }

  modal.classList.add("open");
}

function closeRecDetailsModal() {
  const modal = document.getElementById("recDetailsModal");
  if (modal) modal.classList.remove("open");
}

async function executeApproveFromModal(recId) {
  await executeApprove(recId);
  openRecDetailsModal(recId);
}

async function executeRejectFromModal(recId) {
  await executeReject(recId);
  openRecDetailsModal(recId);
}

// ── Render Smart Stock Transfer Recommendations (Overview feed) ──
function renderRecommendationsFeed() {
  const container = document.getElementById("recommendationsFeed");
  if (!container) return;

  let recs = state.recommendations;
  if (state.currentRegion && state.currentRegion !== "ALL") {
    recs = recs.filter(r => 
      (r.shortage && r.shortage.branch_id === state.currentRegion) || 
      (r.surplus && r.surplus.branch_id === state.currentRegion)
    );
  }

  if (!recs || recs.length === 0) {
    container.innerHTML = `
      <div style="background:#ffffff; border:1px dashed #cbd5e1; border-radius:12px; padding:36px; text-align:center; color:#64748b;">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin:0 auto 12px; display:block; color:#94a3b8;"><circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/></svg>
        <p style="font-weight:600; font-size:1rem; color:#0f172a; margin-bottom:4px;">No Active Stock Balancing Recommendations</p>
        <p style="font-size:0.85rem;">All regional branches are currently balanced within safe thresholds.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = recs.slice(0, 15).map(r => {
    const priorityClass = (r.priority || "medium").toLowerCase();
    const statusClass = (r.status || "pending").toLowerCase();
    const isApproved = r.status === "APPROVED";
    const isRejected = r.status === "REJECTED";

    return `
      <div class="rec-card ${priorityClass}" id="card-${r.recommendation_id}">
        <!-- Header -->
        <div class="rec-card-header">
          <div class="rec-id-group">
            <span class="rec-id-badge">${r.recommendation_id}</span>
            <span class="status-badge ${priorityClass}">${r.priority} Priority</span>
            ${r.is_high_impact ? `<span class="high-impact-pill">⚠️ High Impact (Requires Confirmation)</span>` : ""}
            <span class="status-badge ${statusClass}" id="status-badge-${r.recommendation_id}">${r.status}</span>
          </div>
          <div style="font-size:0.78rem; color:#64748b; font-weight:500;">
            ${r.surplus.city} ➔ ${r.shortage.city} Route • ${r.date}
          </div>
        </div>

        <!-- 3-Box Rebalancing Flow -->
        <div class="rec-flow-grid">
          <!-- Shortage Box -->
          <div class="flow-box shortage">
            <div class="flow-box-header">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
              1. Shortage Detected
            </div>
            <div class="flow-box-title">${r.shortage.branch_name} (${r.shortage.branch_id})</div>
            <div class="flow-box-meta">
              <div>Product: <span class="flow-highlight">${r.shortage.product_name} (${r.shortage.product_id})</span></div>
              <div>Current Stock: <span class="flow-highlight">${r.shortage.current_stock} units</span></div>
              <div>Required Floor: <span class="flow-highlight">${r.shortage.required_stock} units</span> (Demand + Safety)</div>
              <div>Shortage Deficit: <span class="flow-deficit-pill">-${r.shortage.deficit} units</span></div>
            </div>
          </div>

          <!-- Surplus Box -->
          <div class="flow-box surplus">
            <div class="flow-box-header">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><path d="M8 12h8"/><path d="M12 8v8"/></svg>
              2. Transferable Surplus Found
            </div>
            <div class="flow-box-title">${r.surplus.branch_name} (${r.surplus.branch_id})</div>
            <div class="flow-box-meta">
              <div>Product: <span class="flow-highlight">${r.surplus.product_name}</span></div>
              <div>Transferable Surplus: <span class="flow-surplus-pill">+${r.surplus.available_surplus} units</span></div>
              <div>Safety Stock Protected: <span class="flow-highlight">100% Invariant</span></div>
              <div>Donor Secondary Stockout: <span style="color:#16a34a; font-weight:600;">Zero Risk</span></div>
            </div>
          </div>

          <!-- Recommendation Box -->
          <div class="flow-box recommendation">
            <div class="flow-box-header">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="13 17 18 12 13 7"/><polyline points="6 17 11 12 6 7"/></svg>
              3. Recommended Transfer
            </div>
            <div class="flow-box-title">Move <span class="flow-transfer-pill">${r.recommendation.recommended_quantity} Units</span> from ${r.recommendation.source_city} ➔ ${r.recommendation.dest_city}</div>
            <div class="flow-box-meta">
              <div>Transit Lead Time: <span class="flow-highlight">${r.recommendation.transfer_time_hours} hrs</span> (${r.recommendation.distance_km} km)</div>
              <div>Estimated Freight Cost: <span class="flow-highlight">₹${r.recommendation.estimated_cost.toFixed(2)}</span> (vs external procurement)</div>
              <div>Shortage Avoidance: <span style="color:#15803d; font-weight:700;">100% Internal Network Fulfillment</span></div>
            </div>
          </div>
        </div>

        <!-- Evidence & Rationale -->
        <div class="rec-evidence-bar">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="flex-shrink:0; margin-top:2px; color:#2563eb;"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
          <div>
            <strong>Rebalancing Evidence:</strong> ${escapeHtml(r.recommendation.evidence)}
            ${r.override_reason ? `<div style="margin-top:4px; color:#7c3aed; font-weight:600;">Manual Override Reason: "${escapeHtml(r.override_reason)}"</div>` : ""}
          </div>
        </div>

        <!-- Action Footer -->
        <div class="rec-actions-bar">
          <div style="display:flex; gap:8px;">
            <button class="btn btn-outline-primary btn-sm" onclick="openRecDetailsModal('${r.recommendation_id}')">
              View
            </button>
            <button class="btn btn-primary btn-sm" onclick="openCreateTransferModal('${r.recommendation_id}')">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
              Create Transfer
            </button>
          </div>

          <div class="rec-governance-buttons">
            <button class="btn btn-success btn-sm" onclick="executeApprove('${r.recommendation_id}')" ${isApproved ? "disabled" : ""}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
              ${isApproved ? "Approved" : "Approve"}
            </button>
            <button class="btn btn-danger btn-sm" onclick="executeReject('${r.recommendation_id}')" ${isRejected ? "disabled" : ""}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              ${isRejected ? "Rejected" : "Reject"}
            </button>
            <button class="btn btn-secondary btn-sm" onclick="openOverrideModal('${r.recommendation_id}')">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m3 11 18-5v12L3 14v-3z"/></svg>
              Override
            </button>
          </div>
        </div>
      </div>
    `;
  }).join("");
}

// ── Stock Movement Overview Chart ──
function renderMovementChart() {
  const ctx = document.getElementById("stockMovementChart");
  if (!ctx || !window.Chart) return;
  if (!state.overviewData || !state.overviewData.movement_overview) return;

  const movementData = state.overviewData.movement_overview[state.currentMovementRange];
  if (!movementData) return;

  if (state.movementChart) {
    state.movementChart.destroy();
  }

  state.movementChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: movementData.dates.map(d => d.slice(5)), // Format MM-DD
      datasets: [
        {
          label: "Stock Dispatched (Demand)",
          data: movementData.dispatched,
          borderColor: "#dc2626",
          backgroundColor: "rgba(220, 38, 38, 0.08)",
          fill: true,
          tension: 0.3,
          borderWidth: 2,
          pointRadius: 2,
        },
        {
          label: "Stock Received (Inbound)",
          data: movementData.received,
          borderColor: "#2563eb",
          backgroundColor: "rgba(37, 99, 235, 0.08)",
          fill: true,
          tension: 0.3,
          borderWidth: 2,
          pointRadius: 2,
        },
        {
          label: "Inter-Branch Transfers",
          data: movementData.transfers,
          borderColor: "#16a34a",
          backgroundColor: "rgba(22, 163, 74, 0.12)",
          fill: true,
          tension: 0.3,
          borderWidth: 2.5,
          pointRadius: 3,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "top",
          labels: { boxWidth: 12, font: { family: "Inter", size: 11 } }
        },
        tooltip: {
          padding: 10,
          boxPadding: 4,
          usePointStyle: true,
        }
      },
      scales: {
        x: { grid: { display: false } },
        y: {
          grid: { color: "#f1f5f9" },
          ticks: { font: { size: 11 } }
        }
      }
    }
  });
}

function updateMovementChart() {
  if (!state.overviewData || !state.overviewData.movement_overview) return;
  if (!state.movementChart) {
    renderMovementChart();
    return;
  }
  const movementData = state.overviewData.movement_overview[state.currentMovementRange];
  if (!movementData) return;

  state.movementChart.data.labels = movementData.dates.map(d => d.slice(5));
  state.movementChart.data.datasets[0].data = movementData.dispatched;
  state.movementChart.data.datasets[1].data = movementData.received;
  state.movementChart.data.datasets[2].data = movementData.transfers;
  state.movementChart.update();
}

// ── Stock by Category Doughnut Chart ──
function renderCategoryChart() {
  const ctx = document.getElementById("categoryChart");
  if (!ctx || !window.Chart) return;

  const categories = state.overviewData.category_breakdown;
  if (!categories || categories.length === 0) return;

  if (state.categoryChart) {
    state.categoryChart.destroy();
  }

  state.categoryChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: categories.map(c => c.category),
      datasets: [{
        data: categories.map(c => c.stock_units),
        backgroundColor: categories.map(c => c.color),
        borderWidth: 2,
        borderColor: "#ffffff",
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "68%",
      plugins: {
        legend: {
          position: "bottom",
          labels: { boxWidth: 12, padding: 14, font: { family: "Inter", size: 11 } }
        },
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${ctx.label}: ${ctx.raw} units (${categories[ctx.dataIndex].share_pct}%)`
          }
        }
      }
    }
  });
}

// ── Branch Stock Levels Cards ──
function renderBranchCards() {
  const container = document.getElementById("branchCardsContainer");
  if (!container) return;
  if (!state.overviewData || !state.overviewData.branch_stock_levels) return;

  const branches = state.overviewData.branch_stock_levels;
  if (!branches || branches.length === 0) return;

  container.innerHTML = branches.map(b => {
    let badgeColorClass = "green";
    if (b.status === "CRITICAL") badgeColorClass = "critical";
    else if (b.status === "WARNING") badgeColorClass = "high";
    else if (b.status === "SURPLUS") badgeColorClass = "low";

    const isSelected = state.currentRegion === b.branch_id;
    const highlightStyle = isSelected ? 'border: 2px solid var(--blue-600); box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);' : '';

    return `
      <div class="branch-card ${isSelected ? 'active-focus' : ''}" style="${highlightStyle}">
        <div>
          <div class="branch-card-header">
            <div>
              <div class="branch-name-title">${b.city}</div>
              <div class="branch-city-sub">${b.branch_name} (${b.branch_id})</div>
            </div>
            <span class="status-badge ${badgeColorClass}">${b.status}</span>
          </div>

          <div class="branch-stock-row">
            <span class="branch-stock-val">${b.current_stock.toLocaleString()} units</span>
            <span class="branch-capacity-val">${b.utilization_pct}% of ${b.capacity}</span>
          </div>

          <div class="progress-bar-bg">
            <div class="progress-bar-fill" style="width:${b.utilization_pct}%; background-color:${b.status_color};"></div>
          </div>
        </div>

        <div class="branch-stats-footer">
          <span>Shortage SKUs: <strong style="color:#dc2626;">${b.shortage_skus}</strong></span>
          <span>Surplus SKUs: <strong style="color:#7c3aed;">${b.surplus_skus}</strong></span>
          <button class="btn btn-outline-primary btn-sm" onclick="filterByBranch('${b.branch_id}')">${isSelected ? 'Focused' : 'View'}</button>
        </div>
      </div>
    `;
  }).join("");
}

// ── Inventory Health Widget ──
function renderInventoryHealth() {
  const health = state.overviewData.inventory_health;
  if (!health) return;

  const scoreEl = document.getElementById("healthScoreValue");
  if (scoreEl) scoreEl.textContent = health.overall_health_score + "%";

  const segHealthy = document.getElementById("healthSegHealthy");
  const segLow = document.getElementById("healthSegLow");
  const segExcess = document.getElementById("healthSegExcess");

  if (segHealthy) segHealthy.style.width = health.healthy_pct + "%";
  if (segLow) segLow.style.width = health.low_stock_pct + "%";
  if (segExcess) segExcess.style.width = health.excess_stock_pct + "%";

  const pctHealthy = document.getElementById("healthPctHealthy");
  const pctLow = document.getElementById("healthPctLow");
  const pctExcess = document.getElementById("healthPctExcess");

  if (pctHealthy) pctHealthy.textContent = health.healthy_pct + "%";
  if (pctLow) pctLow.textContent = health.low_stock_pct + "%";
  if (pctExcess) pctExcess.textContent = health.excess_stock_pct + "%";
}

// ── Operational Alerts ──
function renderAlerts() {
  const listEl = document.getElementById("alertsListContainer");
  const badgeEl = document.getElementById("alertsBadgeCount");
  if (!listEl) return;

  const alerts = state.overviewData.recent_alerts || [];
  if (badgeEl) badgeEl.textContent = alerts.length;

  if (alerts.length === 0) {
    listEl.innerHTML = `<div style="text-align:center; padding:20px; color:#64748b;">No active operational alerts.</div>`;
    return;
  }

  listEl.innerHTML = alerts.map(a => `
    <div class="alert-item ${a.type.toLowerCase()}">
      <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:4px;">
        <span class="status-badge ${a.type.toLowerCase()}">${a.badge}</span>
        <span style="font-size:0.7rem; color:#94a3b8;">${a.timestamp}</span>
      </div>
      <div class="alert-item-title">${a.title}</div>
      <div class="alert-item-msg">${a.message}</div>
    </div>
  `).join("");
}

// ── Governance Actions (Approve / Reject / Override) ──
async function executeApprove(recId) {
  try {
    const res = await fetch("/approve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ recommendation_id: recId })
    });
    if (!res.ok) throw new Error("Approval failed");
    showToast(`Recommendation ${recId} APPROVED successfully!`, "success");
    updateLocalRecommendationStatus(recId, "APPROVED");
  } catch (err) {
    showToast("Error approving recommendation: " + err.message, "error");
  }
}

async function executeReject(recId) {
  try {
    const res = await fetch("/reject", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ recommendation_id: recId })
    });
    if (!res.ok) throw new Error("Rejection failed");
    showToast(`Recommendation ${recId} REJECTED.`, "info");
    updateLocalRecommendationStatus(recId, "REJECTED");
  } catch (err) {
    showToast("Error rejecting recommendation: " + err.message, "error");
  }
}

function openOverrideModal(recId) {
  const modal = document.getElementById("overrideModal");
  const inputId = document.getElementById("overrideRecId");
  const inputReason = document.getElementById("overrideReasonInput");
  if (modal && inputId && inputReason) {
    inputId.value = recId;
    inputReason.value = "";
    modal.classList.add("open");
    inputReason.focus();
  }
}

function closeOverrideModal() {
  const modal = document.getElementById("overrideModal");
  if (modal) modal.classList.remove("open");
}

async function handleOverrideSubmit(e) {
  e.preventDefault();
  const recId = document.getElementById("overrideRecId").value;
  const reason = document.getElementById("overrideReasonInput").value.trim();

  if (!reason) {
    showToast("Override reason is mandatory and cannot be empty.", "error");
    return;
  }

  try {
    const res = await fetch("/override", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ recommendation_id: recId, override_reason: reason })
    });
    if (!res.ok) throw new Error("Override failed");
    closeOverrideModal();
    showToast(`Recommendation ${recId} OVERRIDDEN with reason.`, "success");
    updateLocalRecommendationStatus(recId, "OVERRIDDEN", reason);
  } catch (err) {
    showToast("Error overriding recommendation: " + err.message, "error");
  }
}

function updateLocalRecommendationStatus(recId, newStatus, overrideReason = "") {
  const rec = state.recommendations.find(r => r.recommendation_id === recId);
  if (rec) {
    rec.status = newStatus;
    if (overrideReason) rec.override_reason = overrideReason;
    if (rec.audit) {
      rec.audit.recommendation_status = newStatus;
      rec.audit.decision = newStatus;
      if (overrideReason) {
        rec.audit.override_status = "YES";
        rec.audit.override_reason = overrideReason;
      }
    }
  }
  const badge = document.getElementById(`status-badge-${recId}`);
  if (badge) {
    badge.className = `status-badge ${newStatus.toLowerCase()}`;
    badge.textContent = newStatus;
  }
  const tableBadge = document.getElementById(`table-status-badge-${recId}`);
  if (tableBadge) {
    tableBadge.className = `status-badge ${newStatus.toLowerCase()}`;
    tableBadge.textContent = newStatus;
  }
  updateRecSummaryCards();
}

// ── Transfer Management ("Create Transfer" Modal) ──
function openCreateTransferModal(recId) {
  const modal = document.getElementById("createTransferModal");
  if (!modal) return;

  const rec = state.recommendations.find(r => r.recommendation_id === recId);
  if (rec) {
    document.getElementById("transferSourceBranch").value = rec.recommendation.source_branch;
    document.getElementById("transferDestBranch").value = rec.recommendation.dest_branch;
    document.getElementById("transferProduct").value = rec.shortage.product_id;
    document.getElementById("transferQuantity").value = rec.recommendation.recommended_quantity;
    document.getElementById("transferPriority").value = rec.priority || "MEDIUM";
    document.getElementById("transferReason").value = `Network rebalancing: ${rec.shortage.city} shortage covered by ${rec.surplus.city} surplus`;
  } else {
    document.getElementById("transferSourceBranch").value = "B002";
    document.getElementById("transferDestBranch").value = "B001";
    document.getElementById("transferProduct").value = "P001";
    document.getElementById("transferQuantity").value = 10;
    document.getElementById("transferPriority").value = "MEDIUM";
    document.getElementById("transferReason").value = "Operational network rebalancing";
  }
  modal.classList.add("open");
}

function closeCreateTransferModal() {
  const modal = document.getElementById("createTransferModal");
  if (modal) modal.classList.remove("open");
}

async function handleCreateTransferSubmit(e) {
  e.preventDefault();
  const payload = {
    source_branch: document.getElementById("transferSourceBranch").value,
    destination_branch: document.getElementById("transferDestBranch").value,
    product_id: document.getElementById("transferProduct").value,
    quantity: parseFloat(document.getElementById("transferQuantity").value),
    priority: document.getElementById("transferPriority").value,
    reason: document.getElementById("transferReason").value,
  };

  if (payload.source_branch === payload.destination_branch) {
    showToast("Source and Destination branches cannot be the same.", "error");
    return;
  }
  if (!payload.quantity || payload.quantity <= 0) {
    showToast("Quantity must be greater than zero.", "error");
    return;
  }

  try {
    const res = await fetch("/api/transfers/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Transfer creation failed");
    }
    const data = await res.json();
    closeCreateTransferModal();
    showToast(`Transfer ${data.transfer.transfer_id} authorized & created!`, "success");
    // Refresh live overview
    await loadAllData();
  } catch (err) {
    showToast("Error creating transfer: " + err.message, "error");
  }
}

// ── Global Search ──
async function executeSearch(query) {
  const dropdown = document.getElementById("searchResultsDropdown");
  if (!dropdown) return;

  try {
    const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
    if (!res.ok) return;
    const data = await res.json();
    const results = data.results || [];

    if (results.length === 0) {
      dropdown.innerHTML = `<div style="padding:12px 16px; font-size:0.8rem; color:#64748b;">No results found for "${query}"</div>`;
    } else {
      dropdown.innerHTML = results.map(item => `
        <div class="search-result-item" onclick="handleSearchResultClick('${item.category}', '${item.id}')">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <span class="search-result-title">${item.title}</span>
            <span class="status-badge low" style="font-size:0.65rem;">${item.category}</span>
          </div>
          <div class="search-result-subtitle">${item.subtitle}</div>
        </div>
      `).join("");
    }
    dropdown.classList.add("open");
  } catch (err) {
    console.error("Search failed:", err);
  }
}

function handleSearchResultClick(category, id) {
  const dropdown = document.getElementById("searchResultsDropdown");
  if (dropdown) dropdown.classList.remove("open");

  if (category === "Branch") {
    filterByBranch(id);
  } else if (category === "Recommendation") {
    switchView("dashboard");
    const el = document.getElementById(`card-${id}`);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
      el.style.boxShadow = "0 0 0 3px #2563eb";
      setTimeout(() => el.style.boxShadow = "", 2500);
    }
  }
}

async function filterByBranch(branchId) {
  state.currentRegion = branchId;
  const select = document.getElementById("sidebarRegionSelect");
  if (select) select.value = branchId;
  const recSelect = document.getElementById("recFilterBranch");
  if (recSelect) recSelect.value = branchId;
  try {
    await fetchOverviewData();
  } catch (err) {
    console.error("Failed to update overview for branch:", err);
  }
  switchView("dashboard");
  renderAllComponents();
  showToast(`Filtered dashboard to Branch ${branchId}`, "info");
}

// ── Transfers Sub-View Table ──
async function loadTransfersView() {
  const tableBodies = [
    document.getElementById("transfersTableBody"),
    document.getElementById("transfersTableBodyDuplicate")
  ].filter(Boolean);

  if (tableBodies.length === 0) return;

  try {
    const res = await fetch("/api/transfers");
    if (!res.ok) throw new Error("Failed to load transfers");
    const data = await res.json();
    const list = data.transfers || [];

    if (list.length === 0) {
      tableBodies.forEach(tb => tb.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:24px; color:#64748b;">No transfer records available.</td></tr>`);
      return;
    }

    const html = list.map(t => `
      <tr>
        <td><strong>${t.transfer_id}</strong></td>
        <td>${t.source_city} (${t.source_branch})</td>
        <td>${t.destination_city} (${t.destination_branch})</td>
        <td>${t.product_name}</td>
        <td><strong>${t.quantity}</strong></td>
        <td>${t.lead_time_hours}h (${t.distance_km}km)</td>
        <td>₹${t.estimated_cost.toFixed(2)}</td>
        <td><span class="status-badge ${t.status.toLowerCase()}">${t.status}</span></td>
      </tr>
    `).join("");

    tableBodies.forEach(tb => tb.innerHTML = html);
  } catch (err) {
    tableBodies.forEach(tb => tb.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:24px; color:#dc2626;">Error loading transfers: ${err.message}</td></tr>`);
  }
}

// ── Branches Sub-View Directory ──
async function loadBranchesView() {
  const container = document.getElementById("branchesViewGrid");
  if (!container) return;

  try {
    const res = await fetch("/api/branches");
    if (!res.ok) throw new Error("Failed to load branches");
    const data = await res.json();
    const branches = data.branches || [];

    container.innerHTML = branches.map(b => `
      <div class="branch-card">
        <div class="branch-card-header">
          <div>
            <div class="branch-name-title">${b.city}</div>
            <div class="branch-city-sub">${b.branch_name} (${b.branch_id})</div>
          </div>
          <span class="status-badge ${b.status === 'CRITICAL' ? 'critical' : (b.status === 'WARNING' ? 'high' : 'green')}">${b.status}</span>
        </div>
        <div style="font-size:0.85rem; color:#475569; margin-bottom:10px;">
          <div>State: <strong>${b.state}</strong></div>
          <div>Capacity: <strong>${b.capacity} units</strong></div>
          <div>Current Stock: <strong>${b.current_stock.toLocaleString()} units</strong></div>
          <div>Utilization: <strong>${b.utilization_pct}%</strong></div>
        </div>
        <div class="progress-bar-bg">
          <div class="progress-bar-fill" style="width:${b.utilization_pct}%;"></div>
        </div>
        <div class="branch-stats-footer">
          <span>Shortage SKUs: <strong style="color:#dc2626;">${b.shortage_count}</strong></span>
          <span>Surplus SKUs: <strong style="color:#7c3aed;">${b.surplus_count}</strong></span>
          <button class="btn btn-primary btn-sm" onclick="filterByBranch('${b.branch_id}')">Select</button>
        </div>
      </div>
    `).join("");
  } catch (err) {
    container.innerHTML = `<div style="color:#dc2626;">Error loading branches: ${err.message}</div>`;
  }
}

// ── Toast Alerts ──
function showToast(message, type = "info") {
  let container = document.getElementById("toastContainer");
  if (!container) {
    container = document.createElement("div");
    container.id = "toastContainer";
    container.className = "toast-container";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      ${type === "success" ? '<polyline points="20 6 9 17 4 12"/>' : (type === "error" ? '<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>' : '<circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>')}
    </svg>
    <span>${message}</span>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
    setTimeout(() => toast.remove(), 250);
  }, 4000);
}
