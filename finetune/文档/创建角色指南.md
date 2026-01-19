# 角色数据集创建指南

## 🎯 快速开始

```bash
cd finetune
python3 create_character.py
```

## 📝 使用流程

### 1. 运行工具
```bash
python3 create_character.py
```

### 2. 输入角色信息

工具会依次询问：

**基础信息**
- 角色ID（英文，如 xiaoxue）
- 角色名字（中文，如 小雪）
- 年龄（如 22岁）

**外貌特征**（每行一个，空行结束）
```
示例：
- 清瘦白皙，及肩黑发微卷
- 大眼睛，笑起来有小酒窝
```

**性格特点**（每行一个，空行结束）
```
示例：
- 活泼开朗，喜欢社交
- 善解人意，乐于助人
```

**说话风格**（每行一个，空行结束）
```
示例：
- 语气活泼，经常用感叹号
- 喜欢用"嗯嗯"、"哇"等语气词
```

**互动特点**（每行一个，空行结束）
```
示例：
- 善于倾听，会主动关心他人
- 表达直接，不会拐弯抹角
```

**简短描述**（一句话）
```
示例：活泼开朗的22岁女大学生
```

### 3. 选择生成方式

**选项1：空模板**
- 生成带"【待填写】"占位符的模板
- 需要手动填写所有回复
- 适合完全自定义内容

**选项2：AI辅助生成（推荐）**
- 使用本地Ollama自动生成参考回复
- 可以后续修改和优化
- 快速获得初始数据集

### 4. 自动完成的工作

工具会自动：
- ✅ 生成 `datasets/{角色ID}/train.jsonl`（训练集，80%）
- ✅ 生成 `datasets/{角色ID}/val.jsonl`（验证集，20%）
- ✅ 更新 `character_configs.yaml`（添加角色配置）
- ✅ 创建 `datasets/{角色ID}/README.md`（说明文档）

## 📊 生成的数据集

### 初始数据量
- **20条基础对话**：涵盖常见场景
- **自动拆分**：80% 训练集 + 20% 验证集

### 基础问题类型

**基础对话**
- 你好、你是谁、介绍自己
- 年龄、爱好、喜欢做什么

**情感互动**
- 你开心吗、心情不好
- 我想和你聊聊、你会陪着我吗

**日常场景**
- 要不要一起吃饭、周末有什么安排
- 最近在忙什么、累不累

## 🔧 数据扩充建议

初始20条数据**仅供测试**，建议扩充到：

### 最小可用量：200-300条
- 能训练出基本角色特征
- 对话可能较单一

### 推荐量：1000+条
- 角色特征稳定
- 对话自然流畅
- 场景覆盖全面

### 优秀量：2000+条
- 角色个性鲜明
- 能应对复杂场景
- 情感表达细腻

## 📝 编辑数据集

### 数据格式（JSONL）
```json
{
  "messages": [
    {
      "role": "system",
      "content": "你是小雪，22岁，活泼开朗的女大学生..."
    },
    {
      "role": "user",
      "content": "你好呀！"
    },
    {
      "role": "assistant",
      "content": "嗨嗨！你好呀！今天天气真不错呢！"
    }
  ],
  "style": "normal",
  "category": "basic_qa"
}
```

### 编辑方法

**方法1：文本编辑器**
```bash
# 用任何文本编辑器打开
code datasets/xiaoxue/train.jsonl
vim datasets/xiaoxue/train.jsonl
```

**方法2：Python脚本批量生成**
```python
import json

# 读取现有数据
with open('datasets/xiaoxue/train.jsonl', 'r') as f:
    data = [json.loads(line) for line in f]

# 添加新对话
new_item = {
    "messages": [
        {"role": "system", "content": "系统提示词"},
        {"role": "user", "content": "新问题"},
        {"role": "assistant", "content": "新回复"}
    ],
    "style": "normal",
    "category": "daily_chat"
}
data.append(new_item)

# 保存
with open('datasets/xiaoxue/train.jsonl', 'w') as f:
    for item in data:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')
```

