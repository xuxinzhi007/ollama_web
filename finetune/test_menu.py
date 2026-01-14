#!/usr/bin/env python3
"""
测试新菜单系统 - 快速演示 questionary 效果
"""

try:
    import questionary
    print("✅ questionary 已安装\n")

    print("📋 演示箭头选择菜单：\n")

    # 演示主菜单
    choices = [
        "🎨 角色开发  - 创建和管理角色",
        "🚀 模型训练  - 训练角色模型",
        "📦 模型部署  - 导入和测试模型",
        "🔧 系统工具  - 环境检查和数据验证",
        "🚪 退出演示"
    ]

    choice = questionary.select(
        "请选择功能:",
        choices=choices,
        instruction="(使用↑↓箭头选择，回车确认)"
    ).ask()

    if choice:
        print(f"\n你选择了: {choice}")
        print("\n✨ 完美！箭头选择工作正常！")
        print("\n现在可以运行: ./train --menu")
    else:
        print("\n已取消")

except ImportError:
    print("❌ questionary 未安装")
    print("\n安装方法：")
    print("  pip install questionary")
    print("  或")
    print("  pip install -r requirements.txt")
    print("\n安装后，菜单将自动使用箭头选择模式")
except KeyboardInterrupt:
    print("\n\n已取消")
