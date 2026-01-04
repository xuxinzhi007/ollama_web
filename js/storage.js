// localStorage / 配置 / 历史 相关

function getAgentConfig(modelName) {
    for (const keyName of getModelNameAliases(modelName)) {
        const raw = localStorage.getItem(`agent_config_${keyName}`);
        if (!raw) continue;
        try { return JSON.parse(raw); } catch (_) {}
    }
    return null;
}

function setAgentConfig(modelName, configObj) {
    for (const keyName of getModelNameAliases(modelName)) {
        localStorage.setItem(`agent_config_${keyName}`, JSON.stringify(configObj));
    }
}

function clearAgentLocalData(modelName) {
    for (const keyName of getModelNameAliases(modelName)) {
        localStorage.removeItem(`chat_${keyName}`);
        localStorage.removeItem(`agent_config_${keyName}`);
    }
    // 兼容历史上可能保存的 lastAgent / recentAgents 指向已删除模型
    try {
        const last = JSON.parse(localStorage.getItem('lastAgent') || 'null');
        if (last && getModelNameAliases(modelName).includes(last.modelName)) {
            localStorage.removeItem('lastAgent');
        }
    } catch (_) {}
    try {
        const recent = JSON.parse(localStorage.getItem('recentAgents') || '[]');
        if (Array.isArray(recent)) {
            const aliases = new Set(getModelNameAliases(modelName));
            const filtered = recent.filter(a => !aliases.has(a.modelName));
            localStorage.setItem('recentAgents', JSON.stringify(filtered));
        }
    } catch (_) {}
}

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
        } catch (e) {}
    }
}
