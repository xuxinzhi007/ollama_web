## 目标

- 一套代码同时支持 mac / Windows
- 自动检测：CUDA / MPS / CPU，并给出保守默认训练参数（batch/seq/dtype）
- 用 `Qwen/Qwen2.5-0.5B-Instruct` + LoRA 跑通微调链路（先练小模型，后续可换大）

## 目录说明

- `make_dataset.py`：生成 `data/train.jsonl`、`data/val.jsonl`（默认 300 条，风格：毒舌/温柔/爱追问）
- `env_detect.py`：设备与内存探测 + 默认超参策略
- `train_lora.py`：LoRA 训练入口（保存 adapter，可选 merge）
- `run_mac.sh`：mac 一键（venv + 安装 + 生成数据 + 训练）
- `run_win.ps1`：Windows 一键

## 快速开始（mac）

```bash
cd /Users/admin/Documents/ollama_web/finetune
bash run_mac.sh
```

## 快速开始（Windows PowerShell）

```powershell
cd C:\path\to\ollama_web\finetune
.\run_win.ps1
```

## 常用参数（可覆盖自动默认）

例如你想把 seq 调小，降低 OOM 风险：

```bash
python train_lora.py --max_seq_length 256
```

或强制 batch/累积步数：

```bash
python train_lora.py --per_device_train_batch_size 1 --gradient_accumulation_steps 16
```

## 输出

- LoRA adapter：`out/lora/`
- 训练元信息：`out/lora/run_meta.json`（包含检测到的设备/内存与最终采用的参数）

## 注意

- 首次运行需要下载 pip 依赖与 HF 模型（需要网络）。
- 如果 Windows 有 NVIDIA 且你想用 CUDA Torch，建议按 PyTorch 官方指引安装对应 CUDA 版本的 torch，然后再装其它依赖。


