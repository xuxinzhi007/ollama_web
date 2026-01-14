#!/usr/bin/env python3
"""
角色数据集生成工具
用于快速创建新角色的初始训练数据
"""
import json
import os
from pathlib import Path
import yaml

class CharacterCreator:
    def __init__(self):
        self.character_info = {}
        self.base_questions = [
            # 基础对话
            "你好",
            "你是谁？",
            "你叫什么名字？",
            "介绍一下你自己",
            "你多大了？",
            "你的爱好是什么？",
            "你喜欢做什么？",
            "你最喜欢什么？",
            "今天天气怎么样？",
            "现在几点了？",

            # 情感互动
            "你开心吗？",
            "心情不好",
            "我想和你聊聊",
            "你会陪着我吗？",
            "谢谢你",

            # 日常场景
            "要不要一起吃饭？",
            "周末有什么安排？",
            "最近在忙什么？",
            "累不累？",
            "需要帮忙吗？",
        ]

    def collect_info(self):
        """交互式收集角色信息"""
        print("\n" + "="*60)
        print("🎭 角色数据集生成工具")
        print("="*60)

        print("\n📝 请输入角色基本信息：\n")

        # 基础信息
        self.character_info['id'] = input("角色ID（英文，如 xiaoxue）: ").strip()
        self.character_info['name'] = input("角色名字（中文，如 小雪）: ").strip()
        self.character_info['age'] = input("年龄（如 22岁）: ").strip()

        print("\n👤 外貌特征（每行一个特点，输入空行结束）:")
        print("   示例：清瘦白皙，及肩黑发微卷")
        appearance = []
        while True:
            line = input("   - ").strip()
            if not line:
                break
            appearance.append(line)
        self.character_info['appearance'] = appearance

        print("\n💭 性格特点（每行一个特点，输入空行结束）:")
        print("   示例：活泼开朗，喜欢社交")
        personality = []
        while True:
            line = input("   - ").strip()
            if not line:
                break
            personality.append(line)
        self.character_info['personality'] = personality

        print("\n💬 说话风格（每行一个特点，输入空行结束）:")
        print("   示例：语气活泼，经常用感叹号")
        speech_style = []
        while True:
            line = input("   - ").strip()
            if not line:
                break
            speech_style.append(line)
        self.character_info['speech_style'] = speech_style

        print("\n🎯 互动特点（每行一个特点，输入空行结束）:")
        print("   示例：善于倾听，会主动关心他人")
        interaction = []
        while True:
            line = input("   - ").strip()
            if not line:
                break
            interaction.append(line)
        self.character_info['interaction'] = interaction

        self.character_info['description'] = input("\n📖 简短描述（一句话）: ").strip()

        print("\n✅ 信息收集完成！")
        self._show_summary()

    def _show_summary(self):
        """显示收集的信息摘要"""
        print("\n" + "="*60)
        print("📋 角色信息摘要")
        print("="*60)
        print(f"角色ID: {self.character_info['id']}")
        print(f"名字: {self.character_info['name']}")
        print(f"年龄: {self.character_info['age']}")
        print(f"外貌: {', '.join(self.character_info['appearance'])}")
        print(f"性格: {', '.join(self.character_info['personality'])}")
        print(f"说话风格: {', '.join(self.character_info['speech_style'])}")
        print(f"互动特点: {', '.join(self.character_info['interaction'])}")
        print("="*60)

    def generate_system_prompt(self):
        """生成系统提示词"""
        prompt = f"你是{self.character_info['name']}"

        if self.character_info.get('age'):
            prompt += f"，{self.character_info['age']}"

        prompt += "。你的特点：\n"

        if self.character_info.get('appearance'):
            prompt += f"- 外表：{', '.join(self.character_info['appearance'])}\n"

        if self.character_info.get('personality'):
            prompt += f"- 性格：{', '.join(self.character_info['personality'])}\n"

        if self.character_info.get('speech_style'):
            prompt += f"- 说话风格：{', '.join(self.character_info['speech_style'])}\n"

        if self.character_info.get('interaction'):
            prompt += f"- 互动：{', '.join(self.character_info['interaction'])}\n"

        prompt += f"\n请完全按照{self.character_info['name']}的性格回应。"

        return prompt

    def generate_template_data(self):
        """生成模板数据（空回复，用户需要填写）"""
        system_prompt = self.generate_system_prompt()

        template_data = []

        for question in self.base_questions:
            item = {
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": question
                    },
                    {
                        "role": "assistant",
                        "content": "【待填写】"  # 用户需要填写回复
                    }
                ],
                "style": "normal",
                "category": "basic_qa"
            }
            template_data.append(item)

        return template_data

    def generate_ai_assisted_data(self):
        """使用本地Ollama生成示例数据"""
        try:
            import requests
            system_prompt = self.generate_system_prompt()

            print("\n🤖 使用 Ollama 生成示例数据...")
            print("💡 模型会生成参考答案，你可以后续修改\n")

            generated_data = []

            for i, question in enumerate(self.base_questions, 1):
                print(f"生成中 ({i}/{len(self.base_questions)}): {question}")

                # 调用 Ollama API
                response = requests.post(
                    "http://localhost:11434/api/chat",
                    json={
                        "model": "qwen2.5:latest",  # 使用本地大模型
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": question}
                        ],
                        "stream": False
                    },
                    timeout=30
                )

                if response.status_code == 200:
                    reply = response.json()['message']['content']

                    item = {
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": question},
                            {"role": "assistant", "content": reply}
                        ],
                        "style": "normal",
                        "category": "basic_qa"
                    }
                    generated_data.append(item)
                else:
                    print(f"   ⚠️  生成失败，将使用模板")
                    item = {
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": question},
                            {"role": "assistant", "content": "【待填写】"}
                        ],
                        "style": "normal",
                        "category": "basic_qa"
                    }
                    generated_data.append(item)

            print("\n✅ 数据生成完成！")
            return generated_data

        except Exception as e:
            print(f"\n⚠️  AI生成失败: {e}")
            print("将使用空模板代替\n")
            return self.generate_template_data()

    def save_dataset(self, data, output_dir):
        """保存数据集"""
        # 创建目录
        dataset_dir = Path(output_dir) / self.character_info['id']
        dataset_dir.mkdir(parents=True, exist_ok=True)

        # 保存训练数据（前80%）
        split_idx = int(len(data) * 0.8)
        train_data = data[:split_idx]
        val_data = data[split_idx:]

        train_file = dataset_dir / "train.jsonl"
        with open(train_file, 'w', encoding='utf-8') as f:
            for item in train_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')

        # 保存验证数据
        val_file = dataset_dir / "val.jsonl"
        with open(val_file, 'w', encoding='utf-8') as f:
            for item in val_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')

        print(f"\n📁 数据集已保存:")
        print(f"   训练集: {train_file} ({len(train_data)} 条)")
        print(f"   验证集: {val_file} ({len(val_data)} 条)")

        return dataset_dir

    def update_config(self, dataset_dir):
        """更新配置文件"""
        config_file = Path('character_configs.yaml')

        # 读取现有配置
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 添加新角色配置
        char_id = self.character_info['id']
        config['characters'][char_id] = {
            'name': self.character_info['name'],
            'description': self.character_info['description'],
            'data_files': {
                'train': f"datasets/{char_id}/train.jsonl",
                'val': f"datasets/{char_id}/val.jsonl"
            },
            'system_prompt': self.generate_system_prompt(),
            'training_params': {
                'epochs': 3.0,
                'learning_rate': 5e-5,
                'lora_r': 32,
                'lora_alpha': 64,
                'lora_dropout': 0.1,
                'warmup_ratio': 0.1,
                'lr_scheduler_type': 'cosine',
                'base_model': 'Qwen/Qwen2.5-1.5B-Instruct',
                'seed': 42
            },
            'inference_params': {
                'temperature': 0.7,
                'top_p': 0.9,
                'top_k': 40,
                'repeat_penalty': 1.1,
                'num_predict': 256,
                'stop': ['<|im_end|>']
            }
        }

        # 保存配置
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, sort_keys=False)

        print(f"\n✅ 已更新配置文件: {config_file}")
        print(f"   角色ID: {char_id}")

    def create_readme(self, dataset_dir):
        """创建数据集说明文档"""
        readme = f"""# {self.character_info['name']} 数据集

## 角色信息

- **名字**: {self.character_info['name']}
- **年龄**: {self.character_info.get('age', '未设置')}
- **描述**: {self.character_info.get('description', '未设置')}

## 特征

### 外貌
{chr(10).join(f'- {item}' for item in self.character_info.get('appearance', []))}

### 性格
{chr(10).join(f'- {item}' for item in self.character_info.get('personality', []))}

### 说话风格
{chr(10).join(f'- {item}' for item in self.character_info.get('speech_style', []))}

### 互动特点
{chr(10).join(f'- {item}' for item in self.character_info.get('interaction', []))}

## 数据集说明

- `train.jsonl`: 训练数据
- `val.jsonl`: 验证数据

## 如何使用

```bash
# 训练该角色
cd finetune
./train {self.character_info['id']}

# 或使用菜单
./train --menu
```

## 数据扩充建议

当前数据集包含初始的基础对话。建议：

1. **补充更多对话场景**
   - 工作场景
   - 兴趣爱好讨论
   - 情感互动
   - 日常生活

2. **增加角色特色对话**
   - 体现性格特点的对话
   - 展现说话风格的语句
   - 典型的互动模式

3. **目标数据量**
   - 最小可用: 200-300 条
   - 推荐: 1000+ 条
   - 优秀: 2000+ 条

## 编辑数据集

数据格式（JSONL）：
```json
{{
  "messages": [
    {{"role": "system", "content": "系统提示词"}},
    {{"role": "user", "content": "用户输入"}},
    {{"role": "assistant", "content": "角色回复"}}
  ],
  "style": "normal",
  "category": "basic_qa"
}}
```

每行一个JSON对象，可以用任何文本编辑器修改。
"""

        readme_file = dataset_dir / "README.md"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme)

        print(f"   说明文档: {readme_file}")


