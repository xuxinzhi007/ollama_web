// 兼容入口（已拆分）：优先使用 index.html 底部的多 <script> 引用。
// 旧版本完整代码备份：app.legacy.js
// 新版本脚本位于：js/state.js、js/utils.js、js/storage.js、js/api.js、js/ui.js、js/chat.js、js/main.js

(function loadSplitScriptsIfNeeded() {
    if (window.__OLLAMA_WEB_BOOTSTRAPPED__) return;

    const scripts = [
        'js/state.js',
        'js/utils.js',
        'js/storage.js',
        'js/api.js',
        'js/ui.js',
        'js/chat.js',
        'js/main.js'
    ];

    const loadOne = (src) => new Promise((resolve, reject) => {
        const s = document.createElement('script');
        s.src = src;
        s.onload = resolve;
        s.onerror = () => reject(new Error(`Failed to load ${src}`));
        document.body.appendChild(s);
    });

    (async () => {
        try {
            for (const src of scripts) await loadOne(src);
        } catch (e) {
            console.error(e);
        }
    })();
})();
