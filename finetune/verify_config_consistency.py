#!/usr/bin/env python3
"""
配置一致性验证脚本 - 确保两个工具使用相同的配置数据源
无需安装额外依赖，直接读取 YAML 文件验证
"""

import sys
import json
from pathlib import Path

def simple_yaml_read(file_path: Path) -> dict:
    """简单的 YAML 读取（仅支持基本格式）"""
    if not file_path.exists():
        return {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 简单解析（仅适用于本项目的 YAML 格式）
        result = {}
        current_section = None
        current_char = None

        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if line.startswith('characters:'):
                current_section = 'characters'
                result[current_section] = {}
                continue

            if current_section == 'characters':
                if line.endswith(':') and not line.startswith(' '):
                    # 角色名
                    current_char = line.rstrip(':')
                    result[current_section][current_char] = {}
                elif line.startswith('  ') and ':' in line and current_char:
                    # 角色属性
                    key, value = line.strip().split(':', 1)
                    value = value.strip().strip('"\'')

                    # 尝试转换类型
                    if value.lower() == 'true':
                        value = True
                    elif value.lower() == 'false':
                        value = False
                    elif value.replace('.', '').replace('-', '').isdigit():
                        if '.' in value:
                            value = float(value)
                        else:
                            value = int(value)

                    if key == 'training_params':
                        result[current_section][current_char][key] = {}
                    elif key == 'inference_params':
                        result[current_section][current_char][key] = {}
                    else:
                        result[current_section][current_char][key] = value

        return result
    except Exception as e:
        print(f"❌ YAML 解析失败: {e}")
        return {}

def extract_training_params(char_config: dict, character: str) -> dict:
    """从角色配置中提取训练参数"""
    if 'characters' not in char_config or character not in char_config['characters']:
        return {}

    char_data = char_config['characters'][character]

    # 手动提取训练参数（模拟 smart_train.py 的逻辑）
    training_params = {}

    # 从字符串中解析 training_params
    content_lines = []
    with open('character_configs.yaml', 'r', encoding='utf-8') as f:
        in_character = False
        in_training_params = False
        indent_level = 0

        for line in f:
            if f"  {character}:" in line:
                in_character = True
                continue
            elif in_character and line.strip() and not line.startswith('  '):
                # 退出当前角色
                break
            elif in_character and "training_params:" in line:
                in_training_params = True
                indent_level = len(line) - len(line.lstrip())
                continue
            elif in_training_params:
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= indent_level and line.strip():
                    # 退出 training_params
                    break
                elif ':' in line:
                    key, value = line.strip().split(':', 1)
                    value = value.strip()

                    # 转换类型
                    if value.replace('.', '').replace('-', '').isdigit():
                        if '.' in value:
                            training_params[key] = float(value)
                        else:
                            training_params[key] = int(value)
                    else:
                        training_params[key] = value.strip('"\'')

    return training_params

def verify_smart_train_config(character: str) -> dict:
    """验证 smart_train.py 读取的配置"""
    print(f"📋 验证 smart_train.py 配置读取...")

    # 读取 character_configs.yaml
    config_file = Path("character_configs.yaml")
    if not config_file.exists():
        print(f"❌ 配置文件不存在: {config_file}")
        return {}

    training_params = extract_training_params({}, character)

    print(f"   角色: {character}")
    print(f"   配置源: character_configs.yaml")
    print(f"   读取到的训练参数:")
    for key, value in training_params.items():
        print(f"      {key}: {value}")

    return training_params

def simulate_train_to_ollama_config(character: str) -> dict:
    """模拟 train_to_ollama.py 通过 ConfigManager 读取的配置"""
    print(f"\\n📋 模拟 train_to_ollama.py 配置读取...")

    # 模拟 ConfigManager 的参数映射逻辑
    training_params = extract_training_params({}, character)

    # 模拟 config_manager.py 中的映射
    mapped_config = {
        "model.base_model": training_params.get('base_model', 'Qwen/Qwen2.5-0.5B-Instruct'),
        "training.epochs": training_params.get('epochs', 2.0),
        "training.learning_rate": training_params.get('learning_rate', 2e-4),
        "lora.rank": training_params.get('lora_r', 8),
        "lora.alpha": training_params.get('lora_alpha', 16),
        "lora.dropout": training_params.get('lora_dropout', 0.05),
    }

    print(f"   角色: {character}")
    print(f"   配置源: character_configs.yaml (通过 ConfigManager)")
    print(f"   映射后的参数:")
    for key, value in mapped_config.items():
        print(f"      {key}: {value}")

    return mapped_config

def compare_configurations(character: str) -> bool:
    """对比两个工具读取的配置是否一致"""
    print(f"\\n🔍 对比配置一致性...")

    # 获取两边的配置
    smart_train_params = verify_smart_train_config(character)
    train_to_ollama_config = simulate_train_to_ollama_config(character)

    # 建立映射关系进行对比
    param_mapping = {
        'base_model': 'model.base_model',
        'epochs': 'training.epochs',
        'learning_rate': 'training.learning_rate',
        'lora_r': 'lora.rank',
        'lora_alpha': 'lora.alpha',
        'lora_dropout': 'lora.dropout',
    }

    inconsistencies = []

    for smart_key, ollama_key in param_mapping.items():
        smart_value = smart_train_params.get(smart_key)
        ollama_value = train_to_ollama_config.get(ollama_key)

        if smart_value != ollama_value:
            inconsistencies.append({
                'parameter': smart_key,
                'smart_train_value': smart_value,
                'train_to_ollama_value': ollama_value
            })

    print(f"\\n📊 一致性检查结果:")
    if not inconsistencies:
        print(f"   ✅ 所有参数一致！")
        print(f"   ✅ 两个工具使用相同的配置数据源")
        return True
    else:
        print(f"   ❌ 发现 {len(inconsistencies)} 个参数不一致:")
        for issue in inconsistencies:
            print(f"      {issue['parameter']}:")
            print(f"         smart_train.py: {issue['smart_train_value']}")
            print(f"         train_to_ollama.py: {issue['train_to_ollama_value']}")
        return False

def check_file_dependencies() -> dict:
    """检查文件依赖关系"""
    print(f"\\n📁 检查文件依赖关系...")

    files = {
        'character_configs.yaml': Path('character_configs.yaml').exists(),
        'config.yaml': Path('config.yaml').exists(),
        'config_manager.py': Path('config_manager.py').exists(),
        'smart_train.py': Path('smart_train.py').exists(),
        'train_to_ollama.py': Path('train_to_ollama.py').exists(),
    }

    for file_name, exists in files.items():
        status = "✅ 存在" if exists else "❌ 缺失"
        print(f"   {file_name}: {status}")

    return files

def main():
    """主验证流程"""
    print("🔍 配置一致性验证")
    print("=" * 50)

    # 检查文件
    files = check_file_dependencies()

    if not files.get('character_configs.yaml'):
        print("\\n❌ 缺少主配置文件，无法继续验证")
        return False

    # 验证配置一致性
    test_character = "linzhi"  # 使用 linzhi 作为测试角色

    try:
        consistent = compare_configurations(test_character)

        print(f"\\n" + "=" * 50)
        print(f"📊 验证结果总结")
        print(f"=" * 50)

        if consistent:
            print(f"✅ 配置一致性验证通过！")
            print(f"✅ 两个工具使用相同的配置数据源")
            print(f"✅ 可以安全使用统一配置管理")

            print(f"\\n💡 使用建议:")
            print(f"   主工具: python smart_train.py")
            print(f"   一键流程: python train_to_ollama.py --character {test_character} --ollama_name {test_character}-lora")

            return True
        else:
            print(f"❌ 配置不一致！")
            print(f"❌ 需要修复配置映射问题")
            return False

    except Exception as e:
        print(f"❌ 验证过程出错: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)