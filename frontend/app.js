// Local-AI-RAG Frontend Application
const API_BASE = 'http://localhost:8000';

// State management
const state = {
    sessionId: null,
    firewallEnabled: true,
    scoutEnabled: true,
    ragEnabled: false,
    isLoading: false
};

// DOM elements
const elements = {
    messagesContainer: document.getElementById('messagesContainer'),
    chatForm: document.getElementById('chatForm'),
    messageInput: document.getElementById('messageInput'),
    sendBtn: document.getElementById('sendBtn'),
    firewallToggle: document.getElementById('firewallToggle'),
    scoutToggle: document.getElementById('scoutToggle'),
    ragToggle: document.getElementById('ragToggle'),
    newChatBtn: document.getElementById('newChatBtn'),
    ragManageBtn: document.getElementById('ragManageBtn'),
    ragModal: document.getElementById('ragModal'),
    closeModalBtn: document.getElementById('closeModalBtn'),
    addDocForm: document.getElementById('addDocForm'),
    documentList: document.getElementById('documentList'),
    firewallStatus: document.getElementById('firewallStatus'),
    scoutStatus: document.getElementById('scoutStatus'),
    ragStatus: document.getElementById('ragStatus'),
    sessionInfo: document.getElementById('sessionInfo'),
    systemStatus: document.getElementById('systemStatus'),
    messageCount: document.getElementById('messageCount'),
    docCount: document.getElementById('docCount'),
    firewallBlocks: document.getElementById('firewallBlocks')
};

// Initialize application
async function init() {
    setupEventListeners();
    await checkHealth();
    await updateStats();
    updateStatusIndicators();
    
    // Start new session
    state.sessionId = generateSessionId();
    elements.sessionInfo.textContent = `Session: ${state.sessionId.substring(0, 8)}...`;
}

// Event listeners
function setupEventListeners() {
    // Chat form
    elements.chatForm.addEventListener('submit', handleSendMessage);
    
    // Toggles
    elements.firewallToggle.addEventListener('change', (e) => {
        state.firewallEnabled = e.target.checked;
        updateStatusIndicators();
    });
    
    elements.scoutToggle.addEventListener('change', (e) => {
        state.scoutEnabled = e.target.checked;
        updateStatusIndicators();
    });
    
    elements.ragToggle.addEventListener('change', (e) => {
        state.ragEnabled = e.target.checked;
        updateStatusIndicators();
    });
    
    // Buttons
    elements.newChatBtn.addEventListener('click', startNewChat);
    elements.ragManageBtn.addEventListener('click', openRagModal);
    elements.closeModalBtn.addEventListener('click', closeRagModal);
    elements.addDocForm.addEventListener('submit', handleAddDocument);
}

// Generate session ID
function generateSessionId() {
    return 'session_' + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
}

// Check API health
async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();
        
        if (data.status === 'healthy') {
            elements.systemStatus.textContent = '✓ Online';
            elements.systemStatus.classList.add('text-cato-orange-400');
            elements.systemStatus.classList.remove('text-red-400', 'text-yellow-400');
        } else {
            elements.systemStatus.textContent = '⚠ Degraded';
            elements.systemStatus.classList.add('text-yellow-400');
            elements.systemStatus.classList.remove('text-cato-orange-400', 'text-red-400');
        }
    } catch (error) {
        elements.systemStatus.textContent = '✗ Offline';
        elements.systemStatus.classList.add('text-red-400');
        elements.systemStatus.classList.remove('text-cato-orange-400', 'text-yellow-400');
        console.error('Health check failed:', error);
    }
}

// Update statistics
async function updateStats() {
    try {
        const response = await fetch(`${API_BASE}/api/stats`);
        const data = await response.json();
        
        elements.messageCount.textContent = data.database.total_messages || 0;
        elements.docCount.textContent = data.database.total_documents || 0;
        elements.firewallBlocks.textContent = data.database.firewall_blocks || 0;
    } catch (error) {
        console.error('Failed to update stats:', error);
    }
}

// Update status indicators
function updateStatusIndicators() {
    elements.firewallStatus.classList.toggle('hidden', !state.firewallEnabled);
    elements.scoutStatus.classList.toggle('hidden', !state.scoutEnabled);
    elements.ragStatus.classList.toggle('hidden', !state.ragEnabled);
}

