import subprocess
from pathlib import Path


def rebuild_video(frames_dir: Path, fps: float, output_path: Path) -> None:
    pattern = frames_dir / "frame_%09d.png"
    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-framerate", f"{fps:.6f}",
        "-i", str(pattern),
        "-an",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(output_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Video reconstruction failed: {result.stderr.strip()}")
