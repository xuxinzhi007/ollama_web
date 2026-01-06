#!/usr/bin/env python3
"""
自定义数据集生成工具
支持多种方式创建训练数据：
1. 使用内置生成器（make_dataset.py）
2. 从CSV/Excel导入
3. 从JSON导入
4. 交互式创建
5. 模板引导创建
"""

import argparse
import json
import csv
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd


class DatasetBuilder:
    def __init__(self):
        self.data: List[Dict[str, Any]] = []

    def add_conversation(self, system_prompt: str, user_message: str, assistant_message: str,
                        category: str = "custom", style: str = "standard") -> None:
        """添加一条对话数据"""
        conversation = {
            "style": style,
            "category": category,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": assistant_message}
            ]
        }
        self.data.append(conversation)

    def load_from_csv(self, csv_path: Path) -> None:
        """从CSV文件加载数据

        CSV格式要求：
        system_prompt, user_message, assistant_message, category, style
        """
        print(f"📊 从CSV加载数据: {csv_path}")

        try:
            df = pd.read_csv(csv_path)
            required_columns = ['system_prompt', 'user_message', 'assistant_message']

            # 检查必需列
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                print(f"❌ CSV文件缺少必需列: {missing_cols}")
                print("💡 请确保CSV包含: system_prompt, user_message, assistant_message")
                return

            # 设置默认值
            if 'category' not in df.columns:
                df['category'] = 'custom'
            if 'style' not in df.columns:
                df['style'] = 'standard'

            # 转换数据
            for _, row in df.iterrows():
                self.add_conversation(
                    system_prompt=str(row['system_prompt']),
                    user_message=str(row['user_message']),
                    assistant_message=str(row['assistant_message']),
                    category=str(row.get('category', 'custom')),
                    style=str(row.get('style', 'standard'))
                )

            print(f"✅ 成功加载 {len(df)} 条对话")

        except Exception as e:
            print(f"❌ CSV加载失败: {e}")

    def load_from_json(self, json_path: Path) -> None:
        """从JSON文件加载数据

        JSON格式：
        [
            {
                "system_prompt": "...",
                "user_message": "...",
                "assistant_message": "...",
                "category": "...",
                "style": "..."
            }
        ]
        """
        print(f"📊 从JSON加载数据: {json_path}")

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)

            if not isinstance(json_data, list):
                print("❌ JSON格式错误：根元素应该是数组")
                return

            for item in json_data:
                if not isinstance(item, dict):
                    print("⚠️  跳过非对象元素")
                    continue

                required_fields = ['system_prompt', 'user_message', 'assistant_message']
                missing_fields = [field for field in required_fields if field not in item]
                if missing_fields:
                    print(f"⚠️  跳过缺少字段的条目: {missing_fields}")
                    continue

                self.add_conversation(
                    system_prompt=item['system_prompt'],
                    user_message=item['user_message'],
                    assistant_message=item['assistant_message'],
                    category=item.get('category', 'custom'),
                    style=item.get('style', 'standard')
                )

            print(f"✅ 成功加载 {len(self.data)} 条对话")

        except Exception as e:
            print(f"❌ JSON加载失败: {e}")

    def interactive_create(self) -> None:
        """交互式创建数据集"""
        print("\n🎯 交互式数据集创建")
        print("=" * 50)

        # 获取基础设置
        print("📋 首先设置基础信息:")
        system_prompt = input("系统提示 (描述AI的角色和行为): ").strip()
        if not system_prompt:
            system_prompt = "你是一个有帮助的AI助手。请提供准确、有用的回答。"

        category = input("数据类别 (如: coding, writing, qa): ").strip() or "custom"
        style = input("对话风格 (如: professional, friendly, casual): ").strip() or "standard"

        print(f"\n✅ 设置完成:")
        print(f"   系统提示: {system_prompt}")
        print(f"   数据类别: {category}")
        print(f"   对话风格: {style}")
        print("\n💡 开始添加对话 (输入空行结束):")

        count = 0
        while True:
            print(f"\n--- 对话 {count + 1} ---")
            user_msg = input("用户消息: ").strip()
            if not user_msg:
                break

            assistant_msg = input("助手回复: ").strip()
            if not assistant_msg:
                print("⚠️  助手回复不能为空，跳过此条")
                continue

            self.add_conversation(system_prompt, user_msg, assistant_msg, category, style)
            count += 1
            print(f"✅ 已添加 {count} 条对话")

        print(f"\n🎉 交互式创建完成！共添加 {count} 条对话")

    def create_from_template(self, template_type: str) -> None:
        """从模板创建数据集"""
        templates = {
            "qa": {
                "system_prompt": "你是一个知识渊博的AI助手，专门回答各种问题。请提供准确、详细的答案。",
                "category": "qa",
                "style": "informative",
                "examples": [
                    {
                        "user": "什么是机器学习？",
                        "assistant": "机器学习是人工智能的一个分支，它让计算机系统能够从数据中自动学习和改进，而无需被明确编程。主要包括监督学习、无监督学习和强化学习三大类型。"
                    },
                    {
                        "user": "Python和Java的主要区别是什么？",
                        "assistant": "Python和Java的主要区别包括：1) 语法简洁性：Python更简洁易读；2) 执行方式：Python是解释型，Java是编译型；3) 性能：Java通常执行更快；4) 应用场景：Python擅长数据科学，Java擅长企业应用。"
                    }
                ]
            },
            "assistant": {
                "system_prompt": "你是一个友好、乐于助人的AI助手。用温暖的语气回答用户问题，提供实用的帮助和建议。",
                "category": "assistant",
                "style": "friendly",
                "examples": [
                    {
                        "user": "我感觉工作压力很大，怎么办？",
                        "assistant": "我理解工作压力确实会让人感到疲惫。建议你可以尝试：1) 列出优先级，专注最重要的事；2) 适当休息，保证睡眠质量；3) 与同事或朋友交流，分享压力；4) 学习放松技巧，如深呼吸或冥想。记住，适度的压力是正常的，关键是找到平衡。"
                    },
                    {
                        "user": "推荐一些提高效率的工具",
                        "assistant": "很高兴为你推荐一些效率工具：1) 时间管理：Notion、Todoist；2) 笔记整理：Obsidian、RoamResearch；3) 专注工具：Forest、番茄工作法应用；4) 协作沟通：Slack、Zoom；5) 自动化：Zapier、IFTTT。选择适合你工作流程的1-2个工具即可，避免工具过多反而降低效率。"
                    }
                ]
            },
            "coding": {
                "system_prompt": "你是一个资深程序员，擅长多种编程语言和技术。请提供准确的代码示例和技术解释。",
                "category": "coding",
                "style": "technical",
                "examples": [
                    {
                        "user": "如何在Python中读取CSV文件？",
                        "assistant": "在Python中读取CSV文件有几种方法：\n\n使用pandas（推荐）：\n```python\nimport pandas as pd\ndf = pd.read_csv('file.csv')\nprint(df.head())\n```\n\n使用内置csv模块：\n```python\nimport csv\nwith open('file.csv', 'r') as f:\n    reader = csv.DictReader(f)\n    for row in reader:\n        print(row)\n```\n\npandas更适合数据分析，csv模块更轻量。"
                    }
                ]
            }
        }

        if template_type not in templates:
            print(f"❌ 未知模板类型: {template_type}")
            print(f"💡 可用模板: {', '.join(templates.keys())}")
            return

        template = templates[template_type]
        print(f"\n📝 使用 {template_type} 模板创建数据集")
        print(f"📋 系统提示: {template['system_prompt']}")

        for example in template['examples']:
            self.add_conversation(
                system_prompt=template['system_prompt'],
                user_message=example['user'],
                assistant_message=example['assistant'],
                category=template['category'],
                style=template['style']
            )

        print(f"✅ 模板数据添加完成，共 {len(template['examples'])} 条")

    def save_dataset(self, output_dir: Path, train_ratio: float = 0.9) -> None:
        """保存数据集为JSONL格式"""
        if not self.data:
            print("❌ 没有数据可保存")
            return

        output_dir.mkdir(parents=True, exist_ok=True)

        # 分割训练和验证集
        total = len(self.data)
        train_count = int(total * train_ratio)

        train_data = self.data[:train_count]
        val_data = self.data[train_count:]

        # 保存训练集
        train_path = output_dir / "train.jsonl"
        with open(train_path, 'w', encoding='utf-8') as f:
            for item in train_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')

        # 保存验证集
        val_path = output_dir / "val.jsonl"
        with open(val_path, 'w', encoding='utf-8') as f:
            for item in val_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')

        print(f"✅ 数据集保存完成:")
        print(f"   📈 训练集: {len(train_data)} 条 -> {train_path}")
        print(f"   📊 验证集: {len(val_data)} 条 -> {val_path}")
        print(f"   📝 总计: {total} 条对话")

    def export_template_csv(self, output_path: Path) -> None:
        """导出CSV模板文件"""
        template_data = [
            {
                'system_prompt': '你是一个有帮助的AI助手。请提供准确、有用的回答。',
                'user_message': '你好，你能帮我什么？',
                'assistant_message': '你好！我是AI助手，可以帮你解答问题、提供建议、协助思考等。有什么我可以帮助你的吗？',
                'category': 'greeting',
                'style': 'friendly'
            },
            {
                'system_prompt': '你是一个编程助手，擅长多种编程语言。',
                'user_message': '如何学习Python？',
                'assistant_message': '学习Python建议按以下步骤：1) 掌握基础语法；2) 练习小项目；3) 学习常用库；4) 参与开源项目。推荐资源：Python官方教程、LeetCode练习。',
                'category': 'coding',
                'style': 'educational'
            }
        ]

        df = pd.DataFrame(template_data)
        df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"✅ CSV模板已导出: {output_path}")
        print("💡 编辑此文件后可使用 --csv 参数导入")


