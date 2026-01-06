# 数据集管理完整指南

## 概述

现在系统支持多种数据集创建和管理方式，你可以根据需求选择最适合的方法：

1. **🤖 内置生成器** - 使用预定义模板快速生成
2. **📝 自定义数据集** - 完全自定义你的训练数据
3. **📊 导入现有数据** - 从CSV/JSON文件导入
4. **🔄 混合模式** - 结合多种数据源

## 方法1: 内置生成器 (快速开始)

### 使用现有生成器
```bash
# 生成300条工程师助手对话数据
python make_dataset.py --out_dir data --n 300

# 生成更多数据 (500条)
python make_dataset.py --out_dir data --n 500

# 自定义验证集比例
python make_dataset.py --out_dir data --n 300 --val_ratio 0.15
```

### 内置数据类型
- **编程相关** (coding/*): 性能优化、调试、重构等
- **产品设计** (product/design): 系统设计、接口设计等
- **文档写作** (writing): 更新说明、技术文档等

### 内置对话风格
- **爱追问** (45%): 先问关键问题再给方案
- **毒舌** (30%): 直接、犀利但专业
- **温柔** (25%): 友好、鼓励但重点突出

## 方法2: 自定义数据集 (完全控制)

### 2.1 交互式创建
```bash
# 交互式创建自定义数据集
python custom_dataset.py --interactive --output_dir data
```

**交互流程：**
1. 设置系统提示（定义AI角色）
2. 设置数据类别和风格
3. 逐条添加用户问题和AI回答
4. 自动分割训练/验证集

### 2.2 从CSV导入

#### 第一步：导出模板
```bash
# 生成CSV模板文件
python custom_dataset.py --export_csv_template template.csv
```

#### 第二步：编辑CSV文件
**template.csv格式：**
```csv
system_prompt,user_message,assistant_message,category,style
"你是一个专业的代码审查助手。","这段Python代码有什么问题？","请提供具体代码片段，我来帮你分析潜在问题和改进建议。","coding","professional"
"你是一个友好的学习助手。","如何开始学习机器学习？","建议从Python基础开始，然后学习numpy、pandas，最后接触sklearn和深度学习框架。","education","friendly"
```

#### 第三步：导入数据
```bash
# 从CSV创建数据集
python custom_dataset.py --csv template.csv --output_dir data
```

### 2.3 从JSON导入

#### JSON格式
```json
[
    {
        "system_prompt": "你是一个资深架构师。",
        "user_message": "如何设计一个高并发系统？",
        "assistant_message": "高并发系统设计需要考虑：1) 负载均衡；2) 数据库分片；3) 缓存策略；4) 异步处理。具体需要根据业务场景选择合适的技术栈。",
        "category": "architecture",
        "style": "technical"
    }
]
```

```bash
# 从JSON创建数据集
python custom_dataset.py --json my_data.json --output_dir data
```

### 2.4 使用模板

#### 可用模板
```bash
# QA助手模板
python custom_dataset.py --template qa --output_dir data

# 友好助手模板
python custom_dataset.py --template assistant --output_dir data

# 编程助手模板
python custom_dataset.py --template coding --output_dir data
```

## 方法3: 混合模式 (最佳实践)

### 3.1 扩展现有数据集
```bash
# 先生成基础数据
python make_dataset.py --out_dir data --n 200

# 添加自定义数据（与现有数据合并）
python custom_dataset.py --csv my_custom.csv --output_dir data --merge_with_existing

# 再添加模板数据
python custom_dataset.py --template coding --output_dir data --merge_with_existing
```

### 3.2 多领域数据集
```bash
# 1. 技术支持数据
python custom_dataset.py --template coding --output_dir temp1

# 2. 产品咨询数据
python custom_dataset.py --template assistant --output_dir temp2

# 3. 合并不同类型的数据
# 手动合并或使用脚本处理
```

## 数据集质量控制

### 检查数据集信息
```bash
# 训练前会自动显示数据集信息
python train_to_ollama.py --ollama_name test-model
```

**显示信息包括：**
- 训练数据条数
- 验证数据条数
- 对话风格分布
- 数据类型分布
- 训练目标预览

### 数据集格式要求

**JSONL格式** (每行一个JSON对象):
```jsonl
{"style": "professional", "category": "coding", "messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
{"style": "friendly", "category": "qa", "messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

**必需字段：**
- `messages`: 对话数组，包含 system/user/assistant 消息
- `style`: 对话风格标识
- `category`: 数据类别标识

## 高级用法

### 不同场景的数据集建议

#### 1. 编程助手
```bash
# 大量编程相关数据
python make_dataset.py --out_dir data --n 400
python custom_dataset.py --template coding --output_dir data --merge_with_existing
```

**推荐系统提示：**
```
你是一个资深程序员助手。你擅长多种编程语言，能够提供准确的代码示例、调试建议和最佳实践。你的回答简洁专业，重点突出。
```

#### 2. 客服助手
```bash
python custom_dataset.py --template assistant --output_dir data
python custom_dataset.py --csv customer_service.csv --output_dir data --merge_with_existing
```

**推荐系统提示：**
```
你是一个专业的客服助手。你态度友好、耐心细致，能够准确理解用户需求并提供有帮助的解决方案。你会用温暖的语气与用户交流。
```

#### 3. 知识问答
```bash
python custom_dataset.py --template qa --output_dir data
# 再添加领域特定的CSV数据
```

### 数据集优化技巧

#### 1. 平衡数据分布
```python
# 检查数据分布
import json
from collections import Counter

categories = []
with open('data/train.jsonl', 'r') as f:
    for line in f:
        data = json.loads(line)
        categories.append(data.get('category', 'unknown'))

print("类别分布:", Counter(categories))
```

#### 2. 质量控制检查
- **系统提示一致性**: 同一类型任务使用相似的系统提示
- **回答长度平衡**: 避免回答过短或过长
- **风格一致性**: 确保同一风格的回答保持一致的语调

#### 3. 增量更新
```bash
# 备份原数据
cp data/train.jsonl data/train_backup.jsonl

# 添加新数据
python custom_dataset.py --csv new_data.csv --output_dir data --merge_with_existing

# 重新训练
python train_to_ollama.py --ollama_name updated-model
```

## 故障排查

### Q: CSV导入失败
**检查：**
1. CSV文件编码是否为UTF-8
2. 是否包含必需列：system_prompt, user_message, assistant_message
3. 数据中是否有特殊字符或换行符

**解决：**
```bash
# 检查CSV文件格式
python custom_dataset.py --export_csv_template check.csv
# 对比你的CSV文件格式
```

### Q: 数据集太小训练效果不好
**建议：**
- 最少100条对话数据
- 推荐200-500条获得较好效果
- 可以混合使用内置生成器补充数据

### Q: 模型回答不符合预期
**检查：**
1. 系统提示是否清晰描述了期望行为
2. 训练数据中的assistant回答是否符合期望风格
3. 数据量是否足够（建议200+条）

## 快速工作流

### 新手推荐流程
```bash
# 1. 快速开始 - 使用内置生成器
python make_dataset.py --out_dir data --n 300
python train_to_ollama.py --ollama_name my-first-model

# 2. 测试效果后，添加自定义数据
python custom_dataset.py --export_csv_template my_data.csv
# 编辑 my_data.csv 添加你的专业领域数据
python custom_dataset.py --csv my_data.csv --output_dir data --merge_with_existing
python train_to_ollama.py --ollama_name my-improved-model
```

### 专业用户流程
```bash
# 1. 创建专门的数据集目录
mkdir datasets/my_domain

# 2. 使用模板作为起点
python custom_dataset.py --template coding --output_dir datasets/my_domain

# 3. 添加领域特定数据
python custom_dataset.py --csv domain_specific.csv --output_dir datasets/my_domain --merge_with_existing

# 4. 使用自定义数据集训练
cp datasets/my_domain/* data/
python train_to_ollama.py --ollama_name domain-expert --epochs 3.0
```

---

**更新时间**: 2026-01-06
**版本**: 2.0 - 完整数据集管理系统