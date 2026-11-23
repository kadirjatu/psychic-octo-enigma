import gc
import logging
from pathlib import Path
from typing import Callable, Optional
import sys
import types

import cv2
import torch
import torchvision.transforms.functional as torchvision_functional

# BasicSR 1.4.2 references an API removed by newer torchvision releases.
if "torchvision.transforms.functional_tensor" not in sys.modules:
    compatibility_module = types.ModuleType(
        "torchvision.transforms.functional_tensor"
    )
    compatibility_module.rgb_to_grayscale = (
        torchvision_functional.rgb_to_grayscale
    )
    sys.modules["torchvision.transforms.functional_tensor"] = compatibility_module

from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer

from ai.device_manager import configure_torch, select_device
from ai.model_loader import WEIGHTS_PATH, download_weights
from config import TILE_PAD, TILE_SIZE

log = logging.getLogger(__name__)


class RealESRGANEngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._upsampler = None
            cls._instance.device = None
        return cls._instance

    def load(self, tile_size: int | None = None) -> None:
        if self._upsampler is not None:
            return

        weights = download_weights()
        if weights.stat().st_size <= 1_000_000:
            raise RuntimeError("RealESRGAN_x2plus weights failed verification")

        self.device = select_device()
        configure_torch(self.device)
        model = RRDBNet(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=64,
            num_block=23,
            num_grow_ch=32,
            scale=2,
        )
        self._upsampler = RealESRGANer(
            scale=2,
            model_path=str(weights),
            model=model,
            tile=tile_size or TILE_SIZE,
            tile_pad=TILE_PAD,
            pre_pad=10,
            half=False,
            device=torch.device(self.device),
        )
        log.info("Loaded RealESRGAN_x2plus on %s", self.device)

    def enhance_frame(self, frame_path: Path) -> object:
        if self._upsampler is None:
            raise RuntimeError("Model is not loaded")
        image = cv2.imread(str(frame_path), cv2.IMREAD_COLOR)
        if image is None:
            raise RuntimeError(f"Failed to read frame: {frame_path}")
        with torch.inference_mode():
            try:
                output, _ = self._upsampler.enhance(image, outscale=2)
            except RuntimeError as exc:
                if "out of memory" in str(exc).lower():
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                    raise RuntimeError("AI processing ran out of memory") from exc
                raise
        del image
        gc.collect()
        return output
