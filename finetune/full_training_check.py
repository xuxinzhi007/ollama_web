#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全项目训练检查 - 检查训练是否真的执行
"""

import json
import sys
import io
from pathlib import Path
from datetime import datetime

# Windows编码修复
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def check_training_status():
    """全面检查训练状态"""
    
    print("=" * 70)
    print("全项目训练检查")
    print("=" * 70)
    
    character = "linzhi"
    
    # 1. 检查训练输出目录
    print("\n📁 1. 检查训练输出目录")
    print("-" * 70)
    
    lora_dir = Path(f"out/lora_{character}")
    merged_dir = Path(f"out/merged_{character}")
    
    lora_exists = lora_dir.exists()
    merged_exists = merged_dir.exists()
    
    print(f"  LoRA目录: {lora_dir} - {'✅ 存在' if lora_exists else '❌ 不存在'}")
    print(f"  合并目录: {merged_dir} - {'✅ 存在' if merged_exists else '❌ 不存在'}")
    
    if lora_exists:
        files = list(lora_dir.glob("*"))
        print(f"  文件数量: {len(files)}")
        for f in files[:10]:
            size = f.stat().st_size / 1024 / 1024 if f.is_file() else 0
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            print(f"    - {f.name} ({size:.1f}MB, {mtime.strftime('%Y-%m-%d %H:%M')})")
    
    # 2. 检查checkpoint
    print("\n📊 2. 检查训练checkpoint")
    print("-" * 70)
    
    if lora_exists:
        checkpoints = sorted([d for d in lora_dir.iterdir() if d.is_dir() and d.name.startswith('checkpoint-')])
        print(f"  Checkpoint数量: {len(checkpoints)}")
        
        if checkpoints:
            latest = checkpoints[-1]
            print(f"  最新checkpoint: {latest.name}")
            
            # 检查trainer_state.json
            trainer_state = latest / "trainer_state.json"
            if trainer_state.exists():
                try:
                    with open(trainer_state, 'r', encoding='utf-8') as f:
                        state = json.load(f)
                    
                    print(f"  ✅ 训练状态文件存在")
                    print(f"     Epoch: {state.get('epoch', 'N/A')}")
                    print(f"     总步数: {state.get('max_steps', 'N/A')}")
                    print(f"     已完成步数: {state.get('global_step', 'N/A')}")
                    print(f"     最新loss: {state.get('log_history', [{}])[-1].get('loss', 'N/A') if state.get('log_history') else 'N/A'}")
                    
                except Exception as e:
                    print(f"  ⚠️  无法读取训练状态: {e}")
            else:
                print(f"  ❌ 训练状态文件不存在")
            
            # 检查LoRA权重文件
            adapter_files = list(latest.glob("adapter_model.*"))
            print(f"  LoRA权重文件: {len(adapter_files)}个")
            for f in adapter_files:
                size = f.stat().st_size / 1024 / 1024
                print(f"    - {f.name} ({size:.1f}MB)")
        else:
            print(f"  ❌ 没有找到checkpoint")
    else:
        print(f"  ❌ LoRA目录不存在，无法检查checkpoint")
    
    # 3. 检查合并模型
    print("\n🔗 3. 检查合并模型")
    print("-" * 70)
    
    if merged_exists:
        model_files = list(merged_dir.glob("*.safetensors")) + list(merged_dir.glob("*.bin"))
        config_files = list(merged_dir.glob("config.json"))
        tokenizer_files = list(merged_dir.glob("tokenizer*"))
        
        print(f"  模型文件: {len(model_files)}个")
        for f in model_files[:5]:
            size = f.stat().st_size / 1024 / 1024
            print(f"    - {f.name} ({size:.1f}MB)")
        
        print(f"  配置文件: {len(config_files)}个")
        print(f"  Tokenizer文件: {len(tokenizer_files)}个")
        
        if model_files and config_files and tokenizer_files:
            print(f"  ✅ 合并模型文件完整")
        else:
            print(f"  ⚠️  合并模型文件不完整")
    else:
        print(f"  ❌ 合并模型目录不存在")
    
    # 4. 检查Ollama模型
    print("\n🤖 4. 检查Ollama模型")
    print("-" * 70)
    
    try:
        import subprocess
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            output = result.stdout
            if 'linzhi-lora' in output:
                print(f"  ✅ Ollama模型存在: linzhi-lora")
                
                # 检查模型信息
                info_result = subprocess.run(['ollama', 'show', 'linzhi-lora'], capture_output=True, text=True, timeout=5)
                if info_result.returncode == 0:
                    print(f"  模型信息:")
                    for line in info_result.stdout.split('\n')[:10]:
                        if line.strip():
                            print(f"    {line}")
            else:
                print(f"  ❌ Ollama模型不存在: linzhi-lora")
        else:
            print(f"  ⚠️  无法检查Ollama模型（ollama命令失败）")
    except Exception as e:
        print(f"  ⚠️  无法检查Ollama模型: {e}")
    
    # 5. 检查训练数据
    print("\n📚 5. 检查训练数据")
    print("-" * 70)
    
    train_file = Path(f"datasets/{character}/train.jsonl")
    if train_file.exists():
        with open(train_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"  ✅ 训练文件存在: {train_file}")
        print(f"  样本数量: {len(lines)}")
        
        # 检查第一个样本
        if lines:
            try:
                data = json.loads(lines[0])
                messages = data.get('messages', [])
                print(f"  第一个样本消息数: {len(messages)}")
                print(f"  消息角色: {[m.get('role') for m in messages]}")
                
                # 检查是否有system
                has_system = any(m.get('role') == 'system' for m in messages)
                print(f"  包含system: {'❌ 是' if has_system else '✅ 否'}")
                
            except Exception as e:
                print(f"  ⚠️  无法解析第一个样本: {e}")
    else:
        print(f"  ❌ 训练文件不存在: {train_file}")
    
    # 6. 检查训练配置
    print("\n⚙️  6. 检查训练配置")
    print("-" * 70)
    
    try:
        import yaml
        with open("character_configs.yaml", 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        char_config = config.get('characters', {}).get(character, {})
        training_params = char_config.get('training_params', {})
        
        print(f"  ✅ 配置文件存在")
        print(f"  Epochs: {training_params.get('epochs', 'N/A')}")
        print(f"  Learning rate: {training_params.get('learning_rate', 'N/A')}")
        print(f"  LoRA r: {training_params.get('lora_r', 'N/A')}")
        print(f"  Base model: {training_params.get('base_model', 'N/A')}")
        
    except Exception as e:
        print(f"  ⚠️  无法读取配置: {e}")
    
    # 7. 检查训练日志（如果有）
    print("\n📝 7. 检查训练日志")
    print("-" * 70)
    
    log_files = list(Path(".").glob("*.log")) + list(Path(".").glob("training_*.txt"))
    if log_files:
        print(f"  找到日志文件: {len(log_files)}个")
        for f in log_files[:5]:
            size = f.stat().st_size / 1024
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            print(f"    - {f.name} ({size:.1f}KB, {mtime.strftime('%Y-%m-%d %H:%M')})")
    else:
        print(f"  ℹ️  未找到日志文件")
    
    # 8. 总结和建议
    print("\n💡 8. 总结和建议")
    print("-" * 70)
    
    issues = []
    
    if not lora_exists:
        issues.append("❌ LoRA目录不存在 - 可能没有训练过")
    
    if lora_exists and not checkpoints:
        issues.append("❌ 没有checkpoint - 训练可能没有完成")
    
    if not merged_exists:
        issues.append("❌ 合并模型不存在 - 无法导入Ollama")
    
    if not issues:
        print("  ✅ 所有检查通过")
        print("  💡 如果模型效果不好，可能是:")
        print("     1. 训练数据质量问题")
        print("     2. 训练参数不合适")
        print("     3. 模型过拟合或欠拟合")
        print("     4. Ollama导入时使用了错误的模型")
    else:
        print("  ⚠️  发现以下问题:")
        for issue in issues:
            print(f"     {issue}")
        print("\n  🔧 建议:")
        print("     1. 运行 .\\quick_fix.ps1 清理旧模型")
        print("     2. 运行 .\\train.ps1 linzhi 重新训练")
        print("     3. 确保训练完成后再导入Ollama")

if __name__ == "__main__":
    check_training_status()