def main():
    parser = argparse.ArgumentParser(description="自定义数据集创建工具")

    # 数据源选项
    parser.add_argument("--csv", type=str, help="从CSV文件导入数据")
    parser.add_argument("--json", type=str, help="从JSON文件导入数据")
    parser.add_argument("--interactive", action="store_true", help="交互式创建数据集")
    parser.add_argument("--template", type=str, choices=["qa", "assistant", "coding"],
                       help="从模板创建数据集")

    # 输出选项
    parser.add_argument("--output_dir", type=str, default="data",
                       help="输出目录 (默认: data)")
    parser.add_argument("--train_ratio", type=float, default=0.9,
                       help="训练集比例 (默认: 0.9)")

    # 工具选项
    parser.add_argument("--export_csv_template", type=str,
                       help="导出CSV模板文件")
    parser.add_argument("--merge_with_existing", action="store_true",
                       help="与现有数据集合并")

    args = parser.parse_args()

    # 导出CSV模板
    if args.export_csv_template:
        builder = DatasetBuilder()
        builder.export_template_csv(Path(args.export_csv_template))
        return

    print("🎯 自定义数据集创建工具")
    print("=" * 50)

    builder = DatasetBuilder()

    # 如果要合并现有数据，先加载
    if args.merge_with_existing:
        existing_train = Path(args.output_dir) / "train.jsonl"
        if existing_train.exists():
            print(f"📊 加载现有训练数据: {existing_train}")
            try:
                with open(existing_train, 'r', encoding='utf-8') as f:
                    for line in f:
                        data = json.loads(line.strip())
                        builder.data.append(data)
                print(f"✅ 加载了 {len(builder.data)} 条现有数据")
            except Exception as e:
                print(f"⚠️  加载现有数据失败: {e}")

    # 处理数据源
    if args.csv:
        builder.load_from_csv(Path(args.csv))
    elif args.json:
        builder.load_from_json(Path(args.json))
    elif args.interactive:
        builder.interactive_create()
    elif args.template:
        builder.create_from_template(args.template)
    else:
        print("❌ 请指定数据源:")
        print("   --csv FILE           # 从CSV导入")
        print("   --json FILE          # 从JSON导入")
        print("   --interactive        # 交互式创建")
        print("   --template TYPE      # 使用模板 (qa/assistant/coding)")
        print("\n💡 工具选项:")
        print("   --export_csv_template FILE  # 导出CSV模板")
        sys.exit(1)

    # 保存数据集
    if builder.data:
        builder.save_dataset(Path(args.output_dir), args.train_ratio)

        # 显示数据集统计
        print(f"\n📊 数据集统计:")
        categories = {}
        styles = {}
        for item in builder.data:
            cat = item.get('category', 'unknown')
            style = item.get('style', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1
            styles[style] = styles.get(style, 0) + 1

        print(f"   🏷️  类别分布: {dict(sorted(categories.items()))}")
        print(f"   🎨 风格分布: {dict(sorted(styles.items()))}")

        print(f"\n🚀 下一步:")
        print(f"   python train_to_ollama.py --ollama_name 'your-model-name'")
    else:
        print("❌ 没有生成任何数据")


if __name__ == "__main__":
    main()