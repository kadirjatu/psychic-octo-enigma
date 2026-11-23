from fastapi import APIRouter, Header, HTTPException

from api.enhancement import jobs

router = APIRouter(tags=["jobs"])


@router.get("/api/jobs/{job_id}")
def get_job(job_id: str, x_session_id: str = Header(..., alias="X-Session-ID")):
    job = jobs.get(job_id, x_session_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs.public(job)


@router.post("/api/jobs/{job_id}/cancel")
def cancel_job(job_id: str, x_session_id: str = Header(..., alias="X-Session-ID")):
    if not jobs.cancel(job_id, x_session_id):
        raise HTTPException(status_code=404, detail="Active owned job not found")
    job = jobs.get(job_id, x_session_id)
    return jobs.public(job)


@router.get("/api/jobs/{job_id}/result")
def job_result(job_id: str, x_session_id: str = Header(..., alias="X-Session-ID")):
    job = jobs.get(job_id, x_session_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "Completed":
        raise HTTPException(status_code=409, detail="Job is not complete")
    return {
        "job_id": job_id,
        "status": job["status"],
        "result": job.get("result"),
        "download_url": f"/api/download/{job_id}",
    }
