# LoRA 微调快速上手指南

> 📌 **简化版本**：直接可用的命令，无需复杂的脚本

## 🎯 前提条件

- Python 3.10+
- 已激活虚拟环境
- 训练数据已存在

## ⚡ 最简流程

### 1. 进入目录并激活环境

```bash
cd /Users/admin/Documents/ollama_web/finetune
source .venv/bin/activate
```

### 2. 直接开始 LoRA 训练

```bash
# 快速测试（0.1 轮，约10秒）
python train_lora.py \
    --model_name_or_path "Qwen/Qwen2.5-0.5B-Instruct" \
    --output_dir "out/test" \
    --num_train_epochs 0.1 \
    --no_eval

# 正式训练（2轮，约5-10分钟）
python train_lora.py \
    --model_name_or_path "Qwen/Qwen2.5-0.5B-Instruct" \
    --output_dir "out/lora" \
    --num_train_epochs 2
```

### 3. 合并模型（可选）

```bash
# 训练完成后合并 LoRA 到完整模型
python merge_lora.py \
    --base_model "Qwen/Qwen2.5-0.5B-Instruct" \
    --lora_dir "out/lora" \
    --out_dir "out/merged"
```

## 📊 训练结果

- **LoRA 适配器**: `out/lora/` (约10MB)
- **完整模型**: `out/merged/` (约2GB)
- **可训练参数**: 4.4M / 498M (0.88%)

## 🔧 参数说明

### 常用参数
- `--num_train_epochs`: 训练轮次 (建议: 0.1测试, 2正式)
- `--output_dir`: LoRA 输出目录
- `--no_eval`: 跳过验证（加速训练）
- `--learning_rate`: 学习率 (默认: 2e-4)

### 高级参数
- `--merge_and_save`: 训练后自动合并
- `--max_seq_length`: 最大序列长度 (0=自动)
- `--gradient_checkpointing`: 节省显存

## 🚀 完整训练 + 合并

```bash
# 一步完成：训练 + 合并
python train_lora.py \
    --model_name_or_path "Qwen/Qwen2.5-0.5B-Instruct" \
    --output_dir "out/lora" \
    --merged_dir "out/merged" \
    --num_train_epochs 2 \
    --merge_and_save
```

## 📈 系统资源

### 测试环境
- **设备**: Apple Silicon (MPS)
- **内存**: 24GB 统一内存，8.7GB 可用
- **精度**: FP32 (MPS 稳定性)
- **批次**: 1 样本/设备，8 梯度累积

### 性能表现
- **训练速度**: ~2.3秒/步，0.44步/秒
- **训练时间**: 0.1轮约10秒，2轮约5-10分钟
- **显存占用**: 相比全量微调节省50-80%

## ❌ 常见问题

### Q: 训练很慢？
```bash
# 降低序列长度加速
python train_lora.py --max_seq_length 256 --num_train_epochs 2
```

### Q: 内存不够？
```bash
# 开启梯度检查点
python train_lora.py --gradient_checkpointing --num_train_epochs 2
```

### Q: 想快速验证？
```bash
# 超短训练测试流程
python train_lora.py --num_train_epochs 0.01 --no_eval --output_dir "out/quick_test"
```

## 🔄 与复杂脚本的对比

| 方式 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **直接命令** | 简单、快速、可控 | 需要手动设置参数 | ⭐⭐⭐⭐⭐ |
| `run_mac.sh` | 自动化程度高 | 复杂、重复生成数据 | ⭐⭐⭐ |
| `OPERATION.md` | 文档详细 | 步骤繁琐 | ⭐⭐ |

## 🎯 下一步

1. **导出到 Ollama**: 参考 `export_to_ollama.md`
2. **调整参数**: 根据效果调整 `--num_train_epochs`
3. **多轮实验**: 尝试不同的 `--learning_rate`

---

**更新**: 2026-01-06
**测试环境**: macOS Apple Silicon MPS