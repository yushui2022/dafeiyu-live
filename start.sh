#!/usr/bin/env bash
# 一键起直播侧：TTS(6211) + 静态页(6210) + 弹幕桥(6220)。
# 大脑(6200) 在 Hippocampus 仓库里，需要先起来。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
LOG="${TMPDIR:-/tmp}/dafeiyu-live"
mkdir -p "$LOG"

echo "== 大脑检查 =="
if curl -s --max-time 3 http://127.0.0.1:6200/health >/dev/null 2>&1; then
  echo "大脑 :6200 已在线"
else
  echo "警告：6200 没有响应。画面和语音能起来，但不会回话。"
  echo "      先启动 Hippocampus 的 companion。"
fi

echo
echo "== 语音 =="
"$ROOT/tts/start.sh"

echo
echo "== 画面 + 弹幕桥 =="
"$ROOT/stream/start.sh"

echo
echo "画面   http://127.0.0.1:6210/stream/stream.html?audio=1"
echo "场控   http://127.0.0.1:6210/stream/control.html"
echo "日志   $LOG"
