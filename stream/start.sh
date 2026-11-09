#!/usr/bin/env bash
# 起静态页(6210) + 弹幕桥(6220)。
# 大脑(6200) 和 TTS(6211) 是另外的服务。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STREAM="$ROOT/stream"
LOG="${TMPDIR:-/tmp}/dafeiyu-live"
PY="${PYTHON:-$ROOT/.venv/bin/python}"
[ -x "$PY" ] || PY=python3

mkdir -p "$LOG"

if ! lsof -nP -iTCP:6210 -sTCP:LISTEN >/dev/null 2>&1; then
  (cd "$ROOT" && nohup python3 -m http.server 6210 >"$LOG/web.log" 2>&1 &)
  echo "web      :6210 started"
else
  echo "web      :6210 already running"
fi

if ! lsof -nP -iTCP:6220 -sTCP:LISTEN >/dev/null 2>&1; then
  (cd "$STREAM" && nohup "$PY" bridge.py >"$LOG/bridge.log" 2>&1 &)
  echo "bridge   :6220 started"
else
  echo "bridge   :6220 already running"
fi

sleep 2
echo
echo "画面   http://127.0.0.1:6210/stream/stream.html?audio=1"
echo "场控   http://127.0.0.1:6210/stream/control.html"
echo "日志   $LOG"
