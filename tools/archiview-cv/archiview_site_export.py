"""Экспорт современного фото для сайта (без tkinter — для copy_to_website.ps1)."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np


def parse_crop_rect(text: str) -> Optional[Tuple[float, float, float, float]]:
    clean = str(text or "").strip()
    if not clean:
        return None
    parts = [p.strip() for p in clean.replace(" ", "").split(",")]
    if len(parts) != 4:
        return None
    try:
        x0, y0, x1, y1 = (float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3]))
    except ValueError:
        return None
    if x0 > x1:
        x0, x1 = x1, x0
    if y0 > y1:
        y0, y1 = y1, y0
    if x1 - x0 < 8 or y1 - y0 < 8:
        return None
    return x0, y0, x1, y1


def apply_source_crop(img: np.ndarray, crop_text: str) -> Tuple[np.ndarray, Tuple[float, float]]:
    box = parse_crop_rect(crop_text)
    if box is None:
        return img, (0.0, 0.0)
    x0, y0, x1, y1 = box
    h, w = img.shape[:2]
    ix0 = max(0, min(w - 1, int(round(x0))))
    iy0 = max(0, min(h - 1, int(round(y0))))
    ix1 = max(ix0 + 1, min(w, int(round(x1))))
    iy1 = max(iy0 + 1, min(h, int(round(y1))))
    return img[iy0:iy1, ix0:ix1].copy(), (float(ix0), float(iy0))


def project_is_side_by_side(project: dict) -> bool:
    return str(project.get("labeling_layout") or "") == "side_by_side" or bool(project.get("no_rectification"))


def export_modern_source_for_site(outdir: Path, project: dict) -> Optional[Path]:
    if project_is_side_by_side(project):
        return None
    modern_src_path = Path(str(project.get("modern_image") or ""))
    if not modern_src_path.exists():
        return None
    modern_bgr = cv2.imread(str(modern_src_path), cv2.IMREAD_COLOR)
    if modern_bgr is None:
        return None
    crop_text = str(project.get("modern_crop_rect_text") or "")
    modern_bgr, _ = apply_source_crop(modern_bgr, crop_text)
    out_path = Path(outdir) / "11_modern_source_for_site.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(out_path), modern_bgr):
        return None
    return out_path


def export_modern_source_for_site_from_result(result_dir: str) -> int:
    outdir = Path(result_dir)
    project_path = outdir / "project_v8.json"
    if not project_path.exists():
        return 1
    project = json.loads(project_path.read_text(encoding="utf-8"))
    return 0 if export_modern_source_for_site(outdir, project) else 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: archiview_site_export.py <result_dir>", file=sys.stderr)
        sys.exit(2)
    sys.exit(export_modern_source_for_site_from_result(sys.argv[1]))
