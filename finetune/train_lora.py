from __future__ import annotations

import argparse
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List

from env_detect import lora_target_modules_for_qwen, plan_environment, pretty_env_summary


def _require(pkg: str):
    try:
        __import__(pkg)
    except Exception as e:
        raise RuntimeError(
            f"缺少依赖 {pkg}。请先安装: pip install -r requirements.txt。原始错误: {type(e).__name__}: {e}"
        ) from e


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model_name_or_path", type=str, default="Qwen/Qwen2.5-0.5B-Instruct")
    ap.add_argument("--train_jsonl", type=str, default="data/train.jsonl")
    ap.add_argument("--val_jsonl", type=str, default="data/val.jsonl")
    ap.add_argument("--output_dir", type=str, default="out/lora")
    ap.add_argument("--merged_dir", type=str, default="out/merged")

    ap.add_argument("--num_train_epochs", type=float, default=2.0)
    ap.add_argument("--learning_rate", type=float, default=2e-4)
    ap.add_argument("--warmup_ratio", type=float, default=0.03)
    ap.add_argument("--weight_decay", type=float, default=0.0)
    ap.add_argument("--logging_steps", type=int, default=10)
    ap.add_argument("--save_steps", type=int, default=200)
    ap.add_argument("--eval_steps", type=int, default=200)
    ap.add_argument("--seed", type=int, default=42)

    ap.add_argument("--max_seq_length", type=int, default=0, help="0 表示自动选择")
    ap.add_argument("--per_device_train_batch_size", type=int, default=0, help="0 表示自动选择")
    ap.add_argument("--gradient_accumulation_steps", type=int, default=0, help="0 表示自动选择")

    ap.add_argument("--lora_r", type=int, default=8)
    ap.add_argument("--lora_alpha", type=int, default=16)
    ap.add_argument("--lora_dropout", type=float, default=0.05)
    ap.add_argument("--target_modules", type=str, default="")  # comma-separated

    ap.add_argument("--merge_and_save", action="store_true", help="训练完成后合并 LoRA 到 base 并保存到 merged_dir")
    ap.add_argument("--no_eval", action="store_true")
    ap.add_argument("--gradient_checkpointing", action="store_true")
    ap.add_argument("--report_to", type=str, default="none", help="none|tensorboard|wandb 等")

    return ap.parse_args()


