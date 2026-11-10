#!/usr/bin/env python3
"""Blender RGBA frames -> aligned 1366x768 VP9 alpha WebM.

Blender should render a transparent PNG sequence:

    frames/frame_0001.png
    frames/frame_0002.png
    ...

This script finds the largest alpha component in each frame, anchors it by
head width / feet / centre, writes a fixed-size canvas, and calls ffmpeg with
`yuva420p` so the WebM keeps its alpha channel.

Example:

    python toon3d/render_to_webm.py \
      --input /tmp/toon_frames \
      --output assets/toon3d/idle_a.webm \
      --head-width 311 --bottom 671 --center 683

The anchor defaults match the existing 2D clips. If the 3D model has different
proportions, set `--head-width 0` to use the clip median and choose new
bottom/centre values; all clips in a set must then use the same anchors.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

RESAMPLE = getattr(Image, "Resampling", Image).LANCZOS


def body_box(alpha: np.ndarray, threshold: int = 24) -> tuple[int, int, int, int] | None:
    """Bounding box of the largest connected opaque blob."""
    mask = alpha > threshold
    labels, count = ndimage.label(mask)
    if count == 0:
        return None
    sizes = ndimage.sum(mask, labels, range(1, count + 1))
    ys, xs = np.where(labels == int(np.argmax(sizes)) + 1)
    if ys.size == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def head_width(alpha: np.ndarray, threshold: int = 24, top_frac: float = 0.42) -> int | None:
    """Horizontal span of the upper 42% of the largest blob."""
    box = body_box(alpha, threshold)
    if box is None:
        return None
    mask = alpha > threshold
    labels, count = ndimage.label(mask)
    if count == 0:
        return None
    sizes = ndimage.sum(mask, labels, range(1, count + 1))
    ys, xs = np.where(labels == int(np.argmax(sizes)) + 1)
    top, bottom = ys.min(), ys.max()
    band = ys < top + (bottom - top) * top_frac
    if not band.any():
        return None
    return int(xs[band].max() - xs[band].min())


def load_frames(directory: Path) -> list[Image.Image]:
    paths = sorted(directory.glob("*.png"))
    if not paths:
        raise SystemExit(f"no PNG frames found in {directory}")
    frames = []
    opaque = 0
    for path in paths:
        with Image.open(path) as image:
            frame = image.convert("RGBA").copy()
        if (np.array(frame.getchannel("A")) > 24).mean() > 0.98:
            opaque += 1
        frames.append(frame)
    if opaque:
        raise SystemExit(
            f"{opaque}/{len(frames)} frames are almost fully opaque; "
            "enable Blender Film Transparent and export PNG with alpha"
        )
    return frames


def align_frame(
    frame: Image.Image,
    target_head: int,
    bottom: int,
    center: int,
    width: int,
    height: int,
    floor: int,
) -> Image.Image:
    alpha = np.array(frame.getchannel("A"))
    box = body_box(alpha)
    if box is None:
        return Image.new("RGBA", (width, height), (0, 0, 0, 0))

    measured = head_width(alpha)
    scale = 1.0
    if target_head > 0 and measured:
        scale = target_head / measured
        if scale < 0.2 or scale > 5.0:
            scale = max(0.2, min(5.0, scale))

    if abs(scale - 1.0) > 0.005:
        frame = frame.resize(
            (max(1, round(frame.width * scale)), max(1, round(frame.height * scale))),
            RESAMPLE,
        )
        alpha = np.array(frame.getchannel("A"))
        box = body_box(alpha)
        if box is None:
            return Image.new("RGBA", (width, height), (0, 0, 0, 0))

    x0, y0, x1, y1 = box
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    canvas.alpha_composite(frame, (center - (x0 + x1) // 2, bottom - y1))

    if floor > 0:
        data = np.array(canvas)
        data[floor:, :, 3] = 0
        canvas = Image.fromarray(data, "RGBA")
    return canvas


def encode(frames_dir: Path, output: Path, fps: float, crf: int) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg not found in PATH")
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg,
        "-y",
        "-v",
        "error",
        "-framerate",
        str(fps),
        "-i",
        str(frames_dir / "frame_%04d.png"),
        "-c:v",
        "libvpx-vp9",
        "-pix_fmt",
        "yuva420p",
        "-crf",
        str(crf),
        "-b:v",
        "0",
        "-row-mt",
        "1",
        "-cpu-used",
        "3",
        str(output),
    ]
    subprocess.run(command, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="directory of transparent PNG frames")
    parser.add_argument("--output", type=Path, required=True, help="output .webm path")
    parser.add_argument("--width", type=int, default=1366)
    parser.add_argument("--height", type=int, default=768)
    parser.add_argument("--fps", type=float, default=24.0)
    parser.add_argument("--crf", type=int, default=20)
    parser.add_argument("--head-width", type=int, default=311,
                        help="target head width in px; 0 uses the clip median")
    parser.add_argument("--bottom", type=int, default=671, help="target bottom of the body")
    parser.add_argument("--center", type=int, default=683, help="target horizontal centre")
    parser.add_argument("--floor", type=int, default=0, help="zero alpha below this y; 0 disables")
    args = parser.parse_args()

    frames = load_frames(args.input)
    widths = [w for frame in frames if (w := head_width(np.array(frame.getchannel("A"))))]
    target = args.head_width
    if target == 0:
        if not widths:
            raise SystemExit("could not measure head width; pass --head-width explicitly")
        target = int(np.median(widths))

    with tempfile.TemporaryDirectory(prefix="toon3d-") as tmp:
        out_dir = Path(tmp)
        for index, frame in enumerate(frames, 1):
            aligned = align_frame(
                frame, target, args.bottom, args.center, args.width, args.height, args.floor
            )
            aligned.save(out_dir / f"frame_{index:04d}.png")
        encode(out_dir, args.output, args.fps, args.crf)

    print(f"frames: {len(frames)}")
    print(f"head width: {target}px (source median: {int(np.median(widths)) if widths else 'n/a'}px)")
    print(f"output: {args.output} ({args.output.stat().st_size / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    main()
