#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

if [[ -x ".venv/bin/python" ]]; then
    PYTHON=".venv/bin/python"
else
    PYTHON="${PYTHON:-python}"
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "Error: ffmpeg is not installed."
    echo "Termux: pkg install ffmpeg"
    exit 1
fi

exec "$PYTHON" main.py
