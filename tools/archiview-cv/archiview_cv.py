#!/usr/bin/env python3
"""
archiview_cv.py

OpenCV utility for two related photo tasks:
1) Straighten architectural photos so house/building verticals look upright.
2) Align a historical photo to a modern photo and export visual comparisons.

Install:
    pip install opencv-python numpy

Examples:
    python archiview_cv.py straighten house.jpg -o house_straight.jpg --debug house_lines.jpg
    python archiview_cv.py straighten house.jpg -o facade.jpg --points "120,80;900,110;860,1300;150,1280"
    python archiview_cv.py compare old.jpg modern.jpg -o comparison_results
"""

from __future__ import annotations

import argparse
import html
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

import numpy as np

try:
    import cv2 as cv
except Exception as exc:  # pragma: no cover - friendly CLI error
    print("OpenCV is not installed. Run: pip install opencv-python numpy", file=sys.stderr)
    raise


Point = Tuple[float, float]
Segment = Tuple[float, float, float, float, float, float]  # x1, y1, x2, y2, length, angle_deg


@dataclass
class AlignResult:
    homography: np.ndarray
    detector: str
    keypoints_old: int
    keypoints_new: int
    good_matches: int
    inliers: int
    inlier_ratio: float
    matches_debug: Optional[np.ndarray]


# ----------------------------- basic IO ----------------------------------

def read_image(path: str | Path) -> np.ndarray:
    """Read image safely on Windows, including paths with Cyrillic/Unicode letters.

    OpenCV's cv.imread() can fail on some Windows installations when the path
    contains non-Latin characters. Reading bytes through NumPy and then decoding
    with cv.imdecode() avoids that problem.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Could not read image: file does not exist: {path}")
    try:
        data = np.fromfile(str(path), dtype=np.uint8)
    except Exception as exc:
        raise FileNotFoundError(f"Could not read image bytes: {path}. Error: {exc}") from exc
    if data.size == 0:
        raise FileNotFoundError(f"Could not read image: file is empty or unavailable: {path}")
    img = cv.imdecode(data, cv.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Could not decode image: {path}")
    return img


def write_image(path: str | Path, img: np.ndarray) -> None:
    """Write image safely on Windows, including paths with Cyrillic/Unicode letters."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    ext = path.suffix.lower() or ".png"
    if ext == ".jpg":
        ext = ".jpeg"
    ok, encoded = cv.imencode(ext, img)
    if not ok:
        raise IOError(f"Could not encode image for writing: {path}")
    try:
        encoded.tofile(str(path))
    except Exception as exc:
        raise IOError(f"Could not write image: {path}. Error: {exc}") from exc


def resize_max(img: np.ndarray, max_dim: int) -> Tuple[np.ndarray, float]:
    h, w = img.shape[:2]
    longest = max(h, w)
    if max_dim <= 0 or longest <= max_dim:
        return img.copy(), 1.0
    scale = max_dim / float(longest)
    resized = cv.resize(img, (int(round(w * scale)), int(round(h * scale))), interpolation=cv.INTER_AREA)
    return resized, scale


def to_gray(img: np.ndarray) -> np.ndarray:
    if img.ndim == 2:
        return img
    return cv.cvtColor(img, cv.COLOR_BGR2GRAY)


def ensure_bgr(img: np.ndarray) -> np.ndarray:
    if img.ndim == 2:
        return cv.cvtColor(img, cv.COLOR_GRAY2BGR)
    return img


def clahe_gray(img: np.ndarray, clip_limit: float = 2.0, tile_grid_size: int = 8) -> np.ndarray:
    gray = to_gray(img)
    clahe = cv.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile_grid_size, tile_grid_size))
    return clahe.apply(gray)


# ---------------------- architectural vertical correction -----------------

def line_angle_deg(x1: float, y1: float, x2: float, y2: float) -> float:
    angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
    angle = angle % 180.0
    return angle


def weighted_median(values: Sequence[float], weights: Sequence[float]) -> float:
    if len(values) == 0:
        raise ValueError("weighted_median needs at least one value")
    values_np = np.asarray(values, dtype=np.float64)
    weights_np = np.asarray(weights, dtype=np.float64)
    order = np.argsort(values_np)
    values_np = values_np[order]
    weights_np = weights_np[order]
    cumulative = np.cumsum(weights_np)
    cutoff = 0.5 * np.sum(weights_np)
    return float(values_np[np.searchsorted(cumulative, cutoff)])


def detect_line_segments(
    img: np.ndarray,
    max_dim: int = 1800,
    canny_low: int = 50,
    canny_high: int = 160,
    hough_threshold: int = 70,
    min_len_frac: float = 0.06,
    max_gap_frac: float = 0.015,
) -> Tuple[List[Segment], np.ndarray]:
    """Detect line segments and return them in original image coordinates."""
    small, scale = resize_max(img, max_dim)
    gray = clahe_gray(small)
    gray = cv.GaussianBlur(gray, (5, 5), 0)
    edges = cv.Canny(gray, canny_low, canny_high, apertureSize=3)

    h, w = small.shape[:2]
    min_len = max(20, int(min(h, w) * min_len_frac))
    max_gap = max(5, int(min(h, w) * max_gap_frac))

    lines = cv.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180.0,
        threshold=hough_threshold,
        minLineLength=min_len,
        maxLineGap=max_gap,
    )

    segments: List[Segment] = []
    if lines is None:
        return segments, edges

    inv_scale = 1.0 / scale
    for line in lines[:, 0, :]:
        x1, y1, x2, y2 = [float(v) * inv_scale for v in line]
        length = math.hypot(x2 - x1, y2 - y1)
        if length < 8:
            continue
        angle = line_angle_deg(x1, y1, x2, y2)
        segments.append((x1, y1, x2, y2, length, angle))
    return segments, edges


def filter_vertical_segments(segments: Iterable[Segment], tolerance_deg: float = 35.0) -> List[Segment]:
    vertical: List[Segment] = []
    for seg in segments:
        angle = seg[5]
        if abs(angle - 90.0) <= tolerance_deg:
            vertical.append(seg)
    return vertical


def rotate_bound(img: np.ndarray, angle_deg: float, border_mode: int = cv.BORDER_REPLICATE) -> Tuple[np.ndarray, np.ndarray]:
    h, w = img.shape[:2]
    center = (w / 2.0, h / 2.0)
    mat = cv.getRotationMatrix2D(center, angle_deg, 1.0)
    cos = abs(mat[0, 0])
    sin = abs(mat[0, 1])
    new_w = int((h * sin) + (w * cos))
    new_h = int((h * cos) + (w * sin))
    mat[0, 2] += new_w / 2.0 - center[0]
    mat[1, 2] += new_h / 2.0 - center[1]
    rotated = cv.warpAffine(img, mat, (new_w, new_h), flags=cv.INTER_CUBIC, borderMode=border_mode)
    h3 = np.eye(3, dtype=np.float64)
    h3[:2, :] = mat
    return rotated, h3


def segment_to_line(seg: Segment) -> np.ndarray:
    x1, y1, x2, y2, *_ = seg
    p1 = np.array([x1, y1, 1.0], dtype=np.float64)
    p2 = np.array([x2, y2, 1.0], dtype=np.float64)
    line = np.cross(p1, p2)
    norm = math.hypot(line[0], line[1])
    if norm == 0:
        return line
    return line / norm


def estimate_vanishing_point(segments: Sequence[Segment]) -> Optional[Tuple[float, float, float]]:
    """Least-squares intersection of line segments in homogeneous coordinates.

    Returns (x, y, w). If abs(w) is tiny, the vanishing point is effectively at infinity.
    """
    if len(segments) < 4:
        return None
    rows = []
    for seg in segments:
        line = segment_to_line(seg)
        if not np.all(np.isfinite(line)):
            continue
        weight = math.sqrt(max(seg[4], 1.0))
        rows.append(line * weight)
    if len(rows) < 4:
        return None
    L = np.vstack(rows)
    try:
        _, _, vt = np.linalg.svd(L)
    except np.linalg.LinAlgError:
        return None
    vp = vt[-1, :]
    if not np.all(np.isfinite(vp)):
        return None
    return float(vp[0]), float(vp[1]), float(vp[2])


