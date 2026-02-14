// MedAudit Demo UI - Interactive Testing Interface
// Connects to AI Orchestrator API at http://localhost:5001

const API_BASE_URL = 'http://localhost:5001';

// Store for tracking ongoing audits
let activeAudits = new Map();
let pollInterval = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    checkAPIStatus();
    loadQueueStats();

    // Auto-refresh queue stats every 5 seconds
    setInterval(loadQueueStats, 5000);
});

/**
 * Check if API is available
 */
async function checkAPIStatus() {
    const statusIndicator = document.getElementById('api-status');
    const statusText = document.getElementById('api-status-text');

    try {
        const response = await fetch(`${API_BASE_URL}/health`, {
            method: 'GET',
            mode: 'cors'
        });

        if (response.ok) {
            statusIndicator.className = 'w-3 h-3 rounded-full bg-green-500';
            statusText.textContent = 'API Connected';
            statusText.className = 'text-sm text-green-600';
        } else {
            throw new Error('API returned error');
        }
    } catch (error) {
        statusIndicator.className = 'w-3 h-3 rounded-full bg-red-500';
        statusText.textContent = 'API Offline';
        statusText.className = 'text-sm text-red-600';
        console.error('API health check failed:', error);
    }
}

/**
 * Load demo patient data (Mrs. Justine Garnett)
 */
function loadDemoPatient() {
    document.getElementById('patient-id').value = '39b7de4b-abf2-d772-461e-193e503a035b';
    document.getElementById('audit-type').value = 'breast_cancer_screening';

    // Show notification
    showNotification('Demo patient loaded: Mrs. Justine Garnett', 'success');
}

/**
 * Submit audit request
 */
