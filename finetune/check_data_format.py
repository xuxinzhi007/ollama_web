#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据格式 - 确认是否还有system prompt
"""

import json
import sys
import io
from pathlib import Path

# Windows编码修复
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def check_data_format():
    """检查训练数据格式"""
    
    train_file = Path("datasets/linzhi/train.jsonl")
    if not train_file.exists():
        print(f"❌ 训练文件不存在: {train_file}")
        return
    
    print("=" * 70)
    print("检查训练数据格式")
    print("=" * 70)
    
    with open(train_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"\n📊 数据集大小: {len(lines)} 个样本")
    
    # 检查前5个样本
    has_system_count = 0
    sample_count = min(5, len(lines))
    
    print(f"\n🔍 检查前 {sample_count} 个样本:")
    print("-" * 70)
    
    for i in range(sample_count):
        try:
            data = json.loads(lines[i])
            messages = data.get('messages', [])
            
            has_system = any(msg.get('role') == 'system' for msg in messages)
            if has_system:
                has_system_count += 1
            
            print(f"\n样本 {i+1}:")
            print(f"  消息数量: {len(messages)}")
            print(f"  包含system: {'❌ 是' if has_system else '✅ 否'}")
            
            if has_system:
                system_msg = next((msg for msg in messages if msg.get('role') == 'system'), None)
                if system_msg:
                    content = system_msg.get('content', '')
                    print(f"  System内容: {content[:100]}...")
            
            # 显示所有消息角色
            roles = [msg.get('role', 'unknown') for msg in messages]
            print(f"  消息角色: {', '.join(roles)}")
            
        except Exception as e:
            print(f"  ⚠️  解析失败: {e}")
    
    # 统计所有样本
    print(f"\n📈 统计所有样本:")
    print("-" * 70)
    total_has_system = 0
    for line in lines:
        try:
            data = json.loads(line)
            messages = data.get('messages', [])
            if any(msg.get('role') == 'system' for msg in messages):
                total_has_system += 1
        except:
            pass
    
    print(f"  总样本数: {len(lines)}")
    print(f"  包含system的样本: {total_has_system} ({total_has_system/len(lines)*100:.1f}%)")
    
    if total_has_system > 0:
        print(f"\n❌ 问题: 数据中还有 {total_has_system} 个样本包含system prompt")
        print(f"   建议: 运行 python fix_overfitting.py 移除system prompt")
    else:
        print(f"\n✅ 数据格式正确: 没有system prompt")
    
    # 检查数据质量
    print(f"\n📋 数据质量检查:")
    print("-" * 70)
    
    empty_count = 0
    short_count = 0
    for line in lines[:100]:  # 只检查前100个
        try:
            data = json.loads(line)
            messages = data.get('messages', [])
            
            # 检查是否有空消息
            for msg in messages:
                content = msg.get('content', '').strip()
                if not content:
                    empty_count += 1
                elif len(content) < 5:
                    short_count += 1
        except:
            pass
    
    if empty_count > 0:
        print(f"  ⚠️  发现 {empty_count} 个空消息")
    if short_count > 0:
        print(f"  ⚠️  发现 {short_count} 个过短消息（<5字符）")
    if empty_count == 0 and short_count == 0:
        print(f"  ✅ 数据质量良好")

if __name__ == "__main__":
    check_data_format()

