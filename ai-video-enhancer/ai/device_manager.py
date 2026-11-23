import logging

import torch

from config import CPU_THREADS, DEVICE

log = logging.getLogger(__name__)


def select_device() -> str:
    if DEVICE == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("DEVICE=cuda requested, but CUDA is not available")
        return "cuda"
    if DEVICE == "cpu":
        return "cpu"
    return "cuda" if torch.cuda.is_available() else "cpu"


def configure_torch(device: str) -> None:
    torch.set_num_threads(max(1, CPU_THREADS))
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass
    if device == "cuda":
        torch.backends.cudnn.benchmark = True
