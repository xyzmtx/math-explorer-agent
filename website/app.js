/**
 * Math Explorer Agent - Visualization App
 * Main JavaScript application with interactive exploration support
 */

// ================================
// Configuration
// ================================
const API_BASE = window.location.origin;

// ================================
// State Management
// ================================
let memoryData = null;
let currentTab = 'objects';
let isExplorationActive = false;
let isRunning = false;
let eventSource = null;

// ================================
// DOM Elements
// ================================
const elements = {
    fileInput: () => document.getElementById('file-input'),
    loadingOverlay: () => document.getElementById('loading-overlay'),
    loadingText: () => document.getElementById('loading-text'),
    statsObjects: () => document.getElementById('stat-objects'),
    statsConcepts: () => document.getElementById('stat-concepts'),
    statsDirections: () => document.getElementById('stat-directions'),
    statsConjectures: () => document.getElementById('stat-conjectures'),
    statsLemmas: () => document.getElementById('stat-lemmas'),
    objectsGrid: () => document.getElementById('objects-grid'),
    conceptsGrid: () => document.getElementById('concepts-grid'),
    directionsGrid: () => document.getElementById('directions-grid'),
    conjecturesGrid: () => document.getElementById('conjectures-grid'),
    lemmasGrid: () => document.getElementById('lemmas-grid'),
    exploreModal: () => document.getElementById('explore-modal'),
    mathInput: () => document.getElementById('math-input'),
    statusBar: () => document.getElementById('status-bar'),
    statusDot: () => document.querySelector('.status-dot'),
    statusText: () => document.getElementById('status-text'),
    activityLog: () => document.getElementById('activity-log'),
    logContent: () => document.getElementById('log-content'),
    btnRun: () => document.getElementById('btn-run'),
    btnRun5: () => document.getElementById('btn-run-5'),
    btnStop: () => document.getElementById('btn-stop'),
};

// ================================
// Initialization
// ================================
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    checkServerStatus();
    loadSampleData();
});

function initializeEventListeners() {
    // File upload
    const fileInput = elements.fileInput();
    if (fileInput) {
        fileInput.addEventListener('change', handleFileUpload);
    }

    // Tab navigation
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            switchTab(btn.dataset.tab);
        });
    });

    // Close modal on escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeExploreModal();
        }
    });
}

// ================================
// Server Communication
// ================================
async function checkServerStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/status`);
        if (response.ok) {
            const data = await response.json();
            if (data.initialized) {
                activateExplorationMode();
                if (data.memory_summary) {
                    updateStatsFromSummary(data.memory_summary);
                }
                // Fetch full memory
                await refreshMemory();
            }
        }
    } catch (error) {
        console.log('Server not available, running in static mode');
    }
}

async function refreshMemory() {
    try {
        const response = await fetch(`${API_BASE}/api/memory`);
        if (response.ok) {
            memoryData = await response.json();
            renderAllData();
        }
    } catch (error) {
        console.error('Failed to refresh memory:', error);
    }
}

// ================================
// Exploration Modal
// ================================
function openExploreModal() {
    const modal = elements.exploreModal();
    if (modal) {
        modal.classList.add('active');
        elements.mathInput()?.focus();
    }
}

function closeExploreModal() {
    const modal = elements.exploreModal();
    if (modal) {
        modal.classList.remove('active');
    }
}

// ================================
// Exploration Control
// ================================
async function startExploration() {
    const mathInput = elements.mathInput();
    const text = mathInput?.value?.trim();

    if (!text) {
        alert('Please enter a mathematical problem or topic to explore.');
        return;
    }

    showLoading(true, 'Initializing exploration...');
    closeExploreModal();

    try {
        const response = await fetch(`${API_BASE}/api/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });

        const data = await response.json();

        if (data.success) {
            memoryData = data.memory;
            activateExplorationMode();
            renderAllData();
            addLogEntry('Exploration initialized successfully', 'action-complete');
            connectSSE();
        } else {
            alert('Error: ' + (data.error || 'Failed to start exploration'));
        }
    } catch (error) {
        console.error('Failed to start exploration:', error);
        alert('Failed to connect to server. Make sure server.py is running.');
    } finally {
        showLoading(false);
    }
}

