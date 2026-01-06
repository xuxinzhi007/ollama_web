#!/usr/bin/env python3
"""
训练诊断工具 - 检查为什么loss重置和效果差
"""

import json
import sys
from pathlib import Path

def check_checkpoint_status(character="linzhi"):
    """检查checkpoint状态"""
    print(f"\n🔍 检查 {character} 的训练状态...")
    print("=" * 60)
    
    lora_dir = Path(f"out/lora_{character}")
    if not lora_dir.exists():
        print("❌ LoRA目录不存在，没有训练记录")
        return
    
    # 检查checkpoint
    checkpoint_dirs = list(lora_dir.glob('checkpoint-*'))
    if not checkpoint_dirs:
        print("⚠️  没有找到checkpoint目录")
        print("   说明训练可能没有保存checkpoint，或者训练未完成")
        return
    
    print(f"✅ 找到 {len(checkpoint_dirs)} 个checkpoint:")
    
    for checkpoint_dir in sorted(checkpoint_dirs, key=lambda x: x.stat().st_mtime, reverse=True):
        print(f"\n📁 {checkpoint_dir.name}")
        
        # 读取trainer_state.json
        state_file = checkpoint_dir / "trainer_state.json"
        if state_file.exists():
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                
                epoch = state.get('epoch', 0)
                best_metric = state.get('best_metric', {})
                log_history = state.get('log_history', [])
                
                print(f"   当前epoch: {epoch:.2f}")
                print(f"   训练步数: {state.get('global_step', 0)}")
                
                if log_history:
                    last_log = log_history[-1]
                    loss = last_log.get('loss', 'N/A')
                    print(f"   最新loss: {loss}")
                    if 'eval_loss' in last_log:
                        print(f"   验证loss: {last_log['eval_loss']}")
                
                if best_metric:
                    print(f"   最佳指标: {best_metric}")
                    
            except Exception as e:
                print(f"   ⚠️  无法读取状态文件: {e}")
        else:
            print("   ⚠️  缺少trainer_state.json")
        
        # 检查是否有adapter文件
        adapter_file = checkpoint_dir / "adapter_model.bin"
        adapter_safetensors = checkpoint_dir / "adapter_model.safetensors"
        if adapter_file.exists() or adapter_safetensors.exists():
            print("   ✅ 有LoRA权重文件")
        else:
            print("   ⚠️  缺少LoRA权重文件")

def check_training_config(character="linzhi"):
    """检查训练配置"""
    print(f"\n⚙️  检查训练配置...")
    print("=" * 60)
    
    try:
        import yaml
        config_file = Path("character_configs.yaml")
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            char_config = config.get('characters', {}).get(character)
            if char_config:
                params = char_config.get('training_params', {})
                print(f"训练参数:")
                print(f"  epochs: {params.get('epochs', 'N/A')}")
                print(f"  learning_rate: {params.get('learning_rate', 'N/A')}")
                print(f"  lora_r: {params.get('lora_r', 'N/A')}")
                print(f"  lora_alpha: {params.get('lora_alpha', 'N/A')}")
                print(f"  lora_dropout: {params.get('lora_dropout', 'N/A')}")
    except Exception as e:
        print(f"⚠️  无法读取配置: {e}")

