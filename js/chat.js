// 聊天相关（sendMessage / addMessage / clearChat / handleInputKeydown）

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
            headers: { 'Content-Type': 'application/json' },
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

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
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
                } catch (e) {}
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

window.clearChat = function() {
    chatHistory = [];
    const container = document.getElementById('chatContainerInner');
    if (container) container.innerHTML = '';

    if (currentAgent) {
        localStorage.removeItem(`chat_${currentAgent.modelName}`);
    }
    showToast('对话已清空');
};

window.handleInputKeydown = function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        window.sendMessage();
    }
};
