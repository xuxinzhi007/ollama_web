# 过拟合问题修复指南

## 🔴 问题现象

模型输出完全混乱，包含训练数据的格式：
```
你的特点：
- 外表：清瘦白皙...
- 性格：文静少言...
```

模型在"背诵"训练数据，而不是正常对话。

## 🔍 根本原因

### 1. **数据格式问题** ⭐⭐⭐⭐⭐

**问题：每个样本都包含完整的system prompt**

```json
{
  "messages": [
    {"role": "system", "content": "你是林栀...你的特点：\n- 外表：...\n- 性格：..."},
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "..."}
  ]
}
```

**影响：**
- 模型过度关注system prompt的格式
- 学会了"背诵"格式化的列表
- 450个样本，每个都重复相同的system prompt
- 模型认为这是对话的一部分

### 2. **System Prompt格式问题** ⭐⭐⭐⭐

**问题：System prompt包含格式化的列表**

```
你的特点：
- 外表：清瘦白皙...
- 性格：文静少言...
```

**影响：**
- 模型学会了生成这种格式
- 输出时重复这些格式标记
- 无法正常对话

### 3. **训练过度** ⭐⭐⭐

**问题：Loss降得太低，导致过拟合**

- Loss降到0.1以下可能过拟合
- 模型记住了训练数据的细节
- 无法泛化到新对话

## ✅ 解决方案

### 方案1: 移除训练数据中的System Prompt（推荐）⭐⭐⭐⭐⭐

**原理：**
- System prompt只在Modelfile中设置（推理时使用）
- 训练数据只包含user和assistant对话
- 模型学习对话模式，而不是格式

**步骤：**

1. **运行修复脚本：**
   ```bash
   python fix_overfitting.py
   # 选择选项1：移除system prompt
   ```

2. **检查修复后的数据：**
   ```bash
   # 查看前几行
   head -n 3 datasets/linzhi/train.jsonl
   ```

3. **替换原文件：**
   ```bash
   mv datasets/linzhi/train.jsonl datasets/linzhi/train.jsonl
   mv datasets/linzhi/val.jsonl datasets/linzhi/val.jsonl
   ```

4. **重新训练：**
   ```bash
   # 删除旧结果
   rm -rf out/lora_linzhi out/merged_linzhi
   
   # 重新训练
   .\train.ps1 linzhi
   ```

### 方案2: 简化System Prompt ⭐⭐⭐

**原理：**
- 保留system prompt，但简化格式
- 移除格式化的列表
- 只保留核心角色设定

**步骤：**

1. **运行修复脚本：**
   ```bash
   python fix_overfitting.py
   # 选择选项2：简化system prompt
   ```

2. **简化后的格式：**
   ```
   原始: 你是林栀...你的特点：\n- 外表：...\n- 性格：...
   简化: 你是林栀，一个24岁的温柔女孩。文静少言，说话轻软，容易害羞脸红。
   ```

### 方案3: 调整训练参数 ⭐⭐

**如果数据格式无法修改，可以尝试：**

```yaml
training_params:
  epochs: 2.0              # 减少训练轮数
  learning_rate: 3e-5      # 降低学习率
  lora_r: 8               # 降低rank（减少参数量）
  lora_alpha: 16
  lora_dropout: 0.2       # 增加dropout（防止过拟合）
```

## 📊 修复后的数据格式

### 修复前（有问题）：
```json
{
  "messages": [
    {"role": "system", "content": "你是林栀...你的特点：\n- 外表：...\n- 性格：..."},
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "..."}
  ]
}
```

### 修复后（正确）：
```json
{
  "messages": [
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "..."}
  ]
}
```

**System prompt只在Modelfile中设置：**
```
SYSTEM """你是林栀，一个24岁的温柔女孩。文静少言，说话轻软，容易害羞脸红。"""
```

## 🎯 为什么这样修复有效？

### 问题根源：
1. **重复的system prompt** → 模型过度关注格式
2. **格式化的列表** → 模型学会生成格式
3. **450次重复** → 强化了格式记忆

### 修复效果：
1. **移除system prompt** → 模型只学习对话
2. **简化格式** → 模型学习自然语言
3. **Modelfile设置** → 推理时应用角色设定

## 📝 修复检查清单

修复后检查：

- [ ] 训练数据中没有system prompt（或已简化）
- [ ] 数据格式正确（只有user和assistant）
- [ ] Modelfile中有system prompt
- [ ] 重新训练模型
- [ ] Loss正常下降（0.1-0.3）
- [ ] 模型输出正常对话（不包含格式标记）

## 🚀 快速修复命令

```bash
# 1. 修复数据格式
python fix_overfitting.py
# 选择1（移除system prompt）

# 2. 替换文件
mv datasets/linzhi/train.jsonl datasets/linzhi/train.jsonl
mv datasets/linzhi/val.jsonl datasets/linzhi/val.jsonl

# 3. 删除旧结果
rm -rf out/lora_linzhi out/merged_linzhi

# 4. 重新训练
.\train.ps1 linzhi
```

## ⚠️ 重要提醒

1. **备份原数据**：修复脚本会自动创建备份
2. **检查修复结果**：修复后检查数据格式是否正确
3. **重新训练**：必须重新训练，不能继续旧训练
4. **验证效果**：训练后测试模型输出是否正常

## 💡 预期效果

修复后，模型应该：
- ✅ 正常对话，不包含格式标记
- ✅ 符合角色性格（通过Modelfile的system prompt）
- ✅ 不重复训练数据
- ✅ 自然流畅的回复

