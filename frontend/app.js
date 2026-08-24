/**
 * PREDICTIVE MAINTENANCE AI - PRECISION FRONTEND CONTROLLER
 */

let ws = null;
let machineInventory = [];
let activeMachine = { id: "MCH-07", name: "CNC Milling Machine - 07", condition: "Old Machine", type: "CNC Mill" };
let isAuthenticated = true;
let lastTelemetryTickTime = "--:--:--";
let currentUserRole = "Admin";

function updateAdminProfileDisplay(adminName, adminRole) {
    const nameElem = document.getElementById("sidebar-admin-name");
    const roleElem = document.getElementById("sidebar-admin-role");
    if (nameElem) nameElem.textContent = adminName || "Admin User";
    if (roleElem) roleElem.textContent = adminRole || "Admin";
}
window.updateAdminProfileDisplay = updateAdminProfileDisplay;

function applyUserRole(role) {
    currentUserRole = (role !== undefined && role !== null) ? role : "Admin";

    const roleInput = document.getElementById("set-user-role");

    if (roleInput && document.activeElement !== roleInput && roleInput.value !== currentUserRole) {
        roleInput.value = currentUserRole;
    }

    const adminNameInput = document.getElementById("set-admin-name");
    const adminName = adminNameInput ? adminNameInput.value : "Admin User";
    updateAdminProfileDisplay(adminName, currentUserRole);

    const addBtn = document.getElementById("btn-open-add-machine");
    if (addBtn) {
        if (currentUserRole && currentUserRole.toLowerCase() === "operator") {
            addBtn.style.opacity = "0.6";
            addBtn.title = "Operator Mode: Adding machines is restricted to Admin role";
        } else {
            addBtn.style.opacity = "1";
            addBtn.title = "";
        }
    }

    renderMachineInventoryTable();
}
window.applyUserRole = applyUserRole;

// Single Analytics Chart instance
let chartSingleSensorTrend = null;

// Telemetry Data Buffers (last 20 ticks)
const maxHistoryLength = 20;
const timeLabels = [];
const tempBuffer = [];
const pressBuffer = [];
const rpmBuffer = [];
const vibBuffer = [];
const utilBuffer = [];

// Alert Collections
let activeAlerts = [];
let alertsHistory = [];
let maintenanceHistory = [];

document.addEventListener("DOMContentLoaded", () => {
    initClock();
    initNetworkMonitor();
    initNavigation();
    initPasswordToggles();
    initModals();
    initSingleAnalyticsChart();
    initSettingsForm();
    initActions();
    loadMachinesFromBackend();
    connectWebSocket();
});

// Live Clock & Date Updater
function initClock() {
    function updateClock() {
        const now = new Date();
        const dateOptions = { month: 'short', day: 'numeric', year: 'numeric' };
        const timeOptions = { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true };

        const dElem = document.getElementById("current-date");
        const tElem = document.getElementById("current-time");

        if (dElem) dElem.textContent = now.toLocaleDateString('en-US', dateOptions);
        if (tElem) tElem.textContent = now.toLocaleTimeString('en-US', timeOptions);
    }
    updateClock();
    setInterval(updateClock, 1000);
}

// Network Online/Offline Monitor
function initNetworkMonitor() {
    function updateNetStatus() {
        const badge = document.getElementById("net-status-badge");
        if (!badge) return;

        if (navigator.onLine) {
            badge.textContent = "Online";
            badge.className = "pill-badge green";
        } else {
            badge.textContent = "Offline";
            badge.className = "pill-badge red";
        }
    }
    window.addEventListener("online", updateNetStatus);
    window.addEventListener("offline", updateNetStatus);
    updateNetStatus();
}

// Global Tab Switcher Function
function switchTab(tabId) {
    if (!tabId) return;
    document.body.classList.remove("logged-out");

    const navItems = document.querySelectorAll(".sidebar-nav .nav-item");
    const tabContents = document.querySelectorAll(".tab-content");

    navItems.forEach(n => {
        if (n.getAttribute("data-tab") === tabId) {
            n.classList.add("active");
        } else {
            n.classList.remove("active");
        }
    });

    tabContents.forEach(tc => {
        if (tc.id === `tab-${tabId}`) {
            tc.classList.add("active");
        } else {
            tc.classList.remove("active");
        }
    });

    if (tabId === "settings" && typeof window.loadSettings === "function") {
        window.loadSettings();
    }
}
window.switchTab = switchTab;

