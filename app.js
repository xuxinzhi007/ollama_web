const API_BASE = 'http://localhost:11434';
let chatHistory = [];
let currentAgent = null; // 当前选中的智能体
let agents = []; // 所有智能体列表
let baseModels = []; // 底座模型列表
let editingAgent = null; // 正在编辑的智能体
let isPulling = false; // 是否正在拉取模型

// Toast 通知系统
function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = {
        'success': '✓',
        'error': '✕',
        'info': 'ℹ',
        'warning': '⚠'
    }[type] || 'ℹ';
    
    toast.innerHTML = `<span style="font-size: 18px;">${icon}</span><span style="flex: 1;">${message}</span><span class="toast-close">✕</span>`;
    
    container.appendChild(toast);
    
    // 点击关闭
    toast.onclick = () => {
        toast.classList.add('hiding');
        setTimeout(() => {
            if (toast.parentNode) {
                container.removeChild(toast);
            }
        }, 300);
    };
    
    // 自动消失
    const timer = setTimeout(() => {
        toast.classList.add('hiding');
        setTimeout(() => {
            if (toast.parentNode) {
                container.removeChild(toast);
            }
        }, 300);
    }, duration);
    
    // 鼠标悬停时暂停自动关闭
    toast.onmouseenter = () => clearTimeout(timer);
    toast.onmouseleave = () => {
        setTimeout(() => {
            if (toast.parentNode) {
                toast.classList.add('hiding');
                setTimeout(() => {
                    if (toast.parentNode) {
                        container.removeChild(toast);
                    }
                }, 300);
            }
        }, 1000);
    };
}

// 检查是否为底座模型
function isBaseModel(modelName) {
    const baseModels = [
        'llama', 'qwen', 'gemma', 'mistral', 'phi', 'deepseek', 
        'codellama', 'vicuna', 'orca', 'nous-hermes', 'dolphin',
        'yi', 'mixtral', 'solar', 'openchat', 'starling', 'neural-chat'
    ];
    
    const lowerName = modelName.toLowerCase();
    return baseModels.some(base => lowerName.startsWith(base));
}

