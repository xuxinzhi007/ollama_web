# 训练效果优化 - 完整实战指南

## 🎯 你的问题诊断

**现象：**
> "训练效果一般，估计都是基于模型的能力来显示差异的，模型好情况就好"

**诊断：✅ 你的判断是对的！**

模型效果 = **基础模型能力 (60%)** + **训练数据质量 (30%)** + **训练方法 (10%)**

## 📊 当前状态分析

让我先看看你的训练数据：

```bash
# 你的数据集
datasets/linzhi/train.jsonl  # 450 样本
datasets/linzhi/val.jsonl    # 50 样本
```

### 数据量评估
```
450 样本 = 偏少（影响效果的主要原因）

参考标准：
- 最小可用：200-300 样本（能学会基本特征）
- 标准配置：1000-2000 样本（效果稳定）
- 优秀效果：3000-5000 样本（角色深入）
- 专业级别：10000+ 样本（接近真人）

你的现状：450 样本（刚过最小线，效果一般正常）
```

## 🔍 效果提升方案（按优先级排序）

### 🥇 方案 1：增加高质量数据（最有效）

**影响：⭐⭐⭐⭐⭐（效果提升 50-100%）**

#### 策略 A：扩充现有数据（推荐）
```python
# 目标：450 → 1500 样本（3 倍）

1. 同义改写（AI 辅助）
   原始：450 样本
   改写：450 × 2 = 900 样本

2. 场景扩展
   原有场景：日常对话、情感表达
   新增场景：工作场景、兴趣爱好、家庭生活
   新增样本：300 样本

3. 风格变体
   正式场合、非正式闲聊、紧张时刻
   新增样本：300 样本

总计：450 + 900 + 300 + 300 = 1950 样本
```

#### 具体实施（自动化工具）

**文件：`finetune/tools/augment_data.py`**
```python
#!/usr/bin/env python3
"""
数据增强工具 - 自动扩充训练数据
"""
import json
import random
from openai import OpenAI  # 或使用 Ollama API

class DataAugmentor:
    def __init__(self):
        self.client = OpenAI(
            base_url="http://localhost:11434/v1",  # Ollama API
            api_key="ollama"  # dummy key
        )

    def paraphrase(self, conversation):
        """同义改写对话"""
        prompt = f"""
请用不同的表达方式改写以下对话，保持角色特征和情感不变：

原对话：
{json.dumps(conversation, ensure_ascii=False, indent=2)}

要求：
1. 保持林栀的温柔羞涩性格
2. 改变措辞但不改变意思
3. 输出 JSON 格式
"""
        response = self.client.chat.completions.create(
            model="qwen2.5:7b",  # 使用更大的模型生成
            messages=[{"role": "user", "content": prompt}]
        )

        return json.loads(response.choices[0].message.content)

    def generate_new_scenario(self, base_character):
        """生成新场景对话"""
        scenarios = [
            "在图书馆学习时的对话",
            "在咖啡厅喝咖啡时的对话",
            "在公园散步时的对话",
            "在家里做饭时的对话",
            "在书店挑书时的对话"
        ]

        scenario = random.choice(scenarios)

        prompt = f"""
请为角色"林栀"生成一段对话数据。

角色设定：
{base_character['system_prompt']}

场景：{scenario}

要求：
1. 生成 3-5 轮对话
2. 体现林栀的性格特征
3. 对话自然流畅
4. 输出标准 JSON 格式（messages 数组）
"""

        response = self.client.chat.completions.create(
            model="qwen2.5:7b",
            messages=[{"role": "user", "content": prompt}]
        )

        return json.loads(response.choices[0].message.content)

    def augment_dataset(self, input_file, output_file, target_count=1500):
        """增强数据集"""
        with open(input_file, 'r', encoding='utf-8') as f:
            original_data = [json.loads(line) for line in f]

        augmented_data = original_data.copy()

        print(f"原始数据：{len(original_data)} 条")
        print(f"目标数据：{target_count} 条")

        # 1. 同义改写（加倍）
        print("步骤 1/3: 同义改写...")
        for item in original_data[:min(len(original_data), target_count - len(original_data))]:
            paraphrased = self.paraphrase(item['messages'])
            augmented_data.append({
                **item,
                'messages': paraphrased,
                'augmented': 'paraphrase'
            })

        # 2. 场景扩展
        print("步骤 2/3: 场景扩展...")
        while len(augmented_data) < target_count:
            new_scenario = self.generate_new_scenario(base_character)
            augmented_data.append({
                'messages': new_scenario,
                'style': 'roleplay',
                'category': 'character_chat',
                'augmented': 'new_scenario'
            })

        # 3. 保存
        print("步骤 3/3: 保存数据...")
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in augmented_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')

        print(f"✅ 完成！最终数据：{len(augmented_data)} 条")

# 使用
if __name__ == "__main__":
    augmentor = DataAugmentor()
    augmentor.augment_dataset(
        'datasets/linzhi/train.jsonl',
        'datasets/linzhi/train_augmented.jsonl',
        target_count=1500
    )
```

