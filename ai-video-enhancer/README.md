# AI Video Enhancer

A browser-based FastAPI application that enhances videos 2x with the official
`RealESRGAN_x2plus` model. It does not use Telegram.

## Replit

```bash
cd ai-video-enhancer
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements.txt
nix-shell -p ffmpeg
python main.py
```

The `.replit` file starts `python main.py`. Open port 8000 or use the Replit
web preview.

## Termux / phone

From the repository directory, run:

```bash
cd ai-video-enhancer
bash run.sh
```

Before the first run, install FFmpeg and Python dependencies in Termux:

```bash
pkg install python ffmpeg
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

Then one command starts both the FastAPI backend and the browser frontend:

```bash
bash run.sh
```

Open `http://127.0.0.1:8000` on the phone. For another device on the same
network, use `http://PHONE_IP:8000`.

## Configuration

Copy `.env.example` to `.env`. The limits default to `0`, which means no
application-level byte limit:

- `MAX_VIDEO_DURATION=60`
- `MAX_APP_INPUT_SIZE_MB=0`
- `MAX_APP_OUTPUT_SIZE_MB=0`
- `UPLOAD_CHUNK_SIZE_MB=8`
- `MAX_CONCURRENT_JOBS=1`
- `DEVICE=auto`
- `TILE_SIZE=128`
- `TILE_PAD=10`
- `CPU_THREADS=2`
- `PROCESSING_TIMEOUT=1800`
- `STORAGE_BACKEND=local`

Set `MAX_APP_INPUT_SIZE_MB` only for a deliberate infrastructure policy.
Telegram upload limits are not used.

## API

- `GET /health`
- `GET /api/status`
- `POST /api/upload/init`
- `POST /api/upload/chunk`
- `POST /api/upload/complete`
- `GET /api/upload/{upload_id}/status`
- `POST /api/enhance`
- `GET /api/jobs/{job_id}`
- `POST /api/jobs/{job_id}/cancel`
- `GET /api/jobs/{job_id}/result`
- `GET /api/download/{job_id}`

The frontend creates a browser session ID and sends it as `X-Session-ID`.
Uploads and jobs are scoped to that ID.

## Processing

The existing FFprobe, FFmpeg, and Real-ESRGAN pipeline is reused. It validates
the video, extracts frames, performs sequential FP32 CPU or CUDA inference,
rebuilds H.264/yuv420p MP4 frames, restores original audio, and verifies 2x
output resolution.

## Storage and deployment limits

The implementation uses local disk chunk storage. Upload and resumed chunk
support are implemented, but Replit request, proxy, disk, memory, CPU, and
process-duration limits remain infrastructure-specific and must be verified on
the selected Replit plan. The application does not claim unlimited capacity.
For reliable 1 GB uploads or long-duration jobs, use external S3-compatible
object storage and a dedicated processing worker. `STORAGE_BACKEND=local` is
the only storage backend implemented locally.