// 检查 Ollama 连接
async function checkOllamaConnection() {
    try {
        const response = await fetch(`${API_BASE}/api/tags`, {
            method: 'GET',
            signal: AbortSignal.timeout(5000) // 5秒超时
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
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // 分类模型
        baseModels = [];
        agents = [];
        
        data.models.forEach(model => {
            if (isBaseModel(model.name)) {
                baseModels.push(model);
            } else {
                agents.push({
                    name: model.name,
                    displayName: model.name,
                    baseModel: 'unknown',
                    modelName: model.name
                });
            }
        });
        
        renderAgentList();
        renderBaseModelList();
        updateBaseModelSelect();
        
    } catch (error) {
        console.error('加载模型失败:', error);
        
        // 在侧边栏显示错误提示（不显示 Toast，避免重复）
        const agentList = document.getElementById('agentList');
        const noAgents = document.getElementById('noAgents');
        agentList.innerHTML = '';
        noAgents.style.display = 'block';
        noAgents.innerHTML = `
            <div style="font-size: 40px; margin-bottom: 10px;">⚠️</div>
            <div style="color: #ef4444; font-weight: 500;">连接失败</div>
            <div style="font-size: 12px; margin-top: 10px; color: #9ca3af; line-height: 1.5;">
                ${error.message}<br>
                <br>
                端口: ${API_BASE}
            </div>
            <button onclick="location.reload()" style="margin-top: 15px; padding: 8px 16px; background: #2563eb; border: none; border-radius: 6px; color: white; cursor: pointer; font-size: 13px;">
                重新连接
            </button>
        `;
    }
}

// 渲染智能体列表
function renderAgentList() {
    const agentList = document.getElementById('agentList');
    const noAgents = document.getElementById('noAgents');
    
    agentList.innerHTML = '';
    
    if (agents.length === 0) {
        noAgents.style.display = 'block';
        return;
    }
    
    noAgents.style.display = 'none';
    
    agents.forEach(agent => {
        const item = document.createElement('div');
        item.className = 'agent-item';
        if (currentAgent && currentAgent.name === agent.name) {
            item.classList.add('active');
        }
        
        // 头像
        const avatar = document.createElement('div');
        avatar.className = 'agent-avatar';
        avatar.textContent = agent.displayName.charAt(0).toUpperCase();
        
        // 信息
        const info = document.createElement('div');
        info.className = 'agent-info';
        info.onclick = () => selectAgentMobile(agent);
        
        const name = document.createElement('div');
        name.className = 'agent-name';
        name.textContent = agent.displayName;
        
        const base = document.createElement('div');
        base.className = 'agent-base';
        base.textContent = agent.baseModel;
        
        info.appendChild(name);
        info.appendChild(base);
        
        // 菜单按钮
        const menu = document.createElement('div');
        menu.className = 'agent-menu';
        
        const menuBtn = document.createElement('button');
        menuBtn.className = 'menu-btn';
        menuBtn.textContent = '⋮';
        menuBtn.onclick = (e) => {
            e.stopPropagation();
            showAgentMenu(agent, menuBtn);
        };
        
        menu.appendChild(menuBtn);
        
        item.appendChild(avatar);
        item.appendChild(info);
        item.appendChild(menu);
        
        agentList.appendChild(item);
    });
}

// 渲染底座模型列表
function renderBaseModelList() {
    const baseModelList = document.getElementById('baseModelList');
    baseModelList.innerHTML = '';
    
    if (baseModels.length === 0) {
        baseModelList.innerHTML = '<div style="padding: 10px; color: #9ca3af; font-size: 12px;">暂无底座模型</div>';
        return;
    }
    
    baseModels.forEach(model => {
        const item = document.createElement('div');
        item.style.cssText = 'padding: 10px; margin: 5px 0; background: #333; border-radius: 6px; display: flex; justify-content: space-between; align-items: center;';
        
        const name = document.createElement('span');
        name.textContent = model.name;
        name.style.flex = '1';
        
        const deleteBtn = document.createElement('button');
        deleteBtn.textContent = '删除';
        deleteBtn.style.cssText = 'padding: 4px 10px; background: #dc2626; border: none; border-radius: 4px; color: white; cursor: pointer; font-size: 12px;';
        deleteBtn.onclick = () => deleteBaseModel(model.name);
        
        item.appendChild(name);
        item.appendChild(deleteBtn);
        baseModelList.appendChild(item);
    });
}

// 更新底座模型选择框
function updateBaseModelSelect() {
    const select = document.getElementById('baseModelSelect');
    select.innerHTML = '<option value="">选择底座模型...</option>';
    
    baseModels.forEach(model => {
        const option = document.createElement('option');
        option.value = model.name;
        option.textContent = model.name;
        select.appendChild(option);
    });
}

// 选择智能体
function selectAgent(agent) {
    // 切换智能体时询问是否清空对话
    if (chatHistory.length > 0 && currentAgent && currentAgent.name !== agent.name) {
        if (confirm('切换智能体，是否清空当前对话？')) {
            clearChat();
        }
    }
    
    currentAgent = agent;
    document.getElementById('currentAgentName').textContent = agent.displayName;
    renderAgentList();
}

// 显示智能体菜单
let currentMenu = null;
function showAgentMenu(agent, button) {
    // 关闭之前的菜单
    if (currentMenu) {
        currentMenu.remove();
        currentMenu = null;
        return;
    }
    
    const menu = document.createElement('div');
    menu.className = 'dropdown-menu show';
    
    const editItem = document.createElement('div');
    editItem.className = 'dropdown-item';
    editItem.textContent = '✏️ 编辑';
    editItem.onclick = () => {
        editAgent(agent);
        menu.remove();
        currentMenu = null;
    };
    
    const deleteItem = document.createElement('div');
    deleteItem.className = 'dropdown-item';
    deleteItem.textContent = '🗑️ 删除';
    deleteItem.onclick = () => {
        deleteAgent(agent);
        menu.remove();
        currentMenu = null;
    };
    
    menu.appendChild(editItem);
    menu.appendChild(deleteItem);
    
    button.parentElement.parentElement.appendChild(menu);
    currentMenu = menu;
    
    // 点击其他地方关闭菜单
    setTimeout(() => {
        document.addEventListener('click', function closeMenu(e) {
            if (menu && !menu.contains(e.target)) {
                menu.remove();
                currentMenu = null;
                document.removeEventListener('click', closeMenu);
            }
        });
    }, 0);
}

// 创建新智能体
function createNewAgent() {
    editingAgent = null;
    document.getElementById('editorTitle').textContent = '创建智能体';
    document.getElementById('agentName').value = '';
    document.getElementById('baseModelSelect').value = '';
    document.getElementById('systemPrompt').value = '';
    document.getElementById('temperature').value = '0.8';
    document.getElementById('top_p').value = '0.9';
    document.getElementById('top_k').value = '40';
    document.getElementById('repeat_penalty').value = '1.1';
    document.getElementById('num_ctx').value = '2048';
    document.getElementById('num_predict').value = '-1';
    document.getElementById('seed').value = '0';
    document.getElementById('stop_sequences').value = '';
    updateParamValue('temp', '0.8');
    updateParamValue('topp', '0.9');
    updateParamValue('topk', '40');
    updateParamValue('repeat', '1.1');
    updateParamValue('ctx', '2048');
    updateParamValue('predict', '-1');
    updateParamValue('seed', '0');
    document.getElementById('agentEditor').style.display = 'block';
}

// 编辑智能体
async function editAgent(agent) {
    editingAgent = agent;
    document.getElementById('editorTitle').textContent = '编辑智能体';
    document.getElementById('agentName').value = agent.displayName;
    
    // 加载现有配置
    try {
        const response = await fetch(`${API_BASE}/api/show`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: agent.modelName })
        });
        const data = await response.json();
        
        // 解析 Modelfile
        const modelfile = data.modelfile || '';
        const fromMatch = modelfile.match(/FROM\s+(\S+)/);
        const systemMatch = modelfile.match(/SYSTEM\s+"""([\s\S]*?)"""/);
        const tempMatch = modelfile.match(/PARAMETER\s+temperature\s+([\d.]+)/);
        const toppMatch = modelfile.match(/PARAMETER\s+top_p\s+([\d.]+)/);
        const topkMatch = modelfile.match(/PARAMETER\s+top_k\s+([\d]+)/);
        const repeatMatch = modelfile.match(/PARAMETER\s+repeat_penalty\s+([\d.]+)/);
        const ctxMatch = modelfile.match(/PARAMETER\s+num_ctx\s+([\d]+)/);
        const predictMatch = modelfile.match(/PARAMETER\s+num_predict\s+([-\d]+)/);
        const seedMatch = modelfile.match(/PARAMETER\s+seed\s+([\d]+)/);
        const stopMatches = modelfile.match(/PARAMETER\s+stop\s+"([^"]+)"/g);
        
        if (fromMatch) document.getElementById('baseModelSelect').value = fromMatch[1];
        if (systemMatch) document.getElementById('systemPrompt').value = systemMatch[1].trim();
        if (tempMatch) {
            document.getElementById('temperature').value = tempMatch[1];
            updateParamValue('temp', tempMatch[1]);
        }
        if (toppMatch) {
            document.getElementById('top_p').value = toppMatch[1];
            updateParamValue('topp', toppMatch[1]);
        }
        if (topkMatch) {
            document.getElementById('top_k').value = topkMatch[1];
            updateParamValue('topk', topkMatch[1]);
        }
        if (repeatMatch) {
            document.getElementById('repeat_penalty').value = repeatMatch[1];
            updateParamValue('repeat', repeatMatch[1]);
        }
        if (ctxMatch) {
            document.getElementById('num_ctx').value = ctxMatch[1];
            updateParamValue('ctx', ctxMatch[1]);
        }
        if (predictMatch) {
            document.getElementById('num_predict').value = predictMatch[1];
            updateParamValue('predict', predictMatch[1]);
        }
        if (seedMatch) {
            document.getElementById('seed').value = seedMatch[1];
            updateParamValue('seed', seedMatch[1]);
        }
        if (stopMatches) {
            const stops = stopMatches.map(m => m.match(/"([^"]+)"/)[1]);
            document.getElementById('stop_sequences').value = stops.join(', ');
        }
        
    } catch (error) {
        console.error('加载智能体配置失败:', error);
    }
    
    document.getElementById('agentEditor').style.display = 'block';
}

