#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证配置文件使用情况 - 检查哪个配置实际生效
"""

import sys
import io
from pathlib import Path

# Windows编码修复
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def check_configs():
    """检查两个配置文件的内容和使用情况"""
    
    print("=" * 70)
    print("配置文件使用情况检查")
    print("=" * 70)
    
    # 1. 检查 character_configs.yaml
    print("\n📄 1. character_configs.yaml (角色配置文件)")
    print("-" * 70)
    try:
        import yaml
        char_config_file = Path("character_configs.yaml")
        if char_config_file.exists():
            with open(char_config_file, 'r', encoding='utf-8') as f:
                char_config = yaml.safe_load(f)
            
            linzhi_config = char_config.get('characters', {}).get('linzhi', {})
            training_params = linzhi_config.get('training_params', {})
            
            print("✅ 文件存在")
            print(f"\n角色 'linzhi' 的训练参数:")
            print(f"  epochs: {training_params.get('epochs', 'N/A')}")
            print(f"  learning_rate: {training_params.get('learning_rate', 'N/A')}")
            print(f"  lora_r: {training_params.get('lora_r', 'N/A')}")
            print(f"  lora_alpha: {training_params.get('lora_alpha', 'N/A')}")
            print(f"  lora_dropout: {training_params.get('lora_dropout', 'N/A')}")
            print(f"  base_model: {training_params.get('base_model', 'N/A')}")
            
            print(f"\n📌 使用位置:")
            print(f"  - smart_train.py (第50行): self.config_file = 'character_configs.yaml'")
            print(f"  - smart_train.py (第669行): training_params = char_config.get('training_params')")
            print(f"  - smart_train.py (第784-793行): 传递参数到 train_lora.py")
        else:
            print("❌ 文件不存在")
    except Exception as e:
        print(f"❌ 读取失败: {e}")
    
    # 2. 检查 config.yaml
    print("\n📄 2. config.yaml (全局配置文件)")
    print("-" * 70)
    try:
        config_file = Path("config.yaml")
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            print("✅ 文件存在")
            print(f"\n全局训练参数:")
            print(f"  epochs: {config.get('training', {}).get('epochs', 'N/A')}")
            print(f"  learning_rate: {config.get('training', {}).get('learning_rate', 'N/A')}")
            print(f"  lora.rank: {config.get('lora', {}).get('rank', 'N/A')}")
            print(f"  lora.alpha: {config.get('lora', {}).get('alpha', 'N/A')}")
            print(f"  lora.dropout: {config.get('lora', {}).get('dropout', 'N/A')}")
            print(f"  base_model: {config.get('model', {}).get('base_model', 'N/A')}")
            
            print(f"\n📌 使用位置:")
            print(f"  - config_manager.py: ConfigManager('config.yaml')")
            print(f"  - train_to_ollama.py: 用于Ollama导入时的参数")
            print(f"  - ⚠️  注意: 训练时 NOT 使用此文件！")
        else:
            print("❌ 文件不存在")
    except Exception as e:
        print(f"❌ 读取失败: {e}")
    
    # 3. 检查实际训练时使用的配置
    print("\n🔍 3. 实际训练时使用的配置")
    print("-" * 70)
    print("训练流程:")
    print("  1. smart_train.py 读取 character_configs.yaml")
    print("  2. 提取 training_params (epochs, learning_rate, lora_r等)")
    print("  3. 通过命令行参数传递给 train_lora.py")
    print("  4. train_lora.py 接收这些参数并用于训练")
    print()
    print("✅ 结论: 训练时使用的是 character_configs.yaml")
    print("⚠️  config.yaml 主要用于其他功能（如Ollama导入）")
    
    # 4. 检查最近的训练记录
    print("\n📊 4. 检查最近的训练记录")
    print("-" * 70)
    checkpoint_dir = Path("out/lora_linzhi")
    if checkpoint_dir.exists():
        checkpoint_dirs = sorted([d for d in checkpoint_dir.iterdir() 
                                  if d.is_dir() and d.name.startswith('checkpoint-')])
        if checkpoint_dirs:
            latest_checkpoint = checkpoint_dirs[-1]
            meta_file = checkpoint_dir / "run_meta.json"
            if meta_file.exists():
                try:
                    import json
                    with open(meta_file, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                    
                    args = meta.get('args', {})
                    print("✅ 找到训练记录")
                    print(f"\n实际使用的训练参数:")
                    print(f"  num_train_epochs: {args.get('num_train_epochs', 'N/A')}")
                    print(f"  learning_rate: {args.get('learning_rate', 'N/A')}")
                    print(f"  lora_r: {args.get('lora_r', 'N/A')}")
                    print(f"  lora_alpha: {args.get('lora_alpha', 'N/A')}")
                    
                    print(f"\n对比 character_configs.yaml:")
                    print(f"  epochs: {training_params.get('epochs', 'N/A')} → 实际: {args.get('num_train_epochs', 'N/A')}")
                    print(f"  learning_rate: {training_params.get('learning_rate', 'N/A')} → 实际: {args.get('learning_rate', 'N/A')}")
                    
                    if str(training_params.get('epochs')) == str(args.get('num_train_epochs')):
                        print("\n✅ 配置匹配！character_configs.yaml 的配置已生效")
                    else:
                        print("\n⚠️  配置不匹配！可能使用了其他配置")
                except Exception as e:
                    print(f"⚠️  无法读取训练记录: {e}")
            else:
                print("ℹ️  未找到 run_meta.json，无法验证实际使用的配置")
        else:
            print("ℹ️  未找到checkpoint，可能还没有训练过")
    else:
        print("ℹ️  未找到训练输出目录")
    
    # 5. 建议
    print("\n💡 5. 建议")
    print("-" * 70)
    print("1. 修改训练参数: 编辑 character_configs.yaml")
    print("   位置: characters.linzhi.training_params")
    print()
    print("2. config.yaml 的作用:")
    print("   - Ollama导入时的参数（temperature, top_p等）")
    print("   - 全局默认配置（如果某些脚本需要）")
    print("   - ⚠️  训练参数不使用此文件")
    print()
    print("3. 如果两个文件参数不一致:")
    print("   - character_configs.yaml 优先（用于训练）")
    print("   - config.yaml 用于其他功能")
    print()
    print("4. 建议:")
    print("   - 保持 character_configs.yaml 中的训练参数")
    print("   - config.yaml 可以保留作为全局默认值")
    print("   - 或者删除 config.yaml 中重复的训练参数，避免混淆")

if __name__ == "__main__":
    check_configs()

