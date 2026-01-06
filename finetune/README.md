# 🚀 智能LoRA训练系统

一键式LoRA微调到Ollama导入的完整解决方案，支持智能环境检测、自动文件匹配、实时训练监控。

## 📦 环境准备

### 自动安装（推荐）

**Windows用户**: 直接运行启动脚本，会自动检查和安装所有依赖：
```powershell
.\train.ps1 --menu    # PowerShell脚本（推荐）
```

**macOS/Linux用户**: 
```bash
./train --menu
```

启动脚本会自动：
- ✅ 创建虚拟环境（如果不存在）
- ✅ 激活虚拟环境
- ✅ 检查并安装缺失的依赖
- ✅ 处理编码问题（Windows）

### 手动安装

如果需要手动安装依赖：

**1. 创建虚拟环境（推荐）:**
```bash
python -m venv .venv

# Windows激活
.venv\Scripts\activate

# macOS/Linux激活
source .venv/bin/activate
```

**2. 安装Python依赖:**
```bash
pip install -r requirements.txt
```

**注意**: `requirements.txt` 包含所有必需依赖，包括：
- `torch` - PyTorch深度学习框架（必需）
- `transformers` - HuggingFace模型库（必需）
- `peft` - LoRA参数高效微调（必需）
- `trl` - Transformer强化学习（必需）
- `datasets` - 数据集处理（必需）
- `pyyaml` - YAML配置文件解析（必需）
- `accelerate` - 分布式训练加速

### 🚀 GPU加速（重要！）

**默认安装的是CPU版本的PyTorch，训练会很慢！**

如果你有NVIDIA GPU，启动脚本会自动检测CUDA版本并提示安装对应的PyTorch版本。

**自动检测和安装（推荐）:**

运行启动脚本时，如果检测到CPU版本的PyTorch，脚本会：
1. ✅ 自动检测系统CUDA版本（通过 `nvidia-smi`）
2. ✅ 根据CUDA版本自动选择对应的PyTorch安装命令
3. ✅ 询问是否立即安装CUDA版本的PyTorch

**支持的CUDA版本自动映射:**
- CUDA 12.4 → PyTorch cu124
- CUDA 12.3 → PyTorch cu124（兼容）
- CUDA 12.2 → PyTorch cu121（兼容）
- CUDA 12.1 → PyTorch cu121
- CUDA 12.0 → PyTorch cu121（兼容）
- CUDA 11.8 → PyTorch cu118
- CUDA 11.7 → PyTorch cu118（兼容）

**手动安装（如果自动检测失败）:**

**1. 检查GPU和CUDA版本:**
```powershell
nvidia-smi  # 查看GPU信息和CUDA版本
```

**2. 根据CUDA版本安装:**

**CUDA 12.4/12.3:**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

**CUDA 12.1/12.2/12.0:**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

**CUDA 11.8/11.7:**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**最新稳定版（推荐）:**
访问 https://pytorch.org/get-started/locally/ 获取最新安装命令

**3. 验证GPU可用:**
```python
python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
```

**macOS用户（Apple Silicon）:**
- MPS会自动检测，无需额外安装
- 如果使用Intel Mac，只能使用CPU（会很慢）

如果遇到 `No module named 'yaml'` 或 `No module named 'torch'` 等错误，请运行：
```bash
pip install -r requirements.txt
```

## ⚡ 快速开始

### 🆕 首次使用（推荐）

**Windows用户（最简单）:**
```powershell
# 1. 进入项目目录
cd finetune

# 2. 运行启动脚本（会自动创建环境并安装依赖）
.\train.ps1 --menu

# 脚本会自动：
# - 创建虚拟环境（如果不存在）
# - 安装所有必需依赖（torch, transformers等）
# - 显示交互式菜单
```

**macOS/Linux用户:**
```bash
# 1. 进入项目目录
cd finetune

# 2. 运行启动脚本
./train --menu

# 或直接运行Python脚本（会自动检测环境）
python smart_train.py
```

### 📝 新用户首次运行（自动环境设置）

如果直接运行Python脚本，系统会自动检测并引导环境设置：
```bash
python smart_train.py  # 🎯 自动检测并引导环境设置
```

**日常使用**（统一入口）：