// 保存智能体
async function saveAgent() {
    const displayName = document.getElementById('agentName').value.trim();
    const baseModel = document.getElementById('baseModelSelect').value;
    const systemPrompt = document.getElementById('systemPrompt').value.trim();
    const temp = document.getElementById('temperature').value;
    const topp = document.getElementById('top_p').value;
    const topk = document.getElementById('top_k').value;
    const repeat = document.getElementById('repeat_penalty').value;
    const numCtx = document.getElementById('num_ctx').value;
    const numPredict = document.getElementById('num_predict').value;
    const seed = document.getElementById('seed').value;
    const stopSeq = document.getElementById('stop_sequences').value.trim();
    
    if (!displayName || !baseModel) {
        showToast('请填写智能体名称并选择底座模型', 'warning');
        return;
    }
    
    // 生成模型名称（使用小写和连字符）
    const modelName = editingAgent ? editingAgent.modelName : displayName.toLowerCase().replace(/\s+/g, '-');
    
    // 生成 Modelfile
    let modelfile = `FROM ${baseModel}

PARAMETER temperature ${temp}
PARAMETER top_p ${topp}
PARAMETER top_k ${topk}
PARAMETER repeat_penalty ${repeat}`;

    // 添加高级参数（如果不是默认值）
    if (numCtx !== '2048') {
        modelfile += `\nPARAMETER num_ctx ${numCtx}`;
    }
    if (numPredict !== '-1') {
        modelfile += `\nPARAMETER num_predict ${numPredict}`;
    }
    if (seed !== '0') {
        modelfile += `\nPARAMETER seed ${seed}`;
    }
    if (stopSeq) {
        const stops = stopSeq.split(',').map(s => s.trim()).filter(s => s);
        stops.forEach(stop => {
            modelfile += `\nPARAMETER stop "${stop}"`;
        });
    }

    modelfile += `

SYSTEM """
${systemPrompt || '你是一个友好的AI助手。'}
"""`;
    
    const statusDiv = document.getElementById('agentStatus');
    statusDiv.innerHTML = '<div class="status">正在保存...</div>';
    
    // 如果是编辑，先删除旧模型
    if (editingAgent) {
        try {
            await fetch(`${API_BASE}/api/delete`, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: editingAgent.modelName })
            });
        } catch (error) {
            console.log('删除旧模型失败，继续创建');
        }
    }
    
    // 创建模型
    try {
        const response = await fetch(`${API_BASE}/api/create`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: modelName, modelfile, stream: true })
        });
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n').filter(line => line.trim());
            
            for (const line of lines) {
                try {
                    const json = JSON.parse(line);
                    if (json.status) {
                        statusDiv.innerHTML = `<div class="status">${json.status}</div>`;
                    }
                } catch (e) {}
            }
        }
        
        statusDiv.innerHTML = '<div class="status success">保存成功！</div>';
        showToast(`智能体 "${displayName}" ${editingAgent ? '更新' : '创建'}成功！`, 'success');
        
        setTimeout(() => {
            closeAgentEditor();
            loadModels();
        }, 1000);
        
    } catch (error) {
        statusDiv.innerHTML = `<div class="status error">错误: ${error.message}</div>`;
        showToast('保存失败: ' + error.message, 'error');
    }
}

