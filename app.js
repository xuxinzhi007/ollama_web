// ==========================================
// 核心状态与全局函数定义 (UI 交互优先定义)
// ==========================================
const API_BASE = 'http://localhost:11434';
let chatHistory = [];
let currentAgent = null; 
let agents = []; 
let baseModels = []; 
let editingAgent = null; 
let isPulling = false; 

// 将 UI 控制函数挂载到 window，确保第一时间可用
window.toggleManagePanel = function() {
    const panel = document.getElementById('managePanel');
    if (panel) panel.style.display = 'block';
    renderBaseModelList(); // 打开时刷新列表
};

window.closeManagePanel = function() {
    const panel = document.getElementById('managePanel');
    if (panel) panel.style.display = 'none';
};

window.toggleMobileSidebar = function() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.getElementById('mobileOverlay');
    if (sidebar) sidebar.classList.toggle('open');
    if (overlay) overlay.classList.toggle('show');
};

window.createNewAgent = function() {
    editingAgent = null;
    const title = document.getElementById('editorTitle');
    const nameInput = document.getElementById('agentName');
    const modelSelect = document.getElementById('baseModelSelect');
    const prompt = document.getElementById('systemPrompt');
    const status = document.getElementById('agentStatus');
    const hint = document.getElementById('manualCreateHint');
    
    if (title) title.textContent = '创建智能体';
    if (nameInput) nameInput.value = '';
    if (modelSelect) modelSelect.value = '';
    if (prompt) prompt.value = '';
    if (status) status.innerHTML = '';
    if (hint) hint.style.display = 'none';
    
    resetParams();
    
    const editor = document.getElementById('agentEditor');
    if (editor) editor.style.display = 'flex';
};

window.closeAgentEditor = function() {
    const editor = document.getElementById('agentEditor');
    if (editor) editor.style.display = 'none';
};

window.showStorageInfo = function() {
    const modal = document.getElementById('storageInfoModal');
    if (modal) modal.style.display = 'flex';
    
    // 显示路径信息
    const pathDiv = document.getElementById('defaultStoragePath');
    if (pathDiv) {
        const isWin = navigator.platform.toLowerCase().includes('win');
        pathDiv.innerHTML = isWin 
            ? 'C:\\Users\\<用户名>\\.ollama\\models'
            : '~/.ollama/models';
    }
};

window.closeStorageInfo = function() {
    const modal = document.getElementById('storageInfoModal');
    if (modal) modal.style.display = 'none';
};

// 欢迎页 Tab 切换
window.switchWelcomeTab = function(tab) {
    // 移除所有 active 类
    document.querySelectorAll('.welcome-tab').forEach(t => t.classList.remove('active'));
    
    // 给当前选中的 tab 添加 active 类
    const activeTab = document.querySelector(`.welcome-tab[data-tab="${tab}"]`);
    if (activeTab) activeTab.classList.add('active');
    
    // 切换内容显示
    const quickTab = document.getElementById('quickTab');
    const plazaTab = document.getElementById('plazaTab');
    
    if (quickTab) quickTab.style.display = tab === 'quick' ? 'flex' : 'none';
    if (plazaTab) plazaTab.style.display = tab === 'plaza' ? 'block' : 'none';
    
    if (tab === 'plaza') renderPlazaAgents();
};

// ==========================================
// 业务逻辑函数
// ==========================================

// Toast 通知系统
function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = {
        'success': '<span style="color:#10b981">✓</span>',
        'error': '<span style="color:#ef4444">✕</span>',
        'info': '<span style="color:#3b82f6">ℹ</span>',
        'warning': '<span style="color:#f59e0b">⚠</span>'
    }[type] || 'ℹ';
    
    toast.innerHTML = `
        <div style="font-size: 18px; display: flex; align-items: center;">${icon}</div>
        <div style="flex: 1; font-size: 14px;">${message}</div>
        <button class="toast-close" style="background:none; border:none; color:inherit; cursor:pointer; opacity:0.5;">✕</button>
    `;
    
    container.appendChild(toast);
    
    const closeBtn = toast.querySelector('.toast-close');
    if (closeBtn) {
        closeBtn.onclick = () => removeToast(toast);
    }
    
    if (duration > 0) {
        setTimeout(() => removeToast(toast), duration);
    }
}

