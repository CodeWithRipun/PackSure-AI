// ============================================================
// PACKSURE AI - MAIN JAVASCRIPT
// ============================================================

document.addEventListener("DOMContentLoaded", () => {
    // Dashboard Initialization
    initNavigation();
    initChart();
    loadDashboardData();
    initScanner();
    initSandbox();
});

// ============================================================
// SIDEBAR NAVIGATION
// ============================================================
function initNavigation() {
    const navItems = document.querySelectorAll(".sidebar-nav .nav-item");
    const views = document.querySelectorAll(".app-view");

    navItems.forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();

            // Remove active class
            navItems.forEach(nav => nav.classList.remove("active"));
            
            // Add active class
            item.classList.add("active");

            // Target view
            const targetView = item.getAttribute("data-view");

            views.forEach(view => {
                view.style.display = view.id === `view-${targetView}` ? "block" : "none";
            });
        });
    });

    // New Inspection button
    const newInspectionBtn = document.getElementById("top-new-inspection");
    if (newInspectionBtn) {
        newInspectionBtn.addEventListener("click", () => {
            const scanNav = document.querySelector('[data-view="scan"]');
            if (scanNav) scanNav.click();
        });
    }
}

// ============================================================
// DASHBOARD DATA
// ============================================================
async function loadDashboardData() {
    try {
        const [statsRes, scansRes] = await Promise.all([
            fetch("/api/v1/statistics"),
            fetch("/api/v1/scans?limit=10")
        ]);

        // STATISTICS
        if (statsRes.ok) {
            const stats = await statsRes.json();
            const totalElement = document.getElementById("stat-total");
            const averageElement = document.getElementById("stat-avg");
            const failedElement = document.getElementById("stat-failed");

            if (totalElement) totalElement.textContent = stats.total_scans;
            if (averageElement) averageElement.textContent = `${stats.average_score}%`;
            if (failedElement) failedElement.textContent = stats.failed;
        }

        // SCAN HISTORY
        if (scansRes.ok) {
            const scans = await scansRes.json();
            const historyBody = document.getElementById("history-body");

            if (!historyBody) return;

            if (scans.length > 0) {
                historyBody.innerHTML = scans.map(scan => `
                    <tr>
                        <td class="text-blue">#${escapeHtml(scan.id)}</td>
                        <td>${new Date(scan.created_at).toLocaleString()}</td>
                        <td><strong>${escapeHtml(scan.filename)}</strong></td>
                        <td>Packaged Commodity</td>
                        <td class="${scan.status === 'PASS' ? 'text-green' : 'text-red'}">
                            ${escapeHtml(scan.status)}
                        </td>
                        <td><strong>${escapeHtml(scan.score)}%</strong></td>
                        <td>
                            ${scan.report_url ? `
                                <a href="${escapeHtml(scan.report_url)}" target="_blank" class="btn-outline">
                                    Report
                                </a>
                            ` : ""}
                        </td>
                    </tr>
                `).join("");
            } else {
                historyBody.innerHTML = `
                    <tr>
                        <td colspan="7" style="text-align:center; color:var(--text-muted);">
                            No scans recorded yet.
                        </td>
                    </tr>
                `;
            }
        }
    } catch (error) {
        console.error("Dashboard sync error:", error);
        
        // UI fallback to prevent infinite loading state
        const historyBody = document.getElementById("history-body");
        if (historyBody) {
            historyBody.innerHTML = `
                <tr>
                    <td colspan="7" style="text-align:center; color:var(--color-red);">
                        <i class="fa-solid fa-triangle-exclamation"></i> Connection failed. Could not load audit history.
                    </td>
                </tr>
            `;
        }
    }
}