// 删除智能体
async function deleteAgent(agent) {
    if (!confirm(`确定要删除智能体 "${agent.displayName}" 吗？`)) {
        return;
    }
    
    try {
        await fetch(`${API_BASE}/api/delete`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: agent.modelName })
        });
        
        if (currentAgent && currentAgent.name === agent.name) {
            currentAgent = null;
            document.getElementById('currentAgentName').textContent = '选择一个智能体开始对话';
            clearChat();
        }
        
        showToast(`智能体 "${agent.displayName}" 已删除`, 'success');
        loadModels();
    } catch (error) {
        showToast('删除失败: ' + error.message, 'error');
    }
}

function closeAgentEditor() {
    document.getElementById('agentEditor').style.display = 'none';
    editingAgent = null;
}

// 管理面板
function toggleManagePanel() {
    document.getElementById('managePanel').style.display = 'block';
    // 不需要重新加载，因为已经在页面加载时加载过了
    // 只在需要时更新底座模型列表
    renderBaseModelList();
}

function closeManagePanel() {
    document.getElementById('managePanel').style.display = 'none';
}

// 删除底座模型
async function deleteBaseModel(modelName) {
    if (!confirm(`确定要删除底座模型 "${modelName}" 吗？\n\n删除后如需使用需要重新拉取。`)) {
        return;
    }
    
    try {
        await fetch(`${API_BASE}/api/delete`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: modelName })
        });
        
        showToast(`底座模型 "${modelName}" 已删除`, 'success');
        loadModels();
    } catch (error) {
        showToast('删除失败: ' + error.message, 'error');
    }
}

