import logging
from logging.handlers import RotatingFileHandler

import torch
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config import APP_HOST, APP_PORT, LOG_DIR, MAX_VIDEO_DURATION, TILE_PAD, TILE_SIZE
from api import router as api_router
from ai.device_manager import select_device


def configure_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            RotatingFileHandler(LOG_DIR / "app.log", maxBytes=5 * 1024 * 1024, backupCount=3),
            logging.StreamHandler(),
        ],
    )


configure_logging()
app = FastAPI(title="AI Video Enhancer", version="1.0.0")
app.include_router(api_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/status")
def status():
    device = select_device()
    return {
        "status": "ok",
        "model": "RealESRGAN_x2plus",
        "scale": 2,
        "device": device,
        "cuda_available": torch.cuda.is_available(),
        "max_video_duration": MAX_VIDEO_DURATION,
        "tile_size": TILE_SIZE,
        "tile_pad": TILE_PAD,
    }


app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=APP_HOST, port=APP_PORT)