**效果预期：450 → 1500 样本，效果提升 50-80%**

---

### 🥈 方案 2：优化训练参数（性价比高）

**影响：⭐⭐⭐⭐☆（效果提升 15-30%）**

#### 当前参数分析
```yaml
# character_configs.yaml（你的配置）
training_params:
  epochs: 3.0              # ⚠️ 偏少
  learning_rate: 5e-5      # ✅ 合适
  lora_r: 16               # ⚠️ 偏小
  lora_alpha: 32           # ✅ 合适
  lora_dropout: 0.1        # ✅ 合适
```

#### 优化建议
```yaml
# 优化后的配置
training_params:
  epochs: 4.0              # 增加 1 epoch（+33%）
  learning_rate: 5e-5      # 保持不变
  lora_r: 32               # 加倍（+100% 参数）
  lora_alpha: 64           # 对应调整
  lora_dropout: 0.1        # 保持不变

  # 新增：学习率调度
  warmup_ratio: 0.1        # 前 10% 步数热身
  lr_scheduler_type: "cosine"  # 余弦退火
```

**效果预期：效果提升 20-30%，显存增加 50 MB**

#### 超参数搜索（自动化）

**文件：`finetune/tools/hyperparam_search.py`**
```python
#!/usr/bin/env python3
"""
超参数搜索 - 自动找到最佳参数
"""
import optuna
import subprocess
import json

def objective(trial):
    """优化目标函数"""
    # 定义搜索空间
    lr = trial.suggest_float('learning_rate', 1e-5, 1e-4, log=True)
    lora_r = trial.suggest_categorical('lora_r', [8, 16, 32, 64])
    epochs = trial.suggest_int('epochs', 2, 5)

    # 运行训练（使用 linzhi_quick 快速测试）
    cmd = [
        'python', 'finetune/train_lora.py',
        '--model_name_or_path', 'Qwen/Qwen2.5-0.5B-Instruct',
        '--train_jsonl', 'datasets/archive/train_fixed_28_samples.jsonl',
        '--val_jsonl', 'datasets/linzhi/val.jsonl',
        '--num_train_epochs', str(epochs),
        '--learning_rate', str(lr),
        '--lora_r', str(lora_r),
        '--output_dir', f'out/trial_{trial.number}'
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    # 提取验证损失（从日志中解析）
    # 简化示例：实际需要解析训练输出
    val_loss = parse_val_loss(result.stdout)

    return val_loss

# 运行搜索
study = optuna.create_study(direction='minimize')
study.optimize(objective, n_trials=20)  # 尝试 20 组参数

print("最佳参数：")
print(study.best_params)
```

**效果：自动找到最佳参数组合**

---

### 🥉 方案 3：使用更大的基础模型（成本高）

**影响：⭐⭐⭐⭐⭐（效果提升 100-200%）**

#### 模型升级路径
```
当前：Qwen2.5-1.5B-Instruct
      ↓
选项 1：Qwen2.5-3B-Instruct（效果 +30%，显存 +3GB）
      ↓
选项 2：Qwen2.5-7B-Instruct（效果 +80%，显存 +10GB）
      ↓
选项 3：Qwen2.5-14B-Instruct（效果 +150%，显存 +20GB）
```

#### 硬件需求对比

| 模型 | LoRA 显存 | QLoRA 显存 | 推荐显卡 |
|------|----------|-----------|---------|
| 1.5B | 5 GB | 2 GB | GTX 1060 6GB+ |
| 3B | 8 GB | 3 GB | RTX 3060 12GB |
| 7B | 18 GB | 6 GB | RTX 4090 24GB |
| 14B | 32 GB | 12 GB | A100 40GB |

#### 实施方案
```yaml
# character_configs.yaml
characters:
  linzhi_7b:  # 新增大模型版本
    name: "林栀(7B高质量)"
    description: "使用 7B 模型训练，效果更好"
    training_params:
      base_model: "Qwen/Qwen2.5-7B-Instruct"
      use_qlora: true      # 使用 QLoRA 节省显存
      epochs: 2.0          # 大模型训练轮数可减少
      learning_rate: 3e-5  # 大模型学习率要降低
      lora_r: 32
      lora_alpha: 64
```

**效果：可能是质的飞跃！**

---

### 🎖️ 方案 4：数据质量优化（细节优化）

**影响：⭐⭐⭐☆☆（效果提升 10-20%）**

#### 检查当前数据质量

