#!/usr/bin/env python3
"""
测试配置兼容性 - 验证角色配置和传统配置是否都能正常工作
"""

import sys
from pathlib import Path

# 确保能导入 config_manager
sys.path.append(str(Path(__file__).parent))

from config_manager import ConfigManager

def test_character_config():
    """测试角色配置读取"""
    print("🧪 测试角色配置读取")
    print("=" * 50)

    try:
        # 测试读取 linzhi 角色配置
        config = ConfigManager(character="linzhi")

        print(f"✅ ConfigManager 初始化成功")
        print(f"🤖 基础模型: {config.get('model.base_model')}")
        print(f"🔄 训练轮数: {config.get('training.epochs')}")
        print(f"📊 学习率: {config.get('training.learning_rate')}")
        print(f"🔧 LoRA rank: {config.get('lora.rank')}")
        print(f"🔧 LoRA alpha: {config.get('lora.alpha')}")
        print(f"🔧 LoRA dropout: {config.get('lora.dropout')}")
        print(f"🌡️ 温度: {config.get('ollama.temperature')}")

        return True

    except Exception as e:
        print(f"❌ 角色配置测试失败: {e}")
        return False

def test_traditional_config():
    """测试传统配置读取"""
    print("\n🧪 测试传统配置读取")
    print("=" * 50)

    try:
        # 测试读取 config.yaml
        config = ConfigManager("config.yaml")

        print(f"✅ ConfigManager 初始化成功")
        print(f"🤖 基础模型: {config.get('model.base_model')}")
        print(f"🔄 训练轮数: {config.get('training.epochs')}")
        print(f"📊 学习率: {config.get('training.learning_rate')}")
        print(f"🔧 LoRA rank: {config.get('lora.rank')}")
        print(f"🔧 LoRA alpha: {config.get('lora.alpha')}")

        return True

    except Exception as e:
        print(f"❌ 传统配置测试失败: {e}")
        return False

def test_fallback():
    """测试回退机制"""
    print("\n🧪 测试回退机制 (角色不存在时)")
    print("=" * 50)

    try:
        # 测试不存在的角色
        config = ConfigManager("config.yaml", character="nonexistent")

        print(f"✅ 回退机制工作正常")
        print(f"🤖 基础模型: {config.get('model.base_model')}")

        return True

    except Exception as e:
        print(f"❌ 回退机制测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🔧 配置兼容性测试")
    print("=" * 60)

    # 检查必要文件
    required_files = ["character_configs.yaml", "config.yaml"]
    missing_files = []

    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)

    if missing_files:
        print(f"⚠️ 缺少必要文件: {missing_files}")
        print("请确保在 finetune 目录下运行此测试")
        return False

    results = []

    # 执行测试
    results.append(("角色配置", test_character_config()))
    results.append(("传统配置", test_traditional_config()))
    results.append(("回退机制", test_fallback()))

    # 总结结果
    print("\n📊 测试结果总结")
    print("=" * 60)

    all_passed = True
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:20} {status}")
        if not result:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过！配置兼容性良好")
        print("\n💡 使用方式:")
        print("   # 使用角色配置:")
        print("   python train_to_ollama.py --character linzhi --ollama_name linzhi-lora")
        print("   # 使用传统配置:")
        print("   python train_to_ollama.py --config config.yaml --ollama_name my-model")
    else:
        print("❌ 部分测试失败，请检查配置文件")

    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)