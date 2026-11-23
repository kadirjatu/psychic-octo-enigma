import asyncio
import threading

from config import MAX_CONCURRENT_JOBS


class QueueManager:
    def __init__(self):
        self._semaphore = asyncio.Semaphore(MAX_CONCURRENT_JOBS)
        self.running = 0
        self.waiting = 0
        self._lock = threading.Lock()

    async def acquire(self):
        with self._lock:
            self.waiting += 1
        await self._semaphore.acquire()
        with self._lock:
            self.waiting -= 1
            self.running += 1

    def release(self):
        with self._lock:
            self.running -= 1
        self._semaphore.release()
