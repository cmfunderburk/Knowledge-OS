"""
Shared CUDA utilities for voice and TTS modules.

Handles CUDA availability checking and NVIDIA library preloading.
"""
import ctypes
import importlib.util
import os

_cuda_available: bool | None = None


def is_cuda_available() -> bool:
    """Check if CUDA is available for PyTorch."""
    global _cuda_available
    if _cuda_available is not None:
        return _cuda_available

    try:
        import torch
        _cuda_available = torch.cuda.is_available()
    except ImportError:
        _cuda_available = False

    return _cuda_available


def preload_nvidia_libraries() -> None:
    """
    Preload NVIDIA libraries so PyTorch/ctranslate2 can find them.

    This is needed when using pip-installed nvidia-* packages,
    as the libraries aren't in the standard library path.
    """
    if not is_cuda_available():
        return

    libs_to_load = [
        ("nvidia.nccl.lib", "libnccl.so.2"),
        ("nvidia.cublas.lib", "libcublas.so.12"),
        ("nvidia.cublas.lib", "libcublasLt.so.12"),
        ("nvidia.cudnn.lib", "libcudnn.so.9"),
    ]

    for module_name, lib_name in libs_to_load:
        try:
            spec = importlib.util.find_spec(module_name)
            if spec and spec.submodule_search_locations:
                lib_path = os.path.join(spec.submodule_search_locations[0], lib_name)
                if os.path.exists(lib_path):
                    ctypes.CDLL(lib_path, mode=ctypes.RTLD_GLOBAL)
        except Exception:
            pass


# Preload on import
preload_nvidia_libraries()
