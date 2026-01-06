#!/usr/bin/env python3
"""
修复过拟合问题 - 优化数据格式
问题：模型输出训练数据的格式，而不是正常对话
"""

import json
import sys
from pathlib import Path

def fix_data_format(input_file, output_file, remove_system=True, simplify_system=False):
    """
    修复数据格式
    - remove_system: 是否移除每个样本中的system prompt
    - simplify_system: 是否简化system prompt（如果保留）
    """
    print(f"处理数据: {input_file} -> {output_file}")
    
    fixed_count = 0
    total_count = 0
    
    with open(input_file, 'r', encoding='utf-8') as f_in, \
         open(output_file, 'w', encoding='utf-8') as f_out:
        
        for line in f_in:
            if not line.strip():
                continue
            
            try:
                data = json.loads(line.strip())
                messages = data.get('messages', [])
                
                if not messages:
                    continue
                
                total_count += 1
                
                # 简化或移除system prompt
                new_messages = []
                for msg in messages:
                    role = msg.get('role', '')
                    content = msg.get('content', '')
                    
                    if role == 'system':
                        if remove_system:
                            # 完全移除system prompt（会在Modelfile中设置）
                            continue
                        elif simplify_system:
                            # 简化system prompt，移除格式化内容
                            # 只保留核心角色设定
                            simplified = "你是林栀，一个24岁的温柔女孩。文静少言，说话轻软，容易害羞脸红。"
                            new_messages.append({"role": "system", "content": simplified})
                        else:
                            # 保留原始system prompt
                            new_messages.append(msg)
                    else:
                        new_messages.append(msg)
                
                # 如果没有system了，确保至少有一个user和assistant
                if new_messages and new_messages[0].get('role') != 'system':
                    # 第一个消息应该是user
                    if new_messages[0].get('role') != 'user':
                        continue
                
                # 写入修复后的数据
                fixed_data = {
                    "messages": new_messages
                }
                # 保留其他字段（如果有）
                for key in ['style', 'category']:
                    if key in data:
                        fixed_data[key] = data[key]
                
                f_out.write(json.dumps(fixed_data, ensure_ascii=False) + '\n')
                fixed_count += 1
                
            except json.JSONDecodeError as e:
                print(f"⚠️  JSON解析错误: {e}")
                continue
    
    print(f"✅ 处理完成: {fixed_count}/{total_count} 样本")
    return fixed_count

def create_backup(original_file):
    """创建备份"""
    backup_file = str(original_file).replace('.jsonl', '_backup.jsonl')
    import shutil
    shutil.copy2(original_file, backup_file)
    print(f"📦 已创建备份: {backup_file}")
    return backup_file

def main():
    print("🔧 修复过拟合问题 - 优化数据格式")
    print("=" * 60)
    
    # 处理训练数据
    train_file = Path("datasets/linzhi/train.jsonl")
    val_file = Path("datasets/linzhi/val.jsonl")
    
    if not train_file.exists():
        print(f"❌ 训练文件不存在: {train_file}")
        return
    
    print("\n问题分析:")
    print("1. 每个样本都包含完整的system prompt")
    print("2. System prompt包含格式化的列表（'你的特点：'、'外表：'等）")
    print("3. 模型学会了'背诵'这些格式，而不是正常对话")
    
    print("\n解决方案:")
    print("选项1: 移除所有样本中的system prompt（推荐）")
    print("  - System prompt只在Modelfile中设置")
    print("  - 训练数据只包含user和assistant对话")
    print("\n选项2: 简化system prompt")
    print("  - 移除格式化的列表")
    print("  - 只保留核心角色设定")
    
    choice = input("\n选择方案 (1=移除system, 2=简化system, 其他=取消): ").strip()
    
    if choice == "1":
        remove_system = True
        simplify_system = False
        print("\n✅ 将移除所有样本中的system prompt")
    elif choice == "2":
        remove_system = False
        simplify_system = True
        print("\n✅ 将简化system prompt")
    else:
        print("已取消")
        return
    
    # 创建备份
    print("\n创建备份...")
    create_backup(train_file)
    if val_file.exists():
        create_backup(val_file)
    
    # 处理训练数据
    print("\n处理训练数据...")
    fixed_train = train_file.parent / f"{train_file.stem}_fixed.jsonl"
    fix_data_format(train_file, fixed_train, remove_system, simplify_system)
    
    # 处理验证数据
    if val_file.exists():
        print("\n处理验证数据...")
        fixed_val = val_file.parent / f"{val_file.stem}_fixed.jsonl"
        fix_data_format(val_file, fixed_val, remove_system, simplify_system)
    
    print("\n" + "=" * 60)
    print("✅ 修复完成！")
    print("\n下一步:")
    print("1. 检查修复后的数据:")
    print(f"   - 训练数据: {fixed_train}")
    print(f"   - 验证数据: {fixed_val if val_file.exists() else 'N/A'}")
    print("\n2. 如果数据正确，替换原文件:")
    print(f"   mv {fixed_train} {train_file}")
    if val_file.exists():
        print(f"   mv {fixed_val} {val_file}")
    print("\n3. 重新训练模型")
    print("   .\\train.ps1 linzhi")

if __name__ == "__main__":
    main()

