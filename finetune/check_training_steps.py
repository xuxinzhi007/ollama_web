#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查训练步数计算 - 诊断为什么总是339步
"""

import json
import sys
import io
from pathlib import Path

# Windows编码修复
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def check_training_steps():
    """检查训练步数计算"""
    
    # 1. 检查数据集大小
    train_file = Path("datasets/linzhi/train.jsonl")
    if not train_file.exists():
        print(f"❌ 训练文件不存在: {train_file}")
        return
    
    with open(train_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    dataset_size = len(lines)
    print(f"📊 数据集大小: {dataset_size} 个样本")
    
    # 2. 检查训练配置（从character_configs.yaml）
    try:
        import yaml
        with open("character_configs.yaml", 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        char_config = config['characters']['linzhi']
        epochs = char_config['training_params']['epochs']
        print(f"📋 训练轮数: {epochs} epochs")
        
    except Exception as e:
        print(f"⚠️  无法读取配置文件: {e}")
        epochs = 3.0
    
    # 3. 检查环境配置（从env_detect）
    try:
        from env_detect import plan_environment
        
        plan = plan_environment()
        batch_size = plan.defaults.get('per_device_train_batch_size', 1)
        grad_accum = plan.defaults.get('gradient_accumulation_steps', 1)
        
        print(f"\n🔧 训练配置:")
        print(f"   Batch size (per device): {batch_size}")
        print(f"   Gradient accumulation steps: {grad_accum}")
        print(f"   Effective batch size: {batch_size * grad_accum}")
        print(f"   Device: {plan.device}")
        print(f"   Dtype: {plan.dtype}")
        
        # 计算步数
        steps_per_epoch = dataset_size / (batch_size * grad_accum)
        total_steps = int(steps_per_epoch * epochs)
        
        print(f"\n📈 步数计算:")
        print(f"   每个epoch步数: {steps_per_epoch:.1f} ≈ {int(steps_per_epoch)} 步")
        print(f"   总训练步数: {total_steps} 步 ({epochs} epochs × {int(steps_per_epoch)} steps)")
        
        if int(steps_per_epoch) == 339:
            print(f"\n✅ 确认：每个epoch确实是339步（这是正常的）")
            print(f"   原因：数据集大小({dataset_size}) ÷ 有效batch size({batch_size * grad_accum}) = {steps_per_epoch:.1f}")
        else:
            print(f"\n⚠️  预期步数: {int(steps_per_epoch)}, 但实际显示339步")
            print(f"   可能原因：")
            print(f"   1. 实际使用的batch size或gradient accumulation不同")
            print(f"   2. 数据集在训练时被过滤或处理")
        
    except Exception as e:
        print(f"❌ 无法检查环境配置: {e}")
        import traceback
        traceback.print_exc()
    
    # 4. 检查最近的checkpoint（如果有）
    checkpoint_dir = Path("out/lora_linzhi")
    if checkpoint_dir.exists():
        checkpoint_dirs = sorted([d for d in checkpoint_dir.iterdir() if d.is_dir() and d.name.startswith('checkpoint-')])
        if checkpoint_dirs:
            latest_checkpoint = checkpoint_dirs[-1]
            trainer_state_file = latest_checkpoint / "trainer_state.json"
            if trainer_state_file.exists():
                try:
                    with open(trainer_state_file, 'r', encoding='utf-8') as f:
                        state = json.load(f)
                    
                    print(f"\n📁 最新checkpoint: {latest_checkpoint.name}")
                    print(f"   当前epoch: {state.get('epoch', 0):.2f}")
                    print(f"   总步数: {state.get('max_steps', 'N/A')}")
                    print(f"   已完成步数: {state.get('global_step', 0)}")
                    print(f"   每个epoch步数: {state.get('log_history', [{}])[-1].get('step', 'N/A') if state.get('log_history') else 'N/A'}")
                    
                except Exception as e:
                    print(f"⚠️  无法读取checkpoint状态: {e}")

if __name__ == "__main__":
    check_training_steps()