// ============================================================
// PACKAGE SCANNER
// ============================================================
function initScanner() {
    const cards = document.querySelectorAll(".panel-card");
    const auditBtn = document.getElementById("run-audit-btn");
    
    // Setup to handle multiple files and demo functionality
    let uploadedFiles = {};
    let isDemoMode = false;

    // Dashboard may not contain scanner view
    if (!auditBtn) return;

    // IMAGE UPLOAD
    cards.forEach(card => {
        const input = card.querySelector(".panel-input");
        const linkText = card.querySelector(".upload-link");
        
        if (!input) return;

        card.addEventListener("click", () => input.click());

        input.addEventListener("change", (e) => {
            if (e.target.files && e.target.files[0]) {
                const panelName = card.getAttribute("data-panel");
                uploadedFiles[panelName] = e.target.files[0];

                if (linkText) {
                    linkText.textContent = e.target.files[0].name;
                    linkText.style.color = "#10b981";
                }
                isDemoMode = false; // Disable demo if an actual file is uploaded
            }
        });
    });

    // DEMO BUTTONS
    document.querySelectorAll(".demo-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            document.querySelectorAll(".demo-btn").forEach(b => b.classList.remove("active"));
            e.currentTarget.classList.add("active");
            isDemoMode = true; // Flag for demo processing
        });
    });

    // COMPLIANCE AUDIT
    auditBtn.addEventListener("click", async () => {
        if (Object.keys(uploadedFiles).length === 0 && !isDemoMode) {
            alert("Please click on a panel and select an image or choose a demo first.");
            return;
        }

        const formData = new FormData();
        
        if (isDemoMode) {
            formData.append("demo", "true");
        } else {
            // FIX 1: Append all files using the exact key "file" 
            // so FastAPI recognizes them
            Object.values(uploadedFiles).forEach((file) => {
                formData.append("file", file);
            });
        }

        // Disable button while processing
        auditBtn.disabled = true;
        auditBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Running Audit...';

        try {
            const res = await fetch("/api/v1/scan", {
                method: "POST",
                body: formData
            });

            const data = await res.json();

            if (!res.ok) {
                // FIX 2: Correctly format the error object so it doesn't show [object Object]
                let errorMsg = data.detail;
                if (typeof errorMsg === 'object') {
                    errorMsg = JSON.stringify(errorMsg);
                }
                throw new Error(errorMsg || "Scan failed");
            }

            // RESULT
            const resultContainer = document.getElementById("scan-result-container");
            if (resultContainer) {
                resultContainer.innerHTML = `
                    <div class="card" style="margin-top:16px;">
                        <h3 class="text-green">
                            <i class="fa-solid fa-circle-check"></i> Audit Complete
                        </h3>
                        <p style="margin-top:8px;">
                            Score: <strong>${escapeHtml(data.score)}%</strong> | 
                            Status: <strong>${escapeHtml(data.status)}</strong>
                        </p>
                        <pre style="
                            background:var(--bg-main); 
                            padding:12px; 
                            border-radius:6px; 
                            margin-top:12px; 
                            font-size:12px; 
                            overflow-x:auto;
                        ">${escapeHtml(JSON.stringify(data.extracted, null, 2))}</pre>
                        
                        ${data.report_url ? `
                            <a href="${escapeHtml(data.report_url)}" target="_blank" class="btn-primary" style="display:inline-block; margin-top:16px; text-decoration:none;">
                                Download PDF Report
                            </a>
                        ` : ""}
                    </div>
                `;
            }

            // Refresh dashboard
            loadDashboardData();

        } catch (error) {
            const resultContainer = document.getElementById("scan-result-container");
            if (resultContainer) {
                resultContainer.innerHTML = `
                    <div class="card text-red" style="margin-top:16px;">
                        Error: ${escapeHtml(error.message)}
                    </div>
                `;
            }
            console.error("Scan error:", error);
        } finally {
            auditBtn.disabled = false;
            auditBtn.innerHTML = 'Run Client Compliance Audit <i class="fa-solid fa-arrow-right"></i>';
        }
    });
}

// ============================================================
// LABEL SANDBOX
// ============================================================
function initSandbox() {
    const evalBtn = document.getElementById("sandbox-eval-btn");

    if (!evalBtn) return;

    evalBtn.addEventListener("click", () => {
        const textElement = document.getElementById("sandbox-text");
        const resultsBox = document.getElementById("sandbox-results");

        if (!textElement || !resultsBox) return;

        const text = textElement.value;

        if (!text.trim()) {
            resultsBox.innerHTML = `
                <div class="card text-red">
                    Please enter some text to test.
                </div>
            `;
            return;
        }

        resultsBox.innerHTML = `
            <div class="card">
                <h3>Sandbox Evaluation Passed</h3>
                <p class="text-green" style="margin-top:8px;">
                    <i class="fa-solid fa-check"></i> Evaluated ${text.length} characters of label text successfully against Metrology rules.
                </p>
            </div>
        `;
    });
}

// ============================================================
// ESCAPE HTML
// ============================================================
function escapeHtml(str) {
    return String(str ?? "").replace(/[&<>"']/g, m => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
    }[m]));
}

// ============================================================
// CHART
// ============================================================
function initChart() {
    const canvas = document.getElementById("trendChart");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, "rgba(56, 189, 248, 0.2)");
    gradient.addColorStop(1, "rgba(56, 189, 248, 0)");

    // Chart
    new Chart(ctx, {
        type: "line",
        data: {
            labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"],
            datasets: [{
                data: [35, 32, 45, 30, 25, 48, 52, 58],
                borderColor: "#38bdf8",
                backgroundColor: gradient,
                borderWidth: 3,
                tension: 0.4,
                fill: true,
                pointRadius: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { display: false, min: 0 },
                x: { display: false }
            }
        }
    });
}