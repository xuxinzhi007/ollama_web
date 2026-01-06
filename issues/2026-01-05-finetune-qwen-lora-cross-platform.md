## 背景

- 目标：一套训练代码在 mac / Windows 两端可运行，自动检测 CUDA/MPS/CPU，并根据可获得的显存/内存信息自动给出较稳的默认训练参数。
- 练习模型：`Qwen/Qwen2.5-0.5B-Instruct`
- 训练方法：LoRA（PEFT）+ SFT（TRL）
- 数据：先生成 300 条通用但具备“毒舌/温柔/爱追问”个性的数据集（JSONL），用于跑通训练链路。

## 计划（执行步骤）

1. 在项目根目录新增 `finetune/` 子目录，包含：
   - `env_detect.py`：设备/显存/内存检测与默认超参策略
   - `make_dataset.py`：生成 `finetune/data/train.jsonl`、`finetune/data/val.jsonl`（9:1 切分）
   - `train_lora.py`：跨平台训练入口（LoRA + SFT），保存 adapter，并支持可选 merge
   - `requirements.txt`：依赖列表
   - `run_mac.sh`、`run_win.ps1`：一键运行脚本
   - `README_finetune.md`：最短上手说明
   - `export_to_ollama.md`：训练完成后导出/转换并导入 Ollama 的说明
2. 本地做脚本语法自检（`python -m py_compile ...`）。
3. 如需“真正跑通训练”，需要网络权限下载 pip 依赖与 HF 模型（后续执行时请求 `network` 权限）。

## 关键命令（mac）

```bash
cd /Users/admin/Documents/ollama_web/finetune
bash run_mac.sh
```

## 关键命令（Windows PowerShell）

```powershell
cd C:\path\to\ollama_web\finetune
.\run_win.ps1
```