function removeToast(toast) {
    if (!toast.parentNode) return;
    toast.style.animation = 'slideOut 0.3s forwards'; // 需要在CSS定义 slideOut
    toast.style.opacity = '0';
    setTimeout(() => {
        if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 300);
}

// 检查是否为底座模型
function isBaseModel(modelName) {
    const baseModelsList = [
        'llama', 'qwen', 'gemma', 'mistral', 'phi', 'deepseek', 
        'codellama', 'vicuna', 'orca', 'nous-hermes', 'dolphin',
        'yi', 'mixtral', 'solar', 'openchat', 'starling', 'neural-chat'
    ];
    const lowerName = modelName.toLowerCase();
    return baseModelsList.some(base => lowerName.startsWith(base));
}

// 检查 Ollama 连接
async function checkOllamaConnection() {
    try {
        const response = await fetch(`${API_BASE}/api/tags`, {
            method: 'GET',
            signal: AbortSignal.timeout(5000)
        });
        return response.ok;
    } catch (error) {
        return false;
    }
}

// 加载所有模型
async function loadModels() {
    try {
        const response = await fetch(`${API_BASE}/api/tags`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        
        baseModels = [];
        agents = [];
        
        // 分类模型
        if (data.models) {
            data.models.forEach(model => {
                if (isBaseModel(model.name)) {
                    baseModels.push(model);
                }
            });
            
            data.models.forEach(model => {
                if (!isBaseModel(model.name)) {
                    let baseModel = 'unknown';
                    for (const base of baseModels) {
                        if (model.name.includes(base.name.split(':')[0])) {
                            baseModel = base.name;
                            break;
                        }
                    }
                    agents.push({
                        name: model.name,
                        displayName: model.name,
                        baseModel: baseModel,
                        modelName: model.name
                    });
                }
            });
        }
        
        renderAgentList();
        renderBaseModelList();
        updateBaseModelSelect();
        
        // 恢复状态检查
        if (currentAgent) {
             const exists = agents.find(a => a.modelName === currentAgent.modelName);
             if (!exists) showWelcomeScreen();
        }
        
    } catch (error) {
        console.error('加载模型失败:', error);
        handleConnectionError();
    }
}

function handleConnectionError() {
    const agentList = document.getElementById('agentList');
    const noAgents = document.getElementById('noAgents');
    
    if (agentList) agentList.innerHTML = '';
    if (noAgents) {
        noAgents.style.display = 'block';
        noAgents.innerHTML = `
            <div style="color: #ef4444; margin-bottom: 10px;">无法连接到 Ollama</div>
            <button onclick="location.reload()" class="primary" style="width:100%; font-size:12px;">重连</button>
        `;
    }
}

// 渲染列表相关函数
function renderAgentList() {
    const agentList = document.getElementById('agentList');
    const noAgents = document.getElementById('noAgents');
    if (!agentList) return;
    
    agentList.innerHTML = '';
    
    if (agents.length === 0) {
        if (noAgents) noAgents.style.display = 'block';
        return;
    }
    
    if (noAgents) noAgents.style.display = 'none';
    
    agents.forEach(agent => {
        const item = document.createElement('div');
        item.className = 'agent-item';
        if (currentAgent && currentAgent.name === agent.name) {
            item.classList.add('active');
        }
        
        item.innerHTML = `
            <div class="agent-avatar">${agent.displayName.charAt(0).toUpperCase()}</div>
            <div class="agent-info" onclick="selectAgentMobile('${agent.modelName}')">
                <div class="agent-name">${agent.displayName}</div>
                <div class="agent-base">${agent.baseModel}</div>
            </div>
            <div class="agent-menu">
                <button class="menu-btn" onclick="toggleAgentMenu(event, '${agent.modelName}')">⋮</button>
            </div>
        `;
        agentList.appendChild(item);
    });
}

function renderBaseModelList() {
    const baseModelList = document.getElementById('baseModelList');
    if (!baseModelList) return;
    
    baseModelList.innerHTML = '';
    
    if (baseModels.length === 0) {
        baseModelList.innerHTML = '<div style="color: var(--text-tertiary); font-size: 13px; padding: 10px;">暂无模型</div>';
        return;
    }
    
    baseModels.forEach(model => {
        const item = document.createElement('div');
        item.style.cssText = 'padding: 12px; margin-bottom: 8px; background: rgba(255,255,255,0.03); border-radius: var(--radius-sm); display: flex; justify-content: space-between; align-items: center; border: 1px solid transparent;';
        
        item.innerHTML = `
            <span style="font-size: 13px; font-family: monospace;">${model.name}</span>
            <button onclick="deleteBaseModel('${model.name}')" style="color: #ef4444; background: transparent; padding: 4px; font-size: 12px; border: none; cursor: pointer;">删除</button>
        `;
        baseModelList.appendChild(item);
    });
}

function updateBaseModelSelect() {
    const select = document.getElementById('baseModelSelect');
    if (!select) return;
    
    select.innerHTML = '<option value="">选择底座模型...</option>';
    baseModels.forEach(model => {
        const option = document.createElement('option');
        option.value = model.name;
        option.textContent = model.name;
        select.appendChild(option);
    });
}

// 智能体选择
function selectAgent(agent) {
    if (currentAgent && chatHistory.length > 0) {
        saveChatHistory();
    }
    
    currentAgent = agent;
    const nameEl = document.getElementById('currentAgentName');
    if (nameEl) nameEl.textContent = agent.displayName;
    
    renderAgentList();
    
    localStorage.setItem('lastAgent', JSON.stringify(agent));
    updateRecentAgents(agent);
    
    loadChatHistory();
    
    // 切换视图
    document.getElementById('welcomeScreen').style.display = 'none';
    document.getElementById('chatArea').style.display = 'block';
    document.getElementById('inputArea').style.display = 'block';
    document.getElementById('backToHomeBtn').style.display = 'flex';
    document.getElementById('keepHistoryLabel').style.display = 'flex';
    document.getElementById('clearChatBtn').style.display = 'flex';
    
    setTimeout(() => {
        const input = document.getElementById('userInput');
        if (input) input.focus();
    }, 100);
}

// 更多全局函数绑定
window.selectAgentMobile = function(modelName) {
    const agent = agents.find(a => a.modelName === modelName);
    if (agent) {
        selectAgent(agent);
        if (window.innerWidth <= 768) {
            window.toggleMobileSidebar();
        }
    }
};

window.toggleAgentMenu = function(event, modelName) {
    event.stopPropagation();
    const existingMenu = document.querySelector('.dropdown-menu');
    if (existingMenu) existingMenu.remove();
    
    const agent = agents.find(a => a.modelName === modelName);
    if (!agent) return;
    
    const menu = document.createElement('div');
    menu.className = 'dropdown-menu';
    menu.innerHTML = `
        <div class="dropdown-item" onclick="editAgentByName('${modelName}')">✏️ 编辑</div>
        <div class="dropdown-item" onclick="deleteAgentByName('${modelName}')" style="color: #ef4444;">🗑️ 删除</div>
    `;
    
    const rect = event.target.getBoundingClientRect();
    menu.style.position = 'fixed'; 
    menu.style.left = `${rect.left}px`;
    menu.style.top = `${rect.bottom + 5}px`;
    menu.style.minWidth = '100px';
    
    document.body.appendChild(menu);
    
    setTimeout(() => {
        document.addEventListener('click', function closeMenu() {
            if (menu.parentNode) menu.remove();
            document.removeEventListener('click', closeMenu);
        }, { once: true });
    }, 0);
};

window.editAgentByName = function(name) {
    const agent = agents.find(a => a.modelName === name);
    if (agent) editAgent(agent);
};

window.deleteAgentByName = function(name) {
    const agent = agents.find(a => a.modelName === name);
    if (agent) deleteAgent(agent);
};

// 参数重置
function resetParams() {
    updateParamValue('temp', 0.8);
    updateParamValue('topp', 0.9);
    updateParamValue('topk', 40);
    updateParamValue('repeat', 1.1);
    updateParamValue('ctx', 2048);
    updateParamValue('seed', 0);
    
    const setVal = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.value = val;
    };
    
    setVal('temperature', 0.8);
    setVal('top_p', 0.9);
    setVal('top_k', 40);
    setVal('repeat_penalty', 1.1);
    setVal('num_ctx', 2048);
    setVal('seed', 0);
}

// 编辑智能体
async function editAgent(agent) {
    editingAgent = agent;
    const title = document.getElementById('editorTitle');
    if (title) title.textContent = '编辑智能体';
    
    const nameInput = document.getElementById('agentName');
    if (nameInput) nameInput.value = agent.displayName;
    
    // 尝试加载配置
    const savedConfig = localStorage.getItem(`agent_config_${agent.modelName}`);
    if (savedConfig) {
        try {
            const config = JSON.parse(savedConfig);
            const modelSelect = document.getElementById('baseModelSelect');
            const prompt = document.getElementById('systemPrompt');
            
            if (modelSelect) modelSelect.value = config.baseModel || '';
            if (prompt) prompt.value = config.systemPrompt || '';
            
            if (config.parameters) {
                const p = config.parameters;
                if (p.temp) { document.getElementById('temperature').value = p.temp; updateParamValue('temp', p.temp); }
                if (p.topp) { document.getElementById('top_p').value = p.topp; updateParamValue('topp', p.topp); }
                // ... 可以继续补充其他参数的恢复
            }
            const editor = document.getElementById('agentEditor');
            if (editor) editor.style.display = 'flex';
            return;
        } catch(e) {}
    }
    
    if (agent.baseModel) {
        const modelSelect = document.getElementById('baseModelSelect');
        if (modelSelect) modelSelect.value = agent.baseModel;
    }
    
    const editor = document.getElementById('agentEditor');
    if (editor) editor.style.display = 'flex';
}

// 保存智能体
window.saveAgent = async function() {
    const displayName = document.getElementById('agentName').value.trim();
    const baseModel = document.getElementById('baseModelSelect').value;
    const systemPrompt = document.getElementById('systemPrompt').value.trim();
    
    if (!displayName || !baseModel) {
        showToast('请填写名称并选择底座模型', 'warning');
        return;
    }
    
    const params = {
        temp: document.getElementById('temperature').value,
        topp: document.getElementById('top_p').value,
        topk: document.getElementById('top_k').value,
        repeat: document.getElementById('repeat_penalty').value,
        numCtx: document.getElementById('num_ctx').value,
        seed: document.getElementById('seed').value
    };
    
    // 生成模型名
    let modelName = editingAgent ? editingAgent.modelName : displayName.toLowerCase().replace(/[^a-z0-9-_]/g, '-');
    if (!modelName || modelName === '-') modelName = 'agent-' + Date.now();
    
    const modelfile = `FROM ${baseModel}
PARAMETER temperature ${params.temp}
PARAMETER top_p ${params.topp}
PARAMETER top_k ${params.topk}
PARAMETER repeat_penalty ${params.repeat}
PARAMETER num_ctx ${params.numCtx}
PARAMETER seed ${params.seed}
SYSTEM """
${systemPrompt || '你是一个友好的AI助手。'}
"""`;

    const statusDiv = document.getElementById('agentStatus');
    if (statusDiv) statusDiv.innerHTML = '<div class="loading-spinner">正在创建智能体...</div>';
    
    try {
        if (editingAgent) {
            await fetch(`${API_BASE}/api/delete`, {
                method: 'DELETE',
                body: JSON.stringify({ name: editingAgent.modelName })
            });
        }
        
        const response = await fetch(`${API_BASE}/api/create`, {
            method: 'POST',
            body: JSON.stringify({ name: modelName, modelfile: modelfile, stream: false })
        });
        
        if (!response.ok) throw new Error(await response.text());
        
        localStorage.setItem(`agent_config_${modelName}`, JSON.stringify({
            modelName, displayName, baseModel, systemPrompt, parameters: params
        }));
        
        if (statusDiv) statusDiv.innerHTML = '<span style="color:#10b981">✓ 创建成功</span>';
        showToast('智能体创建成功', 'success');
        
        setTimeout(() => {
            window.closeAgentEditor();
            loadModels();
        }, 1000);
        
    } catch (error) {
        console.error(error);
        if (statusDiv) statusDiv.innerHTML = `<span style="color:#ef4444">创建失败: ${error.message}</span>`;
        
        const hint = document.getElementById('manualCreateHint');
        const cmdDiv = document.getElementById('createCommand');
        if (hint) hint.style.display = 'block';
        if (cmdDiv) cmdDiv.textContent = `ollama create ${modelName} -f Modelfile`;
    }
};

window.deleteBaseModel = async function(modelName) {
    if(!confirm(`确定要删除底座模型 ${modelName} 吗？`)) return;
    try {
        await fetch(`${API_BASE}/api/delete`, {
            method: 'DELETE',
            body: JSON.stringify({ name: modelName })
        });
        showToast('已删除', 'success');
        loadModels();
    } catch(e) {
        showToast('删除失败', 'error');
    }
}

async function deleteAgent(agent) {
    if (!confirm(`确定要删除 "${agent.displayName}" 吗？`)) return;
    try {
        await fetch(`${API_BASE}/api/delete`, {
            method: 'DELETE',
            body: JSON.stringify({ name: agent.modelName })
        });
        
        if (currentAgent && currentAgent.name === agent.name) {
            window.backToHome();
        }
        showToast('已删除', 'success');
        loadModels();
    } catch(e) {
        showToast('删除失败', 'error');
    }
}

// 聊天相关
window.sendMessage = async function() {
    const input = document.getElementById('userInput');
    const message = input.value.trim();
    if (!message || !currentAgent) return;
    
    input.value = '';
    input.style.height = 'auto'; 
    
    addMessage('user', message);
    const assistantMsg = addMessage('assistant', '...');
    const contentDiv = assistantMsg.querySelector('.message-content');
    
    const keepHistory = document.getElementById('keepHistory').checked;
    const messages = keepHistory ? chatHistory : [chatHistory[chatHistory.length - 1]];
    
    try {
        const response = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            body: JSON.stringify({
                model: currentAgent.modelName,
                messages: messages,
                stream: true
            })
        });
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullText = '';
        contentDiv.textContent = ''; 
        
        while(true) {
            const {done, value} = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value, {stream: true});
            const lines = chunk.split('\n');
            
            for (const line of lines) {
                if (!line.trim()) continue;
                try {
                    const json = JSON.parse(line);
                    if (json.message && json.message.content) {
                        const content = json.message.content;
                        fullText += content;
                        contentDiv.textContent = fullText;
                        const chatArea = document.getElementById('chatArea');
                        chatArea.scrollTop = chatArea.scrollHeight;
                    }
                } catch(e) {}
            }
        }
        
        chatHistory.push({ role: 'assistant', content: fullText });
        saveChatHistory();
        
    } catch (error) {
        contentDiv.textContent = 'Error: ' + error.message;
        contentDiv.style.color = '#ef4444';
    }
};

