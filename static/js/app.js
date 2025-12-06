// Inwebstigate Frontend JavaScript

// State
let socket;
let isInvestigating = false;
let currentStep = 0;

// DOM Elements
const queryInput = document.getElementById('query');
const startUrlInput = document.getElementById('start-url');
const maxDepthInput = document.getElementById('max-depth');
const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');
const progressContainer = document.getElementById('progress-container');
const progressText = document.getElementById('progress-text');
const progressBarFill = document.getElementById('progress-bar-fill');
const navLogContent = document.getElementById('nav-log-content');
const pathTableBody = document.getElementById('path-table-body');
const answerContent = document.getElementById('answer-content');
const statusText = document.getElementById('status-text');
const pagesVisited = document.getElementById('pages-visited');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initSocketIO();
    initTabs();
    initEventListeners();
    loadConfig();
});

// Socket.IO Setup
function initSocketIO() {
    socket = io();

    socket.on('connect', () => {
        console.log('Connected to server');
        updateStatus('Connected | Ready');
    });

    socket.on('connected', (data) => {
        console.log(data.message);
    });

    socket.on('investigation_started', (data) => {
        isInvestigating = true;
        currentStep = 0;
        startBtn.disabled = true;
        stopBtn.disabled = false;
        progressContainer.style.display = 'block';
        progressBarFill.style.width = '100%';
        
        // Clear ALL previous results and state
        navLogContent.innerHTML = '';
        pathTableBody.innerHTML = '<tr><td colspan="3" class="empty-state">Investigation starting...</td></tr>';
        answerContent.innerHTML = '<div class="empty-state">Investigation in progress...</div>';
        updatePagesVisited(0);
        updateStatus('Investigating...');
        
        addLogEntry(`🚀 Starting investigation: ${data.query}`, 'header');
        addLogEntry(`📊 Maximum pages to visit: ${data.max_depth || 5}`, 'info');
    });

    socket.on('progress_update', (data) => {
        handleProgressUpdate(data);
    });

    socket.on('investigation_complete', (data) => {
        handleInvestigationComplete(data);
    });

    socket.on('investigation_stopped', (data) => {
        isInvestigating = false;
        startBtn.disabled = false;
        stopBtn.disabled = true;
        progressContainer.style.display = 'none';
        addLogEntry(`\n⏹ ${data.message}`, 'warning');
        
        // If there's a summary, display it
        if (data.summary) {
            addLogEntry(`\n📊 Investigation Summary:`, 'info');
            addLogEntry(`   Pages visited: ${data.summary.total_pages_visited}`, 'info');
            
            // Generate partial answer if we have findings
            if (data.summary.investigation_log && data.summary.investigation_log.length > 0) {
                let partialAnswer = "Investigation was stopped. Here's what was found:\n\n";
                data.summary.investigation_log.forEach((page, i) => {
                    partialAnswer += `${i + 1}. From ${page.url}:\n${page.findings}\n\n`;
                });
                displayFinalAnswer(partialAnswer);
                document.querySelector('[data-tab="final-answer"]').click();
            }
        }
        
        updateStatus('Investigation stopped');
    });

    socket.on('error', (data) => {
        addLogEntry(`❌ Error: ${data.message}`, 'error');
        isInvestigating = false;
        startBtn.disabled = false;
        stopBtn.disabled = true;
        progressContainer.style.display = 'none';
        updateStatus('Error occurred');
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        updateStatus('Disconnected');
    });
}

// Event Listeners
function initEventListeners() {
    startBtn.addEventListener('click', startInvestigation);
    stopBtn.addEventListener('click', stopInvestigation);
    
    // Enter key to start
    queryInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !isInvestigating) {
            startInvestigation();
        }
    });
}

// Tab System
function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.getAttribute('data-tab');
            
            // Remove active class from all
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            // Add active to clicked
            btn.classList.add('active');
            document.getElementById(tabName).classList.add('active');
        });
    });
}

// Load Configuration
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        const config = await response.json();
        
        // Set LLM provider radio
        if (config.llm_provider === 'groq') {
            document.getElementById('groq-radio').checked = true;
        } else {
            document.getElementById('ollama-radio').checked = true;
        }
        
        // Set max depth
        maxDepthInput.value = config.max_depth;
        
        // Update status
        const modelName = config.llm_provider === 'ollama' ? config.ollama_model : config.groq_model;
        updateStatus(`Ready | LLM: ${config.llm_provider.toUpperCase()} (${modelName})`);
        
        // Disable Groq if no API key
        if (!config.has_groq_key) {
            document.getElementById('groq-radio').disabled = true;
            document.getElementById('groq-radio').parentElement.title = 'Groq API key not configured';
        }
    } catch (error) {
        console.error('Error loading config:', error);
    }
}

