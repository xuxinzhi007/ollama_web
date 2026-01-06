#!/usr/bin/env python3
"""
一键式 LoRA 训练 -> Ollama 导入
完全避开 sentencepiece/llama.cpp 编译问题
"""

import argparse
import subprocess
import sys
from pathlib import Path
import tempfile
import json
import time
import threading


def run_command(cmd: str, check: bool = True) -> tuple[int, str]:
    """运行命令并返回结果"""
    print(f"[CMD] {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if check and result.returncode != 0:
            print(f"[ERROR] {result.stderr}")
        print(result.stdout)
        return result.returncode, result.stdout.strip()
    except Exception as e:
        print(f"[ERROR] {e}")
        return 1, str(e)


def run_command_realtime(cmd: str) -> int:
    """运行命令并实时显示输出，优化进度条显示"""
    print(f"[CMD] {cmd}")
    print("=" * 60)

    try:
        # 启动进程
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )

        last_progress_line = ""

        # 实时读取输出
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break

            if output:
                line = output.strip()

                # 检测进度条行（包含 % 和 |）
                if '%' in line and '|' in line and '/it]' in line:
                    # 清除上一行进度显示
                    if last_progress_line:
                        print(f"\r{' ' * len(last_progress_line)}", end="")
                    # 显示新的进度
                    print(f"\r🔄 {line}", end="", flush=True)
                    last_progress_line = f"🔄 {line}"
                else:
                    # 非进度行，正常显示
                    if last_progress_line:
                        print()  # 换行
                        last_progress_line = ""
                    print(line)

        # 如果最后有进度行，确保换行
        if last_progress_line:
            print()

        # 等待进程完成
        return_code = process.poll()
        print("=" * 60)
        return return_code

    except Exception as e:
        print(f"[ERROR] {e}")
        return 1


