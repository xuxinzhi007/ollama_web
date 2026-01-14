# 项目文件结构

## 🚀 快速启动

### Web UI（聊天界面）
```bash
python3 server.py
# 访问: http://localhost:8080
```

### 模型训练
```bash
cd finetune
./train --menu    # 交互式菜单（推荐）
./train linzhi    # 直接训练林栀角色
```

### 创建新角色
```bash
cd finetune
python3 create_character.py  # 创建新角色数据集
```

## 📁 项目结构

```
ollama_web/
├── index.html              # Web 界面主页
├── style.css               # 样式文件
├── server.py               # Flask 服务器
├── js/                     # 前端 JavaScript
│   ├── main.js            # 主应用
│   ├── chat.js            # 聊天功能
│   ├── ui.js              # UI 控制
│   ├── api.js             # Ollama API
│   └── ...
│
├── finetune/              # 训练模块
│   ├── train              # 启动脚本 ⭐
│   ├── create_character.py  # 角色创建工具 🆕
│   ├── character_manager.py # 角色管理工具 🆕
│   ├── smart_train.py     # 智能训练核心
│   ├── train_lora.py      # LoRA 训练
│   ├── character_configs.yaml  # 角色配置
│   ├── datasets/          # 训练数据
│   ├── out/               # 训练输出
│   ├── README.md                        # 使用说明
│   ├── CREATE_CHARACTER_GUIDE.md        # 角色创建指南 🆕
│   ├── CHARACTER_MANAGEMENT_GUIDE.md    # 角色管理指南 🆕
│   ├── example_character_output.md      # 创建示例 🆕
│   ├── PARAMETER_GUIDE.md               # 参数指南
│   ├── CONFIG_FILES_EXPLAINED.md        # 配置说明
│   ├── USAGE_GUIDE.md                   # 详细用法
│   └── TRAINING_STEPS_EXPLAINED.md      # 步骤说明
│
├── archive/               # 归档文档
│   └── design/            # 早期设计文档
│
└── README.md              # 项目说明
```

## 📚 核心文档

| 文档 | 用途 |
|------|------|
| `README.md` | 项目总览 |
| `finetune/README.md` | 训练使用说明 |
| `finetune/CREATE_CHARACTER_GUIDE.md` | 角色创建指南 🆕 |
| `finetune/CHARACTER_MANAGEMENT_GUIDE.md` | 角色管理指南 🆕 |
| `finetune/PARAMETER_GUIDE.md` | 训练参数详解 |
| `finetune/USAGE_GUIDE.md` | 详细使用指南 |

## 🎯 常用命令

```bash
# Web UI
python3 server.py

# 创建新角色 🆕
cd finetune && python3 create_character.py

# 训练（推荐）
cd finetune && ./train --menu

# 查看训练帮助
cd finetune && ./train --help
```
