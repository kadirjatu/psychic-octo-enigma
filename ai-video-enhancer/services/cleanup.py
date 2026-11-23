import shutil
from pathlib import Path


def cleanup_directory(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