async function submitAudit(event) {
    event.preventDefault();

    const patientId = document.getElementById('patient-id').value.trim();
    const auditType = document.getElementById('audit-type').value;
    const submitBtn = document.getElementById('submit-btn');

    if (!patientId) {
        showNotification('Please enter a patient ID', 'error');
        return;
    }

    // Disable submit button
    submitBtn.disabled = true;
    submitBtn.innerHTML = '⏳ Submitting...';

    try {
        const response = await fetch(`${API_BASE_URL}/audit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                patient_id: patientId,
                audit_type: auditType
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to submit audit');
        }

        const data = await response.json();

        // Show results section
        document.getElementById('results-section').classList.remove('hidden');

        // Start tracking this job
        activeAudits.set(data.job_id, {
            patient_id: patientId,
            audit_type: auditType,
            submitted_at: new Date()
        });

        // Show queued status
        updateJobStatus(data.job_id, 'PENDING', {
            patient_id: patientId,
            audit_type: auditType
        });

        // Start polling for results
        startPolling(data.job_id);

        showNotification(`Audit queued successfully! Job ID: ${data.job_id.substring(0, 8)}...`, 'success');

        // Add to recent audits
        addToRecentAudits(data.job_id, patientId, auditType);

    } catch (error) {
        console.error('Error submitting audit:', error);
        showNotification(`Error: ${error.message}`, 'error');
        document.getElementById('results-section').classList.add('hidden');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '🚀 Submit Audit';
    }
}

/**
 * Poll for job status and results
 */
function startPolling(jobId) {
    // Clear any existing poll interval
    if (pollInterval) {
        clearInterval(pollInterval);
    }

    // Poll every 2 seconds
    pollInterval = setInterval(async () => {
        await checkJobStatus(jobId);
    }, 2000);

    // Also check immediately
    checkJobStatus(jobId);
}

/**
 * Check status of a specific job
 */
async function checkJobStatus(jobId) {
    try {
        const response = await fetch(`${API_BASE_URL}/audit/${jobId}`);

        if (!response.ok) {
            throw new Error('Failed to fetch job status');
        }

        const data = await response.json();
        const status = data.state || data.status;

        updateJobStatus(jobId, status, data);

        // If completed or failed, fetch final result
        if (status === 'SUCCESS') {
            clearInterval(pollInterval);
            await fetchAuditResult(jobId);
        } else if (status === 'FAILURE') {
            clearInterval(pollInterval);
            showJobError(jobId, data.error || 'Audit failed');
        }

    } catch (error) {
        console.error('Error checking job status:', error);
    }
}

/**
 * Fetch final audit result
 */
async function fetchAuditResult(jobId) {
    try {
        const response = await fetch(`${API_BASE_URL}/audit/${jobId}/result`);

        if (!response.ok) {
            throw new Error('Failed to fetch audit result');
        }

        const data = await response.json();
        displayAuditReport(jobId, data);

    } catch (error) {
        console.error('Error fetching audit result:', error);
        showJobError(jobId, error.message);
    }
}

/**
 * Update job status display
 */
function updateJobStatus(jobId, status, data) {
    const statusDiv = document.getElementById('job-status');

    let statusClass, statusIcon, statusText, progressBar;

    switch (status) {
        case 'PENDING':
            statusClass = 'bg-yellow-50 border border-yellow-200';
            statusIcon = '⏳';
            statusText = 'Audit queued, waiting for worker...';
            progressBar = `
                <div class="mt-2 w-full bg-gray-200 rounded-full h-2">
                    <div class="bg-yellow-500 h-2 rounded-full w-1/4"></div>
                </div>`;
            break;
        case 'PROCESSING':
        case 'STARTED':
            statusClass = 'bg-blue-50 border border-blue-200';
            statusIcon = '🔄';
            statusText = 'Processing audit...';
            progressBar = `
                <div class="mt-2 w-full bg-gray-200 rounded-full h-2">
                    <div class="bg-blue-500 h-2 rounded-full w-3/4 pulse-slow"></div>
                </div>`;
            break;
        case 'SUCCESS':
            statusClass = 'bg-green-50 border border-green-200';
            statusIcon = '✅';
            statusText = 'Audit completed successfully!';
            progressBar = `
                <div class="mt-2 w-full bg-gray-200 rounded-full h-2">
                    <div class="bg-green-500 h-2 rounded-full w-full"></div>
                </div>`;
            break;
        case 'FAILURE':
            statusClass = 'bg-red-50 border border-red-200';
            statusIcon = '❌';
            statusText = 'Audit failed';
            progressBar = '';
            break;
        default:
            statusClass = 'bg-gray-50 border border-gray-200';
            statusIcon = '❓';
            statusText = `Status: ${status}`;
            progressBar = '';
    }

    statusDiv.className = `mb-4 p-4 rounded-lg ${statusClass}`;
    statusDiv.innerHTML = `
        <div class="flex items-center gap-2">
            <span class="text-2xl">${statusIcon}</span>
            <div class="flex-1">
                <p class="font-semibold">${statusText}</p>
                <p class="text-xs text-gray-600 mt-1">Job ID: ${jobId.substring(0, 16)}...</p>
            </div>
        </div>
        ${progressBar}
    `;
}

/**
 * Display audit report
 */
function displayAuditReport(jobId, data) {
    const reportDiv = document.getElementById('audit-report');
    const report = data.report || {};

    const compliant = report.compliant;
    const gaps = report.gaps || [];
    const evidence = report.evidence || [];
    const sources = data.sources || [];

    // Build evidence HTML
    let evidenceHTML = '';
    if (evidence && evidence.length > 0) {
        evidenceHTML = `
            <div class="mt-4">
                <h4 class="font-semibold text-gray-800 mb-2">Evidence (${evidence.length} findings):</h4>
                <div class="space-y-3">
                    ${evidence.map((item, idx) => `
                        <div class="bg-gray-50 p-3 rounded border border-gray-200">
                            <p class="text-sm font-medium text-gray-700">Guideline:</p>
                            <p class="text-sm text-gray-600 mb-2">${escapeHtml(item.guideline)}</p>
                            <p class="text-sm font-medium text-gray-700">Violation:</p>
                            <p class="text-sm text-gray-600">${escapeHtml(item.violation)}</p>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    // Build gaps HTML
    let gapsHTML = '';
    if (gaps && gaps.length > 0) {
        gapsHTML = `
            <div class="mt-4">
                <h4 class="font-semibold text-gray-800 mb-2">Identified Gaps (${gaps.length}):</h4>
                <ul class="list-disc list-inside space-y-1">
                    ${gaps.map(gap => `<li class="text-sm text-gray-700">${escapeHtml(gap)}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    // Build sources HTML
    let sourcesHTML = '';
    if (sources && sources.length > 0) {
        sourcesHTML = `
            <div class="mt-4">
                <h4 class="font-semibold text-gray-800 mb-2">Referenced Guidelines (${sources.length}):</h4>
                <div class="space-y-2">
                    ${sources.slice(0, 3).map((source, idx) => `
                        <div class="bg-purple-50 p-2 rounded text-xs text-gray-700">
                            ${escapeHtml(source.substring(0, 200))}${source.length > 200 ? '...' : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    reportDiv.className = 'p-6 rounded-lg border-2 ' +
        (compliant ? 'bg-green-50 border-green-300' : 'bg-red-50 border-red-300');

    reportDiv.innerHTML = `
        <div class="flex items-center gap-3 mb-4">
            <span class="text-4xl">${compliant ? '✅' : '❌'}</span>
            <div>
                <h3 class="text-2xl font-bold ${compliant ? 'text-green-800' : 'text-red-800'}">
                    ${compliant ? 'COMPLIANT' : 'NON-COMPLIANT'}
                </h3>
                <p class="text-sm text-gray-600">Patient: ${data.patient_id}</p>
                <p class="text-sm text-gray-600">Audit Type: ${formatAuditType(data.audit_type)}</p>
            </div>
        </div>

        ${gapsHTML}
        ${evidenceHTML}
        ${sourcesHTML}

        <div class="mt-6 pt-4 border-t border-gray-300">
            <p class="text-xs text-gray-500">
                Completed at ${new Date().toLocaleString()}
            </p>
        </div>
    `;

    reportDiv.classList.remove('hidden');
}

/**
 * Show job error
 */
function showJobError(jobId, errorMessage) {
    const reportDiv = document.getElementById('audit-report');

    reportDiv.className = 'p-6 rounded-lg border-2 bg-red-50 border-red-300';
    reportDiv.innerHTML = `
        <div class="flex items-center gap-3 mb-4">
            <span class="text-4xl">❌</span>
            <div>
                <h3 class="text-2xl font-bold text-red-800">Audit Failed</h3>
                <p class="text-sm text-gray-600">Job ID: ${jobId.substring(0, 16)}...</p>
            </div>
        </div>
        <div class="bg-white p-4 rounded border border-red-200">
            <p class="text-sm text-gray-700 font-mono">${escapeHtml(errorMessage)}</p>
        </div>
    `;

    reportDiv.classList.remove('hidden');
}

/**
 * Load queue statistics
 */
async function loadQueueStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/queue/stats`);

        if (!response.ok) {
            throw new Error('Failed to fetch queue stats');
        }

        const data = await response.json();

        // Update worker count
        const workerCount = data.active_workers || 0;
        const workerElem = document.getElementById('worker-count');
        workerElem.textContent = workerCount;
        workerElem.className = workerCount > 0 ? 'font-bold text-green-600' : 'font-bold text-red-600';

        // Update active jobs
        const activeJobs = data.active_jobs || 0;
        document.getElementById('active-jobs').textContent = activeJobs;

        // Update queued jobs
        const queuedJobs = data.queued_jobs || 0;
        document.getElementById('queued-jobs').textContent = queuedJobs;

    } catch (error) {
        console.error('Error loading queue stats:', error);
        document.getElementById('worker-count').textContent = '?';
        document.getElementById('active-jobs').textContent = '?';
        document.getElementById('queued-jobs').textContent = '?';
    }
}

/**
 * Add job to recent audits list
 */
function addToRecentAudits(jobId, patientId, auditType) {
    const recentDiv = document.getElementById('recent-audits');

    // Clear "No audits yet" message
    if (recentDiv.querySelector('p.text-gray-500')) {
        recentDiv.innerHTML = '';
    }

    const auditItem = document.createElement('div');
    auditItem.className = 'p-2 bg-gray-50 rounded border border-gray-200 text-xs';
    auditItem.innerHTML = `
        <p class="font-semibold text-gray-800">${patientId.substring(0, 8)}...</p>
        <p class="text-gray-600">${formatAuditType(auditType)}</p>
        <p class="text-gray-500">${new Date().toLocaleTimeString()}</p>
    `;

    // Add to top of list
    recentDiv.insertBefore(auditItem, recentDiv.firstChild);

    // Keep only last 5 audits
    while (recentDiv.children.length > 5) {
        recentDiv.removeChild(recentDiv.lastChild);
    }
}

/**
 * Show notification toast
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    const bgColor = type === 'success' ? 'bg-green-500' : type === 'error' ? 'bg-red-500' : 'bg-blue-500';

    notification.className = `fixed top-4 right-4 ${bgColor} text-white px-6 py-3 rounded-lg shadow-lg z-50 animate-fade-in`;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 4000);
}

/**
 * Format audit type for display
 */
function formatAuditType(auditType) {
    const types = {
        'breast_cancer_screening': 'Breast Cancer Screening',
        'hypertension_compliance': 'Hypertension Compliance',
        'diabetes_management': 'Diabetes Management',
        'general': 'General Audit'
    };
    return types[auditType] || auditType;
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