async function runExploration(rounds = 1) {
    if (isRunning) return;

    setRunningState(true);
    addLogEntry(`Starting ${rounds} exploration round(s)...`, 'round-start');

    try {
        const response = await fetch(`${API_BASE}/api/run`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ rounds })
        });

        const data = await response.json();

        if (!data.success) {
            addLogEntry('Error: ' + (data.error || 'Failed to run exploration'), 'action-error');
            setRunningState(false);
        }
    } catch (error) {
        console.error('Failed to run exploration:', error);
        addLogEntry('Connection error: ' + error.message, 'action-error');
        setRunningState(false);
    }
}

async function stopExploration() {
    try {
        await fetch(`${API_BASE}/api/stop`, { method: 'POST' });
        addLogEntry('Stop requested...', 'action-error');
    } catch (error) {
        console.error('Failed to stop:', error);
    }
}

function activateExplorationMode() {
    isExplorationActive = true;

    elements.statusBar()?.classList.add('active');
    elements.activityLog()?.classList.add('active');
    elements.statusDot()?.classList.add('ready');

    updateStatus('Ready', 'ready');
    updateRunButtons(true);
}

function setRunningState(running) {
    isRunning = running;

    if (running) {
        updateStatus('Running...', 'running');
    } else {
        updateStatus('Ready', 'ready');
    }

    updateRunButtons(!running);

    const btnStop = elements.btnStop();
    if (btnStop) btnStop.disabled = !running;
}

function updateStatus(text, state) {
    const statusText = elements.statusText();
    const statusDot = elements.statusDot();

    if (statusText) statusText.textContent = text;
    if (statusDot) {
        statusDot.classList.remove('ready', 'running', 'error');
        statusDot.classList.add(state);
    }
}

function updateRunButtons(enabled) {
    const btnRun = elements.btnRun();
    const btnRun5 = elements.btnRun5();

    if (btnRun) btnRun.disabled = !enabled;
    if (btnRun5) btnRun5.disabled = !enabled;
}

// ================================
// Server-Sent Events (SSE)
// ================================
function connectSSE() {
    if (eventSource) {
        eventSource.close();
    }

    eventSource = new EventSource(`${API_BASE}/api/stream`);

    eventSource.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            handleSSEEvent(data);
        } catch (error) {
            console.error('SSE parse error:', error);
        }
    };

    eventSource.onerror = (error) => {
        console.error('SSE error:', error);
        // Reconnect after delay
        setTimeout(connectSSE, 5000);
    };
}

function handleSSEEvent(event) {
    switch (event.type) {
        case 'action_start':
            addLogEntry(`▶ ${event.data.action_type} started`, 'action-start');
            break;

        case 'action_complete':
            addLogEntry(`✓ ${event.data.action_type} completed`, 'action-complete');
            break;

        case 'action_error':
            addLogEntry(`✗ Error: ${event.data.error}`, 'action-error');
            break;

        case 'round_start':
            addLogEntry(`━━━ Round ${event.data.round} (${event.data.actions_count} actions) ━━━`, 'round-start');
            break;

        case 'round_complete':
            addLogEntry(`Round ${event.data.round} complete`, 'action-complete');
            // Refresh memory after each round
            refreshMemory();
            break;

        case 'exploration_complete':
            addLogEntry('✓ Exploration completed', 'action-complete');
            setRunningState(false);
            refreshMemory();
            break;

        case 'exploration_error':
            addLogEntry(`✗ Exploration error: ${event.data.error}`, 'action-error');
            setRunningState(false);
            break;

        case 'memory_saved':
            addLogEntry(`Memory saved: ${event.data.path}`, 'action-complete');
            break;

        case 'initialized':
            addLogEntry('Memory initialized', 'action-complete');
            if (event.data.memory) {
                memoryData = event.data.memory;
                renderAllData();
            }
            break;

        case 'keepalive':
            // Ignore keepalive
            break;

        default:
            console.log('Unknown SSE event:', event);
    }
}

// ================================
// Activity Log
// ================================
function addLogEntry(message, className = '') {
    const logContent = elements.logContent();
    if (!logContent) return;

    const entry = document.createElement('div');
    entry.className = `log-entry ${className}`;
    entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;

    logContent.insertBefore(entry, logContent.firstChild);

    // Limit log entries
    while (logContent.children.length > 100) {
        logContent.removeChild(logContent.lastChild);
    }
}

