# 配置文件说明 - character_configs.yaml vs config.yaml

## 🔍 问题

发现有两个配置文件都包含训练参数，不知道哪个生效？

## ✅ 答案

**训练时使用的是 `character_configs.yaml`，`config.yaml` 用于其他功能。**

## 📄 两个配置文件的作用

### 1. `character_configs.yaml` - 角色配置文件（训练时使用）

**位置**: `finetune/character_configs.yaml`

**作用**: 
- ✅ **训练参数的主要来源**
- 每个角色有独立的训练参数
- 通过 `smart_train.py` 读取并传递给 `train_lora.py`

**结构**:
```yaml
characters:
  linzhi:
    training_params:
      epochs: 3.0              # ← 训练时使用这个
      learning_rate: 5e-5      # ← 训练时使用这个
      lora_r: 16               # ← 训练时使用这个
      lora_alpha: 32
      lora_dropout: 0.1
      base_model: "Qwen/Qwen2.5-0.5B-Instruct"
```

**使用流程**:
1. `smart_train.py` 读取 `character_configs.yaml` (第50行)
2. 提取 `training_params` (第669行)
3. 通过命令行参数传递给 `train_lora.py` (第784-793行)
4. `train_lora.py` 使用这些参数进行训练

### 2. `config.yaml` - 全局配置文件（其他功能使用）

**位置**: `finetune/config.yaml`

**作用**:
- ⚠️ **训练时不使用**
- 用于 `train_to_ollama.py` 导入模型时的参数
- 用于 `ConfigManager` 的全局默认配置
- Ollama生成参数（temperature, top_p等）

**结构**:
```yaml
training:
  epochs: 5.0              # ← 训练时 NOT 使用
  learning_rate: 1e-4       # ← 训练时 NOT 使用

lora:
  rank: 16                  # ← 训练时 NOT 使用
  alpha: 32                 # ← 训练时 NOT 使用

ollama:
  temperature: 0.7          # ← 用于Ollama生成
  top_p: 0.9               # ← 用于Ollama生成
```

## 🔄 配置传递流程

```
character_configs.yaml
    ↓
smart_train.py (读取)
    ↓
提取 training_params
    ↓
命令行参数传递
    ↓
train_lora.py (接收并使用)
    ↓
实际训练
```

## ✅ 验证结果

运行 `python verify_config.py` 可以验证：

```
✅ 配置匹配！character_configs.yaml 的配置已生效

实际使用的训练参数:
  num_train_epochs: 3.0          ← 来自 character_configs.yaml
  learning_rate: 5e-05          ← 来自 character_configs.yaml
  lora_r: 16                    ← 来自 character_configs.yaml
```

## 📝 如何修改训练参数

### ✅ 正确方式：修改 `character_configs.yaml`

```yaml
characters:
  linzhi:
    training_params:
      epochs: 5.0              # ← 修改这里
      learning_rate: 1e-4      # ← 修改这里
      lora_r: 32               # ← 修改这里
```

### ❌ 错误方式：只修改 `config.yaml`

```yaml
training:
  epochs: 5.0              # ← 修改这里无效！
  learning_rate: 1e-4       # ← 修改这里无效！
```

## 🎯 训练轮数（epochs）是如何工作的？

### 1. 配置来源
- 从 `character_configs.yaml` 读取 `epochs: 3.0`

### 2. 传递过程
```python
# smart_train.py 第784-785行
if 'epochs' in training_params:
    cmd.extend(["--num_train_epochs", str(training_params['epochs'])])
```

### 3. 训练执行
- `train_lora.py` 接收 `--num_train_epochs 3.0`
- 训练3个epoch
- 每个epoch = 数据集大小 ÷ (batch_size × gradient_accumulation)
- 例如: 450样本 ÷ 4 = 113步/epoch
- 总步数: 113 × 3 = 339步

### 4. 继续训练（断点续训）
- 如果选择"继续训练"
- 计算剩余epochs: `remaining_epochs = total_epochs - current_epoch`
- 只训练剩余的部分

## 💡 建议

### 1. 统一配置管理
- ✅ **训练参数**: 只修改 `character_configs.yaml`
- ✅ **Ollama参数**: 可以修改 `config.yaml` 的 `ollama` 部分
- ⚠️ **避免混淆**: 不要在两个文件中都修改训练参数

### 2. 清理建议
如果想避免混淆，可以：
- 保留 `character_configs.yaml` 中的训练参数
- 删除 `config.yaml` 中重复的训练参数（只保留 `ollama` 部分）

### 3. 验证配置
运行以下命令验证配置是否生效：
```bash
python verify_config.py
```

## 📊 配置对比表

| 参数 | character_configs.yaml | config.yaml | 实际使用 |
|------|------------------------|-------------|----------|
| epochs | 3.0 | 5.0 | ✅ 3.0 (来自character_configs) |
| learning_rate | 5e-5 | 1e-4 | ✅ 5e-5 (来自character_configs) |
| lora_r | 16 | 16 | ✅ 16 (来自character_configs) |
| temperature | - | 0.7 | ✅ 0.7 (来自config.yaml，用于Ollama) |

## 🎓 总结

1. **训练参数**: 使用 `character_configs.yaml` ✅
2. **Ollama参数**: 使用 `config.yaml` ✅
3. **修改训练参数**: 编辑 `character_configs.yaml` ✅
4. **验证配置**: 运行 `python verify_config.py` ✅

**记住**: `character_configs.yaml` 是训练时使用的配置文件！

