#!/bin/bash
# 🚀 LoRA微调 - 快速入门脚本

set -e

echo "🚀 LoRA 微调到 Ollama - 快速入门"
echo "=================================="

# 检查虚拟环境
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "❌ 请先激活虚拟环境："
    echo "   source .venv/bin/activate"
    exit 1
fi

# 检查Ollama
if ! command -v ollama &> /dev/null; then
    echo "❌ 请先安装 Ollama: https://ollama.ai"
    exit 1
fi

echo "✅ 环境检查完成"
echo ""

# 显示菜单
echo "请选择操作："
echo "1) 🔥 一键训练新模型（推荐 - 实时进度显示）"
echo "2) ⚡ 高级训练（自定义参数）"
echo "3) 📦 批量导入现有模型"
echo "4) 📊 查看当前模型"
echo "5) 🧪 测试指定模型"
echo "6) 🗑️  清理旧模型"
echo "7) 📋 查看系统状态"
echo "0) 退出"
echo ""

read -p "请输入选择 (0-7): " choice

case $choice in
    1)
        echo ""
        read -p "输入新模型名称 (如: my-assistant): " model_name
        if [[ -z "$model_name" ]]; then
            echo "❌ 模型名称不能为空"
            exit 1
        fi

        echo "🔥 开始训练模型: $model_name"
        echo ""
        echo "💡 提示：现在使用统一增强版本，支持实时进度显示和数据集验证"
        echo "⏰ 预计需要 3-5 分钟，请耐心等待..."
        echo ""
        python train_to_ollama.py --ollama_name "$model_name"

        echo ""
        echo "🎉 训练完成！测试命令："
        echo "   ollama run $model_name"
        ;;

    2)
        echo ""
        read -p "输入模型名称: " model_name
        if [[ -z "$model_name" ]]; then
            echo "❌ 模型名称不能为空"
            exit 1
        fi

        echo ""
        echo "⚡ 高级训练选项:"
        read -p "训练轮数 (默认 2.0): " epochs
        epochs=${epochs:-2.0}

        echo ""
        echo "🔥 开始高级训练: $model_name (轮数: $epochs)"
        python train_to_ollama.py --ollama_name "$model_name" --epochs "$epochs"
        ;;

    3)
        echo ""
        echo "📦 批量导入现有模型..."
        python scripts/ultimate_solution.py --batch
        ;;

    4)
        echo ""
        echo "📊 当前 Ollama 模型列表："
        ollama list
        ;;

    5)
        echo ""
        ollama list | grep -v "NAME" | head -5
        echo ""
        read -p "输入要测试的模型名称: " test_model
        if [[ -n "$test_model" ]]; then
            echo ""
            echo "🧪 测试模型: $test_model"
            echo "测试问题：你好，请介绍一下自己。"
            echo "回答："
            echo "----------------------------------------"
            echo "你好，请介绍一下自己。" | ollama run "$test_model"
        fi
        ;;

    6)
        echo ""
        echo "🗑️  可清理的模型："
        ollama list | grep -E "(test|old|debug|temp)" || echo "没有找到明显的测试模型"
        echo ""
        read -p "输入要删除的模型名称 (留空取消): " del_model
        if [[ -n "$del_model" ]]; then
            ollama rm "$del_model"
            echo "✅ 已删除: $del_model"
        fi
        ;;

    7)
        echo ""
        echo "📋 系统状态检查..."
        echo ""
        echo "🔍 环境信息:"
        python env_detect.py 2>/dev/null || echo "   环境检测脚本未找到"

        echo ""
        echo "💾 磁盘占用:"
        python scripts/cleanup.py --dry-run --all 2>/dev/null || echo "   清理脚本未找到"

        echo ""
        echo "📊 Ollama 服务状态:"
        ollama list >/dev/null 2>&1 && echo "   ✅ Ollama 服务正常" || echo "   ❌ Ollama 服务异常"
        ;;

    0)
        echo "👋 再见！"
        exit 0
        ;;

    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo ""
echo "💡 提示：查看详细文档请运行 'cat README.md'"