// Navigation Tabs Handler
function initNavigation() {
    document.body.classList.remove("logged-out");

    const navItems = document.querySelectorAll(".sidebar-nav .nav-item");
    navItems.forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            const tabId = item.getAttribute("data-tab");
            switchTab(tabId);
            window.location.hash = tabId;
        });
    });

    document.querySelectorAll(".nav-shortcut").forEach(btn => {
        btn.addEventListener("click", (e) => {
            e.preventDefault();
            const target = btn.getAttribute("data-target");
            switchTab(target);
            window.location.hash = target;
        });
    });

    window.addEventListener("hashchange", () => {
        const hashTab = window.location.hash.replace("#", "");
        if (hashTab) switchTab(hashTab);
    });

    if (window.location.hash) {
        const initialTab = window.location.hash.replace("#", "");
        switchTab(initialTab);
    }
}

// Password Eye Toggle
function initPasswordToggles() {
    document.querySelectorAll(".eye-toggle-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const targetId = btn.getAttribute("data-target");
            const input = document.getElementById(targetId);
            if (!input) return;

            if (input.type === "password") {
                input.type = "text";
                btn.textContent = "🙈";
            } else {
                input.type = "password";
                btn.textContent = "👁️";
            }
        });
    });
}

// Load Machines from Backend
async function loadMachinesFromBackend() {
    try {
        const res = await fetch("/api/machines");
        const data = await res.json();
        machineInventory = data.machines || [];
        if (machineInventory.length > 0) {
            activeMachine = data.active_machine || machineInventory[0];
        } else {
            activeMachine = { id: "N/A", name: "No Machine Available", condition: "N/A", type: "N/A" };
        }

        renderMachineInventoryTable();
        renderAnalyticsMachineDropdown();
        renderMaintenanceMachineDropdown();
        renderAlertsLists();
        await loadMaintenanceHistoryFromBackend();
    } catch (err) {
        console.error("Error loading machines:", err);
    }
}

// Render Industrial Machine Inventory Table with Trash (Delete) and Pencil (Edit) Icons
function renderMachineInventoryTable() {
    const tbody = document.getElementById("inventory-table-body");
    if (!tbody) return;

    if (machineInventory.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-muted text-center">No machines in inventory. Click '+ Add New Machine' to add one.</td></tr>`;
        return;
    }

    const isOperator = currentUserRole === "Operator";

    tbody.innerHTML = machineInventory.map(m => `
        <tr>
            <td><strong>${m.id}</strong></td>
            <td>${m.name}</td>
            <td><span class="status-badge ${m.condition === 'New Machine' ? 'blue' : 'yellow'}">${m.condition || 'Old Machine'}</span></td>
            <td>${m.type || 'CNC Mill'}</td>
            <td>
                <div class="action-icons-group">
                    <button class="action-icon-btn delete-icon" onclick="deleteMachine('${m.id}')" title="${isOperator ? 'Operator Notice: Admin permissions required to delete machines' : 'Delete Machine'}">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                    </button>
                    <button class="action-icon-btn edit-icon" onclick="openEditMachineModal('${m.id}')" title="${isOperator ? 'Operator Notice: Admin permissions required to edit machines' : 'Edit Machine Details'}">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                    </button>
                </div>
            </td>
        </tr>
    `).join("");
}

// Add New Machine
async function addMachineHandler(machineId, machineName, condition, machineType) {
    if (currentUserRole === "Operator") {
        showToast("Operator Notice: Admin permissions required to add machines.");
        return;
    }

    try {
        const res = await fetch("/api/machines/add", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ machine_id: machineId, machine_name: machineName, condition: condition, type: machineType })
        });
        const data = await res.json();

        if (res.ok) {
            machineInventory = data.machines;
            showToast(`Added ${machineId} (${machineName}) to inventory.`);
            renderMachineInventoryTable();
            renderAnalyticsMachineDropdown();
            renderAlertsLists();
        } else {
            showToast(`Error: ${data.detail}`);
        }
    } catch (err) {
        console.error("Error adding machine:", err);
    }
}

