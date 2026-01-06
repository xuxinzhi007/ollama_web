from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple


@dataclass(frozen=True)
class MemoryInfo:
    backend: str  # "cuda" | "mps" | "cpu" | "unknown"
    total_bytes: Optional[int] = None
    free_bytes: Optional[int] = None
    note: str = ""

    def total_gb(self) -> Optional[float]:
        if self.total_bytes is None:
            return None
        return self.total_bytes / (1024**3)

    def free_gb(self) -> Optional[float]:
        if self.free_bytes is None:
            return None
        return self.free_bytes / (1024**3)


@dataclass(frozen=True)
class EnvPlan:
    device: str  # "cuda" | "mps" | "cpu"
    dtype: str  # "bf16" | "fp16" | "fp32"
    memory: MemoryInfo
    defaults: Dict[str, Any]


def _try_import(name: str):
    try:
        module = __import__(name)
        return module
    except Exception:
        return None


def _cuda_memory_info() -> MemoryInfo:
    torch = _try_import("torch")
    if torch is None or not getattr(torch.cuda, "is_available", lambda: False)():
        return MemoryInfo(backend="cuda", note="torch.cuda 不可用")

    # 1) Best effort: NVML
    pynvml = _try_import("pynvml")
    if pynvml is not None:
        try:
            pynvml.nvmlInit()
            h = pynvml.nvmlDeviceGetHandleByIndex(0)
            mem = pynvml.nvmlDeviceGetMemoryInfo(h)
            return MemoryInfo(
                backend="cuda",
                total_bytes=int(mem.total),
                free_bytes=int(mem.free),
                note="来源: NVML",
            )
        except Exception as e:
            # fallthrough to torch
            note = f"NVML 失败: {type(e).__name__}"
        finally:
            try:
                pynvml.nvmlShutdown()
            except Exception:
                pass
    else:
        note = "未安装 pynvml，使用 torch 兜底"

    # 2) Fallback: torch api
    try:
        if hasattr(torch.cuda, "mem_get_info"):
            free_b, total_b = torch.cuda.mem_get_info()
            return MemoryInfo(
                backend="cuda",
                total_bytes=int(total_b),
                free_bytes=int(free_b),
                note=f"来源: torch.cuda.mem_get_info（{note}）",
            )
        props = torch.cuda.get_device_properties(0)
        total_b = int(getattr(props, "total_memory", 0)) or None
        return MemoryInfo(
            backend="cuda",
            total_bytes=total_b,
            free_bytes=None,
            note=f"来源: torch.cuda.get_device_properties（{note}）",
        )
    except Exception as e:
        return MemoryInfo(backend="cuda", note=f"torch 读取显存失败: {type(e).__name__}（{note}）")


def _mps_memory_info() -> MemoryInfo:
    # Apple MPS 无法像 CUDA 一样精确获得“显存”，这里只做保守策略：
    # - total/free：用系统内存近似（统一内存架构）
    # - note：标记为估算，不要当作 VRAM 精确值
    psutil = _try_import("psutil")
    if psutil is None:
        return MemoryInfo(backend="mps", note="未安装 psutil，无法估算内存")
    try:
        vm = psutil.virtual_memory()
        return MemoryInfo(
            backend="mps",
            total_bytes=int(vm.total),
            free_bytes=int(vm.available),
            note="来源: psutil.virtual_memory（统一内存，非精确 VRAM）",
        )
    except Exception as e:
        return MemoryInfo(backend="mps", note=f"psutil 读取内存失败: {type(e).__name__}")


def _cpu_memory_info() -> MemoryInfo:
    psutil = _try_import("psutil")
    if psutil is None:
        return MemoryInfo(backend="cpu", note="未安装 psutil，无法读取内存")
    try:
        vm = psutil.virtual_memory()
        return MemoryInfo(
            backend="cpu",
            total_bytes=int(vm.total),
            free_bytes=int(vm.available),
            note="来源: psutil.virtual_memory",
        )
    except Exception as e:
        return MemoryInfo(backend="cpu", note=f"psutil 读取内存失败: {type(e).__name__}")


def detect_device() -> str:
    torch = _try_import("torch")
    if torch is None:
        return "cpu"
    if getattr(torch.cuda, "is_available", lambda: False)():
        return "cuda"
    if getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def choose_dtype(device: str) -> str:
    # 默认策略：
    # - CUDA 优先 bf16，其次 fp16
    # - MPS：为了兼容 accelerate/transformers 某些版本对 mixed precision 的限制，默认用 fp32（更稳）
    # - CPU：fp32
    if device == "cuda":
        torch = _try_import("torch")
        if torch is None:
            return "fp16"
        # bf16 是否支持：较新 GPU 通常支持；不支持也可以退回 fp16
        try:
            if hasattr(torch.cuda, "is_bf16_supported") and torch.cuda.is_bf16_supported():
                return "bf16"
        except Exception:
            pass
        return "fp16"
    if device == "mps":
        return "fp32"
    return "fp32"


def _defaults_from_memory(device: str, mem: MemoryInfo) -> Dict[str, Any]:
    # 尽量保守：保证“跑得起来”，而不是追求极限速度
    total_gb = mem.total_gb()
    if device == "cuda" and total_gb is not None:
        if total_gb >= 16:
            return {"max_seq_length": 1024, "per_device_train_batch_size": 8, "gradient_accumulation_steps": 1}
        if total_gb >= 12:
            return {"max_seq_length": 1024, "per_device_train_batch_size": 4, "gradient_accumulation_steps": 1}
        if total_gb >= 8:
            return {"max_seq_length": 768, "per_device_train_batch_size": 2, "gradient_accumulation_steps": 2}
        return {"max_seq_length": 512, "per_device_train_batch_size": 1, "gradient_accumulation_steps": 4}

    if device == "mps":
        # MPS 容易 OOM，默认更保守
        return {"max_seq_length": 512, "per_device_train_batch_size": 1, "gradient_accumulation_steps": 8}

    # cpu
    return {"max_seq_length": 256, "per_device_train_batch_size": 1, "gradient_accumulation_steps": 16}


def plan_environment(overrides: Optional[Dict[str, Any]] = None) -> EnvPlan:
    device = detect_device()
    dtype = choose_dtype(device)

    if device == "cuda":
        mem = _cuda_memory_info()
    elif device == "mps":
        mem = _mps_memory_info()
    else:
        mem = _cpu_memory_info()

    defaults = _defaults_from_memory(device, mem)
    if overrides:
        defaults = {**defaults, **overrides}

    # 兼容可能出现的历史 typo key，避免日志/配置污染后续逻辑
    if "per_deatch_size" in defaults and "per_device_train_batch_size" not in defaults:
        defaults["per_device_train_batch_size"] = defaults.pop("per_deatch_size")

    return EnvPlan(device=device, dtype=dtype, memory=mem, defaults=defaults)


def pretty_env_summary(plan: EnvPlan) -> str:
    mem = plan.memory
    total = f"{mem.total_gb():.2f} GB" if mem.total_gb() is not None else "unknown"
    free = f"{mem.free_gb():.2f} GB" if mem.free_gb() is not None else "unknown"
    return (
        f"device={plan.device}, dtype={plan.dtype}, "
        f"mem.total={total}, mem.free={free}, note={mem.note}, "
        f"defaults={plan.defaults}"
    )


def lora_target_modules_for_qwen() -> Tuple[str, ...]:
    # Qwen2.x 常见线性层命名（注意不同版本可能略有差异）
    return (
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
    )