**macOS/Linux:**
```bash
./train                    # 交互式选择角色训练
./train linzhi            # 直接训练林栀角色
./train linzhi --ollama   # 训练并导入Ollama（导入需要 GGUF，脚本会检测并提示）
```

**Windows:**
```powershell
.\train.ps1               # 交互式选择角色训练（推荐）
.\train.ps1 linzhi        # 直接训练林栀角色
.\train.ps1 --menu        # 显示完整菜单
python smart_train.py linzhi  # 直接运行Python脚本
```

## 📁 项目结构

```
finetune/
├── 📄 README.md                    ← 你在这里！
├── 🚀 train                        ← macOS/Linux启动脚本
├── 🚀 train.ps1                    ← Windows PowerShell启动脚本（推荐）
├── 🧠 smart_train.py              ← 智能训练主脚本
├── 🔧 train_lora.py               ← LoRA训练引擎
├── 📄 character_configs.yaml      ← 角色配置文件
├── 📄 requirements.txt            ← Python依赖
│
├── 📂 datasets/                   ← 训练数据
│   ├── linzhi/                   ← 林栀数据集
│   │   ├── train.jsonl           ← 训练数据(450样本)
│   │   └── val.jsonl             ← 验证数据(50样本)
│   └── archive/                  ← 历史数据
├── 📂 out/                       ← 训练输出
└── 📂 .venv/                     ← 虚拟环境
```

## 🎯 核心功能

### 🔥 智能训练系统
- ✅ **智能环境检测**：自动检查Python、依赖、Ollama服务
- 📊 **自动文件匹配**：智能发现和匹配训练数据
- ⏰ **实时进度显示**：训练过程可视化监控
- 🎯 **一键导入Ollama**：训练完成自动导入使用

### 📱 完整功能菜单
```bash
./train --menu          # 完整功能菜单

🚀 智能LoRA训练系统 - 主菜单
1) 🎭 角色训练（智能文件匹配）
2) 📊 数据集管理
3) 🔍 系统状态检查
4) 🤖 Ollama模型管理
5) 🧪 模型测试
```

## 📋 使用指南

### 🎭 可用角色

**林栀（主角色）**: 450训练样本 + 50验证样本
**林栀(测试版)**: 28训练样本，快速测试用

### 🚀 训练流程

**标准训练流程:**

**macOS/Linux:**
```bash
./train linzhi               # 开始训练
```

**Windows:**
```powershell
.\train.ps1 linzhi           # 开始训练
```

**训练完成后会自动显示:**
```
🎉 训练完成！下一步操作
✅ 模型已训练完成：linzhi
📁 文件位置：out/merged_linzhi/

⚠️  注意：模型目前还没有导入到Ollama，无法直接使用

📋 后续选项：
1) 🚀 导入到Ollama（推荐）
2) 📦 稍后导入
3) 🏠 返回主菜单
4) 👋 退出系统
```

**快速训练+导入:**

**macOS/Linux:**
```bash
./train linzhi --ollama      # 训练后自动导入Ollama
```

**Windows:**
```powershell
.\train.ps1 linzhi --ollama  # 训练后自动导入Ollama
```

**快速测试:**

**macOS/Linux:**
```bash
./train linzhi_quick         # 使用28样本快速测试
```

**Windows:**
```powershell
.\train.ps1 linzhi_quick     # 使用28样本快速测试
```

### 🔧 系统管理

**环境检查:**

**macOS/Linux:**
```bash
./train --env-check          # 全面环境诊断
./train --setup             # 环境初始化设置
./train --cache             # 检查模型缓存状态
```

**Windows:**
```powershell
.\train.ps1 --env-check      # 全面环境诊断
.\train.ps1 --setup         # 环境初始化设置
.\train.ps1 --cache         # 检查模型缓存状态
```

**数据管理:**

**macOS/Linux:**
```bash
./train --scan              # 扫描数据集状态
./train --list              # 查看所有角色配置
```

**Windows:**
```powershell
.\train.ps1 --scan           # 扫描数据集状态
.\train.ps1 --list          # 查看所有角色配置
```

## 🛠️ 高级功能

