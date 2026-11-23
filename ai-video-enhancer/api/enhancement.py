import asyncio
import logging
import shutil
import threading
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from config import (
    MAX_CONCURRENT_JOBS,
    PROCESSING_TIMEOUT,
    TEMP_DIR,
)
from api.upload import uploads
from services.job_manager import JobManager
from services.pipeline import process_video

log = logging.getLogger(__name__)
router = APIRouter(tags=["enhancement"])
jobs = JobManager()
semaphore = asyncio.Semaphore(MAX_CONCURRENT_JOBS)


class EnhanceRequest(BaseModel):
    upload_id: str
    tile_size: int | None = None


async def run_job(job_id: str):
    await semaphore.acquire()
    job = jobs.get(job_id)
    if job is None:
        return
    try:
        work_dir = Path(job["work_dir"])
        input_path = work_dir / "input.mp4"
        source = TEMP_DIR / "uploads" / job["upload_id"] / "video.bin"
        shutil.copyfile(source, input_path)

        def stage(stage: str, force: bool):
            jobs.update(job_id, status=stage, stage=stage)

        def frame(done: int, total: int):
            progress = int(done * 100 / total) if total else 0
            jobs.update(
                job_id,
                status="Enhancing",
                stage=f"Enhancing frame {done} of {total}",
                completed_frames=done,
                total_frames=total,
                progress=progress,
            )

        output, final = await asyncio.wait_for(
            asyncio.to_thread(
                process_video,
                input_path,
                work_dir,
                job["cancel_event"],
                stage,
                frame,
                job.get("tile_size"),
            ),
            timeout=PROCESSING_TIMEOUT,
        )
        result_path = work_dir / "enhanced.mp4"
        jobs.update(
            job_id,
            status="Completed",
            stage="Completed",
            progress=100,
            end_time=asyncio.get_running_loop().time(),
            output_path=str(result_path),
            result=final,
        )
    except asyncio.CancelledError:
        jobs.update(job_id, status="Cancelled", stage="Cancelled")
    except InterruptedError:
        jobs.update(job_id, status="Cancelled", stage="Cancelled")
    except asyncio.TimeoutError:
        jobs.update(
            job_id,
            status="Failed",
            stage="Processing timed out",
            error="The configured processing timeout was reached",
            end_time=asyncio.get_running_loop().time(),
        )
    except Exception as exc:
        log.exception("Video processing failed")
        jobs.update(
            job_id,
            status="Failed",
            stage="Processing failed",
            error=str(exc),
            end_time=asyncio.get_running_loop().time(),
        )
    finally:
        semaphore.release()


@router.post("/api/enhance")
async def enhance(
    payload: EnhanceRequest,
    x_session_id: str = Header(..., alias="X-Session-ID"),
):
    manifest = uploads.get(payload.upload_id, x_session_id)
    if manifest is None or not manifest["completed"]:
        raise HTTPException(status_code=404, detail="Completed upload not found")
    work_dir = TEMP_DIR / "jobs" / payload.upload_id
    work_dir.mkdir(parents=True, exist_ok=True)
    job = jobs.create(payload.upload_id, x_session_id, work_dir)
    tile_size = payload.tile_size
    if tile_size is not None and not 32 <= tile_size <= 1024:
        raise HTTPException(status_code=400, detail="Tile size must be between 32 and 1024")
    jobs.update(job["job_id"], tile_size=tile_size)
    task = asyncio.create_task(run_job(job["job_id"]))
    jobs.update(job["job_id"], task=task)
    return job
