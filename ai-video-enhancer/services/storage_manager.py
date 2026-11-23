import os
from pathlib import Path
from typing import BinaryIO


class LocalStorageManager:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def create_upload(self, upload_id: str) -> Path:
        directory = self.root / "uploads" / upload_id
        directory.mkdir(parents=True, mode=0o700)
        return directory

    def append_chunk(self, path: Path, chunk: BinaryIO) -> int:
        path.parent.mkdir(parents=True, exist_ok=True)
        written = 0
        with path.open("ab") as destination:
            while True:
                data = chunk.read(1024 * 1024)
                if not data:
                    break
                destination.write(data)
                written += len(data)
        return written

    def upload_path(self, upload_id: str, name: str = "video.bin") -> Path:
        return self.root / "uploads" / upload_id / name

