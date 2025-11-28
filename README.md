# Ollama Web 面板

一个简洁的 Web 界面，用于管理和使用 Ollama 本地模型。

## 功能特性

✅ 聊天界面 - 无需命令行，直接对话
✅ 模型管理 - 查看、拉取、切换模型
✅ Modelfile 编辑 - 在线查看和创建自定义模型
✅ 流式响应 - 实时显示 AI 回复
✅ 角色扮演优化 - 支持自定义系统提示词

## 快速开始

### 1. 启动服务

#### Windows 系统

**方法 1 - Python（推荐）:**
```bash
cd ollama-web
python server.py
```

**方法 2 - 直接双击:**
双击 `server.py` 文件即可启动

**方法 3 - Node.js:**
```bash
cd ollama-web
npx http-server -p 8080
```

#### macOS 系统

**方法 1 - Python 3（推荐）:**
```bash
cd ollama-web
python3 server.py
```

**方法 2 - Python 内置服务器:**
```bash
cd ollama-web
python3 -m http.server 8080
```

**方法 3 - Node.js:**
```bash
cd ollama-web
npx http-server -p 8080
```

#### Linux 系统

```bash
cd ollama-web
python3 server.py
```

### 2. 访问面板

启动成功后，打开浏览器访问: **http://localhost:8080**

### 3. 确保 Ollama 运行

确保 Ollama 服务在后台运行（默认端口 11434）

**检查 Ollama 是否运行:**
```bash
ollama list
```

**如果未运行，启动 Ollama:**
- Windows: 从开始菜单启动 Ollama，或查看系统托盘图标
- macOS: 从应用程序启动 Ollama，或查看菜单栏图标
- Linux: `ollama serve`

## 使用说明

### 聊天
1. 从侧边栏或顶部下拉框选择模型
2. 在底部输入框输入消息
3. 点击发送或按 Ctrl+Enter

### 拉取新模型
1. 在侧边栏"拉取新模型"输入框输入模型名称
2. 例如: `qwen2.5:7b`, `gemma2:9b`, `llama3.1:8b`
3. 点击"拉取"按钮

### 创建自定义模型（角色扮演）
1. 选择一个基础模型
2. 点击"编辑 Modelfile"
3. 切换到"创建新模型"标签
4. 输入新模型名称和 Modelfile 内容
5. 点击"创建模型"

### Modelfile 示例

```
FROM gemma2:9b

PARAMETER temperature 0.9
PARAMETER top_p 0.95
PARAMETER repeat_penalty 1.1

SYSTEM """
你是一个活泼开朗的AI助手，喜欢用表情符号。
说话风格轻松幽默，但不失专业。
"""
```

## 推荐模型

**中文对话:**
- qwen2.5:7b
- qwen2.5:14b

**角色扮演:**
- nous-hermes2:latest
- dolphin-mistral:latest

**代码助手:**
- deepseek-coder:6.7b
- codellama:7b

## 故障排除

**无法连接到 Ollama:**
- 确保 Ollama 服务正在运行
- 检查端口 11434 是否被占用
- Windows: 查看系统托盘图标
- 命令行测试: `ollama list`

**模型响应慢:**
- 检查 GPU/CPU 使用率
- 尝试更小的模型
- 调整 Modelfile 参数

## 技术栈

- 纯前端实现（HTML + CSS + JavaScript）
- Ollama REST API
- Python 简单 HTTP 服务器
