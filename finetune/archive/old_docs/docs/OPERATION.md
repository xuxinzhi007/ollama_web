## 操作文档（精简版：训练 → Ollama 可用）

### 0) 前置条件

- Python 3.10+（推荐 3.11/3.12）
- 网络可下载 pip 依赖与 HuggingFace 模型（约 1GB 级）
- 想在 Ollama 里看到模型：需要 `ollama` + `llama.cpp`（用于转 GGUF）

> 若你在大陆网络，建议使用镜像或代理；也可以先在一台机器下载好 `.hf/` 目录再拷贝到其它机器。

---

## 1) 在新电脑上初始化（mac）

```bash
cd /path/to/ollama_web/finetune
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip setuptools wheel
python -m pip install -r requirements.txt
```

（可选）生成 300 条测试数据：

```bash
python make_dataset.py --out_dir data --n 300 --seed 42 --val_ratio 0.1
```

---

## 2) 在新电脑上初始化（Windows PowerShell）

```powershell
cd C:\path\to\ollama_web\finetune
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip setuptools wheel
python -m pip install -r requirements.txt
```

> 如果你之前安装过旧依赖并遇到各种兼容性报错，建议强制刷新：
>
> ```bash
> python -m pip install -U -r requirements.txt
> ```

---

## 3) 下载模型（断点续传）

建议把 HF 缓存放在项目目录，方便复制到其它电脑：

### 3.1 设置缓存目录

mac / Linux:

```bash
export HF_HOME="$PWD/.hf"
```

Windows PowerShell:

```powershell
$env:HF_HOME="$PWD\.hf"
```

### 3.2 下载（官方直连）

```bash
hf download Qwen/Qwen2.5-0.5B-Instruct \
  --local-dir "$HF_HOME/models/Qwen2.5-0.5B-Instruct" \
  --resume-download \
  --max-workers 2
```

> 注意：如果你是用 `AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-0.5B-Instruct")` 直连下载的，
> 权重可能被缓存到系统默认目录（如 `~/.cache/huggingface/`），而不是 `$HF_HOME/models/...`。
> 此时要么用上面的 `hf download` 重新下载到 `$HF_HOME`，要么后续命令直接用 repo id（推荐）。

### 3.3 下载（镜像端点，可选）

```bash
export HF_ENDPOINT="https://hf-mirror.com"
hf download Qwen/Qwen2.5-0.5B-Instruct \
  --local-dir "$HF_HOME/models/Qwen2.5-0.5B-Instruct" \
  --resume-download \
  --max-workers 2
```

> 如果遇到 429 限流：建议 `hf auth login`（使用你的 HF token 登录）或改回官方直连/换网络。

---

## 4) 训练（先 smoke test，跑通再加大）

```bash
python train_lora.py \
  --model_name_or_path "$HF_HOME/models/Qwen2.5-0.5B-Instruct" \
  --num_train_epochs 0.2 \
  --max_seq_length 256 \
  --no_eval \
  --output_dir out/lora_smoke
```

> 备注：在部分依赖版本组合下，MPS 不支持 fp16 mixed precision。本项目会在检测到 MPS 时自动回退到 fp32（更稳，但会慢一点）。

产物在：`out/lora_smoke/`（LoRA adapter）

要更明显地“学到风格”，把 epoch/seq 调大：

```bash
python train_lora.py \
  --model_name_or_path "$HF_HOME/models/Qwen2.5-0.5B-Instruct" \
  --num_train_epochs 2 \
  --max_seq_length 256 \
  --output_dir out/lora
```

---

## 5) 为什么 `ollama list` 看不到？

因为你现在得到的是 **LoRA adapter（HF 格式）**，不是 Ollama 可直接加载的 GGUF 模型。
要让 `ollama list` 里出现，需要：**合并权重 → 转 GGUF → `ollama create`**。

---

## 6) 导入 Ollama（最短步骤）

### 6.1 合并 LoRA（生成完整 HF 权重）

不需要再训练一遍，直接合并：

```bash
python merge_lora.py --base_model "Qwen/Qwen2.5-0.5B-Instruct" --lora_dir out/lora --out_dir out/merged
```

产物：`out/merged/`

### 6.2 转 GGUF（需要 llama.cpp）

如果你没装 `llama.cpp`（mac）：

```bash
brew install llama.cpp
```

> 说明：brew 版 `convert_hf_to_gguf.py` 在不同版本上可能出现 Python 依赖不匹配（例如缺少/不兼容的 `gguf` 模块）。
> **最稳的方式**是直接拉取 llama.cpp 源码，只用它的转换脚本（不需要编译）。

```bash
cd /Users/admin/Documents/ollama_web/finetune
git clone https://github.com/ggerganov/llama.cpp.git
PYTHONPATH="$PWD/llama.cpp/gguf-py" python "$PWD/llama.cpp/convert_hf_to_gguf.py" out/merged --outtype f16 --outfile qwen2.5-0.5b-merged.gguf
```

（可选）再量化，体积更小、推理更快：

```bash
QUANT="$LLAMA_PREFIX/bin/llama-quantize"
"$QUANT" qwen2.5-0.5b-merged.gguf qwen2.5-0.5b-merged-q4_k_m.gguf q4_k_m
```

### （备用）源码方式安装 llama.cpp（一定有转换脚本）

```bash
git clone https://github.com/ggerganov/llama.cpp.git
python llama.cpp/convert_hf_to_gguf.py out/merged --outtype f16 --outfile qwen2.5-0.5b-merged.gguf
```

### 6.3 `ollama create`，然后 `ollama list`

在 `finetune/` 下新建 `Modelfile`（示例）：

```text
FROM ./qwen2.5-0.5b-merged-q4_k_m.gguf
```

然后：

```bash
ollama create qwen2.5-0.5b-lora -f Modelfile
ollama list
ollama run qwen2.5-0.5b-lora
```

---

## 7) 把下载好的模型缓存拷贝到其它电脑（最快）

把整目录拷贝：

- `finetune/.hf/`

拷贝到另一台机器同路径，然后设置 `HF_HOME="$PWD/.hf"`，即可跳过下载。