// 格式化文件大小
function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// 格式化速度
function formatSpeed(bytesPerSecond) {
    if (!bytesPerSecond || bytesPerSecond === 0) return '--';
    return formatBytes(bytesPerSecond) + '/s';
}

// 更新拉取方式
function updatePullMethod() {
    const method = document.querySelector('input[name="pullMethod"]:checked').value;
    const commandHint = document.getElementById('pullCommandHint');
    const pullBtn = document.getElementById('pullBtn');
    
    if (method === 'cli') {
        commandHint.style.display = 'block';
        pullBtn.textContent = '显示命令';
    } else {
        commandHint.style.display = 'none';
        pullBtn.textContent = '拉取模型';
    }
}

// 拉取模型
async function pullModel() {
    const modelName = document.getElementById('pullModelInput').value.trim();
    if (!modelName) {
        showToast('请输入模型名称', 'warning');
        return;
    }
    
    const method = document.querySelector('input[name="pullMethod"]:checked').value;
    
    // 如果选择命令行方式
    if (method === 'cli') {
        const commandDiv = document.getElementById('pullCommand');
        const commandHint = document.getElementById('pullCommandHint');
        
        if (!commandDiv) {
            console.error('pullCommand 元素未找到');
            showToast('界面错误，请刷新页面', 'error');
            return;
        }
        
        const command = `ollama pull ${modelName}`;
        commandDiv.textContent = command;
        commandDiv.innerHTML = command; // 同时设置 innerHTML 确保显示
        commandHint.style.display = 'block';
        
        console.log('显示命令:', command);
        
        // 复制到剪贴板
        navigator.clipboard.writeText(command).then(() => {
            showToast('命令已复制到剪贴板', 'success');
        }).catch((err) => {
            console.error('复制失败:', err);
            showToast('请手动复制命令', 'info');
        });
        
        return;
    }
    
    // HTTP API 方式
    const statusDiv = document.getElementById('pullStatus');
    const progressDiv = document.getElementById('pullProgress');
    const progressBar = document.getElementById('pullProgressBar');
    const progressText = document.getElementById('pullProgressText');
    const progressPercent = document.getElementById('pullProgressPercent');
    const speedText = document.getElementById('pullSpeed');
    const sizeText = document.getElementById('pullSize');
    const pullBtn = document.getElementById('pullBtn');
    
    // 显示进度条
    progressDiv.style.display = 'block';
    statusDiv.innerHTML = '';
    pullBtn.disabled = true;
    pullBtn.textContent = '拉取中...';
    isPulling = true; // 标记正在拉取
    
    let lastTime = Date.now();
    let lastCompleted = 0;
    
    try {
        const response = await fetch(`${API_BASE}/api/pull`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: modelName, stream: true })
        });
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n').filter(line => line.trim());
            
            for (const line of lines) {
                try {
                    const json = JSON.parse(line);
                    
                    // 显示状态信息
                    if (json.status) {
                        let statusText = json.status;
                        
                        // 翻译常见状态
                        const statusMap = {
                            'pulling manifest': '正在拉取清单',
                            'pulling': '正在下载',
                            'verifying sha256 digest': '正在验证文件',
                            'writing manifest': '正在写入清单',
                            'removing any unused layers': '正在清理',
                            'success': '完成'
                        };
                        
                        statusText = statusMap[json.status.toLowerCase()] || json.status;
                        progressText.textContent = statusText;
                    }
                    
                    // 计算进度
                    if (json.completed !== undefined && json.total !== undefined && json.total > 0) {
                        const percent = Math.round((json.completed / json.total) * 100);
                        progressBar.style.width = percent + '%';
                        progressPercent.textContent = percent + '%';
                        
                        // 计算速度
                        const now = Date.now();
                        const timeDiff = (now - lastTime) / 1000; // 秒
                        const bytesDiff = json.completed - lastCompleted;
                        
                        if (timeDiff > 0.5) { // 每0.5秒更新一次速度
                            const speed = bytesDiff / timeDiff;
                            speedText.textContent = '速度: ' + formatSpeed(speed);
                            lastTime = now;
                            lastCompleted = json.completed;
                        }
                        
                        // 显示大小
                        sizeText.textContent = `${formatBytes(json.completed)} / ${formatBytes(json.total)}`;
                    }
                    
                    // 如果没有进度信息，但有 digest 信息
                    if (json.digest) {
                        progressText.textContent = `正在处理: ${json.digest.substring(0, 12)}...`;
                    }
                    
                } catch (e) {
                    console.error('解析进度失败:', e, line);
                }
            }
        }
        
        progressBar.style.width = '100%';
        progressPercent.textContent = '100%';
        progressText.textContent = '拉取完成！';
        isPulling = false; // 标记拉取结束
        showToast(`模型 "${modelName}" 拉取成功！`, 'success');
        
        setTimeout(() => {
            progressDiv.style.display = 'none';
            loadModels();
        }, 2000);
        
    } catch (error) {
        progressDiv.style.display = 'none';
        
        let errorMsg = error.message;
        if (error.message.includes('Failed to fetch')) {
            errorMsg = '无法连接到 Ollama 服务，请确保 Ollama 正在运行';
            statusDiv.innerHTML = `<div class="status error">
                ${errorMsg}<br>
                <small style="margin-top: 5px; display: block;">建议使用"命令行"方式拉取</small>
            </div>`;
        } else {
            statusDiv.innerHTML = `<div class="status error">错误: ${errorMsg}</div>`;
        }
        
        showToast('拉取失败: ' + errorMsg, 'error');
    } finally {
        pullBtn.disabled = false;
        pullBtn.textContent = '拉取模型';
        isPulling = false; // 标记拉取结束
    }
}

