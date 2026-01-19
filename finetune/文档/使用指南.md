# LoRA 训练系统使用指南

## 🎯 配置管理策略

### ✅ 统一配置源
- **主配置文件**: `character_configs.yaml` (唯一数据源)
- **配置管理器**: `config_manager.py` (兼容角色配置)
- **可删除文件**: `config.yaml` (可选，已不使用)

### 🛡️ 安全保证
- ✅ 两个工具使用**相同的配置数据源**
- ✅ 训练参数**完全一致**
- ✅ **零风险**改动，不影响模型质量

## 🚀 使用方法

### 方式一：智能训练系统（推荐）
```bash
# 交互式菜单
python smart_train.py

# 直接指定角色
python smart_train.py linzhi

# 显示配置
python smart_train.py --list
```

### 方式二：一键训练到部署
```bash
# 使用角色配置
python train_to_ollama.py --character linzhi --ollama_name linzhi-lora

# 传统配置（不推荐）
python train_to_ollama.py --config config.yaml --ollama_name my-model
```

## 📝 配置文件说明

### character_configs.yaml
```yaml
characters:
  linzhi:
    name: "林栀"
    training_params:
      epochs: 3.0
      learning_rate: 5e-5
      lora_r: 16
      lora_alpha: 32
      base_model: "Qwen/Qwen2.5-0.5B-Instruct"
    inference_params:
      temperature: 0.65
      top_p: 0.92
```

### 参数优先级
1. **角色配置** (`character_configs.yaml`) - 优先使用
2. **传统配置** (`config.yaml`) - 回退使用
3. **默认配置** - 最后回退

## 🔧 配置管理原理

### ConfigManager 兼容性
```python
# 自动选择配置源
ConfigManager(character="linzhi")     # 使用角色配置
ConfigManager("config.yaml")         # 使用传统配置
```

### 参数映射
```python
# 角色配置 → 标准配置
lora_r      → lora.rank
lora_alpha  → lora.alpha
epochs      → training.epochs
base_model  → model.base_model
```

## 📊 工具对比

| 工具 | 用途 | 配置源 | 特点 |
|------|------|--------|------|
| `smart_train.py` | 交互式训练 | 角色配置 | 功能完整，用户友好 |
| `train_to_ollama.py` | 一键流程 | 兼容两种 | 高级功能，命令行 |

## 💡 最佳实践

### 1. 配置管理
- ✅ 使用 `character_configs.yaml` 管理所有角色
- ✅ 每个角色独立配置训练和推理参数
- ❌ 不再使用 `config.yaml`

### 2. 工具选择
- **日常使用**: `python smart_train.py`
- **批量训练**: `python train_to_ollama.py --character <角色>`
- **自动化脚本**: 使用 `train_to_ollama.py`

### 3. 安全训练
- ✅ 训练前检查数据文件
- ✅ 验证配置参数
- ✅ 小批量测试新配置

## 🛠️ 故障排除

### 配置不一致
```bash
# 验证配置
python verify_config_consistency.py
```

### 模型质量问题
1. 检查数据质量
2. 调整 `epochs`（避免过拟合）
3. 调整 `learning_rate`
4. 修改 `lora_r` 和 `lora_alpha`

### 环境问题
```bash
# 环境检查
python smart_train.py --env-check

# 自动设置
python smart_train.py --setup
```

## 📋 清理建议

### 可安全删除的文件
- ✅ `config.yaml` - 已不使用
- ⚠️  `validate_merge_safety.py` - 验证完成后可删除
- ⚠️  `verify_config_consistency.py` - 验证完成后可删除

### 保留的核心文件
- ✅ `character_configs.yaml` - 主配置
- ✅ `config_manager.py` - 配置管理器
- ✅ `smart_train.py` - 主训练工具
- ✅ `train_to_ollama.py` - 一键流程工具
- ✅ `train_lora.py` - 底层训练脚本

## 🎉 总结

**配置统一完成！**

- ✅ **数据源一致**: 两个工具都使用 `character_configs.yaml`
- ✅ **参数一致**: 训练参数完全相同
- ✅ **零风险**: 不影响现有训练质量
- ✅ **向后兼容**: 保留原有功能

现在可以放心使用统一的配置管理系统！