function toggleActivityLog() {
    const logContent = elements.logContent();
    if (logContent) {
        logContent.style.display = logContent.style.display === 'none' ? 'block' : 'none';
    }
}

// ================================
// File Handling
// ================================
async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    showLoading(true, 'Loading file...');

    try {
        const text = await file.text();
        const data = JSON.parse(text);
        memoryData = data;
        renderAllData();
    } catch (error) {
        console.error('Error loading file:', error);
        alert('Failed to load file. Please ensure it is a valid JSON file.');
    } finally {
        showLoading(false);
    }
}

async function loadSampleData() {
    try {
        // Try to load the latest memory snapshot from root directory
        const response = await fetch('/memory_snapshots/memory_verify_20251230_033111.json');
        if (response.ok) {
            memoryData = await response.json();
            renderAllData();
        } else {
            // Show empty state
            renderEmptyState();
        }
    } catch (error) {
        console.log('No sample data loaded, showing empty state');
        renderEmptyState();
    }
}

// ================================
// Rendering Functions
// ================================
function renderAllData() {
    if (!memoryData) return;

    // Update statistics
    updateStats();

    // Render each section
    renderObjects();
    renderConcepts();
    renderDirections();
    renderConjectures();
    renderLemmas();

    // Trigger KaTeX rendering
    setTimeout(renderMathContent, 100);
}

function updateStats() {
    if (!memoryData) return;

    elements.statsObjects().textContent = memoryData.objects?.length || 0;
    elements.statsConcepts().textContent = memoryData.concepts?.length || 0;
    elements.statsDirections().textContent = memoryData.directions?.length || 0;
    elements.statsConjectures().textContent = memoryData.conjectures?.length || 0;
    elements.statsLemmas().textContent = memoryData.lemmas?.length || 0;
}

function updateStatsFromSummary(summary) {
    elements.statsObjects().textContent = summary.objects || 0;
    elements.statsConcepts().textContent = summary.concepts || 0;
    elements.statsDirections().textContent = summary.directions || 0;
    elements.statsConjectures().textContent = summary.conjectures || 0;
    elements.statsLemmas().textContent = summary.lemmas || 0;
}

function renderObjects() {
    const grid = elements.objectsGrid();
    if (!grid || !memoryData.objects) return;

    grid.innerHTML = memoryData.objects.map(obj => `
        <div class="entity-card object">
            <div class="card-header">
                <span class="card-id">${escapeHtml(obj.id)}</span>
                <h3 class="card-title">${obj.name}</h3>
            </div>
            <div class="card-content">
                <div class="card-field">
                    <span class="field-label">Type & Definition</span>
                    <div class="field-value math-content">${escapeHtml(obj.type_and_definition)}</div>
                </div>
                ${obj.comment ? `
                <div class="card-field">
                    <span class="field-label">Comment</span>
                    <div class="field-value">${escapeHtml(obj.comment)}</div>
                </div>
                ` : ''}
            </div>
        </div>
    `).join('');
}

function renderConcepts() {
    const grid = elements.conceptsGrid();
    if (!grid || !memoryData.concepts) return;

    grid.innerHTML = memoryData.concepts.map(concept => `
        <div class="entity-card concept">
            <div class="card-header">
                <span class="card-id">${escapeHtml(concept.id)}</span>
                <h3 class="card-title">${escapeHtml(concept.name)}</h3>
            </div>
            <div class="card-content">
                <div class="card-field">
                    <span class="field-label">Definition</span>
                    <div class="field-value math-content">${escapeHtml(concept.definition)}</div>
                </div>
                ${concept.comment ? `
                <div class="card-field">
                    <span class="field-label">Comment</span>
                    <div class="field-value">${escapeHtml(concept.comment)}</div>
                </div>
                ` : ''}
            </div>
        </div>
    `).join('');
}

function renderDirections() {
    const grid = elements.directionsGrid();
    if (!grid || !memoryData.directions) return;

    grid.innerHTML = memoryData.directions.map(dir => `
        <div class="entity-card direction">
            <div class="card-header">
                <span class="card-id">${escapeHtml(dir.id)}</span>
                ${dir.completely_solved ? '<span class="card-badge badge-solved">✓ Solved</span>' : ''}
            </div>
            <div class="card-content">
                <div class="card-field">
                    <span class="field-label">Description</span>
                    <div class="field-value math-content">${escapeHtml(dir.description)}</div>
                </div>
                ${dir.comment ? `
                <div class="card-field">
                    <span class="field-label">Comment</span>
                    <div class="field-value">${escapeHtml(dir.comment)}</div>
                </div>
                ` : ''}
            </div>
        </div>
    `).join('');
}

