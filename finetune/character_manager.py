#!/usr/bin/env python3
"""
角色管理器 - 统一管理角色的创建和删除
"""
import os
import sys
import shutil
import yaml
from pathlib import Path
from typing import List, Dict, Optional

class CharacterManager:
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.config_file = self.root_dir / "character_configs.yaml"
        self.datasets_dir = self.root_dir / "datasets"
        self.output_dir = self.root_dir / "out"

    def load_config(self) -> Dict:
        """加载配置文件"""
        if not self.config_file.exists():
            print(f"❌ 配置文件不存在: {self.config_file}")
            return {"characters": {}}

        with open(self.config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def save_config(self, config: Dict):
        """保存配置文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, sort_keys=False)

    def list_characters(self) -> List[str]:
        """列出所有角色"""
        config = self.load_config()
        return list(config.get('characters', {}).keys())

    def get_character_info(self, character_id: str) -> Optional[Dict]:
        """获取角色信息"""
        config = self.load_config()
        return config.get('characters', {}).get(character_id)

    def create_character(self):
        """创建新角色（调用 create_character.py）"""
        import subprocess

        create_script = self.root_dir / "create_character.py"
        if not create_script.exists():
            print(f"❌ 角色创建脚本不存在: {create_script}")
            return False

        try:
            # 使用当前Python解释器运行脚本
            result = subprocess.run(
                [sys.executable, str(create_script)],
                cwd=str(self.root_dir)
            )
            return result.returncode == 0
        except Exception as e:
            print(f"❌ 创建角色失败: {e}")
            return False

    def delete_character(self, character_id: str, confirm: bool = True) -> bool:
        """
        删除角色及其所有相关文件

        Args:
            character_id: 角色ID
            confirm: 是否需要确认

        Returns:
            是否成功删除
        """
        config = self.load_config()
        characters = config.get('characters', {})

        if character_id not in characters:
            print(f"❌ 角色不存在: {character_id}")
            return False

        character_info = characters[character_id]
        character_name = character_info.get('name', character_id)

        # 显示即将删除的内容
        print(f"\n⚠️  即将删除角色: {character_name} ({character_id})")
        print("\n将删除以下内容:")

        # 1. 数据集目录
        dataset_dir = self.datasets_dir / character_id
        if dataset_dir.exists():
            print(f"  📁 数据集: {dataset_dir}")

        # 2. 训练输出目录
        output_dirs = []
        if self.output_dir.exists():
            for item in self.output_dir.iterdir():
                if item.is_dir() and character_id in item.name:
                    output_dirs.append(item)
                    print(f"  📁 训练输出: {item}")

        # 3. 配置文件中的条目
        print(f"  ⚙️  配置文件中的角色定义")

        if not output_dirs and not dataset_dir.exists():
            print("  (仅有配置文件条目)")

        # 确认删除
        if confirm:
            print("\n" + "="*50)
            response = input("确认删除？(yes/NO): ").strip().lower()
            if response not in ['yes', 'y']:
                print("❌ 已取消删除")
                return False

        print("\n🗑️  开始删除...")

        deleted_items = []
        failed_items = []

        # 删除数据集目录
        if dataset_dir.exists():
            try:
                shutil.rmtree(dataset_dir)
                deleted_items.append(f"数据集: {dataset_dir}")
                print(f"  ✅ 已删除数据集: {dataset_dir}")
            except Exception as e:
                failed_items.append(f"数据集: {dataset_dir} - {e}")
                print(f"  ❌ 删除数据集失败: {e}")

        # 删除训练输出目录
        for output_dir in output_dirs:
            try:
                shutil.rmtree(output_dir)
                deleted_items.append(f"训练输出: {output_dir}")
                print(f"  ✅ 已删除训练输出: {output_dir}")
            except Exception as e:
                failed_items.append(f"训练输出: {output_dir} - {e}")
                print(f"  ❌ 删除训练输出失败: {e}")

        # 从配置文件中删除
        try:
            del characters[character_id]
            config['characters'] = characters
            self.save_config(config)
            deleted_items.append("配置文件条目")
            print(f"  ✅ 已从配置文件中删除")
        except Exception as e:
            failed_items.append(f"配置文件 - {e}")
            print(f"  ❌ 从配置文件删除失败: {e}")

        # 总结
        print("\n" + "="*50)
        if failed_items:
            print(f"⚠️  删除完成（有 {len(failed_items)} 项失败）")
            print("\n失败项目:")
            for item in failed_items:
                print(f"  - {item}")
        else:
            print(f"✅ 角色 {character_name} ({character_id}) 已完全删除")
            print(f"\n共删除 {len(deleted_items)} 项:")
            for item in deleted_items:
                print(f"  - {item}")

        return len(failed_items) == 0

    def show_character_details(self, character_id: str):
        """显示角色详细信息"""
        config = self.load_config()
        character = config.get('characters', {}).get(character_id)

        if not character:
            print(f"❌ 角色不存在: {character_id}")
            return

        print("\n" + "="*50)
        print(f"📋 角色信息: {character.get('name', character_id)}")
        print("="*50)

        print(f"\n基本信息:")
        print(f"  ID: {character_id}")
        print(f"  名字: {character.get('name', '未设置')}")
        print(f"  描述: {character.get('description', '未设置')}")

        # 数据集信息
        print(f"\n数据集:")
        data_files = character.get('data_files', {})
        train_file = self.root_dir / data_files.get('train', '')
        val_file = self.root_dir / data_files.get('val', '')

        print(f"  训练集: {data_files.get('train', '未设置')}")
        if train_file.exists():
            with open(train_file, 'r') as f:
                train_count = sum(1 for _ in f)
            print(f"    ✅ 存在 ({train_count} 条)")
        else:
            print(f"    ❌ 不存在")

        print(f"  验证集: {data_files.get('val', '未设置')}")
        if val_file.exists():
            with open(val_file, 'r') as f:
                val_count = sum(1 for _ in f)
            print(f"    ✅ 存在 ({val_count} 条)")
        else:
            print(f"    ❌ 不存在")

        # 训练输出
        print(f"\n训练输出:")
        output_dirs = []
        if self.output_dir.exists():
            for item in self.output_dir.iterdir():
                if item.is_dir() and character_id in item.name:
                    output_dirs.append(item)

        if output_dirs:
            for output_dir in output_dirs:
                # 获取目录大小
                size = sum(f.stat().st_size for f in output_dir.rglob('*') if f.is_file())
                size_mb = size / (1024 * 1024)
                print(f"  📁 {output_dir.name} ({size_mb:.1f} MB)")
        else:
            print(f"  (无训练输出)")

        # 训练参数
        print(f"\n训练参数:")
        train_params = character.get('training_params', {})
        print(f"  轮数: {train_params.get('epochs', '未设置')}")
        print(f"  学习率: {train_params.get('learning_rate', '未设置')}")
        print(f"  LoRA rank: {train_params.get('lora_r', '未设置')}")
        print(f"  基础模型: {train_params.get('base_model', '未设置')}")

        print()


def main():
    """命令行接口"""
    import argparse

    parser = argparse.ArgumentParser(description="角色管理工具")
    parser.add_argument("action", choices=['list', 'create', 'delete', 'info'],
                       help="操作类型")
    parser.add_argument("character_id", nargs='?',
                       help="角色ID（用于 delete 和 info）")
    parser.add_argument("--yes", "-y", action="store_true",
                       help="跳过删除确认")

    args = parser.parse_args()

    manager = CharacterManager()

    if args.action == 'list':
        characters = manager.list_characters()
        print(f"\n📋 当前有 {len(characters)} 个角色:")
        for char_id in characters:
            char_info = manager.get_character_info(char_id)
            print(f"  - {char_id}: {char_info.get('name', '未命名')}")

    elif args.action == 'create':
        manager.create_character()

    elif args.action == 'delete':
        if not args.character_id:
            print("❌ 请指定角色ID")
            return
        manager.delete_character(args.character_id, confirm=not args.yes)

    elif args.action == 'info':
        if not args.character_id:
            print("❌ 请指定角色ID")
            return
        manager.show_character_details(args.character_id)


if __name__ == "__main__":
    main()
