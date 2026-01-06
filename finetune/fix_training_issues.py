#!/usr/bin/env python3
"""
训练问题诊断和修复脚本
解决：
1. Loss重置问题（继续训练时epoch计算错误）
2. 模型效果差（数据格式、参数优化）
"""

import json
import sys
from pathlib import Path

def check_data_format(data_file):
    """检查数据格式"""
    print(f"\n检查数据格式: {data_file}")
    issues = []
    
    with open(data_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"总样本数: {len(lines)}")
    
    # 检查前几个样本
    for i, line in enumerate(lines[:5]):
        try:
            data = json.loads(line.strip())
            messages = data.get('messages', [])
            
            # 检查是否有system message
            has_system = any(msg.get('role') == 'system' for msg in messages)
            if not has_system:
                issues.append(f"样本 {i+1}: 缺少system message")
            
            # 检查system message是否重复
            system_count = sum(1 for msg in messages if msg.get('role') == 'system')
            if system_count > 1:
                issues.append(f"样本 {i+1}: 有多个system message")
            
            # 检查消息格式
            if len(messages) < 2:
                issues.append(f"样本 {i+1}: 消息数量不足（至少需要user和assistant）")
            
        except json.JSONDecodeError as e:
            issues.append(f"样本 {i+1}: JSON格式错误 - {e}")
    
    if issues:
        print("⚠️  发现问题:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ 数据格式检查通过")
    
    return len(issues) == 0

def optimize_training_params():
    """优化训练参数建议"""
    print("\n📊 训练参数优化建议:")
    print("=" * 50)
    
    print("\n当前配置问题:")
    print("1. LoRA rank=32 可能过大，容易过拟合")
    print("2. 学习率 1e-4 可能偏高，建议降低")
    print("3. 每个样本都重复system prompt，可能导致过度关注")
    
    print("\n推荐配置:")
    print("- LoRA rank: 16 (降低过拟合风险)")
    print("- LoRA alpha: 32 (保持alpha=2*rank)")
    print("- Learning rate: 5e-5 (更稳定的学习)")
    print("- Epochs: 3-5 (根据loss曲线调整)")
    print("- Dropout: 0.1 (保持不变)")
    
    print("\n数据优化建议:")
    print("- 考虑移除每个样本中的system message，统一在Modelfile中设置")
    print("- 或者只在第一个样本保留system message")

def check_checkpoint_resume():
    """检查checkpoint续训问题"""
    print("\n🔍 检查checkpoint续训问题:")
    print("=" * 50)
    
    print("\n问题分析:")
    print("当使用 --resume_from_checkpoint 继续训练时：")
    print("- num_train_epochs 参数是总epochs数，不是剩余epochs数")
    print("- 如果之前训练了0.71个epoch，设置epochs=5.0，会重新开始训练")
    print("- 这导致loss从初始值重新开始")
    
    print("\n解决方案:")
    print("1. 继续训练时，应该计算剩余epochs数")
    print("2. 或者使用 --resume_from_checkpoint 时，不设置epochs参数")
    print("3. 让训练脚本自动从checkpoint恢复训练状态")

def main():
    print("🔧 训练问题诊断工具")
    print("=" * 50)
    
    # 检查数据格式
    train_file = Path("datasets/linzhi/train.jsonl")
    if train_file.exists():
        check_data_format(train_file)
    else:
        print(f"⚠️  训练文件不存在: {train_file}")
    
    # 优化建议
    optimize_training_params()
    
    # checkpoint问题
    check_checkpoint_resume()
    
    print("\n" + "=" * 50)
    print("✅ 诊断完成")

if __name__ == "__main__":
    main()
