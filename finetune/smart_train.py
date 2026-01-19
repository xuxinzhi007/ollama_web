#!/usr/bin/env python3
"""
智能LoRA训练脚本 - 自动匹配数据文件，简化工作流程
解决问题：
1. 自动检测和匹配数据集文件
2. 无需手动指定文件路径
3. 智能处理缺失文件情况
4. 提高测试效率

使用方法：
  python smart_train.py                    # 交互式选择角色
  python smart_train.py --character linzhi # 直接指定角色
  python smart_train.py --list             # 列出所有可用配置
  python smart_train.py --scan             # 扫描数据集状态
"""

import os
import sys
import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import subprocess
import time
import shutil
import zipfile
import urllib.request
import urllib.error

try:
    import questionary
except ImportError:
    questionary = None

def ask_confirm(message: str, default: bool = True) -> bool:
    """统一的确认对话框"""
    if questionary:
        return questionary.confirm(message, default=default).ask()
    else:
        suffix = " (Y/n)" if default else " (y/N)"
        response = input(f"{message}{suffix}: ").strip().lower()
        if default:
            return response in ['', 'y', 'yes']
        else:
            return response in ['y', 'yes']

def ask_text(message: str, default: str = "") -> str:
    """统一的文本输入"""
    if questionary:
        return questionary.text(message, default=default).ask() or default
    else:
        suffix = f" (默认: {default})" if default else ""
        response = input(f"{message}{suffix}: ").strip()
        return response if response else default

# Windows编码处理：设置UTF-8输出以支持emoji和中文
if sys.platform == 'win32':
    try:
        # 设置环境变量（如果未设置）
        if 'PYTHONIOENCODING' not in os.environ:
            os.environ['PYTHONIOENCODING'] = 'utf-8'
        if 'PYTHONUTF8' not in os.environ:
            os.environ['PYTHONUTF8'] = '1'
        
        # 尝试设置控制台编码为UTF-8
        import io
        # 重新打开stdout和stderr以应用UTF-8编码
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        if hasattr(sys.stderr, 'buffer'):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        # 如果设置失败，使用replace模式避免崩溃
        pass

