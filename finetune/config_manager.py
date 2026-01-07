#!/usr/bin/env python3
"""
配置管理工具 - 读取和管理训练参数
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any

class ConfigManager:
    def __init__(self, config_path: str = "config.yaml", character: str = None):
        self.config_path = Path(config_path)
        self.character = character
        self.character_config_path = Path("character_configs.yaml")
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """智能加载配置文件 - 支持角色配置和传统配置"""

        # 优先尝试从角色配置读取
        if self.character and self.character_config_path.exists():
            try:
                return self._load_from_character_config()
            except Exception as e:
                print(f"⚠️  从角色配置加载失败: {e}")
                print("💡 回退到传统配置")

        # 回退到传统 config.yaml 方式
        if not self.config_path.exists():
            print(f"⚠️  配置文件不存在: {self.config_path}")
            print("💡 使用默认配置")
            return self.get_default_config()

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            print(f"✅ 配置文件加载成功: {self.config_path}")
            return config
        except Exception as e:
            print(f"❌ 配置文件读取失败: {e}")
            print("💡 使用默认配置")
            return self.get_default_config()

    def get_default_config(self) -> Dict[str, Any]:
        """默认配置"""
        return {
            "model": {
                "base_model": "Qwen/Qwen2.5-0.5B-Instruct",
                "model_type": "qwen"
            },
            "training": {
                "epochs": 2.0,
                "learning_rate": 2e-4,
                "warmup_ratio": 0.03,
                "weight_decay": 0.0,
                "seed": 42
            },
            "lora": {
                "rank": 8,
                "alpha": 16,
                "dropout": 0.05
            },
            "data": {
                "max_seq_length": 0,
                "batch_size": 0,
                "gradient_accumulation": 0
            },
            "logging": {
                "logging_steps": 10,
                "save_steps": 200,
                "eval_steps": 200
            },
            "ollama": {
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 40,
                "repeat_penalty": 1.05,
                "context_length": 4096
            },
            "advanced": {
                "gradient_checkpointing": False,
                "no_eval": False,
                "report_to": "none"
            }
        }

    def _load_from_character_config(self) -> Dict[str, Any]:
        """从角色配置文件加载并转换为标准格式"""
        print(f"📋 从角色配置加载: {self.character}")

        with open(self.character_config_path, 'r', encoding='utf-8') as f:
            char_configs = yaml.safe_load(f)

        if 'characters' not in char_configs or self.character not in char_configs['characters']:
            raise ValueError(f"角色 '{self.character}' 在配置文件中未找到")

        char_config = char_configs['characters'][self.character]
        training_params = char_config.get('training_params', {})

        # 将角色配置转换为标准 config.yaml 格式
        standard_config = {
            "model": {
                "base_model": training_params.get('base_model', "Qwen/Qwen2.5-0.5B-Instruct"),
                "model_type": "qwen"
            },
            "training": {
                "epochs": training_params.get('epochs', 2.0),
                "learning_rate": training_params.get('learning_rate', 2e-4),
                "warmup_ratio": 0.03,  # 使用默认值
                "weight_decay": 0.0,   # 使用默认值
                "seed": 42             # 使用默认值
            },
            "lora": {
                "rank": training_params.get('lora_r', 8),      # 注意：角色配置用 lora_r
                "alpha": training_params.get('lora_alpha', 16), # 角色配置用 lora_alpha
                "dropout": training_params.get('lora_dropout', 0.05) # 角色配置用 lora_dropout
            },
            "data": {
                "max_seq_length": 0,
                "batch_size": 0,
                "gradient_accumulation": 0
            },
            "logging": {
                "logging_steps": 10,
                "save_steps": 200,
                "eval_steps": 200
            },
            "ollama": {
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 40,
                "repeat_penalty": 1.05,
                "context_length": 4096
            },
            "advanced": {
                "gradient_checkpointing": False,
                "no_eval": False,
                "report_to": "none"
            }
        }

        # 如果角色配置有推理参数，覆盖 ollama 配置
        inference_params = char_config.get('inference_params', {})
        if inference_params:
            standard_config["ollama"].update({
                "temperature": inference_params.get('temperature', 0.7),
                "top_p": inference_params.get('top_p', 0.9),
                "top_k": inference_params.get('top_k', 40),
                "repeat_penalty": inference_params.get('repeat_penalty', 1.05),
                "context_length": inference_params.get('num_predict', 4096)
            })

        print(f"✅ 角色配置转换成功: {self.character}")
        print(f"🤖 使用模型: {standard_config['model']['base_model']}")
        print(f"🔄 训练轮数: {standard_config['training']['epochs']}")
        print(f"🔧 LoRA rank: {standard_config['lora']['rank']}")

        return standard_config

    def get(self, key_path: str, default=None):
        """获取配置值 (支持嵌套路径，如 'model.base_model')"""
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def get_training_args(self) -> Dict[str, Any]:
        """获取训练参数 (用于 train_lora.py)"""
        return {
            "model_name_or_path": self.get("model.base_model"),
            "num_train_epochs": self.get("training.epochs"),
            "learning_rate": self.get("training.learning_rate"),
            "warmup_ratio": self.get("training.warmup_ratio"),
            "weight_decay": self.get("training.weight_decay"),
            "seed": self.get("training.seed"),
            "lora_r": self.get("lora.rank"),
            "lora_alpha": self.get("lora.alpha"),
            "lora_dropout": self.get("lora.dropout"),
            "max_seq_length": self.get("data.max_seq_length"),
            "per_device_train_batch_size": self.get("data.batch_size"),
            "gradient_accumulation_steps": self.get("data.gradient_accumulation"),
            "logging_steps": self.get("logging.logging_steps"),
            "save_steps": self.get("logging.save_steps"),
            "eval_steps": self.get("logging.eval_steps"),
            "gradient_checkpointing": self.get("advanced.gradient_checkpointing"),
            "no_eval": self.get("advanced.no_eval"),
            "report_to": self.get("advanced.report_to")
        }

    def get_ollama_params(self) -> Dict[str, Any]:
        """获取 Ollama 参数 (用于 Modelfile)"""
        return {
            "temperature": self.get("ollama.temperature"),
            "top_p": self.get("ollama.top_p"),
            "top_k": self.get("ollama.top_k"),
            "repeat_penalty": self.get("ollama.repeat_penalty"),
            "num_ctx": self.get("ollama.context_length")
        }

    def show_config(self):
        """显示当前配置"""
        print("\n📋 当前配置:")
        print("=" * 50)
        print(f"🤖 基础模型: {self.get('model.base_model')}")
        print(f"🔄 训练轮数: {self.get('training.epochs')}")
        print(f"📊 学习率: {self.get('training.learning_rate')}")
        print(f"🔧 LoRA rank: {self.get('lora.rank')}")
        print(f"🔧 LoRA alpha: {self.get('lora.alpha')}")
        print(f"🌡️  温度: {self.get('ollama.temperature')}")
        print("=" * 50)

    def save_model_config(self, merged_dir: Path, model_name: str, actual_args: Dict = None):
        """保存模型专用配置到模型目录"""
        model_config = {
            "model_name": model_name,
            "base_model": self.get("model.base_model"),
            "config_snapshot": self.config.copy(),
            "ollama_params": self.get_ollama_params()
        }

        # 如果有实际使用的参数，也保存
        if actual_args:
            model_config["actual_training_args"] = actual_args

        config_file = merged_dir / "model_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(model_config, f, indent=2, ensure_ascii=False)

        print(f"💾 模型配置已保存到: {config_file}")

def load_config(config_path: str = "config.yaml") -> ConfigManager:
    """快捷加载配置"""
    return ConfigManager(config_path)

if __name__ == "__main__":
    # 测试配置管理器
    config = ConfigManager()
    config.show_config()

    print("\n🔧 训练参数:")
    training_args = config.get_training_args()
    for key, value in training_args.items():
        print(f"  {key}: {value}")