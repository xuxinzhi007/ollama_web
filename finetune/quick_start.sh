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

# 主循环菜单
while true; do
    echo ""
    echo "==================== 主菜单 ===================="
    echo "请选择操作："
    echo "1) 🔥 一键训练新模型（推荐 - 实时进度显示）"
    echo "2) ⚡ 高级训练（自定义参数）"
    echo "3) 🔄 继续训练已有模型（增量/调参）"
    echo "4) 📝 数据集管理（创建/导入自定义数据）"
    echo "5) 📦 批量导入现有模型"
    echo "6) 📊 查看当前模型"
    echo "7) 🧪 测试指定模型"
    echo "8) 🗑️  清理旧模型"
    echo "9) 📋 查看系统状态"
    echo "0) 退出"
    echo ""

    read -p "请输入选择 (0-9): " choice

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
        echo ""
        read -p "按回车键返回主菜单..."
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
        echo ""
        read -p "按回车键返回主菜单..."
        ;;

    3)
        echo ""
        echo "🔄 继续训练已有模型"
        echo ""
        echo "📊 当前可训练的模型列表："
        ollama list | tail -n +2 | head -5
        echo ""
        read -p "输入要继续训练的模型名称: " existing_model
        if [[ -z "$existing_model" ]]; then
            echo "❌ 模型名称不能为空"
        else
            echo ""
            echo "🔄 启动继续训练: $existing_model"
            python train_to_ollama.py --ollama_name "$existing_model" --continue_train
        fi
        echo ""
        read -p "按回车键返回主菜单..."
        ;;

    4)
        echo ""
        echo "📝 数据集管理选项："
        echo "   1) 🤖 生成预设数据集（工程师助手风格）"
        echo "   2) 📊 交互式创建自定义数据集"
        echo "   3) 📋 导出CSV模板（用于批量编辑）"
        echo "   4) 📥 从CSV导入数据集"
        echo "   5) 📄 查看当前数据集信息"
        echo ""
        read -p "选择数据集操作 (1-5): " data_choice

        case $data_choice in
            1)
                echo ""
                read -p "生成多少条数据 (默认300): " data_count
                data_count=${data_count:-300}
                echo "🤖 生成 $data_count 条预设数据..."
                python make_dataset.py --out_dir data --n "$data_count"
                echo "✅ 数据集生成完成！"
                ;;
            2)
                echo ""
                echo "📊 启动交互式数据集创建..."
                python custom_dataset.py --interactive --output_dir data
                ;;
            3)
                echo ""
                read -p "CSV模板文件名 (默认: template.csv): " template_name
                template_name=${template_name:-template.csv}
                python custom_dataset.py --export_csv_template "$template_name"
                echo "💡 编辑 $template_name 后使用选项4导入"
                ;;
            4)
                echo ""
                read -p "CSV文件路径: " csv_file
                if [[ -f "$csv_file" ]]; then
                    echo "📥 从CSV导入数据集..."
                    python custom_dataset.py --csv "$csv_file" --output_dir data --merge_with_existing
                else
                    echo "❌ 文件不存在: $csv_file"
                fi
                ;;
            5)
                echo ""
                echo "📄 当前数据集信息："
                if [[ -f "data/train.jsonl" ]]; then
                    train_count=$(wc -l < data/train.jsonl)
                    echo "   📈 训练数据: $train_count 条"

                    if [[ -f "data/val.jsonl" ]]; then
                        val_count=$(wc -l < data/val.jsonl)
                        echo "   📊 验证数据: $val_count 条"
                    fi

                    echo "   📝 数据样本:"
                    head -1 data/train.jsonl | python -m json.tool 2>/dev/null | head -10 || echo "   无法解析数据格式"
                else
                    echo "   ❌ 未找到训练数据文件"
                    echo "   💡 请先创建数据集"
                fi
                ;;
            *)
                echo "❌ 无效选择"
                ;;
        esac
        echo ""
        read -p "按回车键返回主菜单..."
        ;;

    5)
        echo ""
        echo "📦 批量导入现有模型..."
        python scripts/ultimate_solution.py --batch 2>/dev/null || echo "   批量导入脚本未找到"
        echo ""
        read -p "按回车键返回主菜单..."
        ;;

    6)
        echo ""
        echo "📊 当前 Ollama 模型列表："
        ollama list
        echo ""
        read -p "按回车键返回主菜单..."
        ;;

    7)
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
        echo ""
        read -p "按回车键返回主菜单..."
        ;;

    8)
        echo ""
        echo "🗑️  可清理的模型："
        ollama list | grep -E "(test|old|debug|temp)" || echo "没有找到明显的测试模型"
        echo ""
        read -p "输入要删除的模型名称 (留空取消): " del_model
        if [[ -n "$del_model" ]]; then
            ollama rm "$del_model"
            echo "✅ 已删除: $del_model"
        fi
        echo ""
        read -p "按回车键返回主菜单..."
        ;;

    9)
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
        echo ""
        read -p "按回车键返回主菜单..."
        ;;

    0)
        echo "👋 再见！"
        break
        ;;

    *)
        echo "❌ 无效选择，请重新输入"
        echo ""
        read -p "按回车键返回主菜单..."
        ;;
esac
done

echo ""
echo "💡 提示：查看详细文档请运行 'cat README.md'"