def main() -> None:
    args = parse_args()

    # 延迟导入，方便在没装依赖时给更友好的错误
    _require("torch")
    _require("datasets")
    _require("transformers")
    _require("peft")
    _require("trl")

    import torch
    from datasets import load_dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer

    try:
        from trl import SFTTrainer
    except Exception as e:
        raise RuntimeError(f"导入 trl.SFTTrainer 失败，请检查 trl 版本。{type(e).__name__}: {e}") from e
    try:
        from trl.trainer.sft_config import SFTConfig
    except Exception as e:
        raise RuntimeError(f"导入 trl.trainer.sft_config.SFTConfig 失败。{type(e).__name__}: {e}") from e

    overrides: Dict[str, Any] = {}
    if args.max_seq_length:
        overrides["max_seq_length"] = args.max_seq_length
    if args.per_device_train_batch_size:
        overrides["per_device_train_batch_size"] = args.per_device_train_batch_size
    if args.gradient_accumulation_steps:
        overrides["gradient_accumulation_steps"] = args.gradient_accumulation_steps

    plan = plan_environment(overrides=overrides)
    print("[env]", pretty_env_summary(plan))

    # CUDA 一些常见加速开关（安全）
    if plan.device == "cuda":
        try:
            torch.backends.cuda.matmul.allow_tf32 = True
        except Exception:
            pass

    # dtype
    # 注意：某些 accelerate/transformers 版本在 MPS 上不允许 fp16 mixed precision（会报错），
    # 所以 env_detect 已默认把 MPS 设为 fp32；这里再做一次兜底。
    torch_dtype = {"bf16": torch.bfloat16, "fp16": torch.float16, "fp32": torch.float32}[plan.dtype]

    # tokenizer & model
    tokenizer = AutoTokenizer.from_pretrained(args.model_name_or_path, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # device_map 策略：cuda 用 auto；mps/cpu 直接本地加载后 .to(device)
    device_map = "auto" if plan.device == "cuda" else None
    # transformers 新版本逐步将 torch_dtype 参数迁移为 dtype
    model_kwargs: Dict[str, Any] = {"device_map": device_map}
    if plan.device != "cpu":
        model_kwargs["dtype"] = torch_dtype
    model = AutoModelForCausalLM.from_pretrained(args.model_name_or_path, **model_kwargs)

    if plan.device in ("mps", "cpu"):
        model.to(plan.device)

    if args.gradient_checkpointing:
        model.gradient_checkpointing_enable()
        model.config.use_cache = False

    # LoRA
    if args.target_modules.strip():
        target_modules = tuple(x.strip() for x in args.target_modules.split(",") if x.strip())
    else:
        target_modules = lora_target_modules_for_qwen()

    lora_cfg = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=list(target_modules),
    )

    # dataset
    train_path = str(Path(args.train_jsonl))
    val_path = str(Path(args.val_jsonl))
    data_files = {"train": train_path}
    if not args.no_eval and Path(val_path).exists():
        data_files["validation"] = val_path

    ds = load_dataset("json", data_files=data_files)

    def formatting_func(example: Dict[str, Any]) -> str:
        messages: List[Dict[str, str]] = example.get("messages") or []
        if not messages:
            # 兼容 instruction/input/output 的简易格式（如果用户未来换数据）
            inst = (example.get("instruction") or "").strip()
            inp = (example.get("input") or "").strip()
            out = (example.get("output") or "").strip()
            user = inst + ("\n\n" + inp if inp else "")
            messages = [{"role": "user", "content": user}, {"role": "assistant", "content": out}]
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)

    # training args
    per_device_bs = int(plan.defaults["per_device_train_batch_size"])
    grad_accum = int(plan.defaults["gradient_accumulation_steps"])
    max_seq_len = int(plan.defaults["max_seq_length"])

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    eval_strategy = "no" if args.no_eval else "steps"
    report_to = None if args.report_to == "none" else [args.report_to]

    # TRL 0.15.x：通过 SFTConfig 传递 max_seq_length/packing 等参数
    use_mps_device = plan.device == "mps"
    sft_args = SFTConfig(
        output_dir=str(out_dir),
        num_train_epochs=args.num_train_epochs,
        learning_rate=args.learning_rate,
        warmup_ratio=args.warmup_ratio,
        weight_decay=args.weight_decay,
        per_device_train_batch_size=per_device_bs,
        gradient_accumulation_steps=grad_accum,
        logging_steps=args.logging_steps,
        save_steps=args.save_steps,
        eval_strategy=eval_strategy,
        eval_steps=args.eval_steps if not args.no_eval else None,
        save_total_limit=2,
        lr_scheduler_type="cosine",
        optim="adamw_torch",
        # accelerate 对 MPS 的 mixed precision 支持在不同版本里差异较大；为稳定起见，MPS 强制关闭 fp16/bf16
        fp16=(plan.dtype == "fp16") and not use_mps_device,
        bf16=(plan.dtype == "bf16") and not use_mps_device,
        use_mps_device=use_mps_device,
        report_to=report_to,
        seed=args.seed,
        dataloader_pin_memory=(plan.device == "cuda"),
        max_seq_length=max_seq_len,
        packing=False,
    )

    trainer = SFTTrainer(
        model=model,
        args=sft_args,
        train_dataset=ds["train"],
        eval_dataset=None if args.no_eval or "validation" not in ds else ds["validation"],
        processing_class=tokenizer,
        formatting_func=formatting_func,
        peft_config=lora_cfg,
    )
    try:
        trainer.model.print_trainable_parameters()
    except Exception:
        pass

    trainer.train()

    # 保存 LoRA adapter
    trainer.model.save_pretrained(str(out_dir))
    tokenizer.save_pretrained(str(out_dir))

    # 记录环境/超参
    meta = {
        "env_plan": asdict(plan),
        "args": vars(args),
        "resolved": {"per_device_train_batch_size": per_device_bs, "gradient_accumulation_steps": grad_accum, "max_seq_length": max_seq_len},
    }
    (out_dir / "run_meta.json").write_text(__import__("json").dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.merge_and_save:
        merged_dir = Path(args.merged_dir)
        merged_dir.mkdir(parents=True, exist_ok=True)
        merged = trainer.model.merge_and_unload()
        merged.save_pretrained(str(merged_dir), safe_serialization=True)
        tokenizer.save_pretrained(str(merged_dir))
        (merged_dir / "run_meta.json").write_text(__import__("json").dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"完成：LoRA 输出 -> {out_dir}")
    if args.merge_and_save:
        print(f"完成：Merged 输出 -> {args.merged_dir}")


if __name__ == "__main__":
    # 让 Windows 控制台输出 UTF-8 更稳一点
    try:
        os.environ.setdefault("PYTHONUTF8", "1")
    except Exception:
        pass
    main()