def warp_perspective_bounds(
    img: np.ndarray,
    H: np.ndarray,
    max_expand: float = 3.0,
    border_mode: int = cv.BORDER_REPLICATE,
) -> Tuple[np.ndarray, np.ndarray]:
    h, w = img.shape[:2]
    corners = np.array([[0, 0, 1], [w, 0, 1], [w, h, 1], [0, h, 1]], dtype=np.float64).T
    tc = H @ corners
    if np.any(np.abs(tc[2, :]) < 1e-8):
        raise ValueError("Perspective warp is too strong: a transformed corner is near infinity")
    pts = (tc[:2, :] / tc[2, :]).T
    min_xy = np.floor(pts.min(axis=0)).astype(int)
    max_xy = np.ceil(pts.max(axis=0)).astype(int)
    new_w = int(max_xy[0] - min_xy[0])
    new_h = int(max_xy[1] - min_xy[1])
    if new_w <= 0 or new_h <= 0:
        raise ValueError("Perspective warp produced invalid output size")
    if new_w > int(w * max_expand) or new_h > int(h * max_expand):
        raise ValueError(
            f"Perspective warp would expand image too much ({new_w}x{new_h}); lower --strength"
        )
    shift = np.array([[1.0, 0.0, -float(min_xy[0])], [0.0, 1.0, -float(min_xy[1])], [0.0, 0.0, 1.0]])
    H2 = shift @ H
    warped = cv.warpPerspective(img, H2, (new_w, new_h), flags=cv.INTER_CUBIC, borderMode=border_mode)
    return warped, H2


def rectify_vertical_perspective(
    img: np.ndarray,
    vp_homogeneous: Tuple[float, float, float],
    strength: float = 0.9,
    max_expand: float = 3.0,
) -> Tuple[np.ndarray, np.ndarray, str]:
    """Projective correction that sends the vertical vanishing point toward infinity."""
    h, w = img.shape[:2]
    vx, vy, vw = vp_homogeneous
    if abs(vw) < 1e-8:
        return img.copy(), np.eye(3), "vertical lines are already close to parallel"

    vp = np.array([vx / vw, vy / vw, 1.0], dtype=np.float64)
    max_dim = float(max(w, h))
    cx, cy = w / 2.0, h / 2.0
    T = np.array([[1 / max_dim, 0, -cx / max_dim], [0, 1 / max_dim, -cy / max_dim], [0, 0, 1]], dtype=np.float64)
    Ti = np.array([[max_dim, 0, cx], [0, max_dim, cy], [0, 0, 1]], dtype=np.float64)

    vpn = T @ vp
    if abs(vpn[2]) < 1e-8:
        return img.copy(), np.eye(3), "vanishing point is numerically at infinity"
    vpn = vpn / vpn[2]
    # y coordinate of the vertical vanishing point in normalized, centered coordinates.
    y_vp = float(vpn[1])
    if abs(y_vp) < 0.30:
        return img.copy(), np.eye(3), "vanishing point is too close to image center; skipping risky warp"
    if max(abs(float(vpn[0])), abs(y_vp)) > 80:
        return img.copy(), np.eye(3), "vanishing point is very far away; perspective correction is unnecessary"

    # Try requested strength first, then back off if the bounding box explodes.
    candidates = [strength, 0.75 * strength, 0.5 * strength, 0.35 * strength]
    last_error = ""
    for s in candidates:
        if s <= 0:
            continue
        Hn = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, -float(s) / y_vp, 1.0]], dtype=np.float64)
        H = Ti @ Hn @ T
        try:
            warped, H2 = warp_perspective_bounds(img, H, max_expand=max_expand)
            return warped, H2, f"applied projective vertical correction, strength={s:.3f}"
        except ValueError as exc:
            last_error = str(exc)
            continue
    return img.copy(), np.eye(3), f"skipped perspective correction: {last_error or 'warp unstable'}"


def draw_line_debug(
    img: np.ndarray,
    all_segments: Sequence[Segment],
    vertical_segments: Sequence[Segment],
    vp: Optional[Tuple[float, float, float]] = None,
) -> np.ndarray:
    out = ensure_bgr(img.copy())
    # Thin gray-ish lines for all segments, brighter lines for selected verticals.
    for x1, y1, x2, y2, *_ in all_segments[:600]:
        cv.line(out, (int(x1), int(y1)), (int(x2), int(y2)), (160, 160, 160), 1, cv.LINE_AA)
    for x1, y1, x2, y2, *_ in vertical_segments[:400]:
        cv.line(out, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 2, cv.LINE_AA)
    if vp is not None and abs(vp[2]) > 1e-8:
        x, y = vp[0] / vp[2], vp[1] / vp[2]
        if -out.shape[1] <= x <= 2 * out.shape[1] and -out.shape[0] <= y <= 2 * out.shape[0]:
            cv.drawMarker(out, (int(x), int(y)), (255, 0, 0), markerType=cv.MARKER_CROSS, markerSize=30, thickness=2)
    return out


def parse_four_points(text: str) -> np.ndarray:
    """Parse 'x1,y1;x2,y2;x3,y3;x4,y4' as TL, TR, BR, BL."""
    clean = text.replace(" ", "")
    parts = [p for p in clean.replace("|", ";").split(";") if p]
    if len(parts) != 4:
        raise ValueError('Expected four points: "x1,y1;x2,y2;x3,y3;x4,y4" in order TL,TR,BR,BL')
    pts = []
    for p in parts:
        xy = p.split(",")
        if len(xy) != 2:
            raise ValueError(f"Bad point: {p}")
        pts.append((float(xy[0]), float(xy[1])))
    return np.array(pts, dtype=np.float32)


