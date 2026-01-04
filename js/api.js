// Ollama API 调用（保持原行为）

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
