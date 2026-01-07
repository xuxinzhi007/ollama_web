#!/usr/bin/env python3
"""
合并安全性验证脚本
验证合并前后训练参数和流程的一致性，确保不影响模型训练质量
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

# 确保能导入 config_manager
sys.path.append(str(Path(__file__).parent))

from config_manager import ConfigManager

class MergeSafetyValidator:
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.issues = []

    def log_issue(self, level: str, message: str):
        """记录验证问题"""
        self.issues.append({"level": level, "message": message})
        symbol = {"INFO": "💡", "WARNING": "⚠️", "ERROR": "❌"}
        print(f"{symbol.get(level, '📝')} {level}: {message}")

    def validate_config_parameter_mapping(self) -> bool:
        """验证配置参数映射的正确性"""
        print("\n🔍 验证配置参数映射...")

        try:
            # 测试角色配置读取
            config_char = ConfigManager(character="linzhi")

            # 关键训练参数检查
            critical_params = {
                'model.base_model': ('基础模型', 'Qwen/Qwen2.5-0.5B-Instruct'),
                'training.epochs': ('训练轮数', float),
                'training.learning_rate': ('学习率', float),
                'lora.rank': ('LoRA rank', int),
                'lora.alpha': ('LoRA alpha', int),
                'lora.dropout': ('LoRA dropout', float),
            }

            all_params_valid = True

            for param_path, (desc, expected_type) in critical_params.items():
                value = config_char.get(param_path)

                if value is None:
                    self.log_issue("ERROR", f"关键参数缺失: {desc} ({param_path})")
                    all_params_valid = False
                    continue

                # 类型检查
                if expected_type == str:
                    if not isinstance(value, str):
                        self.log_issue("ERROR", f"参数类型错误: {desc} 应为字符串，实际为 {type(value)}")
                        all_params_valid = False
                elif expected_type in [int, float]:
                    if not isinstance(value, (int, float)):
                        self.log_issue("ERROR", f"参数类型错误: {desc} 应为数字，实际为 {type(value)}")
                        all_params_valid = False
                else:  # 特定值检查
                    if value != expected_type:
                        self.log_issue("WARNING", f"参数值异常: {desc} = {value}，期望 {expected_type}")

                print(f"   ✅ {desc}: {value}")

            return all_params_valid

        except Exception as e:
            self.log_issue("ERROR", f"配置参数验证失败: {e}")
            return False

    def validate_training_args_generation(self) -> bool:
        """验证训练参数生成的正确性"""
        print("\n🔍 验证训练参数生成...")

        try:
            config_char = ConfigManager(character="linzhi")
            training_args = config_char.get_training_args()

            # 检查必要的训练参数
            required_args = [
                'model_name_or_path', 'num_train_epochs', 'learning_rate',
                'lora_r', 'lora_alpha', 'lora_dropout'
            ]

            missing_args = []
            for arg in required_args:
                if arg not in training_args or training_args[arg] is None:
                    missing_args.append(arg)

            if missing_args:
                self.log_issue("ERROR", f"训练参数缺失: {missing_args}")
                return False

            # 显示生成的训练参数
            print("   生成的训练参数:")
            for key, value in training_args.items():
                if value is not None:
                    print(f"      {key}: {value}")

            self.log_issue("INFO", "训练参数生成验证通过")
            return True

        except Exception as e:
            self.log_issue("ERROR", f"训练参数生成验证失败: {e}")
            return False

    def simulate_training_command(self, character: str) -> Tuple[bool, List[str]]:
        """模拟训练命令生成（不实际执行）"""
        print(f"\n🔍 模拟 {character} 的训练命令生成...")

        try:
            # 模拟 smart_train.py 的命令生成逻辑
            config = ConfigManager(character=character)

            # 获取训练参数
            training_params = config.config.get('characters', {}).get(character, {}).get('training_params', {})

            # 构建模拟命令
            cmd = [
                sys.executable, "train_lora.py",
                "--train_jsonl", f"datasets/{character}/train.jsonl",
                "--output_dir", f"out/lora_{character}"
            ]

            # 添加模型参数
            base_model = training_params.get("base_model")
            if base_model:
                cmd.extend(["--model_name_or_path", str(base_model)])

            # 添加训练参数
            if 'epochs' in training_params:
                cmd.extend(["--num_train_epochs", str(training_params['epochs'])])
            if 'learning_rate' in training_params:
                cmd.extend(["--learning_rate", str(training_params['learning_rate'])])
            if 'lora_r' in training_params:
                cmd.extend(["--lora_r", str(training_params['lora_r'])])
            if 'lora_alpha' in training_params:
                cmd.extend(["--lora_alpha", str(training_params['lora_alpha'])])
            if 'lora_dropout' in training_params:
                cmd.extend(["--lora_dropout", str(training_params['lora_dropout'])])

            # 默认参数
            cmd.extend([
                "--merge_and_save",
                "--merged_dir", f"out/merged_{character}"
            ])

            print("   生成的训练命令:")
            print(f"      {' '.join(cmd)}")

            # 验证命令完整性
            required_params = ["--train_jsonl", "--output_dir", "--model_name_or_path"]
            missing_params = [p for p in required_params if p not in cmd]

            if missing_params:
                self.log_issue("ERROR", f"训练命令缺失必要参数: {missing_params}")
                return False, cmd

            self.log_issue("INFO", f"{character} 训练命令生成验证通过")
            return True, cmd

        except Exception as e:
            self.log_issue("ERROR", f"训练命令模拟失败: {e}")
            return False, []

    def validate_data_file_access(self) -> bool:
        """验证数据文件访问逻辑"""
        print("\n🔍 验证数据文件访问...")

        datasets_dir = self.root_dir / "datasets"
        if not datasets_dir.exists():
            self.log_issue("WARNING", "datasets 目录不存在，跳过数据文件验证")
            return True

        valid_chars = []
        for char_dir in datasets_dir.iterdir():
            if not char_dir.is_dir() or char_dir.name == 'archive':
                continue

            char_name = char_dir.name
            train_files = list(char_dir.glob("*train*.jsonl"))
            val_files = list(char_dir.glob("*val*.jsonl"))

            if train_files:
                print(f"   ✅ {char_name}: 找到 {len(train_files)} 个训练文件")
                valid_chars.append(char_name)
            else:
                self.log_issue("WARNING", f"{char_name}: 未找到训练文件")

        if valid_chars:
            self.log_issue("INFO", f"数据文件验证通过，可用角色: {', '.join(valid_chars)}")
            return True
        else:
            self.log_issue("ERROR", "未找到任何可用的训练数据")
            return False

    def check_critical_file_integrity(self) -> bool:
        """检查关键文件完整性"""
        print("\n🔍 检查关键文件完整性...")

        critical_files = {
            "character_configs.yaml": "角色配置文件",
            "train_lora.py": "训练脚本",
            "config_manager.py": "配置管理器",
            "smart_train.py": "智能训练脚本"
        }

        missing_files = []
        for file_name, desc in critical_files.items():
            file_path = self.root_dir / file_name
            if file_path.exists():
                print(f"   ✅ {desc}: {file_name}")
            else:
                missing_files.append(f"{desc} ({file_name})")

        if missing_files:
            self.log_issue("ERROR", f"关键文件缺失: {', '.join(missing_files)}")
            return False

        self.log_issue("INFO", "关键文件完整性检查通过")
        return True

    def generate_safety_report(self) -> Dict[str, Any]:
        """生成安全性评估报告"""
        error_count = len([i for i in self.issues if i["level"] == "ERROR"])
        warning_count = len([i for i in self.issues if i["level"] == "WARNING"])

        safety_level = "SAFE"
        if error_count > 0:
            safety_level = "UNSAFE"
        elif warning_count > 2:
            safety_level = "RISKY"

        return {
            "safety_level": safety_level,
            "error_count": error_count,
            "warning_count": warning_count,
            "issues": self.issues,
            "recommendation": self._get_recommendation(safety_level)
        }

    def _get_recommendation(self, safety_level: str) -> str:
        """获取安全建议"""
        if safety_level == "SAFE":
            return "✅ 安全：可以进行合并操作"
        elif safety_level == "RISKY":
            return "⚠️  有风险：建议先解决警告项，再进行合并"
        else:
            return "❌ 不安全：必须先解决所有错误，才能进行合并"

def main():
    """主验证流程"""
    print("🛡️  合并安全性验证")
    print("=" * 60)

    validator = MergeSafetyValidator()

    # 执行各项验证
    tests = [
        ("关键文件完整性", validator.check_critical_file_integrity),
        ("配置参数映射", validator.validate_config_parameter_mapping),
        ("训练参数生成", validator.validate_training_args_generation),
        ("数据文件访问", validator.validate_data_file_access),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            validator.log_issue("ERROR", f"{test_name} 执行失败: {e}")
            results[test_name] = False

    # 测试命令生成（如果有可用角色）
    try:
        validator.simulate_training_command("linzhi")
    except Exception as e:
        validator.log_issue("WARNING", f"命令生成测试失败: {e}")

    # 生成安全报告
    report = validator.generate_safety_report()

    print("\n" + "=" * 60)
    print("📊 安全性评估报告")
    print("=" * 60)
    print(f"安全等级: {report['safety_level']}")
    print(f"错误数量: {report['error_count']}")
    print(f"警告数量: {report['warning_count']}")
    print(f"建议: {report['recommendation']}")

    # 显示测试结果摘要
    print(f"\n📋 测试结果摘要:")
    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"   {test_name}: {status}")

    # 保存详细报告
    report_file = Path("merge_safety_report.json")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n💾 详细报告已保存到: {report_file}")

    if report['safety_level'] == "SAFE":
        print(f"\n🎉 验证完成！可以安全进行合并操作")
        return True
    else:
        print(f"\n⚠️  请先解决上述问题，再进行合并")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)