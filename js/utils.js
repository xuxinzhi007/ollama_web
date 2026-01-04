// 纯工具函数（尽量无 DOM 副作用）

function getModelNameAliases(name) {
    const aliases = new Set();
    if (!name) return [];
    aliases.add(name);
    if (name.endsWith(':latest')) aliases.add(name.slice(0, -':latest'.length));
    if (!name.includes(':')) aliases.add(`${name}:latest`);
    return Array.from(aliases);
}

function ensureSelectHasOption(selectEl, value) {
    if (!selectEl || !value) return;
    const exists = Array.from(selectEl.options || []).some(o => o.value === value);
    if (!exists) {
        const opt = document.createElement('option');
        opt.value = value;
        opt.textContent = value;
        selectEl.appendChild(opt);
    }
}

function parseModelfile(modelfileText) {
    const res = { from: '', system: '', parameters: {} };
    if (typeof modelfileText !== 'string' || !modelfileText.trim()) return res;

    const lines = modelfileText.split('\n');
    const fromLine = lines.find(l => l.trim().toUpperCase().startsWith('FROM '));
    if (fromLine) res.from = fromLine.trim().slice(5).trim();

    // SYSTEM """ ... """
    const sysTriple = modelfileText.match(/SYSTEM\s+"""\s*([\s\S]*?)\s*"""/m);
    if (sysTriple && sysTriple[1] != null) {
        res.system = sysTriple[1];
    } else {
        // SYSTEM "..."
        const sysSingle = modelfileText.match(/SYSTEM\s+"([\s\S]*?)"/m);
        if (sysSingle && sysSingle[1] != null) res.system = sysSingle[1];
    }

    for (const l of lines) {
        const m = l.match(/^\s*PARAMETER\s+(\S+)\s+(.+?)\s*$/i);
        if (!m) continue;
        const k = m[1];
        const vRaw = m[2];
        const vNum = Number(vRaw);
        res.parameters[k] = Number.isFinite(vNum) ? vNum : vRaw;
    }
    return res;
}

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

function isBaseModel(modelName) {
    const baseModelsList = [
        'llama', 'qwen', 'gemma', 'mistral', 'phi', 'deepseek',
        'codellama', 'vicuna', 'orca', 'nous-hermes', 'dolphin',
        'yi', 'mixtral', 'solar', 'openchat', 'starling', 'neural-chat'
    ];
    const lowerName = (modelName || '').toLowerCase();
    return baseModelsList.some(base => lowerName.startsWith(base));
}
