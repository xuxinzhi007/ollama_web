// ============ 应用初始化入口 ============

/**
 * 欢迎页 Tab 切换
 */
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

    if (tab === 'plaza') {
        if (typeof renderPlazaAgents === 'function') {
            renderPlazaAgents();
        }
    }
};

// ============ 应用初始化 ============

document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 Ollama Web UI 初始化中...');

    // 自动调整输入框高度
    const input = document.getElementById('userInput');
    if (input) {
        input.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    }

    // 初始化主应用
    if (await checkOllamaConnection()) {
        console.log('✅ Ollama 连接成功');
        await loadModels();
        try {
            const last = JSON.parse(localStorage.getItem('lastAgent'));
            if (last && agents.find(a => a.modelName === last.modelName)) {
                selectAgent(last);
            } else {
                renderRecentAgents();
            }
        } catch (e) {
            renderRecentAgents();
        }
    } else {
        console.log('❌ Ollama 连接失败');
        handleConnectionError();
    }

    console.log('✅ Ollama Web UI 初始化完成');
});