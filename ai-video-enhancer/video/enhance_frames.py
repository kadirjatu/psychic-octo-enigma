import gc
from pathlib import Path
from typing import Callable, Optional

import cv2

from ai.realesrgan_engine import RealESRGANEngine


def enhance_frames(
    input_dir: Path,
    output_dir: Path,
    cancel_event,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    tile_size: Optional[int] = None,
) -> int:
    if output_dir.exists():
        for file in output_dir.iterdir():
            file.unlink()
    else:
        output_dir.mkdir(parents=True)

    engine = RealESRGANEngine()
    engine.load(tile_size)
    frames = sorted(input_dir.glob("frame_*.png"))
    total = len(frames)
    for index, frame_path in enumerate(frames, start=1):
        if cancel_event.is_set():
            raise InterruptedError("Processing cancelled")
        output = engine.enhance_frame(frame_path)
        destination = output_dir / frame_path.name
        if not cv2.imwrite(str(destination), output):
            raise RuntimeError(f"Failed to write enhanced frame: {destination}")
        del output
        gc.collect()
        if progress_callback:
            progress_callback(index, total)
    return total
