from fastapi import APIRouter

from api.upload import router as upload_router
from api.enhancement import router as enhancement_router
from api.jobs import router as jobs_router
from api.download import router as download_router

router = APIRouter()
router.include_router(upload_router)
router.include_router(enhancement_router)
router.include_router(jobs_router)
router.include_router(download_router)