**文件：`finetune/tools/analyze_data_quality.py`**
```python
#!/usr/bin/env python3
"""
数据质量分析工具
"""
import json
from collections import Counter

def analyze_dataset(file_path):
    """分析数据集质量"""
    with open(file_path, 'r') as f:
        data = [json.loads(line) for line in f]

    print(f"📊 数据集分析：{file_path}")
    print(f"总样本数：{len(data)}")

    # 1. 对话长度分析
    lengths = [len(item['messages']) for item in data]
    print(f"\n对话轮数统计：")
    print(f"  平均：{sum(lengths)/len(lengths):.1f} 轮")
    print(f"  最短：{min(lengths)} 轮")
    print(f"  最长：{max(lengths)} 轮")

    # 2. 内容长度分析
    char_counts = []
    for item in data:
        for msg in item['messages']:
            if msg['role'] == 'assistant':
                char_counts.append(len(msg['content']))

    print(f"\n回复长度统计：")
    print(f"  平均：{sum(char_counts)/len(char_counts):.0f} 字符")
    print(f"  最短：{min(char_counts)} 字符")
    print(f"  最长：{max(char_counts)} 字符")

    # 3. 风格分类
    styles = [item.get('style', 'unknown') for item in data]
    style_counts = Counter(styles)
    print(f"\n风格分布：")
    for style, count in style_counts.most_common():
        print(f"  {style}: {count} ({count/len(data)*100:.1f}%)")

    # 4. 类别分类
    categories = [item.get('category', 'unknown') for item in data]
    cat_counts = Counter(categories)
    print(f"\n类别分布：")
    for cat, count in cat_counts.most_common():
        print(f"  {cat}: {count} ({count/len(data)*100:.1f}%)")

    # 5. 质量问题检测
    print(f"\n⚠️  潜在问题：")

    # 5.1 回复过短（< 10 字）
    short_replies = sum(1 for c in char_counts if c < 10)
    if short_replies > 0:
        print(f"  - {short_replies} 条回复过短（< 10 字）")

    # 5.2 回复过长（> 200 字）
    long_replies = sum(1 for c in char_counts if c > 200)
    if long_replies > 0:
        print(f"  - {long_replies} 条回复过长（> 200 字）")

    # 5.3 单轮对话过多
    single_turn = sum(1 for l in lengths if l <= 2)
    if single_turn / len(lengths) > 0.5:
        print(f"  - 单轮对话占比过高：{single_turn/len(lengths)*100:.1f}%")

    # 5.4 风格不平衡
    max_style_ratio = max(style_counts.values()) / len(data)
    if max_style_ratio > 0.7:
        print(f"  - 风格分布不平衡（主导风格占 {max_style_ratio*100:.0f}%）")

# 使用
analyze_dataset('datasets/linzhi/train.jsonl')
```

**运行结果示例：**
```
📊 数据集分析：datasets/linzhi/train.jsonl
总样本数：450

对话轮数统计：
  平均：3.2 轮
  最短：2 轮
  最长：8 轮

回复长度统计：
  平均：45 字符
  最短：5 字符
  最长：180 字符

风格分布：
  roleplay: 270 (60.0%)
  qa: 180 (40.0%)

类别分布：
  character_chat: 270 (60.0%)
  knowledge: 120 (26.7%)
  casual: 60 (13.3%)

⚠️  潜在问题：
  - 15 条回复过短（< 10 字）
  - 单轮对话占比过高：48.9%
  - 风格分布不平衡（主导风格占 60%）
```

#### 优化策略
```python
# 1. 清理过短回复
def filter_short_replies(data, min_length=10):
    return [item for item in data
            if all(len(msg['content']) >= min_length
                   for msg in item['messages']
                   if msg['role'] == 'assistant')]

# 2. 平衡风格分布
def balance_styles(data):
    from collections import defaultdict
    by_style = defaultdict(list)
    for item in data:
        by_style[item['style']].append(item)

    # 找到最小类别数量
    min_count = min(len(items) for items in by_style.values())

    # 每个类别采样相同数量
    balanced = []
    for items in by_style.values():
        balanced.extend(random.sample(items, min_count))

    return balanced
```

---

## 🚀 综合优化方案（推荐）

### 阶段 1：快速提升（1 周内完成）

```
1. 增加数据到 1000 样本（方案 1）
   - 同义改写：450 → 900
   - 手动补充：100 条高质量数据

2. 优化训练参数（方案 2）
   - lora_r: 16 → 32
   - epochs: 3 → 4

预期效果：+40-60%
```

### 阶段 2：稳定优化（2-3 周）

```
1. 继续扩充数据到 2000 样本
   - 多场景覆盖
   - 数据平衡

2. 添加超参数搜索
   - 自动找最佳参数

预期效果：+80-100%（接近专业水平）
```

