// 应用初始化入口（最后加载）

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
        } catch (e) { renderRecentAgents(); }
    } else {
        handleConnectionError();
    }
});
