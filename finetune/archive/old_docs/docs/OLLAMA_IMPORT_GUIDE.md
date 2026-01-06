# 🚀 完全避开 sentencepiece 编译问题 - Ollama 导入指南

> **终极解决方案**：零编译、零依赖，直接使用 Ollama 原生能力导入 LoRA 模型

## ❌ 问题背景

```bash
ERROR: Failed building wheel for sentencepiece
subprocess.CalledProcessError: Command ['./build_bundled.sh', '0.1.99'] returned non-zero exit status 127
```

这是 macOS 下常见的编译错误，特别是 Apple Silicon 机器。传统解决方案需要安装大量编译依赖，容易失败。

## ✅ 完美解决方案

**核心思路**：完全绕开 `sentencepiece`/`llama.cpp` 编译，直接用 Ollama 原生能力完成模型转换和导入。

### 🎯 方案优势

- ✅ **零编译**: 无需 sentencepiece/llama.cpp
- ✅ **零手动**: 全自动生成 Modelfile
- ✅ **零依赖**: 只需要 Ollama
- ✅ **模型独立**: 删除原模型不影响导入的模型
- ✅ **一键完成**: 训练到导入全流程

## 🚀 使用方法

### 方法 1: 一键式训练+导入（推荐）

```bash
cd /Users/admin/Documents/ollama_web/finetune
source .venv/bin/activate

# 一键完成：训练 -> 合并 -> 导入 Ollama
python train_to_ollama.py --ollama_name "my-qwen-lora"
```

**参数说明**:
- `--ollama_name`: 在 Ollama 中的模型名称（必填）
- `--epochs`: 训练轮次（默认2）
- `--force`: 强制覆盖已存在模型

### 方法 2: 分步执行

```bash
# 1. 训练并合并（你已经会的）
python train_lora.py \\
    --model_name_or_path "Qwen/Qwen2.5-0.5B-Instruct" \\
    --output_dir "out/lora" \\
    --merged_dir "out/merged" \\
    --num_train_epochs 2 \\
    --merge_and_save

# 2. 导入到 Ollama
python auto_import_ollama.py \\
    --merged_dir "out/merged" \\
    --model_name "my-qwen-lora"
```

### 方法 3: 超快速测试

```bash
# 快速测试（0.1轮训练，约10秒）
python train_to_ollama.py \\
    --ollama_name "qwen-test" \\
    --epochs 0.1
```

## 📋 完整示例

```bash
cd /Users/admin/Documents/ollama_web/finetune
source .venv/bin/activate

# 训练一个定制化的助手模型
python train_to_ollama.py \\
    --ollama_name "my-assistant" \\
    --epochs 2 \\
    --lora_dir "out/assistant_lora" \\
    --merged_dir "out/assistant_merged"

# 完成后测试
ollama run my-assistant
```

## 🔧 自动生成的 Modelfile 示例

脚本会自动生成如下 Modelfile（无需手动创建）：

```dockerfile
# LoRA 微调模型: my-assistant
# 基于 Qwen2.5-0.5B-Instruct

FROM /Users/admin/Documents/ollama_web/finetune/out/assistant_merged

# 基础参数
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER repeat_penalty 1.05
PARAMETER num_ctx 4096

# 系统提示
SYSTEM \"\"\"你是一个经过专门微调的AI助手。请提供有帮助、准确和友好的回答。\"\"\"
```

## 📊 流程说明

### 自动化流程
1. **训练 LoRA** → `out/lora/` (17MB 适配器)
2. **合并模型** → `out/merged/` (1.8GB 完整模型)
3. **生成 Modelfile** → 自动创建配置
4. **导入 Ollama** → `ollama create` 完成导入
5. **清理临时文件** → 自动清理

### 文件大小对比
- **LoRA 适配器**: ~17MB
- **合并模型**: ~1.8GB
- **Ollama 模型**: ~1.8GB (独立存储)

## 🎯 验证结果

```bash
# 检查模型列表
ollama list

# 输出示例:
NAME                ID              SIZE    MODIFIED
my-assistant        abc123def456    1.8GB   2 minutes ago

# 测试运行
ollama run my-assistant
```

## 💡 常见问题

### Q: 还是遇到编译问题？
A: 本方案完全不涉及编译，如果还有问题可能是其他依赖。

### Q: 模型会占用双倍空间吗？
A: 不会。Ollama 导入后，可以删除 `out/merged/` 目录节省空间。

### Q: 删除原 Qwen 模型会影响吗？
A: 不会。导入的模型是完全独立的副本。

### Q: 如何修改系统提示词？
A: 修改 `train_to_ollama.py` 中的 `SYSTEM` 部分，或手动创建 Modelfile。

### Q: 可以导入多个模型吗？
A: 可以，每次用不同的 `--ollama_name` 即可。

## 🚀 下一步

```bash
# 创建多个专门化模型
python train_to_ollama.py --ollama_name "coding-assistant" --epochs 3
python train_to_ollama.py --ollama_name "writing-helper" --epochs 2
python train_to_ollama.py --ollama_name "translator" --epochs 1.5

# 然后选择使用
ollama run coding-assistant    # 编程助手
ollama run writing-helper      # 写作助手
ollama run translator          # 翻译助手
```

---

**更新**: 2026-01-06
**测试环境**: macOS Apple Silicon + Ollama
**状态**: ✅ 完全解决 sentencepiece 编译问题