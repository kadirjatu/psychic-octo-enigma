from fastapi import APIRouter, Header, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from pathlib import Path

from config import UPLOAD_CHUNK_SIZE_MB
from services.upload_manager import UploadManager
from video.probe import probe_video

router = APIRouter(tags=["upload"])
uploads = UploadManager()


class UploadInit(BaseModel):
    filename: str
    total_size: int


@router.post("/api/upload/init")
def init_upload(payload: UploadInit, x_session_id: str = Header(..., alias="X-Session-ID")):
    try:
        manifest = uploads.init(payload.filename, payload.total_size, x_session_id)
        return {
            "upload_id": manifest["upload_id"],
            "received": 0,
            "chunk_size": UPLOAD_CHUNK_SIZE_MB * 1024 * 1024,
        }
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/upload/chunk")
async def upload_chunk(
    upload_id: str = Form(...),
    offset: int = Form(...),
    chunk: UploadFile = File(...),
    x_session_id: str = Header(..., alias="X-Session-ID"),
):
    try:
        manifest = uploads.append_chunk(
            upload_id,
            x_session_id,
            offset,
            chunk.file,
            chunk.size,
        )
        return {"upload_id": upload_id, "received": manifest["received"]}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/upload/complete")
def complete_upload(payload: dict, x_session_id: str = Header(..., alias="X-Session-ID")):
    upload_id = payload.get("upload_id")
    if not upload_id:
        raise HTTPException(status_code=400, detail="upload_id is required")
    try:
        manifest = uploads.complete(upload_id, x_session_id)
        path = Path(uploads.storage.upload_path(upload_id, "video.bin"))
        info = probe_video(path)
        from config import MAX_VIDEO_DURATION
        if info["duration"] > MAX_VIDEO_DURATION:
            raise ValueError(
                f"Video is {info['duration']:.1f}s; maximum is "
                f"{MAX_VIDEO_DURATION}s."
            )
        return {"upload_id": upload_id, "info": info}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/api/upload/{upload_id}/status")
def upload_status(upload_id: str, x_session_id: str = Header(..., alias="X-Session-ID")):
    manifest = uploads.get(upload_id, x_session_id)
    if manifest is None:
        raise HTTPException(status_code=404, detail="Upload session not found")
    return {
        "upload_id": upload_id,
        "received": manifest["received"],
        "total_size": manifest["total_size"],
        "completed": manifest["completed"],
    }
