#!/usr/bin/env python3
"""
修复训练数据 - 给正式训练数据添加system prompt
解决问题：正式训练数据缺少角色设定导致模型表现不佳
"""

import json
import shutil
from pathlib import Path

def fix_training_data():
    """修复训练数据，添加system prompt"""

    # 文件路径
    original_file = Path("datasets/linzhi/train.jsonl")
    backup_file = Path("datasets/linzhi/train_backup.jsonl")
    fixed_file = Path("datasets/linzhi/train_fixed.jsonl")

    # system prompt模板（从测试数据中提取）
    system_prompt = """你是林栀，一个24岁的温柔女孩。你的特点：
- 外表：清瘦白皙，及肩黑发微卷，鹿眼温润，气质安静清甜
- 性格：文静少言，说话轻软，容易害羞脸红，内心敏感细腻
- 互动：对喜欢的人会含蓄试探，用细节表达好感，不会直白表达情感

请完全按照林栀的性格回应，包括语气、动作描写和心理活动。"""

    print("🔧 开始修复训练数据...")

    # 1. 备份原文件
    if original_file.exists():
        print(f"📦 备份原文件: {original_file} -> {backup_file}")
        shutil.copy2(original_file, backup_file)
    else:
        print(f"❌ 原文件不存在: {original_file}")
        return False

    # 2. 读取并修复数据
    fixed_count = 0
    already_has_system = 0

    with open(original_file, 'r', encoding='utf-8') as infile, \
         open(fixed_file, 'w', encoding='utf-8') as outfile:

        for line_num, line in enumerate(infile, 1):
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)

                # 检查是否已有system prompt
                messages = data.get('messages', [])
                has_system = False

                if messages and messages[0].get('role') == 'system':
                    has_system = True
                    already_has_system += 1
                    print(f"⚠️  第{line_num}行已有system prompt，跳过")

                if not has_system:
                    # 添加system prompt到messages开头
                    system_message = {
                        "role": "system",
                        "content": system_prompt
                    }

                    # 插入到messages开头
                    data['messages'] = [system_message] + messages
                    fixed_count += 1

                    if fixed_count <= 5:  # 只显示前5个修复的样例
                        print(f"✅ 修复第{line_num}行: {messages[0].get('content', '')[:30]}...")

                # 写入修复后的数据
                outfile.write(json.dumps(data, ensure_ascii=False) + '\n')

            except json.JSONDecodeError as e:
                print(f"❌ 第{line_num}行JSON格式错误: {e}")
                continue
            except Exception as e:
                print(f"❌ 第{line_num}行处理错误: {e}")
                continue

    # 3. 替换原文件
    if fixed_file.exists():
        print(f"📁 替换原文件: {fixed_file} -> {original_file}")
        shutil.move(fixed_file, original_file)

    # 4. 显示统计信息
    print("\n📊 修复统计:")
    print(f"   ✅ 修复条数: {fixed_count}")
    print(f"   ⚠️  已有system prompt: {already_has_system}")
    print(f"   📦 备份文件: {backup_file}")

    # 5. 验证修复结果
    print("\n🔍 验证修复结果:")
    verify_fixed_data(original_file)

    return True

def verify_fixed_data(file_path):
    """验证修复后的数据格式"""

    total_lines = 0
    has_system_count = 0
    sample_shown = False

    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            total_lines += 1

            try:
                data = json.loads(line)
                messages = data.get('messages', [])

                if messages and messages[0].get('role') == 'system':
                    has_system_count += 1

                    # 显示第一个修复后的样例
                    if not sample_shown:
                        print(f"   📝 样例 (第{line_num}行):")
                        for i, msg in enumerate(messages[:2]):  # 只显示system和user
                            role_emoji = "🤖" if msg['role'] == 'system' else "👤" if msg['role'] == 'user' else "🎭"
                            content = msg['content'][:50].replace('\n', ' ') + "..." if len(msg['content']) > 50 else msg['content']
                            print(f"      {role_emoji} {msg['role']}: {content}")
                        sample_shown = True

            except json.JSONDecodeError:
                continue

    print(f"   📊 总行数: {total_lines}")
    print(f"   ✅ 有system prompt: {has_system_count}")
    print(f"   📈 覆盖率: {has_system_count/total_lines*100:.1f}%")

    if has_system_count == total_lines:
        print("   🎉 所有数据都已正确添加system prompt!")
    else:
        print(f"   ⚠️  还有 {total_lines - has_system_count} 条数据缺少system prompt")

if __name__ == "__main__":
    success = fix_training_data()

    if success:
        print("\n🎉 数据修复完成!")
        print("\n📋 后续步骤:")
        print("1. 用修复后的数据重新训练模型")
        print("2. 对比训练效果，应该会看到显著改善")
        print("3. 角色一致性和对话质量都会提升")

        # 提示用户重新训练
        print(f"\n🚀 重新训练命令:")
        print(f"   python smart_train.py --character linzhi")

    else:
        print("❌ 数据修复失败，请检查错误信息")