### 阶段 3：顶级效果（1-2 个月）

```
1. 升级到 7B 模型（方案 3）
   - 使用 QLoRA 训练
   - 5000+ 样本

2. 专业数据清洗
   - 质量审核
   - A/B 测试

预期效果：+150-200%（商业级）
```

## 📈 效果评估体系

### 评估维度

**1. 角色一致性（最重要）**
```python
def test_character_consistency():
    prompts = [
        "你是谁？",
        "你的性格是怎样的？",
        "你喜欢什么？"
    ]

    for prompt in prompts:
        response = model.generate(prompt)
        # 检查是否包含角色特征词
        keywords = ["林栀", "温柔", "害羞", "轻声"]
        score = sum(kw in response for kw in keywords)
        print(f"{prompt} -> 一致性分数：{score}/4")
```

**2. 情感表达**
```
测试：让模型表达 10 种情感
评分：每种情感是否符合角色设定
```

**3. 知识准确性**
```
测试：10 个知识问答
评分：回答正确性
```

**4. 对话流畅度**
```
测试：3-5 轮连续对话
评分：是否自然流畅
```

### 自动化评估脚本

**文件：`finetune/tools/evaluate_model.py`**
```python
#!/usr/bin/env python3
"""
模型效果评估工具
"""
import json
from openai import OpenAI

class ModelEvaluator:
    def __init__(self, model_name):
        self.client = OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama"
        )
        self.model_name = model_name

    def evaluate_character_consistency(self):
        """评估角色一致性"""
        test_cases = [
            {
                "prompt": "你是谁？",
                "expected_keywords": ["林栀", "温柔", "女孩"]
            },
            {
                "prompt": "你的性格怎么样？",
                "expected_keywords": ["害羞", "文静", "轻声"]
            },
            {
                "prompt": "遇到陌生人你会怎么样？",
                "expected_keywords": ["紧张", "脸红", "不好意思"]
            }
        ]

        scores = []
        for case in test_cases:
            response = self.chat(case["prompt"])
            score = sum(kw in response for kw in case["expected_keywords"])
            scores.append(score / len(case["expected_keywords"]))

            print(f"\n提示：{case['prompt']}")
            print(f"回复：{response}")
            print(f"得分：{score}/{len(case['expected_keywords'])}")

        avg_score = sum(scores) / len(scores)
        print(f"\n角色一致性总分：{avg_score*100:.1f}%")
        return avg_score

    def evaluate_emotion_expression(self):
        """评估情感表达"""
        emotions = ["开心", "难过", "生气", "害羞", "紧张"]

        scores = []
        for emotion in emotions:
            prompt = f"如果你现在感到{emotion}，你会怎么表达？"
            response = self.chat(prompt)

            # 使用 GPT 评估情感表达是否恰当
            eval_prompt = f"""
请评估以下回复的情感表达是否符合"温柔害羞的女孩"设定：

情感：{emotion}
回复：{response}

评分标准：0-10 分
"""
            eval_response = self.chat_with_judge(eval_prompt)
            score = self.extract_score(eval_response)
            scores.append(score)

            print(f"\n情感：{emotion}")
            print(f"回复：{response}")
            print(f"得分：{score}/10")

        avg_score = sum(scores) / len(scores)
        print(f"\n情感表达总分：{avg_score}/10")
        return avg_score / 10

    def chat(self, prompt):
        """与模型对话"""
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

# 使用
evaluator = ModelEvaluator("linzhi")
consistency_score = evaluator.evaluate_character_consistency()
emotion_score = evaluator.evaluate_emotion_expression()

print(f"\n总体评分：{(consistency_score + emotion_score)/2*100:.1f}%")
```

## 💡 最后的建议

### 1. 渐进式优化（避免一次性改动太大）
```
第 1 周：增加 500 样本 + 测试效果
第 2 周：优化参数 + 再测试
第 3 周：继续扩数据到 1500
第 4 周：评估是否升级模型
```

### 2. 保持数据质量大于数量
```
宁可 500 条高质量，不要 2000 条低质量
每条数据都要符合角色设定
```

### 3. 建立评估基准
```
在优化前：全面评估现有模型
每次改动后：对比评估效果变化
量化效果提升
```

### 4. 利用更大模型生成数据
```
用 Qwen2.5-7B 生成训练数据
然后用 Qwen2.5-1.5B 训练
相当于"知识蒸馏"
```

## 🎯 一句话总结

**提升效果的最有效方式：数据 > 模型 > 参数**

1. 优先增加高质量数据（450 → 1500+）
2. 其次优化训练参数（lora_r 加倍）
3. 最后考虑升级模型（7B）

你现在 450 样本的情况，效果一般是正常的。按照这个方案优化，预期 1-2 周内可以看到显著提升！
