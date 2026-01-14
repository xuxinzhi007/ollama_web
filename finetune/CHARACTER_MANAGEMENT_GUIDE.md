# 角色管理指南

## 🎨 功能概述

角色管理功能提供统一的界面来创建和删除角色，无需手动操作文件系统。

## 🚀 使用方法

### 方式1：通过主菜单（推荐）

```bash
cd finetune
./train --menu
```

在主菜单中选择：
```
6) 🎨 角色管理（创建/删除）
```

### 方式2：命令行工具

```bash
cd finetune
python3 character_manager.py <action> [options]
```

## 📋 功能详解

### 1. 创建新角色

**通过菜单**:
```
主菜单 → 6) 角色管理 → 1) 创建新角色
```

**命令行**:
```bash
python3 character_manager.py create
```

工具会：
1. 交互式收集角色信息
2. 生成训练数据集（train.jsonl + val.jsonl）
3. 自动更新 character_configs.yaml
4. 创建角色说明文档

详细使用方法参考：`CREATE_CHARACTER_GUIDE.md`

### 2. 查看所有角色

**通过菜单**:
```
主菜单 → 6) 角色管理 → 2) 查看所有角色
```

显示内容：
- 角色ID
- 角色名字
- 简短描述

**命令行**:
```bash
python3 character_manager.py list
```

### 3. 查看角色详情

**通过菜单**:
```
主菜单 → 6) 角色管理 → 3) 查看角色详情
```

显示内容：
- 基本信息（ID、名字、描述）
- 数据集状态（训练集/验证集数量）
- 训练输出（已有的训练模型）
- 训练参数配置

**命令行**:
```bash
python3 character_manager.py info <角色ID>

# 示例
python3 character_manager.py info linzhi
```

### 4. 删除角色

**通过菜单**:
```
主菜单 → 6) 角色管理 → 4) 删除角色
```

删除内容包括：
- ✅ 数据集目录（datasets/{角色ID}/）
- ✅ 训练输出目录（out/*{角色ID}*/）
- ✅ 配置文件条目（character_configs.yaml）

**命令行**:
```bash
# 交互式删除（需要确认）
python3 character_manager.py delete <角色ID>

# 跳过确认直接删除
python3 character_manager.py delete <角色ID> --yes

# 示例
python3 character_manager.py delete xiaoxue
python3 character_manager.py delete xiaoxue -y
```

## 💡 使用场景

### 场景1：创建新角色

```
1. 准备角色信息（名字、性格、说话风格等）
2. 运行 ./train --menu
3. 选择 6) 角色管理 → 1) 创建新角色
4. 按提示输入信息
5. 选择生成方式（空模板 或 AI辅助）
6. 完成！自动创建数据集和配置
```

### 场景2：测试完不满意，想重新创建

```
1. 删除旧角色: ./train --menu → 6) 角色管理 → 4) 删除角色
2. 创建新角色: 选择 1) 创建新角色
3. 重新设计角色定位和数据
```

### 场景3：清理测试角色

```
1. 查看所有角色: ./train --menu → 6) 角色管理 → 2) 查看所有角色
2. 批量删除不需要的角色
3. 释放磁盘空间
```

### 场景4：检查角色状态

```
1. 查看角色详情: ./train --menu → 6) 角色管理 → 3) 查看角色详情
2. 检查数据集数量是否充足
3. 查看已有的训练输出
4. 确认训练参数配置
```

## ⚠️ 注意事项

### 删除角色时

1. **无法恢复**：删除操作不可逆，请谨慎操作
2. **需要确认**：默认会要求输入 "yes" 确认
3. **完全清理**：会删除所有相关文件（数据集、训练输出、配置）

### 命令行删除

```bash
# ❌ 危险：跳过确认
python3 character_manager.py delete xiaoxue --yes

# ✅ 安全：交互式确认
python3 character_manager.py delete xiaoxue
```

### 删除确认示例

```
⚠️  即将删除角色: 小雪 (xiaoxue)

将删除以下内容:
  📁 数据集: datasets/xiaoxue
  📁 训练输出: out/xiaoxue-20250114-143052
  ⚙️  配置文件中的角色定义

==================================================
确认删除？(yes/NO):
```

只有输入 `yes` 或 `y` 才会执行删除。

## 🔍 命令行工具完整参数

```bash
# 查看帮助
python3 character_manager.py --help

# 列出所有角色
python3 character_manager.py list

# 创建新角色
python3 character_manager.py create

# 查看角色详情
python3 character_manager.py info <角色ID>

# 删除角色（需要确认）
python3 character_manager.py delete <角色ID>

# 删除角色（跳过确认）
python3 character_manager.py delete <角色ID> --yes
python3 character_manager.py delete <角色ID> -y
```

## 📊 集成工作流

### 完整开发流程

```
1. 创建角色
   ↓
   ./train --menu → 6) 角色管理 → 1) 创建新角色
   ↓
2. 补充数据
   ↓
   编辑 datasets/{角色ID}/train.jsonl
   ↓
3. 开始训练
   ↓
   ./train --menu → 1) 角色训练
   ↓
4. 测试效果
   ↓
   Web UI 或 ./train --menu → 5) 模型测试
   ↓
5. 不满意？删除重来
   ↓
   ./train --menu → 6) 角色管理 → 4) 删除角色
   ↓
6. 满意！导入到 Ollama
   ↓
   ./train --menu → 4) Ollama模型管理 → 2) 导入模型
```

## 📚 相关文档

- **创建角色详细指南**: `CREATE_CHARACTER_GUIDE.md`
- **角色创建示例**: `example_character_output.md`
- **训练参数指南**: `PARAMETER_GUIDE.md`
- **完整使用指南**: `USAGE_GUIDE.md`

## 💡 最佳实践

### 1. 创建前先规划

- 明确角色定位和特点
- 准备好角色设定资料
- 想好说话风格和互动方式

### 2. 测试用小数据集

- 先创建20条数据快速测试
- 验证角色设定是否合理
- 确认训练流程正常

### 3. 不满意就删除重建

- 不要在错误的设定上浪费时间
- 删除旧角色，重新设计
- 迭代优化直到满意

### 4. 定期清理

- 删除不再使用的测试角色
- 释放磁盘空间
- 保持项目整洁

### 5. 备份重要角色

在删除前，如果角色很重要，建议手动备份：

```bash
# 备份数据集
cp -r datasets/xiaoxue datasets/xiaoxue.backup

# 备份训练输出
cp -r out/xiaoxue-* out/xiaoxue.backup

# 备份配置（手动复制配置内容）
```

---

**工具位置**: `finetune/character_manager.py`
**菜单入口**: `./train --menu` → 6) 角色管理
