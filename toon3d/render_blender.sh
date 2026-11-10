#!/usr/bin/env bash
# Render a Blender scene to a transparent PNG sequence.
# Usage: BLENDER=/Applications/Blender.app/Contents/MacOS/Blender \
#          ./toon3d/render_blender.sh scene.blend /tmp/toon_frames
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "usage: $0 scene.blend output_dir [extra Blender args]" >&2
  exit 2
fi

SCENE="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
OUT="$2"
shift 2

mkdir -p "$OUT"

if [ -z "${BLENDER:-}" ]; then
  if [ -x /Applications/Blender.app/Contents/MacOS/Blender ]; then
    BLENDER=/Applications/Blender.app/Contents/MacOS/Blender
  else
    BLENDER=blender
  fi
fi

if ! command -v "$BLENDER" >/dev/null 2>&1; then
  echo "Blender not found: $BLENDER" >&2
  echo "Set BLENDER=/Applications/Blender.app/Contents/MacOS/Blender" >&2
  exit 1
fi

echo "scene:  $SCENE"
echo "frames: $OUT/frame_####.png"
"$BLENDER" -b "$SCENE" -o "$OUT/frame_####" -F PNG -x 1 "$@" -a
