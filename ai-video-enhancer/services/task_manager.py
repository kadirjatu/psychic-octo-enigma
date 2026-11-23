import asyncio
import threading
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class ProcessingTask:
    user_id: int
    cancel_event: threading.Event = field(default_factory=threading.Event)
    asyncio_task: Optional[asyncio.Task] = None
    input_path: Optional[str] = None
    work_dir: Optional[str] = None


class TaskManager:
    def __init__(self):
        self._tasks: Dict[int, ProcessingTask] = {}
        self._lock = threading.Lock()

    def get_or_create(self, user_id: int) -> ProcessingTask:
        with self._lock:
            task = self._tasks.get(user_id)
            if task is None:
                task = ProcessingTask(user_id=user_id)
                self._tasks[user_id] = task
            return task

    def cancel(self, user_id: int) -> bool:
        with self._lock:
            task = self._tasks.get(user_id)
            if task is None:
                return False
            task.cancel_event.set()
            if task.asyncio_task:
                task.asyncio_task.cancel()
            return True

    def remove(self, user_id: int) -> None:
        with self._lock:
            self._tasks.pop(user_id, None)