function addMessage(role, content) {
    const container = document.getElementById('chatContainerInner');
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}`;
    
    msgDiv.innerHTML = `
        <div class="message-content">${content}</div>
        <div class="message-time">${new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>
    `;
    
    container.appendChild(msgDiv);
    const chatArea = document.getElementById('chatArea');
    chatArea.scrollTop = chatArea.scrollHeight;
    
    if (role === 'user') {
        chatHistory.push({ role: 'user', content: content });
    }
    
    return msgDiv;
}

window.updateParamValue = function(id, value) {
    const el = document.getElementById(id + 'Value');
    if (el) el.textContent = value;
};

// 格式化相对时间
function formatRelativeTime(timestamp) {
    const now = Date.now();
    const diff = now - timestamp;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (minutes < 1) return '刚刚';
    if (minutes < 60) return `${minutes} 分钟前`;
    if (hours < 24) return `${hours} 小时前`;
    return `${days} 天前`;
}

function updateRecentAgents(agent) {
    let recent = JSON.parse(localStorage.getItem('recentAgents') || '[]');
    recent = recent.filter(a => a.modelName !== agent.modelName);
    recent.unshift({ modelName: agent.modelName, displayName: agent.displayName, lastUsed: Date.now() });
    localStorage.setItem('recentAgents', JSON.stringify(recent.slice(0, 4)));
    renderRecentAgents();
}

function renderRecentAgents() {
    const container = document.getElementById('recentAgents');
    if (!container) return;
    const recent = JSON.parse(localStorage.getItem('recentAgents') || '[]');
    if (recent.length === 0) {
        container.innerHTML = '';
        return;
    }
    
    container.innerHTML = `
        <h3 style="font-size: 14px; color: var(--text-secondary); margin-bottom: 12px;">最近使用</h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 10px;">
            ${recent.map(a => `
                <button onclick="selectAgentMobile('${a.modelName}')" style="padding: 12px; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-sm); text-align: left; color: var(--text-primary); transition: var(--transition-fast);">
                    <div style="font-weight: 500; font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${a.displayName}</div>
                    <div style="font-size: 11px; color: var(--text-tertiary); margin-top: 4px;">${formatRelativeTime(a.lastUsed)}</div>
                </button>
            `).join('')}
        </div>
    `;
}

function renderPlazaAgents() {
    const container = document.getElementById('plazaAgentList');
    const empty = document.getElementById('plazaEmpty');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (agents.length === 0) {
        container.style.display = 'none';
        if (empty) empty.style.display = 'block';
        return;
    }
    
    container.style.display = 'grid';
    if (empty) empty.style.display = 'none';
    
    agents.forEach(agent => {
        const card = document.createElement('div');
        card.className = 'plaza-agent-card';
        card.onclick = () => window.selectAgentMobile(agent.modelName);
        
        card.innerHTML = `
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                <div class="agent-avatar" style="width: 48px; height: 48px; font-size: 20px;">${agent.displayName[0].toUpperCase()}</div>
                <div>
                    <div style="font-weight: 600; font-size: 16px;">${agent.displayName}</div>
                    <div style="font-size: 12px; color: var(--text-tertiary);">${agent.baseModel}</div>
                </div>
            </div>
            <button class="primary" style="width: 100%; font-size: 13px;">开始对话</button>
        `;
        container.appendChild(card);
    });
}

window.backToHome = function() {
    if (currentAgent) saveChatHistory();
    currentAgent = null;
    const welcome = document.getElementById('welcomeScreen');
    if (welcome) welcome.style.display = 'flex';
    
    document.getElementById('chatArea').style.display = 'none';
    document.getElementById('inputArea').style.display = 'none';
    document.getElementById('backToHomeBtn').style.display = 'none';
    document.getElementById('keepHistoryLabel').style.display = 'none';
    document.getElementById('clearChatBtn').style.display = 'none';
    
    const nameEl = document.getElementById('currentAgentName');
    if (nameEl) nameEl.textContent = '选择一个智能体开始对话';
    
    renderAgentList();
    renderRecentAgents();
};

window.pullModel = async function() {
    const name = document.getElementById('pullModelInput').value.trim();
    if (!name) return showToast('请输入模型名称', 'warning');
    
    const methodEl = document.querySelector('input[name="pullMethod"]:checked');
    const method = methodEl ? methodEl.value : 'api';
    
    if (method === 'cli') {
        const cmd = `ollama pull ${name}`;
        const cmdDiv = document.getElementById('pullCommand');
        const hint = document.getElementById('pullCommandHint');
        if (cmdDiv) cmdDiv.textContent = cmd;
        if (hint) hint.style.display = 'block';
        return;
    }
    
    const progress = document.getElementById('pullProgress');
    if (progress) progress.style.display = 'block';
    const progressText = document.getElementById('pullProgressText');
    const progressBar = document.getElementById('pullProgressBar');
    const percentText = document.getElementById('pullProgressPercent');
    
    try {
        const response = await fetch(`${API_BASE}/api/pull`, {
            method: 'POST',
            body: JSON.stringify({ name: name, stream: true })
        });
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        while(true) {
            const {done, value} = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            for(const line of lines) {
                if(!line) continue;
                try {
                    const json = JSON.parse(line);
                    if(json.total) {
                        const percent = Math.round((json.completed / json.total) * 100);
                        if (progressBar) progressBar.style.width = `${percent}%`;
                        if (percentText) percentText.textContent = `${percent}%`;
                        if (progressText) progressText.textContent = json.status;
                    } else if(json.status) {
                        if (progressText) progressText.textContent = json.status;
                    }
                } catch(e) {}
            }
        }
        
        showToast('拉取完成', 'success');
        setTimeout(() => {
            if (progress) progress.style.display = 'none';
            loadModels();
        }, 1000);
        
    } catch(e) {
        showToast('拉取失败: ' + e.message, 'error');
        if (progress) progress.style.display = 'none';
    }
};

window.updatePullMethod = function() {
    const methodEl = document.querySelector('input[name="pullMethod"]:checked');
    const method = methodEl ? methodEl.value : 'api';
    const hint = document.getElementById('pullCommandHint');
    const btn = document.getElementById('pullBtn');
    
    if (method === 'cli') {
        if (hint) hint.style.display = 'block';
        if (btn) btn.textContent = '生成命令';
    } else {
        if (hint) hint.style.display = 'none';
        if (btn) btn.textContent = '拉取模型';
    }
};

window.insertTemplate = function() {
    const prompt = document.getElementById('systemPrompt');
    if (prompt) {
        prompt.value = `你是一个专业的助手。
    
性格特点：
- 专业、客观
- 乐于助人

请用简洁的语言回答问题。`;
        showToast('模板已插入');
    }
};

window.downloadModelfile = function() {
    const displayName = document.getElementById('agentName').value.trim();
    const baseModel = document.getElementById('baseModelSelect').value;
    
    if (!displayName || !baseModel) {
        showToast('请填写名称并选择底座模型', 'warning');
        return;
    }
    showToast('功能暂未完全实现（纯前端模拟）');
};

// 历史记录保存与加载
function saveChatHistory() {
    if (currentAgent) {
        localStorage.setItem(`chat_${currentAgent.modelName}`, JSON.stringify(chatHistory));
    }
}

function loadChatHistory() {
    chatHistory = [];
    const container = document.getElementById('chatContainerInner');
    if (container) container.innerHTML = '';
    
    if (currentAgent) {
        try {
            const saved = JSON.parse(localStorage.getItem(`chat_${currentAgent.modelName}`) || '[]');
            saved.forEach(msg => {
                addMessage(msg.role, msg.content);
            });
            chatHistory = saved;
        } catch(e) {}
    }
}

window.clearChat = function() {
    chatHistory = [];
    const container = document.getElementById('chatContainerInner');
    if (container) container.innerHTML = '';
    
    if (currentAgent) {
        localStorage.removeItem(`chat_${currentAgent.modelName}`);
    }
    showToast('对话已清空');
};

// 初始化
document.addEventListener('DOMContentLoaded', async () => {
    // 自动调整输入框高度
    const input = document.getElementById('userInput');
    if (input) {
        input.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    }

    if (await checkOllamaConnection()) {
        await loadModels();
        try {
            const last = JSON.parse(localStorage.getItem('lastAgent'));
            if (last && agents.find(a => a.modelName === last.modelName)) {
                selectAgent(last);
            } else {
                renderRecentAgents();
            }
        } catch(e) { renderRecentAgents(); }
    } else {
        handleConnectionError();
    }
});

window.handleInputKeydown = function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        window.sendMessage();
    }
};