// Open Edit Machine Modal
window.openEditMachineModal = function (machineId) {
    if (currentUserRole === "Operator") {
        showToast("Operator Notice: Machine modifications require Admin permissions.");
        return;
    }

    const target = machineInventory.find(m => m.id.toLowerCase() === machineId.toLowerCase());
    if (!target) return;

    document.getElementById("edit-old-id").value = target.id;
    document.getElementById("edit-machine-id").value = target.id;
    document.getElementById("edit-machine-name").value = target.name;
    document.getElementById("edit-machine-condition").value = target.condition || "Old Machine";
    document.getElementById("edit-machine-type").value = target.type || "CNC Mill";

    openModal("modal-edit-machine");
};

// Save Edited Machine
async function editMachineHandler(oldId, newId, name, condition, type) {
    if (currentUserRole === "Operator") {
        showToast("Operator Notice: Machine modifications require Admin permissions.");
        return;
    }

    try {
        const res = await fetch("/api/machines/edit", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ old_id: oldId, machine_id: newId, machine_name: name, condition: condition, type: type })
        });
        const data = await res.json();

        if (res.ok) {
            machineInventory = data.machines;
            if (activeMachine.id.toLowerCase() === oldId.toLowerCase()) {
                activeMachine = data.machine;
            }
            showToast(`Updated details for machine ${newId}.`);
            renderMachineInventoryTable();
            renderAnalyticsMachineDropdown();
        } else {
            showToast(`Error: ${data.detail}`);
        }
    } catch (err) {
        console.error("Error editing machine:", err);
    }
}

// Delete Machine
window.deleteMachine = async function (machineId) {
    if (currentUserRole === "Operator") {
        showToast("Operator Notice: Deleting machines requires Admin permissions.");
        return;
    }

    if (!confirm(`Are you sure you want to delete ${machineId} from machine inventory?`)) return;

    try {
        const res = await fetch(`/api/machines/${machineId}`, { method: "DELETE" });
        const data = await res.json();

        if (res.ok) {
            machineInventory = data.machines;
            showToast(`Deleted machine ${machineId} from inventory.`);

            // Purge alerts for deleted machine
            activeAlerts = activeAlerts.filter(a => a.machine_id.toLowerCase() !== machineId.toLowerCase());
            alertsHistory = alertsHistory.filter(a => a.machine_id.toLowerCase() !== machineId.toLowerCase());

            renderMachineInventoryTable();
            renderAnalyticsMachineDropdown();
            renderAlertsLists();
        }
    } catch (err) {
        console.error("Error deleting machine:", err);
    }
};

// Analytics Machine Dropdown Sync
function renderAnalyticsMachineDropdown() {
    const select = document.getElementById("analytics-machine-select");
    if (!select) return;

    if (machineInventory.length === 0) {
        select.innerHTML = `<option value="">No Machines Available</option>`;
        return;
    }

    select.innerHTML = machineInventory.map(m => `
        <option value="${m.id}" ${m.id === activeMachine.id ? 'selected' : ''}>${m.name} (${m.id})</option>
    `).join("");

    select.onchange = async () => {
        const selectedId = select.value;
        if (selectedId) await selectActiveMachine(selectedId);
    };
}

async function selectActiveMachine(machineId) {
    try {
        const res = await fetch("/api/select-machine", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ machine_id: machineId })
        });
        const data = await res.json();
        activeMachine = data.selected_machine;

        // Clear graph telemetry history buffers on active machine change
        timeLabels.length = 0;
        tempBuffer.length = 0;
        pressBuffer.length = 0;
        rpmBuffer.length = 0;
        vibBuffer.length = 0;
        utilBuffer.length = 0;
        if (chartSingleSensorTrend) {
            chartSingleSensorTrend.update();
        }

        showToast(`Target machine selected: ${activeMachine.name}`);
    } catch (err) {
        console.error("Error selecting machine:", err);
    }
}

