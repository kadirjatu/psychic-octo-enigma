import hashlib
import logging
import os
import urllib.request
from pathlib import Path

from ai.device_manager import configure_torch, select_device
from config import MODEL_URL, TILE_PAD, TILE_SIZE, WEIGHTS_DIR

log = logging.getLogger(__name__)

WEIGHTS_PATH = WEIGHTS_DIR / "RealESRGAN_x2plus.pth"


def download_weights(progress_callback=None) -> Path:
    WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    if WEIGHTS_PATH.is_file() and WEIGHTS_PATH.stat().st_size > 1_000_000:
        log.info("Using existing Real-ESRGAN weights: %s", WEIGHTS_PATH)
        return WEIGHTS_PATH

    tmp_path = WEIGHTS_PATH.with_suffix(".pth.download")
    try:
        with urllib.request.urlopen(MODEL_URL, timeout=60) as response:
            total = int(response.headers.get("Content-Length", 0))
            downloaded = 0
            with open(tmp_path, "wb") as output:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    output.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total:
                        progress_callback(downloaded, total)
        if tmp_path.stat().st_size <= 1_000_000:
            raise RuntimeError("Downloaded model weights are unexpectedly small")
        os.replace(tmp_path, WEIGHTS_PATH)
    finally:
        if tmp_path.exists() and not WEIGHTS_PATH.exists():
            tmp_path.unlink(missing_ok=True)
    return WEIGHTS_PATH
