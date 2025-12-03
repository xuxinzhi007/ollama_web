# Ollama Web 面板 - 开发规则

## 技术栈

- 纯 HTML + CSS + JavaScript（无框架）
- Python HTTP 服务器（托管静态文件）
- Ollama REST API (localhost:11434)
- localStorage（数据持久化）

## 文件结构

```
├── index.html      # 主界面
├── app.js          # 应用逻辑
├── server.py       # HTTP 服务器
└── README.md       # 文档
```

## 代码规范

### JavaScript
- 使用 `async/await` 处理异步
- 驼峰命名法 (camelCase)
- 全局变量用 `let` 声明在顶部
- 事件处理用 `window.functionName` 暴露

### CSS
- 内联样式（`<style>` 标签）
- Flexbox 布局
- 响应式断点：768px（平板）、480px（手机）
- 深色主题：#1a1a1a 背景，#252525 卡片

## API 规范

### Ollama 端点
```
GET  /api/tags      # 获取模型
POST /api/chat      # 聊天（流式）
POST /api/create    # 创建智能体
POST /api/pull      # 拉取模型（流式）
POST /api/show      # 模型详情
DELETE /api/delete  # 删除模型
```

### 流式响应
```javascript
const reader = response.body.getReader();
const decoder = new TextDecoder();
while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value);
    // 处理数据
}
```

## 数据存储

### localStorage 键名
```
chat_${modelName}          # 聊天记录
agent_config_${modelName}  # 智能体配置
recentAgents               # 最近使用
lastAgent                  # 当前选择
```

## UI 规范

### Toast 通知
```javascript
showToast(message, type, duration)
// type: success | error | info | warning
// duration: 默认 3000ms
```

### 错误处理
- 所有 API 调用必须用 try-catch
- 显示友好的错误提示
- 提供重试机制
- 记录错误到控制台

### 按钮规范
- 添加 `title` 属性（悬停提示）
- 使用 SVG 图标 + 文字
- 移动端缩小字体和图标
- 保持触摸目标 ≥ 40px

## 页面状态管理

### 欢迎页面状态
**隐藏**：
- `#inputArea` - 输入框区域
- `#backToHomeBtn` - 首页按钮
- `#keepHistoryLabel` - 保留历史复选框
- `#clearChatBtn` - 清空对话按钮

**显示**：
- `#welcomeScreen` - 欢迎内容
- Tab 导航（快速开始/智能体广场）

### 聊天页面状态
**显示**：
- `#chatArea` - 聊天区域
- `#inputArea` - 输入框区域
- `#backToHomeBtn` - 首页按钮
- `#keepHistoryLabel` - 保留历史复选框
- `#clearChatBtn` - 清空对话按钮

**隐藏**：
- `#welcomeScreen` - 欢迎页面

### 状态切换函数
```javascript
// 进入聊天
selectAgent(agent) {
    welcomeScreen.style.display = 'none';
    chatArea.style.display = 'block';
    inputArea.style.display = 'block';
    backToHomeBtn.style.display = 'flex';
    keepHistoryLabel.style.display = 'flex';
    clearChatBtn.style.display = 'flex';
}

// 返回首页
showWelcomeScreen() {
    welcomeScreen.style.display = 'flex';
    chatArea.style.display = 'none';
    inputArea.style.display = 'none';
    backToHomeBtn.style.display = 'none';
    keepHistoryLabel.style.display = 'none';
    clearChatBtn.style.display = 'none';
}
```

## 智能体规范

### 底座模型识别
```javascript
const baseModels = ['llama', 'qwen', 'gemma', 'mistral', 'phi', 'deepseek'];
function isBaseModel(name) {
    return baseModels.some(base => name.toLowerCase().startsWith(base));
}
```

### Modelfile 格式
```
FROM <底座模型>
PARAMETER temperature <值>
PARAMETER top_p <值>
SYSTEM """<提示词>"""
```

## 图标规范

### 使用 SVG 内联图标
- ❌ 不使用 Emoji（跨平台显示不一致）
- ✅ 使用 SVG 内联（完全可控）
- 使用 `currentColor` 继承父元素颜色
- 使用 `fill` 或 `stroke` 根据图标类型

### 标准尺寸
```
小图标: 12-14px  # 移动端按钮图标
中图标: 16-18px  # 桌面端按钮图标
大图标: 36-48px  # 卡片图标
超大图标: 64-80px # 主视觉图标
```

### 示例
```html
<!-- 填充风格 -->
<svg style="width: 18px; height: 18px;" viewBox="0 0 24 24" fill="currentColor">
    <path d="..."/>
</svg>

<!-- 线条风格 -->
<svg style="width: 18px; height: 18px;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <path d="..."/>
</svg>
```

## 响应式规范

### 桌面端（> 768px）
- 侧边栏固定显示
- 按钮显示完整文字
- 字体 13-16px

### 移动端（≤ 768px）
- 侧边栏滑动显示
- 按钮显示简化文字（11px）
- 图标缩小（12-14px）
- 智能体名称限制宽度（90px）
- 触摸目标 ≥ 40px

### 超小屏（≤ 480px）
- 字体进一步缩小（10px）
- 智能体名称更窄（70px）
- 间距紧凑（3px）

## 性能规范

- 页面加载只调用一次 `loadModels()`
- 全局变量缓存模型列表
- 配置优先从 localStorage 读取
- 使用 ReadableStream 处理流式数据

## 安全规范

### 输入验证
```javascript
// 清理模型名称
modelName = name.toLowerCase()
    .replace(/[^a-z0-9-_]/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
```

## 调试

### 检查连接
```javascript
await checkOllamaConnection()  // 返回 true/false
```

### 查看存储
```javascript
Object.keys(localStorage).forEach(key => {
    console.log(key, localStorage.getItem(key));
});
```

## 部署

```bash
# 本地运行
python3 server.py

# 访问
http://localhost:8080
```

## 关键元素 ID

### 页面容器
- `#welcomeScreen` - 欢迎页面
- `#chatArea` - 聊天区域
- `#inputArea` - 输入框区域

### 头部按钮
- `#backToHomeBtn` - 返回首页按钮
- `#keepHistoryLabel` - 保留历史标签
- `#keepHistory` - 保留历史复选框
- `#clearChatBtn` - 清空对话按钮
- `#currentAgentName` - 当前智能体名称

### Tab 导航
- `.welcome-tab` - Tab 按钮
- `#quickTab` - 快速开始内容
- `#plazaTab` - 智能体广场内容

## 常见问题

### Q: 如何添加新的头部按钮？
1. 在 HTML 中添加按钮元素
2. 给按钮添加唯一 ID
3. 在 `selectAgent()` 中显示按钮
4. 在 `showWelcomeScreen()` 中隐藏按钮
5. 添加移动端响应式样式

### Q: 如何修改响应式断点？
修改 `@media` 查询：
```css
@media (max-width: 768px) { /* 平板 */ }
@media (max-width: 480px) { /* 手机 */ }
```

### Q: 如何调试页面状态？
```javascript
// 检查当前状态
console.log('欢迎页面:', welcomeScreen.style.display);
console.log('聊天区域:', chatArea.style.display);
console.log('当前智能体:', currentAgent);
```

---

**更新**: 2024-12  
**版本**: 2.0