// Render Alerts (Filtered by Active Machine Inventory)
function renderAlertsLists() {
    const activeIds = machineInventory.map(m => m.id.toUpperCase());

    const filteredActive = activeAlerts.filter(alt => activeIds.includes(alt.machine_id.toUpperCase()));
    const filteredHistory = alertsHistory.filter(alt => activeIds.includes(alt.machine_id.toUpperCase()));

    // Update count badge
    const badgeCount = document.getElementById("alerts-count");
    if (badgeCount) badgeCount.textContent = filteredActive.length;

    // Current Active Alerts Column
    const activeContainer = document.getElementById("current-active-alerts-list");
    if (activeContainer) {
        if (filteredActive.length === 0) {
            activeContainer.innerHTML = `<div class="text-muted text-sm">No active alerts for machines in inventory.</div>`;
        } else {
            activeContainer.innerHTML = filteredActive.map(alt => `
                <div class="history-item">
                    <span class="h-time">${alt.time}</span>
                    <span class="h-msg"><strong>${alt.machine_id}</strong>: ${alt.msg}</span>
                    <span class="status-badge ${alt.severity}">${alt.status}</span>
                </div>
            `).join("");
        }
    }

    // Alerts History Column
    const historyContainer = document.getElementById("full-alerts-history-list");
    if (historyContainer) {
        if (filteredHistory.length === 0) {
            historyContainer.innerHTML = `<div class="text-muted text-sm">No past alert history recorded.</div>`;
        } else {
            historyContainer.innerHTML = filteredHistory.map(alt => `
                <div class="history-item">
                    <span class="h-time">${alt.time}</span>
                    <span class="h-msg"><strong>${alt.machine_id}</strong> - ${alt.msg}</span>
                    <span class="status-badge ${alt.severity}">${alt.status}</span>
                </div>
            `).join("");
        }
    }
}

// Render Maintenance History (Clean Empty State if none completed)
function renderMaintenanceHistory() {
    const dashList = document.getElementById("dash-maint-history-list");
    if (!dashList) return;

    if (maintenanceHistory.length === 0) {
        dashList.innerHTML = `<div class="text-muted text-sm p-12">No completed maintenance history recorded.</div>`;
    } else {
        dashList.innerHTML = maintenanceHistory.map(item => `
            <div class="history-item">
                <span class="h-time">${item.time}</span>
                <span class="h-msg"><strong>${item.machine_id}</strong>: ${item.action}</span>
                <span class="status-badge green">Completed</span>
            </div>
        `).join("");
    }
}

// WebSocket Telemetry Listener
function connectWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host || "127.0.0.1:8000";
    const wsUrl = `${protocol}//${host}/ws/telemetry`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        isConnected = true;
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            updateDashboard(data);
        } catch (err) {
            console.error("Error parsing WebSocket telemetry payload:", err);
        }
    };

    ws.onerror = (err) => {
        isConnected = false;
    };

    ws.onclose = () => {
        isConnected = false;
        setTimeout(connectWebSocket, 3000);
    };
}

