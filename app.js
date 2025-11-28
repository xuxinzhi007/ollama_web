const API_BASE = 'http://localhost:11434';
let chatHistory = [];
let currentAgent = null; // 当前选中的智能体
let agents = []; // 所有智能体列表
let baseModels = []; // 底座模型列表
let editingAgent = null; // 正在编辑的智能体

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
    
    toast.innerHTML = `<span style="font-size: 18px;">${icon}</span><span>${message}</span>`;
    
    container.appendChild(toast);
    
    // 自动消失
    setTimeout(() => {
        toast.classList.add('hiding');
        setTimeout(() => {
            container.removeChild(toast);
        }, 300);
    }, duration);
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

// 加载所有模型
async function loadModels() {
    try {
        const response = await fetch(`${API_BASE}/api/tags`);
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
        showToast('无法连接到 Ollama，请确保服务正在运行', 'error', 5000);
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
        info.onclick = () => selectAgent(agent);
        
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
    updateParamValue('temp', '0.8');
    updateParamValue('topp', '0.9');
    updateParamValue('topk', '40');
    updateParamValue('repeat', '1.1');
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
    
    if (!displayName || !baseModel) {
        showToast('请填写智能体名称并选择底座模型', 'warning');
        return;
    }
    
    // 生成模型名称（使用小写和连字符）
    const modelName = editingAgent ? editingAgent.modelName : displayName.toLowerCase().replace(/\s+/g, '-');
    
    // 生成 Modelfile
    const modelfile = `FROM ${baseModel}

PARAMETER temperature ${temp}
PARAMETER top_p ${topp}
PARAMETER top_k ${topk}
PARAMETER repeat_penalty ${repeat}

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
    loadModels();
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

// 拉取模型
async function pullModel() {
    const modelName = document.getElementById('pullModelInput').value.trim();
    if (!modelName) return;
    
    const statusDiv = document.getElementById('pullStatus');
    statusDiv.innerHTML = '<div class="status">正在拉取...</div>';
    
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
                    if (json.status) {
                        statusDiv.innerHTML = `<div class="status">${json.status}</div>`;
                    }
                } catch (e) {}
            }
        }
        
        statusDiv.innerHTML = '<div class="status success">拉取完成！</div>';
        showToast(`模型 "${modelName}" 拉取成功！`, 'success');
        loadModels();
    } catch (error) {
        statusDiv.innerHTML = `<div class="status error">错误: ${error.message}</div>`;
        showToast('拉取失败: ' + error.message, 'error');
    }
}

// 更新参数显示值
function updateParamValue(type, value) {
    const displays = {
        'temp': 'tempValue',
        'topp': 'toppValue',
        'topk': 'topkValue',
        'repeat': 'repeatValue'
    };
    const elementId = displays[type];
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
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

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', () => {
    loadModels();
});
