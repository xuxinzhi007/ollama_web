# 安装 Questionary - 升级菜单体验

## 🎯 什么是 Questionary？

Questionary 是一个现代化的终端交互库，提供：
- ✅ **箭头键选择**：使用 ↑↓ 键选择，无需输入数字
- ✅ **可视化高亮**：当前选项高亮显示
- ✅ **更直观**：看到即可选
- ✅ **跨平台**：macOS 和 Windows 完美支持

## 📦 安装方法

### 方法 1：使用启动脚本（推荐）

启动脚本会自动检测并安装：

**macOS/Linux:**
```bash
cd finetune
./train --menu
```

**Windows:**
```powershell
cd finetune
.\train.ps1 --menu
```

### 方法 2：手动安装

```bash
# 激活虚拟环境（如果使用）
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# 安装 questionary
pip install questionary
```

### 方法 3：重新安装所有依赖

```bash
pip install -r requirements.txt
```

## ✨ 使用体验

### 安装前（传统数字输入）
```
==================================================
🚀 智能LoRA训练系统 - 主菜单
==================================================

📋 按工作流程选择:
1) 🎨 角色开发  - 创建和管理角色
2) 🚀 模型训练  - 训练角色模型
3) 📦 模型部署  - 导入和测试模型
4) 🔧 系统工具  - 环境检查和数据验证
0) 退出

请选择 (0-4): _
```

### 安装后（箭头选择）
```
==================================================
🚀 智能LoRA训练系统 - 主菜单
==================================================

? 请选择功能: (使用↑↓箭头选择，回车确认)
❯ 🎨 角色开发  - 创建和管理角色
  🚀 模型训练  - 训练角色模型
  📦 模型部署  - 导入和测试模型
  🔧 系统工具  - 环境检查和数据验证
  🚪 退出
```

## 🔧 验证安装

运行以下命令检查是否安装成功：

```bash
python3 -c "import questionary; print('✅ Questionary 已安装')"
```

如果显示 "✅ Questionary 已安装"，说明安装成功！

## ❓ 常见问题

### Q: 如果不安装 questionary 会怎样？
A: 系统会自动降级到传统数字输入模式，功能完全不受影响

### Q: 需要重启终端吗？
A: 不需要，安装后直接运行 `./train --menu` 即可

### Q: Windows 支持吗？
A: 完全支持！PowerShell 和 CMD 都可以

### Q: 为什么推荐使用 questionary？
A: 更现代、更直观、更不容易出错（不会输错数字）

## 🚀 开始使用

安装完成后，运行菜单：

**macOS/Linux:**
```bash
./train --menu
```

**Windows:**
```powershell
.\train.ps1 --menu
```

享受全新的箭头选择体验！🎉
