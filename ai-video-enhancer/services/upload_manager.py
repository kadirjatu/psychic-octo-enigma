import json
import threading
import uuid
from pathlib import Path
from typing import BinaryIO, Optional

from config import MAX_INPUT_SIZE_MB, STORAGE_BACKEND, TEMP_DIR
from services.storage_manager import LocalStorageManager


class UploadManager:
    def __init__(self):
        self.storage = LocalStorageManager(TEMP_DIR)
        self._uploads = {}
        self._lock = threading.Lock()

    def init(self, filename: str, total_size: int, owner: str) -> dict:
        if STORAGE_BACKEND not in ("local", ""):
            raise RuntimeError(
                "S3-compatible storage is not configured. "
                "Set STORAGE_BACKEND=local or configure an external worker."
            )
        if total_size < 0:
            raise ValueError("Invalid upload size")
        if MAX_INPUT_SIZE_MB > 0 and total_size > MAX_INPUT_SIZE_MB * 1024 * 1024:
            raise ValueError(
                f"Upload exceeds the configured application limit of "
                f"{MAX_INPUT_SIZE_MB} MB"
            )
        upload_id = uuid.uuid4().hex
        directory = self.storage.create_upload(upload_id)
        manifest = {
            "upload_id": upload_id,
            "filename": Path(filename).name,
            "total_size": total_size,
            "owner": owner,
            "received": 0,
            "chunks": [],
            "completed": False,
        }
        self._write_manifest(directory, manifest)
        return manifest

    def _manifest_path(self, directory: Path) -> Path:
        return directory / "manifest.json"

    def _write_manifest(self, directory: Path, manifest: dict) -> None:
        temporary = directory / ".manifest.tmp"
        temporary.write_text(json.dumps(manifest), encoding="utf-8")
        temporary.replace(self._manifest_path(directory))

    def get(self, upload_id: str, owner: str) -> Optional[dict]:
        directory = TEMP_DIR / "uploads" / upload_id
        path = self._manifest_path(directory)
        if not path.is_file():
            return None
        manifest = json.loads(path.read_text(encoding="utf-8"))
        if manifest["owner"] != owner:
            return None
        return manifest

    def append_chunk(
        self,
        upload_id: str,
        owner: str,
        offset: int,
        chunk: BinaryIO,
        chunk_size: Optional[int],
    ) -> dict:
        manifest = self.get(upload_id, owner)
        if manifest is None:
            raise KeyError("Upload session not found")
        if manifest["completed"]:
            raise ValueError("Upload is already complete")
        if offset != manifest["received"]:
            raise ValueError(
                f"Chunk offset mismatch: expected {manifest['received']}, got {offset}"
            )
        directory = TEMP_DIR / "uploads" / upload_id
        target = directory / "video.bin"
        written = self.storage.append_chunk(target, chunk)
        if chunk_size is not None and written != chunk_size:
            raise RuntimeError("Chunk was truncated")
        manifest["received"] += written
        if manifest["received"] > manifest["total_size"]:
            raise ValueError("Upload exceeds the declared file size")
        manifest["chunks"].append({"offset": offset, "size": written})
        self._write_manifest(directory, manifest)
        return manifest

    def complete(self, upload_id: str, owner: str) -> dict:
        manifest = self.get(upload_id, owner)
        if manifest is None:
            raise KeyError("Upload session not found")
        if manifest["received"] != manifest["total_size"]:
            raise ValueError(
                f"Upload incomplete: {manifest['received']} of "
                f"{manifest['total_size']} bytes received"
            )
        directory = TEMP_DIR / "uploads" / upload_id
        source = directory / "video.bin"
        if not source.is_file() or source.stat().st_size == 0:
            raise ValueError("Uploaded file is empty")
        manifest["completed"] = True
        self._write_manifest(directory, manifest)
        return manifest

