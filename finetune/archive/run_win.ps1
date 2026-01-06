$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

if (-not (Test-Path ".venv")) {
  python -m venv .venv
}

& .\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt

# 建议把 HF 缓存放到项目目录，方便复制到其它电脑
$env:HF_HOME="$root\.hf"
$modelLocal = Join-Path $env:HF_HOME "models\Qwen2.5-0.5B-Instruct"
$modelRemote = "Qwen/Qwen2.5-0.5B-Instruct"
$model = $modelRemote
if (Test-Path $modelLocal) { $model = $modelLocal }

# 1) 生成数据
python make_dataset.py --out_dir data --n 300 --seed 42 --val_ratio 0.1

# 2) 训练（默认自动探测 CUDA/MPS/CPU）
python train_lora.py `
  --model_name_or_path "$model" `
  --train_jsonl "data/train.jsonl" `
  --val_jsonl "data/val.jsonl" `
  --output_dir "out/lora" `
  --num_train_epochs 2 `
  --learning_rate 2e-4

Write-Host ""
Write-Host "训练完成。LoRA adapter 在: $root\out\lora"