// Update Telemetry Payload
function updateDashboard(payload) {
    const isNoMachine = payload.no_machine || payload.machine_id === "N/A" || machineInventory.length === 0;

    // Exact Live Update Timestamp (from telemetry tick, NOT current clock)
    lastTelemetryTickTime = isNoMachine ? "--:--:--" : payload.timestamp;

    // Dashboard & Analytics Machine Banner Values
    const mName = isNoMachine ? "No Machine Available" : payload.machine_name;
    const mId = isNoMachine ? "N/A" : payload.machine_id;
    const mType = isNoMachine ? "N/A" : (payload.machine_type || "CNC Mill");
    const lastUpd = isNoMachine ? "--:--:--" : `${lastTelemetryTickTime} (Live)`;

    const setElemText = (id, text) => { const el = document.getElementById(id); if (el) el.textContent = text; };

    setElemText("machine-name-display", mName);
    setElemText("machine-id-display", mId);
    setElemText("machine-type-display", mType);
    setElemText("last-updated-display", lastUpd);

    setElemText("an-machine-name-display", mName);
    setElemText("an-machine-id-display", mId);
    setElemText("an-machine-type-display", mType);
    setElemText("an-last-updated-display", lastUpd);

    // Keep analytics dropdown in sync if needed
    const anSelect = document.getElementById("analytics-machine-select");
    if (anSelect && payload.machine_id && anSelect.value !== payload.machine_id && document.activeElement !== anSelect) {
        anSelect.value = payload.machine_id;
    }

    const kpis = payload.kpis || {};
    const telemetry = payload.telemetry || {};

    const uHealth = document.getElementById("unit-health-score");
    const uRisk = document.getElementById("unit-failure-risk");

    if (isNoMachine) {
        setElemText("val-health-score", "--");
        if (uHealth) uHealth.style.display = "none";
        setElemText("val-health-text", "No Machine");

        const healthRing = document.getElementById("health-ring");
        if (healthRing) {
            healthRing.style.setProperty("--pct", 0);
            healthRing.style.setProperty("--ring-color", "#64748b");
        }

        setElemText("val-anomaly-score", "--");
        setElemText("val-anomaly-thresh", "--");

        setElemText("val-rul-hours", "--");
        setElemText("val-rul-days", "--");

        setElemText("val-failure-risk", "--");
        if (uRisk) uRisk.style.display = "none";
        setElemText("val-risk-level", "N/A");

        // Analytics Page Parameter Cards
        setElemText("an-temp-val", "--");
        setElemText("an-press-val", "--");
        setElemText("an-rpm-val", "--");
        setElemText("an-vib-val", "--");
        setElemText("an-util-val", "--");
        return;
    }

    // Normal State when machine is active
    if (uHealth) { uHealth.style.display = "inline"; uHealth.textContent = "%"; }
    if (uRisk) { uRisk.style.display = "inline"; uRisk.textContent = "%"; }

    // Dashboard 4 KPI Cards
    const ringColor = kpis.health_score >= 88 ? "#22c55e" : (kpis.health_score >= 60 ? "#eab308" : "#ef4444");

    setElemText("val-health-score", kpis.health_score);
    setElemText("val-health-text", kpis.health_status);
    const healthRing = document.getElementById("health-ring");
    if (healthRing) {
        healthRing.style.setProperty("--pct", kpis.health_score);
        healthRing.style.setProperty("--ring-color", ringColor);
    }

    setElemText("val-anomaly-score", kpis.anomaly_score);
    setElemText("val-anomaly-thresh", kpis.anomaly_threshold);

    setElemText("val-rul-hours", kpis.rul_hours);
    setElemText("val-rul-days", kpis.rul_days);

    setElemText("val-failure-risk", kpis.failure_risk_pct);
    setElemText("val-risk-level", `${kpis.risk_level} Risk`);

    // Analytics Page Parameter Cards
    setElemText("an-temp-val", typeof telemetry.temperature === 'number' ? telemetry.temperature.toFixed(1) : "--");
    setElemText("an-press-val", typeof telemetry.pressure === 'number' ? telemetry.pressure.toFixed(2) : "--");
    setElemText("an-rpm-val", typeof telemetry.rpm === 'number' ? Math.round(telemetry.rpm) : "--");
    setElemText("an-vib-val", typeof telemetry.vibration === 'number' ? telemetry.vibration.toFixed(2) : "--");
    setElemText("an-util-val", kpis.machine_utilization_pct || 78);

    // Trigger Real Anomaly Alert if vibration > 3.8 or anomaly_score > threshold
    if (telemetry.vibration > 3.8 || kpis.anomaly_score > kpis.anomaly_threshold) {
        const alertMsg = `Vibration elevated to ${telemetry.vibration.toFixed(2)} mm/s (High mechanical friction)`;
        const existing = activeAlerts.find(a => a.machine_id === payload.machine_id);
        if (!existing) {
            const newAlt = {
                id: `alt-${Date.now()}`,
                machine_id: payload.machine_id,
                time: payload.timestamp,
                msg: alertMsg,
                status: "Critical",
                severity: "red"
            };
            activeAlerts.unshift(newAlt);
            alertsHistory.unshift(newAlt);
            renderAlertsLists();
        }
    } else {
        // Clear active alert if back to normal
        activeAlerts = activeAlerts.filter(a => a.machine_id !== payload.machine_id);
        renderAlertsLists();
    }

    // Update Analytics Single Chart Buffers
    timeLabels.push(payload.timestamp);
    tempBuffer.push(telemetry.temperature);
    pressBuffer.push(telemetry.pressure);
    rpmBuffer.push(telemetry.rpm / 20.0);
    vibBuffer.push(telemetry.vibration * 10.0);
    utilBuffer.push(kpis.machine_utilization_pct || 78);

    if (timeLabels.length > maxHistoryLength) {
        timeLabels.shift();
        tempBuffer.shift();
        pressBuffer.shift();
        rpmBuffer.shift();
        vibBuffer.shift();
        utilBuffer.shift();
    }

    if (chartSingleSensorTrend) {
        chartSingleSensorTrend.update('none');
    }
}

