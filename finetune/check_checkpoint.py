#!/usr/bin/env python3
"""检查checkpoint状态"""

import json
from pathlib import Path

character = "linzhi"
lora_dir = Path(f"out/lora_{character}")

if not lora_dir.exists():
    print("LoRA目录不存在")
    exit(1)

checkpoint_dirs = list(lora_dir.glob('checkpoint-*'))
if not checkpoint_dirs:
    print("没有checkpoint")
    exit(1)

print(f"找到 {len(checkpoint_dirs)} 个checkpoint:\n")

checkpoints_info = []
for cp_dir in checkpoint_dirs:
    state_file = cp_dir / "trainer_state.json"
    if state_file.exists():
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            epoch = state.get('epoch', 0)
            step = state.get('global_step', 0)
            logs = state.get('log_history', [])
            last_loss = logs[-1].get('loss', 'N/A') if logs else 'N/A'
            
            checkpoints_info.append({
                'name': cp_dir.name,
                'epoch': epoch,
                'step': step,
                'loss': last_loss,
                'mtime': cp_dir.stat().st_mtime
            })
        except Exception as e:
            print(f"⚠️  {cp_dir.name}: 无法读取 - {e}")

# 按epoch排序
checkpoints_info.sort(key=lambda x: x['epoch'], reverse=True)

print("按epoch排序（最新的在前）:")
for cp in checkpoints_info:
    print(f"  {cp['name']}: epoch={cp['epoch']:.2f}, step={cp['step']}, loss={cp['loss']}")

# 按修改时间排序
checkpoints_info.sort(key=lambda x: x['mtime'], reverse=True)
print("\n按修改时间排序（最新的在前）:")
for cp in checkpoints_info:
    print(f"  {cp['name']}: epoch={cp['epoch']:.2f}, step={cp['step']}, loss={cp['loss']}")

# 推荐使用的checkpoint
if checkpoints_info:
    # 按epoch选择最新的
    best_by_epoch = max(checkpoints_info, key=lambda x: x['epoch'])
    print(f"\n✅ 推荐使用（按epoch）: {best_by_epoch['name']}")
    print(f"   Epoch: {best_by_epoch['epoch']:.2f}, Loss: {best_by_epoch['loss']}")

