#!/usr/bin/env python3
"""
🧹 项目清理工具 - 管理磁盘空间
"""

import argparse
import shutil
import subprocess
from pathlib import Path


def get_dir_size(path):
    """获取目录大小（MB）"""
    try:
        total = sum(f.stat().st_size for f in Path(path).rglob('*') if f.is_file())
        return total / (1024 * 1024)  # 转换为MB
    except:
        return 0


def run_cmd(cmd):
    """运行命令"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout.strip()
    except:
        return False, ""


def main():
    parser = argparse.ArgumentParser(description="项目清理工具")
    parser.add_argument("--dry-run", action="store_true", help="预览操作，不实际删除")
    parser.add_argument("--all", action="store_true", help="清理所有可清理内容")
    parser.add_argument("--cache", action="store_true", help="清理缓存")
    parser.add_argument("--checkpoints", action="store_true", help="清理训练检查点")
    parser.add_argument("--old-models", action="store_true", help="清理旧的Ollama模型")

    args = parser.parse_args()

    print("🧹 项目清理工具")
    print("=" * 30)

    total_saved = 0

    # 1. 清理Python缓存
    if args.cache or args.all:
        cache_dirs = [
            "__pycache__",
            ".pytest_cache",
            "*.egg-info"
        ]

        cache_size = 0
        for pattern in cache_dirs:
            for path in Path(".").rglob(pattern):
                if path.exists():
                    cache_size += get_dir_size(path)
                    if not args.dry_run:
                        if path.is_dir():
                            shutil.rmtree(path)
                        else:
                            path.unlink()

        if cache_size > 0:
            print(f"🗑️  清理缓存: {cache_size:.1f} MB")
            total_saved += cache_size

    # 2. 清理训练检查点
    if args.checkpoints or args.all:
        checkpoint_size = 0
        out_dir = Path("out")

        if out_dir.exists():
            for checkpoint_dir in out_dir.rglob("checkpoint-*"):
                if checkpoint_dir.is_dir():
                    size = get_dir_size(checkpoint_dir)
                    checkpoint_size += size
                    if not args.dry_run:
                        shutil.rmtree(checkpoint_dir)
                        print(f"   删除: {checkpoint_dir}")

        if checkpoint_size > 0:
            print(f"🗑️  清理检查点: {checkpoint_size:.1f} MB")
            total_saved += checkpoint_size

    # 3. 列出可清理的Ollama模型
    if args.old_models or args.all:
        print("\n📊 Ollama 模型分析:")
        success, output = run_cmd("ollama list")

        if success and output:
            lines = output.split('\n')[1:]  # 跳过标题行
            old_models = []

            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 4:
                        name = parts[0]
                        size = parts[2]

                        # 识别可能的旧模型
                        if any(keyword in name.lower() for keyword in ['test', 'debug', 'temp', 'old', 'backup']):
                            old_models.append((name, size))

            if old_models:
                print("   可清理的模型:")
                for name, size in old_models:
                    print(f"   📦 {name:25} {size:>8}")
                print(f"\n💡 手动清理命令: ollama rm 模型名")
            else:
                print("   ✅ 没有发现明显的测试模型")

    # 4. 显示总结
    print(f"\n📈 总结:")
    if total_saved > 0:
        action = "可节省" if args.dry_run else "已节省"
        print(f"💾 {action}磁盘空间: {total_saved:.1f} MB")
    else:
        print("✨ 项目已经很干净了！")

    # 5. 显示当前占用
    print(f"\n📊 当前磁盘占用:")
    dirs_to_check = {
        "训练输出": "out",
        "数据集": "data",
        "虚拟环境": ".venv",
        "Hugging Face缓存": ".hf"
    }

    for name, path in dirs_to_check.items():
        if Path(path).exists():
            size = get_dir_size(path)
            print(f"   {name:12}: {size:>8.1f} MB")

    if args.dry_run:
        print(f"\n🔍 这是预览模式，使用 --all 执行实际清理")


if __name__ == "__main__":
    main()