### 💡 环境管理
- **首次运行检测**：自动识别新用户并引导设置
- **依赖自动安装**：智能检测并安装缺失的依赖
- **跨平台支持**：Windows/macOS/Linux全平台兼容
  - Windows: 使用 `train.ps1` PowerShell脚本
  - macOS/Linux: 使用 `train` 脚本
- **问题自动修复**：提供详细的解决方案

### 📦 依赖安装

**完整安装（推荐）:**
```bash
pip install -r requirements.txt
```

**主要依赖包括:**
- `torch` - PyTorch深度学习框架
- `transformers` - HuggingFace模型库
- `peft` - LoRA参数高效微调
- `trl` - Transformer强化学习
- `datasets` - 数据集处理
- `pyyaml` - YAML配置文件解析（必需）
- `accelerate` - 分布式训练加速

**Windows用户注意**: 如果遇到编码问题，请使用 `train.ps1` 脚本，已内置UTF-8编码处理。脚本已优化编码设置，避免中文乱码问题。

### 🎯 训练优化
- **智能参数调整**：根据数据量自动优化训练参数
- **断点续训支持**：支持继续训练已有模型
- **多格式数据支持**：自动识别不同格式的训练数据
- **质量验证**：训练前验证数据格式和质量

### 🤖 Ollama集成
- **一键导入（需要 GGUF）**：训练完成后可导入到 Ollama 使用（脚本会检测是否已生成 `.gguf`）
- **智能命名**：自动生成合适的模型名称
- **参数优化**：自动配置最佳推理参数
- **模型管理**：查看、测试、删除Ollama模型

> 重要：`out/merged_*` 默认是 HuggingFace 格式（`config.json` + `model.safetensors`）。  
> Ollama 的 `FROM` 需要 **GGUF 文件** 或 **Ollama 模型名**，不能可靠直接 `FROM out/merged_*`。  
> 如果你看到模型输出“刷题/选择题/答案”这类离谱内容，通常就是 **Ollama 实际没加载到你的训练权重**。

## ❓ 问题排查

### 常见问题

**数据找不到**: 
- macOS/Linux: `./train --scan`
- Windows: `.\train.ps1 --scan`

**配置问题**: 
- macOS/Linux: `./train --list`
- Windows: `.\train.ps1 --list`

**环境问题**: 
- macOS/Linux: `./train --env-check`
- Windows: `.\train.ps1 --env-check`

**格式错误**: 检查JSONL文件每行都是有效JSON

**依赖缺失**: 
- 如果提示 `No module named 'torch'` 或 `No module named 'yaml'` 等错误
- **解决方案1（推荐）**: 重新运行启动脚本，会自动安装依赖
  ```powershell
  .\train.ps1 --menu
  ```
- **解决方案2**: 手动安装
  ```bash
  pip install -r requirements.txt
  ```

**训练速度慢（CPU模式）**: 
- 如果启动脚本提示"CPU-only PyTorch detected"，说明在使用CPU训练
- **解决方案**: 安装CUDA版本的PyTorch（见上方"GPU加速"部分）
- 检查GPU: `nvidia-smi`
- 安装CUDA PyTorch: 访问 https://pytorch.org/get-started/locally/
- 验证: `python -c "import torch; print(torch.cuda.is_available())"`

**Windows编码问题**: 
- 使用 `train.ps1` 脚本，已自动处理编码问题
- 如果PowerShell提示"找不到命令"，使用 `.\train.ps1` 而不是 `train.ps1`
- 脚本已优化编码设置，避免中文乱码问题

**虚拟环境问题**:
- 启动脚本会自动创建虚拟环境
- 如果手动创建失败，检查Python版本（需要Python 3.10+）
- Windows: `python --version`
- macOS/Linux: `python3 --version`

## 🚨 重要提醒

- **训练完成后要在 Ollama 使用，需要先准备 GGUF**：没有 `.gguf` 时，脚本会提示你先用 `llama.cpp` 的 `convert_hf_to_gguf.py` 转换
- 同时只运行一个训练任务，避免资源冲突
- 训练前运行 `./train --cache` 确认模型已缓存
- 使用 `./train linzhi_quick` 先做快速测试

## 🎯 一句话总结

**用 `./train` 就够了！** 新用户自动引导设置，老用户一键训练导入！

---
**统一入口**: `./train` | **完整功能**: `./train --menu`