function renderConjectures() {
    const grid = elements.conjecturesGrid();
    if (!grid || !memoryData.conjectures) return;

    grid.innerHTML = memoryData.conjectures.map(conj => {
        const confidenceClass = getConfidenceBadgeClass(conj.confidence_score);
        return `
            <div class="entity-card conjecture">
                <div class="card-header">
                    <span class="card-id">${escapeHtml(conj.id)}</span>
                    <div style="display: flex; gap: 0.5rem;">
                        <span class="card-badge ${confidenceClass}">${escapeHtml(conj.confidence_score || 'Medium')}</span>
                        ${conj.completely_solved ? '<span class="card-badge badge-solved">✓ Solved</span>' : ''}
                    </div>
                </div>
                <div class="card-content">
                    <div class="card-field">
                        <span class="field-label">Statement</span>
                        <div class="field-value math-content">${escapeHtml(conj.statement)}</div>
                    </div>
                    ${conj.comment ? `
                    <div class="card-field">
                        <span class="field-label">Comment</span>
                        <div class="field-value">${escapeHtml(conj.comment)}</div>
                    </div>
                    ` : ''}
                </div>
            </div>
        `;
    }).join('');
}

function renderLemmas() {
    const grid = elements.lemmasGrid();
    if (!grid || !memoryData.lemmas) return;

    grid.innerHTML = memoryData.lemmas.map(lemma => `
        <div class="entity-card lemma">
            <div class="card-header">
                <span class="card-id">${escapeHtml(lemma.id)}</span>
                <span class="card-badge badge-solved">✓ Proven</span>
            </div>
            <div class="card-content">
                <div class="card-field">
                    <span class="field-label">Statement</span>
                    <div class="field-value math-content">${escapeHtml(lemma.statement)}</div>
                </div>
                ${lemma.proof ? `
                <div class="card-field">
                    <span class="field-label">Proof</span>
                    <div class="proof-content">${escapeHtml(lemma.proof)}</div>
                </div>
                ` : ''}
            </div>
        </div>
    `).join('');
}

function renderEmptyState() {
    const grids = [
        elements.objectsGrid(),
        elements.conceptsGrid(),
        elements.directionsGrid(),
        elements.conjecturesGrid(),
        elements.lemmasGrid()
    ];

    grids.forEach(grid => {
        if (grid) {
            grid.innerHTML = `
                <div class="empty-state" style="grid-column: 1 / -1;">
                    <div class="empty-state-icon">🔬</div>
                    <p>No data yet. Click "Start Exploration" to begin mathematical exploration.</p>
                </div>
            `;
        }
    });
}

// ================================
// KaTeX Rendering
// ================================
function renderMathContent() {
    if (typeof renderMathInElement !== 'undefined') {
        renderMathInElement(document.body, {
            delimiters: [
                { left: '$$', right: '$$', display: true },
                { left: '$', right: '$', display: false },
                { left: '\\[', right: '\\]', display: true },
                { left: '\\(', right: '\\)', display: false }
            ],
            throwOnError: false,
            trust: true,
            strict: false
        });
    }
}

// ================================
// Tab Navigation
// ================================
function switchTab(tabName) {
    currentTab = tabName;

    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });

    // Update sections
    document.querySelectorAll('.section').forEach(section => {
        section.classList.toggle('active', section.id === `${tabName}-section`);
    });

    // Re-render math content for the new section
    setTimeout(renderMathContent, 100);
}

// ================================
// Utility Functions
// ================================
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getConfidenceBadgeClass(confidence) {
    switch (confidence?.toLowerCase()) {
        case 'high':
        case '高':
            return 'badge-confidence-high';
        case 'low':
        case '低':
            return 'badge-confidence-low';
        default:
            return 'badge-confidence-medium';
    }
}

function showLoading(show, text = 'Loading...') {
    const overlay = elements.loadingOverlay();
    const loadingText = elements.loadingText();

    if (overlay) {
        overlay.classList.toggle('active', show);
    }
    if (loadingText) {
        loadingText.textContent = text;
    }
}
