#!/usr/bin/env python3
"""
自动导入 LoRA 训练结果到 Ollama
完全避开 sentencepiece 编译问题
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
import tempfile
import shutil


def run_command(cmd: str, check: bool = True) -> tuple[int, str]:
    """运行命令并返回结果"""
    print(f"[CMD] {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if check and result.returncode != 0:
            print(f"[ERROR] 命令执行失败: {cmd}")
            print(f"[ERROR] {result.stderr}")
            return result.returncode, result.stderr
        return result.returncode, result.stdout.strip()
    except Exception as e:
        print(f"[ERROR] 执行命令时出错: {e}")
        return 1, str(e)


def check_ollama():
    """检查 Ollama 是否可用"""
    ret, _ = run_command("ollama --version", check=False)
    if ret != 0:
        print("❌ 请先安装 Ollama: https://ollama.ai")
        return False

    # 检查 Ollama 服务是否运行
    ret, _ = run_command("ollama list", check=False)
    if ret != 0:
        print("🔄 启动 Ollama 服务...")
        subprocess.Popen("ollama serve", shell=True)
        import time
        time.sleep(3)

    return True


def create_modelfile(merged_dir: Path, model_name: str) -> str:
    """自动创建 Modelfile"""

    # 读取模型配置
    config_path = merged_dir / "config.json"
    config = {}
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)

    # 生成 Modelfile 内容
    modelfile_content = f"""# 自动生成的 Modelfile - {model_name}
# 基于合并后的 HuggingFace 模型

FROM {merged_dir.absolute()}

# 模型参数配置
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER repeat_penalty 1.1

# 系统提示词（可根据需要修改）
SYSTEM \"\"\"你是一个有用的AI助手，经过专门训练以提供准确和有帮助的回答。\"\"\"
"""

    # 如果有特定配置，添加更多参数
    if config:
        if "max_position_embeddings" in config:
            modelfile_content += f"\nPARAMETER num_ctx {config['max_position_embeddings']}"

    return modelfile_content


def import_to_ollama(merged_dir: str, model_name: str) -> bool:
    """导入模型到 Ollama"""

    merged_path = Path(merged_dir)
    if not merged_path.exists():
        print(f"❌ 合并模型目录不存在: {merged_path}")
        return False

    # 检查必要文件
    required_files = ["config.json", "tokenizer.json"]
    for file in required_files:
        if not (merged_path / file).exists():
            print(f"❌ 缺少必要文件: {file}")
            return False

    # 创建临时 Modelfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='', delete=False, prefix='Modelfile_') as f:
        modelfile_content = create_modelfile(merged_path, model_name)
        f.write(modelfile_content)
        modelfile_path = f.name

    try:
        print(f"📝 生成的 Modelfile:")
        print("=" * 50)
        print(modelfile_content)
        print("=" * 50)

        # 使用 ollama create 导入模型
        print(f"🔄 导入模型到 Ollama: {model_name}")
        ret, output = run_command(f"ollama create {model_name} -f {modelfile_path}")

        if ret == 0:
            print(f"✅ 模型 '{model_name}' 导入成功!")
            print(f"🚀 现在可以使用: ollama run {model_name}")
            return True
        else:
            print(f"❌ 导入失败: {output}")
            return False

    finally:
        # 清理临时文件
        Path(modelfile_path).unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description="自动导入 LoRA 训练结果到 Ollama")
    parser.add_argument("--merged_dir", type=str, default="out/merged",
                       help="合并后的模型目录")
    parser.add_argument("--model_name", type=str, required=True,
                       help="在 Ollama 中的模型名称")
    parser.add_argument("--force", action="store_true",
                       help="强制覆盖已存在的模型")

    args = parser.parse_args()

    print("🎯 自动导入 LoRA 模型到 Ollama")
    print("=" * 50)

    # 检查 Ollama
    if not check_ollama():
        sys.exit(1)

    # 检查模型是否已存在
    if not args.force:
        ret, output = run_command(f"ollama list | grep {args.model_name}", check=False)
        if ret == 0:
            print(f"⚠️  模型 '{args.model_name}' 已存在")
            print("💡 使用 --force 参数强制覆盖")
            sys.exit(1)

    # 导入模型
    success = import_to_ollama(args.merged_dir, args.model_name)

    if success:
        print("\n🎉 导入完成!")
        print(f"📋 验证模型列表:")
        run_command("ollama list")

        print(f"\n🔥 测试运行:")
        print(f"   ollama run {args.model_name}")

    else:
        print("\n❌ 导入失败，请检查错误信息")
        sys.exit(1)


if __name__ == "__main__":
    main()