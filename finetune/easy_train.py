#!/usr/bin/env python3
"""
🎯 简化版 LoRA 训练脚本
一个文件搞定：数据准备 -> 训练 -> 导出到 Ollama

用法：
  python easy_train.py --name "my-model"
  python easy_train.py --name "linzhi" --data data/train.jsonl
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

# 设置环境变量，启用 HuggingFace 下载进度条
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
os.environ["TRANSFORMERS_VERBOSITY"] = "info"


def print_step(step: int, total: int, msg: str):
    """打印步骤"""
    print(f"\n{'='*50}")
    print(f"📍 步骤 {step}/{total}: {msg}")
    print(f"{'='*50}\n")


def check_data(data_path: str) -> dict:
    """检查训练数据"""
    path = Path(data_path)
    if not path.exists():
        return {"ok": False, "error": f"文件不存在: {data_path}"}
    
    count = 0
    sample = None
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if count == 0:
                sample = json.loads(line.strip())
            count += 1
    
    return {"ok": True, "count": count, "sample": sample}


def download_model(model_name: str):
    """下载模型（优先使用本地缓存）"""
    print(f"📥 检查模型: {model_name}")
    
    try:
        from huggingface_hub import snapshot_download, try_to_load_from_cache
        
        # 先检查本地是否已有缓存
        try:
            cache_dir = snapshot_download(
                repo_id=model_name,
                local_files_only=True,  # 只用本地
            )
            print(f"✅ 使用本地缓存: {cache_dir}")
            return True
        except Exception:
            pass
        
        # 本地没有，需要下载
        print(f"💡 本地没有缓存，开始下载...")
        print(f"⏳ 首次下载需要一些时间，请耐心等待...\n")
        
        cache_dir = snapshot_download(
            repo_id=model_name,
            resume_download=True,
        )
        print(f"✅ 模型已下载到: {cache_dir}")
        return True
        
    except Exception as e:
        print(f"⚠️  检查失败，直接加载试试: {e}")
        return False


def train(
    model_name: str,
    data_path: str,
    output_name: str,
    epochs: float = 3.0,
    lora_rank: int = 16,
    learning_rate: float = 1e-4,
):
    """执行训练"""
    
    # 延迟导入
    print("📦 加载依赖库...")
    import torch
    from datasets import load_dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from trl import SFTTrainer
    from trl.trainer.sft_config import SFTConfig
    
    # 检测设备
    if torch.cuda.is_available():
        device = "cuda"
        dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
        print(f"🎮 使用 CUDA GPU")
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        device = "mps"
        dtype = torch.float32  # MPS 用 fp32 更稳定
        print(f"🍎 使用 Apple MPS")
    else:
        device = "cpu"
        dtype = torch.float32
        print(f"💻 使用 CPU（会比较慢）")
    
    # 加载 tokenizer
    print(f"\n📝 加载 Tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    print("✅ Tokenizer 加载完成")
    
    # 加载模型
    print(f"\n🤖 加载模型: {model_name}")
    print("⏳ 这可能需要几分钟...")
    
    model_kwargs = {}
    if device == "cuda":
        model_kwargs["device_map"] = "auto"
        model_kwargs["torch_dtype"] = dtype
    
    model = AutoModelForCausalLM.from_pretrained(model_name, **model_kwargs)
    
    if device in ("mps", "cpu"):
        model.to(device)
    
    print("✅ 模型加载完成")
    
    # LoRA 配置
    lora_config = LoraConfig(
        r=lora_rank,
        lora_alpha=lora_rank * 2,
        lora_dropout=0.1,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    )
    
    # 加载数据
    print(f"\n📊 加载训练数据: {data_path}")
    ds = load_dataset("json", data_files={"train": data_path})
    print(f"✅ 加载了 {len(ds['train'])} 条数据")
    
    # 格式化函数
    def formatting_func(example):
        messages = example.get("messages", [])
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
    
    # 训练配置
    output_dir = Path(f"out/lora_{output_name}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 根据设备调整参数
    if device == "cuda":
        batch_size, grad_accum, max_len = 4, 2, 512
    elif device == "mps":
        batch_size, grad_accum, max_len = 1, 8, 512
    else:
        batch_size, grad_accum, max_len = 1, 16, 256
    
    sft_config = SFTConfig(
        output_dir=str(output_dir),
        num_train_epochs=epochs,
        learning_rate=learning_rate,
        warmup_ratio=0.1,
        weight_decay=0.01,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=grad_accum,
        logging_steps=10,
        save_steps=500,
        save_total_limit=2,
        fp16=(dtype == torch.float16) and device == "cuda",
        bf16=(dtype == torch.bfloat16) and device == "cuda",
        use_mps_device=(device == "mps"),
        max_seq_length=max_len,
        packing=False,
        report_to=None,
    )
    
    # 创建训练器
    trainer = SFTTrainer(
        model=model,
        args=sft_config,
        train_dataset=ds["train"],
        processing_class=tokenizer,
        formatting_func=formatting_func,
        peft_config=lora_config,
    )
    
    try:
        trainer.model.print_trainable_parameters()
    except:
        pass
    
    # 开始训练
    print(f"\n🚀 开始训练...")
    print(f"   轮数: {epochs}")
    print(f"   学习率: {learning_rate}")
    print(f"   LoRA rank: {lora_rank}")
    print(f"   批次大小: {batch_size} x {grad_accum} = {batch_size * grad_accum}")
    
    start_time = time.time()
    trainer.train()
    elapsed = time.time() - start_time
    
    print(f"\n✅ 训练完成！耗时: {int(elapsed//60)}分{int(elapsed%60)}秒")
    
    # 保存
    trainer.model.save_pretrained(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))
    
    # 合并模型
    print(f"\n🔀 合并 LoRA 到基础模型...")
    merged_dir = Path(f"out/merged_{output_name}")
    merged_dir.mkdir(parents=True, exist_ok=True)
    
    merged = trainer.model.merge_and_unload()
    merged.save_pretrained(str(merged_dir), safe_serialization=True)
    tokenizer.save_pretrained(str(merged_dir))
    
    print(f"✅ 合并完成: {merged_dir}")
    
    return str(merged_dir)


def export_to_ollama(merged_dir: str, ollama_name: str, system_prompt: str = None):
    """导出到 Ollama"""
    import subprocess
    
    merged_path = Path(merged_dir)
    
    # 默认系统提示
    if system_prompt is None:
        # 尝试从训练数据读取
        train_file = Path("data/train.jsonl")
        if train_file.exists():
            with open(train_file, 'r', encoding='utf-8') as f:
                data = json.loads(f.readline())
                for msg in data.get("messages", []):
                    if msg.get("role") == "system":
                        system_prompt = msg.get("content", "")
                        break
        
        if not system_prompt:
            system_prompt = "你是一个有帮助的AI助手。"
    
    # 创建 Modelfile
    modelfile = f'''FROM {merged_path.absolute()}

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER repeat_penalty 1.1
PARAMETER num_ctx 2048

SYSTEM """{system_prompt}"""
'''
    
    modelfile_path = merged_path / "Modelfile"
    with open(modelfile_path, 'w', encoding='utf-8') as f:
        f.write(modelfile)
    
    print(f"📝 Modelfile 已创建: {modelfile_path}")
    
    # 导入到 Ollama
    print(f"\n📦 导入到 Ollama: {ollama_name}")
    result = subprocess.run(
        f"ollama create {ollama_name} -f {modelfile_path}",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(f"✅ 导入成功！")
        print(f"\n🎉 完成！运行以下命令测试：")
        print(f"   ollama run {ollama_name}")
        return True
    else:
        print(f"❌ 导入失败: {result.stderr}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="🎯 简化版 LoRA 训练",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python easy_train.py --name linzhi
  python easy_train.py --name linzhi --data data/train.jsonl --epochs 5
  python easy_train.py --name linzhi --model Qwen/Qwen2.5-0.5B
        """
    )
    
    parser.add_argument("--name", required=True, help="模型名称（用于 Ollama）")
    parser.add_argument("--data", default="datasets/linzhi/train.jsonl", help="训练数据路径")
    parser.add_argument("--model", default="Qwen/Qwen2.5-0.5B", help="基础模型")
    parser.add_argument("--epochs", type=float, default=3.0, help="训练轮数")
    parser.add_argument("--rank", type=int, default=16, help="LoRA rank")
    parser.add_argument("--lr", type=float, default=1e-4, help="学习率")
    parser.add_argument("--skip-train", action="store_true", help="跳过训练，直接导出")
    
    args = parser.parse_args()
    
    print("🎯 简化版 LoRA 训练")
    print("=" * 50)
    print(f"📦 模型名称: {args.name}")
    print(f"🤖 基础模型: {args.model}")
    print(f"📊 训练数据: {args.data}")
    print(f"🔄 训练轮数: {args.epochs}")
    print("=" * 50)
    
    total_steps = 4
    
    # 步骤 1: 检查数据
    print_step(1, total_steps, "检查训练数据")
    data_info = check_data(args.data)
    if not data_info["ok"]:
        print(f"❌ {data_info['error']}")
        print(f"💡 请先准备训练数据，或运行: python generate_linzhi_data.py")
        sys.exit(1)
    print(f"✅ 找到 {data_info['count']} 条训练数据")
    
    merged_dir = f"out/merged_{args.name}"
    
    if not args.skip_train:
        # 步骤 2: 下载模型
        print_step(2, total_steps, "下载/加载模型")
        download_model(args.model)
        
        # 步骤 3: 训练
        print_step(3, total_steps, "LoRA 训练")
        merged_dir = train(
            model_name=args.model,
            data_path=args.data,
            output_name=args.name,
            epochs=args.epochs,
            lora_rank=args.rank,
            learning_rate=args.lr,
        )
    else:
        print_step(2, total_steps, "跳过下载")
        print_step(3, total_steps, "跳过训练")
        if not Path(merged_dir).exists():
            print(f"❌ 合并模型不存在: {merged_dir}")
            sys.exit(1)
    
    # 步骤 4: 导出到 Ollama
    print_step(4, total_steps, "导出到 Ollama")
    export_to_ollama(merged_dir, args.name)
    
    print("\n" + "=" * 50)
    print("🎉 全部完成！")
    print("=" * 50)


if __name__ == "__main__":
    main()
