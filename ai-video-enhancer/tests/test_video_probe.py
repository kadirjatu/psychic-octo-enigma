import shutil
import subprocess
from pathlib import Path

import pytest

from video.probe import probe_video


@pytest.fixture
def sample_video(tmp_path: Path) -> Path:
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        pytest.skip("FFmpeg/FFprobe are required")
    path = tmp_path / "sample.mp4"
    result = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "testsrc2=size=160x90:rate=30",
            "-f", "lavfi", "-i", "sine=frequency=1000",
            "-t", "1", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", str(path),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    return path


def test_probe_reports_video_details(sample_video: Path):
    info = probe_video(sample_video)
    assert info["width"] == 160
    assert info["height"] == 90
    assert info["fps"] == 30
    assert info["has_audio"] is True
    assert 0.9 <= info["duration"] <= 1.2
