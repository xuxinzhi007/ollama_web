#!/bin/bash
# 安全清理旧脚本工具 - 统一系统版

echo "🧹 清理不需要的旧脚本..."

# 创建备份目录
mkdir -p archive/old_scripts
echo "📁 创建备份目录: archive/old_scripts/"

# 备份并移除已整合功能的旧脚本
echo "📦 备份旧脚本（功能已整合到统一系统）..."

# UI界面相关的旧脚本
for script in "quick_start.sh" "easy_train.py" "train_to_ollama.py"; do
    if [ -f "$script" ]; then
        mv "$script" archive/old_scripts/
        echo "   ✅ $script -> archive/old_scripts/"
    fi
done

# 数据处理相关的不常用脚本
for script in "make_dataset.py" "custom_dataset.py" "generate_linzhi_data.py"; do
    if [ -f "$script" ]; then
        mv "$script" archive/old_scripts/
        echo "   ✅ $script -> archive/old_scripts/"
    fi
done

# 修复和临时脚本
for script in "fix_training_issues.py" "fix_data_format.py" "download_model.py" "download_progress.py"; do
    if [ -f "$script" ]; then
        mv "$script" archive/old_scripts/
        echo "   ✅ $script -> archive/old_scripts/"
    fi
done

# 配置和环境检测（保留但不常用）
for script in "config_manager.py" "env_detect.py"; do
    if [ -f "$script" ]; then
        mv "$script" archive/old_scripts/
        echo "   ✅ $script -> archive/old_scripts/"
    fi
done

echo ""
echo "✅ 清理完成！"
echo ""
echo "🎯 现在只保留核心系统："
echo "   ./train               # 统一入口（推荐）"
echo "   smart_train.py       # 智能训练主脚本"
echo "   train_lora.py        # 核心训练引擎"
echo "   model_cache.py       # 模型缓存检测"
echo "   character_configs.yaml # 角色配置"
echo ""
echo "📂 备份位置: archive/old_scripts/"
echo "💡 如需还原，从备份目录复制回来"
echo ""
echo "🚀 开始使用统一系统："
echo "   ./train              # 交互式训练"
echo "   ./train --menu       # 完整功能菜单"
echo "   ./train --scan       # 检查数据状态"