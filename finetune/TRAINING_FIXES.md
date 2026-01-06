# 训练问题修复说明

## 🔍 发现的问题

### 1. Loss重置问题
**问题描述**：继续训练时，loss从3.多重新开始，而不是从之前的0.2继续

**根本原因**：
- 当使用 `--resume_from_checkpoint` 继续训练时，`--num_train_epochs` 参数设置的是**总epochs数**，而不是**剩余epochs数**
- 例如：之前训练了0.71个epoch，配置中epochs=5.0，继续训练时又设置epochs=5.0
- 这导致训练脚本认为要重新训练5个epoch，loss重置

**修复方案**：
- ✅ 已修复：继续训练时自动计算剩余epochs数
- ✅ 从checkpoint的 `trainer_state.json` 读取当前epoch
- ✅ 使用 `总epochs - 当前epoch` 作为剩余epochs

### 2. 模型效果差问题
**问题描述**：训练好的模型答非所问，效果很差

**可能原因**：
1. **LoRA rank过大**：rank=32 可能导致过拟合
2. **学习率偏高**：1e-4 可能不够稳定
3. **训练轮数过多**：5.0 epochs 可能导致过拟合
4. **数据格式问题**：每个样本都重复system prompt

**修复方案**：
- ✅ 降低LoRA rank: 32 → 16
- ✅ 降低学习率: 1e-4 → 5e-5
- ✅ 降低训练轮数: 5.0 → 3.0
- ✅ 保持LoRA alpha = 2 * rank

## 📊 优化后的配置

```yaml
training_params:
  epochs: 3.0              # 降低训练轮数
  learning_rate: 5e-5      # 更稳定的学习率
  lora_r: 16              # 降低rank，减少过拟合
  lora_alpha: 32          # alpha = 2 * rank
  lora_dropout: 0.1       # 保持不变
```

## 🚀 使用建议

### 重新训练（推荐）
如果之前的训练效果不好，建议：
1. 删除旧的训练结果：`rm -rf out/lora_linzhi out/merged_linzhi`
2. 使用新的优化参数重新训练
3. 监控loss曲线，如果loss降到0.1以下且稳定，可以提前停止

### 继续训练
如果之前的训练loss还在下降：
1. 使用"继续训练"选项
2. 系统会自动计算剩余epochs
3. 不会重置loss

## 📈 训练监控建议

1. **Loss曲线**：
   - 正常：从3.0逐渐降到0.1-0.3
   - 异常：loss不下降或反复波动 → 降低学习率
   - 过拟合：loss降到0.05以下但验证loss上升 → 减少epochs或增加dropout

2. **Token准确率**：
   - 正常：从0.3逐渐提升到0.9+
   - 如果准确率不提升 → 检查数据格式

3. **训练时间**：
   - 450样本，3 epochs，GPU训练约10-30分钟
   - 如果太慢 → 检查是否使用了GPU

## ⚠️ 注意事项

1. **数据格式**：确保每个样本都有正确的messages格式
2. **System prompt**：考虑只在第一个样本保留，或统一在Modelfile中设置
3. **验证集**：使用验证集监控过拟合
4. **保存检查点**：训练过程中会保存checkpoint，可以随时继续训练

## 🔧 如果还有问题

运行诊断脚本：
```bash
python fix_training_issues.py
```

检查训练日志：
- 查看 `out/lora_linzhi/trainer_state.json` 了解训练状态
- 查看loss曲线判断是否过拟合

