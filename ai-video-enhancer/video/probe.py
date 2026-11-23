import json
import subprocess
from fractions import Fraction
from pathlib import Path


SUPPORTED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi"}


def probe_video(path: Path) -> dict:
    command = [
        "ffprobe", "-v", "error", "-show_format", "-show_streams",
        "-of", "json", str(path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise ValueError(f"Invalid video file: {result.stderr.strip()}")
    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    if not video_stream:
        raise ValueError("The file contains no video stream")

    duration = float(data.get("format", {}).get("duration", video_stream.get("duration", 0)))
    width = int(video_stream["width"])
    height = int(video_stream["height"])
    rotation = 0
    for entry in video_stream.get("tags", {}).values():
        pass
    for side_data in video_stream.get("side_data_list", []) or []:
        if "rotation" in side_data:
            rotation = int(side_data["rotation"])
    if abs(rotation) in (90, 270):
        width, height = height, width

    rate = video_stream.get("avg_frame_rate") or video_stream.get("r_frame_rate") or "30/1"
    fraction = Fraction(rate)
    fps = float(fraction)
    if not 0 < fps <= 240:
        raise ValueError("Could not determine a valid frame rate")

    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    frame_count = None
    count_result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-count_frames", "-show_entries", "stream=nb_read_frames",
            "-of", "default=nokey=1:noprint_wrappers=1", str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if count_result.returncode == 0 and count_result.stdout.strip().isdigit():
        frame_count = int(count_result.stdout.strip())
    return {
        "duration": duration,
        "width": width,
        "height": height,
        "fps": fps,
        "frame_count": frame_count,
        "video_codec": video_stream.get("codec_name"),
        "audio_codec": audio.get("codec_name") if audio else None,
        "rotation": rotation,
        "pixel_format": video_stream.get("pix_fmt"),
        "has_audio": audio is not None,
        "format": data.get("format", {}).get("format_name", ""),
        "size_bytes": int(data.get("format", {}).get("size", path.stat().st_size)),
    }
