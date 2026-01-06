#!/usr/bin/env python3
"""
模型缓存检测和管理工具
解决重复下载模型的问题
"""

import os
from pathlib import Path
from typing import Optional, Tuple
import tempfile

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    from transformers.utils import TRANSFORMERS_CACHE
except ImportError:
    print("⚠️ transformers库未安装，无法检测模型缓存")
    TRANSFORMERS_CACHE = None


def get_cache_dir() -> Path:
    """获取HuggingFace缓存目录"""
    if TRANSFORMERS_CACHE:
        return Path(TRANSFORMERS_CACHE)

    # 回退到默认位置
    home = Path.home()
    return home / ".cache" / "huggingface" / "transformers"


def is_model_cached(model_name: str) -> Tuple[bool, Optional[Path]]:
    """
    检查模型是否已经缓存

    Args:
        model_name: 模型名称，如 "Qwen/Qwen2.5-0.5B-Instruct"

    Returns:
        (是否缓存, 缓存路径)
    """
    try:
        # 方法1: 尝试加载tokenizer配置文件，不实际下载
        from transformers import AutoConfig

        # 使用临时目录，local_files_only=True 强制只使用本地文件
        config = AutoConfig.from_pretrained(
            model_name,
            local_files_only=True,
            cache_dir=None  # 使用默认缓存
        )

        # 如果能成功加载配置，说明模型已缓存
        cache_dir = get_cache_dir()

        # 查找实际的模型文件夹
        model_hash_dirs = list(cache_dir.glob(f"*{model_name.replace('/', '--')}*"))
        if model_hash_dirs:
            return True, model_hash_dirs[0]

        return True, cache_dir  # 配置能加载但找不到具体路径

    except Exception:
        # 如果加载失败，说明模型未缓存或缓存不完整
        return False, None


def check_model_files(model_name: str) -> dict:
    """
    详细检查模型文件缓存状态

    Returns:
        {
            'cached': bool,
            'cache_path': str,
            'files': {
                'config': bool,
                'tokenizer': bool,
                'model': bool,
            },
            'size': str
        }
    """
    result = {
        'cached': False,
        'cache_path': None,
        'files': {
            'config': False,
            'tokenizer': False,
            'model': False,
        },
        'size': '0 MB'
    }

    try:
        is_cached, cache_path = is_model_cached(model_name)
        if not is_cached:
            return result

        result['cached'] = True
        result['cache_path'] = str(cache_path) if cache_path else "未知"

        # 检查关键文件
        cache_dir = get_cache_dir()

        # 查找模型相关的文件
        model_pattern = model_name.replace('/', '--')
        model_files = list(cache_dir.glob(f"*{model_pattern}*"))

        total_size = 0
        config_found = False
        tokenizer_found = False
        model_found = False

        for file_path in cache_dir.rglob("*"):
            if not file_path.is_file():
                continue

            if model_pattern in str(file_path):
                file_size = file_path.stat().st_size
                total_size += file_size

                filename = file_path.name.lower()
                if "config" in filename:
                    config_found = True
                elif "tokenizer" in filename:
                    tokenizer_found = True
                elif any(x in filename for x in ["pytorch_model", "model.safetensors", ".bin"]):
                    model_found = True

        result['files']['config'] = config_found
        result['files']['tokenizer'] = tokenizer_found
        result['files']['model'] = model_found

        # 转换文件大小
        if total_size > 0:
            if total_size > 1024 * 1024 * 1024:  # > 1GB
                result['size'] = f"{total_size / (1024**3):.1f} GB"
            else:  # MB
                result['size'] = f"{total_size / (1024**2):.1f} MB"

    except Exception as e:
        print(f"⚠️ 检查模型缓存时出错: {e}")

    return result


def print_cache_status(model_name: str):
    """打印模型缓存状态"""
    print(f"\n🔍 检查模型缓存: {model_name}")

    status = check_model_files(model_name)

    if status['cached']:
        print("✅ 模型已缓存")
        print(f"   📁 缓存路径: {status['cache_path']}")
        print(f"   📦 缓存大小: {status['size']}")
        print(f"   📄 配置文件: {'✅' if status['files']['config'] else '❌'}")
        print(f"   🔤 分词器: {'✅' if status['files']['tokenizer'] else '❌'}")
        print(f"   🤖 模型权重: {'✅' if status['files']['model'] else '❌'}")

        # 检查缓存完整性
        files = status['files']
        if all([files['config'], files['tokenizer'], files['model']]):
            print("🎉 缓存完整，将使用本地文件")
            return True
        else:
            print("⚠️ 缓存不完整，可能需要重新下载部分文件")
            return False
    else:
        print("❌ 模型未缓存")
        print("💡 首次使用需要从网络下载（约500MB-1GB）")
        return False


def estimate_download_time(model_name: str) -> str:
    """估算下载时间"""
    # 根据模型大小估算
    if "0.5B" in model_name:
        return "约1-3分钟"
    elif "1.5B" in model_name or "1B" in model_name:
        return "约3-5分钟"
    elif "7B" in model_name:
        return "约10-15分钟"
    else:
        return "几分钟"


def smart_model_load_message(model_name: str):
    """智能显示模型加载消息"""
    print(f"\n📥 正在加载模型: {model_name}")

    if print_cache_status(model_name):
        print("⚡ 使用缓存，加载速度更快")
    else:
        download_time = estimate_download_time(model_name)
        print(f"🌐 从网络下载模型文件，预计耗时: {download_time}")


if __name__ == "__main__":
    # 测试常见模型
    models = [
        "Qwen/Qwen2.5-0.5B-Instruct",
        "Qwen/Qwen2.5-1.5B-Instruct",
    ]

    for model in models:
        print_cache_status(model)
        print()