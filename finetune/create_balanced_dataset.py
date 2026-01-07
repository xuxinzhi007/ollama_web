#!/usr/bin/env python3
"""
创建平衡的训练数据集 - 解决答非所问问题
将 100% roleplay 数据调整为平衡结构
"""

import json
import random
from pathlib import Path

def create_balanced_dataset():
    """创建平衡的数据集"""

    print("🔄 创建平衡训练数据集...")

    # 读取原始 roleplay 数据
    original_file = Path("datasets/linzhi/train.jsonl")
    basic_qa_file = Path("datasets/linzhi/basic_qa_supplement.jsonl")

    # 输出平衡数据集
    balanced_file = Path("datasets/linzhi/train_balanced.jsonl")

    print(f"📖 读取原始数据: {original_file}")

    # 读取所有数据
    roleplay_data = []
    basic_qa_data = []

    # 读取原始 roleplay 数据
    if original_file.exists():
        with open(original_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    roleplay_data.append(json.loads(line))

    # 读取基础问答数据
    if basic_qa_file.exists():
        with open(basic_qa_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    basic_qa_data.append(json.loads(line))

    print(f"📊 原始 roleplay 数据: {len(roleplay_data)} 条")
    print(f"📊 基础问答数据: {len(basic_qa_data)} 条")

    # 创建平衡数据集
    # 建议比例: 60% roleplay + 40% 基础问答
    roleplay_count = int(len(roleplay_data) * 0.6)  # 约 287 条
    basic_qa_count = len(basic_qa_data)  # 20 条

    # 需要更多基础问答数据来平衡，复制几次
    basic_qa_multiplier = max(1, (roleplay_count * 2) // (3 * basic_qa_count))

    print(f"🎯 目标比例:")
    print(f"   Roleplay: {roleplay_count} 条 (60%)")
    print(f"   基础问答: {basic_qa_count * basic_qa_multiplier} 条 (40%)")

    # 构建平衡数据集
    balanced_data = []

    # 添加 roleplay 数据 (随机采样)
    selected_roleplay = random.sample(roleplay_data, min(roleplay_count, len(roleplay_data)))
    balanced_data.extend(selected_roleplay)

    # 添加基础问答数据 (重复以达到目标数量)
    for i in range(basic_qa_multiplier):
        balanced_data.extend(basic_qa_data)

    # 随机打乱顺序
    random.shuffle(balanced_data)

    # 保存平衡数据集
    with open(balanced_file, 'w', encoding='utf-8') as f:
        for item in balanced_data:
            json.dump(item, f, ensure_ascii=False)
            f.write('\n')

    print(f"✅ 平衡数据集已创建: {balanced_file}")
    print(f"📈 总数据量: {len(balanced_data)} 条")

    # 分析数据分布
    roleplay_final = sum(1 for item in balanced_data if item.get('style') == 'roleplay')
    basic_qa_final = len(balanced_data) - roleplay_final

    print(f"📊 最终分布:")
    print(f"   Roleplay: {roleplay_final} 条 ({roleplay_final/len(balanced_data)*100:.1f}%)")
    print(f"   基础问答: {basic_qa_final} 条 ({basic_qa_final/len(balanced_data)*100:.1f}%)")

    return balanced_file

def update_character_config():
    """更新角色配置使用新的平衡数据集"""

    config_file = Path("character_configs.yaml")

    print(f"\n🔧 更新配置文件...")

    # 读取配置
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 替换训练数据路径
    old_path = 'train: "datasets/linzhi/train.jsonl"'
    new_path = 'train: "datasets/linzhi/train_balanced.jsonl"'

    if old_path in content:
        content = content.replace(old_path, new_path)

        # 保存更新的配置
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ 配置已更新: 使用平衡数据集")
    else:
        print(f"⚠️  未找到需要更新的配置路径")

if __name__ == "__main__":
    # 设置随机种子以确保可重现性
    random.seed(42)

    print("🎯 解决林栀答非所问问题 - 数据平衡方案")
    print("=" * 50)

    # 创建平衡数据集
    balanced_file = create_balanced_dataset()

    # 更新配置
    update_character_config()

    print("\n" + "=" * 50)
    print("🎉 数据平衡完成!")
    print("\n💡 下一步:")
    print("1️⃣ 重新训练: python train_to_ollama.py --character linzhi --ollama_name linzhi-balanced")
    print("2️⃣ 使用防过拟合参数: epochs=2.0, learning_rate=3e-5")
    print("3️⃣ 测试基础问答: '你是谁？'、'人机吗？'、'你好'")