class SmartTrainer:
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.datasets_dir = self.root_dir / "datasets"
        self.config_file = self.root_dir / "character_configs.yaml"
        self.config = None  # 延迟加载配置

        # 工具目录（放下载的 llama.cpp，不需要编译，只用转换脚本）
        self.tools_dir = self.root_dir / ".tools"
        self.llama_cpp_dir = self.tools_dir / "llama.cpp"

    def _ensure_llama_cpp_converter(self) -> Optional[Path]:
        """
        确保 llama.cpp 的 convert_hf_to_gguf.py 可用。
        优先：
        - 已存在的 .tools/llama.cpp
        - git clone（如果有 git）
        - 下载 zip 解压（没有 git 也能用）
        返回转换脚本路径或 None。
        """
        convert_py = self.llama_cpp_dir / "convert_hf_to_gguf.py"
        gguf_py_dir = self.llama_cpp_dir / "gguf-py"
        if convert_py.exists() and gguf_py_dir.exists():
            return convert_py

        self.tools_dir.mkdir(parents=True, exist_ok=True)

        # 如果目录存在但不完整，先清理，避免半拉子状态
        if self.llama_cpp_dir.exists() and not (convert_py.exists() and gguf_py_dir.exists()):
            try:
                shutil.rmtree(self.llama_cpp_dir)
            except Exception:
                pass

        print("\n📦 未找到 GGUF 转换工具，准备自动获取 llama.cpp（无需编译，仅下载源码）...")

        git = shutil.which("git")
        if git:
            try:
                cmd = [git, "clone", "--depth", "1", "https://github.com/ggerganov/llama.cpp.git", str(self.llama_cpp_dir)]
                print(f"执行: {' '.join(cmd)}")
                r = subprocess.run(cmd, capture_output=True, text=True)
                if r.returncode != 0:
                    print(f"⚠️ git clone 失败，将尝试 zip 下载。错误: {r.stderr.strip()}")
                else:
                    if convert_py.exists() and gguf_py_dir.exists():
                        print("✅ llama.cpp 已下载完成")
                        return convert_py
            except Exception as e:
                print(f"⚠️ git clone 异常，将尝试 zip 下载: {e}")

        # zip 下载兜底
        try:
            zip_url = "https://github.com/ggerganov/llama.cpp/archive/refs/heads/master.zip"
            zip_path = self.tools_dir / "llama.cpp-master.zip"
            print(f"下载: {zip_url}")
            urllib.request.urlretrieve(zip_url, zip_path)

            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(self.tools_dir)

            extracted = self.tools_dir / "llama.cpp-master"
            if extracted.exists():
                extracted.rename(self.llama_cpp_dir)
            try:
                zip_path.unlink(missing_ok=True)
            except Exception:
                pass

            if convert_py.exists() and gguf_py_dir.exists():
                print("✅ llama.cpp 已下载完成（zip）")
                return convert_py

            print("❌ llama.cpp 下载后未找到转换脚本/gguf-py，可能网络被拦截或下载不完整。")
            return None
        except urllib.error.URLError as e:
            print(f"❌ 下载 llama.cpp 失败（网络错误）: {e}")
            return None
        except Exception as e:
            print(f"❌ 下载/解压 llama.cpp 失败: {e}")
            return None

    def _convert_merged_to_gguf(self, merged_dir: Path, gguf_out: Path, outtype: str = "f16") -> bool:
        """
        使用 llama.cpp 的 convert_hf_to_gguf.py 把 HuggingFace merged 目录转换为 GGUF。
        注意：不做量化（量化需要编译出来的 quantize 可执行文件），这里只生成 f16 以保证“能跑”。
        """
        convert_py = self._ensure_llama_cpp_converter()
        if not convert_py:
            return False

        gguf_py_dir = self.llama_cpp_dir / "gguf-py"
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        # 让 convert_hf_to_gguf.py 能 import gguf
        env["PYTHONPATH"] = str(gguf_py_dir) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")

        # 许多模型（包含 Qwen 系列的部分变体）在写入词表时会用到 sentencepiece
        # Windows 上通常有预编译 wheel，直接 pip 安装即可（无需编译）。
        try:
            import sentencepiece  # noqa: F401
        except Exception:
            print("\n📦 检测到缺少依赖: sentencepiece（GGUF 转换需要）")
            print("   将自动安装（不需要编译）。")
            try:
                r = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-U", "sentencepiece"],
                    capture_output=True,
                    text=True,
                )
                if r.returncode != 0:
                    print("❌ 安装 sentencepiece 失败：")
                    if r.stdout.strip():
                        print(r.stdout.strip())
                    if r.stderr.strip():
                        print(r.stderr.strip())
                    return False
            except Exception as e:
                print(f"❌ 安装 sentencepiece 异常: {e}")
                return False

        def _run_convert_once() -> tuple[bool, str]:
            cmd = [
                sys.executable,
                str(convert_py),
                str(merged_dir),
                "--outtype",
                outtype,
                "--outfile",
                str(gguf_out),
            ]

            print("\n🔄 正在转换 GGUF（首次会比较慢）...")
            print(f"输出: {gguf_out}")
            print(f"执行: {' '.join(cmd)}")

            combined = []
            try:
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
                # 实时打印（避免卡住没反馈）
                assert p.stdout is not None
                for line in p.stdout:
                    line = line.rstrip()
                    if line:
                        print(line)
                        # 保存少量尾部输出用于错误诊断（避免占用太多内存）
                        combined.append(line)
                        if len(combined) > 300:
                            combined = combined[-300:]
                p.wait()
                if p.returncode != 0:
                    return False, "\n".join(combined[-80:])
                return True, "\n".join(combined[-80:])
            except Exception as e:
                return False, f"{e}"

        ok, tail = _run_convert_once()
        if not ok:
            print(f"❌ GGUF 转换失败。末尾日志：\n{tail}")
            return False

        if gguf_out.exists() and gguf_out.stat().st_size > 0:
            print("✅ GGUF 转换完成")
            return True
        print("❌ GGUF 文件未生成或为空")
        return False

    def _ensure_config_loaded(self):
        """确保配置已加载"""
        if self.config is None:
            self.config = self._load_config()

    def _load_config(self) -> Dict:
        """加载角色配置"""
        try:
            import yaml
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"❌ 配置文件不存在: {self.config_file}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ 加载配置失败: {e}")
            sys.exit(1)

    def check_model_cache(self):
        """检查模型缓存状态"""
        self._ensure_config_loaded()
        try:
            from model_cache import print_cache_status

            print("\n🔍 检查模型缓存状态")
            print("=" * 50)

            # 检查配置中的所有模型
            models_to_check = set()

            for char_name, char_config in self.config.get('characters', {}).items():
                training_params = char_config.get('training_params', {})
                base_model = training_params.get('base_model', 'Qwen/Qwen2.5-0.5B')

                # 标准化模型名称
                if base_model == 'Qwen/Qwen2.5-0.5B':
                    base_model = 'Qwen/Qwen2.5-0.5B-Instruct'

                models_to_check.add(base_model)

            # 如果没有配置，检查默认模型
            if not models_to_check:
                models_to_check.add('Qwen/Qwen2.5-0.5B-Instruct')

            for model in models_to_check:
                print_cache_status(model)
                print()

        except ImportError:
            print("❌ 无法导入模型缓存检测模块")
        except Exception as e:
            print(f"❌ 检查缓存时出错: {e}")

    def scan_datasets(self) -> Dict[str, Dict]:
        """扫描数据集目录，自动发现可用的数据文件"""
        print("🔍 扫描数据集...")

        dataset_info = {}

        if not self.datasets_dir.exists():
            print(f"📁 数据集目录不存在: {self.datasets_dir}")
            return dataset_info

        # 扫描各个角色目录
        for char_dir in self.datasets_dir.iterdir():
            if not char_dir.is_dir() or char_dir.name == 'archive':
                continue

            char_name = char_dir.name
            train_files = []
            val_files = []

            # 查找训练和验证文件
            for file_path in char_dir.glob("*.jsonl"):
                if "train" in file_path.name.lower():
                    train_files.append(file_path)
                elif "val" in file_path.name.lower():
                    val_files.append(file_path)

            if train_files or val_files:
                dataset_info[char_name] = {
                    'train_files': train_files,
                    'val_files': val_files,
                    'dir': char_dir
                }

        # 扫描archive目录中的历史数据
        archive_dir = self.datasets_dir / "archive"
        if archive_dir.exists():
            archive_files = list(archive_dir.glob("*.jsonl"))
            if archive_files:
                dataset_info['archive'] = {
                    'train_files': [f for f in archive_files if "train" in f.name.lower()],
                    'val_files': [f for f in archive_files if "val" in f.name.lower()],
                    'dir': archive_dir
                }

        return dataset_info

    def count_samples(self, file_path: Path) -> int:
        """统计JSONL文件中的样本数量"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return sum(1 for line in f if line.strip())
        except:
            return 0

    def validate_jsonl(self, file_path: Path) -> Tuple[bool, str]:
        """验证JSONL文件格式"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        if 'messages' not in data:
                            return False, f"第{i+1}行缺少'messages'字段"
                        if not isinstance(data['messages'], list):
                            return False, f"第{i+1}行'messages'不是数组"
                    except json.JSONDecodeError as e:
                        return False, f"第{i+1}行JSON格式错误: {e}"
            return True, "格式正确"
        except Exception as e:
            return False, f"文件读取错误: {e}"

    def list_configurations(self):
        """列出所有可用的角色配置"""
        self._ensure_config_loaded()
        print("\n📋 可用角色配置:")
        print("=" * 50)

        dataset_info = self.scan_datasets()

        for char_name, char_config in self.config.get('characters', {}).items():
            print(f"\n🎭 角色: {char_name}")
            print(f"   名称: {char_config.get('name', 'N/A')}")
            print(f"   描述: {char_config.get('description', 'N/A')}")

            # 检查配置的数据文件是否存在
            data_files = char_config.get('data_files', {})
            train_file = data_files.get('train')
            val_file = data_files.get('val')

            print(f"   配置的训练文件: {train_file}")
            print(f"   配置的验证文件: {val_file}")

            # 检查实际文件状态
            if char_name in dataset_info:
                info = dataset_info[char_name]
                print(f"   🔍 发现的训练文件: {len(info['train_files'])}个")
                for tf in info['train_files']:
                    count = self.count_samples(tf)
                    print(f"      📄 {tf.name} ({count}样本)")

                print(f"   🔍 发现的验证文件: {len(info['val_files'])}个")
                for vf in info['val_files']:
                    count = self.count_samples(vf)
                    print(f"      📄 {vf.name} ({count}样本)")
            else:
                print(f"   ⚠️  未发现 {char_name} 的数据文件")

        # 显示未配置的数据集
        unconfigured = set(dataset_info.keys()) - set(self.config.get('characters', {}).keys())
        if unconfigured:
            print(f"\n📂 发现未配置的数据集:")
            for char_name in unconfigured:
                if char_name == 'archive':
                    continue
                info = dataset_info[char_name]
                print(f"   📁 {char_name}/")
                print(f"      训练文件: {len(info['train_files'])}个")
                print(f"      验证文件: {len(info['val_files'])}个")

    def auto_match_files(self, character: str) -> Tuple[Optional[str], Optional[str]]:
        """自动匹配角色的训练和验证文件"""
        self._ensure_config_loaded()
        dataset_info = self.scan_datasets()

        # 首先检查配置文件中指定的路径
        char_config = self.config.get('characters', {}).get(character)
        if char_config:
            data_files = char_config.get('data_files', {})
            train_path = data_files.get('train')
            val_path = data_files.get('val')

            if train_path and val_path:
                train_full = self.root_dir / train_path
                val_full = self.root_dir / val_path

                if train_full.exists() and val_full.exists():
                    print(f"✅ 使用配置文件指定的数据:")
                    print(f"   训练: {train_path} ({self.count_samples(train_full)}样本)")
                    print(f"   验证: {val_path} ({self.count_samples(val_full)}样本)")
                    return str(train_full), str(val_full)

        # 如果配置文件路径不存在，尝试自动匹配
        if character in dataset_info:
            info = dataset_info[character]

            # 选择最大的训练文件
            train_file = None
            if info['train_files']:
                train_file = max(info['train_files'], key=lambda f: self.count_samples(f))

            # 选择验证文件
            val_file = None
            if info['val_files']:
                val_file = info['val_files'][0]  # 通常只有一个验证文件

            if train_file and val_file:
                print(f"🎯 自动匹配的数据文件:")
                print(f"   训练: {train_file.name} ({self.count_samples(train_file)}样本)")
                print(f"   验证: {val_file.name} ({self.count_samples(val_file)}样本)")
                return str(train_file), str(val_file)

            elif train_file:
                print(f"⚠️  只找到训练文件: {train_file.name} ({self.count_samples(train_file)}样本)")
                print(f"   缺少验证文件，可能影响训练效果")
                return str(train_file), None

        return None, None

    def interactive_select(self) -> str:
        """交互式选择角色"""
        self._ensure_config_loaded()
        dataset_info = self.scan_datasets()
        characters = list(self.config.get('characters', {}).keys())

        if not characters:
            print("\n❌ 没有可用的角色配置")
            sys.exit(1)

        print("\n🎭 请选择要训练的角色:")
        print("=" * 40)

        # 准备选择列表
        char_choices = []
        char_info_map = {}

        for char_name in characters:
            char_config = self.config['characters'][char_name]
            name = char_config.get('name', char_name)
            desc = char_config.get('description', '无描述')

            # 检查数据可用性（优先检查配置文件路径）
            status = "❌ 无数据"

            # 首先检查配置文件中指定的路径
            char_config = self.config['characters'][char_name]
            data_files = char_config.get('data_files', {})
            train_path = data_files.get('train')
            val_path = data_files.get('val')

            train_count = 0
            val_count = 0

            # 优先检查配置文件指定的路径
            config_files_exist = False
            if train_path:
                train_full = self.root_dir / train_path
                if train_full.exists():
                    train_count = self.count_samples(train_full)
                    config_files_exist = True

            if val_path:
                val_full = self.root_dir / val_path
                if val_full.exists():
                    val_count = self.count_samples(val_full)

            # 如果配置文件路径无效或不存在，再检查扫描结果
            if not config_files_exist and char_name in dataset_info:
                info = dataset_info[char_name]
                if info['train_files']:
                    train_count = sum(self.count_samples(f) for f in info['train_files'])
                if info['val_files']:
                    val_count = sum(self.count_samples(f) for f in info['val_files'])

            if train_count > 0:
                status = f"✅ {train_count}训练, {val_count}验证" if val_count > 0 else f"✅ {train_count}训练"

            # 格式化选项
            choice_text = f"{name} - {status}"
            char_choices.append(choice_text)
            char_info_map[choice_text] = char_name

        if questionary:
            # 使用箭头选择
            selected = questionary.select(
                "选择角色:",
                choices=char_choices
            ).ask()

            if not selected:
                print("\n👋 训练已取消")
                sys.exit(0)

            return char_info_map[selected]
        else:
            # 降级到传统数字输入
            for i, (char_name, choice_text) in enumerate(zip(characters, char_choices), 1):
                print(f"{i:2d}. {choice_text}")

            while True:
                try:
                    choice = input(f"\n请输入选择 (1-{len(characters)}): ").strip()
                    if not choice:
                        continue

                    idx = int(choice) - 1
                    if 0 <= idx < len(characters):
                        return characters[idx]
                    else:
                        print("❌ 无效选择，请重新输入")
                except ValueError:
                    print("❌ 请输入数字")
                except KeyboardInterrupt:
                    print("\n👋 训练已取消")
                    sys.exit(0)

    def check_prerequisites(self, character: str) -> bool:
        """检查训练前置条件"""
        self._ensure_config_loaded()
        print(f"\n🔍 检查 {character} 的训练前置条件...")

        # 检查角色配置
        if character not in self.config.get('characters', {}):
            print(f"❌ 角色配置不存在: {character}")
            return False

        # 检查数据文件
        train_path, val_path = self.auto_match_files(character)
        if not train_path:
            print(f"❌ 未找到 {character} 的训练数据")
            print(f"   请确保在以下位置放置数据文件:")
            print(f"   - datasets/{character}/train.jsonl")
            print(f"   - datasets/{character}/val.jsonl")
            return False

        # 验证数据格式
        print("🔍 验证数据格式...")
        valid, msg = self.validate_jsonl(Path(train_path))
        if not valid:
            print(f"❌ 训练数据格式错误: {msg}")
            return False

        if val_path:
            valid, msg = self.validate_jsonl(Path(val_path))
            if not valid:
                print(f"❌ 验证数据格式错误: {msg}")
                return False

        # 检查样本数量
        train_count = self.count_samples(Path(train_path))
        if train_count < 10:
            print(f"⚠️  训练样本数量较少: {train_count} (建议 ≥ 10)")

        print(f"✅ 前置条件检查通过")
        return True

    def show_main_menu(self):
        """显示主菜单（按工作流程组织）"""
        while True:
            print("\n" + "="*50)
            print("🚀 智能LoRA训练系统 - 主菜单")
            print("="*50)

            try:
                if questionary:
                    # 使用 questionary 的箭头选择
                    choices = [
                        "🎨 角色开发  - 创建和管理角色",
                        "🚀 模型训练  - 训练角色模型",
                        "📦 模型部署  - 导入和测试模型",
                        "🔧 系统工具  - 环境检查和数据验证",
                        "🚪 退出"
                    ]

                    choice = questionary.select(
                        "请选择功能:",
                        choices=choices,
                        instruction="(使用↑↓箭头选择，回车确认)"
                    ).ask()

                    if not choice:  # 用户取消
                        print("\n👋 再见！")
                        break

                    if "角色开发" in choice:
                        self._menu_character_development()
                    elif "模型训练" in choice:
                        self._menu_model_training()
                    elif "模型部署" in choice:
                        self._menu_model_deployment()
                    elif "系统工具" in choice:
                        self._menu_system_tools()
                    elif "退出" in choice:
                        print("👋 再见！")
                        break
                else:
                    # 降级到传统数字输入
                    print("\n📋 按工作流程选择:")
                    print("1) 🎨 角色开发  - 创建和管理角色")
                    print("2) 🚀 模型训练  - 训练角色模型")
                    print("3) 📦 模型部署  - 导入和测试模型")
                    print("4) 🔧 系统工具  - 环境检查和数据验证")
                    print("0) 退出")
                    print()

                    choice = input("请选择 (0-4): ").strip()

                    if choice == "1":
                        self._menu_character_development()
                    elif choice == "2":
                        self._menu_model_training()
                    elif choice == "3":
                        self._menu_model_deployment()
                    elif choice == "4":
                        self._menu_system_tools()
                    elif choice == "0":
                        print("👋 再见！")
                        break
                    else:
                        print("❌ 无效选择")

            except (KeyboardInterrupt, EOFError):
                print("\n👋 再见！")
                break

    def _menu_character_development(self):
        """菜单：角色开发"""
        from character_manager import CharacterManager
        manager = CharacterManager()

        print("\n" + "="*50)
        print("🎨 角色开发")
        print("="*50)

        if questionary:
            # 使用箭头选择
            choices = [
                "🆕 创建新角色",
                "📋 查看所有角色",
                "🔍 查看角色详情",
                "🗑️  删除角色",
                "📊 数据集统计",
                "🔙 返回主菜单"
            ]

            choice = questionary.select(
                "选择操作:",
                choices=choices
            ).ask()

            if not choice or "返回" in choice:
                return
        else:
            # 降级到传统输入
            print("1) 🆕 创建新角色")
            print("2) 📋 查看所有角色")
            print("3) 🔍 查看角色详情")
            print("4) 🗑️  删除角色")
            print("5) 📊 数据集统计")
            print("0) 返回")
            choice = input("\n选择 (0-5): ").strip()

        # 处理选择
        if "创建新角色" in choice or choice == "1":
            # 创建新角色
            print("\n📝 启动角色创建工具...\n")
            manager.create_character()

        elif "查看所有角色" in choice or choice == "2":
            # 列出所有角色
            characters = manager.list_characters()
            if not characters:
                print("\n❌ 当前没有角色")
                return

            print(f"\n📋 当前有 {len(characters)} 个角色:")
            print("="*50)
            for char_id in characters:
                char_info = manager.get_character_info(char_id)
                name = char_info.get('name', '未命名')
                desc = char_info.get('description', '无描述')
                print(f"\n🎭 {char_id}")
                print(f"   名字: {name}")
                print(f"   描述: {desc}")

        elif "查看角色详情" in choice or choice == "3":
            # 查看角色详情
            characters = manager.list_characters()
            if not characters:
                print("\n❌ 当前没有角色")
                return

            if questionary:
                # 使用箭头选择角色
                char_choices = []
                for char_id in characters:
                    char_info = manager.get_character_info(char_id)
                    name = char_info.get('name', '未命名')
                    char_choices.append(f"{char_id} - {name}")

                selected = questionary.select(
                    "选择要查看的角色:",
                    choices=char_choices
                ).ask()

                if selected:
                    char_id = selected.split(" - ")[0]
                    manager.show_character_details(char_id)
            else:
                print(f"\n📋 可用角色:")
                for i, char_id in enumerate(characters, 1):
                    char_info = manager.get_character_info(char_id)
                    print(f"{i}) {char_id} - {char_info.get('name', '未命名')}")

                try:
                    idx = int(input("\n选择角色编号: ").strip()) - 1
                    if 0 <= idx < len(characters):
                        manager.show_character_details(characters[idx])
                    else:
                        print("❌ 无效的编号")
                except ValueError:
                    print("❌ 请输入数字")

        elif "删除角色" in choice or choice == "4":
            # 删除角色
            characters = manager.list_characters()
            if not characters:
                print("\n❌ 当前没有角色")
                return

            if questionary:
                # 使用箭头选择要删除的角色
                char_choices = []
                for char_id in characters:
                    char_info = manager.get_character_info(char_id)
                    name = char_info.get('name', '未命名')
                    char_choices.append(f"{char_id} - {name}")

                selected = questionary.select(
                    "选择要删除的角色:",
                    choices=char_choices
                ).ask()

                if selected:
                    char_id = selected.split(" - ")[0]
                    manager.delete_character(char_id, confirm=True)
            else:
                print(f"\n📋 可删除的角色:")
                for i, char_id in enumerate(characters, 1):
                    char_info = manager.get_character_info(char_id)
                    print(f"{i}) {char_id} - {char_info.get('name', '未命名')}")

                try:
                    idx = int(input("\n选择要删除的角色编号: ").strip()) - 1
                    if 0 <= idx < len(characters):
                        manager.delete_character(characters[idx], confirm=True)
                    else:
                        print("❌ 无效的编号")
                except ValueError:
                    print("❌ 请输入数字")

        elif "数据集统计" in choice or choice == "5":
            # 数据集统计
            self._show_dataset_stats()

    def _menu_model_training(self):
        """菜单：模型训练"""
        print("\n" + "="*50)
        print("🚀 模型训练")
        print("="*50)

        if questionary:
            choices = [
                "🎯 选择角色开始训练",
                "📋 查看训练配置",
                "📊 扫描数据集状态",
                "💾 检查模型缓存",
                "🔙 返回主菜单"
            ]

            choice = questionary.select(
                "选择操作:",
                choices=choices
            ).ask()

            if not choice or "返回" in choice:
                return
        else:
            print("1) 🎯 选择角色开始训练")
            print("2) 📋 查看训练配置")
            print("3) 📊 扫描数据集状态")
            print("4) 💾 检查模型缓存")
            print("0) 返回")
            choice = input("\n选择 (0-4): ").strip()

        if "开始训练" in choice or choice == "1":
            character = self.interactive_select()
            if self.check_prerequisites(character):
                self._confirm_and_train(character)
        elif "训练配置" in choice or choice == "2":
            self.list_configurations()
        elif "扫描数据集" in choice or choice == "3":
            self._show_dataset_scan()
        elif "检查模型缓存" in choice or choice == "4":
            self.check_model_cache()

    def _menu_model_deployment(self):
        """菜单：模型部署"""
        print("\n" + "="*50)
        print("📦 模型部署")
        print("="*50)

        if questionary:
            choices = [
                "📥 导入模型到Ollama",
                "📋 查看Ollama模型列表",
                "🗑️  删除Ollama模型",
                "🧪 测试模型效果",
                "🔙 返回主菜单"
            ]

            choice = questionary.select(
                "选择操作:",
                choices=choices
            ).ask()

            if not choice or "返回" in choice:
                return
        else:
            print("1) 📥 导入模型到Ollama")
            print("2) 📋 查看Ollama模型列表")
            print("3) 🗑️  删除Ollama模型")
            print("4) 🧪 测试模型效果")
            print("0) 返回")
            choice = input("\n选择 (0-4): ").strip()

        if "导入模型" in choice or choice == "1":
            self._import_to_ollama()
        elif "模型列表" in choice or choice == "2":
            self._show_ollama_models()
        elif "删除" in choice or choice == "3":
            self._delete_ollama_model()
        elif "测试" in choice or choice == "4":
            self._test_ollama_model()

    def _menu_system_tools(self):
        """菜单：系统工具"""
        print("\n" + "="*50)
        print("🔧 系统工具")
        print("="*50)

        if questionary:
            choices = [
                "🔍 全面环境诊断",
                "✅ 验证数据集格式",
                "💾 查看磁盘使用",
                "🛠️  环境设置助手",
                "🔙 返回主菜单"
            ]

            choice = questionary.select(
                "选择操作:",
                choices=choices
            ).ask()

            if not choice or "返回" in choice:
                return
        else:
            print("1) 🔍 全面环境诊断")
            print("2) ✅ 验证数据集格式")
            print("3) 💾 查看磁盘使用")
            print("4) 🛠️  环境设置助手")
            print("0) 返回")
            choice = input("\n选择 (0-4): ").strip()

        if "环境诊断" in choice or choice == "1":
            self._comprehensive_environment_check()
        elif "验证数据集" in choice or choice == "2":
            self._validate_all_datasets()
        elif "磁盘使用" in choice or choice == "3":
            self._check_disk_usage()
        elif "设置助手" in choice or choice == "4":
            self._environment_setup_helper()

    def _comprehensive_environment_check(self):
        """全面环境诊断"""
        issues = self._check_environment_comprehensive()

        if not issues:
            print("\n🎉 环境检查完成 - 所有检查通过！")
        else:
            print(f"\n⚠️  发现 {len(issues)} 个环境问题")
            print("\n💡 解决建议:")

            if 'python_version' in issues:
                print("   • Python版本: 请升级到3.10+")
            if 'virtual_env' in issues:
                print("   • 虚拟环境: 运行 python smart_train.py --setup 创建环境")
            if 'dependencies' in issues:
                print("   • 依赖包: 运行 pip install -r requirements.txt")
            if 'ollama' in issues:
                print("   • Ollama服务: 访问 https://ollama.com/ 安装")

            print(f"\n🛠️  快速修复: python smart_train.py --setup")

    def _environment_setup_helper(self):
        """环境设置助手"""
        print("\n🛠️  环境设置助手")
        print("=" * 40)

        if questionary:
            choices = [
                "🔧 自动环境准备 (推荐)",
                "📋 手动设置指南",
                "🔍 问题诊断",
                "🔄 重置环境"
            ]

            choice = questionary.select(
                "选择操作:",
                choices=choices
            ).ask()

            if not choice:
                return
        else:
            print("1) 🔧 自动环境准备 (推荐)")
            print("2) 📋 手动设置指南")
            print("3) 🔍 问题诊断")
            print("4) 🔄 重置环境")
            choice = input("\n选择操作 (1-4): ").strip()

        if "自动环境准备" in choice or choice == "1":
            # 自动环境准备
            issues = self._check_environment_comprehensive()
            if not issues:
                print("\n✅ 环境已经准备好了！")
            else:
                if ask_confirm("检测到环境问题，是否自动修复?"):
                    self._auto_setup_environment(issues)

        elif "手动设置指南" in choice or choice == "2":
            # 手动设置指南
            self._show_manual_setup_guide()

        elif "问题诊断" in choice or choice == "3":
            # 问题诊断
            self._diagnose_environment_issues()

        elif "重置环境" in choice or choice == "4":
            # 重置环境
            self._reset_environment()

    def _show_manual_setup_guide(self):
        """显示手动设置指南"""
        print("\n📋 手动环境设置指南")
        print("=" * 40)

        print("\n1️⃣ 创建虚拟环境:")
        print("   python3 -m venv .venv")

        print("\n2️⃣ 激活虚拟环境:")
        import platform
        if platform.system() == 'Windows':
            print("   .venv\\Scripts\\activate")
        else:
            print("   source .venv/bin/activate")

        print("\n3️⃣ 安装依赖:")
        print("   pip install -U pip")
        print("   pip install -r requirements.txt")

        print("\n4️⃣ 验证安装:")
        print("   python smart_train.py --env-check")

        print("\n5️⃣ 安装Ollama (可选):")
        print("   访问 https://ollama.com/ 下载安装")

    def _diagnose_environment_issues(self):
        """诊断环境问题"""
        print("\n🔍 环境问题诊断")
        print("=" * 40)

        issues = self._check_environment_comprehensive()

        if not issues:
            print("\n✅ 没有发现问题！环境配置良好。")
            return

        print(f"\n🔧 诊断结果和解决方案:")

        for issue in issues:
            if issue == 'python_version':
                print(f"\n❌ Python版本问题:")
                print(f"   当前版本过低，需要Python 3.10+")
                self._show_python_upgrade_guide()

            elif issue == 'virtual_env':
                print(f"\n❌ 虚拟环境问题:")
                print(f"   未检测到虚拟环境")
                print(f"   解决方案: python3 -m venv .venv")

            elif issue == 'dependencies':
                print(f"\n❌ 依赖包问题:")
                print(f"   训练依赖未完整安装")
                print(f"   解决方案: pip install -r requirements.txt")

            elif issue == 'ollama':
                print(f"\n⚠️  Ollama服务问题:")
                print(f"   Ollama未安装或不可用")
                print(f"   解决方案: 访问 https://ollama.com/ 安装")
                print(f"   注意: Ollama不是训练必需的，只在导入模型时需要")

    def _analyze_training_performance(self, log_history: list, current_epoch: float) -> dict:
        """智能分析训练效果并给出建议"""
        if not log_history:
            return {"status": "no_data", "message": "无法获取训练历史数据"}

        # 提取关键指标
        latest_log = log_history[-1] if log_history else {}

        # 获取loss和accuracy
        train_loss = latest_log.get('train_loss', latest_log.get('loss', None))
        token_accuracy = latest_log.get('mean_token_accuracy', 0)

        # 改进的loss趋势分析
        loss_trend = "unknown"
        loss_improvement = 0

        if len(log_history) >= 2:
            # 收集所有有效的loss值
            all_losses = []
            for entry in log_history:
                loss = entry.get('train_loss', entry.get('loss'))
                if loss is not None:
                    all_losses.append(loss)

            if len(all_losses) >= 2:
                # 计算整体趋势
                first_loss = all_losses[0] if len(all_losses) > 2 else all_losses[0]
                last_loss = all_losses[-1]
                loss_improvement = first_loss - last_loss

                # 分析最近的趋势（最近3-5个记录点）
                recent_count = min(5, len(all_losses))
                recent_losses = all_losses[-recent_count:]

                if len(recent_losses) >= 2:
                    # 计算最近的平均斜率
                    improving_count = 0
                    worsening_count = 0

                    for i in range(1, len(recent_losses)):
                        if recent_losses[i] < recent_losses[i-1]:
                            improving_count += 1
                        elif recent_losses[i] > recent_losses[i-1]:
                            worsening_count += 1

                    # 基于趋势计数判断总体趋势
                    if improving_count > worsening_count:
                        loss_trend = "improving"
                    elif worsening_count > improving_count:
                        loss_trend = "worsening"
                    else:
                        loss_trend = "stable"

        # 效果评级
        performance_level = "unknown"
        recommendation = ""
        emoji = ""

        if train_loss is not None:
            if train_loss < 0.5:
                performance_level = "excellent"
                emoji = "🎉"
                recommendation = "模型表现优秀！可以停止训练或微调1-2个epochs"
            elif train_loss < 1.0:
                performance_level = "good"
                emoji = "✅"
                recommendation = "模型表现良好，可以停止训练或继续1-3个epochs进一步优化"
            elif train_loss < 2.0:
                performance_level = "fair"
                emoji = "🔄"
                recommendation = "模型还在学习中，建议继续训练2-4个epochs"
            elif train_loss < 3.0:
                performance_level = "poor"
                emoji = "⚠️"
                recommendation = "模型学习效果一般，强烈建议继续训练3-6个epochs"
            else:
                performance_level = "very_poor"
                emoji = "❌"
                recommendation = "模型学习效果不佳，检查数据质量或调整学习率后继续训练"

        # Token准确率评估
        accuracy_status = ""
        if token_accuracy > 0:
            if token_accuracy > 0.7:
                accuracy_status = "准确率优秀(>70%)"
            elif token_accuracy > 0.6:
                accuracy_status = "准确率良好(60-70%)"
            elif token_accuracy > 0.5:
                accuracy_status = "准确率一般(50-60%)"
            else:
                accuracy_status = "准确率较低(<50%)"

        return {
            "status": "analyzed",
            "train_loss": train_loss,
            "token_accuracy": token_accuracy,
            "accuracy_status": accuracy_status,
            "loss_trend": loss_trend,
            "loss_improvement": loss_improvement,
            "performance_level": performance_level,
            "emoji": emoji,
            "recommendation": recommendation,
            "current_epoch": current_epoch
        }

    def _show_training_analysis(self, analysis: dict):
        """显示训练分析结果"""
        if analysis["status"] != "analyzed":
            return

        # 🎯 核心指标面板 - 突出显示最重要的数据
        print(f"\n" + "🎯" + " 训练核心指标 ".center(48, "="))

        # 创建紧凑的状态面板
        train_loss = analysis.get("train_loss")
        token_accuracy = analysis.get("token_accuracy", 0)
        loss_improvement = analysis.get("loss_improvement", 0)
        performance_level = analysis.get("performance_level", "unknown")
        emoji = analysis.get("emoji", "📊")

        # 核心指标一览表格
        if train_loss is not None:
            # 确定Loss状态颜色
            if train_loss < 0.5:
                loss_status = "🟢 优秀"
            elif train_loss < 1.0:
                loss_status = "🟡 良好"
            elif train_loss < 2.0:
                loss_status = "🟠 一般"
            else:
                loss_status = "🔴 较差"

            print(f"📈 当前Loss: {train_loss:.4f} ({loss_status})")

        if token_accuracy > 0:
            # 确定准确率状态
            if token_accuracy > 0.7:
                acc_status = "🟢 优秀"
            elif token_accuracy > 0.6:
                acc_status = "🟡 良好"
            elif token_accuracy > 0.5:
                acc_status = "🟠 一般"
            else:
                acc_status = "🔴 较差"

            print(f"🎯 准确率: {token_accuracy:.1%} ({acc_status})")

        # 改进情况 - 用更直观的表示
        if loss_improvement > 0:
            improvement_display = f"📉 已改进: -{loss_improvement:.4f}"
            if loss_improvement > 2.0:
                improvement_display += " (显著提升 🎉)"
            elif loss_improvement > 1.0:
                improvement_display += " (良好提升 ✅)"
            else:
                improvement_display += " (稳步提升)"
        elif loss_improvement < 0:
            improvement_display = f"📈 Loss上升: +{abs(loss_improvement):.4f} ⚠️"
        else:
            improvement_display = "➡️ Loss无明显变化"

        print(f"{improvement_display}")

        # 趋势指示器
        loss_trend = analysis.get("loss_trend", "unknown")
        if loss_trend == "improving":
            trend_display = "📉 趋势: 持续下降 ✅"
        elif loss_trend == "worsening":
            trend_display = "📈 趋势: 最近上升 ⚠️"
        elif loss_trend == "stable":
            trend_display = "➡️ 趋势: 趋于稳定"
        else:
            trend_display = "❓ 趋势: 数据不足"

        print(f"{trend_display}")

        # 🎯 快速决策面板
        print(f"\n" + "💡" + " 快速决策 ".center(48, "="))
        print(f"{emoji} 训练效果: {performance_level}")
        print(f"📋 建议: {analysis.get('recommendation', '继续观察')}")

        # 🎯 参考指南（简化版）
        print(f"\n" + "📏" + " 指标参考 ".center(48, "="))
        print(f"Loss: <0.5优秀 <1.0良好 <2.0一般 | 准确率: >70%优秀 >60%良好")

    def show_training_status_quick(self, analysis: dict):
        """超级简洁的训练状态一览（用户最想要的信息）"""
        if analysis.get("status") != "analyzed":
            return

        train_loss = analysis.get("train_loss")
        token_accuracy = analysis.get("token_accuracy", 0)
        loss_improvement = analysis.get("loss_improvement", 0)
        performance_level = analysis.get("performance_level", "unknown")

        # 🎯 一行显示最关键信息
        print(f"\n" + "⚡" + " 训练状态速览 ".center(48, "="))

        # 状态指示器
        if train_loss is not None:
            if train_loss < 0.5:
                status_emoji = "🎉"
                status_text = "优秀"
            elif train_loss < 1.0:
                status_emoji = "✅"
                status_text = "良好"
            elif train_loss < 2.0:
                status_emoji = "📈"
                status_text = "学习中"
            else:
                status_emoji = "⚠️"
                status_text = "需改进"

            print(f"{status_emoji} Loss: {train_loss:.4f} ({status_text})", end="")

        if token_accuracy > 0:
            print(f" | 🎯 准确率: {token_accuracy:.1%}", end="")

        if loss_improvement > 0:
            print(f" | 📉 已改进: {loss_improvement:.3f}")
        else:
            print()

        # 快速决策
        if performance_level == "excellent":
            print("💡 可停止训练或微调1轮稳定")
        elif performance_level == "good":
            print("💡 效果良好，建议继续1-2轮")
        elif performance_level in ["fair", "poor"]:
            print("💡 还在学习，建议继续2-4轮")
        else:
            print("💡 建议继续训练")

        print("=" * 48)

    def _show_continue_training_recommendation(self, analysis: dict, current_epoch: float, original_total_epochs: float):
        """显示继续训练的智能建议"""
        print(f"\n" + "🚀" + " 继续训练决策 ".center(48, "="))

        # 进度信息
        print(f"📊 进度: {current_epoch:.1f}/{original_total_epochs} epochs 已完成")

        if analysis["status"] != "analyzed":
            print("💡 建议: 继续训练 1-2 epochs")
            return

        train_loss = analysis.get("train_loss")
        token_accuracy = analysis.get("token_accuracy", 0)
        loss_trend = analysis.get("loss_trend", "unknown")
        loss_improvement = analysis.get("loss_improvement", 0)
        performance_level = analysis.get("performance_level", "unknown")

        # 🎯 一目了然的决策建议
        print(f"\n" + "🎯 决策建议".center(32, "-"))

        if performance_level == "excellent":
            print("🏆 状态: 训练效果优秀")
            if loss_improvement > 1.0:
                print("✅ 建议: 可以停止，或再训练 0.5-1 epoch 稳定效果")
            else:
                print("✅ 建议: 建议停止训练，效果已达标")

        elif performance_level == "good":
            print("✅ 状态: 训练效果良好")
            if loss_trend == "improving":
                print("📈 建议: 继续训练 1-2 epochs，还有改进空间")
            else:
                print("⏸️ 建议: 可以停止，或继续 1 epoch")

        elif performance_level in ["fair", "poor"]:
            print("📈 状态: 还在学习中")
            if loss_trend == "improving":
                if loss_improvement > 1.0:
                    print("🚀 建议: 强烈建议继续 3-5 epochs，进展良好")
                else:
                    print("📈 建议: 继续训练 2-3 epochs")
            elif loss_trend == "stable":
                print("⚠️ 建议: 尝试 2-3 epochs 或调整学习率")
            else:
                print("🛑 建议: 可能过拟合，谨慎继续或停止")

        elif performance_level == "very_poor":
            print("🔴 状态: 训练效果较差")
            if loss_improvement > 0.5:
                print("🔄 建议: 继续训练 4-6 epochs")
            else:
                print("🔧 建议: 检查数据质量或调整参数")

        # 关键指标提醒
        print(f"\n" + "📋 关键提醒".center(32, "-"))
        if train_loss and train_loss < 0.6:
            print("🟢 Loss已达到良好水平")
        if token_accuracy > 0.75:
            print("🟢 准确率表现优秀")
        if loss_improvement > 2.0:
            print("🎉 训练改进显著")
        elif loss_improvement < 0:
            print("⚠️ Loss出现上升，需要关注")

        print("=" * 48)

    def _reset_environment(self):
        """重置环境"""
        print("\n🔄 环境重置")
        print("=" * 40)

        print("⚠️  这将删除现有的虚拟环境并重新创建")

        if ask_confirm("确认要重置环境吗?", default=False):
            import shutil

            # 删除现有虚拟环境
            if Path('.venv').exists():
                print("🗑️  删除现有虚拟环境...")
                shutil.rmtree('.venv')
                print("   ✅ 删除完成")

            # 重新创建环境
            print("🔧 重新创建环境...")
            if self._create_virtual_environment():
                print("   ✅ 虚拟环境创建成功")

                if self._install_dependencies():
                    print("   ✅ 依赖安装完成")
                    print("\n🎉 环境重置完成！")
                else:
                    print("   ❌ 依赖安装失败")
            else:
                print("   ❌ 虚拟环境创建失败")
        else:
            print("👋 重置已取消")

    def estimate_training_time(self, epochs: float, data_size: int = 300) -> str:
        """估算训练时间"""
        base_time_per_epoch = 2.5  # 分钟
        time_factor = max(1.0, data_size / 300)  # 数据量调整系数
        estimated_minutes = epochs * base_time_per_epoch * time_factor

        if estimated_minutes < 60:
            return f"约 {int(estimated_minutes)} 分钟"
        else:
            hours = int(estimated_minutes // 60)
            minutes = int(estimated_minutes % 60)
            return f"约 {hours} 小时 {minutes} 分钟"

    def show_training_info(self, character: str, model_name: str, epochs: float, ollama_name: str, train_count: int, val_count: int, training_analysis: dict = None):
        """显示训练信息概览"""
        print(f"\n" + "🎯" + f" {character} 训练任务 ".center(48, "="))

        # 🎯 核心配置一览
        print(f"🤖 模型: {model_name.split('/')[-1]}")  # 只显示模型名，不显示完整路径
        print(f"🔄 轮数: {epochs} epochs | 📊 数据: {train_count}训练 + {val_count}验证")
        print(f"⏰ 预计: {self.estimate_training_time(epochs, train_count)} | 📦 输出: {ollama_name or f'{character}-lora'}")

        # 显示当前训练状态（如果是继续训练）
        if training_analysis and training_analysis.get("status") == "analyzed":
            current_loss = training_analysis.get("train_loss")
            token_accuracy = training_analysis.get("token_accuracy", 0)

            print(f"\n" + "📊" + " 当前状态 ".center(32, "-"))
            if current_loss is not None:
                if current_loss < 0.5:
                    status_color = "🟢"
                elif current_loss < 1.0:
                    status_color = "🟡"
                else:
                    status_color = "🟠"
                print(f"{status_color} Loss: {current_loss:.4f} | 🎯 准确率: {token_accuracy:.1%}")

        print(f"\n" + "🚀" + " 执行流程 ".center(32, "-"))
        steps = [
            "✅ 环境检查", "✅ 数据验证", "⏳ LoRA训练", "⏳ 模型合并"
        ]
        if ollama_name:
            steps.append("⏳ 导入Ollama")

        print(" → ".join(steps))
        print("=" * 48)

    def start_training(self, character: str, background: bool = False, export_ollama: bool = False, ollama_name: str = None):
        """启动训练"""
        self._ensure_config_loaded()
        print(f"\n🚀 启动 {character} 的LoRA训练...")

        # 获取角色配置
        char_config = self.config.get('characters', {}).get(character)
        if not char_config:
            print(f"❌ 未找到角色配置: {character}")
            return

        # 获取数据文件路径
        train_path, val_path = self.auto_match_files(character)
        if not train_path:
            print(f"❌ 未找到训练数据文件")
            return

        # 获取训练参数
        training_params = char_config.get('training_params', {})

        # 检查是否已有训练结果并处理用户选择
        choice = self.handle_existing_training_choice(character)
        if choice == "cancel":
            return

        resume_from_checkpoint = None
        remaining_epochs = None
        current_epoch_for_resume = None
        total_epochs_target = None
        if choice == "resume":
            # 断点续训模式
            lora_dir = Path(f"out/lora_{character}")
            checkpoint_files = list(lora_dir.glob('checkpoint-*'))
            if checkpoint_files:
                # 找到最新的checkpoint（优先按epoch，其次按修改时间）
                latest_checkpoint = None
                latest_epoch = -1
                checkpoint_info = []
                
                # 收集所有checkpoint的信息
                for cp_dir in checkpoint_files:
                    trainer_state_file = cp_dir / "trainer_state.json"
                    if trainer_state_file.exists():
                        try:
                            import json
                            with open(trainer_state_file, 'r', encoding='utf-8') as f:
                                trainer_state = json.load(f)
                                epoch = trainer_state.get('epoch', 0)
                                checkpoint_info.append({
                                    'dir': cp_dir,
                                    'epoch': epoch,
                                    'step': trainer_state.get('global_step', 0),
                                    'mtime': cp_dir.stat().st_mtime
                                })
                        except Exception:
                            # 如果无法读取，记录但标记epoch为-1
                            checkpoint_info.append({
                                'dir': cp_dir,
                                'epoch': -1,
                                'step': 0,
                                'mtime': cp_dir.stat().st_mtime
                            })
                
                if checkpoint_info:
                    # 优先选择epoch最大的checkpoint
                    valid_checkpoints = [cp for cp in checkpoint_info if cp['epoch'] >= 0]
                    if valid_checkpoints:
                        latest_checkpoint_info = max(valid_checkpoints, key=lambda x: (x['epoch'], x['mtime']))
                        latest_checkpoint = latest_checkpoint_info['dir']
                        latest_epoch = latest_checkpoint_info['epoch']
                    else:
                        # 如果所有checkpoint都无法读取epoch，使用修改时间
                        latest_checkpoint_info = max(checkpoint_info, key=lambda x: x['mtime'])
                        latest_checkpoint = latest_checkpoint_info['dir']
                
                # 如果还是没有找到，使用修改时间
                if latest_checkpoint is None:
                    latest_checkpoint = max(checkpoint_files, key=lambda x: x.stat().st_mtime)
                
                # 使用绝对路径，确保跨平台兼容
                resume_from_checkpoint = str(latest_checkpoint.resolve())
                
                # 读取checkpoint的训练状态
                try:
                    import json
                    trainer_state_file = Path(latest_checkpoint) / "trainer_state.json"
                    if trainer_state_file.exists():
                        with open(trainer_state_file, 'r', encoding='utf-8') as f:
                            trainer_state = json.load(f)
                            current_epoch = trainer_state.get('epoch', 0)
                            global_step = trainer_state.get('global_step', 0)
                            log_history = trainer_state.get('log_history', [])
                            last_loss = log_history[-1].get('loss', 'N/A') if log_history else 'N/A'
                            current_epoch_for_resume = float(current_epoch) if current_epoch is not None else 0.0

                            # 智能训练效果分析
                            training_analysis = self._analyze_training_performance(log_history, current_epoch)

                            total_epochs = training_params.get('epochs', 3.0)
                            remaining_epochs = max(0.1, total_epochs - current_epoch)

                            print(f"📍 将从检查点继续训练: {latest_checkpoint.name}")
                            print(f"   当前epoch: {current_epoch:.2f} | 训练步数: {global_step}")

                            # 🎯 首先显示简洁的状态概览（用户最想要的信息）
                            self.show_training_status_quick(training_analysis)

                            # 智能继续训练建议（基于训练效果而不是epochs数）
                            self._show_continue_training_recommendation(training_analysis, current_epoch, total_epochs)

                            # 详细分析（可选展开查看）
                            if ask_confirm("\n是否显示详细训练分析?", default=False):
                                self._show_training_analysis(training_analysis)

                            try:
                                extra = ask_text("请输入要额外继续训练的 epochs（输入 0 取消继续训练）", default="1.0")
                                extra_epochs = float(extra)
                                if extra_epochs <= 0:
                                    print("👋 已取消继续训练")
                                    return
                                # 关键：transformers/trl 的 resume 语义是"训练到总 epochs"，不是"追加 epochs"
                                # 所以这里需要把 --num_train_epochs 设置为 current_epoch + extra_epochs
                                total_epochs_target = max(0.1, float(current_epoch_for_resume or 0.0) + float(extra_epochs))
                                print(f"📊 将额外继续训练 {extra_epochs:.2f} epochs（目标总epochs: {total_epochs_target:.2f}）")
                            except Exception:
                                # 输入异常时，保持原逻辑（至少继续一点点）
                                pass
                            
                            # 显示所有可用checkpoint供参考
                            if len(checkpoint_info) > 1:
                                print(f"\n📋 所有可用checkpoint:")
                                sorted_checkpoints = sorted([cp for cp in checkpoint_info if cp['epoch'] >= 0], 
                                                          key=lambda x: x['epoch'], reverse=True)
                                for cp in sorted_checkpoints[:5]:  # 只显示前5个
                                    marker = " ← 将使用" if cp['dir'] == latest_checkpoint else ""
                                    print(f"   {cp['dir'].name}: epoch={cp['epoch']:.2f}, step={cp['step']}{marker}")
                except Exception as e:
                    print(f"⚠️  无法读取checkpoint状态: {e}")
                    print(f"📍 将从检查点继续训练: {latest_checkpoint.name}")

        # 构建训练命令
        cmd = [
            sys.executable, "train_lora.py",
            "--train_jsonl", train_path,
            "--output_dir", f"out/lora_{character}"
        ]

        # 选择基础模型：来自 character_configs.yaml 的 training_params.base_model
        # （注意：train_lora.py 的默认值是 Qwen/Qwen2.5-0.5B-Instruct，但如果你在 YAML 里配置了 base_model，
        # 这里必须显式传入，否则你修改配置不会生效）
        base_model = training_params.get("base_model")
        if base_model:
            cmd.extend(["--model_name_or_path", str(base_model)])
            print(f"🤖 Base model: {base_model}")

        # 添加验证数据
        if val_path:
            cmd.extend(["--val_jsonl", val_path])

        # 添加训练参数
        # 重要：如果继续训练，使用剩余epochs数，而不是总epochs数
        if resume_from_checkpoint:
            if total_epochs_target is not None:
                cmd.extend(["--num_train_epochs", str(total_epochs_target)])
                print(f"📊 继续训练：目标总epochs {total_epochs_target:.2f}")
            elif remaining_epochs:
                # fallback：如果没拿到 current_epoch，就用“剩余”作为最低限度的继续训练
                cmd.extend(["--num_train_epochs", str(remaining_epochs)])
                print(f"📊 继续训练剩余 {remaining_epochs:.2f} epochs")
        elif 'epochs' in training_params:
            cmd.extend(["--num_train_epochs", str(training_params['epochs'])])
        if 'learning_rate' in training_params:
            cmd.extend(["--learning_rate", str(training_params['learning_rate'])])
        if 'lora_r' in training_params:
            cmd.extend(["--lora_r", str(training_params['lora_r'])])
        if 'lora_alpha' in training_params:
            cmd.extend(["--lora_alpha", str(training_params['lora_alpha'])])
        if 'lora_dropout' in training_params:
            cmd.extend(["--lora_dropout", str(training_params['lora_dropout'])])

        use_qlora = training_params.get("use_qlora")
        if use_qlora:
            cmd.append("--use_qlora")
            print("🧮 训练模式: QLoRA (4bit 量化)")
        else:
            print("🧮 训练模式: 标准 LoRA")

        # 断点续训参数
        if resume_from_checkpoint:
            cmd.extend(["--resume_from_checkpoint", resume_from_checkpoint])

        # 默认参数
        cmd.extend([
            "--merge_and_save",  # 自动合并并保存
            "--merged_dir", f"out/merged_{character}"
        ])

        # 统计训练数据样本数量
        train_count = self.count_samples(Path(train_path))
        val_count = self.count_samples(Path(val_path)) if val_path else 0

        # 获取训练轮数用于显示
        epochs = training_params.get('epochs', 3.0)
        if resume_from_checkpoint and total_epochs_target is not None:
            epochs = total_epochs_target
        elif resume_from_checkpoint and remaining_epochs:
            epochs = remaining_epochs

        # 获取训练分析信息（如果是继续训练）
        current_training_analysis = None
        if resume_from_checkpoint:
            # 如果是继续训练，尝试获取当前训练状态进行显示
            lora_dir = Path(f"out/lora_{character}")
            if lora_dir.exists():
                try:
                    # 查找最新checkpoint的训练状态
                    checkpoint_files = list(lora_dir.glob('checkpoint-*'))
                    if checkpoint_files:
                        latest_checkpoint = max(checkpoint_files, key=lambda x: x.stat().st_mtime)
                        trainer_state_file = latest_checkpoint / "trainer_state.json"
                        if trainer_state_file.exists():
                            import json
                            with open(trainer_state_file, 'r', encoding='utf-8') as f:
                                trainer_state = json.load(f)
                                log_history = trainer_state.get('log_history', [])
                                current_epoch = trainer_state.get('epoch', 0)
                                current_training_analysis = self._analyze_training_performance(log_history, current_epoch)
                except Exception:
                    pass

        # 显示训练信息概览
        self.show_training_info(
            character=character,
            model_name=base_model or "Qwen/Qwen2.5-0.5B-Instruct",
            epochs=epochs,
            ollama_name=ollama_name,
            train_count=train_count,
            val_count=val_count,
            training_analysis=current_training_analysis
        )

        print(f"📝 执行命令: {' '.join(cmd)}")

        if background:
            print("🔄 后台训练模式...")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # 实时显示输出
            for line in process.stdout:
                print(line.rstrip())

            process.wait()

            if process.returncode == 0:
                print(f"🎉 {character} 训练完成!")
                print(f"   LoRA模型: out/lora_{character}")
                print(f"   合并模型: out/merged_{character}")
                return_code = process.returncode
            else:
                print(f"❌ {character} 训练失败 (退出码: {process.returncode})")
                return_code = process.returncode
        else:
            # 直接执行，用户可以看到实时输出
            result = subprocess.run(cmd)
            if result.returncode == 0:
                print(f"🎉 {character} 训练完成!")
                print(f"   LoRA模型: out/lora_{character}")
                print(f"   合并模型: out/merged_{character}")
            else:
                print(f"❌ {character} 训练失败")
            return_code = result.returncode

        # 训练完成后的友好提示和Ollama导入处理
        if return_code == 0:
            if export_ollama:
                self._export_to_ollama(character, ollama_name)
            else:
                self._show_post_training_options(character, ollama_name)

    def _show_post_training_options(self, character: str, ollama_name: str = None):
        """训练完成后显示后续选项"""
        print("\n" + "=" * 60)
        print("🎉 训练完成！下一步操作")
        print("=" * 60)
        print(f"✅ 模型已训练完成：{character}")
        print(f"📁 文件位置：out/merged_{character}/")
        print()
        print("⚠️  注意：模型目前还没有导入到Ollama，无法直接使用")
        print()

        if questionary:
            # 使用箭头选择
            choices = [
                "🚀 导入到Ollama（推荐）- 可以立即使用",
                "📦 稍后导入 - 返回主菜单",
                "🏠 返回主菜单 - 继续其他操作",
                "👋 退出系统"
            ]

            choice = questionary.select(
                "请选择下一步操作:",
                choices=choices
            ).ask()

            if not choice:
                return

            if "导入到Ollama" in choice:
                # 询问Ollama模型名称
                if not ollama_name:
                    default_name = f"{character}-lora"
                    ollama_name = ask_text("请输入Ollama模型名称", default_name)

                success = self._export_to_ollama(character, ollama_name)
                if success:
                    print(f"\n🎉 导入成功！现在可以使用：")
                    print(f"   ollama run {ollama_name}")
                    print()
                    input("按回车键返回主菜单...")

            elif "稍后导入" in choice:
                print("\n💡 提示：稍后可通过主菜单 -> 3)模型部署 -> 1)导入模型到Ollama 来导入")
                input("按回车键返回主菜单...")

            elif "返回主菜单" in choice:
                print("\n🏠 返回主菜单...")

            elif "退出" in choice:
                print("\n👋 感谢使用！")
                sys.exit(0)
        else:
            # 降级到传统数字输入
            print("📋 后续选项：")
            print("1) 🚀 导入到Ollama（推荐）- 可以立即使用 ollama run 命令")
            print("2) 📦 稍后导入 - 返回主菜单，通过 4)Ollama模型管理 导入")
            print("3) 🏠 返回主菜单 - 继续其他操作")
            print("4) 👋 退出系统")
            print()

            while True:
                try:
                    choice = input("请选择 (1-4): ").strip()

                    if choice == "1":
                        # 询问Ollama模型名称
                        if not ollama_name:
                            default_name = f"{character}-lora"
                            ollama_name = ask_text("请输入Ollama模型名称", default_name)

                        success = self._export_to_ollama(character, ollama_name)
                        if success:
                            print(f"\n🎉 导入成功！现在可以使用：")
                            print(f"   ollama run {ollama_name}")
                            print()
                            input("按回车键返回主菜单...")
                        break

                    elif choice == "2":
                        print("\n💡 提示：稍后可通过主菜单 -> 4)Ollama模型管理 -> 2)导入训练好的模型 来导入")
                        input("按回车键返回主菜单...")
                        break

                    elif choice == "3":
                        print("\n🏠 返回主菜单...")
                        break

                    elif choice == "4":
                        print("\n👋 感谢使用！")
                        sys.exit(0)

                    else:
                        print("❌ 无效选择，请输入1-4")

                except (KeyboardInterrupt, EOFError):
                    print("\n\n🏠 返回主菜单...")
                    break

    def _export_to_ollama(self, character: str, ollama_name: str = None):
        """导出到Ollama"""
        if not ollama_name:
            ollama_name = f"{character}-lora"

        print(f"\n🚀 导出到Ollama: {ollama_name}")

        # 覆盖同名模型：先检测是否存在，存在则删除后重建，避免"看似导入成功但实际还是旧模型"
        try:
            show = subprocess.run(["ollama", "show", ollama_name], capture_output=True, text=True)
            if show.returncode == 0:
                if not ask_confirm(f"⚠️ 已存在模型 {ollama_name}，是否覆盖?"):
                    print("👋 已取消导入")
                    return False
                rm = subprocess.run(["ollama", "rm", ollama_name], capture_output=True, text=True)
                if rm.returncode != 0:
                    msg = (rm.stderr or rm.stdout or "").strip()
                    print(f"❌ 删除旧模型失败: {msg}")
                    return False
        except Exception as e:
            print(f"⚠️ 无法检测/删除同名模型（将继续尝试导入）: {e}")

        # 使用绝对路径并验证目录存在
        merged_dir = Path(f"out/merged_{character}").resolve()
        if not merged_dir.exists():
            print(f"❌ 合并模型不存在: {merged_dir}")
            print("   请确保训练时使用了 --merge_and_save 参数")
            return False

        # 重要说明：
        # Ollama 的 Modelfile `FROM` 需要是 Ollama 模型名或本地 GGUF 文件路径。
        # HuggingFace 合并目录（config.json + safetensors）不能可靠地直接作为 `FROM <dir>` 使用。
        # 这会导致“看似导入成功，但实际运行的不是训练后的权重”，出现你看到的“刷题/不搭边”输出。
        # 选择/生成 GGUF
        # 关键：如果 GGUF 比 merged 权重更旧，则必须重新生成，否则 Ollama 实际跑的是旧模型（表现为“怎么训都不变/答得很怪”）
        gguf_out = (merged_dir / f"{character}.gguf").resolve()
        weight_file = None
        for cand in ["model.safetensors", "pytorch_model.bin"]:
            p = merged_dir / cand
            if p.exists():
                weight_file = p
                break

        def _needs_rebuild_gguf() -> bool:
            if not gguf_out.exists():
                return True
            try:
                if gguf_out.stat().st_size == 0:
                    return True
                if weight_file and weight_file.exists():
                    return gguf_out.stat().st_mtime < weight_file.stat().st_mtime
            except Exception:
                return True
            return False

        if _needs_rebuild_gguf():
            if gguf_out.exists():
                try:
                    print("⚠️  检测到 GGUF 可能过期/损坏（或模型已重新训练），将重新生成 GGUF...")
                    gguf_out.unlink()
                except Exception:
                    pass
            else:
                print(f"⚠️  未找到 GGUF 文件（{merged_dir}/*.gguf），将尝试自动转换...")

            ok = self._convert_merged_to_gguf(merged_dir=merged_dir, gguf_out=gguf_out, outtype="f16")
            if not ok:
                print("\n❌ 自动转换失败。你也可以手动转换：")
                print(f"   python /path/to/llama.cpp/convert_hf_to_gguf.py \"{merged_dir}\" --outtype f16 --outfile \"{gguf_out}\"")
                return False

        if not gguf_out.exists():
            print("❌ 未找到/未生成 GGUF 文件")
            return False

        gguf_path = gguf_out
        print(f"📦 将使用 GGUF: {gguf_path}")

        # 创建Ollama Modelfile (使用完整角色配置和优化推理参数)
        self._ensure_config_loaded()
        char_config = self.config.get('characters', {}).get(character, {})
        global_settings = (self.config.get("global_settings") or {}) if isinstance(self.config, dict) else {}

        # 简化system_prompt，避免格式化的列表（防止模型输出格式标记）
        raw_system_prompt = char_config.get('system_prompt', f'你是{character}，请保持角色特征进行对话。').strip()
        
        # 简化system prompt：移除格式化的列表，只保留核心角色设定
        # 避免模型学会输出"你的特点："、"外表："等格式标记
        system_prompt = raw_system_prompt
        if "你的特点：" in system_prompt or "- 外表：" in system_prompt:
            # 提取核心角色设定，移除格式化内容
            lines = system_prompt.split('\n')
            simplified_lines = []
            skip_format = False
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                # 跳过格式化的列表
                if line.startswith('- ') or line.startswith('你的特点：') or line.startswith('外表：') or line.startswith('性格：') or line.startswith('互动：'):
                    skip_format = True
                    continue
                if skip_format and not line.startswith('请'):
                    continue
                skip_format = False
                # 保留核心设定
                if '你是' in line or '请' in line:
                    simplified_lines.append(line)
            
            if simplified_lines:
                # 构建简化的system prompt
                system_prompt = ' '.join(simplified_lines)
                # 进一步简化：移除多余的格式
                system_prompt = system_prompt.replace('你的特点：', '').replace('外表：', '').replace('性格：', '').replace('互动：', '')
                system_prompt = ' '.join(system_prompt.split())  # 清理多余空格
            else:
                # 如果简化失败，使用最基本的设定
                system_prompt = f"你是{char_config.get('name', character)}，请按照角色性格进行对话。"

        # 规则：优先用角色配置里的 system_prompt_rules；否则使用默认规则（保持现有行为）
        rules_text = char_config.get("system_prompt_rules") or global_settings.get("system_prompt_rules")
        if not rules_text:
            rules_text = (
                "输出规则：\n"
                "1) 你必须用第一人称，以角色口吻与用户对话。\n"
                "2) 禁止输出：题目、答案、解析、判断题、选择题、A/B/C/D 选项、填空题、材料分析等应试内容。\n"
                "3) 禁止输出：system/user/assistant 等角色标签或提示词格式。\n"
                "4) 回复自然简短，避免重复同一句话。\n"
                "5) 遇到客观问题（如数学、时间、常识）：必须先给出准确答案；不要胡编。\n"
                "   例如：用户问“1+1等于几”，你要回答“2”，然后再用林栀口吻补一句也可以。\n"
            )
        system_prompt = f"{system_prompt}\n\n{str(rules_text).strip()}\n"
        
        # 获取角色的中文名称用于显示
        char_name = char_config.get('name', character)

        print(f"📝 角色配置: {char_name}")
        print(f"📄 System Prompt (原始): {raw_system_prompt[:100]}..." if len(raw_system_prompt) > 100 else f"📄 System Prompt (原始): {raw_system_prompt}")
        print(f"📄 System Prompt (简化): {system_prompt[:100]}..." if len(system_prompt) > 100 else f"📄 System Prompt (简化): {system_prompt}")

        # 优化推理参数，更适合角色扮演
        # 模板：允许在角色文件中覆盖；默认使用 Qwen2 的 <|im_start|>/<|im_end|> 格式
        template = char_config.get("ollama_template") or global_settings.get("ollama_template")
        if not template:
            template = r"""{{- if .System -}}<|im_start|>system
{{ .System }}<|im_end|>
{{- else -}}<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
{{- end -}}
{{- range .Messages }}
{{- if eq .Role "system" }}<|im_start|>system
{{ .Content }}<|im_end|>
{{- else if eq .Role "user" }}<|im_start|>user
{{ .Content }}<|im_end|>
{{- else if eq .Role "assistant" }}<|im_start|>assistant
{{ .Content }}<|im_end|>
{{- end }}
{{- end }}
<|im_start|>assistant
"""

        # 推理参数：角色 inference_params 覆盖全局 inference_defaults，再覆盖代码默认值
        defaults = global_settings.get("inference_defaults") or {}
        infer = {}
        if isinstance(defaults, dict):
            infer.update(defaults)
        if isinstance(char_config.get("inference_params"), dict):
            infer.update(char_config["inference_params"])

        temperature = infer.get("temperature", 0.5)
        top_p = infer.get("top_p", 0.9)
        top_k = infer.get("top_k", 40)
        repeat_penalty = infer.get("repeat_penalty", 1.15)
        num_predict = infer.get("num_predict", 256)
        stop_list = infer.get("stop", ["<|im_end|>"])
        if isinstance(stop_list, str):
            stop_list = [stop_list]

        stop_lines = "\n".join([f'PARAMETER stop "{s}"' for s in stop_list if s])

        # 检查是否已有Modelfile，询问用户是否使用现有的
        permanent_modelfile = gguf_out.parent / "Modelfile"
        use_existing = False

        if permanent_modelfile.exists():
            print(f"\n📋 发现已存在的Modelfile: {permanent_modelfile}")
            try:
                with open(permanent_modelfile, 'r', encoding='utf-8') as f:
                    existing_content = f.read()

                print("📝 现有Modelfile内容预览:")
                preview_lines = existing_content.split('\n')[:10]  # 显示前10行
                for line in preview_lines:
                    if line.strip():
                        print(f"   {line}")
                if len(existing_content.split('\n')) > 10:
                    print("   ...")

                if ask_confirm("🤔 是否使用现有的Modelfile?"):
                    use_existing = True
                    modelfile_content = existing_content
                    print("✅ 将使用现有的Modelfile")
                else:
                    print("🔄 将从配置重新生成Modelfile")
            except Exception as e:
                print(f"⚠️  读取现有Modelfile失败: {e}，将重新生成")

        if not use_existing:
            # 重新生成Modelfile内容
            modelfile_content = f"""FROM {gguf_path}
# 更稳的角色扮演推理参数（减少跑偏与长篇刷题）
PARAMETER temperature {temperature}
PARAMETER top_p {top_p}
PARAMETER top_k {top_k}
PARAMETER repeat_penalty {repeat_penalty}
PARAMETER num_predict {num_predict}
{stop_lines}

TEMPLATE \"\"\"{template}\"\"\"
SYSTEM \"\"\"{system_prompt}\"\"\"
"""

        try:
            # 保存永久Modelfile到模型目录（如果不是使用现有的）
            if not use_existing:
                with open(permanent_modelfile, 'w', encoding='utf-8') as f:
                    f.write(modelfile_content)
                print(f"💾 Modelfile已保存到: {permanent_modelfile}")
            else:
                print(f"📄 使用现有Modelfile: {permanent_modelfile}")

            print(f"📝 可手动编辑此文件来调整推理参数")

            # 使用模型目录中的永久Modelfile进行导入
            cmd = f"ollama create {ollama_name} -f {permanent_modelfile}"
            print(f"执行: {cmd}")

            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                print(f"✅ 成功导入到Ollama: {ollama_name}")
                print(f"🧪 测试命令: ollama run {ollama_name}")
                print(f"🔧 如需调整参数，可编辑: {permanent_modelfile}")
                return True
            else:
                print(f"❌ 导入失败: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ 导出过程出错: {e}")
            return False

    def _show_dataset_scan(self):
        """显示数据集扫描结果"""
        dataset_info = self.scan_datasets()
        print("\n📊 数据集扫描结果:")
        print("=" * 50)
        for char_name, info in dataset_info.items():
            print(f"\n📁 {char_name}/")
            print(f"   训练文件: {len(info['train_files'])}个")
            for tf in info['train_files']:
                print(f"      📄 {tf.name} ({self.count_samples(tf)}样本)")
            print(f"   验证文件: {len(info['val_files'])}个")
            for vf in info['val_files']:
                print(f"      📄 {vf.name} ({self.count_samples(vf)}样本)")

    def _validate_all_datasets(self):
        """验证所有数据集格式"""
        dataset_info = self.scan_datasets()
        print("\n🔍 验证数据集格式...")

        for char_name, info in dataset_info.items():
            print(f"\n📁 {char_name}:")

            for file_list, file_type in [(info['train_files'], '训练'), (info['val_files'], '验证')]:
                for file_path in file_list:
                    valid, msg = self.validate_jsonl(file_path)
                    status = "✅" if valid else "❌"
                    print(f"   {status} {file_type}文件 {file_path.name}: {msg}")

    def _show_dataset_stats(self):
        """显示数据集统计信息"""
        dataset_info = self.scan_datasets()
        print("\n📊 数据集统计:")
        print("=" * 50)

        total_train = 0
        total_val = 0

        for char_name, info in dataset_info.items():
            train_count = sum(self.count_samples(f) for f in info['train_files'])
            val_count = sum(self.count_samples(f) for f in info['val_files'])

            print(f"📁 {char_name}: {train_count}训练样本 + {val_count}验证样本")
            total_train += train_count
            total_val += val_count

        print(f"\n📈 总计: {total_train}训练样本 + {total_val}验证样本")

    def _check_training_environment(self):
        """检查训练环境"""
        print("\n🔍 检查训练环境...")

        try:
            # 检查Python版本
            import sys
            print(f"   🐍 Python: {sys.version}")

            # 检查关键库
            libs = ['torch', 'transformers', 'peft', 'trl', 'datasets']
            for lib in libs:
                try:
                    module = __import__(lib)
                    version = getattr(module, '__version__', 'unknown')
                    print(f"   ✅ {lib}: {version}")
                except ImportError:
                    print(f"   ❌ {lib}: 未安装")

            # 检查设备
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
                print(f"   🖥️  设备: {device}")
            except:
                print(f"   ⚠️  设备: 无法检测")

        except Exception as e:
            print(f"   ❌ 环境检查失败: {e}")

    def first_time_setup(self):
        """首次运行引导设置"""
        print("🚀 LoRA智能训练系统 - 首次运行检测")
        print("=" * 50)

        # 全面环境检测
        issues = self._check_environment_comprehensive()

        if not issues:
            print("\n🎉 环境检查完成 - 所有检查通过！")
            print("现在可以开始使用训练系统了！\n")
            self.show_main_menu()
            return

        # 显示问题和解决方案
        print(f"\n⚠️  发现 {len(issues)} 个环境问题，需要初始化设置")
        print("\n📋 推荐操作流程：")
        if 'python_version' in issues:
            print("1️⃣ 升级Python版本 (必需)")
        if 'virtual_env' in issues:
            print("1️⃣ 创建虚拟环境并安装依赖 (必需)")
        if 'dependencies' in issues:
            print("2️⃣ 安装训练依赖 (必需)")
        if 'ollama' in issues:
            print("3️⃣ 安装Ollama服务 (训练完成后导入模型需要)")

        try:
            # 询问是否自动修复
            if 'python_version' in issues:
                print("\n❌ Python版本过低，请先升级Python再运行")
                self._show_python_upgrade_guide()
                return

            if ask_confirm("是否立即进行环境初始化?"):
                success = self._auto_setup_environment(issues)
                if success:
                    print("\n🎉 环境准备完成！")

                    if ask_confirm("继续进入训练系统?"):
                        self.show_main_menu()
                else:
                    print("\n⚠️  环境准备遇到问题，请查看上方错误信息")
                    print("可以尝试手动解决问题后重新运行")
            else:
                print("\n💡 您可以稍后使用以下命令进行环境准备：")
                print("   python smart_train.py --setup")

        except (KeyboardInterrupt, EOFError):
            print("\n\n👋 设置已取消")

    def _check_environment_comprehensive(self):
        """全面环境检查"""
        print("\n🔍 正在检查运行环境...")

        issues = []

        # 1. 系统平台检测
        import platform
        system = platform.system()
        print(f"   💻 操作系统: {system} {platform.release()}")

        # 2. Python版本检查
        python_status = self._check_python_version()
        if not python_status['compatible']:
            issues.append('python_version')

        # 3. 虚拟环境检测
        venv_status = self._check_virtual_environment()
        if not venv_status['active'] and not venv_status['exists']:
            issues.append('virtual_env')
        elif venv_status['exists'] and not venv_status['active']:
            print(f"   💡 提示: 检测到虚拟环境但未激活，请运行: source .venv/bin/activate")

        # 4. 依赖检查（只有在虚拟环境激活时才检查）
        if venv_status['active'] or not Path('.venv').exists():
            deps_status = self._check_dependencies_simple()
            if deps_status['missing']:
                issues.append('dependencies')
        else:
            print(f"   📚 训练依赖: 需要激活虚拟环境后检查")

        # 5. Ollama服务检测
        ollama_status = self._check_ollama_service()
        if not ollama_status['available']:
            issues.append('ollama')

        return issues

    def _check_python_version(self):
        """检查Python版本"""
        import sys

        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"

        # 要求Python >= 3.10
        compatible = version.major >= 3 and version.minor >= 10

        if compatible:
            print(f"   🐍 Python: {version_str} ✅")
        else:
            print(f"   🐍 Python: {version_str} ❌ (需要 ≥ 3.10)")

        return {
            'compatible': compatible,
            'version': version_str,
            'major': version.major,
            'minor': version.minor
        }

    def _check_virtual_environment(self):
        """检查虚拟环境状态"""
        import sys

        # 检查是否在虚拟环境中
        in_venv = (hasattr(sys, 'real_prefix') or
                   (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))

        venv_exists = Path('.venv').exists()

        if in_venv and venv_exists:
            print(f"   📦 虚拟环境: 已激活 ✅")
        elif venv_exists:
            print(f"   📦 虚拟环境: 存在但未激活 ⚠️")
        elif in_venv:
            print(f"   📦 虚拟环境: 在其他虚拟环境中 ⚠️")
        else:
            print(f"   📦 虚拟环境: 不存在 ❌")

        return {
            'active': in_venv,
            'exists': venv_exists,
            'path': Path('.venv').resolve() if venv_exists else None
        }

    def _check_dependencies_simple(self):
        """简单依赖检查"""
        required_libs = ['torch', 'transformers', 'peft', 'trl', 'datasets']
        missing = []
        installed = []

        for lib in required_libs:
            try:
                module = __import__(lib)
                version = getattr(module, '__version__', 'unknown')
                print(f"   📚 {lib}: {version} ✅")
                installed.append(lib)
            except ImportError:
                print(f"   📚 {lib}: 未安装 ❌")
                missing.append(lib)

        return {
            'missing': missing,
            'installed': installed
        }

    def _check_ollama_service(self):
        """检查Ollama服务状态"""
        try:
            result = subprocess.run(['ollama', '--version'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version = result.stdout.strip().split()[-1] if result.stdout.strip() else "未知版本"
                print(f"   🤖 Ollama服务: {version} ✅")
                return {'available': True, 'version': version}

        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            print(f"   🤖 Ollama服务: 未安装 ⚠️ (训练后导入模型需要)")

        return {'available': False, 'version': None}

    def _show_python_upgrade_guide(self):
        """显示Python升级指南"""
        import platform
        system = platform.system().lower()

        print(f"\n💡 Python升级指南:")
        if 'darwin' in system:  # macOS
            print("   # macOS (推荐使用Homebrew)")
            print("   brew install python@3.11")
            print("   # 或使用pyenv")
            print("   brew install pyenv")
            print("   pyenv install 3.11.5")
            print("   pyenv global 3.11.5")
        elif 'linux' in system:  # Linux
            print("   # Ubuntu/Debian")
            print("   sudo apt update")
            print("   sudo apt install python3.11 python3.11-venv python3.11-pip")
            print("   # CentOS/RHEL")
            print("   sudo yum install python3.11")
        elif 'windows' in system:  # Windows
            print("   # Windows")
            print("   1. 访问 https://www.python.org/downloads/")
            print("   2. 下载Python 3.11+安装包")
            print("   3. 安装时勾选 'Add Python to PATH'")

        print(f"\n然后重新运行: python3.11 smart_train.py")

    def _auto_setup_environment(self, issues):
        """自动环境设置"""
        print(f"\n🔧 开始环境初始化...")

        success = True

        # 1. 创建虚拟环境
        if 'virtual_env' in issues:
            print(f"\n1️⃣ 创建虚拟环境...")
            if self._create_virtual_environment():
                print(f"   ✅ 虚拟环境创建成功: .venv/")
            else:
                print(f"   ❌ 虚拟环境创建失败")
                success = False
                return False

        # 2. 安装依赖
        if 'dependencies' in issues or 'virtual_env' in issues:
            print(f"\n2️⃣ 安装训练依赖...")
            if self._install_dependencies():
                print(f"   ✅ 依赖安装完成")
            else:
                print(f"   ❌ 依赖安装失败")
                success = False

        # 3. 验证环境
        if success:
            print(f"\n3️⃣ 验证环境...")
            issues_after = self._check_environment_comprehensive()
            # 忽略ollama问题，因为不是必需的
            critical_issues = [i for i in issues_after if i != 'ollama']
            if not critical_issues:
                print(f"   ✅ 环境验证通过")
            else:
                print(f"   ⚠️  仍有问题: {', '.join(critical_issues)}")
                success = False

        # 4. Ollama提示
        if 'ollama' in issues:
            print(f"\n💡 关于Ollama服务：")
            print(f"   训练完成后需要Ollama来使用模型")
            print(f"   安装方法: https://ollama.com/")
            print(f"   也可以训练完成后再安装")

        return success

    def _create_virtual_environment(self):
        """创建虚拟环境"""
        try:
            # 使用当前Python创建虚拟环境
            result = subprocess.run([sys.executable, '-m', 'venv', '.venv'],
                                  capture_output=True, text=True, timeout=60)
            return result.returncode == 0
        except Exception as e:
            print(f"   创建虚拟环境时出错: {e}")
            return False

    def _install_dependencies(self):
        """安装依赖"""
        try:
            # 确定python可执行文件路径
            if Path('.venv').exists():
                if sys.platform == 'win32':
                    python_exe = Path('.venv/Scripts/python.exe')
                else:
                    python_exe = Path('.venv/bin/python')
            else:
                python_exe = Path(sys.executable)

            if not python_exe.exists():
                print(f"   ❌ Python可执行文件不存在: {python_exe}")
                return False

            # 升级pip
            print(f"   📦 升级pip工具...")
            result = subprocess.run([str(python_exe), '-m', 'pip', 'install', '-U', 'pip'],
                                  capture_output=True, text=True, timeout=120)

            if result.returncode != 0:
                print(f"   ⚠️  pip升级失败: {result.stderr}")

            # 安装requirements.txt
            if Path('requirements.txt').exists():
                print(f"   📦 安装训练依赖...")
                result = subprocess.run([str(python_exe), '-m', 'pip', 'install', '-r', 'requirements.txt'],
                                      capture_output=True, text=True, timeout=300)

                if result.returncode == 0:
                    return True
                else:
                    print(f"   ❌ 依赖安装失败:")
                    print(f"   {result.stderr}")

                    # 提供解决方案
                    print(f"\n   💡 可能的解决方案:")
                    print(f"   1) 网络问题 - 使用国内镜像:")
                    print(f"      {python_exe} -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt")
                    print(f"   2) 手动安装:")
                    print(f"      {python_exe} -m pip install torch transformers peft trl datasets")
                    return False
            else:
                print(f"   ❌ requirements.txt 文件不存在")
                return False

        except Exception as e:
            print(f"   安装依赖时出错: {e}")
            return False

    def _check_disk_usage(self):
        """检查磁盘使用情况"""
        print("\n💽 磁盘使用情况...")

        dirs_to_check = ['out/', 'datasets/', '.cache/']

        for dir_name in dirs_to_check:
            dir_path = Path(dir_name)
            if dir_path.exists():
                total_size = sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
                if total_size > 1024**3:  # > 1GB
                    size_str = f"{total_size / (1024**3):.1f} GB"
                else:
                    size_str = f"{total_size / (1024**2):.1f} MB"
                print(f"   📁 {dir_name}: {size_str}")
            else:
                print(f"   📁 {dir_name}: 不存在")

    def _show_ollama_models(self):
        """显示Ollama模型列表"""
        print("\n🤖 Ollama模型列表:")
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            if result.returncode == 0:
                print(result.stdout)
            else:
                print("❌ 无法获取Ollama模型列表")
        except Exception as e:
            print(f"❌ 错误: {e}")

    def _import_to_ollama(self):
        """导入模型到Ollama"""
        self._ensure_config_loaded()
        print("\n🚀 导入模型到Ollama")

        # 扫描可用的合并模型
        out_dir = Path("out")
        if not out_dir.exists():
            print("❌ out目录不存在，请先训练模型")
            return

        merged_dirs = list(out_dir.glob("merged_*"))
        if not merged_dirs:
            print("❌ 未找到已训练的模型")
            return

        # 构建模型选择列表
        model_choices = []
        model_info_map = {}

        for dir_path in merged_dirs:
            character = dir_path.name.replace("merged_", "")

            # 尝试从配置文件获取中文名称和描述
            char_config = self.config.get('characters', {}).get(character, {})
            chinese_name = char_config.get('name', character)
            description = char_config.get('description', '未配置')

            # 格式：中文名 (代码) - 描述
            choice_str = f"{chinese_name} ({character}) - {description}"
            model_choices.append(choice_str)
            model_info_map[choice_str] = character

        if questionary:
            # 使用箭头选择
            selected = questionary.select(
                "选择要导入的模型:",
                choices=model_choices
            ).ask()

            if not selected:
                print("\n👋 已取消")
                return

            character = model_info_map[selected]
        else:
            # 降级到数字输入
            print("\n📋 可导入的模型:")
            for i, choice in enumerate(model_choices, 1):
                print(f"   {i}) {choice}")

            try:
                choice_idx = int(input(f"\n请选择模型 (1-{len(model_choices)}): "))
                if 1 <= choice_idx <= len(model_choices):
                    selected = model_choices[choice_idx - 1]
                    character = model_info_map[selected]
                else:
                    print("❌ 无效选择")
                    return
            except (ValueError, IndexError):
                print("❌ 无效选择")
                return

        # 获取中文名称用于确认
        char_config = self.config.get('characters', {}).get(character, {})
        chinese_name = char_config.get('name', character)
        print(f"\n✅ 已选择: {chinese_name} ({character})")

        # 询问Ollama模型名称
        default_name = f"{character}-lora"
        ollama_name = ask_text(f"请输入Ollama模型名称", default=default_name)

        self._export_to_ollama(character, ollama_name)

    def _delete_ollama_model(self):
        """删除Ollama模型"""
        print("\n🗑️ 删除Ollama模型")
        model_name = ask_text("请输入要删除的模型名称", default="")

        if model_name:
            try:
                result = subprocess.run(['ollama', 'rm', model_name], capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✅ 已删除模型: {model_name}")
                else:
                    print(f"❌ 删除失败: {result.stderr}")
            except Exception as e:
                print(f"❌ 错误: {e}")

    def _test_ollama_model(self):
        """测试Ollama模型"""
        print("\n🧪 测试Ollama模型")

        # 显示可用模型
        self._show_ollama_models()

        model_name = ask_text("\n请输入要测试的模型名称", default="")
        if model_name:
            test_prompt = "你好，请介绍一下自己。"
            print(f"\n测试提示: {test_prompt}")
            print("回答:")
            print("-" * 40)

            try:
                result = subprocess.run(['ollama', 'run', model_name],
                                     input=test_prompt, text=True, capture_output=True)
                if result.returncode == 0:
                    print(result.stdout)
                else:
                    print(f"❌ 测试失败: {result.stderr}")
            except Exception as e:
                print(f"❌ 错误: {e}")

    def _confirm_and_train(self, character: str):
        """确认并开始训练"""
        print(f"\n💡 准备训练 '{character}'")

        # 询问是否导出到Ollama
        export_ollama = False
        ollama_name = None

        try:
            if ask_confirm("训练完成后是否导入到Ollama?", default=False):
                export_ollama = True
                default_name = f"{character}-lora"
                ollama_name = ask_text("请输入Ollama模型名称", default=default_name)

            # 直接调用start_training，它会自动检测并处理已有训练结果
            self.start_training(character, export_ollama=export_ollama, ollama_name=ollama_name)

        except (KeyboardInterrupt, EOFError):
            print("\n👋 训练已取消")

    def check_existing_training(self, character: str):
        """检查是否已有训练结果"""
        lora_dir = Path(f"out/lora_{character}")
        merged_dir = Path(f"out/merged_{character}")

        result = {
            'has_lora': lora_dir.exists(),
            'has_merged': merged_dir.exists(),
            'lora_dir': lora_dir,
            'merged_dir': merged_dir
        }

        if result['has_lora'] or result['has_merged']:
            # 获取训练时间信息
            if result['has_lora']:
                try:
                    # 查找最新的checkpoint文件获取训练时间
                    checkpoint_files = list(lora_dir.glob('checkpoint-*'))
                    if checkpoint_files:
                        latest_checkpoint = max(checkpoint_files, key=lambda x: x.stat().st_mtime)
                        result['last_checkpoint'] = latest_checkpoint.name
                        result['train_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(latest_checkpoint.stat().st_mtime))

                    # 读取训练元数据
                    meta_file = lora_dir / "run_meta.json"
                    if meta_file.exists():
                        import json
                        with open(meta_file, 'r', encoding='utf-8') as f:
                            meta = json.load(f)
                            result['training_params'] = meta.get('args', {})
                            result['env_info'] = meta.get('env_plan', {})
                except Exception:
                    pass

            if result['has_merged']:
                try:
                    result['merged_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(merged_dir.stat().st_mtime))
                    # 计算模型大小
                    total_size = sum(f.stat().st_size for f in merged_dir.glob('*') if f.is_file())
                    result['merged_size'] = f"{total_size / (1024**3):.1f} GB"
                except Exception:
                    result['merged_size'] = "未知"

        return result

    def backup_existing_training(self, character: str):
        """备份现有训练结果"""
        import shutil
        timestamp = time.strftime("%Y%m%d_%H%M%S")

        lora_dir = Path(f"out/lora_{character}")
        merged_dir = Path(f"out/merged_{character}")
        backup_base = f"out/backup_{character}_{timestamp}"

        backup_info = {}

        if lora_dir.exists():
            backup_lora = f"{backup_base}_lora"
            shutil.move(str(lora_dir), backup_lora)
            backup_info['lora'] = backup_lora
            print(f"   📦 LoRA模型已备份到: {backup_lora}")

        if merged_dir.exists():
            backup_merged = f"{backup_base}_merged"
            shutil.move(str(merged_dir), backup_merged)
            backup_info['merged'] = backup_merged
            print(f"   📦 合并模型已备份到: {backup_merged}")

        return backup_info

    def show_existing_training_info(self, character: str, existing_info: dict):
        """显示现有训练结果信息"""
        print(f"\n📋 发现 {character} 的现有训练结果:")
        print("=" * 50)

        if existing_info['has_lora']:
            print(f"🔧 LoRA适配器: ✅ 存在")
            if 'train_time' in existing_info:
                print(f"   📅 训练时间: {existing_info['train_time']}")
            if 'last_checkpoint' in existing_info:
                print(f"   📊 最新检查点: {existing_info['last_checkpoint']}")
            if 'training_params' in existing_info:
                params = existing_info['training_params']
                epochs = params.get('num_train_epochs', '未知')
                lr = params.get('learning_rate', '未知')
                print(f"   ⚙️  训练参数: epochs={epochs}, lr={lr}")

        if existing_info['has_merged']:
            print(f"🤖 合并模型: ✅ 存在")
            if 'merged_time' in existing_info:
                print(f"   📅 合并时间: {existing_info['merged_time']}")
            if 'merged_size' in existing_info:
                print(f"   📦 模型大小: {existing_info['merged_size']}")

    def handle_existing_training_choice(self, character: str):
        """处理已有训练结果的用户选择"""
        existing_info = self.check_existing_training(character)

        if not (existing_info['has_lora'] or existing_info['has_merged']):
            return None  # 没有现有结果，正常训练

        # 显示现有结果信息
        self.show_existing_training_info(character, existing_info)

        print(f"\n🤔 检测到已有训练结果，请选择处理方式:")
        print("1) 🔄 重新训练 (覆盖现有结果) - ⚠️  Loss会从初始值重新开始")
        print("2) 📦 备份后重新训练 (保留现有结果) - ⚠️  Loss会从初始值重新开始")
        print("3) ➕ 继续训练 (断点续训，增加更多epochs) - ✅ 推荐！Loss会从之前的值继续")
        print("4) 🚫 取消训练")
        print()
        print("💡 提示：如果loss已经降到0.5以下，建议选择'继续训练'，让loss继续下降")
        print()

        while True:
            try:
                choice = input("请选择 (1-4): ").strip()

                if choice == "1":
                    print("🔄 将覆盖现有训练结果...")
                    return "overwrite"

                elif choice == "2":
                    print("📦 将备份现有结果后重新训练...")
                    backup_info = self.backup_existing_training(character)
                    print("✅ 备份完成，开始重新训练")
                    return "backup_and_retrain"

                elif choice == "3":
                    print("➕ 将从最新检查点继续训练...")
                    if not existing_info['has_lora']:
                        print("❌ 未找到LoRA检查点，无法继续训练")
                        print("   建议选择重新训练")
                        continue
                    return "resume"

                elif choice == "4":
                    print("🚫 训练已取消")
                    return "cancel"

                else:
                    print("❌ 无效选择，请输入1-4")

            except (KeyboardInterrupt, EOFError):
                print("\n🚫 训练已取消")
                return "cancel"

def main():
    parser = argparse.ArgumentParser(description="智能LoRA训练脚本")
    parser.add_argument("character", nargs="?", help="要训练的角色名称")
    parser.add_argument("--character", "-c", dest="character_flag", help="指定要训练的角色")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有可用配置")
    parser.add_argument("--scan", "-s", action="store_true", help="扫描数据集状态")
    parser.add_argument("--background", "-b", action="store_true", help="后台训练模式")
    parser.add_argument("--yes", "-y", action="store_true", help="跳过确认，直接开始训练")
    parser.add_argument("--cache", action="store_true", help="检查模型缓存状态")
    parser.add_argument("--menu", "-m", action="store_true", help="显示交互式菜单")
    parser.add_argument("--ollama", "-o", action="store_true", help="训练后导入到Ollama")
    parser.add_argument("--ollama_name", type=str, help="指定Ollama模型名称")

    # 新增环境管理参数
    parser.add_argument("--setup", action="store_true", help="环境初始化设置")
    parser.add_argument("--env-check", action="store_true", help="全面环境检查")
    parser.add_argument("--auto", action="store_true", help="自动模式，跳过用户确认")

    args = parser.parse_args()

    trainer = SmartTrainer()

    # 首次运行检测：无参数且无虚拟环境时进入引导模式
    if not any(vars(args).values()) and not Path('.venv').exists():
        print("🔍 检测到首次运行...")
        trainer.first_time_setup()
        return

    # 处理新的环境管理参数
    if args.setup:
        print("🔧 环境初始化设置")
        issues = trainer._check_environment_comprehensive()

        if not issues:
            print("\n✅ 环境已经准备好了！")
            if not args.auto:
                if ask_confirm("是否进入主菜单?"):
                    trainer.show_main_menu()
        else:
            if args.auto:
                success = trainer._auto_setup_environment(issues)
                if success:
                    print("\n🎉 环境准备完成！")
                    trainer.show_main_menu()
            else:
                if ask_confirm("检测到环境问题，是否自动修复?"):
                    success = trainer._auto_setup_environment(issues)
                    if success:
                        print("\n🎉 环境准备完成！")
                        if ask_confirm("是否进入主菜单?"):
                            trainer.show_main_menu()
        return

    if args.env_check:
        trainer._comprehensive_environment_check()
        return

    # 处理命令行参数
    if args.menu:
        trainer.show_main_menu()
        return

    if args.list:
        trainer.list_configurations()
        return

    if args.scan:
        dataset_info = trainer.scan_datasets()
        print("\n📊 数据集扫描结果:")
        print("=" * 50)
        for char_name, info in dataset_info.items():
            print(f"\n📁 {char_name}/")
            print(f"   训练文件: {len(info['train_files'])}个")
            for tf in info['train_files']:
                print(f"      📄 {tf.name} ({trainer.count_samples(tf)}样本)")
            print(f"   验证文件: {len(info['val_files'])}个")
            for vf in info['val_files']:
                print(f"      📄 {vf.name} ({trainer.count_samples(vf)}样本)")
        return

    if args.cache:
        trainer.check_model_cache()
        return

    # 选择角色
    character = args.character or args.character_flag
    if character:
        print(f"🎯 指定角色: {character}")
    else:
        character = trainer.interactive_select()

    # 检查前置条件
    if not trainer.check_prerequisites(character):
        print("\n💡 建议:")
        print("   1. 检查数据文件是否存在")
        print("   2. 验证JSONL格式是否正确")
        print("   3. 运行 'python smart_train.py --scan' 查看详细状态")
        sys.exit(1)

    # 确认训练
    if not args.yes:
        print(f"\n💡 即将开始训练 '{character}'")
        try:
            if not ask_confirm("确认开始训练?", default=False):
                print("👋 训练已取消")
                return
        except (KeyboardInterrupt, EOFError):
            print("\n👋 训练已取消")
            return
    else:
        print(f"\n🚀 自动开始训练 '{character}'")

    # 开始训练
    trainer.start_training(character, args.background,
                          export_ollama=args.ollama,
                          ollama_name=args.ollama_name)

if __name__ == "__main__":
    main()