// Handle send message
async function handleSendMessage(e) {
    e.preventDefault();
    
    if (state.isLoading) return;
    
    const message = elements.messageInput.value.trim();
    if (!message) return;
    
    // Add user message to UI
    addMessage('user', message);
    elements.messageInput.value = '';
    
    // Set loading state
    state.isLoading = true;
    elements.sendBtn.disabled = true;
    elements.sendBtn.innerHTML = '<span>Thinking...</span>';
    
    try {
        const response = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                session_id: state.sessionId,
                use_rag: state.ragEnabled,
                stream: false,
                temperature: 0.7
            })
        });
        
        const data = await response.json();
        
        // Add assistant response
        addMessage('assistant', data.response, {
            firewallPassed: data.firewall_passed,
            scoutTriggered: data.scout_triggered,
            ragUsed: data.rag_used,
            searchResults: data.search_results,
            retrievedDocs: data.retrieved_docs
        });
        
        // Update stats
        await updateStats();
        
    } catch (error) {
        console.error('Chat error:', error);
        addMessage('error', 'Sorry, I encountered an error. Please try again.');
    } finally {
        // Reset loading state
        state.isLoading = false;
        elements.sendBtn.disabled = false;
        elements.sendBtn.innerHTML = `
            <span>Send</span>
            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z"/>
            </svg>
        `;
    }
}

// Add message to chat
function addMessage(role, content, metadata = {}) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'flex gap-3 animate-fadeIn';
    
    const isUser = role === 'user';
    const isError = role === 'error';
    
    const avatarColor = isUser 
        ? 'bg-gradient-to-br from-cato-orange-600 to-cato-orange-700 shadow-cato-orange-500/50' 
        : isError 
        ? 'bg-gradient-to-br from-red-600 to-red-700' 
        : 'bg-gradient-to-br from-cato-blue-500 to-cato-orange-500 shadow-cato-blue-500/50';
    
    const bgColor = isUser 
        ? 'bg-gradient-to-br from-cato-orange-900/40 to-cato-orange-800/30 border-cato-orange-700/30' 
        : 'bg-gradient-to-br from-gray-800/80 to-cato-blue-900/30 border-cato-blue-700/30';
    
    const nameColor = isUser
        ? 'bg-gradient-to-r from-cato-orange-400 to-cato-orange-500 bg-clip-text text-transparent'
        : 'bg-gradient-to-r from-cato-blue-400 to-cato-orange-400 bg-clip-text text-transparent';
    
    let badgesHtml = '';
    if (metadata.scoutTriggered) {
        badgesHtml += '<span class="inline-flex items-center gap-1 px-2 py-1 bg-cato-blue-900/40 text-cato-blue-300 rounded border border-cato-blue-700/30 text-xs font-semibold">🔍 Scout</span> ';
    }
    if (metadata.ragUsed) {
        badgesHtml += '<span class="inline-flex items-center gap-1 px-2 py-1 bg-cato-orange-900/40 text-cato-orange-300 rounded border border-cato-orange-700/30 text-xs font-semibold">📚 RAG</span>';
    }
    
    let extraContent = '';
    
    // Add search results if present
    if (metadata.searchResults && metadata.searchResults.length > 0) {
        extraContent += '<div class="mt-3 p-3 bg-cato-blue-900/20 rounded-lg border border-cato-blue-700/30 text-sm"><p class="font-semibold text-cato-blue-300 mb-2">🔍 Search Results:</p><ul class="space-y-2">';
        metadata.searchResults.slice(0, 3).forEach(result => {
            if (!result.error) {
                extraContent += `<li><a href="${result.link}" target="_blank" class="text-cato-blue-400 hover:text-cato-orange-400 transition-colors underline">${result.title}</a><p class="text-gray-400 text-xs mt-1">${result.snippet}</p></li>`;
            }
        });
        extraContent += '</ul></div>';
    }
    
    // Add retrieved documents if present
    if (metadata.retrievedDocs && metadata.retrievedDocs.length > 0) {
        extraContent += '<div class="mt-3 p-3 bg-cato-orange-900/20 rounded-lg border border-cato-orange-700/30 text-sm"><p class="font-semibold text-cato-orange-300 mb-2">📚 Retrieved Documents:</p><ul class="space-y-1">';
        metadata.retrievedDocs.slice(0, 3).forEach(doc => {
            extraContent += `<li class="text-gray-300 text-xs">📄 ${doc.title} <span class="text-cato-orange-400">(${(doc.similarity * 100).toFixed(0)}% match)</span></li>`;
        });
        extraContent += '</ul></div>';
    }
    
    messageDiv.innerHTML = `
        <div class="flex-shrink-0 w-10 h-10 rounded-xl ${avatarColor} flex items-center justify-center shadow-lg relative">
            <div class="absolute inset-0 ${isUser ? 'bg-cato-orange-500' : 'bg-cato-blue-500'} blur-lg opacity-20"></div>
            <span class="text-xl relative z-10">${isUser ? '👤' : '🤖'}</span>
        </div>
        <div class="flex-1 ${bgColor} backdrop-blur-sm rounded-xl p-5 border shadow-lg">
            <p class="text-sm font-bold ${nameColor} mb-2">${isUser ? 'You' : 'AI Assistant'}</p>
            ${badgesHtml ? `<div class="mb-2 flex gap-2">${badgesHtml}</div>` : ''}
            <p class="text-gray-200 leading-relaxed whitespace-pre-wrap">${escapeHtml(content)}</p>
            ${extraContent}
        </div>
    `;
    
    elements.messagesContainer.appendChild(messageDiv);
    elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Start new chat
