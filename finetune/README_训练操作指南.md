# 🚀 LoRA训练系统 - 快速指南

## 核心命令

**一键训练（推荐）:**
```bash
./train                    # 交互选择角色训练
./train linzhi            # 直接训练林栀角色
./train linzhi --ollama   # 训练并导入Ollama
```

**系统管理:**
```bash
./train --scan     # 查看数据状态
./train --list     # 查看所有配置
./train --cache    # 检查模型缓存
./train --menu     # 完整功能菜单
```

## 可用角色

**林栀（主角色）**: 450训练样本 + 50验证样本
**林栀(测试版)**: 28训练样本，快速测试用

## 数据目录结构
```
datasets/
├── linzhi/           # 主角色数据
│   ├── train.jsonl   # 训练数据
│   └── val.jsonl     # 验证数据
└── archive/          # 测试数据
    └── train_fixed_28_samples.jsonl
```

## 训练流程

**标准训练流程:**
```bash
./train linzhi               # 开始训练
```

**训练完成后会自动显示:**
```
🎉 训练完成！下一步操作
✅ 模型已训练完成：linzhi
📁 文件位置：out/merged_linzhi/

⚠️  注意：模型目前还没有导入到Ollama，无法直接使用

📋 后续选项：
1) 🚀 导入到Ollama（推荐）
2) 📦 稍后导入
3) 🏠 返回主菜单
4) 👋 退出系统
```

**快速训练+导入:**
```bash
./train linzhi --ollama      # 训练后自动导入Ollama
```

**快速测试:**
```bash
./train linzhi_quick         # 使用28样本快速测试
```

## 问题排查

**数据找不到**: 运行 `./train --scan` 检查文件位置
**配置问题**: 运行 `./train --list` 查看配置状态
**格式错误**: 检查JSONL文件每行都是有效JSON

## 重要提醒

- **训练完成后需要导入Ollama才能使用** - 系统会自动提示选择
- 同时只运行一个训练任务，避免资源冲突
- 训练前运行 `./train --cache` 确认模型已缓存
- 使用 `./train linzhi_quick` 先做快速测试

---
**统一入口**: `./train` | **完整功能**: `./train --menu`