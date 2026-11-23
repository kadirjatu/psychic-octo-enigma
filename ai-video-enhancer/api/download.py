from pathlib import Path

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import FileResponse

from api.enhancement import jobs
from api.upload import uploads
from config import TEMP_DIR

router = APIRouter(tags=["download"])


@router.get("/api/download/{job_id}")
def download_result(job_id: str, x_session_id: str | None = Header(None, alias="X-Session-ID")):
    job = jobs.get(job_id, x_session_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "Completed" or not job["output_path"]:
        raise HTTPException(status_code=409, detail="Result is not available")
    path = Path(job["output_path"])
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Result file not found")
    return FileResponse(path, media_type="video/mp4", filename="enhanced.mp4")


@router.get("/api/upload/{upload_id}/preview")
def preview_upload(upload_id: str, x_session_id: str | None = Header(None, alias="X-Session-ID")):
    manifest = uploads.get(upload_id, x_session_id)
    if manifest is None:
        raise HTTPException(status_code=404, detail="Upload not found")
    path = TEMP_DIR / "uploads" / upload_id / "video.bin"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Upload file not found")
    return FileResponse(path, media_type="application/octet-stream")