// Start Investigation
function startInvestigation() {
    const query = queryInput.value.trim();
    
    if (!query) {
        alert('Please enter a query to investigate');
        return;
    }
    
    const maxDepth = parseInt(maxDepthInput.value);
    
    // Validate max depth
    if (maxDepth < 1 || maxDepth > 10) {
        alert('Maximum pages must be between 1 and 10');
        return;
    }
    
    const data = {
        query: query,
        start_url: startUrlInput.value.trim(),
        llm_provider: document.querySelector('input[name="llm"]:checked').value,
        max_depth: maxDepth
    };
    
    console.log('Starting investigation with:', data);
    socket.emit('start_investigation', data);
}

// Stop Investigation
function stopInvestigation() {
    if (confirm('Are you sure you want to stop the investigation?')) {
        socket.emit('stop_investigation');
    }
}

// Handle Progress Updates
function handleProgressUpdate(data) {
    const { message, data: updateData } = data;
    
    // Update progress text
    progressText.textContent = message;
    
    if (!updateData) {
        addLogEntry(message, 'info');
        return;
    }
    
    const type = updateData.type;
    
    switch (type) {
        case 'navigation':
            currentStep++;
            addLogEntry(`\n${'='.repeat(80)}`, 'header');
            addLogEntry(`Step ${updateData.depth}/${updateData.max_depth}: Navigating to...`, 'header');
            addLogEntry(updateData.url, 'url');
            updatePagesVisited(currentStep);
            break;
            
        case 'page_loaded':
            addLogEntry(`✅ Page loaded: ${updateData.title}`, 'success');
            addLogEntry(`   Found ${updateData.links_found} links`, 'info');
            break;
            
        case 'analyzing':
            addLogEntry('🤖 Analyzing page content with AI...', 'info');
            break;
            
        case 'findings':
            addLogEntry('\n📝 Findings:', 'finding');
            addLogEntry(updateData.findings, 'finding');
            
            // Add to path table
            addToPathTable(currentStep, updateData.url, updateData.findings);
            break;
            
        case 'deciding':
            addLogEntry('\n🤔 Deciding next navigation step...', 'decision');
            break;
            
        case 'next_link':
            addLogEntry('\n➡️  Next Link:', 'decision');
            addLogEntry(updateData.url, 'url');
            addLogEntry(`💡 Reason: ${updateData.reason}`, 'decision');
            break;
            
        case 'stop':
            addLogEntry(`\n🛑 Stopping: ${updateData.reason}`, 'warning');
            break;
            
        case 'error':
            addLogEntry(`❌ Error: ${updateData.error}`, 'error');
            break;
            
        case 'final_answer':
            addLogEntry('\n📊 Generating final answer...', 'info');
            break;
            
        case 'complete':
            addLogEntry(`\n✨ Investigation complete! Pages visited: ${updateData.pages_visited}`, 'success');
            break;
    }
    
    // Auto-scroll to bottom
    navLogContent.scrollTop = navLogContent.scrollHeight;
}

// Handle Investigation Complete
function handleInvestigationComplete(data) {
    isInvestigating = false;
    startBtn.disabled = false;
    stopBtn.disabled = true;
    progressContainer.style.display = 'none';
    
    // Display final answer
    displayFinalAnswer(data.final_answer);
    
    // Update status
    updateStatus(`Complete | Pages visited: ${data.summary.total_pages_visited}`);
    updatePagesVisited(data.summary.total_pages_visited);
    
    // Switch to final answer tab
    document.querySelector('[data-tab="final-answer"]').click();
}

// Add Log Entry
function addLogEntry(text, type = 'info') {
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    entry.textContent = text;
    navLogContent.appendChild(entry);
}

// Add to Path Table
function addToPathTable(step, url, findings) {
    // Remove empty state if exists
    const emptyState = pathTableBody.querySelector('.empty-state');
    if (emptyState) {
        pathTableBody.innerHTML = '';
    }
    
    const row = document.createElement('tr');
    row.innerHTML = `
        <td><strong>Step ${step}</strong></td>
        <td><a href="${url}" target="_blank" style="color: #667eea; text-decoration: none;">${truncate(url, 50)}</a></td>
        <td>${truncate(findings, 100)}</td>
    `;
    pathTableBody.appendChild(row);
}

// Display Final Answer
function displayFinalAnswer(answer) {
    // Format the answer with basic markdown-like formatting
    const formatted = answer
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    answerContent.innerHTML = `<p>${formatted}</p>`;
}

// Update Status
function updateStatus(text) {
    statusText.textContent = text;
}

// Update Pages Visited
function updatePagesVisited(count) {
    pagesVisited.textContent = `Pages Visited: ${count}`;
}

// Helper: Truncate Text
function truncate(text, length) {
    if (text.length <= length) return text;
    return text.substring(0, length) + '...';
}