def check_merged_model(character="linzhi"):
    """检查合并后的模型"""
    print(f"\n🤖 检查合并模型...")
    print("=" * 60)
    
    merged_dir = Path(f"out/merged_{character}")
    if not merged_dir.exists():
        print("⚠️  合并模型目录不存在")
        print("   说明训练后可能没有合并，或者训练未完成")
        return
    
    # 检查关键文件
    required_files = [
        "config.json",
        "tokenizer.json",
        "model.safetensors",
        "pytorch_model.bin"
    ]
    
    print("模型文件:")
    for file_name in required_files:
        file_path = merged_dir / file_name
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"  ✅ {file_name} ({size_mb:.1f} MB)")
        else:
            print(f"  ❌ {file_name} (缺失)")
    
    # 检查run_meta.json
    meta_file = merged_dir / "run_meta.json"
    if meta_file.exists():
        try:
            with open(meta_file, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            print(f"\n训练元数据:")
            print(f"  设备: {meta.get('env_plan', {}).get('device', 'N/A')}")
            print(f"  训练轮数: {meta.get('args', {}).get('num_train_epochs', 'N/A')}")
            print(f"  学习率: {meta.get('args', {}).get('learning_rate', 'N/A')}")
        except Exception as e:
            print(f"  ⚠️  无法读取元数据: {e}")

def diagnose_loss_reset():
    """诊断loss重置问题"""
    print(f"\n🔍 诊断loss重置问题...")
    print("=" * 60)
    
    print("\n可能的原因:")
    print("1. ❌ 选择了'重新训练'而不是'继续训练'")
    print("   → 解决方案: 选择'继续训练'选项")
    
    print("\n2. ❌ checkpoint路径不正确")
    print("   → 检查: out/lora_linzhi/checkpoint-* 是否存在")
    
    print("\n3. ❌ trainer_state.json损坏或缺失")
    print("   → 检查: checkpoint目录中是否有trainer_state.json")
    
    print("\n4. ❌ 训练参数冲突")
    print("   → 如果设置了--num_train_epochs，可能覆盖checkpoint状态")
    
    print("\n5. ❌ 模型权重没有正确加载")
    print("   → 检查: checkpoint中是否有adapter_model.bin或adapter_model.safetensors")

def diagnose_poor_quality():
    """诊断模型效果差问题"""
    print(f"\n🔍 诊断模型效果差问题...")
    print("=" * 60)
    
    print("\n可能的原因:")
    print("1. ❌ 训练轮数不足")
    print("   → 当前loss: 0.5左右，可能需要降到0.1-0.3")
    print("   → 建议: 继续训练到loss稳定在0.1-0.3")
    
    print("\n2. ❌ 过拟合")
    print("   → 训练loss很低但验证loss很高")
    print("   → 检查: 验证集loss是否也在下降")
    
    print("\n3. ❌ 数据质量问题")
    print("   → 数据量不足（450样本可能不够）")
    print("   → 数据格式问题（system prompt重复）")
    print("   → 建议: 检查数据质量，考虑增加数据")
    
    print("\n4. ❌ LoRA参数设置问题")
    print("   → rank太小（16）可能学不到足够信息")
    print("   → 建议: 尝试rank=32，但注意过拟合")
    
    print("\n5. ❌ 模型合并或推理问题")
    print("   → LoRA权重没有正确合并")
    print("   → 推理时没有正确加载LoRA")
    print("   → 检查: 合并后的模型文件是否完整")
    
    print("\n6. ❌ 基础模型问题")
    print("   → Qwen2.5-0.5B太小，能力有限")
    print("   → 建议: 尝试1.5B或3B模型")

def provide_solutions():
    """提供解决方案"""
    print(f"\n💡 解决方案建议...")
    print("=" * 60)
    
    print("\n1. 正确继续训练:")
    print("   - 选择'继续训练'选项（不是'重新训练'）")
    print("   - 确保checkpoint存在且完整")
    print("   - 让系统自动计算剩余epochs")
    
    print("\n2. 判断训练是否达标:")
    print("   ✅ Loss降到0.1-0.3并稳定")
    print("   ✅ Token准确率>0.9")
    print("   ✅ 验证loss也在下降（不过拟合）")
    print("   ✅ 实际测试效果好（最重要）")
    
    print("\n3. 如果效果还是差:")
    print("   - 增加训练数据（500-1000样本）")
    print("   - 增加训练轮数（5-10 epochs）")
    print("   - 调整LoRA rank（16→32）")
    print("   - 使用更大的基础模型（1.5B或3B）")
    print("   - 检查数据质量（格式、内容）")
    
    print("\n4. 测试模型:")
    print("   - 使用ollama run测试")
    print("   - 检查是否加载了正确的system prompt")
    print("   - 测试多个对话场景")

def main():
    character = sys.argv[1] if len(sys.argv) > 1 else "linzhi"
    
    print("🔧 训练诊断工具")
    print("=" * 60)
    
    check_checkpoint_status(character)
    check_training_config(character)
    check_merged_model(character)
    diagnose_loss_reset()
    diagnose_poor_quality()
    provide_solutions()
    
    print("\n" + "=" * 60)
    print("✅ 诊断完成")

if __name__ == "__main__":
    main()

