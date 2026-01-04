# 任务：拆分 app.js（低影响、多脚本、无构建）

## 目标
- 将单文件 `app.js` 按模块职责拆分为多个脚本文件，降低维护复杂度。
- 不引入构建工具、不改运行方式。
- 保持 `index.html` 内联 `onclick` 与现有 `window.xxx` API 行为不变，确保功能不回归。

## 方案
- 采用传统多 `<script>` 顺序加载（非 ESM）。
- 计划拆分为：`js/state.js`、`js/utils.js`、`js/storage.js`、`js/api.js`、`js/ui.js`、`js/chat.js`、`js/main.js`。
- 关键兼容：函数名/签名/副作用不变；依赖顺序严格；初始化（DOMContentLoaded）放在 `main.js` 最后执行。

## 预期验证
- 可加载模型列表、打开管理面板、拉取/删除底座模型。
- 可创建/删除智能体（含删除当前智能体后返回首页逻辑）。
- 聊天流式响应、历史保存/清空、最近使用恢复正常。
- 控制台无 ReferenceError/undefined。