def manual_perspective_rectify(img: np.ndarray, points_tl_tr_br_bl: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    pts = points_tl_tr_br_bl.astype(np.float32)
    tl, tr, br, bl = pts
    width_top = np.linalg.norm(tr - tl)
    width_bottom = np.linalg.norm(br - bl)
    height_left = np.linalg.norm(bl - tl)
    height_right = np.linalg.norm(br - tr)
    out_w = max(2, int(round(max(width_top, width_bottom))))
    out_h = max(2, int(round(max(height_left, height_right))))
    dst = np.array([[0, 0], [out_w - 1, 0], [out_w - 1, out_h - 1], [0, out_h - 1]], dtype=np.float32)
    H = cv.getPerspectiveTransform(pts, dst)
    warped = cv.warpPerspective(img, H, (out_w, out_h), flags=cv.INTER_CUBIC, borderMode=cv.BORDER_REPLICATE)
    return warped, H


def straighten_image(args: argparse.Namespace) -> int:
    img = read_image(args.input)

    if args.points:
        points = parse_four_points(args.points)
        out, H = manual_perspective_rectify(img, points)
        write_image(args.output, out)
        if args.report:
            report = {"mode": "manual_points", "points_tl_tr_br_bl": points.tolist(), "homography": H.tolist()}
            Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Saved manual perspective correction: {args.output}")
        return 0

    segments, _edges = detect_line_segments(
        img,
        max_dim=args.process_max_dim,
        canny_low=args.canny_low,
        canny_high=args.canny_high,
        hough_threshold=args.hough_threshold,
        min_len_frac=args.min_len_frac,
        max_gap_frac=args.max_gap_frac,
    )
    vertical = filter_vertical_segments(segments, tolerance_deg=args.vertical_tolerance)
    if len(vertical) < args.min_vertical_lines:
        write_image(args.output, img)
        if args.debug:
            write_image(args.debug, draw_line_debug(img, segments, vertical, None))
        print(
            f"Only {len(vertical)} vertical-ish lines found; saved original image. "
            f"Try --points for reliable facade rectification or lower --min-vertical-lines.",
            file=sys.stderr,
        )
        return 2

    angles = [seg[5] for seg in vertical]
    weights = [seg[4] for seg in vertical]
    median_angle = weighted_median(angles, weights)
    roll_correction = 90.0 - median_angle
    if abs(roll_correction) > args.max_roll_correction:
        roll_correction = 0.0

    rotated = img.copy()
    H_total = np.eye(3, dtype=np.float64)
    if abs(roll_correction) >= args.min_roll_correction:
        rotated, H_roll = rotate_bound(img, roll_correction)
        H_total = H_roll @ H_total

    perspective_reason = "not requested"
    rectified = rotated
    H_persp = np.eye(3, dtype=np.float64)
    vp = None

    if not args.no_perspective:
        seg2, _ = detect_line_segments(
            rotated,
            max_dim=args.process_max_dim,
            canny_low=args.canny_low,
            canny_high=args.canny_high,
            hough_threshold=args.hough_threshold,
            min_len_frac=args.min_len_frac,
            max_gap_frac=args.max_gap_frac,
        )
        vert2 = filter_vertical_segments(seg2, tolerance_deg=args.vertical_tolerance)
        vp = estimate_vanishing_point(vert2)
        if vp is not None:
            rectified, H_persp, perspective_reason = rectify_vertical_perspective(
                rotated, vp, strength=args.strength, max_expand=args.max_expand
            )
            H_total = H_persp @ H_total
        else:
            perspective_reason = "not enough stable vertical lines for vanishing point"

    # Final tiny roll cleanup, because the projective transform can introduce a residual tilt.
    if args.final_cleanup:
        seg3, _ = detect_line_segments(rectified, max_dim=args.process_max_dim)
        vert3 = filter_vertical_segments(seg3, tolerance_deg=25.0)
        if len(vert3) >= args.min_vertical_lines:
            angle3 = weighted_median([s[5] for s in vert3], [s[4] for s in vert3])
            cleanup_angle = 90.0 - angle3
            if 0.15 <= abs(cleanup_angle) <= 4.0:
                rectified, H_cleanup = rotate_bound(rectified, cleanup_angle)
                H_total = H_cleanup @ H_total

    write_image(args.output, rectified)

    if args.debug:
        # Debug view is for the original detection stage.
        debug_img = draw_line_debug(img, segments, vertical, None)
        write_image(args.debug, debug_img)

    if args.report:
        report = {
            "mode": "auto",
            "output": str(args.output),
            "segments_found": len(segments),
            "vertical_segments_used": len(vertical),
            "weighted_median_vertical_angle_deg": median_angle,
            "roll_correction_deg": roll_correction,
            "perspective": perspective_reason,
            "homography_total": H_total.tolist(),
        }
        Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Saved straightened image: {args.output}")
    print(f"Detected vertical segments: {len(vertical)}; roll correction: {roll_correction:.2f} deg")
    print(f"Perspective step: {perspective_reason}")
    return 0


# ---------------------- historic/modern image comparison ------------------

def make_detector(name: str, nfeatures: int):
    name = name.lower()
    if name == "sift":
        if not hasattr(cv, "SIFT_create"):
            raise RuntimeError("SIFT is not available in this OpenCV build")
        return cv.SIFT_create(nfeatures=max(0, nfeatures)), cv.NORM_L2, name
    if name == "orb":
        return cv.ORB_create(nfeatures=nfeatures, fastThreshold=7), cv.NORM_HAMMING, name
    if name == "akaze":
        return cv.AKAZE_create(), cv.NORM_HAMMING, name
    raise ValueError(f"Unknown detector: {name}")


def detector_order(requested: str) -> List[str]:
    if requested != "auto":
        return [requested]
    # SIFT often handles historical/modern contrast and scale changes better; ORB/AKAZE are fallbacks.
    order = []
    if hasattr(cv, "SIFT_create"):
        order.append("sift")
    order.extend(["orb", "akaze"])
    return order


def feature_gray(img: np.ndarray) -> np.ndarray:
    gray = clahe_gray(img, clip_limit=2.0, tile_grid_size=8)
    return cv.GaussianBlur(gray, (3, 3), 0)



def validate_homography_geometry(
    H: np.ndarray,
    old_shape: Tuple[int, int] | Tuple[int, int, int],
    new_shape: Tuple[int, int] | Tuple[int, int, int],
    min_area_ratio: float = 0.005,
    max_area_ratio: float = 30.0,
) -> Tuple[bool, str]:
    """Reject degenerate homographies, a common issue with repetitive facades/windows."""
    h_old, w_old = old_shape[:2]
    h_new, w_new = new_shape[:2]
    corners = np.array([[0, 0, 1], [w_old, 0, 1], [w_old, h_old, 1], [0, h_old, 1]], dtype=np.float64).T
    tc = H @ corners
    if np.any(~np.isfinite(tc)) or np.any(np.abs(tc[2, :]) < 1e-8):
        return False, "transformed image corners are not finite"
    pts = (tc[:2, :] / tc[2, :]).T.astype(np.float32)
    if np.any(~np.isfinite(pts)):
        return False, "transformed corner coordinates are not finite"
    area = abs(float(cv.contourArea(pts)))
    new_area = float(max(1, w_new * h_new))
    area_ratio = area / new_area
    if area_ratio < min_area_ratio:
        return False, f"transformed old image is nearly collapsed; area ratio={area_ratio:.6f}"
    if area_ratio > max_area_ratio:
        return False, f"transformed old image is implausibly huge; area ratio={area_ratio:.3f}"
    sides = [np.linalg.norm(pts[(i + 1) % 4] - pts[i]) for i in range(4)]
    if min(sides) < 0.02 * min(w_new, h_new):
        return False, "one transformed side is too short"
    # The mapped center should not be absurdly far from the reference frame.
    center = np.array([[[w_old / 2.0, h_old / 2.0]]], dtype=np.float32)
    mapped_center = cv.perspectiveTransform(center, H)[0, 0]
    if not (-2 * w_new <= mapped_center[0] <= 3 * w_new and -2 * h_new <= mapped_center[1] <= 3 * h_new):
        return False, "mapped old-image center is far outside the modern image"
    return True, f"area ratio={area_ratio:.3f}"

def align_with_detector(
    old_img: np.ndarray,
    new_img: np.ndarray,
    detector_name: str,
    nfeatures: int,
    ratio: float,
    reproj_thresh: float,
    resize_dim: int,
    min_matches: int,
) -> AlignResult:
    old_small, s_old = resize_max(old_img, resize_dim)
    new_small, s_new = resize_max(new_img, resize_dim)
    g_old = feature_gray(old_small)
    g_new = feature_gray(new_small)

    detector, norm, det_name = make_detector(detector_name, nfeatures)
    kp_old, des_old = detector.detectAndCompute(g_old, None)
    kp_new, des_new = detector.detectAndCompute(g_new, None)

    if des_old is None or des_new is None or len(kp_old) < 4 or len(kp_new) < 4:
        raise RuntimeError(f"{det_name}: not enough keypoints")

    matcher = cv.BFMatcher(norm, crossCheck=False)
    raw = matcher.knnMatch(des_old, des_new, k=2)
    good = []
    for pair in raw:
        if len(pair) < 2:
            continue
        m, n = pair
        if m.distance < ratio * n.distance:
            good.append(m)

    if len(good) < min_matches:
        raise RuntimeError(f"{det_name}: not enough good matches ({len(good)} < {min_matches})")

    src_small = np.float32([kp_old[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst_small = np.float32([kp_new[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
    H_small, mask = cv.findHomography(src_small, dst_small, cv.RANSAC, reproj_thresh)
    if H_small is None or mask is None:
        raise RuntimeError(f"{det_name}: homography failed")

    mask_flat = mask.ravel().astype(bool)
    inliers = int(mask_flat.sum())
    if inliers < max(8, min_matches // 2):
        raise RuntimeError(f"{det_name}: too few inliers ({inliers})")

    # Convert homography from resized coordinates to original coordinates.
    S_old = np.array([[s_old, 0, 0], [0, s_old, 0], [0, 0, 1]], dtype=np.float64)
    S_new = np.array([[s_new, 0, 0], [0, s_new, 0], [0, 0, 1]], dtype=np.float64)
    H_orig = np.linalg.inv(S_new) @ H_small @ S_old
    H_orig = H_orig / H_orig[2, 2]

    ok, geometry_reason = validate_homography_geometry(H_orig, old_img.shape, new_img.shape)
    if not ok:
        raise RuntimeError(f"{det_name}: rejected bad homography ({geometry_reason})")

    inlier_matches = [m for m, keep in zip(good, mask_flat) if keep]
    shown = inlier_matches[:120]
    matches_debug = cv.drawMatches(
        old_small,
        kp_old,
        new_small,
        kp_new,
        shown,
        None,
        flags=cv.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS,
    )

    return AlignResult(
        homography=H_orig,
        detector=det_name,
        keypoints_old=len(kp_old),
        keypoints_new=len(kp_new),
        good_matches=len(good),
        inliers=inliers,
        inlier_ratio=float(inliers) / max(1, len(good)),
        matches_debug=matches_debug,
    )



def parse_points_list(text: str, label: str) -> np.ndarray:
    clean = text.replace(" ", "")
    parts = [p for p in clean.replace("|", ";").split(";") if p]
    if len(parts) < 4:
        raise ValueError(f'{label}: expected at least four points: "x1,y1;x2,y2;x3,y3;x4,y4"')
    pts = []
    for p in parts:
        xy = p.split(",")
        if len(xy) != 2:
            raise ValueError(f"{label}: bad point: {p}")
        pts.append((float(xy[0]), float(xy[1])))
    return np.array(pts, dtype=np.float32).reshape(-1, 1, 2)


def align_from_manual_points(args: argparse.Namespace, old_img: np.ndarray, new_img: np.ndarray) -> AlignResult:
    if not (args.points_old and args.points_new):
        raise ValueError("Use both --points-old and --points-new")
    pts_old = parse_points_list(args.points_old, "points-old")
    pts_new = parse_points_list(args.points_new, "points-new")
    if len(pts_old) != len(pts_new):
        raise ValueError("--points-old and --points-new must contain the same number of points")
    H, mask = cv.findHomography(pts_old, pts_new, cv.RANSAC, args.ransac_thresh)
    if H is None:
        raise RuntimeError("Manual-point homography failed")
    H = H / H[2, 2]
    ok, reason = validate_homography_geometry(H, old_img.shape, new_img.shape, min_area_ratio=0.001, max_area_ratio=50.0)
    if not ok:
        raise RuntimeError(f"Manual points produced bad homography ({reason})")
    inliers = int(mask.sum()) if mask is not None else len(pts_old)
    return AlignResult(
        homography=H,
        detector="manual_points",
        keypoints_old=0,
        keypoints_new=0,
        good_matches=len(pts_old),
        inliers=inliers,
        inlier_ratio=float(inliers) / max(1, len(pts_old)),
        matches_debug=None,
    )

def align_historic_to_modern(args: argparse.Namespace, old_img: np.ndarray, new_img: np.ndarray) -> AlignResult:
    if args.points_old or args.points_new:
        return align_from_manual_points(args, old_img, new_img)

    errors = []
    best: Optional[AlignResult] = None
    for det in detector_order(args.detector):
        try:
            result = align_with_detector(
                old_img=old_img,
                new_img=new_img,
                detector_name=det,
                nfeatures=args.max_features,
                ratio=args.ratio,
                reproj_thresh=args.ransac_thresh,
                resize_dim=args.align_max_dim,
                min_matches=args.min_matches,
            )
            if best is None or result.inliers > best.inliers:
                best = result
            # Good enough: stop early.
            if result.inliers >= args.min_inliers and result.inlier_ratio >= args.min_inlier_ratio:
                return result
        except Exception as exc:
            errors.append(str(exc))
    if best is not None and best.inliers >= max(8, args.min_inliers // 2):
        return best
    raise RuntimeError("Could not align images. Details: " + " | ".join(errors))


def normalize_for_difference(gray: np.ndarray, valid_mask: np.ndarray) -> np.ndarray:
    out = gray.copy().astype(np.uint8)
    valid = valid_mask > 0
    if np.count_nonzero(valid) < 100:
        return out
    vals = out[valid]
    lo, hi = np.percentile(vals, [1, 99])
    if hi <= lo + 1e-6:
        return out
    out = np.clip((out.astype(np.float32) - lo) * 255.0 / (hi - lo), 0, 255).astype(np.uint8)
    return out


def clamp_float(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


def opacity_to_01(value: float) -> float:
    """Accept either 0..1 or 0..100 opacity and return 0..1."""
    value = float(value)
    if value > 1.0:
        value = value / 100.0
    return clamp_float(value, 0.0, 1.0)




def make_aligned_old_transparent(old_bgr: np.ndarray, valid_mask: np.ndarray) -> np.ndarray:
    """Return BGRA historical layer with transparent pixels outside the warped old photo."""
    bgra = cv.cvtColor(ensure_bgr(old_bgr), cv.COLOR_BGR2BGRA)
    bgra[:, :, 3] = np.where(valid_mask, 255, 0).astype(np.uint8)
    return bgra


def write_overlay_slider_html(outdir: Path, default_old_opacity: float) -> Path:
    """Create a local browser viewer where the old-photo opacity can be changed after processing."""
    default_percent = int(round(opacity_to_01(default_old_opacity) * 100.0))
    modern = html.escape("modern_reference.png")
    old = html.escape("aligned_historical_transparent.png")
    text = f'''<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>Archiview CV — overlay с ползунком</title>
<style>
  body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; color: #222; }}
  .panel {{ max-width: 1200px; margin: 0 auto; }}
  .controls {{ background: white; padding: 14px 16px; border-radius: 10px; margin-bottom: 14px; box-shadow: 0 2px 10px rgba(0,0,0,.08); }}
  .wrap {{ position: relative; display: inline-block; max-width: 100%; background: #ddd; box-shadow: 0 2px 14px rgba(0,0,0,.18); }}
  .wrap img {{ display: block; max-width: 100%; height: auto; }}
  #oldLayer {{ position: absolute; left: 0; top: 0; opacity: {default_percent / 100.0:.2f}; pointer-events: none; }}
  input[type=range] {{ width: min(680px, 95vw); }}
  .hint {{ color: #555; font-size: 14px; line-height: 1.35; }}
</style>
</head>
<body>
<div class="panel">
  <h2>Overlay: историческое фото поверх современного</h2>
  <div class="controls">
    <label for="opacity"><b>Видимость исторического фото:</b> <span id="value">{default_percent}</span>%</label><br>
    <input id="opacity" type="range" min="0" max="100" value="{default_percent}">
    <p class="hint">0% — видно только современное фото. 100% — видно только выровненное историческое фото. Это окно можно открыть двойным кликом по файлу overlay_slider.html.</p>
  </div>
  <div class="wrap">
    <img id="modernLayer" src="{modern}" alt="Современное фото">
    <img id="oldLayer" src="{old}" alt="Историческое фото">
  </div>
</div>
<script>
const slider = document.getElementById('opacity');
const value = document.getElementById('value');
const oldLayer = document.getElementById('oldLayer');
slider.addEventListener('input', () => {{
  value.textContent = slider.value;
  oldLayer.style.opacity = Number(slider.value) / 100;
}});
</script>
</body>
</html>
'''
    path = outdir / "overlay_slider.html"
    path.write_text(text, encoding="utf-8")
    return path


def write_result_guide(outdir: Path, old_opacity: float) -> Path:
    text = f"""Как читать результаты Archiview CV

1) overlay_slider.html
   Самый удобный файл. Откройте его двойным кликом в браузере и двигайте ползунок.
   Сейчас обычный overlay.png сохранён с видимостью исторического фото примерно {int(round(opacity_to_01(old_opacity) * 100))}%.

2) overlay.png
   Историческое фото выровнено и наложено на современное. Смотрите по нему, хорошо ли совпали окна, крыша, углы фасада.

3) probable_added_on_modern.png
   Оранжевые области — вероятные элементы, которые видны на современном фото, но не подтверждаются старым: надстройки,
   новые окна, пристройки, новые крупные детали фасада. Это подсказка, а не окончательная экспертиза.

4) changes_on_modern.png
   Красные линии — все крупные отличия после совмещения. Это НЕ обязательно «добавлено»: туда могут попасть тени,
   деревья, машины, люди, освещение, шум старой фотографии и ошибки совмещения.

5) difference_heat_overlay.png
   Тепловая карта отличий. Чем сильнее цветовой/контрастный сигнал, тем сильнее отличается участок.

6) aligned_historical.png
   Историческое фото, растянутое в координаты современного.

7) side_by_side.png
   Несколько основных вариантов рядом для общего просмотра.

Лучший порядок работы: overlay_slider.html → probable_added_on_modern.png → overlay.png → aligned_historical.png.
"""
    path = outdir / "КАК_ЧИТАТЬ_РЕЗУЛЬТАТЫ.txt"
    path.write_text(text, encoding="utf-8")
    return path

def filter_contours_by_area(mask: np.ndarray, min_area: float) -> List[np.ndarray]:
    contours, _hier = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    return [c for c in contours if cv.contourArea(c) >= float(min_area)]


def make_directional_change_masks(
    old_gray: np.ndarray,
    new_gray: np.ndarray,
    diff_norm: np.ndarray,
    valid: np.ndarray,
    sensitivity: float = 55.0,
    morph_kernel: int = 5,
) -> Tuple[np.ndarray, np.ndarray]:
    """Estimate directional changes after alignment.

    The output is intentionally conservative computer-vision evidence, not a
    semantic architectural judgment. The added mask means: modern-image edges
    and details that have no nearby edge in the aligned historical image. The
    removed mask is the reverse.
    """
    sensitivity = clamp_float(float(sensitivity), 0.0, 100.0)
    valid_u8 = (valid.astype(np.uint8) * 255)
    if np.count_nonzero(valid) < 100:
        z = np.zeros_like(valid_u8)
        return z, z

    # Crop a few pixels off the valid area; otherwise the warped historical
    # border can look like a false architectural change.
    edge_guard_kernel = cv.getStructuringElement(cv.MORPH_RECT, (5, 5))
    valid_inner = cv.erode(valid_u8, edge_guard_kernel, iterations=1) > 0

    old_blur = cv.GaussianBlur(old_gray, (5, 5), 0)
    new_blur = cv.GaussianBlur(new_gray, (5, 5), 0)

    # After CLAHE/normalization, fixed Canny thresholds work reasonably and are
    # easier to explain than a highly tuned adaptive model.
    old_edges = cv.Canny(old_blur, 55, 155)
    new_edges = cv.Canny(new_blur, 55, 155)
    old_edges[~valid_inner] = 0
    new_edges[~valid_inner] = 0

    # Low sensitivity: allow a wider tolerance around old/new edges.
    # High sensitivity: require less tolerance, so more modern-only details pass.
    tolerance_size = int(round(9 - 0.05 * sensitivity))
    tolerance_size = max(3, min(11, tolerance_size)) | 1
    tol_kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (tolerance_size, tolerance_size))

    old_near = cv.dilate(old_edges, tol_kernel, iterations=1)
    new_near = cv.dilate(new_edges, tol_kernel, iterations=1)

    vals = diff_norm[valid_inner]
    if vals.size == 0:
        z = np.zeros_like(valid_u8)
        return z, z

    # Sensitivity controls how strong a difference must be before it gets grouped.
    # 0 -> only the strongest differences; 100 -> many weaker differences too.
    percentile = 96.0 - 0.20 * sensitivity
    gate = float(np.percentile(vals, percentile))
    gate = max(22.0, min(185.0, gate))
    different_enough = diff_norm >= gate

    added = ((new_edges > 0) & (old_near == 0) & different_enough & valid_inner).astype(np.uint8) * 255
    removed = ((old_edges > 0) & (new_near == 0) & different_enough & valid_inner).astype(np.uint8) * 255

    k = max(3, int(morph_kernel) | 1)
    connect_kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (k, k))
    group_kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (max(5, k * 2 - 1), max(5, k * 2 - 1)))

    def group(mask: np.ndarray) -> np.ndarray:
        mask = cv.dilate(mask, connect_kernel, iterations=2)
        mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, group_kernel)
        mask = cv.morphologyEx(mask, cv.MORPH_OPEN, connect_kernel)
        mask[~valid_inner] = 0
        return mask

    return group(added), group(removed)


def make_side_by_side(images: Sequence[np.ndarray], labels: Sequence[str]) -> np.ndarray:
    bgrs = [ensure_bgr(img) for img in images]
    target_h = min(900, max(img.shape[0] for img in bgrs))
    resized = []
    for img in bgrs:
        h, w = img.shape[:2]
        scale = target_h / float(h)
        resized_img = cv.resize(img, (int(round(w * scale)), target_h), interpolation=cv.INTER_AREA)
        resized.append(resized_img)
    gap = 12
    label_h = 42
    total_w = sum(img.shape[1] for img in resized) + gap * (len(resized) - 1)
    canvas = np.full((target_h + label_h, total_w, 3), 255, dtype=np.uint8)
    x = 0
    for img, label in zip(resized, labels):
        canvas[label_h:, x : x + img.shape[1]] = img
        cv.putText(canvas, label, (x + 10, 28), cv.FONT_HERSHEY_SIMPLEX, 0.8, (20, 20, 20), 2, cv.LINE_AA)
        x += img.shape[1] + gap
    return canvas




@dataclass
class ChangeZone:
    index: int
    kind: str
    x: int
    y: int
    w: int
    h: int
    contour_area: float
    bbox_area: int


def large_level_to_ratio(level: int) -> float:
    """Map 1..10 to minimum meaningful zone size as image-area ratio."""
    table = {
        1: 0.00004,
        2: 0.00007,
        3: 0.00011,
        4: 0.00018,
        5: 0.00030,
        6: 0.00048,
        7: 0.00075,
        8: 0.00115,
        9: 0.00175,
        10: 0.00260,
    }
    level = max(1, min(10, int(level)))
    return table[level]


def build_large_zone_mask(
    mask: np.ndarray,
    image_shape: Tuple[int, int, int] | Tuple[int, int],
    kind: str,
    large_level: int = 6,
    top_n: int = 10,
    group_close: bool = True,
    min_area_override: float = 0.0,
) -> Tuple[np.ndarray, List[np.ndarray], List[ChangeZone]]:
    """Convert a noisy pixel/edge mask into a small list of large zones.

    The purpose is not to mark every changed line, but to keep only large
    architectural-looking regions that are worth a human checking.
    """
    img_h, img_w = image_shape[:2]
    image_area = float(max(1, img_h * img_w))
    level = max(1, min(10, int(large_level)))
    ratio = large_level_to_ratio(level)

    work = (mask > 0).astype(np.uint8) * 255
    if np.count_nonzero(work) == 0:
        return work, [], []

    if group_close:
        # Join broken edge fragments belonging to the same window row / floor / added volume.
        base = min(img_h, img_w)
        group_px = int(round(base * (0.006 + level * 0.0012)))
        group_px = max(7, min(95, group_px)) | 1
        close_px = max(9, int(group_px * 1.7)) | 1
        k_group = cv.getStructuringElement(cv.MORPH_ELLIPSE, (group_px, group_px))
        k_close = cv.getStructuringElement(cv.MORPH_ELLIPSE, (close_px, close_px))
        work = cv.dilate(work, k_group, iterations=1)
        work = cv.morphologyEx(work, cv.MORPH_CLOSE, k_close, iterations=1)
        work = cv.morphologyEx(work, cv.MORPH_OPEN, k_group, iterations=1)

    contours, _hier = cv.findContours(work, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

    min_area = max(float(min_area_override), image_area * ratio)
    min_bbox_area = image_area * ratio * 2.0
    min_long_side = max(22.0, min(img_h, img_w) * (0.022 + 0.002 * level))
    min_short_side = max(8.0, min(img_h, img_w) * 0.006)

    candidates = []
    for c in contours:
        area = float(cv.contourArea(c))
        x, y, bw, bh = cv.boundingRect(c)
        bbox_area = int(bw * bh)
        long_side = max(bw, bh)
        short_side = min(bw, bh)
        if long_side < min_long_side:
            continue
        if short_side < min_short_side and bbox_area < min_bbox_area * 2.0:
            # Very thin scratches/lines are usually not useful here.
            continue
        if area < min_area and bbox_area < min_bbox_area:
            continue
        candidates.append((bbox_area, area, x, y, bw, bh, c))

    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    if top_n and top_n > 0:
        candidates = candidates[: int(top_n)]

    kept_contours: List[np.ndarray] = [item[-1] for item in candidates]
    zones: List[ChangeZone] = []
    for i, (_bbox_area, area, x, y, bw, bh, _c) in enumerate(candidates, start=1):
        zones.append(
            ChangeZone(
                index=i,
                kind=kind,
                x=int(x),
                y=int(y),
                w=int(bw),
                h=int(bh),
                contour_area=float(area),
                bbox_area=int(bw * bh),
            )
        )

    zone_mask = np.zeros_like(work)
    if kept_contours:
        cv.drawContours(zone_mask, kept_contours, -1, 255, thickness=cv.FILLED)
    return zone_mask, kept_contours, zones


def annotate_large_zones(
    img: np.ndarray,
    contours: Sequence[np.ndarray],
    zones: Sequence[ChangeZone],
    color: Tuple[int, int, int],
    fill_alpha: float = 0.16,
) -> np.ndarray:
    """Draw large readable filled areas and numbered boxes on the modern image."""
    base = ensure_bgr(img).copy()
    if not contours:
        return base
    fill = base.copy()
    cv.drawContours(fill, list(contours), -1, color, thickness=cv.FILLED)
    base = cv.addWeighted(base, 1.0 - fill_alpha, fill, fill_alpha, 0)
    cv.drawContours(base, list(contours), -1, color, thickness=3, lineType=cv.LINE_AA)
    for zone in zones:
        x, y, w, h = zone.x, zone.y, zone.w, zone.h
        cv.rectangle(base, (x, y), (x + w, y + h), color, 3, cv.LINE_AA)
        # Draw number badge. Digits are safe with OpenCV fonts on all systems.
        label = str(zone.index)
        (tw, th), _baseline = cv.getTextSize(label, cv.FONT_HERSHEY_SIMPLEX, 0.8, 2)
        bx1, by1 = x, max(0, y - th - 10)
        bx2, by2 = x + tw + 16, max(th + 12, y)
        if by1 == 0:
            by2 = min(base.shape[0] - 1, y + th + 16)
        cv.rectangle(base, (bx1, by1), (bx2, by2), color, thickness=cv.FILLED)
        cv.putText(base, label, (bx1 + 8, by2 - 8), cv.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv.LINE_AA)
    return base


def zones_to_jsonable(zones: Sequence[ChangeZone]) -> List[dict]:
    return [
        {
            "index": z.index,
            "kind": z.kind,
            "x": z.x,
            "y": z.y,
            "w": z.w,
            "h": z.h,
            "bbox_area": z.bbox_area,
            "contour_area": round(z.contour_area, 1),
        }
        for z in zones
    ]


def write_zones_report(outdir: Path, added: Sequence[ChangeZone], removed: Sequence[ChangeZone], all_zones: Sequence[ChangeZone]) -> Path:
    lines = [
        "Archiview CV v5 — крупные зоны отличий",
        "",
        "Главная идея v5: не показывать микролинии, а оставить только крупные зоны, которые стоит проверить глазами.",
        "Зоны — это компьютерная подсказка, не архитектурная экспертиза.",
        "",
        f"Вероятно добавлено на современном фото: {len(added)} зон",
    ]
    for z in added:
        lines.append(f"  {z.index}. x={z.x}, y={z.y}, размер={z.w}x{z.h}, bbox_area={z.bbox_area}")
    lines.extend(["", f"Вероятно исчезло / закрыто относительно старого фото: {len(removed)} зон"])
    for z in removed:
        lines.append(f"  {z.index}. x={z.x}, y={z.y}, размер={z.w}x{z.h}, bbox_area={z.bbox_area}")
    lines.extend(["", f"Все крупные отличия без направления: {len(all_zones)} зон"])
    for z in all_zones:
        lines.append(f"  {z.index}. x={z.x}, y={z.y}, размер={z.w}x{z.h}, bbox_area={z.bbox_area}")
    lines.extend([
        "",
        "Как проверять:",
        "1. Откройте 01_overlay_slider.html и проверьте, хорошо ли совпали окна/углы/крыша.",
        "2. Откройте 02_large_added_on_modern.png — это основной файл для поиска надстроек, новых окон и пристроек.",
        "3. Если зона попала на дерево, машину, тень или сильный шум старого снимка — это ложное срабатывание.",
    ])
    path = outdir / "large_zones_report_ru.txt"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_before_after_slider_html(outdir: Path) -> Path:
    modern = html.escape("modern_reference.png")
    old = html.escape("aligned_historical.png")
    text = f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>Archiview CV — до/после</title>
<style>
  body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; color: #222; }}
  .panel {{ max-width: 1200px; margin: 0 auto; }}
  .controls {{ background: white; padding: 14px 16px; border-radius: 10px; margin-bottom: 14px; box-shadow: 0 2px 10px rgba(0,0,0,.08); }}
  .wrap {{ position: relative; display: inline-block; max-width: 100%; background: #ddd; box-shadow: 0 2px 14px rgba(0,0,0,.18); overflow:hidden; }}
  .wrap img {{ display: block; max-width: 100%; height: auto; user-select:none; }}
  #oldWrap {{ position: absolute; left: 0; top: 0; width: 50%; height: 100%; overflow: hidden; border-right: 3px solid white; }}
  #oldLayer {{ max-width: none; height: 100%; width: auto; }}
  input[type=range] {{ width: min(680px, 95vw); }}
  .hint {{ color: #555; font-size: 14px; line-height: 1.35; }}
</style>
</head>
<body>
<div class="panel">
  <h2>До/после: историческое фото ↔ современное</h2>
  <div class="controls">
    <label for="split"><b>Граница сравнения:</b> <span id="value">50</span>%</label><br>
    <input id="split" type="range" min="0" max="100" value="50">
    <p class="hint">Слева от белой линии — выровненное историческое фото. Справа — современное. Удобно проверять, где появились этажи, окна, пристройки.</p>
  </div>
  <div class="wrap" id="wrap">
    <img id="modernLayer" src="{modern}" alt="Современное фото">
    <div id="oldWrap"><img id="oldLayer" src="{old}" alt="Историческое фото"></div>
  </div>
</div>
<script>
const slider = document.getElementById('split');
const value = document.getElementById('value');
const oldWrap = document.getElementById('oldWrap');
const modernLayer = document.getElementById('modernLayer');
const oldLayer = document.getElementById('oldLayer');
function update() {{
  value.textContent = slider.value;
  oldWrap.style.width = slider.value + '%';
  oldLayer.style.width = modernLayer.clientWidth + 'px';
}}
slider.addEventListener('input', update);
window.addEventListener('resize', update);
modernLayer.addEventListener('load', update);
update();
</script>
</body>
</html>
"""
    path = outdir / "01_before_after_slider.html"
    path.write_text(text, encoding="utf-8")
    return path


def write_result_guide_v5(outdir: Path, old_opacity: float, large_level: int, top_n: int) -> Path:
    text = f"""Как читать результаты Archiview CV v5

Главная идея v5 — показывать только крупные зоны, а не микролинии.
Настройки этого запуска:
- видимость исторического фото в overlay: {int(round(opacity_to_01(old_opacity) * 100))}%
- минимальный размер изменения: {int(large_level)}/10
- максимум зон на картинке: {int(top_n)}

Главные файлы:
1) 01_overlay_slider.html
   Историческое фото поверх современного, видимость регулируется ползунком.

2) 01_before_after_slider.html
   Сравнение «до/после»: слева историческое фото, справа современное. Ползунок двигает границу.

3) 02_large_added_on_modern.png
   Основной файл. Зелёным отмечены крупные зоны, которые вероятно есть на современном фото и не читаются на старом.
   Сюда могут попасть надстройки, новые объёмы, новые окна, пристройки. Но также могут попасть деревья, тени или ошибки совмещения.

4) 03_large_removed_on_modern.png
   Синим отмечены крупные зоны, которые были заметны на старом фото, но не читаются на современном.

5) 04_large_all_changes_on_modern.png
   Оранжевым отмечены все крупные отличия без попытки понять направление.

6) 05_alignment_check_side_by_side.png
   Быстрая проверка совмещения: старое, современное, выровненное старое, overlay и крупные добавления.

7) large_zones_report_ru.txt
   Список найденных зон с координатами и размерами.

Папка technical_debug содержит старые технические карты: маски, heatmap, matches_debug. Их можно смотреть, если основной результат кажется странным.
"""
    path = outdir / "README_results_v5_ru.txt"
    path.write_text(text, encoding="utf-8")
    return path


def compare_images(args: argparse.Namespace) -> int:
    old_img = read_image(args.old)
    new_img = read_image(args.new)
    outdir = Path(args.output)
    outdir.mkdir(parents=True, exist_ok=True)
    debug_dir = outdir / "technical_debug"
    debug_dir.mkdir(parents=True, exist_ok=True)

    align = align_historic_to_modern(args, old_img, new_img)
    h_new, w_new = new_img.shape[:2]

    warped_old = cv.warpPerspective(old_img, align.homography, (w_new, h_new), flags=cv.INTER_CUBIC)
    valid_old = cv.warpPerspective(
        np.full(old_img.shape[:2], 255, dtype=np.uint8), align.homography, (w_new, h_new), flags=cv.INTER_NEAREST
    )
    valid = valid_old > 127

    old_gray = normalize_for_difference(clahe_gray(warped_old), valid_old)
    new_gray = normalize_for_difference(clahe_gray(new_img), valid_old)
    old_blur = cv.GaussianBlur(old_gray, (5, 5), 0)
    new_blur = cv.GaussianBlur(new_gray, (5, 5), 0)
    diff = cv.absdiff(old_blur, new_blur)
    diff[~valid] = 0

    if np.count_nonzero(valid) > 100:
        vals = diff[valid]
        lo, hi = np.percentile(vals, [2, 98])
        diff_norm = np.clip((diff.astype(np.float32) - lo) * 255.0 / (hi - lo + 1e-6), 0, 255).astype(np.uint8)
    else:
        diff_norm = diff
    diff_norm[~valid] = 0

    if args.diff_threshold is None:
        threshold_input = diff_norm.copy()
        threshold_input[~valid] = 0
        _t, change_mask = cv.threshold(threshold_input, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)
    else:
        _t, change_mask = cv.threshold(diff_norm, int(args.diff_threshold), 255, cv.THRESH_BINARY)
    change_mask[~valid] = 0

    kernel_size = max(3, int(args.morph_kernel) | 1)
    kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (kernel_size, kernel_size))
    change_mask = cv.morphologyEx(change_mask, cv.MORPH_OPEN, kernel)
    change_mask = cv.morphologyEx(change_mask, cv.MORPH_CLOSE, kernel)

    new_bgr = ensure_bgr(new_img)
    old_bgr = ensure_bgr(warped_old)

    modern_opacity = opacity_to_01(float(args.alpha))
    if getattr(args, "old_opacity", None) is not None:
        old_overlay_opacity = opacity_to_01(float(args.old_opacity))
        modern_opacity = 1.0 - old_overlay_opacity
    else:
        old_overlay_opacity = 1.0 - modern_opacity
    modern_opacity = clamp_float(modern_opacity, 0.0, 1.0)
    old_overlay_opacity = clamp_float(old_overlay_opacity, 0.0, 1.0)

    overlay = cv.addWeighted(new_bgr, modern_opacity, old_bgr, old_overlay_opacity, 0)
    overlay[~valid] = new_bgr[~valid]

    old_transparent = make_aligned_old_transparent(old_bgr, valid)

    heat = cv.applyColorMap(diff_norm, cv.COLORMAP_JET)
    heat_overlay = new_bgr.copy()
    heat_overlay[valid] = cv.addWeighted(new_bgr[valid], 0.58, heat[valid], 0.42, 0)

    added_mask, removed_mask = make_directional_change_masks(
        old_gray=old_gray,
        new_gray=new_gray,
        diff_norm=diff_norm,
        valid=valid,
        sensitivity=float(args.addition_sensitivity),
        morph_kernel=int(args.morph_kernel),
    )

    group_close = not bool(getattr(args, "no_group_large_zones", False))
    top_n = int(max(1, min(50, int(args.top_zones))))
    large_level = int(max(1, min(10, int(args.large_level))))
    min_area_override = float(max(0.0, float(args.min_change_area)))

    large_added_mask, large_added_contours, added_zones = build_large_zone_mask(
        added_mask, new_bgr.shape, kind="probable_added", large_level=large_level, top_n=top_n,
        group_close=group_close, min_area_override=min_area_override,
    )
    large_removed_mask, large_removed_contours, removed_zones = build_large_zone_mask(
        removed_mask, new_bgr.shape, kind="probable_removed", large_level=large_level, top_n=top_n,
        group_close=group_close, min_area_override=min_area_override,
    )
    large_all_mask, large_all_contours, all_zones = build_large_zone_mask(
        change_mask, new_bgr.shape, kind="changed", large_level=large_level, top_n=top_n,
        group_close=group_close, min_area_override=min_area_override,
    )

    large_added_annotated = annotate_large_zones(new_bgr, large_added_contours, added_zones, (0, 185, 0), fill_alpha=0.18)
    large_removed_annotated = annotate_large_zones(new_bgr, large_removed_contours, removed_zones, (255, 80, 0), fill_alpha=0.18)
    large_all_annotated = annotate_large_zones(new_bgr, large_all_contours, all_zones, (0, 145, 255), fill_alpha=0.18)

    side_by_side = make_side_by_side(
        [old_img, new_img, warped_old, overlay, large_added_annotated],
        ["historical", "modern", "historical aligned", "overlay", "large probable added"],
    )

    all_raw_contours = filter_contours_by_area(change_mask, max(50.0, min_area_override or 50.0))
    raw_added_contours = filter_contours_by_area(added_mask, max(50.0, min_area_override or 50.0))
    raw_removed_contours = filter_contours_by_area(removed_mask, max(50.0, min_area_override or 50.0))
    raw_all_annotated = new_bgr.copy()
    cv.drawContours(raw_all_annotated, all_raw_contours, -1, (0, 0, 255), 2, cv.LINE_AA)
    raw_added_annotated = new_bgr.copy()
    cv.drawContours(raw_added_annotated, raw_added_contours, -1, (0, 180, 0), 2, cv.LINE_AA)
    raw_removed_annotated = new_bgr.copy()
    cv.drawContours(raw_removed_annotated, raw_removed_contours, -1, (255, 0, 0), 2, cv.LINE_AA)

    outputs = {
        "modern_reference": outdir / "modern_reference.png",
        "aligned_old": outdir / "aligned_historical.png",
        "aligned_old_transparent": outdir / "aligned_historical_transparent.png",
        "overlay": outdir / "overlay.png",
        "overlay_slider": outdir / "01_overlay_slider.html",
        "overlay_slider_alias": outdir / "overlay_slider.html",
        "before_after_slider": outdir / "01_before_after_slider.html",
        "large_added": outdir / "02_large_added_on_modern.png",
        "large_removed": outdir / "03_large_removed_on_modern.png",
        "large_all": outdir / "04_large_all_changes_on_modern.png",
        "side_by_side": outdir / "05_alignment_check_side_by_side.png",
        "large_added_mask": debug_dir / "large_added_mask.png",
        "large_removed_mask": debug_dir / "large_removed_mask.png",
        "large_all_mask": debug_dir / "large_all_changes_mask.png",
        "difference_gray": debug_dir / "difference_gray.png",
        "difference_heat": debug_dir / "difference_heat_overlay.png",
        "change_mask": debug_dir / "raw_change_mask.png",
        "raw_changes_on_modern": debug_dir / "raw_all_changes_on_modern.png",
        "raw_added_on_modern": debug_dir / "raw_probable_added_on_modern.png",
        "raw_removed_on_modern": debug_dir / "raw_probable_removed_on_modern.png",
        "added_mask": debug_dir / "raw_probable_added_mask.png",
        "removed_mask": debug_dir / "raw_probable_removed_mask.png",
        "matches_debug": debug_dir / "matches_debug.png",
        "guide": outdir / "README_results_v5_ru.txt",
        "zones_report": outdir / "large_zones_report_ru.txt",
        "zones_json": outdir / "large_zones.json",
        "report": outdir / "report.json",
        "compat_probable_added": outdir / "probable_added_on_modern.png",
        "compat_probable_removed": outdir / "probable_removed_on_modern.png",
        "compat_changes": outdir / "changes_on_modern.png",
        "compat_side_by_side": outdir / "side_by_side.png",
    }

    write_image(outputs["modern_reference"], new_bgr)
    write_image(outputs["aligned_old"], warped_old)
    write_image(outputs["aligned_old_transparent"], old_transparent)
    write_image(outputs["overlay"], overlay)
    write_image(outputs["large_added"], large_added_annotated)
    write_image(outputs["large_removed"], large_removed_annotated)
    write_image(outputs["large_all"], large_all_annotated)
    write_image(outputs["side_by_side"], side_by_side)
    write_image(outputs["large_added_mask"], large_added_mask)
    write_image(outputs["large_removed_mask"], large_removed_mask)
    write_image(outputs["large_all_mask"], large_all_mask)
    write_image(outputs["difference_gray"], diff_norm)
    write_image(outputs["difference_heat"], heat_overlay)
    write_image(outputs["change_mask"], change_mask)
    write_image(outputs["added_mask"], added_mask)
    write_image(outputs["removed_mask"], removed_mask)
    write_image(outputs["raw_changes_on_modern"], raw_all_annotated)
    write_image(outputs["raw_added_on_modern"], raw_added_annotated)
    write_image(outputs["raw_removed_on_modern"], raw_removed_annotated)
    if align.matches_debug is not None:
        write_image(outputs["matches_debug"], align.matches_debug)

    write_image(outputs["compat_probable_added"], large_added_annotated)
    write_image(outputs["compat_probable_removed"], large_removed_annotated)
    write_image(outputs["compat_changes"], large_all_annotated)
    write_image(outputs["compat_side_by_side"], side_by_side)

    write_overlay_slider_html(outdir, old_overlay_opacity)
    default_overlay = outdir / "overlay_slider.html"
    if default_overlay.exists():
        outputs["overlay_slider"].write_text(default_overlay.read_text(encoding="utf-8"), encoding="utf-8")
    write_before_after_slider_html(outdir)
    write_result_guide_v5(outdir, old_overlay_opacity, large_level, top_n)
    write_zones_report(outdir, added_zones, removed_zones, all_zones)

    zones_json = {
        "probable_added": zones_to_jsonable(added_zones),
        "probable_removed": zones_to_jsonable(removed_zones),
        "all_large_changes": zones_to_jsonable(all_zones),
    }
    outputs["zones_json"].write_text(json.dumps(zones_json, ensure_ascii=False, indent=2), encoding="utf-8")

    report = {
        "mode": "compare_historical_modern_v5_large_changes",
        "old_image": str(args.old),
        "new_image": str(args.new),
        "detector": align.detector,
        "keypoints_old": align.keypoints_old,
        "keypoints_new": align.keypoints_new,
        "good_matches": align.good_matches,
        "inliers": align.inliers,
        "inlier_ratio": align.inlier_ratio,
        "overlay_modern_opacity": modern_opacity,
        "overlay_historical_opacity": old_overlay_opacity,
        "addition_sensitivity": float(args.addition_sensitivity),
        "large_level": large_level,
        "top_zones": top_n,
        "group_large_zones": group_close,
        "homography_old_to_new": align.homography.tolist(),
        "large_added_zones_kept": len(added_zones),
        "large_removed_zones_kept": len(removed_zones),
        "large_all_change_zones_kept": len(all_zones),
        "raw_change_contours": len(all_raw_contours),
        "raw_added_contours": len(raw_added_contours),
        "raw_removed_contours": len(raw_removed_contours),
        "outputs": {k: str(v) for k, v in outputs.items() if k != "report"},
    }
    outputs["report"].write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Saved comparison results in: {outdir}")
    print(
        f"Alignment: detector={align.detector}, good_matches={align.good_matches}, "
        f"inliers={align.inliers}, inlier_ratio={align.inlier_ratio:.2f}"
    )
    print(f"Large probable added zones: {len(added_zones)}")
    print(f"Main files: {outputs['overlay_slider']}, {outputs['large_added']}, {outputs['side_by_side']}")
    return 0


# ----------------------------- CLI ---------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Straighten building photos and compare historical vs modern photos with OpenCV.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p1 = sub.add_parser("straighten", help="Correct roll/perspective so building verticals become upright")
    p1.add_argument("input", help="Input architectural photo")
    p1.add_argument("-o", "--output", default="straightened.png", help="Output image path")
    p1.add_argument("--debug", help="Optional debug image with detected line segments")
    p1.add_argument("--report", help="Optional JSON report path")
    p1.add_argument(
        "--points",
        help='Manual facade points in order TL,TR,BR,BL: "x1,y1;x2,y2;x3,y3;x4,y4". Overrides auto mode.',
    )
    p1.add_argument("--no-perspective", action="store_true", help="Only fix camera roll; do not apply projective correction")
    p1.add_argument("--strength", type=float, default=0.9, help="Perspective correction strength, 0..1")
    p1.add_argument("--max-expand", type=float, default=3.0, help="Maximum output expansion for perspective warp")
    p1.add_argument("--process-max-dim", type=int, default=1800, help="Resize longest side for line detection")
    p1.add_argument("--vertical-tolerance", type=float, default=35.0, help="Degrees around 90 considered vertical-ish")
    p1.add_argument("--min-vertical-lines", type=int, default=5, help="Minimum vertical-ish lines needed")
    p1.add_argument("--min-roll-correction", type=float, default=0.10, help="Smallest roll correction to apply")
    p1.add_argument("--max-roll-correction", type=float, default=18.0, help="Ignore auto roll correction if larger than this")
    p1.add_argument("--final-cleanup", action="store_true", help="Apply a second small roll cleanup after perspective correction")
    p1.add_argument("--canny-low", type=int, default=50)
    p1.add_argument("--canny-high", type=int, default=160)
    p1.add_argument("--hough-threshold", type=int, default=70)
    p1.add_argument("--min-len-frac", type=float, default=0.06, help="Minimum line length as fraction of small image short side")
    p1.add_argument("--max-gap-frac", type=float, default=0.015, help="Max line gap as fraction of small image short side")
    p1.set_defaults(func=straighten_image)

    p2 = sub.add_parser("compare", help="Align historical photo to modern photo and export change visualizations")
    p2.add_argument("old", help="Historical/old photo")
    p2.add_argument("new", help="Modern/reference photo")
    p2.add_argument("-o", "--output", default="comparison_results", help="Output directory")
    p2.add_argument("--points-old", help='Manual old-photo points: "x1,y1;x2,y2;x3,y3;x4,y4"')
    p2.add_argument("--points-new", help='Matching modern-photo points in the same order as --points-old')
    p2.add_argument("--detector", choices=["auto", "sift", "orb", "akaze"], default="auto", help="Feature detector")
    p2.add_argument("--max-features", type=int, default=9000, help="Maximum features for SIFT/ORB")
    p2.add_argument("--align-max-dim", type=int, default=1800, help="Resize longest side during feature matching")
    p2.add_argument("--ratio", type=float, default=0.76, help="Lowe ratio test threshold")
    p2.add_argument("--ransac-thresh", type=float, default=4.0, help="RANSAC reprojection threshold in resized pixels")
    p2.add_argument("--min-matches", type=int, default=18, help="Minimum good matches before homography")
    p2.add_argument("--min-inliers", type=int, default=18, help="Preferred inlier count for accepting alignment")
    p2.add_argument("--min-inlier-ratio", type=float, default=0.22, help="Preferred inlier ratio for accepting alignment")
    p2.add_argument("--alpha", type=float, default=0.35, help="Modern image opacity in overlay; lower values make the historical photo more visible")
    p2.add_argument("--old-opacity", type=float, help="Historical image opacity in overlay, 0..1 or 0..100; overrides --alpha")
    p2.add_argument("--diff-threshold", type=int, help="Manual difference threshold 0..255; default uses Otsu")
    p2.add_argument("--morph-kernel", type=int, default=5, help="Morphology kernel for raw change mask")
    p2.add_argument("--min-change-area", type=float, default=0.0, help="Optional absolute minimum area for large zones; 0 means auto by --large-level")
    p2.add_argument("--addition-sensitivity", type=float, default=45.0, help="Sensitivity for probable modern-only additions, 0..100; lower is more conservative")
    p2.add_argument("--large-level", type=int, default=6, help="Minimum size level for large zones, 1..10; higher keeps fewer larger zones")
    p2.add_argument("--top-zones", type=int, default=10, help="Maximum number of large zones drawn for each result")
    p2.add_argument("--no-group-large-zones", action="store_true", help="Do not merge nearby small differences into larger zones")
    p2.set_defaults(func=compare_images)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
