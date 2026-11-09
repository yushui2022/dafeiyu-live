#!/usr/bin/env bash
# 停掉直播侧三个服务。
set -uo pipefail

for port in 6220 6211 6210; do
  pid="$(lsof -ti tcp:$port 2>/dev/null | head -1 || true)"
  if [ -n "$pid" ]; then
    kill "$pid" 2>/dev/null && echo "stopped :$port (pid $pid)"
  else
    echo ":$port 未运行"
  fi
done
