# 🚀 LoRA 微调到 Ollama 工具包

## 📁 项目结构

```
├── 📄 README.md                 ← 你在这里！
├── 🚀 train_to_ollama.py        ← 🔥 主要工具：实时进度显示
├── 🔧 train_lora.py             ← LoRA训练脚本
├── 🔧 make_dataset.py           ← 数据集生成工具
├── 🔧 env_detect.py             ← 环境检测
├── 📄 requirements.txt          ← Python依赖
├── 📄 ULTIMATE_GUIDE.md         ← 详细文档
│
├── 📂 data/                     ← 训练数据
├── 📂 out/                      ← 训练输出
├── 📂 scripts/                  ← 辅助工具
│   └── ultimate_solution.py     ← 批量管理工具
├── 📂 docs/                     ← 详细文档
└── 📂 archive/                  ← 旧文件存档
```

## ⚡ 快速开始

### 🔥 最简单方式（推荐）

#### 方法一：图形菜单（新手推荐）
```bash
# 1. 激活环境
source .venv/bin/activate

# 2. 运行图形菜单
./quick_start.sh
# 选择 "1) 一键训练新模型" 即可
```

#### 方法二：命令行（熟练用户）
```bash
# 1. 激活环境
source .venv/bin/activate

# 2. 一键训练并导入到Ollama (实时进度显示)
python train_to_ollama.py --ollama_name "my-awesome-bot"

# 3. 测试模型
ollama run my-awesome-bot
```

**就这么简单！现在可以看到实时进度！** 🎉

## ✨ 主要特性

### 🔥 实时进度显示
- ✅ **环境检查**：Python版本、虚拟环境、Ollama服务、GPU状态
- 📊 **数据集验证**：自动检查训练数据，显示数据量、对话风格、训练目标
- ⏰ **时间估算**：训练前显示预计耗时
- 🔄 **实时输出**：训练过程中的实时log输出，不再"卡死"
- 📍 **步骤提示**：清晰显示当前执行到第几步
- 🎉 **完成统计**：显示总耗时和详细的测试命令

### 📱 图形菜单功能
```bash
./quick_start.sh
# 新增功能：
# 1) 一键训练（实时进度）
# 2) 高级训练（自定义参数）
# 3) 批量导入模型
# 4) 查看当前模型
# 5) 测试模型对话
# 6) 清理旧模型
# 7) 系统状态检查 ← 新增
```

## 📋 常用操作

### 🎯 训练新模型（实时进度显示）
```bash
# 基础训练（默认2轮）- 实时显示进度
python train_to_ollama.py --ollama_name "helper-v1"

# 自定义训练轮数 - 支持预估时间
python train_to_ollama.py --ollama_name "helper-v2" --epochs 3.0

# 跳过训练，只导入现有模型 - 详细状态信息
python train_to_ollama.py --ollama_name "helper-v3" --skip_train --merged_dir "out/some_merged"

# 或使用图形菜单
./quick_start.sh
# 选择对应选项，支持高级参数设置
```

### 🔄 批量管理
```bash
# 批量导入所有训练好的模型
python scripts/ultimate_solution.py --batch

# 导入单个模型并自定义
python scripts/ultimate_solution.py --single "out/merged" --name "code-assistant" --system "你是编程专家"
```

### 📊 查看和测试
```bash
# 查看所有模型
ollama list

# 测试模型
echo "你好" | ollama run my-model

# 删除不需要的模型
ollama rm old-model
```

## 🛠️ 高级用法

### 生成自定义数据集
```bash
# 生成300条训练数据
python make_dataset.py --out_dir data --n 300

# 生成1000条数据，验证集比例20%
python make_dataset.py --n 1000 --val_ratio 0.2
```

### 只训练不导入
```bash
# 只进行LoRA训练
python train_lora.py --output_dir "out/my_experiment" --num_train_epochs 2.5

# 后续手动导入
python scripts/ultimate_solution.py --single "out/my_experiment_merged" --name "experiment-bot"
```

## ❓ 常见问题

### Q: 训练失败了怎么办？
```bash
# 检查环境
python env_detect.py

# 重新安装依赖
pip install -r requirements.txt
```

### Q: 模型在哪里？
- 训练输出：`out/` 目录
- Ollama模型：`ollama list` 查看

### Q: 如何删除训练文件？
```bash
# 清理训练输出（保留重要的merged模型）
rm -rf out/lora out/test out/quick_lora

# 完全重新开始
rm -rf out/ data/
```

### Q: 想要不同的模型性格？
在 `train_to_ollama.py` 中修改系统提示，或使用：
```bash
python scripts/ultimate_solution.py --single "out/merged" --name "friendly-bot" \
    --system "你是一个友好的AI助手，总是积极乐观。"
```

## 🚨 重要提醒

1. **虚拟环境**：始终在 `.venv` 环境中运行
2. **磁盘空间**：每个模型约1GB，注意清理
3. **GPU内存**：训练时注意显存使用
4. **备份重要模型**：`out/merged` 包含完整模型

## 📖 更多信息

- 详细教程：`ULTIMATE_GUIDE.md`
- 旧文档：`docs/` 目录
- 问题排查：检查 `archive/` 中的旧脚本

## 🎯 一句话总结

**用 `train_to_ollama.py` 或 `./quick_start.sh` 就够了！** 实时进度显示，再也不用担心"卡死"！

