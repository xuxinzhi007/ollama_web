#!/usr/bin/env python3
"""
手动下载模型脚本 - 显示真实下载进度
"""
import os
from huggingface_hub import snapshot_download
from tqdm import tqdm
import requests
from pathlib import Path

def download_qwen_model():
    """下载 Qwen2.5-0.5B 模型"""
    model_name = "Qwen/Qwen2.5-0.5B"

    print(f"🚀 开始下载模型: {model_name}")
    print("📁 模型将保存到 HuggingFace 缓存目录")
    print("💡 下载完成后可以离线使用")
    print("-" * 50)

    try:
        # 下载模型到本地缓存
        local_path = snapshot_download(
            repo_id=model_name,
            resume_download=True,  # 支持断点续传
            local_files_only=False,  # 允许网络下载
        )

        print(f"✅ 模型下载完成！")
        print(f"📍 模型路径: {local_path}")
        return local_path

    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return None

def check_model_cache():
    """检查模型是否已缓存"""
    from transformers import AutoTokenizer
    model_name = "Qwen/Qwen2.5-0.5B"

    try:
        # 尝试加载 tokenizer 检查模型是否已存在
        tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
        print(f"✅ 模型已缓存，无需重新下载")
        return True
    except Exception:
        print(f"📥 模型未缓存，需要下载")
        return False

if __name__ == "__main__":
    print("🔍 检查模型缓存状态...")

    if not check_model_cache():
        print("\n开始下载...")
        download_qwen_model()

    print("\n🎉 模型准备就绪，可以开始训练！")