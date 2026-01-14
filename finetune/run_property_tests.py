#!/usr/bin/env python3
"""
在 finetune 目录中运行属性测试的脚本
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """运行属性测试"""
    print("🚀 LoRA 训练系统属性测试")
    print("=" * 50)

    # 检查虚拟环境
    venv_python = Path(".venv/bin/python")
    if not venv_python.exists():
        print("❌ 虚拟环境 Python 不存在")
        return 1

    # 检查测试文件
    test_file = Path("../tests/test_properties.py")
    if not test_file.exists():
        print("❌ 测试文件不存在:", test_file)
        return 1

    print("✅ 环境检查通过")
    print(f"🐍 使用 Python: {venv_python.absolute()}")
    print(f"📋 测试文件: {test_file.absolute()}")

    try:
        # 运行属性测试
        print("\n🧪 开始运行属性测试...")

        result = subprocess.run([
            str(venv_python), '-m', 'pytest',
            str(test_file),
            '-v',
            '--tb=short',
            '--hypothesis-show-statistics'
        ], check=False, text=True)

        if result.returncode == 0:
            print("\n🎉 所有属性测试通过！")
            return 0
        else:
            print(f"\n⚠️ 测试失败，返回码: {result.returncode}")
            return result.returncode

    except Exception as e:
        print(f"❌ 测试运行失败: {e}")
        return 1

if __name__ == "__main__":
    exit(main())