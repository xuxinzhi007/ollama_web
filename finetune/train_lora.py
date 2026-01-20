from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List

from env_detect import lora_target_modules_for_qwen, plan_environment, pretty_env_summary
from download_progress import progress_indicator


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
    ap.add_argument("--use_qlora", action="store_true", help="使用QLoRA 4bit量化进行训练")
    ap.add_argument("--report_to", type=str, default="none", help="none|tensorboard|wandb 等")
    ap.add_argument("--resume_from_checkpoint", type=str, help="从指定检查点继续训练")

    return ap.parse_args()


def main() -> None:
    args = parse_args()

    # 延迟导入，方便在没装依赖时给更友好的错误
    _require("torch")
    _require("datasets")
    _require("transformers")
    _require("peft")
    _require("trl")
    if args.use_qlora:
        try:
            __import__("bitsandbytes")
        except Exception:
            print("⚠️ 检测到启用 QLoRA，但未找到 bitsandbytes，正在自动安装...")
            result = subprocess.run([sys.executable, "-m", "pip", "install", "bitsandbytes"])
            if result.returncode != 0:
                raise RuntimeError("自动安装 bitsandbytes 失败，请手动执行: pip install bitsandbytes")
        __import__("bitsandbytes")

    import torch
    from datasets import load_dataset
    from peft import LoraConfig
    if args.use_qlora:
        from peft import prepare_model_for_kbit_training
    from transformers import AutoModelForCausalLM, AutoTokenizer
    if args.use_qlora:
        from transformers import BitsAndBytesConfig

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

    # tokenizer & model - 智能缓存检测
    try:
        from model_cache import smart_model_load_message
        smart_model_load_message(args.model_name_or_path)
    except ImportError:
        print(f"\n📥 正在加载模型: {args.model_name_or_path}")
        print(f"💡 如果是第一次使用，需要从网络下载（约500MB-1GB）")

    # 加载tokenizer，简化提示
    print("⏳ 加载 Tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name_or_path, use_fast=True)
    print("✅ Tokenizer 加载完成")
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # device_map 策略：cuda 用 auto；mps/cpu 直接本地加载后 .to(device)
    device_map = "auto" if plan.device == "cuda" else None

    if args.use_qlora:
        if plan.device != "cuda":
            raise RuntimeError("QLoRA 仅支持在 CUDA GPU 上训练，请在有 NVIDIA 显卡的环境中使用 --use_qlora")
        compute_dtype = torch.bfloat16 if plan.dtype == "bf16" else torch.float16
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=compute_dtype,
            bnb_4bit_use_double_quant=True,
        )
        print("⏳ 以 QLoRA 4bit 模式加载模型权重...")
        model = AutoModelForCausalLM.from_pretrained(
            args.model_name_or_path,
            device_map=device_map,
            quantization_config=bnb_config,
        )
        model = prepare_model_for_kbit_training(model)
    else:
        model_kwargs: Dict[str, Any] = {"device_map": device_map}
        if plan.device != "cpu":
            model_kwargs["dtype"] = torch_dtype
        print("⏳ 加载模型权重（这可能需要几分钟）...")
        model = AutoModelForCausalLM.from_pretrained(args.model_name_or_path, **model_kwargs)
    print("✅ 模型权重加载完成")

    if plan.device in ("mps", "cpu") and not args.use_qlora:
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

    # --- 监控回调 ---
    from transformers import TrainerCallback
    import time
    
    class SimpleProgressCallback(TrainerCallback):
        def on_log(self, args, state, control, logs=None, **kwargs):
            """
            自定义进度打印，替代 tqdm 进度条。
            仅在 logging_steps 触发时调用 (当前设置为 10)。
            """
            if state.is_local_process_zero and logs:
                # 提取关键指标，使用 .get 防止某些 step 没有 loss
                loss = logs.get("loss", None)
                lr = logs.get("learning_rate", None)
                epoch = logs.get("epoch", 0.0)
                step = state.global_step
                max_steps = state.max_steps
                
                # 构建输出字符串
                log_parts = [f"🔄 [Step {step}/{max_steps}]"]
                log_parts.append(f"Epoch: {epoch:.2f}")
                
                if loss is not None:
                    log_parts.append(f"Loss: {loss:.4f}")
                if lr is not None:
                    log_parts.append(f"LR: {lr:.2e}")
                    
                print(" | ".join(log_parts))

    class MonitorCallback(TrainerCallback):
        def __init__(self, tokenizer, prompts, model_name="model"):
            self.tokenizer = tokenizer
            self.prompts = prompts
            
            # 创建 logs 目录
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            
            # 生成带时间戳的文件名: logs/20260119-173000_linzhi_monitor.log
            timestamp = time.strftime('%Y%m%d-%H%M%S')
            # 提取纯角色名，去除路径和前缀
            clean_name = Path(model_name).name.replace("lora_", "")
            self.log_file = log_dir / f"{timestamp}_{clean_name}_monitor.log"
            
            # 初始化日志文件
            with open(self.log_file, "w", encoding="utf-8") as f:
                f.write(f"=== 训练监控日志: {clean_name} ===\n")
                f.write(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            print(f"📝 监控日志将写入: {self.log_file}")
            
        def on_step_end(self, args, state, control, model=None, **kwargs):
            # 每 30 步检查一次
            if state.global_step % 30 == 0 and state.global_step > 0:
                self._generate(model, state.global_step)

        def on_epoch_end(self, args, state, control, model=None, **kwargs):
            self._generate(model, f"Epoch {state.epoch}")

        def _generate(self, model, step_info):
            # 准备日志内容 (只保留关键信息，减少废话)
            log_buffer = []
            
            header = f"\n🔍 [{step_info}]"
            print(f"\n{header} ----------------")
            
            log_buffer.append(header)
            
            # 切换到评估模式
            model.eval()
            
            for p in self.prompts:
                try:
                    # 构建消息
                    messages = [{"role": "user", "content": p}]
                    # 使用 chat template
                    text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                    
                    # 编码
                    inputs = self.tokenizer(text, return_tensors="pt").to(model.device)
                    
                    # 生成
                    with torch.no_grad():
                        outputs = model.generate(
                            **inputs, 
                            max_new_tokens=80,  # 减少 token 数以节省空间
                            temperature=0.7,
                            top_p=0.9,
                            do_sample=True,
                            pad_token_id=self.tokenizer.eos_token_id
                        )
                    
                    # 解码
                    response = self.tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()
                    # 压缩空白字符
                    response = " ".join(response.split())
                    
                    # 打印控制台 (保持美观)
                    print(f"🗣️  {p}")
                    print(f"🤖 {response}")
                    print("-" * 20)
                    
                    # 记录到日志 (紧凑格式: User | AI)
                    log_buffer.append(f"Q: {p} | A: {response}")
                    
                except Exception as e:
                    err_msg = f"⚠️ Error: {e}"
                    print(err_msg)
                    log_buffer.append(err_msg)
            
            # 写入文件
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write("\n".join(log_buffer) + "\n")
            except Exception as e:
                print(f"⚠️  写入日志文件失败: {e}")
                
            # 恢复训练模式
            model.train()



    # 根据数据集猜测适合的测试问题
    import random
    
    base_prompts = [
        "你好，你是谁？",
        "你会做什么？",
        "今天天气怎么样？",
        "给我讲个笑话吧。",
        "心情不好怎么办？",
        "你喜欢什么颜色？",
        "虽然不知道说什么，但是想找人聊聊。",
        "你是机器人吗？",
        "你住在哪里呀？",
        "我好累啊，求安慰。",
        "你觉得爱情是什么？",
        "你会写代码吗？",
        "我想去旅行，推荐个地方吧。",
        "如果不开心，你会做什么？"
    ]
    
    linzhi_prompts = [
        "林栀，你在干什么？",
        "林栀，我今天被老板骂了。",
        "林栀，你喜欢我吗？",
        "林栀，我想听你唱歌。",
        "林栀，你是我的女朋友吗？",
        "林栀，你会一直陪着我吗？",
        "林栀，周末要不要一起去看电影？",
        "林栀，你脸红了吗？"
    ]
    
    catgirl_prompts = [
        "主人回来了！",
        "喵喵喵？",
        "把手给我。",
        "我要吃小鱼干！",
        "过来，让我摸摸头。",
        "你是哪里来的小猫咪？"
    ]

    monitor_prompts = []
    # 基础问题随机选 2 个
    monitor_prompts.extend(random.sample(base_prompts, 2))
    
    if "linzhi" in str(args.train_jsonl):
        # 林栀专属问题随机选 2 个
        monitor_prompts.extend(random.sample(linzhi_prompts, 2))
    elif "catgirl" in str(args.train_jsonl):
        # 猫娘专属问题随机选 2 个
        monitor_prompts.extend(random.sample(catgirl_prompts, 2))
    else:
        # 其他情况再补 2 个基础问题
        monitor_prompts.extend(random.sample(base_prompts, 2))

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

        # 对于Qwen模型，确保system消息被正确处理
        # 检查是否包含system消息
        has_system = any(msg.get("role") == "system" for msg in messages)

        try:
            # 尝试使用chat template
            formatted = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)

            # 🔍 Debug: 打印第一条格式化后的数据，让用户放心
            if not hasattr(formatting_func, "has_printed"):
                print("\n" + "="*40)
                print("🔍 [数据格式检查] 实际喂给模型的数据内容 (ChatML格式):")
                print("-" * 20)
                print(formatted[:800])  # 打印前800字符
                print("-" * 20)
                if "<|im_start|>" in formatted:
                    print("✅ 检测到 ChatML 标准标记 (<|im_start|>)，格式正确！")
                else:
                    print("⚠️  未检测到 ChatML 标记，请检查 Tokenizer 配置")
                print("="*40 + "\n")
                formatting_func.has_printed = True

            # 验证system消息是否被包含（简单检查）
            if has_system:
                system_content = next(msg["content"] for msg in messages if msg.get("role") == "system")
                if system_content[:50] not in formatted:
                    print(f"⚠️  警告：system消息可能未被正确处理")

            return formatted
        except Exception as e:
            print(f"⚠️  Chat template处理失败，回退到手动拼接 (Qwen ChatML): {e}")
            # 回退：手动构建 ChatML 格式
            result = ""
            for msg in messages:
                role = msg.get("role", "")
                content = msg.get("content", "")
                # Qwen ChatML 格式
                result += f"<|im_start|>{role}\n{content}<|im_end|>\n"
            
            result += "<|endoftext|>"
            return result
            return result

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
    fp16_flag = (plan.dtype == "fp16") and not use_mps_device and not args.use_qlora
    bf16_flag = (plan.dtype == "bf16") and not use_mps_device and not args.use_qlora
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
        fp16=fp16_flag,
        bf16=bf16_flag,
        use_mps_device=use_mps_device,
        report_to=report_to,
        seed=args.seed,
        dataloader_pin_memory=(plan.device == "cuda"),
        max_seq_length=max_seq_len,
        packing=False,
        resume_from_checkpoint=args.resume_from_checkpoint,
        disable_tqdm=True, # 禁用进度条，防止 IDE 终端缓冲区溢出
    )

    # 如果要从checkpoint恢复，需要先加载LoRA权重
    if args.resume_from_checkpoint:
        print(f"🔄 准备从checkpoint恢复: {args.resume_from_checkpoint}")
        checkpoint_path = Path(args.resume_from_checkpoint)
        if checkpoint_path.exists():
            # 检查checkpoint是否包含LoRA权重
            adapter_files = list(checkpoint_path.glob("adapter_model.*"))
            if adapter_files:
                print(f"✅ 找到LoRA权重文件: {adapter_files[0].name}")
            else:
                print(f"⚠️  警告：checkpoint中未找到LoRA权重文件")
                print(f"   可能无法正确恢复训练状态")
    
    trainer = SFTTrainer(
        model=model,
        args=sft_args,
        train_dataset=ds["train"],
        eval_dataset=None if args.no_eval or "validation" not in ds else ds["validation"],
        processing_class=tokenizer,
        formatting_func=formatting_func,
        peft_config=lora_cfg,
        callbacks=[
            SimpleProgressCallback(),
            MonitorCallback(tokenizer, monitor_prompts, model_name=out_dir.name)
        ],
    )


    try:
        trainer.model.print_trainable_parameters()
    except Exception:
        pass

    # 训练（会自动处理resume_from_checkpoint）
    if args.resume_from_checkpoint:
        print(f"🔄 开始从checkpoint恢复训练...")
        print(f"   如果loss从初始值开始，说明checkpoint可能没有正确加载")
    
    # 显式传入 resume_from_checkpoint，确保 optimizer/scheduler/global_step 等状态被正确恢复
    # （仅在 TrainingArguments/SFTConfig 里设置有时不会触发完整恢复，取决于 transformers/trl 版本）
    trainer.train(resume_from_checkpoint=args.resume_from_checkpoint)

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


