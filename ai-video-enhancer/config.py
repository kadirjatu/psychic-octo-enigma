import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent
WEIGHTS_DIR = ROOT / "weights"
TEMP_DIR = ROOT / "temp"
LOG_DIR = ROOT / "logs"
for directory in (WEIGHTS_DIR, TEMP_DIR, LOG_DIR):
    directory.mkdir(parents=True, exist_ok=True)

APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8000"))
DEVICE = os.getenv("DEVICE", "auto").lower()
MODEL_NAME = os.getenv("MODEL_NAME", "RealESRGAN_x2plus")
MAX_VIDEO_DURATION = int(os.getenv("MAX_VIDEO_DURATION", "60"))
MAX_INPUT_SIZE_MB = int(os.getenv("MAX_APP_INPUT_SIZE_MB", os.getenv("MAX_INPUT_SIZE_MB", "0")))
MAX_OUTPUT_SIZE_MB = int(os.getenv("MAX_APP_OUTPUT_SIZE_MB", os.getenv("MAX_OUTPUT_SIZE_MB", "0")))
UPLOAD_CHUNK_SIZE_MB = int(os.getenv("UPLOAD_CHUNK_SIZE_MB", "8"))
MAX_CONCURRENT_JOBS = int(os.getenv("MAX_CONCURRENT_JOBS", "1"))
TILE_SIZE = int(os.getenv("TILE_SIZE", "128"))
TILE_PAD = int(os.getenv("TILE_PAD", "10"))
CPU_THREADS = int(os.getenv("CPU_THREADS", "2"))
PROCESSING_TIMEOUT = int(os.getenv("PROCESSING_TIMEOUT", "1800"))
LOCAL_BOT_API_URL = os.getenv("TELEGRAM_LOCAL_API_URL", "")
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local").lower()
MODEL_URL = (
    "https://github.com/xinntao/Real-ESRGAN/releases/download/"
    "v0.2.1/RealESRGAN_x2plus.pth"
)
