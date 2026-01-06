from __future__ import annotations

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="将 LoRA adapter 合并到 base 模型并保存（不重新训练）")
    ap.add_argument("--base_model", type=str, default="Qwen/Qwen2.5-0.5B-Instruct", help="HF repo id 或本地模型目录")
    ap.add_argument("--lora_dir", type=str, default="out/lora", help="LoRA adapter 目录（train_lora.py 的 output_dir）")
    ap.add_argument("--out_dir", type=str, default="out/merged", help="合并后输出目录（HF 格式）")
    return ap.parse_args()


def main() -> None:
    args = parse_args()

    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained(args.base_model, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    base = AutoModelForCausalLM.from_pretrained(args.base_model)
    merged = PeftModel.from_pretrained(base, args.lora_dir).merge_and_unload()

    merged.save_pretrained(str(out_dir), safe_serialization=True)
    tokenizer.save_pretrained(str(out_dir))

    print(f"合并完成：{args.lora_dir} + {args.base_model} -> {out_dir}")


if __name__ == "__main__":
    main()