// 更新参数显示值
function updateParamValue(type, value) {
    const displays = {
        'temp': 'tempValue',
        'topp': 'toppValue',
        'topk': 'topkValue',
        'repeat': 'repeatValue',
        'ctx': 'ctxValue',
        'predict': 'predictValue',
        'seed': 'seedValue'
    };
    const elementId = displays[type];
    const element = document.getElementById(elementId);
    if (element) {
        // 特殊处理 predict 的显示
        if (type === 'predict' && value === '-1') {
            element.textContent = '无限制';
        } else {
            element.textContent = value;
        }
    } else {
        console.warn(`Element ${elementId} not found for type ${type}`);
    }
}

// 插入模板
function insertTemplate() {
    const baseModel = document.getElementById('baseModelSelect').value;
    
    if (!baseModel) {
        showToast('请先选择底座模型', 'warning');
        return;
    }
    
    // 根据不同的底座模型生成不同的模板
    let template = '';
    
    if (baseModel.includes('qwen')) {
        template = `你是一个专业的AI助手，基于通义千问模型。

性格特点：
- 专业、准确、高效
- 特别擅长中文理解和生成
- 对中文文化和语境有深入理解

能力范围：
- 回答各类问题
- 文本创作和改写
- 代码编写和解释
- 翻译和总结

说话风格：
- 简洁明了，重点突出
- 适当使用例子说明
- 保持友好和耐心`;
    } else if (baseModel.includes('gemma')) {
        template = `你是一个友好的AI助手，基于 Google Gemma 模型。

性格特点：
- 友好、开放、乐于助人
- 善于理解用户意图
- 注重安全和负责任的回答

能力范围：
- 日常对话和问答
- 创意写作
- 学习辅导
- 生活建议

说话风格：
- 温和友善
- 循循善诱
- 鼓励和支持用户`;
    } else if (baseModel.includes('llama')) {
        template = `你是一个智能AI助手，基于 Meta Llama 模型。

性格特点：
- 聪明、灵活、适应性强
- 逻辑思维清晰
- 善于分析和推理

能力范围：
- 复杂问题分析
- 多步骤推理
- 知识整合
- 创造性思考

说话风格：
- 条理清晰
- 逻辑严谨
- 深入浅出`;
    } else if (baseModel.includes('deepseek')) {
        template = `你是一个专业的编程助手，基于 DeepSeek 模型。

性格特点：
- 技术专家
- 注重代码质量
- 善于解决技术问题

能力范围：
- 代码编写和优化
- Bug 调试
- 算法设计
- 技术方案建议

说话风格：
- 技术准确
- 提供代码示例
- 解释清晰`;
    } else {
        // 通用模板
        template = `你是一个[角色名称]，性格特点：[描述性格]

背景设定：
[角色的背景故事]

能力范围：
- [能力1]
- [能力2]
- [能力3]

说话风格：
[描述说话方式，比如：活泼、严肃、幽默等]

行为准则：
- 始终保持角色设定
- 用第一人称回应
- 展现角色的情感和个性`;
    }
    
    document.getElementById('systemPrompt').value = template;
    showToast('模板已插入，请根据需要修改', 'success');
}

