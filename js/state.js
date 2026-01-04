// 全局状态与常量
// 注意：本项目采用传统多脚本加载（非 ESM），此文件需最先加载。

const API_BASE = 'http://localhost:11434';

let chatHistory = [];
let currentAgent = null;
let agents = [];
let baseModels = [];
let editingAgent = null;
let isPulling = false;

// 兼容：用于旧入口（app.js）检测是否已加载过拆分脚本
window.__OLLAMA_WEB_BOOTSTRAPPED__ = true;