def check_dataset():
    """检查和显示数据集信息"""
    print("📊 检查训练数据...")

    train_file = Path("data/train.jsonl")
    val_file = Path("data/val.jsonl")

    if not train_file.exists():
        print("❌ 训练数据不存在: data/train.jsonl")
        print("💡 请运行: python make_dataset.py --out_dir data --n 300")
        return False

    # 统计数据行数
    try:
        with open(train_file, 'r', encoding='utf-8') as f:
            train_count = sum(1 for _ in f)

        val_count = 0
        if val_file.exists():
            with open(val_file, 'r', encoding='utf-8') as f:
                val_count = sum(1 for _ in f)

        # 读取数据样本分析
        with open(train_file, 'r', encoding='utf-8') as f:
            sample = json.loads(f.readline())

        # 分析数据风格
        styles = set()
        categories = set()

        with open(train_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= 20:  # 只读前20行分析
                    break
                try:
                    data = json.loads(line)
                    if 'style' in data:
                        styles.add(data['style'])
                    if 'category' in data:
                        categories.add(data['category'])
                except:
                    continue

        print(f"✅ 数据集检查完成")
        print(f"   📈 训练数据: {train_count} 条")
        print(f"   📊 验证数据: {val_count} 条")
        print(f"   📝 对话风格: {', '.join(sorted(styles)) if styles else '标准'}")
        print(f"   🏷️  数据类型: {', '.join(sorted(categories)) if categories else '通用'}")

        # 显示数据样本
        if 'messages' in sample and sample['messages']:
            first_msg = sample['messages'][0]
            if first_msg.get('role') == 'system':
                system_prompt = first_msg.get('content', '')[:100]
                print(f"   🎯 训练目标: {system_prompt}{'...' if len(first_msg.get('content', '')) > 100 else ''}")

        return True

    except Exception as e:
        print(f"❌ 读取数据失败: {e}")
        return False


def check_environment():
    """检查环境"""
    print("🔍 检查环境...")

    steps = [
        ("Python版本", "python --version"),
        ("虚拟环境", None),
        ("Ollama服务", "ollama --version"),
        ("PyTorch环境", "python -c 'import torch; print(f\"torch-{torch.__version__}\")'"),
    ]

    for step_name, cmd in steps:
        print(f"   📋 {step_name}...", end=" ")

        if step_name == "虚拟环境":
            if hasattr(sys, 'real_prefix') or sys.base_prefix != sys.prefix:
                print("✅ 已激活")
            else:
                print("⚠️  建议使用虚拟环境")
        else:
            ret, output = run_command(cmd, check=False)
            if ret == 0:
                version = output.split()[0] if output else "正常"
                print(f"✅ {version}")
            else:
                if "ollama" in cmd.lower():
                    print("❌ 请先安装 Ollama")
                    return False
                else:
                    print(f"⚠️  {step_name}异常")

    print("✅ 环境检查完成")
    return True


def estimate_training_time(epochs: float, data_size: int = 300) -> str:
    """估算训练时间"""
    # 基于经验：每个epoch大约2-3分钟，根据数据量调整
    base_time_per_epoch = 2.5  # 分钟
    time_factor = max(1.0, data_size / 300)  # 数据量调整系数
    estimated_minutes = epochs * base_time_per_epoch * time_factor

    if estimated_minutes < 60:
        return f"约 {int(estimated_minutes)} 分钟"
    else:
        hours = int(estimated_minutes // 60)
        minutes = int(estimated_minutes % 60)
        return f"约 {hours} 小时 {minutes} 分钟"


def show_training_info(model_name: str, epochs: float, ollama_name: str, data_info: dict):
    """显示训练信息概览"""
    print("\n📋 训练任务概览")
    print("=" * 50)
    print(f"🤖 基础模型: {model_name}")
    print(f"🔄 训练轮数: {epochs}")
    print(f"📦 目标模型: {ollama_name}")
    print(f"📈 训练数据: {data_info.get('train_count', 0)} 条")
    print(f"📊 验证数据: {data_info.get('val_count', 0)} 条")
    print(f"⏰ 预计时间: {estimate_training_time(epochs, data_info.get('train_count', 300))}")
    print("=" * 50)

    print("\n📍 训练步骤:")
    print("   1️⃣ 环境检查 ✅")
    print("   2️⃣ 数据验证 ✅")
    print("   3️⃣ LoRA训练 ⏳ (实时进度显示)")
    print("   4️⃣ 模型合并 ⏳")
    print("   5️⃣ 导入Ollama ⏳")


def train_lora(model_name: str, epochs: float, output_dir: str, merged_dir: str):
    """训练 LoRA"""
    print(f"\n🚀 开始 LoRA 微调训练...")
    print(f"⏰ 开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    cmd = f"""python train_lora.py \\
        --model_name_or_path "{model_name}" \\
        --output_dir "{output_dir}" \\
        --merged_dir "{merged_dir}" \\
        --num_train_epochs {epochs} \\
        --merge_and_save"""

    print(f"\n💡 提示: 训练过程中可以看到实时进度，进度条会在同一行更新")
    print("📊 如果看到类似 '🔄 85%|████████▌ | 57/68 [01:37<00:16, 1.53s/it]' 说明正常运行\n")

    # 使用实时显示功能
    start_time = time.time()
    ret = run_command_realtime(cmd)

    if ret != 0:
        print("\n❌ 训练失败")
        print("💡 可能的解决方法:")
        print("   - 检查虚拟环境是否正确激活")
        print("   - 检查训练数据是否存在")
        print("   - 查看上面的错误信息")
        return False

    elapsed_time = time.time() - start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)

    print(f"\n✅ 训练完成!")
    print(f"⏰ 完成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🕐 实际耗时: {minutes} 分 {seconds} 秒")

    # 保存训练信息到模型目录
    save_training_info(merged_dir, "训练完成", epochs)

    return True


def save_training_info(merged_dir: str, model_name: str, epochs: float):
    """保存训练时的信息到模型目录"""
    merged_path = Path(merged_dir)
    merged_path.mkdir(parents=True, exist_ok=True)

    # 从训练数据中读取系统提示和其他信息
    system_prompt = "你是一个经过专门微调的AI助手。请提供有帮助、准确和友好的回答。"
    training_info = {
        "model_name": model_name,
        "epochs": epochs,
        "base_model": "Qwen/Qwen2.5-0.5B-Instruct",
        "training_time": time.strftime('%Y-%m-%d %H:%M:%S')
    }

    train_file = Path("data/train.jsonl")
    if train_file.exists():
        try:
            with open(train_file, 'r', encoding='utf-8') as f:
                # 读取第一条数据获取系统提示
                first_line = f.readline().strip()
                if first_line:
                    data = json.loads(first_line)
                    if 'messages' in data and data['messages']:
                        for msg in data['messages']:
                            if msg.get('role') == 'system':
                                system_prompt = msg.get('content', system_prompt)
                                break
                    # 保存训练数据的统计信息
                    if 'style' in data:
                        training_info['style'] = data['style']
                    if 'category' in data:
                        training_info['category'] = data['category']
        except Exception as e:
            print(f"⚠️  无法读取训练数据信息: {e}")

    # 保存训练信息到模型目录
    training_info['system_prompt'] = system_prompt
    info_path = merged_path / "training_info.json"
    with open(info_path, 'w', encoding='utf-8') as f:
        json.dump(training_info, f, indent=2, ensure_ascii=False)

    print(f"💾 训练信息已保存到: {info_path}")


def create_modelfile_for_ollama(merged_dir: Path, model_name: str) -> str:
    """为 Ollama 创建 Modelfile"""

    # 读取保存的训练信息
    training_info_path = merged_dir / "training_info.json"
    system_prompt = "你是一个经过专门微调的AI助手。请提供有帮助、准确和友好的回答。"  # 默认值

    if training_info_path.exists():
        try:
            with open(training_info_path, 'r', encoding='utf-8') as f:
                training_info = json.load(f)
                system_prompt = training_info.get('system_prompt', system_prompt)
                print(f"📋 使用训练时保存的系统提示")
        except Exception as e:
            print(f"⚠️  无法读取训练信息，使用默认系统提示: {e}")
    else:
        print(f"⚠️  未找到训练信息文件，使用默认系统提示")

    modelfile_content = f"""# LoRA 微调模型: {model_name}
# 基于 Qwen2.5-0.5B-Instruct

FROM {merged_dir.absolute()}

# 基础参数
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER repeat_penalty 1.05

# 上下文长度
PARAMETER num_ctx 4096

# 系统提示 - 从训练时保存的信息中读取
SYSTEM \"\"\"{system_prompt}\"\"\"
"""

    return modelfile_content


def import_to_ollama(merged_dir: str, ollama_model_name: str) -> bool:
    """导入到 Ollama"""
    print(f"\n📦 导入模型到 Ollama: {ollama_model_name}")

    merged_path = Path(merged_dir)
    if not merged_path.exists():
        print(f"❌ 合并模型目录不存在: {merged_path}")
        return False

    # 创建标准的 Modelfile
    modelfile_content = create_modelfile_for_ollama(merged_path, ollama_model_name)
    # Ollama 标准格式：必须叫 Modelfile
    modelfile_path = merged_path / "Modelfile"

    # 保存 Modelfile 到模型目录（会覆盖，但每个模型有独立目录）
    with open(modelfile_path, 'w', encoding='utf-8') as f:
        f.write(modelfile_content)

    print("📝 使用的 Modelfile 内容:")
    print("-" * 40)
    print(modelfile_content)
    print("-" * 40)
    print(f"💾 Modelfile 已保存到: {modelfile_path}")

    try:
        # 启动 Ollama 服务（如果未运行）
        print("🔄 检查 Ollama 服务...")
        ret, _ = run_command("ollama list", check=False)
        if ret != 0:
            print("启动 Ollama 服务...")
            subprocess.Popen("ollama serve", shell=True)
            import time
            time.sleep(3)

        # 导入模型
        ret, output = run_command(f"ollama create {ollama_model_name} -f {modelfile_path}")

        if ret == 0:
            print(f"✅ 模型导入成功!")
            print(f"📄 Modelfile 位置: {modelfile_path}")
            return True
        else:
            print(f"❌ 导入失败")
            return False

    except Exception as e:
        print(f"❌ 导入过程出错: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="一键式 LoRA 训练到 Ollama 导入")

    # 训练参数
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-0.5B-Instruct",
                       help="基础模型")
    parser.add_argument("--epochs", type=float, default=2.0,
                       help="训练轮次")
    parser.add_argument("--ollama_name", type=str, required=True,
                       help="在 Ollama 中的模型名称")

    # 目录参数
    parser.add_argument("--lora_dir", type=str, default=None,
                       help="LoRA 适配器输出目录（默认：out/lora_{模型名}）")
    parser.add_argument("--merged_dir", type=str, default=None,
                       help="合并模型输出目录（默认：out/merged_{模型名}）")

    # 选项
    parser.add_argument("--skip_train", action="store_true",
                       help="跳过训练，直接导入已有模型")
    parser.add_argument("--force", action="store_true",
                       help="强制覆盖已存在的 Ollama 模型")

    args = parser.parse_args()

    # 自动生成每个模型的独立目录
    if args.lora_dir is None:
        # 清理模型名称用作目录名
        safe_model_name = args.ollama_name.replace(':', '_').replace('/', '_')
        args.lora_dir = f"out/lora_{safe_model_name}"

    if args.merged_dir is None:
        safe_model_name = args.ollama_name.replace(':', '_').replace('/', '_')
        args.merged_dir = f"out/merged_{safe_model_name}"

    print("🎯 一键式 LoRA 训练到 Ollama 导入")
    print("=" * 50)
    print(f"📂 LoRA 目录: {args.lora_dir}")
    print(f"📂 合并目录: {args.merged_dir}")
    print("=" * 50)

    # 检查环境
    if not check_environment():
        sys.exit(1)

    # 检查并显示数据集信息
    if not args.skip_train:
        if not check_dataset():
            sys.exit(1)

    # 检查模型是否已存在
    if not args.force:
        ret, _ = run_command(f"ollama list | grep {args.ollama_name}", check=False)
        if ret == 0:
            print(f"⚠️  模型 '{args.ollama_name}' 已存在")
            print("💡 使用 --force 强制覆盖，或 --skip_train 跳过训练")
            sys.exit(1)

    try:
        # 准备数据集信息用于显示
        data_info = {}
        if not args.skip_train:
            # 获取数据集统计信息
            train_file = Path("data/train.jsonl")
            val_file = Path("data/val.jsonl")

            if train_file.exists():
                with open(train_file, 'r', encoding='utf-8') as f:
                    data_info['train_count'] = sum(1 for _ in f)

            if val_file.exists():
                with open(val_file, 'r', encoding='utf-8') as f:
                    data_info['val_count'] = sum(1 for _ in f)

        # 显示训练概览
        if not args.skip_train:
            show_training_info(args.model, args.epochs, args.ollama_name, data_info)

        # 步骤 1: 训练（如果需要）
        if not args.skip_train:
            success = train_lora(
                model_name=args.model,
                epochs=args.epochs,
                output_dir=args.lora_dir,
                merged_dir=args.merged_dir
            )
            if not success:
                sys.exit(1)
        else:
            print("⏭️  跳过训练，使用现有模型")

        # 步骤 2: 导入到 Ollama
        success = import_to_ollama(args.merged_dir, args.ollama_name)

        if success:
            print(f"\n🎉 完成! 模型已导入为: {args.ollama_name}")
            print("\n📋 验证:")
            run_command("ollama list")
            print(f"\n🚀 测试运行:")
            print(f"   ollama run {args.ollama_name}")
            print(f"\n💡 提示: 即使删除原始 Qwen 模型，{args.ollama_name} 也会独立存在")

        else:
            print("❌ 导入失败")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⏹️  用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()