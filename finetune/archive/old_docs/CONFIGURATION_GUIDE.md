# 配置系统使用指南

## 概述

现在系统已经完全去除了硬编码参数，支持灵活的配置管理。你可以通过配置文件或命令行参数来调整所有训练和模型参数。

## 配置文件系统

### 主要配置文件：`config.yaml`

这个文件包含了所有可配置的参数，支持详细的注释和说明：

```yaml
# 基础模型配置
model:
  # 支持的模型（已测试）：
  # - Qwen/Qwen2.5-0.5B-Instruct (默认，轻量快速)
  # - Qwen/Qwen2.5-1.5B-Instruct (更强能力)
  # - Qwen/Qwen2.5-3B-Instruct (高性能)
  # - microsoft/DialoGPT-medium (对话专用)
  # - meta-llama/Llama-3.2-1B-Instruct (Meta模型)
  base_model: "Qwen/Qwen2.5-0.5B-Instruct"
  model_type: "qwen"

# 训练参数
training:
  epochs: 2.0              # 训练轮数
  learning_rate: 2e-4      # 学习率
  warmup_ratio: 0.03       # 预热比例
  weight_decay: 0.0        # 权重衰减
  seed: 42                 # 随机种子

# LoRA 参数
lora:
  rank: 8                  # LoRA rank (8=轻量, 16=平衡, 32=重型)
  alpha: 16                # LoRA alpha (通常是rank的2倍)
  dropout: 0.05            # LoRA dropout

# Ollama 生成参数
ollama:
  temperature: 0.7         # 创造性 (0.1-1.0)
  top_p: 0.9              # 核心采样
  top_k: 40               # 候选词数量
  repeat_penalty: 1.05     # 重复惩罚
  context_length: 4096     # 上下文长度
```

## 如何切换模型

### 方法1：修改配置文件
编辑 `config.yaml` 文件：

```yaml
model:
  base_model: "Qwen/Qwen2.5-1.5B-Instruct"  # 改为你想要的模型
  model_type: "qwen"  # 对应模型类型
```

### 方法2：使用命令行参数
```bash
# 使用不同的基础模型
python train_to_ollama.py --model "Qwen/Qwen2.5-1.5B-Instruct" --ollama_name "my-1.5b-model"

# 使用不同的训练轮数
python train_to_ollama.py --epochs 4.0 --ollama_name "my-deep-model"

# 组合使用
python train_to_ollama.py \
    --model "meta-llama/Llama-3.2-1B-Instruct" \
    --epochs 3.0 \
    --ollama_name "my-llama-model"
```

### 方法3：创建多个配置文件
```bash
# 创建专门的配置文件
cp config.yaml config_llama.yaml
# 编辑 config_llama.yaml 设置为 LLaMA 模型

# 使用特定配置文件训练
python train_to_ollama.py --config config_llama.yaml --ollama_name "my-llama-model"
```

## 支持的模型类型

### Qwen 系列（推荐）
- `Qwen/Qwen2.5-0.5B-Instruct` - 轻量快速，适合快速测试
- `Qwen/Qwen2.5-1.5B-Instruct` - 平衡性能和资源
- `Qwen/Qwen2.5-3B-Instruct` - 高性能，需要更多内存

### LLaMA 系列
- `meta-llama/Llama-3.2-1B-Instruct` - Meta官方小型模型
- `meta-llama/Llama-3.2-3B-Instruct` - Meta官方中型模型

### 其他模型
- `microsoft/DialoGPT-medium` - 专为对话优化
- 其他兼容模型（需要设置正确的model_type）

## 参数调优建议

### 数据量少（< 100条）
```yaml
training:
  epochs: 4.0              # 增加训练轮数
  learning_rate: 1e-4      # 降低学习率
lora:
  rank: 16                 # 增加适配器容量
```

### 数据量多（> 1000条）
```yaml
training:
  epochs: 2.0              # 标准轮数
  learning_rate: 2e-4      # 标准学习率
lora:
  rank: 8                  # 轻量适配器即可
```

### 追求高质量
```yaml
training:
  epochs: 6.0              # 更多轮数
  learning_rate: 5e-5      # 更低学习率
lora:
  rank: 32                 # 大容量适配器
  alpha: 64                # 更强适配
```

## 独立模型目录架构

现在每个模型都有独立的目录：

```
out/
├── lora_{模型名}/          # LoRA适配器文件
├── merged_{模型名}/        # 合并后的完整模型
│   ├── Modelfile          # Ollama导入文件
│   ├── training_info.json # 训练信息
│   ├── model_config.json  # 模型配置快照
│   └── model.safetensors  # 模型权重
```

### 查找 Modelfile
```bash
# 查看你的jjkk模型的Modelfile
cat out/merged_jjkk/Modelfile

# 查看所有生成的模型
ls out/merged_*/
```

## 配置系统API

### ConfigManager类使用
```python
from config_manager import ConfigManager

# 加载配置
config = ConfigManager("config.yaml")

# 获取单个参数
model_name = config.get("model.base_model")
epochs = config.get("training.epochs")

# 获取训练参数组
training_args = config.get_training_args()

# 获取Ollama参数组
ollama_params = config.get_ollama_params()

# 显示当前配置
config.show_config()
```

## 故障排查

### Q: 模型训练失败
**检查**：
1. 配置文件格式是否正确：`python -c "import yaml; yaml.safe_load(open('config.yaml'))"`
2. 模型名称是否支持：检查HuggingFace是否有该模型
3. 内存是否足够：大模型需要更多内存

### Q: 找不到 Modelfile
**位置**：`out/merged_{模型名}/Modelfile`

**检查命令**：
```bash
find out/ -name "Modelfile" -type f
```

### Q: 参数不生效
**优先级**：命令行参数 > 配置文件参数 > 默认参数

**确认当前配置**：
```bash
python train_to_ollama.py --config config.yaml --ollama_name test --help
```

## 高级功能

### 批处理训练
```bash
# 创建多个配置文件训练不同模型
python train_to_ollama.py --config config_assistant.yaml --ollama_name my-assistant
python train_to_ollama.py --config config_translator.yaml --ollama_name my-translator
python train_to_ollama.py --config config_coder.yaml --ollama_name my-coder
```

### 配置模板
```bash
# 复制并修改配置文件
cp config.yaml config_custom.yaml
# 编辑 config_custom.yaml
python train_to_ollama.py --config config_custom.yaml --ollama_name custom-model
```

---

**更新时间**: 2026-01-06
**版本**: 3.0 - 完整配置系统支持