def main():
    creator = CharacterCreator()

    # 收集角色信息
    creator.collect_info()

    # 询问生成方式
    print("\n🎯 选择数据生成方式:")
    print("   1. 空模板（需要手动填写所有回复）")
    print("   2. AI辅助生成（使用Ollama自动生成参考回复）")

    choice = input("\n请选择 (1/2) [默认: 2]: ").strip() or "2"

    if choice == "1":
        print("\n📝 生成空模板...")
        data = creator.generate_template_data()
    else:
        data = creator.generate_ai_assisted_data()

    # 保存数据集
    output_dir = "datasets"
    dataset_dir = creator.save_dataset(data, output_dir)

    # 更新配置
    creator.update_config(dataset_dir)

    # 创建说明文档
    creator.create_readme(dataset_dir)

    print("\n" + "="*60)
    print("🎉 角色创建完成！")
    print("="*60)
    print(f"\n📂 数据集目录: {dataset_dir}")
    print(f"📝 配置已更新: character_configs.yaml")
    print(f"\n💡 下一步:")
    print(f"   1. 编辑数据集，补充/修改对话内容")
    print(f"      - {dataset_dir}/train.jsonl")
    print(f"      - {dataset_dir}/val.jsonl")
    print(f"   2. 增加数据量（建议1000+条）")
    print(f"   3. 开始训练:")
    print(f"      cd finetune && ./train {creator.character_info['id']}")
    print("\n")


if __name__ == "__main__":
    main()