// 发送消息
async function sendMessage() {
    const input = document.getElementById('userInput');
    const message = input.value.trim();
    
    if (!message) return;
    if (!currentAgent) {
        showToast('请先选择一个智能体', 'warning');
        return;
    }
    
    // 添加用户消息
    addMessage('user', message);
    input.value = '';
    
    // 添加助手消息占位
    const assistantDiv = addMessage('assistant', '思考中...');
    
    // 检查是否保留历史记录
    const keepHistory = document.getElementById('keepHistory').checked;
    const messages = keepHistory ? chatHistory : [chatHistory[chatHistory.length - 1]];
    
    try {
        const response = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: currentAgent.modelName,
                messages: messages,
                stream: true
            })
        });
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullResponse = '';
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n').filter(line => line.trim());
            
            for (const line of lines) {
                try {
                    const json = JSON.parse(line);
                    if (json.message?.content) {
                        fullResponse += json.message.content;
                        assistantDiv.textContent = fullResponse;
                    }
                } catch (e) {}
            }
        }
        
        chatHistory.push({ role: 'assistant', content: fullResponse });
        
    } catch (error) {
        assistantDiv.textContent = '错误: ' + error.message;
    }
}

// 添加消息到界面
function addMessage(role, content) {
    const chatArea = document.getElementById('chatArea');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.textContent = content;
    chatArea.appendChild(messageDiv);
    chatArea.scrollTop = chatArea.scrollHeight;
    
    if (role === 'user') {
        chatHistory.push({ role: 'user', content });
    }
    
    return messageDiv;
}

// 清空对话
function clearChat() {
    chatHistory = [];
    document.getElementById('chatArea').innerHTML = '';
}

