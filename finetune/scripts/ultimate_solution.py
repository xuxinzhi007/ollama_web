#!/usr/bin/env python3
"""
终极 LoRA -> Ollama 解决方案
完全避开 sentencepiece 编译问题，支持批量导入
"""

import argparse
import subprocess
import sys
from pathlib import Path
import tempfile
import json


def run_cmd(cmd: str) -> tuple[int, str]:
    """运行命令"""
    print(f"[执行] {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout.strip())
    if result.returncode != 0 and result.stderr:
        print(f"[错误] {result.stderr.strip()}")
    return result.returncode, result.stdout.strip()


def check_ollama():
    """检查 Ollama 服务"""
    ret, _ = run_cmd("ollama --version")
    if ret != 0:
        print("❌ 请先安装 Ollama: https://ollama.ai")
        return False

    # 检查服务状态
    ret, _ = run_cmd("ollama list")
    if ret != 0:
        print("🔄 启动 Ollama 服务...")
        subprocess.Popen("ollama serve", shell=True)
        import time
        time.sleep(3)

    print("✅ Ollama 服务正常")
    return True


def create_modelfile(merged_dir: Path, model_name: str, system_prompt: str = None) -> str:
    """创建 Modelfile"""

    # 读取配置（如果存在）
    config = {}
    config_path = merged_dir / "config.json"
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)

    # 默认系统提示
    if not system_prompt:
        system_prompt = "你是一个经过专门微调的AI助手。请提供有帮助、准确和友好的回答。"

    return f"""# LoRA 微调模型: {model_name}
# 自动生成的 Modelfile

FROM {merged_dir.absolute()}

# 性能参数
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER repeat_penalty 1.05
PARAMETER num_ctx 4096

# 系统提示
SYSTEM \"\"\"{system_prompt}\"\"\"
"""


def import_to_ollama(merged_dir: str, ollama_name: str, force: bool = False, system_prompt: str = None) -> bool:
    """导入模型到 Ollama"""

    merged_path = Path(merged_dir)
    if not merged_path.exists():
        print(f"❌ 目录不存在: {merged_path}")
        return False

    # 检查模型是否存在
    if not force:
        ret, output = run_cmd(f"ollama list | grep {ollama_name}")
        if ret == 0:
            print(f"⚠️  模型 '{ollama_name}' 已存在，使用 --force 覆盖")
            return False

    # 创建临时 Modelfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='', delete=False) as f:
        content = create_modelfile(merged_path, ollama_name, system_prompt)
        f.write(content)
        modelfile = f.name

    try:
        print(f"📦 导入 {ollama_name}...")
        ret, _ = run_cmd(f"ollama create {ollama_name} -f {modelfile}")

        if ret == 0:
            print(f"✅ 导入成功: {ollama_name}")
            return True
        else:
            print(f"❌ 导入失败")
            return False

    finally:
        Path(modelfile).unlink(missing_ok=True)


def batch_import(base_dir: str = "out") -> list[str]:
    """批量导入所有合并模型"""

    base_path = Path(base_dir)
    if not base_path.exists():
        print(f"❌ 目录不存在: {base_path}")
        return []

    # 查找所有 merged 目录
    merged_dirs = []
    for p in base_path.rglob("*merged*"):
        if p.is_dir() and (p / "config.json").exists():
            merged_dirs.append(p)

    if not merged_dirs:
        print("❌ 未找到合并模型目录")
        return []

    imported = []
    for merged_dir in merged_dirs:
        model_name = f"lora-{merged_dir.name}"
        print(f"\n🔄 处理: {merged_dir}")

        if import_to_ollama(str(merged_dir), model_name):
            imported.append(model_name)

    return imported


def main():
    parser = argparse.ArgumentParser(description="终极 LoRA -> Ollama 导入工具")

    # 模式选择
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--single", type=str, help="单个模型目录路径")
    group.add_argument("--batch", action="store_true", help="批量导入所有模型")

    # 参数
    parser.add_argument("--name", type=str, help="Ollama 模型名称（单个模式必填）")
    parser.add_argument("--force", action="store_true", help="强制覆盖已存在模型")
    parser.add_argument("--system", type=str, help="自定义系统提示")
    parser.add_argument("--base_dir", type=str, default="out", help="批量模式的基础目录")

    args = parser.parse_args()

    print("🚀 终极 LoRA -> Ollama 导入工具")
    print("=" * 50)

    if not check_ollama():
        sys.exit(1)

    try:
        if args.single:
            # 单个导入
            if not args.name:
                print("❌ 单个模式需要指定 --name")
                sys.exit(1)

            success = import_to_ollama(args.single, args.name, args.force, args.system)
            if success:
                print(f"\n🎉 完成! 使用命令测试:")
                print(f"   ollama run {args.name}")
            else:
                sys.exit(1)

        else:
            # 批量导入
            imported = batch_import(args.base_dir)

            if imported:
                print(f"\n🎉 成功导入 {len(imported)} 个模型:")
                for name in imported:
                    print(f"  ✅ {name}")
                print(f"\n🚀 测试命令:")
                for name in imported:
                    print(f"   ollama run {name}")
            else:
                print("❌ 没有成功导入任何模型")
                sys.exit(1)

    except KeyboardInterrupt:
        print("\n⏹️  用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()