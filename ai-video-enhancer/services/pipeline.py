import logging
import shutil
from pathlib import Path
from typing import Callable

from services.cleanup import cleanup_directory
from video.probe import probe_video
from video.extract_frames import extract_frames
from video.enhance_frames import enhance_frames
from video.rebuild_video import rebuild_video
from video.audio_manager import restore_audio

log = logging.getLogger(__name__)


def validate_output(output: Path, original: dict) -> dict:
    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError("Completed output is missing or empty")
    final = probe_video(output)
    expected_width = original["width"] * 2
    expected_height = original["height"] * 2
    if final["width"] != expected_width or final["height"] != expected_height:
        raise RuntimeError(
            f"Output resolution mismatch: got {final['width']}x{final['height']}, "
            f"expected {expected_width}x{expected_height}"
        )
    if abs(final["duration"] - original["duration"]) > 1.0:
        raise RuntimeError(
            f"Output duration mismatch: {final['duration']:.2f}s "
            f"vs {original['duration']:.2f}s"
        )
    return final


def process_video(
    input_path: Path,
    work_dir: Path,
    cancel_event,
    stage_callback: Callable[[str, bool], None],
    frame_callback: Callable[[int, int], None],
    tile_size: int | None = None,
) -> tuple[Path, dict]:
    stage_callback("Validating video.", True)
    original = probe_video(input_path)

    stage_callback("Extracting frames.", True)
    frames_dir = work_dir / "source_frames"
    frame_count = extract_frames(input_path, frames_dir)

    stage_callback("Loading AI model.", True)
    enhanced_dir = work_dir / "enhanced_frames"
    actual_count = enhance_frames(
        frames_dir,
        enhanced_dir,
        cancel_event,
        frame_callback,
        tile_size,
    )
    if actual_count != frame_count:
        raise RuntimeError(
            f"Enhanced frame count mismatch: {actual_count} != {frame_count}"
        )

    stage_callback("Rebuilding video.", True)
    video_only = work_dir / "enhanced_silent.mp4"
    rebuild_video(enhanced_dir, original["fps"], video_only)

    stage_callback("Restoring audio.", True)
    output = work_dir / "enhanced.mp4"
    if original["has_audio"]:
        restore_audio(video_only, input_path, output)
    else:
        shutil.copy2(video_only, output)

    stage_callback("Validating completed output.", True)
    final = validate_output(output, original)
    return output, final