// 显示存储位置信息
window.showStorageInfo = function() {
    const modal = document.getElementById('storageInfoModal');
    const pathDiv = document.getElementById('defaultStoragePath');
    
    if (!modal || !pathDiv) {
        console.error('存储信息模态框元素未找到');
        showToast('界面错误，请刷新页面', 'error');
        return;
    }
    
    // 根据操作系统显示默认路径
    const platform = navigator.platform.toLowerCase();
    const userAgent = navigator.userAgent.toLowerCase();
    let defaultPath = '';
    let osName = '';
    
    // 检测操作系统
    if (platform.includes('win') || userAgent.includes('windows')) {
        defaultPath = 'C:\\Users\\<用户名>\\.ollama\\models';
        osName = 'Windows';
    } else if (platform.includes('mac') || userAgent.includes('mac')) {
        defaultPath = '~/.ollama/models';
        osName = 'macOS';
    } else if (platform.includes('linux') || userAgent.includes('linux')) {
        defaultPath = '~/.ollama/models';
        osName = 'Linux';
    } else {
        defaultPath = '~/.ollama/models';
        osName = '未知系统';
    }
    
    pathDiv.innerHTML = `
        <div style="margin-bottom: 5px; color: #9ca3af; font-size: 11px;">检测到系统: ${osName}</div>
        <div>${defaultPath}</div>
    `;
    modal.style.display = 'flex';
}

window.closeStorageInfo = function() {
    const modal = document.getElementById('storageInfoModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// 复制命令
window.copyCommand = function(elementId) {
    const element = document.getElementById(elementId);
    if (!element) {
        showToast('元素未找到', 'error');
        return;
    }
    
    const text = element.textContent.trim();
    
    navigator.clipboard.writeText(text).then(() => {
        showToast('命令已复制到剪贴板', 'success');
    }).catch(() => {
        showToast('复制失败，请手动复制', 'error');
    });
}

// 移动端侧边栏切换
function toggleMobileSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.getElementById('mobileOverlay');
    
    sidebar.classList.toggle('open');
    overlay.classList.toggle('show');
}

// 选择智能体后自动关闭移动端侧边栏
function selectAgentMobile(agent) {
    selectAgent(agent);
    
    // 如果是移动端，关闭侧边栏
    if (window.innerWidth <= 768) {
        toggleMobileSidebar();
    }
}

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', async () => {
    // 先检查连接
    const isConnected = await checkOllamaConnection();
    
    if (!isConnected) {
        // 显示 Toast 提示
        showToast(`无法连接到 Ollama (${API_BASE})

请确保 Ollama 服务正在运行`, 'error', 8000);
        
        // 显示连接失败的界面提示
        const agentList = document.getElementById('agentList');
        const noAgents = document.getElementById('noAgents');
        agentList.innerHTML = '';
        noAgents.style.display = 'block';
        noAgents.innerHTML = `
            <div style="font-size: 40px; margin-bottom: 10px;">⚠️</div>
            <div style="color: #ef4444; font-weight: 500;">无法连接到 Ollama</div>
            <div style="font-size: 12px; margin-top: 10px; color: #9ca3af; line-height: 1.5;">
                请确保 Ollama 正在运行<br>
                <br>
                <strong>启动方法：</strong><br>
                • macOS/Linux: 从应用启动<br>
                • Windows: 从开始菜单启动<br>
                <br>
                端口: ${API_BASE}
            </div>
            <button onclick="location.reload()" style="margin-top: 15px; padding: 8px 16px; background: #2563eb; border: none; border-radius: 6px; color: white; cursor: pointer; font-size: 13px;">
                重新连接
            </button>
        `;
        return; // 不再继续加载，避免后续的 loadModels 再次报错
    }
    
    loadModels();
});

// 防止在拉取模型时刷新页面
window.addEventListener('beforeunload', (e) => {
    if (isPulling) {
        e.preventDefault();
        e.returnValue = '正在拉取模型，刷新页面会中断下载。确定要离开吗？';
        return e.returnValue;
    }
});
