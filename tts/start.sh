#!/usr/bin/env bash
# 起 TTS（6211）。依赖 mlx-audio，仅 Apple Silicon。
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$HERE")"

PY="${TTS_PYTHON:-$HERE/.venv/bin/python}"
[ -x "$PY" ] || PY="$ROOT/.venv/bin/python"
[ -x "$PY" ] || PY=python3

export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"

if [ -f "$HERE/tts.pid" ] && kill -0 "$(cat "$HERE/tts.pid" 2>/dev/null)" 2>/dev/null; then
  echo "TTS 已在运行：$(cat "$HERE/tts.pid")"
  exit 0
fi

if lsof -nP -iTCP:6211 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "TTS 端口 6211 已被占用"
  exit 0
fi

nohup "$PY" "$HERE/server.py" > "$HERE/tts.log" 2>&1 &
echo $! > "$HERE/tts.pid"
echo "TTS 启动：$(cat "$HERE/tts.pid")  http://127.0.0.1:6211/health"
