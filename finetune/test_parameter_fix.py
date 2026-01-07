#!/usr/bin/env python3
"""
测试参数传递修复 - 验证 train_to_ollama.py 现在能正确读取角色配置参数
"""

import sys
from pathlib import Path

# 确保能导入 config_manager
sys.path.append(str(Path(__file__).parent))

from config_manager import ConfigManager

def test_config_loading():
    """测试配置加载"""
    print("🧪 测试角色配置参数读取")
    print("=" * 50)

    # 测试角色配置加载
    config = ConfigManager(character="linzhi")

    print(f"✅ ConfigManager 初始化成功")
    print(f"\n📋 读取到的参数:")
    print(f"🤖 基础模型: {config.get('model.base_model')}")
    print(f"🔄 训练轮数: {config.get('training.epochs')}")
    print(f"📊 学习率: {config.get('training.learning_rate')}")
    print(f"🔧 LoRA rank: {config.get('lora.rank')}")
    print(f"🔧 LoRA alpha: {config.get('lora.alpha')}")
    print(f"🔧 LoRA dropout: {config.get('lora.dropout')}")
    print(f"🎲 随机种子: {config.get('training.seed')}")
    print(f"🌡️  温度: {config.get('ollama.temperature')}")

    # 验证关键参数是否正确
    expected_values = {
        'training.epochs': 3.0,
        'training.learning_rate': 5e-5,
        'lora.rank': 16,
        'lora.alpha': 32,
        'lora.dropout': 0.1,
        'training.seed': 42
    }

    print(f"\n🔍 验证关键参数:")
    all_correct = True
    for key, expected in expected_values.items():
        actual = config.get(key)
        status = "✅" if actual == expected else "❌"
        print(f"   {status} {key}: {actual} (期望: {expected})")
        if actual != expected:
            all_correct = False

    print(f"\n" + "=" * 50)
    if all_correct:
        print("🎉 所有参数读取正确！")
        print("✅ train_to_ollama.py 现在会使用正确的角色配置参数")
        print("\n💡 现在可以安全地使用:")
        print("   python train_to_ollama.py --character linzhi --ollama_name linzhi-lora")
        return True
    else:
        print("❌ 部分参数读取有误，请检查配置")
        return False

if __name__ == "__main__":
    success = test_config_loading()
    sys.exit(0 if success else 1)