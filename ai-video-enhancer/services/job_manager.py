import asyncio
import threading
import time
import uuid
from pathlib import Path
from typing import Dict, Optional

from services.cleanup import cleanup_directory


class JobManager:
    def __init__(self):
        self._jobs: Dict[str, dict] = {}
        self._lock = threading.Lock()

    def create(self, upload_id: str, owner: str, work_dir: Path) -> dict:
        job_id = uuid.uuid4().hex
        job = {
            "job_id": job_id,
            "upload_id": upload_id,
            "owner": owner,
            "status": "Uploaded",
            "stage": "Waiting to process",
            "completed_frames": 0,
            "total_frames": 0,
            "progress": 0,
            "start_time": time.time(),
            "end_time": None,
            "error": None,
            "work_dir": str(work_dir),
            "output_path": None,
            "cancel_event": threading.Event(),
            "task": None,
        }
        with self._lock:
            self._jobs[job_id] = job
        return self.public(job)

    def get(self, job_id: str, owner: Optional[str] = None) -> Optional[dict]:
        with self._lock:
            job = self._jobs.get(job_id)
            if job and owner is not None and job["owner"] != owner:
                return None
            return job

    def update(self, job_id: str, **changes) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.update(changes)

    def cancel(self, job_id: str, owner: str) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job or job["owner"] != owner:
                return False
            if job["status"] in ("Completed", "Failed", "Cancelled"):
                return False
            job["cancel_event"].set()
            job["status"] = "Cancelled"
            job["stage"] = "Cancellation requested"
            task = job["task"]
        if task is not None:
            task.cancel()
        return True

    def public(self, job: dict) -> dict:
        return {
            key: value
            for key, value in job.items()
            if key not in ("owner", "work_dir", "output_path", "cancel_event", "task")
        }

    def cleanup(self, job_id: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                cleanup_directory(Path(job["work_dir"]))
