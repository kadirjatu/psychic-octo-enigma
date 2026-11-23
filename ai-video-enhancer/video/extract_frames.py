import shutil
import subprocess
from pathlib import Path


def extract_frames(input_video: Path, output_dir: Path) -> int:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    pattern = output_dir / "frame_%09d.png"
    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(input_video),
        "-map", "0:v:0",
        "-vsync", "0",
        str(pattern),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Frame extraction failed: {result.stderr.strip()}")
    count = len(list(output_dir.glob("frame_*.png")))
    if count == 0:
        raise RuntimeError("Frame extraction produced no frames")
    return count
