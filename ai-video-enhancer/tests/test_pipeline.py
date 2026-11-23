from pathlib import Path

from services.pipeline import validate_output


def test_output_rejects_wrong_resolution(tmp_path: Path):
    output = tmp_path / "wrong.mp4"
    output.write_bytes(b"not a real video")
    original = {"width": 100, "height": 100, "duration": 1.0}
    try:
        validate_output(output, original)
    except (ValueError, RuntimeError):
        return
    raise AssertionError("Invalid output was accepted")