// Single Analytics Chart
function initSingleAnalyticsChart() {
    const ctx = document.getElementById("chart-single-sensor-trend")?.getContext("2d");
    if (!ctx) return;

    chartSingleSensorTrend = new Chart(ctx, {
        type: 'line',
        data: {
            labels: timeLabels,
            datasets: [
                { label: 'Temperature (°C)', data: tempBuffer, borderColor: '#ffb4ab', borderWidth: 2.5, tension: 0.4, pointRadius: 0 },
                { label: 'Pressure (bar)', data: pressBuffer, borderColor: '#a8c7fa', borderWidth: 2.5, tension: 0.4, pointRadius: 0 },
                { label: 'RPM (scaled x10)', data: rpmBuffer, borderColor: '#6ddb95', borderWidth: 2.5, tension: 0.4, pointRadius: 0 },
                { label: 'Vibration (scaled x10)', data: vibBuffer, borderColor: '#d6befe', borderWidth: 2.5, tension: 0.4, pointRadius: 0 },
                { label: 'Machine Utilization (%)', data: utilBuffer, borderColor: '#bbc7db', borderWidth: 2.5, tension: 0.4, pointRadius: 0 }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { color: '#44474f' }, ticks: { color: '#c4c6d0', maxTicksLimit: 8 } },
                y: { grid: { color: '#44474f' }, ticks: { color: '#c4c6d0', stepSize: 10 }, min: 0, max: 100 }
            }
        }
    });
}

// Modals Management & Authentication
function initModals() {
    document.getElementById("btn-open-add-machine")?.addEventListener("click", () => openModal("modal-add-machine"));

    document.getElementById("btn-auth-action")?.addEventListener("click", () => {
        if (isAuthenticated) {
            logoutUser();
        } else {
            openModal("modal-signin");
        }
    });

    document.getElementById("btn-forgot-password")?.addEventListener("click", () => {
        alert("Password reset link has been dispatched to your registered admin email.");
    });

    document.querySelectorAll("[data-close]").forEach(btn => {
        btn.addEventListener("click", () => {
            const modalId = btn.getAttribute("data-close");
            closeModal(modalId);
        });
    });

    // Add Machine Form
    document.getElementById("form-add-machine")?.addEventListener("submit", async (e) => {
        e.preventDefault();
        const mId = document.getElementById("add-machine-id").value;
        const mName = document.getElementById("add-machine-name").value;
        const mCond = document.getElementById("add-machine-condition").value;
        const mType = document.getElementById("add-machine-type").value;

        await addMachineHandler(mId, mName, mCond, mType);
        closeModal("modal-add-machine");
        e.target.reset();
    });

    // Edit Machine Form
    document.getElementById("form-edit-machine")?.addEventListener("submit", async (e) => {
        e.preventDefault();
        const oldId = document.getElementById("edit-old-id").value;
        const newId = document.getElementById("edit-machine-id").value;
        const mName = document.getElementById("edit-machine-name").value;
        const mCond = document.getElementById("edit-machine-condition").value;
        const mType = document.getElementById("edit-machine-type").value;

        await editMachineHandler(oldId, newId, mName, mCond, mType);
        closeModal("modal-edit-machine");
    });

    // Add Maintenance Form
    document.getElementById("form-add-maintenance")?.addEventListener("submit", async (e) => {
        e.preventDefault();
        const mId = document.getElementById("maint-machine-select").value;
        const tech = document.getElementById("maint-technician-input").value;
        const act = document.getElementById("maint-action-input").value;

        if (!mId) {
            showToast("Please select a target machine.");
            return;
        }

        await addMaintenanceHandler(mId, act, tech);
        document.getElementById("maint-action-input").value = "";
    });
}