## 🚀 开始训练

### 查看所有角色
```bash
cd finetune
./train --menu
```

### 直接训练
```bash
cd finetune
./train xiaoxue  # 替换为你的角色ID
```

## 📖 配置说明

工具会自动在 `character_configs.yaml` 中添加：

```yaml
xiaoxue:
  name: "小雪"
  description: "活泼开朗的22岁女大学生"
  data_files:
    train: "datasets/xiaoxue/train.jsonl"
    val: "datasets/xiaoxue/val.jsonl"
  system_prompt: |
    你是小雪，22岁。你的特点：
    - 外表：清瘦白皙，及肩黑发微卷
    - 性格：活泼开朗，喜欢社交
    - 说话风格：语气活泼，经常用感叹号
    - 互动：善于倾听，会主动关心他人

    请完全按照小雪的性格回应。
  training_params:
    epochs: 3.0
    learning_rate: 5e-5
    lora_r: 32
    lora_alpha: 64
    lora_dropout: 0.1
    warmup_ratio: 0.1
    lr_scheduler_type: 'cosine'
    base_model: 'Qwen/Qwen2.5-1.5B-Instruct'
    seed: 42
  inference_params:
    temperature: 0.7
    top_p: 0.9
    top_k: 40
    repeat_penalty: 1.1
    num_predict: 256
    stop: ['<|im_end|>']
```

### 参数调整建议

**训练参数**
- `epochs`: 2-4轮，数据多用少一点
- `learning_rate`: 3e-5到1e-4，数据少用大一点
- `lora_r`: 16-64，数据多用大一点

**推理参数**
- `temperature`: 0.5-0.8，活泼角色用高一点
- `top_p`: 0.85-0.95，创造性要求高用大一点
- `num_predict`: 200-500，细腻角色用大一点

## ⚠️ 常见问题

### Q: Ollama连接失败怎么办？
确保Ollama正在运行：
```bash
# 启动Ollama
ollama serve

# 测试连接
curl http://localhost:11434/api/tags
```

### Q: AI生成的回复不满意？
- 选择"空模板"模式，完全手动填写
- 或者先用AI生成，再手动修改

### Q: 20条数据够用吗？
- **不够**，仅供快速测试
- 建议至少补充到200条
- 推荐1000+条获得好效果

### Q: 如何添加更多数据？
1. 直接编辑 `.jsonl` 文件
2. 复制现有条目，修改内容
3. 保持JSON格式正确
4. 每行一个JSON对象

### Q: 可以修改生成的system_prompt吗？
可以！直接编辑 `character_configs.yaml` 中的 `system_prompt` 字段。

## 💡 最佳实践

### 1. 数据质量 > 数量
- 100条高质量对话 > 500条低质量对话
- 确保每条对话体现角色特征

### 2. 场景多样化
- 不要只有基础问答
- 加入：工作、兴趣、情感、日常等场景

### 3. 语言风格一致
- 统一使用角色的说话方式
- 注意语气词、标点符号的使用

### 4. 测试-修改-迭代
```bash
# 1. 用小数据快速训练测试
cd finetune
./train xiaoxue

# 2. 测试效果
# 在Web UI或命令行测试对话

# 3. 根据效果调整数据或参数
# 编辑 datasets/xiaoxue/train.jsonl

# 4. 重新训练
./train xiaoxue
```

## 📚 参考资料

- **训练参数详解**：查看 `PARAMETER_GUIDE.md`
- **训练详细用法**：查看 `USAGE_GUIDE.md`
- **现有角色示例**：查看 `datasets/linzhi/`

---

**工具位置**: `finetune/create_character.py`
**生成目录**: `finetune/datasets/{角色ID}/`
**配置文件**: `finetune/character_configs.yaml`
