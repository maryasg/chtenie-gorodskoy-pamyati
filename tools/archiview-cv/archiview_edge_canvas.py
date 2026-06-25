#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Edge-stretch canvas fill for Archiview time-layer exports (4200×2452)."""

from __future__ import annotations

from typing import Literal, Tuple

import numpy as np

try:
    import cv2 as cv
except Exception:  # pragma: no cover
    cv = None  # type: ignore[assignment]

TIME_LAYER_WIDTH = 4200
TIME_LAYER_HEIGHT = 2452

AlignMode = Literal["center", "top"]


def contain_fit_size(src_w: int, src_h: int, canvas_w: int, canvas_h: int) -> Tuple[int, int, float]:
    """Return fitted size and scale for image contained inside canvas."""
    if src_w <= 0 or src_h <= 0:
        raise ValueError("Source image size must be positive")
    scale = min(canvas_w / float(src_w), canvas_h / float(src_h))
    fit_w = max(1, int(round(src_w * scale)))
    fit_h = max(1, int(round(src_h * scale)))
    return fit_w, fit_h, scale


def placement_offset(
    canvas_w: int,
    canvas_h: int,
    fit_w: int,
    fit_h: int,
    align: AlignMode = "center",
) -> Tuple[int, int]:
    """Top-left placement of fitted image inside canvas."""
    x0 = (canvas_w - fit_w) // 2
    if align == "top":
        y0 = 0
    else:
        y0 = (canvas_h - fit_h) // 2
    return x0, y0


def edge_stretch_to_canvas(
    img: np.ndarray,
    canvas_w: int = TIME_LAYER_WIDTH,
    canvas_h: int = TIME_LAYER_HEIGHT,
    align: AlignMode = "center",
    corner_fill: Tuple[int, int, int] | None = None,
) -> np.ndarray:
    """Place image inside canvas and fill margins by repeating edge pixels.

  The photo is scaled down (never up) to fit inside the canvas while keeping aspect ratio.
  Empty margins are filled by extruding the nearest row/column of pixels, PastVu-style.
  Corner regions use the corresponding corner pixel; optional ``corner_fill`` colors areas
  that do not touch an image edge (e.g. bottom-right when align=top).
    """
    if cv is None:
        raise RuntimeError("OpenCV (cv2) is required for edge stretch")
    if img is None or img.size == 0:
        raise ValueError("Empty image")
    if canvas_w <= 0 or canvas_h <= 0:
        raise ValueError("Canvas size must be positive")

    src = img
    if src.ndim == 2:
        src = cv.cvtColor(src, cv.COLOR_GRAY2BGR)
    elif src.shape[2] == 4:
        src = cv.cvtColor(src, cv.COLOR_BGRA2BGR)

    h, w = src.shape[:2]
    fit_w, fit_h, scale = contain_fit_size(w, h, canvas_w, canvas_h)
    interp = cv.INTER_AREA if scale < 1.0 else cv.INTER_CUBIC
    resized = cv.resize(src, (fit_w, fit_h), interpolation=interp)

    x0, y0 = placement_offset(canvas_w, canvas_h, fit_w, fit_h, align=align)
    x1 = x0 + fit_w
    y1 = y0 + fit_h

    if corner_fill is None:
        canvas = np.empty((canvas_h, canvas_w, 3), dtype=resized.dtype)
    else:
        canvas = np.full((canvas_h, canvas_w, 3), corner_fill, dtype=resized.dtype)

    canvas[y0:y1, x0:x1] = resized

    # Core bands: repeat edge rows/columns next to the photo.
    if y0 > 0:
        canvas[0:y0, x0:x1] = resized[0:1, :, :]
    if y1 < canvas_h:
        canvas[y1:canvas_h, x0:x1] = resized[-1:, :, :]
    if x0 > 0:
        canvas[y0:y1, 0:x0] = resized[:, 0:1, :]
    if x1 < canvas_w:
        canvas[y0:y1, x1:canvas_w] = resized[:, -1:, :]

    # Corners: single-pixel extrusion where both margins meet.
    if y0 > 0 and x0 > 0:
        canvas[0:y0, 0:x0] = resized[0, 0]
    if y0 > 0 and x1 < canvas_w:
        canvas[0:y0, x1:canvas_w] = resized[0, -1]
    if y1 < canvas_h and x0 > 0:
        canvas[y1:canvas_h, 0:x0] = resized[-1, 0]
    if y1 < canvas_h and x1 < canvas_w:
        canvas[y1:canvas_h, x1:canvas_w] = resized[-1, -1]

    return canvas


def edge_stretch_summary(
    src_w: int,
    src_h: int,
    canvas_w: int = TIME_LAYER_WIDTH,
    canvas_h: int = TIME_LAYER_HEIGHT,
    align: AlignMode = "center",
) -> str:
    fit_w, fit_h, scale = contain_fit_size(src_w, src_h, canvas_w, canvas_h)
    x0, y0 = placement_offset(canvas_w, canvas_h, fit_w, fit_h, align=align)
    return (
        f"исходник {src_w}×{src_h} → вписано {fit_w}×{fit_h} (×{scale:.4f}), "
        f"положение ({x0}, {y0}), холст {canvas_w}×{canvas_h}"
    )


if __name__ == "__main__":
    sample = np.zeros((800, 1200, 3), dtype=np.uint8)
    sample[:, :400] = (40, 40, 40)
    sample[:, 400:800] = (180, 170, 160)
    sample[:, 800:] = (90, 90, 90)
    sample[0, :] = (255, 0, 0)
    sample[-1, :] = (0, 255, 0)
    sample[:, 0] = (0, 0, 255)
    sample[:, -1] = (255, 255, 0)
    out = edge_stretch_to_canvas(sample)
    assert out.shape == (TIME_LAYER_HEIGHT, TIME_LAYER_WIDTH, 3)
    assert np.array_equal(out[0, 2100], out[1, 2100])
    print(edge_stretch_summary(1200, 800))
    print("edge_stretch_to_canvas OK", out.shape)
