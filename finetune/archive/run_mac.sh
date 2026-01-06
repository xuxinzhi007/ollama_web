#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if [[ ! -d ".venv" ]]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt

# 建议把 HF 缓存放到项目目录，方便复制到其它电脑
export HF_HOME="$ROOT/.hf"
MODEL_LOCAL="$HF_HOME/models/Qwen2.5-0.5B-Instruct"
MODEL_REMOTE="Qwen/Qwen2.5-0.5B-Instruct"
MODEL="$MODEL_REMOTE"
if [[ -d "$MODEL_LOCAL" ]]; then
  MODEL="$MODEL_LOCAL"
fi

# 1) 生成数据
python make_dataset.py --out_dir data --n 300 --seed 42 --val_ratio 0.1

# 2) 训练（默认自动探测 CUDA/MPS/CPU）
python train_lora.py \
  --model_name_or_path "$MODEL" \
  --train_jsonl "data/train.jsonl" \
  --val_jsonl "data/val.jsonl" \
  --output_dir "out/lora" \
  --num_train_epochs 2 \
  --learning_rate 2e-4

echo ""
echo "训练完成。LoRA adapter 在: $ROOT/out/lora"


