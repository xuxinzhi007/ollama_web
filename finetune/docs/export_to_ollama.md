## 目的

把微调结果用于 Ollama，一般推荐路线是：

1) HF 可训练权重上训练（本项目 `train_lora.py`）  
2) （可选）合并 LoRA 到 base，得到完整 HF 权重  
3) 转 GGUF  
4) `ollama create` 导入成新模型

> 说明：`ollama pull` 下来的 GGUF/量化模型通常不直接用于 LoRA 训练；训练与部署建议分开。

## 1) 训练时直接产出 merged（推荐方便后续转换）

```bash
python train_lora.py --merge_and_save --merged_dir out/merged
```

输出目录：`out/merged/`

## 2) 转 GGUF（需要 llama.cpp 工具）

你需要准备 `llama.cpp`（包含 `convert_hf_to_gguf.py`）。示例命令（按你的实际路径调整）：

```bash
python /path/to/llama.cpp/convert_hf_to_gguf.py out/merged --outtype f16 --outfile qwen2.5-0.5b-merged.gguf
```

如果你机器资源有限，可以再做量化（示例，按你 llama.cpp 版本调整）：

```bash
/path/to/llama.cpp/quantize qwen2.5-0.5b-merged.gguf qwen2.5-0.5b-merged-q4_k_m.gguf q4_k_m
```

## 3) 导入 Ollama

创建 `Modelfile`（示例）：

```text
FROM ./qwen2.5-0.5b-merged-q4_k_m.gguf
PARAMETER temperature 0.7
```

然后：

```bash
ollama create qwen2.5-0.5b-lora -f Modelfile
ollama run qwen2.5-0.5b-lora
```

## 常见坑

- 转 GGUF 的脚本/参数会随 llama.cpp 版本变化；如果你告诉我你 llama.cpp 的版本或你用的安装方式（brew/源码），我可以给你更贴合的命令。
- Windows CUDA torch 的安装通常需要走 PyTorch 官方 CUDA wheel 源；脚本仍然通用。