function openModal(modalId) {
    document.getElementById(modalId)?.classList.remove("hidden");
}

function closeModal(modalId) {
    document.getElementById(modalId)?.classList.add("hidden");
}

// Settings Form
function initSettingsForm() {
    const form = document.getElementById("form-settings");
    const roleInput = document.getElementById("set-user-role");
    const nameInput = document.getElementById("set-admin-name");

    // Force light theme mode permanently
    document.documentElement.setAttribute("data-theme", "light");

    async function loadSettings() {
        try {
            const res = await fetch("/api/settings");
            if (res.ok) {
                const s = await res.json();
                const setVal = (id, val) => {
                    const el = document.getElementById(id);
                    if (el && val !== undefined && val !== null) el.value = val;
                };

                setVal("set-admin-name", s.admin_name);
                setVal("set-admin-number", s.admin_number);
                setVal("set-admin-email", s.admin_email);
                setVal("set-company-name", s.company_name);
                setVal("set-block-name", s.block_name);
                setVal("set-user-role", s.role);

                const loadedName = (nameInput && nameInput.value) ? nameInput.value : (s.admin_name || "Admin User");
                const loadedRole = (roleInput && roleInput.value) ? roleInput.value : (s.role || "Admin");

                applyUserRole(loadedRole);
                updateAdminProfileDisplay(loadedName, loadedRole);
            }
        } catch (err) {
            console.error("Failed to load settings:", err);
        }
    }
    window.loadSettings = loadSettings;

    loadSettings();

    form?.addEventListener("submit", async (e) => {
        e.preventDefault();

        const adminName = (document.getElementById("set-admin-name")?.value || "").trim();
        const adminNumber = (document.getElementById("set-admin-number")?.value || "").trim();
        const adminEmail = (document.getElementById("set-admin-email")?.value || "").trim();
        const companyName = (document.getElementById("set-company-name")?.value || "").trim();
        const blockName = (document.getElementById("set-block-name")?.value || "").trim();
        const selectedRole = (document.getElementById("set-user-role")?.value || "").trim();

        // Validation: If any details are missing, show unsuccessful toast and return
        if (!adminName || !adminNumber || !adminEmail || !companyName || !blockName || !selectedRole) {
            showToast("System Settings changed unsuccessfully.");
            return;
        }

        const payload = {
            admin_name: adminName,
            admin_number: adminNumber,
            admin_email: adminEmail,
            company_name: companyName,
            block_name: blockName,
            theme: "light",
            role: selectedRole
        };

        try {
            const res = await fetch("/api/settings", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                applyUserRole(selectedRole);
                updateAdminProfileDisplay(adminName, selectedRole);
                showToast("System Settings saved successfully.");
            } else {
                showToast("System Settings changed unsuccessfully.");
            }
        } catch (err) {
            console.error("Error saving settings:", err);
            showToast("System Settings changed unsuccessfully.");
        }
    });
}

function initActions() { }

// Download Reports Helper
window.downloadReport = function (reportType, format) {
    const url = `/api/export-report?machine_id=${activeMachine.id}&format=${format}&report_type=${reportType}`;
    window.open(url, '_blank');
    showToast(`Downloading ${reportType.toUpperCase()} ${format.toUpperCase()} Report...`);
};

// Toast Notifications Helper
function showToast(message) {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = "toast";
    toast.textContent = message;

    container.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 4000);
}