function startNewChat() {
    if (confirm('Start a new chat session? Current conversation will be cleared.')) {
        state.sessionId = generateSessionId();
        elements.sessionInfo.textContent = `Session: ${state.sessionId.substring(0, 8)}...`;
        
        // Clear messages except welcome
        const messages = elements.messagesContainer.children;
        while (messages.length > 1) {
            messages[1].remove();
        }
    }
}

// RAG Modal functions
async function openRagModal() {
    elements.ragModal.classList.remove('hidden');
    await loadDocuments();
}

function closeRagModal() {
    elements.ragModal.classList.add('hidden');
}

// Load documents
async function loadDocuments() {
    try {
        const response = await fetch(`${API_BASE}/api/rag/documents`);
        const data = await response.json();
        
        elements.documentList.innerHTML = '';
        
        if (data.documents.length === 0) {
            elements.documentList.innerHTML = '<p class="text-gray-400 text-sm text-center py-4">No documents yet</p>';
            return;
        }
        
        data.documents.forEach(doc => {
            const docDiv = document.createElement('div');
            docDiv.className = 'bg-gray-700 rounded p-3 flex justify-between items-center';
            docDiv.innerHTML = `
                <div class="flex-1">
                    <p class="font-medium text-sm">${escapeHtml(doc.title || 'Untitled')}</p>
                    <p class="text-xs text-gray-400">${escapeHtml(doc.content.substring(0, 80))}...</p>
                </div>
                <button onclick="deleteDocument('${doc.doc_id}')" class="text-red-400 hover:text-red-300 ml-2">
                    <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"/>
                    </svg>
                </button>
            `;
            elements.documentList.appendChild(docDiv);
        });
    } catch (error) {
        console.error('Failed to load documents:', error);
        elements.documentList.innerHTML = '<p class="text-red-400 text-sm text-center py-4">Error loading documents</p>';
    }
}

// Handle add document
async function handleAddDocument(e) {
    e.preventDefault();
    
    const title = document.getElementById('docTitle').value.trim();
    const content = document.getElementById('docContent').value.trim();
    
    if (!content) {
        alert('Please enter document content');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/rag/ingest`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: title || 'Untitled Document',
                content: content
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(`Document added successfully! Created ${data.chunks_created} chunks.`);
            document.getElementById('docTitle').value = '';
            document.getElementById('docContent').value = '';
            await loadDocuments();
            await updateStats();
        } else {
            alert('Failed to add document: ' + data.error);
        }
    } catch (error) {
        console.error('Failed to add document:', error);
        alert('Error adding document');
    }
}

// Delete document
async function deleteDocument(docId) {
    if (!confirm('Delete this document?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/rag/documents/${docId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            await loadDocuments();
            await updateStats();
        } else {
            alert('Failed to delete document');
        }
    } catch (error) {
        console.error('Failed to delete document:', error);
        alert('Error deleting document');
    }
}

// Make deleteDocument available globally
window.deleteDocument = deleteDocument;

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
