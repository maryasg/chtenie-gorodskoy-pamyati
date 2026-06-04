#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Archiview CV v10 — нормальный workflow, карта с прямой передачей координат, расширенный холст и встроенный preview.

Главная идея:
- подтянуть исторические фото PastVu по адресу/координатам;
- выбрать подходящий ракурс;
- выбрать современное фото с компьютера;
- вручную указать 4 угла одного фасада на старом и новом фото;
- получить выпрямленную пару, overlay и до/после;
- разметить новые элементы полигонами на выпрямленном сравнении;
- перенести разметку обратно на исходное современное фото;
- экспортировать датасет в COCO для Roboflow.
"""

from __future__ import annotations

import base64
import io
import json
import math
import os
import re
import platform
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
import zipfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlencode, urlparse, parse_qs
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

import numpy as np

try:
    import cv2 as cv
except Exception:  # pragma: no cover - GUI message shown at runtime
    cv = None  # type: ignore[assignment]

try:
    from PIL import Image, ImageTk, ImageGrab, ImageEnhance, ImageOps
except Exception:  # pragma: no cover - GUI message shown at runtime
    Image = None  # type: ignore[assignment]
    ImageTk = None  # type: ignore[assignment]
    ImageGrab = None  # type: ignore[assignment]
    ImageEnhance = None  # type: ignore[assignment]
    ImageOps = None  # type: ignore[assignment]

try:
    from archiview_house_db import HouseDatabaseFrame, HouseRecord, create_house_project
except Exception:
    HouseDatabaseFrame = None  # type: ignore[assignment,misc]
    HouseRecord = None  # type: ignore[assignment,misc]
    create_house_project = None  # type: ignore[assignment,misc]

try:
    from archiview_project_model import (
        ComparisonSession,
        ProjectStore,
        address_location_key,
        format_nominatim_short_address,
        house_number_from_nominatim,
        infer_site_card_id,
        merge_map_address,
        normalize_site_card_id,
        normalize_address_dedupe,
        osm_tags_to_address_dict,
        propose_project_slug,
        propose_site_card_id,
        next_site_card_id,
        website_display_name,
    )
    from archiview_project_ui import CombinedHousesTab, ComparisonsTabFrame, MyProjectsPanel, PhotosTabFrame
except Exception:
    ComparisonSession = None  # type: ignore[assignment,misc]
    ProjectStore = None  # type: ignore[assignment,misc]
    infer_site_card_id = None  # type: ignore[assignment,misc]
    normalize_site_card_id = None  # type: ignore[assignment,misc]
    website_display_name = None  # type: ignore[assignment,misc]
    normalize_address_dedupe = None  # type: ignore[assignment,misc]
    merge_map_address = None  # type: ignore[assignment,misc]
    format_nominatim_short_address = None  # type: ignore[assignment,misc]
    house_number_from_nominatim = None  # type: ignore[assignment,misc]
    address_location_key = None  # type: ignore[assignment,misc]
    propose_project_slug = None  # type: ignore[assignment,misc]
    propose_site_card_id = None  # type: ignore[assignment,misc]
    next_site_card_id = None  # type: ignore[assignment,misc]
    osm_tags_to_address_dict = None  # type: ignore[assignment,misc]
    CombinedHousesTab = None  # type: ignore[assignment,misc]
    PhotosTabFrame = None  # type: ignore[assignment,misc]
    ComparisonsTabFrame = None  # type: ignore[assignment,misc]
    MyProjectsPanel = None  # type: ignore[assignment,misc]

APP_VERSION = "v15 projects + hand cursor + delete any region"
APP_DIR = Path(__file__).resolve().parent
SCRIPT = APP_DIR / "archiview_cv.py"
USER_AGENT = "ArchiviewCV-v13/0.1 desktop research tool"

PASTVU_API = "https://api.pastvu.com/api2"
PASTVU_IMG_THUMB = "https://img.pastvu.com/h/"
PASTVU_IMG_STANDARD = "https://img.pastvu.com/d/"
PASTVU_IMG_ORIGINAL = "https://img.pastvu.com/a/"
NOMINATIM_SEARCH = "https://nominatim.openstreetmap.org/search"
NOMINATIM_REVERSE = "https://nominatim.openstreetmap.org/reverse"
PHOTON_REVERSE = "https://photon.komoot.io/reverse"
OVERPASS_INTERPRETER = "https://overpass-api.de/api/interpreter"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
PANORAMAX_API = "https://api.panoramax.xyz/api"

MAPILLARY_GRAPH_IMAGES = "https://graph.mapillary.com/images"
KARTAVIEW_NEARBY_ENDPOINTS = [
    "https://api.openstreetcam.org/1.0/list/nearby-photos/",
    "http://api.openstreetcam.org/1.0/list/nearby-photos/",
    "https://openstreetcam.org/1.0/list/nearby-photos/",
    "http://openstreetcam.org/1.0/list/nearby-photos/",
]

IMAGE_TYPES = [
    ("Фотографии", "*.jpg *.jpeg *.png *.tif *.tiff *.bmp *.webp"),
    ("Все файлы", "*.*"),
]

Point = Tuple[float, float]

CLASS_LABELS = {
    "added_floor": "Надстройка / новый этаж",
    "extension": "Пристройка / новый объём",
    "filled_window": "Заложенное окно",
    "new_window": "Новое окно / новый проём",
    "lost_balcony": "Утраченный балкон",
    "new_balcony": "Новый балкон / устройство балкона",
    "changed_entrance": "Изменённый вход",
    "lost_decor": "Утраченный декор",
    "technical_artifact": "Новый технический элемент",
    "other_artifact": "Другой артефакт / другое изменение",
    "check_manually": "Проверить вручную",
}

# OpenCV colors are BGR.
CLASS_COLORS = {
    "added_floor": (0, 185, 0),
    "extension": (0, 145, 255),
    "filled_window": (255, 120, 0),
    "new_window": (0, 210, 210),
    "lost_balcony": (220, 80, 180),
    "new_balcony": (40, 170, 255),
    "changed_entrance": (120, 120, 255),
    "lost_decor": (170, 80, 255),
    "technical_artifact": (80, 170, 170),
    "other_artifact": (190, 190, 60),
    "check_manually": (180, 0, 180),
}

TK_COLORS = {
    "added_floor": "#00aa00",
    "extension": "#ff8c00",
    "filled_window": "#0078d7",
    "new_window": "#00aaaa",
    "lost_balcony": "#b850b0",
    "new_balcony": "#d08a00",
    "changed_entrance": "#786cff",
    "lost_decor": "#aa50ff",
    "technical_artifact": "#7a8a00",
    "other_artifact": "#8a8a00",
    "check_manually": "#b000b0",
}

NON_FACADE_KEYWORDS = (
    "интерьер", "внутри", "внутрен", "лестниц", "лестница", "подъезд",
    "вестибюль", "комната", "кабинет", "потолок", "лепнина", "решет", "решёт",
    "решетка", "решётка", "зал ", "зал.", "зал,",
)


# ---------------------------------------------------------------------------
# Small cross-platform helpers
# ---------------------------------------------------------------------------

def open_path(path: Path) -> None:
    """Open a file/folder with the default system app."""
    try:
        if platform.system() == "Windows":
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except Exception:
        pass


def safe_filename(text: str, default: str = "photo") -> str:
    keep = []
    for ch in str(text):
        if ch.isalnum() or ch in "-_.":
            keep.append(ch)
        elif ch in " /\\:;|":
            keep.append("_")
    name = "".join(keep).strip("._-")
    while "__" in name:
        name = name.replace("__", "_")
    return name[:80] or default


def points_to_cli(points: List[Point]) -> str:
    return ";".join(f"{x:.1f},{y:.1f}" for x, y in points)


def parse_four_points(text: str) -> np.ndarray:
    clean = text.replace(" ", "")
    parts = [p for p in clean.replace("|", ";").split(";") if p]
    if len(parts) != 4:
        raise ValueError("Нужно ровно 4 точки фасада.")
    pts = []
    for p in parts:
        xy = p.split(",")
        if len(xy) != 2:
            raise ValueError(f"Плохая точка: {p}")
        pts.append((float(xy[0]), float(xy[1])))
    return np.asarray(pts, dtype=np.float32)


def crop_rect_to_text(x0: float, y0: float, x1: float, y1: float) -> str:
    return f"{x0:.1f},{y0:.1f},{x1:.1f},{y1:.1f}"


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
    """Обрезка исходника по рамке; возвращает сдвиг (dx, dy) для координат углов."""
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


def validate_facade_quad_points(pts: np.ndarray) -> Tuple[bool, str]:
    """Проверка, что 4 угла — один фасад, а не небо/улица рядом."""
    if pts.shape[0] != 4:
        return False, "Нужно ровно 4 точки."
    tl, tr, br, bl = pts.astype(np.float64)
    w_top = float(np.linalg.norm(tr - tl))
    w_bot = float(np.linalg.norm(br - bl))
    h_left = float(np.linalg.norm(bl - tl))
    h_right = float(np.linalg.norm(br - tr))
    if min(w_top, w_bot, h_left, h_right) < 12:
        return False, "Точки слишком близко друг к другу."
    if max(w_top, w_bot) / max(min(w_top, w_bot), 1e-6) > 3.5:
        return False, "Верх и низ сильно разной ширины — все 4 точки должны быть на одном фасаде, не в небе."
    if max(h_left, h_right) / max(min(h_left, h_right), 1e-6) > 3.5:
        return False, "Левый и правый край сильно разной высоты — проверьте порядок 1–4."
    if cv is not None:
        contour = pts.astype(np.float32).reshape(-1, 1, 2)
        if not cv.isContourConvex(contour):
            return False, "Углы пересекаются — кликайте строго: 1 верх-лево, 2 верх-право, 3 низ-право, 4 низ-лево."
        if abs(float(cv.contourArea(contour))) < 800:
            return False, "Четырёхугольник слишком маленький."
    return True, ""


def shift_points_after_crop(pts: np.ndarray, offset: Tuple[float, float]) -> np.ndarray:
    dx, dy = offset
    if dx == 0.0 and dy == 0.0:
        return pts
    out = pts.astype(np.float32).copy()
    out[:, 0] -= float(dx)
    out[:, 1] -= float(dy)
    return out


def source_crop_offset_from_project(project: dict, *, side: str = "modern") -> Tuple[float, float]:
    """Сдвиг обрезки исходника: координаты выпрямления → полный файл modern_image."""
    key_off = f"{side}_crop_offset_xy"
    key_rect = f"{side}_crop_rect_text"
    off = project.get(key_off)
    if isinstance(off, (list, tuple)) and len(off) >= 2:
        return float(off[0]), float(off[1])
    box = parse_crop_rect(str(project.get(key_rect) or ""))
    if box is not None:
        return float(box[0]), float(box[1])
    return 0.0, 0.0


def homography_rect_to_full_source(
    H_rect_to_cropped: np.ndarray,
    crop_offset: Tuple[float, float],
) -> np.ndarray:
    """Разметка в выпрямленном кадре → координаты полного исходного фото."""
    dx, dy = float(crop_offset[0]), float(crop_offset[1])
    H = np.asarray(H_rect_to_cropped, dtype=np.float64)
    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
        return H
    T = np.array([[1.0, 0.0, dx], [0.0, 1.0, dy], [0.0, 0.0, 1.0]], dtype=np.float64)
    return T @ H


def _modern_crop_offset_resolved(project: dict, *, fallback_rect_text: str = "") -> Tuple[float, float]:
    off = source_crop_offset_from_project(project, side="modern")
    if off != (0.0, 0.0):
        return off
    for text in (fallback_rect_text, str(project.get("modern_crop_rect_text") or "")):
        box = parse_crop_rect(text)
        if box is not None:
            return float(box[0]), float(box[1])
    return 0.0, 0.0


def H_rect_to_full_modern_from_project(project: dict, *, fallback_rect_text: str = "") -> np.ndarray:
    H = np.asarray(project.get("H_rect_to_modern"), dtype=np.float64)
    off = _modern_crop_offset_resolved(project, fallback_rect_text=fallback_rect_text)
    return homography_rect_to_full_source(H, off)


def modern_crop_rect_from_metadata_near(outdir: Path) -> str:
    for meta in (
        outdir.parent / "metadata" / "historical_sources.json",
        outdir / "historical_sources.json",
    ):
        if not meta.exists():
            continue
        try:
            data = json.loads(meta.read_text(encoding="utf-8"))
            text = str(data.get("modern_crop_rect_text") or "").strip()
            if text:
                return text
        except Exception:
            pass
    return ""


def cv_read(path: str | Path) -> np.ndarray:
    if cv is None:
        raise RuntimeError("OpenCV не установлен. Сначала запустите install_windows.bat.")
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Файл не найден: {p}")
    data = np.fromfile(str(p), dtype=np.uint8)
    if data.size == 0:
        raise FileNotFoundError(f"Файл пустой или недоступен: {p}")
    img = cv.imdecode(data, cv.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Не удалось открыть изображение: {p}")
    return img


def cv_write(path: str | Path, img: np.ndarray) -> None:
    if cv is None:
        raise RuntimeError("OpenCV не установлен. Сначала запустите install_windows.bat.")
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    ext = p.suffix.lower() or ".png"
    if ext == ".jpg":
        ext = ".jpeg"
    ok, encoded = cv.imencode(ext, img)
    if not ok:
        raise IOError(f"Не удалось подготовить файл для записи: {p}")
    encoded.tofile(str(p))


def cv_to_photoimage(path: str | Path, max_w: int, max_h: int) -> Tuple[tk.PhotoImage, float, int, int, int, int]:
    """Load local image with OpenCV and return Tk PhotoImage plus scale/display/original sizes."""
    img = cv_read(path)
    orig_h, orig_w = img.shape[:2]
    scale = min(max_w / float(orig_w), max_h / float(orig_h), 1.0)
    disp_w = max(1, int(round(orig_w * scale)))
    disp_h = max(1, int(round(orig_h * scale)))
    if scale < 1.0:
        img = cv.resize(img, (disp_w, disp_h), interpolation=cv.INTER_AREA)
    ok, encoded = cv.imencode(".png", img)
    if not ok:
        raise RuntimeError("Не удалось подготовить изображение для показа в окне.")
    data = base64.b64encode(encoded.tobytes()).decode("ascii")
    photo = tk.PhotoImage(data=data)
    return photo, scale, disp_w, disp_h, orig_w, orig_h


def request_json(url: str, timeout: int = 25) -> object:
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    return json.loads(raw.decode("utf-8", errors="replace"))


def request_json_post(url: str, data: Dict[str, object], timeout: int = 25) -> object:
    encoded = urlencode({k: str(v) for k, v in data.items() if v is not None}).encode("utf-8")
    req = Request(
        url,
        data=encoded,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    with urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    return json.loads(raw.decode("utf-8", errors="replace"))


def request_bytes(url: str, timeout: int = 35) -> bytes:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


# ---------------------------------------------------------------------------
# PastVu / Nominatim
# ---------------------------------------------------------------------------

@dataclass
class PastVuPhoto:
    cid: int
    file: str
    title: str = ""
    year: str = ""
    year2: str = ""
    distance: str = ""
    lat: str = ""
    lon: str = ""
    thumb_url: str = ""
    standard_url: str = ""
    original_url: str = ""
    page_url: str = ""

    @property
    def years_label(self) -> str:
        y1 = str(self.year or "").strip()
        y2 = str(self.year2 or "").strip()
        if y1 and y2 and y2 != y1:
            return f"{y1}–{y2}"
        return y1 or y2 or "год не указан"

    @property
    def caption(self) -> str:
        title = self.title.strip() or f"PastVu #{self.cid}"
        dist = f", {self.distance} м" if str(self.distance).strip() else ""
        return f"{title}\n{self.years_label}{dist}"



@dataclass
class OpenStreetPhoto:
    source: str
    id: str
    title: str = ""
    date: str = ""
    author: str = ""
    lat: str = ""
    lon: str = ""
    heading: str = ""
    distance_m: float = 0.0
    thumb_url: str = ""
    image_url: str = ""
    page_url: str = ""
    license: str = "CC BY-SA"

    @property
    def caption(self) -> str:
        parts = [self.source]
        if self.title:
            title = " ".join(str(self.title).split())
            if len(title) > 70:
                title = title[:67] + "…"
            parts.append(title)
        if self.date:
            parts.append(str(self.date)[:10])
        if self.distance_m:
            parts.append(f"{int(round(self.distance_m))} м")
        if self.heading not in (None, ""):
            try:
                parts.append(f"курс {int(round(float(self.heading)))}°")
            except Exception:
                pass
        if self.author:
            parts.append(str(self.author))
        return "\n".join(parts)


def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371008.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl/2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def bbox_around(lat: float, lon: float, radius_m: float) -> Tuple[float, float, float, float]:
    dlat = float(radius_m) / 111_111.0
    cos_lat = max(0.05, abs(math.cos(math.radians(lat))))
    dlon = float(radius_m) / (111_111.0 * cos_lat)
    return lon - dlon, lat - dlat, lon + dlon, lat + dlat


def _geo_coords(item: dict) -> Tuple[Optional[float], Optional[float]]:
    for key in ("computed_geometry", "geometry"):
        geom = item.get(key)
        if isinstance(geom, dict):
            coords = geom.get("coordinates")
            if isinstance(coords, (list, tuple)) and len(coords) >= 2:
                try:
                    return float(coords[1]), float(coords[0])  # lat, lon
                except Exception:
                    pass
    for lat_key, lon_key in (("lat", "lng"), ("latitude", "longitude"), ("lat", "lon")):
        if lat_key in item and lon_key in item:
            try:
                return float(item[lat_key]), float(item[lon_key])
            except Exception:
                pass
    return None, None


def _normalize_url(url: object, base: str = "https://openstreetcam.org") -> str:
    text = str(url or "").strip()
    if not text:
        return ""
    if text.startswith("//"):
        return "https:" + text
    if text.startswith("http://") or text.startswith("https://"):
        return text
    if text.startswith("/"):
        return base.rstrip("/") + text
    return "https://" + text



def strip_html(text: object, limit: int = 120) -> str:
    raw = str(text or "")
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = raw.replace("&nbsp;", " ").replace("&amp;", "&").replace("&quot;", '"')
    raw = " ".join(raw.split())
    return raw[:limit]


def _commons_meta_value(meta: dict, key: str) -> str:
    val = meta.get(key)
    if isinstance(val, dict):
        return strip_html(val.get("value") or val.get("hidden") or "")
    return ""


def wikimedia_commons_search(lat: float, lon: float, radius_m: int, limit: int) -> List[OpenStreetPhoto]:
    """Search geotagged Wikimedia Commons image files near coordinates."""
    radius = max(10, min(int(radius_m), 10_000))
    lim = max(1, min(int(limit), 50))
    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "generator": "geosearch",
        "ggsprimary": "all",
        "ggsnamespace": "6",
        "ggsradius": radius,
        "ggscoord": f"{lat}|{lon}",
        "ggslimit": lim,
        "prop": "imageinfo|coordinates",
        "iiprop": "url|mime|size|extmetadata|commonmetadata",
        "iiurlwidth": 420,
    }
    data = request_json(f"{COMMONS_API}?{urlencode(params)}", timeout=45)
    if not isinstance(data, dict):
        return []
    query = data.get("query")
    pages = query.get("pages", []) if isinstance(query, dict) else []
    if not isinstance(pages, list):
        return []
    out: List[OpenStreetPhoto] = []
    for page in pages:
        if not isinstance(page, dict):
            continue
        title = str(page.get("title") or "")
        infos = page.get("imageinfo") or []
        if not infos or not isinstance(infos, list) or not isinstance(infos[0], dict):
            continue
        info = infos[0]
        mime = str(info.get("mime") or "")
        if not mime.startswith("image/"):
            continue
        image_url = str(info.get("url") or "")
        thumb_url = str(info.get("thumburl") or image_url)
        if not image_url:
            continue
        meta = info.get("extmetadata") if isinstance(info.get("extmetadata"), dict) else {}
        coords = page.get("coordinates") or []
        ilat = ilon = None
        if isinstance(coords, list) and coords and isinstance(coords[0], dict):
            try:
                ilat = float(coords[0].get("lat"))
                ilon = float(coords[0].get("lon"))
            except Exception:
                ilat = ilon = None
        if ilat is None or ilon is None:
            ilat, ilon = lat, lon
        dist = haversine_meters(lat, lon, ilat, ilon)
        author = _commons_meta_value(meta, "Artist") or _commons_meta_value(meta, "Credit")
        license_name = _commons_meta_value(meta, "LicenseShortName") or _commons_meta_value(meta, "UsageTerms") or "проверьте на странице файла"
        date = _commons_meta_value(meta, "DateTimeOriginal") or _commons_meta_value(meta, "DateTime")
        object_name = _commons_meta_value(meta, "ObjectName") or title.replace("File:", "")
        page_url = str(info.get("descriptionurl") or f"https://commons.wikimedia.org/wiki/{title.replace(' ', '_')}")
        out.append(OpenStreetPhoto(
            source="Wikimedia Commons",
            id=title,
            title=object_name,
            date=date,
            author=author,
            lat=f"{ilat:.7f}",
            lon=f"{ilon:.7f}",
            heading="",
            distance_m=dist,
            thumb_url=thumb_url,
            image_url=image_url,
            page_url=page_url,
            license=license_name,
        ))
    out.sort(key=lambda p: p.distance_m)
    return out[:lim]


def kartaview_cdn_url(url: str) -> str:
    """KartaView sometimes returns old openstreetcam storage URLs; CDN wrapper is often more reliable."""
    u = str(url or "").strip()
    if not u:
        return ""
    if "cdn.kartaview.org" in u:
        return u
    if "openstreetcam.org/files/photo" in u or ("storage" in u and "openstreetcam" in u):
        b64 = base64.b64encode(u.encode("utf-8")).decode("ascii").rstrip("=")
        return f"https://cdn.kartaview.org/pr:sharp/{b64}"
    return u

def mapillary_search(lat: float, lon: float, radius_m: int, limit: int, token: str) -> List[OpenStreetPhoto]:
    token = token.strip()
    if not token:
        raise RuntimeError("Для Mapillary нужен бесплатный access token. Вставьте его в поле Mapillary token или используйте KartaView без токена.")
    west, south, east, north = bbox_around(lat, lon, radius_m)
    fields = ",".join([
        "id", "thumb_256_url", "thumb_1024_url", "thumb_2048_url", "thumb_original_url",
        "computed_geometry", "geometry", "captured_at", "compass_angle", "computed_compass_angle",
        "camera_type", "creator",
    ])
    query = urlencode({
        "access_token": token,
        "fields": fields,
        "limit": max(1, min(int(limit) * 4, 200)),
        "bbox": f"{west},{south},{east},{north}",
    })
    data = request_json(f"{MAPILLARY_GRAPH_IMAGES}?{query}", timeout=45)
    if not isinstance(data, dict):
        return []
    items = data.get("data")
    if not isinstance(items, list):
        return []
    out: List[OpenStreetPhoto] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        ilat, ilon = _geo_coords(item)
        if ilat is None or ilon is None:
            continue
        dist = haversine_meters(lat, lon, ilat, ilon)
        creator = item.get("creator")
        author = ""
        if isinstance(creator, dict):
            author = str(creator.get("username") or creator.get("id") or "")
        thumb = str(item.get("thumb_2048_url") or item.get("thumb_1024_url") or item.get("thumb_256_url") or "")
        image_url = str(item.get("thumb_original_url") or item.get("thumb_2048_url") or item.get("thumb_1024_url") or thumb)
        pid = str(item.get("id") or "")
        if not pid or not image_url:
            continue
        heading = item.get("computed_compass_angle", item.get("compass_angle", ""))
        out.append(OpenStreetPhoto(
            source="Mapillary",
            id=pid,
            title=f"Mapillary {pid}",
            date=str(item.get("captured_at") or ""),
            author=author,
            lat=f"{ilat:.7f}",
            lon=f"{ilon:.7f}",
            heading=str(heading or ""),
            distance_m=dist,
            thumb_url=thumb or image_url,
            image_url=image_url,
            page_url=f"https://www.mapillary.com/app/?pKey={pid}",
            license="CC BY-SA 4.0 / Mapillary attribution required",
        ))
    out.sort(key=lambda p: p.distance_m)
    return out[:max(1, int(limit))]


def _extract_kartaview_photos(data: object) -> List[dict]:
    if isinstance(data, dict):
        for key in ("currentPageItems", "osv", "photos", "data", "items"):
            val = data.get(key)
            if isinstance(val, list):
                return [x for x in val if isinstance(x, dict)]
            if isinstance(val, dict):
                for k2 in ("photos", "currentPageItems", "items", "data"):
                    val2 = val.get(k2)
                    if isinstance(val2, list):
                        return [x for x in val2 if isinstance(x, dict)]
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    return []


def kartaview_search(lat: float, lon: float, radius_m: int, limit: int) -> List[OpenStreetPhoto]:
    last_error = None
    payload = {
        "lat": lat,
        "lng": lon,
        "radius": int(radius_m),
        "page": 1,
        "ipp": max(1, min(int(limit), 50)),
    }
    data: object = None
    for endpoint in KARTAVIEW_NEARBY_ENDPOINTS:
        try:
            data = request_json_post(endpoint, payload, timeout=35)
            break
        except Exception as exc:
            last_error = exc
            try:
                data = request_json(f"{endpoint}?{urlencode(payload)}", timeout=35)
                break
            except Exception as exc2:
                last_error = exc2
                continue
    if data is None:
        raise RuntimeError(f"KartaView не ответил. Попробуйте позже или используйте Wikimedia Commons. Детали: {last_error}")
    out: List[OpenStreetPhoto] = []
    for item in _extract_kartaview_photos(data):
        ilat, ilon = _geo_coords(item)
        if ilat is None or ilon is None:
            continue
        dist = haversine_meters(lat, lon, ilat, ilon)
        pid = str(item.get("id") or item.get("photoId") or item.get("photo_id") or "")
        thumb_raw = (
            item.get("imageThumbUrl") or item.get("thumbnailUrl") or item.get("thumbUrl") or
            item.get("lth_name") or item.get("th_name") or item.get("thumb_name") or
            item.get("photo") or item.get("fileurlLTh") or item.get("fileurlTh")
        )
        img_raw = (
            item.get("imageProcUrl") or item.get("imageUrl") or item.get("fileurlProc") or
            item.get("name") or item.get("photo") or item.get("lth_name") or thumb_raw
        )
        thumb = kartaview_cdn_url(_normalize_url(thumb_raw))
        img = kartaview_cdn_url(_normalize_url(img_raw))
        if not img:
            continue
        seq = item.get("sequence_id") or item.get("sequenceId")
        seq_idx = item.get("sequence_index") or item.get("sequenceIndex")
        page = f"https://kartaview.org/details/{seq}/{seq_idx}" if seq not in (None, "") else "https://kartaview.org/"
        out.append(OpenStreetPhoto(
            source="KartaView",
            id=pid or f"kv_{len(out)+1}",
            title=f"KartaView {pid}" if pid else "KartaView photo",
            date=str(item.get("date_added") or item.get("date") or ""),
            author=str(item.get("user") or ""),
            lat=f"{ilat:.7f}",
            lon=f"{ilon:.7f}",
            heading=str(item.get("heading") or ""),
            distance_m=dist,
            thumb_url=thumb or img,
            image_url=img,
            page_url=page,
            license="CC BY-SA / © Grab and KartaView Contributors",
        ))
    out.sort(key=lambda p: p.distance_m)
    return out[:max(1, int(limit))]



def _asset_href(asset: object) -> str:
    if isinstance(asset, dict):
        return str(asset.get("href") or asset.get("url") or "")
    if isinstance(asset, str):
        return asset
    return ""


def panoramax_search(lat: float, lon: float, radius_m: int, limit: int) -> List[OpenStreetPhoto]:
    """Search Panoramax meta-catalog for street-level pictures looking at/near a place.

    Panoramax uses lon,lat order in place_position. We keep the parser deliberately
    tolerant because federated instances can expose slightly different STAC fields.
    """
    limit = max(1, min(int(limit), 60))
    radius = max(5, min(int(radius_m), 3000))
    # place_distance accepts ranges in Panoramax examples; this helps include views
    # shot from across the street or a small square.
    params = {
        "place_position": f"{lon:.7f},{lat:.7f}",
        "place_distance": f"0-{radius}",
        "place_fov_tolerance": 60,
        "limit": limit,
    }
    url = f"{PANORAMAX_API}/search?{urlencode(params)}"
    data = request_json(url, timeout=45)
    features = []
    if isinstance(data, dict):
        maybe = data.get("features")
        if isinstance(maybe, list):
            features = [x for x in maybe if isinstance(x, dict)]
    out: List[OpenStreetPhoto] = []
    for feat in features:
        pid = str(feat.get("id") or feat.get("uuid") or "").strip()
        props = feat.get("properties") if isinstance(feat.get("properties"), dict) else {}
        geom = feat.get("geometry") if isinstance(feat.get("geometry"), dict) else {}
        coords = geom.get("coordinates") if isinstance(geom, dict) else None
        ilat = ilon = None
        if isinstance(coords, (list, tuple)) and len(coords) >= 2:
            try:
                ilon = float(coords[0])
                ilat = float(coords[1])
            except Exception:
                ilat = ilon = None
        if ilat is None or ilon is None:
            ilat, ilon = lat, lon
        assets = feat.get("assets") if isinstance(feat.get("assets"), dict) else {}
        thumb = _asset_href(assets.get("thumb")) or (f"{PANORAMAX_API}/pictures/{pid}/thumb.jpg" if pid else "")
        sd = _asset_href(assets.get("sd")) or _asset_href(assets.get("hd")) or _asset_href(assets.get("visual"))
        image = sd or (f"{PANORAMAX_API}/pictures/{pid}/sd.jpg" if pid else thumb)
        if not image:
            continue
        heading = props.get("view:azimuth") or props.get("heading") or props.get("geovisio:heading") or ""
        author = props.get("geovisio:producer") or props.get("author") or props.get("creator") or ""
        date = props.get("datetime") or props.get("created") or props.get("date") or ""
        license_name = props.get("license") or props.get("geovisio:license") or "проверьте лицензию Panoramax-источника"
        dist = haversine_meters(lat, lon, float(ilat), float(ilon))
        page_url = f"https://api.panoramax.xyz/#focus=pic&pic={pid}" if pid else "https://api.panoramax.xyz/"
        out.append(OpenStreetPhoto(
            source="Panoramax",
            id=pid or f"panoramax_{len(out)+1}",
            title=str(props.get("title") or "Panoramax photo"),
            date=str(date),
            author=str(author),
            lat=f"{float(ilat):.7f}",
            lon=f"{float(ilon):.7f}",
            heading=str(heading or ""),
            distance_m=dist,
            thumb_url=thumb or image,
            image_url=image,
            page_url=page_url,
            license=str(license_name),
        ))
    out.sort(key=lambda p: p.distance_m)
    return out[:limit]

def download_open_street_photo(photo: OpenStreetPhoto, folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    ext = ".jpg"
    if ".png" in photo.image_url.lower().split("?")[0]:
        ext = ".png"
    base = f"{safe_filename(photo.source.lower())}_{safe_filename(photo.id, 'photo')}"
    target = folder / f"{base}{ext}"
    raw = request_bytes(photo.image_url, timeout=60)
    target.write_bytes(raw)
    meta = asdict(photo)
    meta["downloaded_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    meta["note_ru"] = "Проверьте лицензию/атрибуцию перед публикацией или экспортом в Roboflow."
    (folder / f"{base}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return target

def geocode_address(address: str) -> Tuple[float, float, str]:
    query = urlencode({"format": "jsonv2", "limit": "1", "q": address, "addressdetails": "1"})
    data = request_json(f"{NOMINATIM_SEARCH}?{query}")
    if not isinstance(data, list) or not data:
        raise RuntimeError("Адрес не найден. Попробуйте добавить город или введите координаты вручную.")
    item = data[0]
    lat = float(item["lat"])
    lon = float(item["lon"])
    addr = item.get("address") if isinstance(item.get("address"), dict) else {}
    if format_nominatim_short_address is not None and addr:
        short = format_nominatim_short_address(addr)
        display = normalize_address_dedupe(short) if normalize_address_dedupe else short  # type: ignore[misc]
    else:
        display = str(item.get("display_name") or address)
        if normalize_address_dedupe is not None:
            display = normalize_address_dedupe(display)  # type: ignore[misc]
    return lat, lon, display


def _nominatim_reverse_raw(lat: float, lon: float, zoom: int, *, layer: str = "") -> dict:
    params: Dict[str, str] = {
        "format": "jsonv2",
        "lat": f"{lat:.7f}",
        "lon": f"{lon:.7f}",
        "accept-language": "ru",
        "addressdetails": "1",
        "extratags": "1",
        "zoom": str(zoom),
    }
    if layer:
        params["layer"] = layer
    query = urlencode(params)
    data = request_json(f"{NOMINATIM_REVERSE}?{query}")
    if not isinstance(data, dict):
        raise RuntimeError("Не удалось определить адрес по точке на карте.")
    return data


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(min(1.0, a)))


def _short_from_osm_tags(tags: Dict[str, object]) -> str:
    if format_nominatim_short_address is None or osm_tags_to_address_dict is None:
        return ""
    addr = osm_tags_to_address_dict({str(k): v for k, v in tags.items()})  # type: ignore[misc]
    if not house_number_from_nominatim(addr):  # type: ignore[misc]
        return ""
    return format_nominatim_short_address(addr)  # type: ignore[misc]


def overpass_nearest_building_address(lat: float, lon: float, radius_m: int = 80) -> str:
    """Ближайшее здание с addr:housenumber в OSM (точнее для Москвы, чем reverse по улице)."""
    if osm_tags_to_address_dict is None:
        return ""
    query = f"""[out:json][timeout:20];
(
  node(around:{radius_m},{lat:.7f},{lon:.7f})["addr:housenumber"];
  way(around:{radius_m},{lat:.7f},{lon:.7f})["addr:housenumber"];
);
out center tags;"""
    try:
        import urllib.error
        import urllib.request

        req = urllib.request.Request(
            OVERPASS_INTERPRETER,
            data=query.encode("utf-8"),
            headers={"User-Agent": USER_AGENT, "Content-Type": "text/plain; charset=utf-8"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return ""
    elements = data.get("elements") if isinstance(data, dict) else None
    if not isinstance(elements, list):
        return ""
    best_short = ""
    best_dist = 1e18
    for el in elements:
        if not isinstance(el, dict):
            continue
        tags = el.get("tags") if isinstance(el.get("tags"), dict) else {}
        short = _short_from_osm_tags(tags)
        if not short:
            continue
        elat = el.get("lat")
        elon = el.get("lon")
        if elat is None or elon is None:
            center = el.get("center") if isinstance(el.get("center"), dict) else {}
            elat = center.get("lat")
            elon = center.get("lon")
        try:
            dist = _haversine_m(lat, lon, float(elat), float(elon))
        except (TypeError, ValueError):
            continue
        if dist < best_dist:
            best_dist = dist
            best_short = short
    if best_dist > float(radius_m) + 5.0:
        return ""
    return best_short


def photon_reverse_address(lat: float, lon: float) -> str:
    """Запасной геокодер (Komoot Photon), иногда даёт housenumber в РФ."""
    query = urlencode({"lat": f"{lat:.7f}", "lon": f"{lon:.7f}", "lang": "ru"})
    try:
        data = request_json(f"{PHOTON_REVERSE}?{query}", timeout=15)
    except Exception:
        return ""
    features = data.get("features") if isinstance(data, dict) else None
    if not isinstance(features, list) or not features:
        return ""
    props = features[0].get("properties") if isinstance(features[0], dict) else {}
    if not isinstance(props, dict):
        return ""
    pseudo = {
        "house_number": str(props.get("housenumber") or ""),
        "road": str(props.get("street") or props.get("name") or ""),
        "city": str(props.get("city") or props.get("state") or "Москва"),
        "unit": str(props.get("unit") or ""),
    }
    if format_nominatim_short_address is None or house_number_from_nominatim is None:
        return ""
    if not house_number_from_nominatim(pseudo):  # type: ignore[misc]
        return ""
    return format_nominatim_short_address(pseudo)  # type: ignore[misc]


def _address_has_house_number(text: str) -> bool:
    if not text:
        return False
    for part in reversed([p.strip() for p in text.split(",") if p.strip()]):
        if part and part[0].isdigit():
            return True
    return False


def _search_building_address_near(lat: float, lon: float, street: str, city: str) -> str:
    """Если reverse дал только улицу — ищем ближайший дом с номером."""
    if not street.strip():
        return ""
    q = f"{street}, {city}".strip(", ")
    query = urlencode(
        {
            "format": "jsonv2",
            "limit": "12",
            "addressdetails": "1",
            "accept-language": "ru",
            "q": q,
        }
    )
    data = request_json(f"{NOMINATIM_SEARCH}?{query}")
    if not isinstance(data, list):
        return ""
    best_short = ""
    best_dist = 1e18
    for item in data:
        if not isinstance(item, dict):
            continue
        addr = item.get("address") if isinstance(item.get("address"), dict) else {}
        if format_nominatim_short_address is None or house_number_from_nominatim is None:
            continue
        if not house_number_from_nominatim(addr):  # type: ignore[misc]
            continue
        try:
            dlat = float(item["lat"]) - lat
            dlon = float(item["lon"]) - lon
            dist = dlat * dlat + dlon * dlon
        except (KeyError, TypeError, ValueError):
            continue
        short = format_nominatim_short_address(addr)  # type: ignore[misc]
        if dist < best_dist:
            best_dist = dist
            best_short = short
    if best_dist > 0.0012:
        return ""
    return best_short


def reverse_geocode_address(lat: float, lon: float) -> Tuple[str, str]:
    """Возвращает (полный адрес OSM, короткий адрес для поля ввода)."""
    if format_nominatim_short_address is None:
        raise RuntimeError("Модуль archiview_project_model не загружен.")
    best_display = ""
    best_short = ""
    best_score = -1
    best_addr: Dict[str, object] = {}
    for zoom in (18, 17, 16):
        for layer in ("", "address", "building"):
            try:
                data = _nominatim_reverse_raw(lat, lon, zoom, layer=layer)
            except Exception:
                continue
            display = str(data.get("display_name") or "")
            addr = data.get("address") if isinstance(data.get("address"), dict) else {}
            short = format_nominatim_short_address(addr)  # type: ignore[misc]
            has_house = bool(house_number_from_nominatim(addr))  # type: ignore[misc]
            score = (3 if has_house else 0) + (1 if addr.get("road") or addr.get("pedestrian") else 0)
            if score > best_score:
                best_score = score
                best_display = display
                best_short = short
                best_addr = addr
    if best_score < 3:
        for radius in (45, 80, 120):
            over = overpass_nearest_building_address(lat, lon, radius_m=radius)
            if over:
                best_short = over
                best_score = 3
                break
    if best_score < 3:
        photon = photon_reverse_address(lat, lon)
        if photon:
            best_short = photon
            best_score = 3
    if best_score < 3:
        city = str(
            best_addr.get("city")
            or best_addr.get("town")
            or best_addr.get("municipality")
            or "Москва"
        )
        street = str(
            best_addr.get("road")
            or best_addr.get("pedestrian")
            or best_addr.get("footway")
            or ""
        )
        near = _search_building_address_near(lat, lon, street, city)
        if near:
            best_short = near
            best_score = 3
    if normalize_address_dedupe is not None:
        best_short = normalize_address_dedupe(best_short or best_display)  # type: ignore[misc]
    if not best_short:
        best_short = best_display
    return best_display, best_short


def normalize_annotation_list(annotations: List[dict]) -> List[dict]:
    """Убирает дубликаты полигонов и перенумеровывает id."""
    seen: set[Tuple[str, Tuple[Tuple[float, float], ...]]] = set()
    out: List[dict] = []
    for ann in annotations:
        if not isinstance(ann, dict):
            continue
        poly = ann.get("polygon") or []
        if not isinstance(poly, list) or len(poly) < 3:
            continue
        pts: List[Tuple[float, float]] = []
        for p in poly:
            if not isinstance(p, (list, tuple)) or len(p) < 2:
                continue
            try:
                pts.append((round(float(p[0]), 1), round(float(p[1]), 1)))
            except (TypeError, ValueError):
                continue
        if len(pts) < 3:
            continue
        key = (str(ann.get("class", "")), tuple(pts))
        if key in seen:
            continue
        seen.add(key)
        clean = dict(ann)
        clean["polygon"] = [[float(x), float(y)] for x, y in pts]
        out.append(clean)
    for idx, ann in enumerate(out, start=1):
        ann["id"] = idx
    return out


def pastvu_api(method: str, params: Dict[str, object]) -> object:
    payload = json.dumps(params, ensure_ascii=False, separators=(",", ":"))
    url = PASTVU_API + "?" + urlencode({"method": method, "params": payload})
    return request_json(url)


def _extract_photo_list(data: object) -> List[dict]:
    """PastVu responses have changed over time; accept several common shapes."""
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if not isinstance(data, dict):
        return []
    candidates = []
    for key in ("result", "photos", "data"):
        if key in data:
            candidates.append(data[key])
    for cand in candidates:
        if isinstance(cand, list):
            return [x for x in cand if isinstance(x, dict)]
        if isinstance(cand, dict):
            for key in ("photos", "items", "result", "data"):
                val = cand.get(key)
                if isinstance(val, list):
                    return [x for x in val if isinstance(x, dict)]
    return []


def _first(item: dict, *keys: str, default: str = "") -> str:
    for key in keys:
        if key in item and item[key] not in (None, ""):
            return str(item[key])
    return default


def parse_pastvu_photos(data: object) -> List[PastVuPhoto]:
    out: List[PastVuPhoto] = []
    for item in _extract_photo_list(data):
        cid_text = _first(item, "cid", "id", "photo", default="0")
        file_text = _first(item, "file", "src", "filename", default="")
        try:
            cid = int(float(cid_text))
        except Exception:
            cid = 0
        if not file_text:
            # Sometimes nearest endpoint may return cid only. Try to skip; GUI will explain if empty.
            continue
        geo = item.get("geo")
        lat = lon = ""
        if isinstance(geo, (list, tuple)) and len(geo) >= 2:
            lat, lon = str(geo[0]), str(geo[1])
        title = _first(item, "title", "name", "caption", "descr", "description", default="")
        year = _first(item, "year", "y", default="")
        year2 = _first(item, "year2", "y2", default="")
        distance = _first(item, "distance", "dist", default="")
        photo = PastVuPhoto(
            cid=cid,
            file=file_text,
            title=title,
            year=year,
            year2=year2,
            distance=distance,
            lat=lat,
            lon=lon,
            thumb_url=PASTVU_IMG_THUMB + file_text,
            standard_url=PASTVU_IMG_STANDARD + file_text,
            original_url=PASTVU_IMG_ORIGINAL + file_text,
            page_url=f"https://pastvu.com/p/{cid}" if cid else "https://pastvu.com/",
        )
        out.append(photo)
    return out


def find_pastvu_nearest(lat: float, lon: float, distance: int = 300, limit: int = 24,
                        year_from: Optional[int] = None, year_to: Optional[int] = None) -> List[PastVuPhoto]:
    params: Dict[str, object] = {"geo": [lat, lon], "distance": int(distance), "limit": min(int(limit), 30)}
    if year_from:
        params["year"] = int(year_from)
    if year_to:
        params["year2"] = int(year_to)
    data = pastvu_api("photo.giveNearestPhotos", params)
    return parse_pastvu_photos(data)


def download_pastvu_photo(photo: PastVuPhoto, folder: Path, prefer_original: bool = False) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    base = f"pastvu_{photo.cid}_{safe_filename(photo.years_label)}"
    target = folder / f"{base}.jpg"
    url = photo.original_url if prefer_original else photo.standard_url
    try:
        raw = request_bytes(url)
    except Exception:
        if prefer_original:
            raw = request_bytes(photo.standard_url)
        else:
            raise
    target.write_bytes(raw)
    (folder / f"{base}.json").write_text(json.dumps(asdict(photo), ensure_ascii=False, indent=2), encoding="utf-8")
    return target


# ---------------------------------------------------------------------------
# Geometry, rectification, outputs
# ---------------------------------------------------------------------------

def facade_output_size(old_pts: np.ndarray, new_pts: np.ndarray, max_dim: int = 2600) -> Tuple[int, int]:
    def size(pts: np.ndarray) -> Tuple[float, float]:
        tl, tr, br, bl = pts.astype(np.float64)
        width = max(np.linalg.norm(tr - tl), np.linalg.norm(br - bl))
        height = max(np.linalg.norm(bl - tl), np.linalg.norm(br - tr))
        return max(width, 2.0), max(height, 2.0)

    ow, oh = size(old_pts)
    nw, nh = size(new_pts)
    # Use the more detailed source as a base, but cap the longest side.
    out_w = max(ow, nw)
    out_h = max(oh, nh)
    scale = min(1.0, float(max_dim) / max(out_w, out_h))
    out_w = max(2, int(round(out_w * scale)))
    out_h = max(2, int(round(out_h * scale)))
    return out_w, out_h


def warp_facade_to_rect(img: np.ndarray, pts: np.ndarray, out_w: int, out_h: int) -> Tuple[np.ndarray, np.ndarray]:
    dst = np.array([[0, 0], [out_w - 1, 0], [out_w - 1, out_h - 1], [0, out_h - 1]], dtype=np.float32)
    H = cv.getPerspectiveTransform(pts.astype(np.float32), dst)
    warped = cv.warpPerspective(img, H, (out_w, out_h), flags=cv.INTER_CUBIC, borderMode=cv.BORDER_REPLICATE)
    return warped, H



def _expand_facade_quad(pts: np.ndarray, expand_ratio: float = 0.45) -> np.ndarray:
    """Расширить четырёхугольник фасада вокруг центра — контекст без всего кадра."""
    ctr = pts.astype(np.float64).mean(axis=0)
    return pts.astype(np.float64) + (pts.astype(np.float64) - ctr) * float(expand_ratio)


def _clip_quad_to_image(pts: np.ndarray, shape: Tuple[int, ...]) -> np.ndarray:
    h, w = int(shape[0]), int(shape[1])
    out = pts.astype(np.float64).copy()
    out[:, 0] = np.clip(out[:, 0], 0.0, float(max(0, w - 1)))
    out[:, 1] = np.clip(out[:, 1], 0.0, float(max(0, h - 1)))
    return out


def _warp_quad(quad: np.ndarray, H: np.ndarray) -> np.ndarray:
    return cv.perspectiveTransform(quad.reshape(-1, 1, 2).astype(np.float32), H).reshape(-1, 2)


def warp_pair_keep_context(
    old_img: np.ndarray,
    old_pts: np.ndarray,
    modern_img: np.ndarray,
    modern_pts: np.ndarray,
    out_w: int,
    out_h: int,
    margin: int = 80,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Выпрямить оба исходных снимка в общую систему координат с полным контекстом.

    Четыре угла задают плоскость фасада для наложения; в кадр попадает весь
    выпрямленный исходник (как на экране «до/после»), а не обрезка по маске.
    """
    dst = np.array([[0, 0], [out_w - 1, 0], [out_w - 1, out_h - 1], [0, out_h - 1]], dtype=np.float32)
    H_old_core = cv.getPerspectiveTransform(old_pts.astype(np.float32), dst)
    H_mod_core = cv.getPerspectiveTransform(modern_pts.astype(np.float32), dst)

    def transformed_bounds(img: np.ndarray, H: np.ndarray) -> np.ndarray:
        h, w = img.shape[:2]
        corners = np.array([[[0, 0]], [[w - 1, 0]], [[w - 1, h - 1]], [[0, h - 1]]], dtype=np.float32)
        return cv.perspectiveTransform(corners, H).reshape(-1, 2)

    all_pts = np.vstack([
        transformed_bounds(old_img, H_old_core),
        transformed_bounds(modern_img, H_mod_core),
        dst.astype(np.float32),
    ])
    min_xy = np.floor(all_pts.min(axis=0) - margin).astype(float)
    max_xy = np.ceil(all_pts.max(axis=0) + margin).astype(float)
    canvas_w = int(max(2, max_xy[0] - min_xy[0]))
    canvas_h = int(max(2, max_xy[1] - min_xy[1]))

    # Avoid accidental gigantic canvases when the four points are nearly degenerate.
    max_side = 4200
    scale = min(1.0, max_side / float(max(canvas_w, canvas_h)))
    T = np.array([[scale, 0, -min_xy[0] * scale], [0, scale, -min_xy[1] * scale], [0, 0, 1]], dtype=np.float64)
    canvas_w = int(max(2, round(canvas_w * scale)))
    canvas_h = int(max(2, round(canvas_h * scale)))
    H_old = T @ H_old_core
    H_modern = T @ H_mod_core

    border = (0, 0, 0)
    old_rect = cv.warpPerspective(old_img, H_old, (canvas_w, canvas_h), flags=cv.INTER_CUBIC, borderMode=cv.BORDER_CONSTANT, borderValue=border)
    modern_rect = cv.warpPerspective(modern_img, H_modern, (canvas_w, canvas_h), flags=cv.INTER_CUBIC, borderMode=cv.BORDER_CONSTANT, borderValue=border)
    return old_rect, modern_rect, H_old, H_modern


def _content_mask(img: np.ndarray) -> np.ndarray:
    """Маска «есть картинка», без белых/серых полей выпрямления."""
    if cv is None:
        return np.ones(img.shape[:2], dtype=np.uint8)
    if img.ndim == 3:
        b, g, r = cv.split(img.astype(np.uint8))
        maxc = np.maximum(np.maximum(b, g), r)
        minc = np.minimum(np.minimum(b, g), r)
        chroma = maxc.astype(np.int16) - minc.astype(np.int16)
        empty = (maxc >= 228) & (chroma <= 14)
        return (~empty).astype(np.uint8)
    gray = img if img.ndim == 2 else cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    return (gray < 228).astype(np.uint8)


def _content_bbox(img: np.ndarray, *, pad: int = 6) -> Tuple[int, int, int, int]:
    if cv is None:
        h, w = img.shape[:2]
        return 0, 0, w, h
    mask = (_content_mask(img) * 255).astype(np.uint8)
    coords = cv.findNonZero(mask)
    if coords is None:
        h, w = img.shape[:2]
        return 0, 0, w, h
    x, y, w, h = cv.boundingRect(coords)
    H, W = img.shape[:2]
    x0 = max(0, int(x) - pad)
    y0 = max(0, int(y) - pad)
    x1 = min(W, int(x + w) + pad)
    y1 = min(H, int(y + h) + pad)
    return x0, y0, x1, y1


def _bbox_area(box: Tuple[int, int, int, int]) -> int:
    x0, y0, x1, y1 = box
    return max(0, x1 - x0) * max(0, y1 - y0)


def crop_white_margins_pair(
    old_rect: np.ndarray,
    modern_rect: np.ndarray,
    *,
    pad: int = 12,
) -> Tuple[np.ndarray, np.ndarray, Tuple[int, int]]:
    """Лёгкая обрезка пустых полей — только для режима «только 4 угла», без контекста."""
    full = old_rect.shape[0] * old_rect.shape[1]
    boxes = [_content_bbox(im, pad=pad) for im in (old_rect, modern_rect)]
    x0 = max(0, min(b[0] for b in boxes) - pad)
    y0 = max(0, min(b[1] for b in boxes) - pad)
    x1 = min(old_rect.shape[1], max(b[2] for b in boxes) + pad)
    y1 = min(old_rect.shape[0], max(b[3] for b in boxes) + pad)
    if x1 - x0 < 40 or y1 - y0 < 40 or _bbox_area((x0, y0, x1, y1)) >= full * 0.97:
        return old_rect, modern_rect, (0, 0)
    return (
        old_rect[y0:y1, x0:x1].copy(),
        modern_rect[y0:y1, x0:x1].copy(),
        (x0, y0),
    )


def _translate_homography(H: np.ndarray, dx: float, dy: float) -> np.ndarray:
    T = np.array([[1.0, 0.0, -dx], [0.0, 1.0, -dy], [0.0, 0.0, 1.0]], dtype=np.float64)
    return T @ H


def create_comparison_for_labeling(old_rect: np.ndarray, new_rect: np.ndarray) -> np.ndarray:
    """Create a calm comparison image for manual markup.

    Earlier versions used red/cyan channels. That was technically clear, but visually
    tiring on old facade photos. Here the modern image is muted and the historical
    image is boosted in grayscale, so the user can still read architecture.
    """
    old_gray = cv.cvtColor(old_rect, cv.COLOR_BGR2GRAY)
    old_gray = cv.equalizeHist(old_gray)
    old_gray = cv.convertScaleAbs(old_gray, alpha=1.18, beta=6)
    old_bgr = cv.cvtColor(old_gray, cv.COLOR_GRAY2BGR)

    modern_muted = cv.convertScaleAbs(new_rect, alpha=0.62, beta=18)
    modern_gray = cv.cvtColor(modern_muted, cv.COLOR_BGR2GRAY)
    # Reduce saturation but keep a little color so the contemporary photo is readable.
    modern_soft = cv.addWeighted(modern_muted, 0.35, cv.cvtColor(modern_gray, cv.COLOR_GRAY2BGR), 0.65, 0)
    comp = cv.addWeighted(modern_soft, 0.52, old_bgr, 0.48, 0)
    return comp


def image_to_base64_png(path: Path) -> str:
    img = cv_read(path)
    ok, enc = cv.imencode(".png", img)
    if not ok:
        raise RuntimeError(f"Не удалось закодировать картинку для HTML: {path}")
    return base64.b64encode(enc.tobytes()).decode("ascii")


def write_overlay_html(out_path: Path, old_img: Path, new_img: Path, old_opacity: int = 70) -> None:
    old64 = image_to_base64_png(old_img)
    new64 = image_to_base64_png(new_img)
    html = f"""<!doctype html>
<html lang=\"ru\">
<head><meta charset=\"utf-8\"><title>Archiview overlay</title>
<style>
body{{font-family:Arial,sans-serif;margin:20px;background:#f6f6f6;color:#222}}
.wrap{{max-width:1200px;margin:auto}}
.stage{{position:relative;display:inline-block;box-shadow:0 2px 16px #999;background:white;overflow:auto;max-width:100%}}
.stage img{{display:block;max-width:100%;height:auto}}
#old{{position:absolute;left:0;top:0;opacity:{old_opacity/100:.2f};filter:grayscale(1) contrast(1.25) brightness(1.05)}}
#new{{filter:saturate(.45) brightness(.80) contrast(.96)}}
.controls{{margin:16px 0;padding:12px;background:white;border-radius:8px;box-shadow:0 1px 8px #ccc}}
.row{{margin:10px 0}}
input[type=range]{{width:480px;max-width:90%}}
.note{{color:#555;line-height:1.45}}
</style></head>
<body><div class=\"wrap\">
<h2>Наложение исторического и современного фасада</h2>
<div class=\"controls\">
<div class=\"row\">Видимость старого фото: <b id=\"oldVal\">{old_opacity}%</b><br><input id=\"oldSlider\" type=\"range\" min=\"0\" max=\"100\" value=\"{old_opacity}\"></div>
<div class=\"row\">Приглушить современное фото: <b id=\"newVal\">80%</b><br><input id=\"newSlider\" type=\"range\" min=\"35\" max=\"120\" value=\"80\"></div>
<div class=\"row\">Контраст исторического фото: <b id=\"contrastVal\">125%</b><br><input id=\"contrastSlider\" type=\"range\" min=\"80\" max=\"220\" value=\"125\"></div>
</div>
<div class=\"stage\"><img id=\"new\" src=\"data:image/png;base64,{new64}\"><img id=\"old\" src=\"data:image/png;base64,{old64}\"></div>
<p class=\"note\">Современное фото специально можно приглушить, а историческое — сделать контрастнее. Так обычно легче глазами увидеть надстройки, пристройки и изменённые проёмы.</p>
</div>
<script>
const oldS=document.getElementById('oldSlider'), newS=document.getElementById('newSlider'), cS=document.getElementById('contrastSlider');
const old=document.getElementById('old'), modern=document.getElementById('new');
const oldVal=document.getElementById('oldVal'), newVal=document.getElementById('newVal'), contrastVal=document.getElementById('contrastVal');
function update(){{
  old.style.opacity=oldS.value/100; oldVal.textContent=oldS.value+'%';
  modern.style.filter='saturate(.45) brightness('+(newS.value/100)+') contrast(.96)'; newVal.textContent=newS.value+'%';
  old.style.filter='grayscale(1) contrast('+(cS.value/100)+') brightness(1.05)'; contrastVal.textContent=cS.value+'%';
}}
oldS.oninput=update; newS.oninput=update; cS.oninput=update; update();
</script></body></html>"""
    out_path.write_text(html, encoding="utf-8")


def write_before_after_html(out_path: Path, old_img: Path, new_img: Path) -> None:
    old64 = image_to_base64_png(old_img)
    new64 = image_to_base64_png(new_img)
    html = f"""<!doctype html>
<html lang=\"ru\"><head><meta charset=\"utf-8\"><title>Archiview до/после</title>
<style>
body{{font-family:Arial,sans-serif;margin:20px;background:#f6f6f6;color:#222}}
.wrap{{max-width:1100px;margin:auto}}
.stage{{position:relative;display:inline-block;box-shadow:0 2px 16px #999;background:white;overflow:hidden}}
.stage img{{display:block;max-width:100%;height:auto}}
#new{{position:absolute;left:0;top:0;clip-path:inset(0 0 0 50%)}}
.controls{{margin:16px 0;padding:12px;background:white;border-radius:8px;box-shadow:0 1px 8px #ccc}}
input[type=range]{{width:420px;max-width:90%}}
.label{{margin-top:8px;color:#555}}
</style></head><body><div class=\"wrap\">
<h2>До / после: исторический фасад ↔ современный фасад</h2>
<div class=\"controls\">Граница сравнения: <b id=\"val\">50%</b><br><input id=\"slider\" type=\"range\" min=\"0\" max=\"100\" value=\"50\"></div>
<div class=\"stage\"><img id=\"old\" src=\"data:image/png;base64,{old64}\"><img id=\"new\" src=\"data:image/png;base64,{new64}\"></div>
<div class=\"label\">Слева видна историческая часть, справа — современная. Двигайте ползунок.</div>
</div><script>
const s=document.getElementById('slider'), n=document.getElementById('new'), val=document.getElementById('val');
s.oninput=()=>{{n.style.clipPath='inset(0 0 0 '+s.value+'%)'; val.textContent=s.value+'%';}};
</script></body></html>"""
    out_path.write_text(html, encoding="utf-8")


def prepare_rectified_project(
    old_path: Path,
    modern_path: Path,
    old_points_text: str,
    modern_points_text: str,
    outdir: Path,
    old_opacity_percent: int = 70,
    pastvu_meta: Optional[dict] = None,
    modern_meta: Optional[dict] = None,
    keep_context: bool = True,
    crop_white: bool = True,
    old_crop_rect_text: str = "",
    modern_crop_rect_text: str = "",
) -> Dict[str, object]:
    if cv is None:
        raise RuntimeError("OpenCV не установлен.")
    outdir.mkdir(parents=True, exist_ok=True)
    old_img = cv_read(old_path)
    modern_img = cv_read(modern_path)
    old_pts = parse_four_points(old_points_text)
    modern_pts = parse_four_points(modern_points_text)
    old_img, old_off = apply_source_crop(old_img, old_crop_rect_text)
    modern_img, modern_off = apply_source_crop(modern_img, modern_crop_rect_text)
    old_pts = shift_points_after_crop(old_pts, old_off)
    modern_pts = shift_points_after_crop(modern_pts, modern_off)
    out_w, out_h = facade_output_size(old_pts, modern_pts)

    if keep_context:
        old_rect, modern_rect, H_old_to_rect, H_modern_to_rect = warp_pair_keep_context(
            old_img, old_pts, modern_img, modern_pts, out_w, out_h
        )
    else:
        old_rect, H_old_to_rect = warp_facade_to_rect(old_img, old_pts, out_w, out_h)
        modern_rect, H_modern_to_rect = warp_facade_to_rect(modern_img, modern_pts, out_w, out_h)
    H_rect_to_modern = np.linalg.inv(H_modern_to_rect)
    crop_offset = (0, 0)
    # С контекстом исходника не обрезаем выпрямленные файлы — 4 угла только для геометрии наложения.
    if crop_white and not keep_context:
        old_rect, modern_rect, crop_offset = crop_white_margins_pair(old_rect, modern_rect)
        if crop_offset != (0, 0):
            dx, dy = crop_offset
            H_old_to_rect = _translate_homography(H_old_to_rect, dx, dy)
            H_modern_to_rect = _translate_homography(H_modern_to_rect, dx, dy)
            H_rect_to_modern = np.linalg.inv(H_modern_to_rect)

    alpha_old = max(0, min(100, int(old_opacity_percent))) / 100.0
    overlay = cv.addWeighted(modern_rect, 1.0 - alpha_old, old_rect, alpha_old, 0)
    comparison = create_comparison_for_labeling(old_rect, modern_rect)

    paths = {
        "overlay_png": outdir / "01_overlay.png",
        "overlay_html": outdir / "01_overlay_slider.html",
        "before_after_html": outdir / "02_before_after_slider.html",
        "historical_rectified": outdir / "03_historical_rectified.png",
        "modern_rectified": outdir / "04_modern_rectified.png",
        "comparison_for_labeling": outdir / "05_comparison_for_labeling.png",
        "project_json": outdir / "project_v8.json",
    }
    cv_write(paths["historical_rectified"], old_rect)
    cv_write(paths["modern_rectified"], modern_rect)
    cv_write(paths["overlay_png"], overlay)
    cv_write(paths["comparison_for_labeling"], comparison)
    write_overlay_html(paths["overlay_html"], paths["historical_rectified"], paths["modern_rectified"], old_opacity_percent)
    write_before_after_html(paths["before_after_html"], paths["historical_rectified"], paths["modern_rectified"])

    project = {
        "version": APP_VERSION,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "historical_image": str(old_path),
        "modern_image": str(modern_path),
        "pastvu": pastvu_meta or {},
        "modern_source": modern_meta or {},
        "old_points_tl_tr_br_bl": old_pts.tolist(),
        "modern_points_tl_tr_br_bl": modern_pts.tolist(),
        "rectified_size": {"width": int(old_rect.shape[1]), "height": int(old_rect.shape[0])},
        "keep_context_outside_four_points": bool(keep_context),
        "crop_white_margins": bool(crop_white),
        "crop_offset_xy": list(crop_offset),
        "old_crop_rect_text": old_crop_rect_text,
        "modern_crop_rect_text": modern_crop_rect_text,
        "old_crop_offset_xy": [float(old_off[0]), float(old_off[1])],
        "modern_crop_offset_xy": [float(modern_off[0]), float(modern_off[1])],
        "H_old_to_rect": H_old_to_rect.tolist(),
        "H_modern_to_rect": H_modern_to_rect.tolist(),
        "H_rect_to_modern": H_rect_to_modern.tolist(),
        "outputs": {k: str(v) for k, v in paths.items() if k != "project_json"},
    }
    paths["project_json"].write_text(json.dumps(project, ensure_ascii=False, indent=2), encoding="utf-8")
    return project


def polygon_area(points: List[Point]) -> float:
    if len(points) < 3:
        return 0.0
    arr = np.asarray(points, dtype=np.float32)
    return abs(float(cv.contourArea(arr.reshape(-1, 1, 2)))) if cv is not None else 0.0


def polygon_bbox(points: List[Point]) -> List[float]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    return [float(x0), float(y0), float(x1 - x0), float(y1 - y0)]


def point_in_polygon(x: float, y: float, polygon: List[Point]) -> bool:
    """Ray casting — для hover/tooltip на итоговой картинке."""
    n = len(polygon)
    if n < 3:
        return False
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = float(polygon[i][0]), float(polygon[i][1])
        xj, yj = float(polygon[j][0]), float(polygon[j][1])
        if (yi > y) != (yj > y):
            xinters = (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi
            if x < xinters:
                inside = not inside
        j = i
    return inside


def _bgr_to_hex(bgr: Tuple[int, int, int]) -> str:
    b, g, r = bgr
    return f"#{r:02x}{g:02x}{b:02x}"


def _put_index_on_cv(img: np.ndarray, x: int, y: int, idx: int, color: Tuple[int, int, int]) -> None:
    """Номер области: цвет типа, без чёрной подложки, с тонким halo для читаемости."""
    text = str(idx)
    scale = max(0.55, min(1.4, img.shape[1] / 2200.0))
    thickness = max(2, int(round(scale * 2.5)))
    halo = (255, 255, 255)
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-1, 1), (1, -1)):
        cv.putText(img, text, (x + dx, y + dy), cv.FONT_HERSHEY_SIMPLEX, scale, halo, thickness + 2, cv.LINE_AA)
    cv.putText(img, text, (x, y), cv.FONT_HERSHEY_SIMPLEX, scale, color, thickness, cv.LINE_AA)


def _canvas_draw_index_label(canvas: tk.Canvas, x: float, y: float, text: str, color: str, tags: str = "") -> None:
    font = ("TkDefaultFont", 13, "bold")
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)):
        canvas.create_text(x + dx, y + dy, text=text, fill="#ffffff", font=font, tags=tags)
    canvas.create_text(x, y, text=text, fill=color, font=font, tags=tags)


def draw_polygons_on_image(
    img: np.ndarray,
    annotations: List[dict],
    transform: Optional[np.ndarray] = None,
    *,
    draw_indices: bool = True,
) -> np.ndarray:
    out = img.copy()
    overlay = out.copy()
    for idx, ann in enumerate(annotations, start=1):
        cls = ann.get("class", "added_architecture")
        color = CLASS_COLORS.get(cls, (0, 190, 0))
        pts = np.asarray(ann.get("polygon", []), dtype=np.float32)
        if pts.shape[0] < 3:
            continue
        if transform is not None:
            pts = cv.perspectiveTransform(pts.reshape(-1, 1, 2), transform).reshape(-1, 2)
        pts_i = np.round(pts).astype(np.int32).reshape(-1, 1, 2)
        cv.fillPoly(overlay, [pts_i], color)
        cv.polylines(out, [pts_i], True, color, 4, cv.LINE_AA)
    out = cv.addWeighted(overlay, 0.22, out, 0.78, 0)
    # Draw outlines one more time over the fill.
    for idx, ann in enumerate(annotations, start=1):
        cls = ann.get("class", "added_architecture")
        color = CLASS_COLORS.get(cls, (0, 190, 0))
        pts = np.asarray(ann.get("polygon", []), dtype=np.float32)
        if pts.shape[0] < 3:
            continue
        if transform is not None:
            pts = cv.perspectiveTransform(pts.reshape(-1, 1, 2), transform).reshape(-1, 2)
        pts_i = np.round(pts).astype(np.int32).reshape(-1, 1, 2)
        cv.polylines(out, [pts_i], True, color, 4, cv.LINE_AA)
    if draw_indices:
        for idx, ann in enumerate(annotations, start=1):
            cls = ann.get("class", "added_architecture")
            color = CLASS_COLORS.get(cls, (0, 190, 0))
            pts = np.asarray(ann.get("polygon", []), dtype=np.float32)
            if pts.shape[0] < 3:
                continue
            if transform is not None:
                pts = cv.perspectiveTransform(pts.reshape(-1, 1, 2), transform).reshape(-1, 2)
            pts_i = np.round(pts).astype(np.int32)
            x, y = pts_i.mean(axis=0).astype(int)
            _put_index_on_cv(out, int(x), int(y), idx, color)
    return out


def save_annotations_and_exports(outdir: Path, annotations: List[dict]) -> Dict[str, str]:
    project_path = outdir / "project_v8.json"
    if not project_path.exists():
        project_path = outdir / "project_v7.json"
    if not project_path.exists():
        # Compatibility with projects created by v6.
        project_path = outdir / "project_v6.json"
    if not project_path.exists():
        raise RuntimeError("Не найден project_v8.json. Сначала подготовьте overlay и выпрямленную пару.")
    project = json.loads(project_path.read_text(encoding="utf-8"))
    outputs = project.get("outputs", {})
    modern_rect_path = Path(outputs.get("modern_rectified", outdir / "04_modern_rectified.png"))
    comparison_path = Path(outputs.get("comparison_for_labeling", outdir / "05_comparison_for_labeling.png"))
    modern_src_path = Path(project.get("modern_image"))
    crop_fb = modern_crop_rect_from_metadata_near(outdir)
    H_rect_to_modern = H_rect_to_full_modern_from_project(project, fallback_rect_text=crop_fb)

    ann_dir = outdir / "annotations"
    ann_dir.mkdir(parents=True, exist_ok=True)
    manual_json = ann_dir / "manual_annotations.json"
    payload = {
        "version": APP_VERSION,
        "image": str(comparison_path),
        "rectified_size": project.get("rectified_size"),
        "annotations": annotations,
        "classes": CLASS_LABELS,
    }
    manual_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    annotations = normalize_annotation_list(annotations)
    modern_rect = cv_read(modern_rect_path)
    modern_src = cv_read(modern_src_path)
    marked_rect = draw_polygons_on_image(modern_rect, annotations, transform=None, draw_indices=False)
    marked_src = draw_polygons_on_image(modern_src, annotations, transform=H_rect_to_modern, draw_indices=False)

    marked_rect_path = outdir / "06_marked_rectified.png"
    marked_src_path = outdir / "07_marked_on_original_modern.png"
    cv_write(marked_rect_path, marked_rect)
    cv_write(marked_src_path, marked_src)

    coco_root = outdir / "roboflow_export"
    images_dir = coco_root / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    coco_image_name = "images/comparison_for_labeling.png"
    shutil.copy2(comparison_path, coco_root / coco_image_name)

    img = cv_read(comparison_path)
    h, w = img.shape[:2]
    categories = []
    class_to_id = {}
    for idx, key in enumerate(CLASS_LABELS.keys(), start=1):
        categories.append({"id": idx, "name": key, "supercategory": "architecture_change"})
        class_to_id[key] = idx

    coco_annotations = []
    for ann_id, ann in enumerate(annotations, start=1):
        pts = [(float(x), float(y)) for x, y in ann.get("polygon", [])]
        if len(pts) < 3:
            continue
        flat = [coord for pt in pts for coord in pt]
        cls = ann.get("class", "added_architecture")
        coco_annotations.append(
            {
                "id": ann_id,
                "image_id": 1,
                "category_id": class_to_id.get(cls, 1),
                "segmentation": [flat],
                "area": polygon_area(pts),
                "bbox": polygon_bbox(pts),
                "iscrowd": 0,
            }
        )

    coco = {
        "info": {"description": "Archiview CV v11 manual facade change annotations", "version": "v11"},
        "licenses": [],
        "images": [{"id": 1, "file_name": coco_image_name, "width": int(w), "height": int(h)}],
        "annotations": coco_annotations,
        "categories": categories,
    }
    coco_path = coco_root / "_annotations.coco.json"
    coco_path.write_text(json.dumps(coco, ensure_ascii=False, indent=2), encoding="utf-8")

    zip_path = outdir / "roboflow_export.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file in coco_root.rglob("*"):
            if file.is_file():
                zf.write(file, file.relative_to(coco_root))

    return {
        "manual_json": str(manual_json),
        "marked_rectified": str(marked_rect_path),
        "marked_on_original_modern": str(marked_src_path),
        "coco": str(coco_path),
        "roboflow_zip": str(zip_path),
    }


# ---------------------------------------------------------------------------
# Point picker windows
# ---------------------------------------------------------------------------


class CropWindow(tk.Toplevel):
    """Simple rectangular crop tool. Saves no file itself; returns bbox in original pixels."""

    def __init__(self, parent: tk.Tk, image_path: str, title: str, callback: Callable[[Tuple[int, int, int, int]], None]) -> None:
        super().__init__(parent)
        self.title(title)
        self.geometry("940x760")
        self.minsize(760, 620)
        self.callback = callback
        self.start: Optional[Point] = None
        self.end: Optional[Point] = None
        try:
            self.photo, self.scale, self.disp_w, self.disp_h, self.orig_w, self.orig_h = cv_to_photoimage(image_path, 860, 590)
        except Exception as exc:
            messagebox.showerror("Не удалось открыть фото", str(exc), parent=parent)
            self.destroy()
            return
        ttk.Label(
            self,
            text="Выделите мышкой нужную область фасада. Это удобно после Win+Shift+S или после загрузки фото из открытого источника.",
            wraplength=880,
        ).pack(anchor="w", padx=12, pady=(10, 4))
        self.canvas = tk.Canvas(self, width=self.disp_w, height=self.disp_h, bg="#eeeeee", highlightthickness=1)
        self.canvas.pack(anchor="center", padx=12, pady=8)
        self.canvas.create_image(0, 0, image=self.photo, anchor="nw")
        self.canvas.bind("<ButtonPress-1>", self._down)
        self.canvas.bind("<B1-Motion>", self._drag)
        self.canvas.bind("<ButtonRelease-1>", self._up)
        self.status = tk.StringVar(value="Зажмите левую кнопку мыши и растяните прямоугольник.")
        ttk.Label(self, textvariable=self.status, font=("TkDefaultFont", 10, "bold")).pack(anchor="w", padx=12, pady=4)
        btns = ttk.Frame(self)
        btns.pack(anchor="w", padx=12, pady=10)
        ttk.Button(btns, text="Сохранить обрезанную область", command=self.done).pack(side="left")
        ttk.Button(btns, text="Очистить", command=self.clear).pack(side="left", padx=8)
        ttk.Button(btns, text="Закрыть", command=self.destroy).pack(side="left", padx=8)
        self.grab_set()

    def _clamp(self, x: float, y: float) -> Point:
        return (max(0, min(float(x), self.disp_w)), max(0, min(float(y), self.disp_h)))

    def _down(self, event: tk.Event) -> None:
        self.start = self._clamp(event.x, event.y)
        self.end = self.start
        self._redraw()

    def _drag(self, event: tk.Event) -> None:
        if self.start is None:
            return
        self.end = self._clamp(event.x, event.y)
        self._redraw()

    def _up(self, event: tk.Event) -> None:
        if self.start is None:
            return
        self.end = self._clamp(event.x, event.y)
        self._redraw()

    def _redraw(self) -> None:
        self.canvas.delete("crop")
        if self.start is None or self.end is None:
            return
        x0, y0 = self.start
        x1, y1 = self.end
        self.canvas.create_rectangle(x0, y0, x1, y1, outline="#00a6a6", width=3, tags="crop")
        w = abs(x1 - x0) / self.scale
        h = abs(y1 - y0) / self.scale
        self.status.set(f"Выделение: примерно {int(w)} × {int(h)} пикселей. Нажмите “Сохранить обрезанную область”.")

    def clear(self) -> None:
        self.start = None
        self.end = None
        self.canvas.delete("crop")
        self.status.set("Зажмите левую кнопку мыши и растяните прямоугольник.")

    def done(self) -> None:
        if self.start is None or self.end is None:
            messagebox.showinfo("Нет выделения", "Сначала выделите область мышкой.", parent=self)
            return
        x0, y0 = self.start
        x1, y1 = self.end
        ox0, ox1 = sorted([int(round(x0 / self.scale)), int(round(x1 / self.scale))])
        oy0, oy1 = sorted([int(round(y0 / self.scale)), int(round(y1 / self.scale))])
        ox0, oy0 = max(0, ox0), max(0, oy0)
        ox1, oy1 = min(self.orig_w, ox1), min(self.orig_h, oy1)
        if ox1 - ox0 < 30 or oy1 - oy0 < 30:
            messagebox.showinfo("Слишком маленькая область", "Выделите область покрупнее.", parent=self)
            return
        self.callback((ox0, oy0, ox1, oy1))
        self.destroy()

class FacadePointPicker(tk.Toplevel):
    """Pick four facade corners in order TL, TR, BR, BL."""

    NAMES = [
        "верхний левый угол фасада",
        "верхний правый угол фасада",
        "нижний правый угол фасада",
        "нижний левый угол фасада",
    ]

    def __init__(self, parent: tk.Tk, image_path: str, title: str, callback: Callable[[str], None]) -> None:
        super().__init__(parent)
        self.title(title)
        self.geometry("860x760")
        self.minsize(760, 620)
        self.callback = callback
        self.points: List[Point] = []

        try:
            self.photo, self.scale, self.disp_w, self.disp_h, self.orig_w, self.orig_h = cv_to_photoimage(image_path, 790, 580)
        except Exception as exc:
            messagebox.showerror("Не удалось открыть фото", str(exc), parent=parent)
            self.destroy()
            return

        intro = (
            "Кликните 4 угла одного и того же фасада в порядке: верх-лево, верх-право, низ-право, низ-лево. "
            "На старом и новом фото нужно выбрать именно одну и ту же плоскость фасада."
        )
        ttk.Label(self, text=intro, wraplength=820).pack(anchor="w", padx=12, pady=(10, 4))

        self.canvas = tk.Canvas(self, width=self.disp_w, height=self.disp_h, bg="#eeeeee", highlightthickness=1)
        self.canvas.pack(anchor="center", padx=12, pady=8)
        self.canvas.create_image(0, 0, image=self.photo, anchor="nw")
        self.canvas.bind("<Button-1>", self._click)

        self.status = tk.StringVar()
        ttk.Label(self, textvariable=self.status, font=("TkDefaultFont", 10, "bold")).pack(anchor="w", padx=12, pady=4)

        btns = ttk.Frame(self)
        btns.pack(anchor="w", padx=12, pady=10)
        ttk.Button(btns, text="Отменить последнюю точку", command=self.undo).pack(side="left")
        ttk.Button(btns, text="Очистить", command=self.clear).pack(side="left", padx=8)
        ttk.Button(btns, text="Готово, использовать эти 4 угла", command=self.done).pack(side="left", padx=8)
        ttk.Button(btns, text="Закрыть", command=self.destroy).pack(side="left", padx=8)

        self._redraw()
        self.grab_set()

    def _click(self, event: tk.Event) -> None:
        if len(self.points) >= 4:
            self.status.set("Уже выбрано 4 точки. Нажмите “Готово” или отмените последнюю точку.")
            return
        if not (0 <= event.x <= self.disp_w and 0 <= event.y <= self.disp_h):
            return
        self.points.append((event.x / self.scale, event.y / self.scale))
        self._redraw()

    def _redraw(self) -> None:
        self.canvas.delete("marker")
        for i, pt in enumerate(self.points, start=1):
            x = pt[0] * self.scale
            y = pt[1] * self.scale
            r = 10
            self.canvas.create_oval(x - r, y - r, x + r, y + r, fill="#d92323", outline="white", width=2, tags="marker")
            self.canvas.create_text(x, y, text=str(i), fill="white", font=("TkDefaultFont", 9, "bold"), tags="marker")
        if len(self.points) < 4:
            self.status.set(f"Точка {len(self.points) + 1} из 4: кликните {self.NAMES[len(self.points)]}.")
        else:
            self.status.set("Все 4 угла выбраны. Нажмите “Готово”.")

    def undo(self) -> None:
        if self.points:
            self.points.pop()
        self._redraw()

    def clear(self) -> None:
        self.points.clear()
        self._redraw()

    def done(self) -> None:
        if len(self.points) != 4:
            messagebox.showinfo("Нужно 4 точки", "Поставьте ровно 4 угла фасада.", parent=self)
            return
        pts = np.asarray(self.points, dtype=np.float32)
        ok, msg = validate_facade_quad_points(pts)
        if not ok:
            messagebox.showwarning("Проверьте углы", msg, parent=self)
            return
        self.callback(points_to_cli(self.points))
        self.destroy()


class AnnotationWindow(tk.Toplevel):
    """Draw polygon annotations on the rectified comparison image."""

    def __init__(self, parent: tk.Tk, outdir: Path, on_saved: Callable[[Dict[str, str]], None]) -> None:
        super().__init__(parent)
        self.title("Разметка новых элементов фасада")
        self.geometry("1180x820")
        self.minsize(980, 680)
        self.outdir = outdir
        self.on_saved = on_saved
        self.annotations: List[dict] = []
        self.current_points: List[Point] = []
        self.class_var = tk.StringVar(value="added_architecture")

        self.image_path = outdir / "05_comparison_for_labeling.png"
        if not self.image_path.exists():
            messagebox.showerror(
                "Нет картинки для разметки",
                "Сначала нажмите “Подготовить overlay и разметку”. Не найден файл 05_comparison_for_labeling.png.",
                parent=parent,
            )
            self.destroy()
            return

        try:
            self.photo, self.scale, self.disp_w, self.disp_h, self.orig_w, self.orig_h = cv_to_photoimage(self.image_path, 1040, 650)
        except Exception as exc:
            messagebox.showerror("Не удалось открыть картинку для разметки", str(exc), parent=parent)
            self.destroy()
            return

        self._build_ui()
        self._load_existing()
        self._redraw()
        self.grab_set()

    def _build_ui(self) -> None:
        intro = (
            "Размечайте только действительно важные новые/изменённые архитектурные элементы. "
            "Левый клик — добавить точку полигона. Enter или двойной клик — закончить область. "
            "Backspace — отменить точку."
        )
        ttk.Label(self, text=intro, wraplength=1120).pack(anchor="w", padx=12, pady=(10, 4))

        top = ttk.Frame(self)
        top.pack(fill="x", padx=12, pady=6)
        ttk.Label(top, text="Класс области:").pack(side="left")
        values = list(CLASS_LABELS.keys())
        combo = ttk.Combobox(top, textvariable=self.class_var, values=values, state="readonly", width=28)
        combo.pack(side="left", padx=8)
        self.class_label = ttk.Label(top, text=CLASS_LABELS[self.class_var.get()], foreground="#444")
        self.class_label.pack(side="left", padx=8)
        combo.bind("<<ComboboxSelected>>", lambda _e: self.class_label.configure(text=CLASS_LABELS.get(self.class_var.get(), "")))

        self.canvas = tk.Canvas(self, width=self.disp_w, height=self.disp_h, bg="#eeeeee", highlightthickness=1)
        self.canvas.pack(anchor="center", padx=12, pady=8)
        self.canvas.create_image(0, 0, image=self.photo, anchor="nw")
        self.canvas.bind("<Button-1>", self._click)
        self.canvas.bind("<Double-Button-1>", lambda _e: self.finish_polygon())
        self.bind("<Return>", lambda _e: self.finish_polygon())
        self.bind("<BackSpace>", lambda _e: self.undo_point())
        self.bind("<Delete>", lambda _e: self.undo_polygon())

        self.status = tk.StringVar()
        ttk.Label(self, textvariable=self.status, font=("TkDefaultFont", 10, "bold")).pack(anchor="w", padx=12, pady=4)

        btns = ttk.Frame(self)
        btns.pack(anchor="w", padx=12, pady=10)
        ttk.Button(btns, text="Закончить область", command=self.finish_polygon).pack(side="left")
        ttk.Button(btns, text="Отменить точку", command=self.undo_point).pack(side="left", padx=6)
        ttk.Button(btns, text="Удалить последнюю область", command=self.undo_polygon).pack(side="left", padx=6)
        ttk.Button(btns, text="Очистить всё", command=self.clear_all).pack(side="left", padx=6)
        ttk.Button(btns, text="Сохранить и перенести на исходное фото", command=self.save).pack(side="left", padx=12)
        ttk.Button(btns, text="Закрыть", command=self.destroy).pack(side="left", padx=6)

        legend = (
            "Совет: для первой модели Roboflow лучше чаще использовать один класс added_architecture: "
            "всё, что появилось и важно. Позже классы можно разделить."
        )
        ttk.Label(self, text=legend, wraplength=1120, foreground="#555").pack(anchor="w", padx=12, pady=(0, 8))

    def _load_existing(self) -> None:
        path = self.outdir / "annotations" / "manual_annotations.json"
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            anns = data.get("annotations", [])
            if isinstance(anns, list):
                self.annotations = anns
        except Exception:
            pass

    def _click(self, event: tk.Event) -> None:
        if not (0 <= event.x <= self.disp_w and 0 <= event.y <= self.disp_h):
            return
        self.current_points.append((event.x / self.scale, event.y / self.scale))
        self._redraw()

    def _to_disp(self, pt: Point) -> Point:
        return (pt[0] * self.scale, pt[1] * self.scale)

    def _redraw(self) -> None:
        self.canvas.delete("ann")
        # Saved polygons.
        for idx, ann in enumerate(self.annotations, start=1):
            pts = ann.get("polygon", [])
            if len(pts) < 3:
                continue
            cls = ann.get("class", "added_architecture")
            color = TK_COLORS.get(cls, "#00aa00")
            flat: List[float] = []
            for p in pts:
                x, y = self._to_disp((float(p[0]), float(p[1])))
                flat.extend([x, y])
            self.canvas.create_polygon(flat, outline=color, fill="", width=3, tags="ann")
            # Number near centroid.
            xs = flat[0::2]
            ys = flat[1::2]
            self.canvas.create_text(sum(xs) / len(xs), sum(ys) / len(ys), text=str(idx), fill=color,
                                    font=("TkDefaultFont", 13, "bold"), tags="ann")
        # Current polygon.
        if self.current_points:
            cls = self.class_var.get()
            color = TK_COLORS.get(cls, "#00aa00")
            disp = [self._to_disp(p) for p in self.current_points]
            for i, (x, y) in enumerate(disp, start=1):
                r = 5
                self.canvas.create_oval(x-r, y-r, x+r, y+r, fill=color, outline="white", width=2, tags="ann")
                self.canvas.create_text(x+8, y-8, text=str(i), fill=color, font=("TkDefaultFont", 9, "bold"), tags="ann")
            if len(disp) >= 2:
                flat = [v for xy in disp for v in xy]
                self.canvas.create_line(flat, fill=color, width=2, tags="ann")
        self.status.set(
            f"Сохранённых областей: {len(self.annotations)}. Точек в текущей области: {len(self.current_points)}."
        )

    def finish_polygon(self) -> None:
        if len(self.current_points) < 3:
            messagebox.showinfo("Нужно больше точек", "Для области нужно минимум 3 точки.", parent=self)
            return
        cls = self.class_var.get()
        self.annotations.append({
            "id": len(self.annotations) + 1,
            "class": cls,
            "label_ru": CLASS_LABELS.get(cls, cls),
            "polygon": [[float(x), float(y)] for x, y in self.current_points],
        })
        self.current_points = []
        self._redraw()

    def undo_point(self) -> None:
        if self.current_points:
            self.current_points.pop()
        self._redraw()

    def undo_polygon(self) -> None:
        if self.annotations:
            self.annotations.pop()
        self._redraw()

    def clear_all(self) -> None:
        if messagebox.askyesno("Очистить разметку", "Удалить все области разметки?", parent=self):
            self.annotations.clear()
            self.current_points.clear()
            self._redraw()

    def save(self) -> None:
        if self.current_points:
            if messagebox.askyesno("Есть незаконченная область", "Закончить текущую область и сохранить?", parent=self):
                if len(self.current_points) >= 3:
                    self.finish_polygon()
                else:
                    self.current_points.clear()
        if not self.annotations:
            messagebox.showinfo("Разметки нет", "Сначала обведите хотя бы одну область.", parent=self)
            return
        try:
            outputs = save_annotations_and_exports(self.outdir, self.annotations)
        except Exception as exc:
            messagebox.showerror("Не удалось сохранить", str(exc), parent=self)
            return
        messagebox.showinfo(
            "Сохранено",
            "Разметка сохранена. Обводки перенесены на исходное современное фото.\n\n"
            f"Главный файл: {outputs['marked_on_original_modern']}\n"
            f"Экспорт Roboflow: {outputs['roboflow_zip']}",
            parent=self,
        )
        self.on_saved(outputs)


@dataclass
class HistoricalSourceItem:
    """Одно историческое фото в списке для сравнения — со своими 4 углами."""

    key: str
    path: str
    label: str
    old_points_text: str = ""
    crop_rect_text: str = ""
    source_type: str = "file"
    pastvu_cid: Optional[int] = None
    comparison_id: str = ""


class DualFacadePointPicker(tk.Toplevel):
    """Pick matching four facade corners on historical and modern photos in one window."""

    NAMES = [
        "верхний левый угол фасада",
        "верхний правый угол фасада",
        "нижний правый угол фасада",
        "нижний левый угол фасада",
    ]

    def __init__(
        self,
        parent: tk.Tk,
        modern_image_path: str,
        callback: Callable[[str, str, List[Dict[str, str]], str], None],
        *,
        historical_sources: List[Dict[str, str]],
        start_index: int = 0,
        initial_modern_points_text: str = "",
        initial_modern_crop_rect_text: str = "",
        lock_modern_when_complete: bool = False,
    ) -> None:
        super().__init__(parent)
        self.title("Углы фасада и рамка обрезки")
        self.geometry("1280x900")
        self.minsize(1040, 720)
        self.callback = callback
        self.hist_sources = list(historical_sources) if historical_sources else []
        self.tool_mode = tk.StringVar(value="corners")
        self.modern_crop_rect_text = str(initial_modern_crop_rect_text or "")
        self._crop_drag: Optional[Tuple[str, float, float]] = None
        if not self.hist_sources:
            messagebox.showerror("Нет фото", "Добавьте хотя бы одно историческое фото.", parent=parent)
            self.destroy()
            return
        self.hist_index = max(0, min(start_index, len(self.hist_sources) - 1))
        self.old_points: List[Optional[Point]] = [None, None, None, None]
        self.modern_points: List[Optional[Point]] = [None, None, None, None]
        self._fill_points_from_text(initial_modern_points_text, self.modern_points)
        self.lock_modern = bool(lock_modern_when_complete)

        try:
            self.modern_photo, self.modern_scale, self.modern_w, self.modern_h, self.modern_orig_w, self.modern_orig_h = cv_to_photoimage(
                modern_image_path, 560, 540
            )
        except Exception as exc:
            messagebox.showerror("Не удалось открыть фото", str(exc), parent=parent)
            self.destroy()
            return

        intro = (
            "Слева — исторические фото (ползунок), справа — современное. "
            "Режим «4 угла»: клики 1–4 на обоих фото для наложения. "
            "Режим «Рамка»: потяните мышью прямоугольник — что останется из исходника перед выпрямлением."
        )
        ttk.Label(self, text=intro, wraplength=1220).pack(anchor="w", padx=12, pady=(10, 4))
        tools = ttk.Frame(self)
        tools.pack(anchor="w", padx=12, pady=(0, 4))
        ttk.Label(tools, text="Инструмент:").pack(side="left")
        ttk.Radiobutton(tools, text="4 угла фасада", variable=self.tool_mode, value="corners", command=self._redraw).pack(side="left", padx=6)
        ttk.Radiobutton(tools, text="Рамка обрезки (историческое)", variable=self.tool_mode, value="crop_old", command=self._redraw).pack(side="left", padx=6)
        ttk.Radiobutton(tools, text="Рамка обрезки (современное)", variable=self.tool_mode, value="crop_modern", command=self._redraw).pack(side="left", padx=6)

        canvases = ttk.Frame(self)
        canvases.pack(fill="both", expand=True, padx=12, pady=6)
        canvases.columnconfigure(0, weight=1)
        canvases.columnconfigure(1, weight=1)

        self.left_box = ttk.LabelFrame(canvases, text="Историческое фото")
        right_box = ttk.LabelFrame(canvases, text="Современное фото")
        self.left_box.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        right_box.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        hist_nav = ttk.Frame(self.left_box)
        hist_nav.pack(fill="x", padx=8, pady=(6, 2))
        ttk.Button(hist_nav, text="◀", width=3, command=self._hist_prev).pack(side="left")
        self.hist_slider = tk.Scale(
            hist_nav,
            from_=0,
            to=max(0, len(self.hist_sources) - 1),
            orient="horizontal",
            showvalue=False,
            command=self._on_hist_slider,
        )
        self.hist_slider.pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(hist_nav, text="▶", width=3, command=self._hist_next).pack(side="left")
        self.hist_caption = ttk.Label(self.left_box, text="", wraplength=520)
        self.hist_caption.pack(anchor="w", padx=8, pady=(0, 4))

        self.old_canvas = tk.Canvas(self.left_box, width=560, height=540, bg="#eeeeee", highlightthickness=1)
        self.old_canvas.pack(anchor="center", padx=8, pady=8)
        self._bind_canvas_events(self.old_canvas, "old")

        self.modern_canvas = tk.Canvas(right_box, width=self.modern_w, height=self.modern_h, bg="#eeeeee", highlightthickness=1)
        self.modern_canvas.pack(anchor="center", padx=8, pady=8)
        self.modern_canvas.create_image(0, 0, image=self.modern_photo, anchor="nw")
        self._bind_canvas_events(self.modern_canvas, "modern")

        self.status = tk.StringVar()
        ttk.Label(self, textvariable=self.status, font=("TkDefaultFont", 10, "bold")).pack(anchor="w", padx=12, pady=5)

        btns = ttk.Frame(self)
        btns.pack(anchor="w", padx=12, pady=(6, 12))
        ttk.Button(btns, text="Отменить последний клик", command=self.undo).pack(side="left")
        ttk.Button(btns, text="Очистить все", command=self.clear_all).pack(side="left", padx=(8, 2))
        ttk.Button(btns, text="Только историческое", command=self.clear_old).pack(side="left", padx=2)
        ttk.Button(btns, text="Только современное", command=self.clear_modern).pack(side="left", padx=2)
        ttk.Button(btns, text="Сбросить рамку слева", command=self.clear_crop_old).pack(side="left", padx=(8, 2))
        ttk.Button(btns, text="Сбросить рамку справа", command=self.clear_crop_modern).pack(side="left", padx=2)
        self.lock_var = tk.BooleanVar(value=self.lock_modern)
        ttk.Checkbutton(
            btns,
            text="Не трогать современное (замок)",
            variable=self.lock_var,
            command=self._toggle_lock_modern,
        ).pack(side="left", padx=8)
        ttk.Button(btns, text="Готово", command=self.done).pack(side="left", padx=8)
        ttk.Button(btns, text="Закрыть", command=self.destroy).pack(side="left", padx=8)

        self._load_historical_index(self.hist_index, initial=True)
        self.grab_set()

    def _points_to_text(self, points: List[Optional[Point]]) -> str:
        if any(p is None for p in points):
            return ""
        return points_to_cli([p for p in points if p is not None])

    def _save_current_historical_points(self) -> None:
        if 0 <= self.hist_index < len(self.hist_sources):
            self.hist_sources[self.hist_index]["points"] = self._points_to_text(self.old_points)
            self.hist_sources[self.hist_index]["crop_rect"] = str(
                self.hist_sources[self.hist_index].get("crop_rect") or ""
            )

    def _bind_canvas_events(self, canvas: tk.Canvas, side: str) -> None:
        canvas.bind("<Button-1>", lambda e, s=side: self._canvas_press(s, e))
        canvas.bind("<B1-Motion>", lambda e, s=side: self._canvas_motion(s, e))
        canvas.bind("<ButtonRelease-1>", lambda e, s=side: self._canvas_release(s, e))

    def _current_old_crop_text(self) -> str:
        if 0 <= self.hist_index < len(self.hist_sources):
            return str(self.hist_sources[self.hist_index].get("crop_rect") or "")
        return ""

    def _set_old_crop_text(self, text: str) -> None:
        if 0 <= self.hist_index < len(self.hist_sources):
            self.hist_sources[self.hist_index]["crop_rect"] = text

    def _load_historical_index(self, index: int, *, initial: bool = False) -> None:
        if not initial:
            self._save_current_historical_points()
        self.hist_index = max(0, min(index, len(self.hist_sources) - 1))
        src = self.hist_sources[self.hist_index]
        path = str(src.get("path") or "")
        label = str(src.get("label") or Path(path).name)
        if "crop_rect" not in src:
            src["crop_rect"] = ""
        self.old_points = [None, None, None, None]
        self._fill_points_from_text(str(src.get("points") or ""), self.old_points)
        try:
            self.old_photo, self.old_scale, self.old_w, self.old_h, self.old_orig_w, self.old_orig_h = cv_to_photoimage(
                path, 560, 540
            )
        except Exception as exc:
            messagebox.showerror("Фото", str(exc), parent=self)
            return
        self.old_canvas.configure(width=self.old_w, height=self.old_h)
        self.old_canvas.delete("all")
        self.old_canvas.create_image(0, 0, image=self.old_photo, anchor="nw")
        self.hist_slider.set(self.hist_index)
        self.hist_caption.configure(text=f"{self.hist_index + 1} / {len(self.hist_sources)} — {label}")
        self.left_box.configure(text=f"Историческое: {label}")
        self._redraw()

    def _on_hist_slider(self, value: str) -> None:
        try:
            idx = int(float(value))
        except ValueError:
            return
        if idx != self.hist_index:
            self._load_historical_index(idx)

    def _hist_prev(self) -> None:
        if self.hist_index > 0:
            self._load_historical_index(self.hist_index - 1)

    def _hist_next(self) -> None:
        if self.hist_index < len(self.hist_sources) - 1:
            self._load_historical_index(self.hist_index + 1)

    def _toggle_lock_modern(self) -> None:
        self.lock_modern = bool(self.lock_var.get())
        self._redraw()

    @staticmethod
    def _fill_points_from_text(text: str, target: List[Optional[Point]]) -> None:
        if not text.strip():
            return
        try:
            pts = parse_four_points(text)
            for i in range(4):
                target[i] = (float(pts[i][0]), float(pts[i][1]))
        except Exception:
            pass

    def _current_index(self) -> int:
        for i in range(4):
            if self.old_points[i] is None:
                return i
            if not self.lock_modern and self.modern_points[i] is None:
                return i
        return 4

    def _canvas_press(self, side: str, event: tk.Event) -> None:
        mode = self.tool_mode.get()
        if mode in ("crop_old", "crop_modern"):
            target = "old" if mode == "crop_old" else "modern"
            if side != target:
                return
            self._crop_drag = (side, float(event.x), float(event.y))
            return
        self._click_corner(side, event)

    def _canvas_motion(self, side: str, event: tk.Event) -> None:
        if self._crop_drag is None or self._crop_drag[0] != side:
            return
        self._redraw(crop_preview=(side, self._crop_drag[1], self._crop_drag[2], float(event.x), float(event.y)))

    def _canvas_release(self, side: str, event: tk.Event) -> None:
        if self._crop_drag is None or self._crop_drag[0] != side:
            return
        x1, y1 = self._crop_drag[1], self._crop_drag[2]
        x2, y2 = float(event.x), float(event.y)
        self._crop_drag = None
        scale = self.old_scale if side == "old" else self.modern_scale
        ox0 = min(x1, x2) / scale
        oy0 = min(y1, y2) / scale
        ox1 = max(x1, x2) / scale
        oy1 = max(y1, y2) / scale
        ow = self.old_orig_w if side == "old" else self.modern_orig_w
        oh = self.old_orig_h if side == "old" else self.modern_orig_h
        ox0 = max(0.0, min(ox0, float(ow)))
        oy0 = max(0.0, min(oy0, float(oh)))
        ox1 = max(0.0, min(ox1, float(ow)))
        oy1 = max(0.0, min(oy1, float(oh)))
        if ox1 - ox0 < 12 or oy1 - oy0 < 12:
            self.status.set("Рамка слишком мала — потяните побольше.")
            self._redraw()
            return
        text = crop_rect_to_text(ox0, oy0, ox1, oy1)
        if side == "old":
            self._set_old_crop_text(text)
        else:
            self.modern_crop_rect_text = text
        self.status.set("Рамка обрезки сохранена. При необходимости укажите 4 угла внутри неё.")
        self._redraw()

    def _click_corner(self, side: str, event: tk.Event) -> None:
        if self.tool_mode.get() != "corners":
            return
        if side == "modern" and self.lock_modern:
            self.status.set("Современные углы уже заданы. Кликайте только на историческом фото слева.")
            return
        idx = self._current_index()
        if idx >= 4:
            self.status.set("Все 4 пары точек уже выбраны. Нажмите “Готово” или очистите точки.")
            return
        if side == "old":
            if not (0 <= event.x <= self.old_w and 0 <= event.y <= self.old_h):
                return
            self.old_points[idx] = (event.x / self.old_scale, event.y / self.old_scale)
        else:
            if not (0 <= event.x <= self.modern_w and 0 <= event.y <= self.modern_h):
                return
            self.modern_points[idx] = (event.x / self.modern_scale, event.y / self.modern_scale)
        self._redraw()

    def _to_disp(self, pt: Point, side: str) -> Point:
        scale = self.old_scale if side == "old" else self.modern_scale
        return (pt[0] * scale, pt[1] * scale)

    def _draw_side(self, canvas: tk.Canvas, points: List[Optional[Point]], side: str) -> None:
        canvas.delete("corner_marker")
        disp_points: List[Point] = []
        for i, pt in enumerate(points, start=1):
            if pt is None:
                continue
            x, y = self._to_disp(pt, side)
            disp_points.append((x, y))
            r = 11
            canvas.create_oval(x - r, y - r, x + r, y + r, fill="#d92323", outline="white", width=2, tags="corner_marker")
            canvas.create_text(x, y, text=str(i), fill="white", font=("TkDefaultFont", 9, "bold"), tags="corner_marker")
            canvas.create_text(x + 16, y - 12, text=self.NAMES[i - 1].replace(" фасада", ""), fill="#d92323", anchor="w", tags="corner_marker")
        # Draw lines only through consecutive existing points. Close polygon when all are present.
        consecutive: List[Point] = []
        for pt in points:
            if pt is None:
                break
            consecutive.append(self._to_disp(pt, side))
        if len(consecutive) >= 2:
            flat = [v for xy in consecutive for v in xy]
            canvas.create_line(flat, fill="#d92323", width=2, tags="corner_marker")
        if len(consecutive) == 4:
            flat = [v for xy in consecutive + [consecutive[0]] for v in xy]
            canvas.create_line(flat, fill="#d92323", width=2, tags="corner_marker")

    def _draw_crop_rect(self, canvas: tk.Canvas, crop_text: str, side: str, *, preview: Optional[Tuple[float, float, float, float]] = None) -> None:
        scale = self.old_scale if side == "old" else self.modern_scale
        if preview is not None:
            x0, y0, x1, y1 = preview
        else:
            box = parse_crop_rect(crop_text)
            if box is None:
                return
            x0, y0, x1, y1 = box
        dx0, dy0 = x0 * scale, y0 * scale
        dx1, dy1 = x1 * scale, y1 * scale
        canvas.create_rectangle(dx0, dy0, dx1, dy1, outline="#1a8a3a", width=2, dash=(6, 4), tags="crop_marker")
        canvas.create_text(dx0 + 6, dy0 + 6, text="обрезка", fill="#1a8a3a", anchor="nw", tags="crop_marker")

    def _redraw(self, crop_preview: Optional[Tuple[str, float, float, float, float]] = None) -> None:
        self.old_canvas.delete("crop_marker")
        self.modern_canvas.delete("crop_marker")
        self._draw_side(self.old_canvas, self.old_points, "old")
        self._draw_side(self.modern_canvas, self.modern_points, "modern")
        self._draw_crop_rect(self.old_canvas, self._current_old_crop_text(), "old")
        self._draw_crop_rect(self.modern_canvas, self.modern_crop_rect_text, "modern")
        if crop_preview is not None:
            side, x1, y1, x2, y2 = crop_preview
            scale = self.old_scale if side == "old" else self.modern_scale
            prev = (min(x1, x2) / scale, min(y1, y2) / scale, max(x1, x2) / scale, max(y1, y2) / scale)
            canvas = self.old_canvas if side == "old" else self.modern_canvas
            self._draw_crop_rect(canvas, "", side, preview=prev)
        mode = self.tool_mode.get()
        if mode == "crop_old":
            self.status.set("Потяните мышью рамку на историческом фото слева — останется выбранный фрагмент.")
            return
        if mode == "crop_modern":
            self.status.set("Потяните мышью рамку на современном фото справа.")
            return
        idx = self._current_index()
        if idx >= 4:
            self.status.set("Все 4 пары выбраны. Нажмите “Готово”.")
            return
        left_ok = self.old_points[idx] is not None
        right_ok = self.modern_points[idx] is not None or self.lock_modern
        missing = []
        if not left_ok:
            missing.append("слева на историческом фото")
        if not right_ok:
            missing.append("справа на современном фото")
        self.status.set(f"Точка {idx + 1} из 4 — {self.NAMES[idx]}. Кликните " + " и ".join(missing) + ".")

    def undo(self) -> None:
        for i in range(3, -1, -1):
            if not self.lock_modern and self.modern_points[i] is not None:
                self.modern_points[i] = None
                self._redraw()
                return
            if self.old_points[i] is not None:
                self.old_points[i] = None
                self._redraw()
                return
        self._redraw()

    def clear_all(self) -> None:
        self.old_points = [None, None, None, None]
        if not self.lock_modern:
            self.modern_points = [None, None, None, None]
        self._save_current_historical_points()
        self._redraw()

    def clear_old(self) -> None:
        self.old_points = [None, None, None, None]
        self._save_current_historical_points()
        self._redraw()

    def clear_modern(self) -> None:
        self.lock_modern = False
        self.lock_var.set(False)
        self.modern_points = [None, None, None, None]
        self._redraw()

    def clear_crop_old(self) -> None:
        self._set_old_crop_text("")
        self._redraw()

    def clear_crop_modern(self) -> None:
        self.modern_crop_rect_text = ""
        self._redraw()

    @staticmethod
    def _points_inside_crop(points: List[Point], crop_text: str) -> bool:
        box = parse_crop_rect(crop_text)
        if box is None:
            return True
        x0, y0, x1, y1 = box
        for x, y in points:
            if x < x0 or x > x1 or y < y0 or y > y1:
                return False
        return True

    @staticmethod
    def _quad_aspect_ratio(points: List[Point]) -> float:
        if len(points) < 4 or any(p is None for p in points):
            return 1.0
        pts = np.asarray([points[0], points[1], points[2], points[3]], dtype=np.float64)
        w = (np.linalg.norm(pts[1] - pts[0]) + np.linalg.norm(pts[2] - pts[3])) / 2.0
        h = (np.linalg.norm(pts[3] - pts[0]) + np.linalg.norm(pts[2] - pts[1])) / 2.0
        return float(w / max(h, 1e-6))

    def done(self) -> None:
        self._save_current_historical_points()
        if any(p is None for p in self.old_points) or any(p is None for p in self.modern_points):
            messagebox.showinfo(
                "Нужны все точки",
                "Поставьте 4 угла на текущем историческом фото и 4 угла на современном.",
                parent=self,
            )
            return
        old = [p for p in self.old_points if p is not None]
        modern = [p for p in self.modern_points if p is not None]
        old_crop = self._current_old_crop_text()
        if not self._points_inside_crop(old, old_crop):
            messagebox.showwarning(
                "Углы вне рамки",
                "Все 4 угла на историческом фото должны быть внутри зелёной рамки обрезки (или сбросьте рамку).",
                parent=self,
            )
            return
        if not self._points_inside_crop(modern, self.modern_crop_rect_text):
            messagebox.showwarning(
                "Углы вне рамки",
                "Все 4 угла на современном фото должны быть внутри зелёной рамки обрезки.",
                parent=self,
            )
            return
        ro = self._quad_aspect_ratio(old)
        rm = self._quad_aspect_ratio(modern)
        if ro > 0 and rm > 0 and (ro / rm > 2.8 or rm / ro > 2.8):
            if not messagebox.askyesno(
                "Проверьте углы",
                "Выделения на историческом и современном фото сильно разной формы "
                "(узкая полоска с одной стороны и широкая с другой).\n\n"
                "Точка 1 должна совпасть с точкой 1 на том же углу здания, и так далее. "
                "Иначе выпрямление «рвёт» картинку.\n\n"
                "Всё равно сохранить эти углы?",
                parent=self,
            ):
                return
        self.callback(
            points_to_cli(old),
            points_to_cli(modern),
            list(self.hist_sources),
            self.modern_crop_rect_text,
        )
        self.destroy()

# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

class ScrollableFrame(ttk.Frame):
    """Прокручиваемая область; в Panedwindow не раздувает окно — высота = родитель."""

    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent)
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas)
        self._window_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.bind_mousewheel()

    def _on_inner_configure(self, _event: tk.Event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event: tk.Event) -> None:
        self.canvas.itemconfig(self._window_id, width=max(event.width, 1))

    def bind_mousewheel(self) -> None:
        def on_wheel(event: tk.Event) -> str:
            if not self.winfo_ismapped():
                return "break"
            delta = 0
            if hasattr(event, "delta") and event.delta:
                delta = -1 * int(event.delta / 120)
            elif getattr(event, "num", None) == 4:
                delta = -1
            elif getattr(event, "num", None) == 5:
                delta = 1
            if delta:
                self.canvas.yview_scroll(delta, "units")
            return "break"

        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.canvas.bind(seq, on_wheel, add="+")
            self.inner.bind(seq, on_wheel, add="+")


class ComparisonPreviewWindow(tk.Toplevel):
    """Interactive in-app overlay/before-after preview for prepared rectified images."""

    def __init__(self, master: "App", outdir: Path) -> None:
        super().__init__(master)
        self.master_app = master
        self.outdir = outdir
        self.title("Archiview — просмотр overlay / до-после")
        self.geometry("1120x820")
        self.minsize(900, 650)
        self.mode = tk.StringVar(value="overlay")
        self.old_opacity = tk.IntVar(value=int(master.old_opacity.get()))
        self.modern_brightness = tk.IntVar(value=72)
        self.old_contrast = tk.IntVar(value=145)
        self.split = tk.IntVar(value=50)
        self.photo_ref: Optional[ImageTk.PhotoImage] = None  # type: ignore[type-arg]
        self._build()
        self._load_images()
        self._render()

    def _build(self) -> None:
        controls = ttk.LabelFrame(self, text="Настройки просмотра")
        controls.pack(fill="x", padx=10, pady=8)
        row = ttk.Frame(controls)
        row.pack(fill="x", padx=8, pady=6)
        ttk.Radiobutton(row, text="Overlay", variable=self.mode, value="overlay", command=self._render).pack(side="left")
        ttk.Radiobutton(row, text="До / после", variable=self.mode, value="before_after", command=self._render).pack(side="left", padx=10)
        ttk.Button(row, text="Использовать текущий вид для разметки", command=self.save_current_for_labeling).pack(side="left", padx=18)
        ttk.Button(row, text="Открыть папку результата", command=lambda: open_path(self.outdir)).pack(side="left", padx=6)

        sliders = ttk.Frame(controls)
        sliders.pack(fill="x", padx=8, pady=(0, 8))
        self._slider(sliders, "Видимость старого", self.old_opacity, 0, 100, 0)
        self._slider(sliders, "Яркость современного", self.modern_brightness, 35, 120, 1)
        self._slider(sliders, "Контраст старого", self.old_contrast, 80, 240, 2)
        self._slider(sliders, "Граница до/после", self.split, 0, 100, 3)

        self.canvas = tk.Canvas(self, background="#2f2f2f", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.canvas.bind("<Configure>", lambda _e: self._render())

    def _slider(self, parent: ttk.Frame, text: str, var: tk.IntVar, start: int, end: int, row: int) -> None:
        ttk.Label(parent, text=text + ":").grid(row=row, column=0, sticky="w", padx=(0, 8), pady=2)
        tk.Scale(parent, from_=start, to=end, orient="horizontal", variable=var, command=lambda _v: self._render(), length=360, showvalue=True).grid(row=row, column=1, sticky="w", pady=2)

    def _load_images(self) -> None:
        if Image is None:
            raise RuntimeError("Pillow не установлен.")
        old_path = self.outdir / "03_historical_rectified.png"
        new_path = self.outdir / "04_modern_rectified.png"
        if not old_path.exists() or not new_path.exists():
            raise RuntimeError("Сначала подготовьте выпрямленную пару во вкладке 2.")
        self.old_img = Image.open(old_path).convert("RGB")  # type: ignore[union-attr]
        self.new_img = Image.open(new_path).convert("RGB")  # type: ignore[union-attr]
        if self.old_img.size != self.new_img.size:
            self.new_img = self.new_img.resize(self.old_img.size)

    def _prepared_old(self):
        old = ImageOps.grayscale(self.old_img) if ImageOps is not None else self.old_img.convert("L")
        if ImageOps is not None:
            old = ImageOps.autocontrast(old)
        if ImageEnhance is not None:
            old = ImageEnhance.Contrast(old).enhance(self.old_contrast.get() / 100.0)
        return old.convert("RGB")

    def _prepared_new(self):
        modern = self.new_img.copy()
        if ImageEnhance is not None:
            modern = ImageEnhance.Color(modern).enhance(0.45)
            modern = ImageEnhance.Brightness(modern).enhance(self.modern_brightness.get() / 100.0)
        return modern.convert("RGB")

    def _compose(self):
        old = self._prepared_old()
        modern = self._prepared_new()
        if self.mode.get() == "before_after":
            w, h = old.size
            x = int(round(w * self.split.get() / 100.0))
            out = old.copy()
            out.paste(modern.crop((x, 0, w, h)), (x, 0))
            return out
        return Image.blend(modern, old, self.old_opacity.get() / 100.0)

    def _render(self) -> None:
        try:
            img = self._compose()
            cw = max(10, self.canvas.winfo_width())
            ch = max(10, self.canvas.winfo_height())
            scale = min(cw / img.width, ch / img.height, 1.0)
            disp = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale)))) if scale < 1 else img
            self.photo_ref = ImageTk.PhotoImage(disp)  # type: ignore[union-attr]
            self.canvas.delete("all")
            self.canvas.create_image(cw // 2, ch // 2, image=self.photo_ref, anchor="center")
        except Exception as exc:
            self.canvas.delete("all")
            self.canvas.create_text(20, 20, anchor="nw", fill="white", text=str(exc))

    def save_current_for_labeling(self) -> None:
        try:
            img = self._compose()
            target = self.outdir / "05_comparison_for_labeling.png"
            img.save(target)
            messagebox.showinfo("Сохранено", f"Текущий вид сохранён как картинка для разметки:\n{target}")
            self.master_app._log(f"Картинка для разметки обновлена из встроенного preview: {target}\n")
        except Exception as exc:
            messagebox.showerror("Не удалось сохранить", str(exc))


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"Archiview CV {APP_VERSION}")

        # Project and photo selection.
        self.address = tk.StringVar(value="")
        self.site_card_id = tk.StringVar(value="")
        self.auto_export_website = tk.BooleanVar(value=True)
        self.object_name = tk.StringVar(value="")
        self.lat = tk.StringVar(value="")
        self.lon = tk.StringVar(value="")
        self.geocode_result = tk.StringVar(value="Адрес/координаты пока не выбраны.")
        self.search_distance = tk.IntVar(value=500)
        self.search_limit = tk.IntVar(value=30)
        self.year_from = tk.StringVar(value="")
        self.year_to = tk.StringVar(value="")
        self.exclude_nonfacade = tk.BooleanVar(value=True)

        self.project_dir = tk.StringVar(value=str(APP_DIR / "archiview_projects" / "new_house_project"))
        self.outdir = tk.StringVar(value=str(Path(self.project_dir.get()) / "result"))
        self.current_house_record = None
        self.current_house_paths = None
        self.project_store = None
        self.historical_img = tk.StringVar(value="")
        self.modern_img = tk.StringVar(value="")
        self.selected_source_label = tk.StringVar(value="Историческое фото ещё не выбрано.")

        self.pastvu_photos: List[PastVuPhoto] = []
        self.pastvu_thumb_refs: List[ImageTk.PhotoImage] = []  # keep alive
        self.selected_pastvu: Optional[PastVuPhoto] = None

        self.modern_source_label = tk.StringVar(value="Современное фото ещё не выбрано.")
        self.modern_meta: Dict[str, object] = {}
        self.open_modern_photos: List[OpenStreetPhoto] = []
        self.open_modern_thumb_refs: List[ImageTk.PhotoImage] = []  # keep alive
        self.modern_source_kind = tk.StringVar(value="Wikimedia Commons")
        self.modern_search_radius = tk.IntVar(value=500)
        self.modern_search_limit = tk.IntVar(value=30)
        self.mapillary_token = tk.StringVar(value=os.environ.get("MAPILLARY_TOKEN", ""))

        # Rectification and analysis.
        self.old_points_text = ""
        self.modern_points_text = ""
        self.modern_crop_rect_text = ""
        self.historical_sources: List[HistoricalSourceItem] = []
        self.active_historical_key = ""
        self.points_status = tk.StringVar(value="Углы фасада ещё не выбраны.")
        self.old_opacity = tk.IntVar(value=75)
        self.old_opacity_label = tk.StringVar(value="Видимость старого фото в overlay: 75%")
        self.keep_context = tk.BooleanVar(value=True)
        self.rectified_status = tk.StringVar(value="Выпрямленная пара ещё не подготовлена.")
        self.last_annotation_outputs: Dict[str, str] = {}

        # Optional separate straightening.
        self.straight_img = tk.StringVar(value="")
        self.straight_out = tk.StringVar(value=str(APP_DIR / "straightened.png"))
        self.straight_points = ""
        self.straight_points_status = tk.StringVar(value="4 угла фасада не выбраны.")

        self._map_server = None
        self._map_server_thread = None
        self._suppress_house_autosave = False
        self._house_save_after_id: Optional[str] = None
        self._bind_house_field_autosave()

        self._build_ui()
        self._fit_main_window_to_screen()
        self._check_environment()

    # ----------------------------- UI ---------------------------------

    def _build_ui(self) -> None:
        title = ttk.Label(
            self,
            text="Archiview CV v10: выбрать фото → расширенно выпрямить фасады → preview/overlay → разметка → показать на реальном фасаде",
            font=("TkDefaultFont", 12, "bold"),
        )
        title.pack(anchor="w", padx=12, pady=(10, 4))

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=12, pady=6)
        self.tab_select = ttk.Frame(notebook)
        self.tab_rectify = ttk.Frame(notebook)
        self.tab_analyze = ttk.Frame(notebook)
        self.tab_straight = ttk.Frame(notebook)
        notebook.add(self.tab_select, text="1. Выбор фото")
        notebook.add(self.tab_rectify, text="2. Выпрямление")
        notebook.add(self.tab_analyze, text="3. Overlay и разметка")
        notebook.add(self.tab_straight, text="4. Отдельно выпрямить фасад")
        self._build_select_tab(self.tab_select)
        self._build_rectify_tab(self.tab_rectify)
        self._build_analyze_tab(self.tab_analyze)
        self._build_straight_tab(self.tab_straight)

        log_frame = ttk.LabelFrame(self, text="Сообщения программы")
        log_frame.pack(fill="x", padx=12, pady=(0, 10))
        self.log = tk.Text(log_frame, height=7, wrap="word")
        self.log.pack(fill="x", expand=False, padx=8, pady=8)
        self._log("Готово. Начните с вкладки 1: выберите историческое и современное фото.\n")

    def _build_select_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        top = ttk.LabelFrame(parent, text="A. Папка дома / проекта")
        top.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 6))
        top.columnconfigure(1, weight=1)
        ttk.Label(top, text="Папка проекта:").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(top, textvariable=self.project_dir).grid(row=0, column=1, sticky="ew", padx=6, pady=6)
        ttk.Button(top, text="Папка…", command=self.choose_project_dir).grid(row=0, column=2, padx=8, pady=6)
        ttk.Label(
            top,
            text=(
                "Каждый выбранный исходник будет скопирован внутрь проекта: historical_sources и modern_sources. "
                "Границы блоков ниже можно двигать мышкой."
            ),
            foreground="#555",
        ).grid(row=1, column=0, columnspan=3, sticky="w", padx=8, pady=(0, 8))

        main_pane = ttk.Panedwindow(parent, orient="horizontal")
        main_pane.grid(row=1, column=0, sticky="nsew", padx=8, pady=6)

        left = ttk.LabelFrame(main_pane, text="B. Историческое фото: PastVu или файл")
        right = ttk.LabelFrame(main_pane, text="C. Современное фото: файл, буфер, Commons / KartaView")
        main_pane.add(left, weight=1)
        main_pane.add(right, weight=1)

        # ---------------- Historical pane ----------------
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)
        hist_pane = ttk.Panedwindow(left, orient="vertical")
        hist_pane.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        hist_controls = ttk.Frame(hist_pane)
        hist_preview = ttk.LabelFrame(hist_pane, text="Миниатюры PastVu — выберите похожий исторический ракурс фасада")
        hist_pane.add(hist_controls, weight=0)
        hist_pane.add(hist_preview, weight=1)
        hist_controls.columnconfigure(1, weight=1)

        ttk.Label(hist_controls, text="Адрес:").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(hist_controls, textvariable=self.address).grid(row=0, column=1, sticky="ew", padx=6, pady=6)
        ttk.Button(hist_controls, text="Найти координаты", command=self.start_geocode).grid(row=0, column=2, padx=8, pady=6)

        ttk.Label(hist_controls, text="Широта:").grid(row=1, column=0, sticky="w", padx=8, pady=4)
        coord_frame = ttk.Frame(hist_controls)
        coord_frame.grid(row=1, column=1, sticky="ew", padx=6, pady=4)
        ttk.Entry(coord_frame, textvariable=self.lat, width=15).pack(side="left")
        ttk.Label(coord_frame, text="  Долгота:").pack(side="left", padx=(8, 2))
        ttk.Entry(coord_frame, textvariable=self.lon, width=15).pack(side="left")
        ttk.Button(hist_controls, text="Карта / выбрать точку", command=self.open_map_picker).grid(row=1, column=2, padx=8, pady=4)
        ttk.Label(hist_controls, textvariable=self.geocode_result, foreground="#555", wraplength=560).grid(row=2, column=0, columnspan=3, sticky="w", padx=8, pady=4)

        filters = ttk.Frame(hist_controls)
        filters.grid(row=3, column=0, columnspan=3, sticky="ew", padx=8, pady=6)
        ttk.Label(filters, text="Радиус PastVu, м:").pack(side="left")
        ttk.Entry(filters, textvariable=self.search_distance, width=6).pack(side="left", padx=(4, 12))
        ttk.Label(filters, text="Лимит:").pack(side="left")
        ttk.Entry(filters, textvariable=self.search_limit, width=5).pack(side="left", padx=(4, 12))
        ttk.Label(filters, text="Годы от:").pack(side="left")
        ttk.Entry(filters, textvariable=self.year_from, width=6).pack(side="left", padx=(4, 6))
        ttk.Label(filters, text="до:").pack(side="left")
        ttk.Entry(filters, textvariable=self.year_to, width=6).pack(side="left", padx=(4, 12))

        pastvu_search_line = ttk.Frame(hist_controls)
        pastvu_search_line.grid(row=4, column=0, columnspan=3, sticky="ew", padx=8, pady=(0, 6))
        ttk.Button(pastvu_search_line, text="Найти фото PastVu", command=self.start_pastvu_search).pack(side="left", fill="x", expand=True)

        ttk.Checkbutton(
            hist_controls,
            text="Скрывать вероятные интерьеры / решётки / детали, не похожие на фасад",
            variable=self.exclude_nonfacade,
        ).grid(row=5, column=0, columnspan=3, sticky="w", padx=8, pady=(0, 6))
        hist_file = ttk.Frame(hist_controls)
        hist_file.grid(row=6, column=0, columnspan=3, sticky="ew", padx=8, pady=(0, 6))
        ttk.Button(hist_file, text="Или выбрать историческое фото с компьютера…", command=self.choose_historical_img).pack(side="left")
        ttk.Button(hist_file, text="Открыть выбранное PastVu", command=self.open_selected_pastvu_page).pack(side="left", padx=6)
        ttk.Label(hist_controls, textvariable=self.selected_source_label, foreground="#555", wraplength=560).grid(row=7, column=0, columnspan=3, sticky="w", padx=8, pady=(0, 6))

        self.thumb_area = ScrollableFrame(hist_preview)
        self.thumb_area.pack(fill="both", expand=True, padx=6, pady=6)

        # ---------------- Modern pane ----------------
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)
        modern_pane = ttk.Panedwindow(right, orient="vertical")
        modern_pane.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        modern_controls = ttk.Frame(modern_pane)
        modern_preview = ttk.LabelFrame(modern_pane, text="Миниатюры современных открытых фото — выберите подходящий ракурс")
        modern_pane.add(modern_controls, weight=0)
        modern_pane.add(modern_preview, weight=1)
        modern_controls.columnconfigure(1, weight=1)

        ttk.Label(modern_controls, text="Историческое фото:").grid(row=0, column=0, sticky="w", padx=8, pady=5)
        ttk.Entry(modern_controls, textvariable=self.historical_img).grid(row=0, column=1, sticky="ew", padx=6, pady=5)
        ttk.Button(modern_controls, text="Выбрать…", command=self.choose_historical_img).grid(row=0, column=2, padx=8, pady=5)

        ttk.Label(modern_controls, text="Современное фото:").grid(row=1, column=0, sticky="w", padx=8, pady=5)
        ttk.Entry(modern_controls, textvariable=self.modern_img).grid(row=1, column=1, sticky="ew", padx=6, pady=5)
        ttk.Button(modern_controls, text="Выбрать файл…", command=self.choose_modern_img).grid(row=1, column=2, padx=8, pady=5)
        ttk.Label(modern_controls, textvariable=self.modern_source_label, foreground="#555", wraplength=560).grid(row=2, column=0, columnspan=3, sticky="w", padx=8, pady=(0, 4))

        modern_actions = ttk.Frame(modern_controls)
        modern_actions.grid(row=3, column=0, columnspan=3, sticky="w", padx=8, pady=5)
        ttk.Button(modern_actions, text="Вставить скрин из буфера", command=self.paste_modern_from_clipboard).pack(side="left")
        ttk.Button(modern_actions, text="Обрезать современное фото", command=self.crop_modern_img).pack(side="left", padx=6)
        ttk.Button(modern_actions, text="Открыть современное", command=lambda: self._open_selected_path(self.modern_img.get())).pack(side="left", padx=6)
        ttk.Button(modern_actions, text="Открыть папку проекта", command=lambda: open_path(self.project_root())).pack(side="left", padx=6)

        open_box = ttk.LabelFrame(modern_controls, text="Открытые современные фото рядом с точкой")
        open_box.grid(row=4, column=0, columnspan=3, sticky="ew", padx=8, pady=(8, 4))
        row0 = ttk.Frame(open_box)
        row0.grid(row=0, column=0, columnspan=3, sticky="ew", padx=6, pady=(6, 2))
        ttk.Radiobutton(row0, text="Wikimedia Commons", variable=self.modern_source_kind, value="Wikimedia Commons").pack(side="left")
        ttk.Radiobutton(row0, text="Panoramax", variable=self.modern_source_kind, value="Panoramax").pack(side="left", padx=10)
        ttk.Radiobutton(row0, text="KartaView", variable=self.modern_source_kind, value="KartaView").pack(side="left", padx=10)
        ttk.Label(row0, text="Радиус, м:").pack(side="left")
        ttk.Entry(row0, textvariable=self.modern_search_radius, width=6).pack(side="left", padx=(4, 12))
        ttk.Label(row0, text="Показать:").pack(side="left")
        ttk.Entry(row0, textvariable=self.modern_search_limit, width=5).pack(side="left", padx=(4, 12))
        ttk.Button(row0, text="Найти современные фото", command=self.start_modern_open_search).pack(side="left")
        ttk.Button(row0, text="Ещё +30", command=self.load_more_modern_photos).pack(side="left", padx=6)

        ttk.Label(
            open_box,
            text=(
                "Commons часто даёт обычные фотографии зданий. Panoramax и KartaView — открытые уличные фото; если миниатюры не грузятся, "
                "используйте кнопку “Миниатюра” или откройте страницу/картинку источника."
            ),
            foreground="#555",
            wraplength=640,
        ).grid(row=1, column=0, columnspan=3, sticky="w", padx=6, pady=(2, 6))

        self.modern_thumb_area = ScrollableFrame(modern_preview)
        self.modern_thumb_area.pack(fill="both", expand=True, padx=6, pady=6)

        help_text = (
            "Дальше переходите во вкладку 2. Там оба фото будут показаны в одном окне, "
            "и вы отметите 4 одинаковых угла фасада на старом и современном фото. "
            "Для Roboflow лучше использовать свои фото или открытые фото с понятной лицензией/атрибуцией."
        )
        ttk.Label(modern_controls, text=help_text, wraplength=640, foreground="#333").grid(row=5, column=0, columnspan=3, sticky="w", padx=8, pady=6)

    def _build_rectify_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(1, weight=1)
        box = ttk.LabelFrame(parent, text="Обязательный шаг: выпрямить оба фото по одной и той же плоскости фасада")
        box.grid(row=0, column=0, columnspan=3, sticky="ew", padx=10, pady=10)
        box.columnconfigure(1, weight=1)
        self._row_file(box, "Историческое фото:", self.historical_img, self.choose_historical_img, 0)
        self._row_file(box, "Современное фото:", self.modern_img, self.choose_modern_img, 1)
        self._row_folder(box, "Папка результата:", self.outdir, self.choose_result_dir, 2)

        point_frame = ttk.LabelFrame(parent, text="4 угла фасада")
        point_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=10, pady=8)
        ttk.Label(
            point_frame,
            text="Нажмите кнопку ниже. Откроется одно окно: старое фото слева, современное справа. Так меньше шансов перепутать точки.",
            wraplength=980,
            foreground="#555",
        ).pack(anchor="w", padx=8, pady=(8, 4))
        pf_btns = ttk.Frame(point_frame)
        pf_btns.pack(anchor="w", padx=8, pady=8)
        ttk.Button(pf_btns, text="Указать 4 угла на двух фото одновременно", command=self.pick_both_corners).pack(side="left")
        ttk.Label(pf_btns, textvariable=self.points_status, foreground="#555").pack(side="left", padx=10)

        slider_frame = ttk.LabelFrame(parent, text="Overlay")
        slider_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=10, pady=8)
        ttk.Label(slider_frame, textvariable=self.old_opacity_label).pack(anchor="w", padx=8, pady=(8, 0))
        tk.Scale(slider_frame, from_=0, to=100, orient="horizontal", variable=self.old_opacity,
                 command=self._update_opacity_label, length=420, showvalue=False).pack(anchor="w", padx=8, pady=(0, 4))
        ttk.Checkbutton(
            slider_frame,
            text="Показывать весь исходный снимок (4 угла только для наложения; рекомендуется)",
            variable=self.keep_context,
        ).pack(anchor="w", padx=8, pady=(0, 8))

        btns = ttk.Frame(parent)
        btns.grid(row=3, column=0, columnspan=3, sticky="w", padx=10, pady=10)
        ttk.Button(btns, text="Подготовить выпрямленные фото и overlay", command=self.start_prepare_project).pack(side="left")
        ttk.Button(btns, text="Открыть overlay", command=self.open_overlay).pack(side="left", padx=6)
        ttk.Button(btns, text="Открыть до/после", command=self.open_before_after).pack(side="left", padx=6)
        ttk.Button(btns, text="Открыть папку результата", command=lambda: open_path(Path(self.outdir.get()))).pack(side="left", padx=6)
        ttk.Button(btns, text="Отправить на сайт", command=self.export_to_website).pack(side="left", padx=6)
        ttk.Checkbutton(
            btns,
            text="Автоматически копировать на сайт (код из «Данные дома»)",
            variable=self.auto_export_website,
        ).pack(side="left", padx=8)

        ttk.Label(parent, textvariable=self.rectified_status, font=("TkDefaultFont", 10, "bold")).grid(row=4, column=0, columnspan=3, sticky="w", padx=10, pady=8)
        warning = (
            "Важно: 4 точки должны быть одной и той же плоскостью здания. Не берите выступающий козырёк, дерево, забор, "
            "балкон с объёмом или разные боковые фасады. Включённый расширенный холст не обрезает всё за пределами этих 4 точек — "
            "поэтому надстройка или пристройка останется видимой, даже если её не было на старом фото."
        )
        ttk.Label(parent, text=warning, wraplength=980, foreground="#6b4a00").grid(row=5, column=0, columnspan=3, sticky="w", padx=10, pady=8)

    def _build_analyze_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        view_box = ttk.LabelFrame(parent, text="Смотреть сравнение")
        view_box.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        ttk.Label(
            view_box,
            text="Главные инструменты здесь — overlay и до/после. Сначала глазами проверьте, что фасады совпали, потом размечайте новые элементы.",
            wraplength=980,
            foreground="#555",
        ).pack(anchor="w", padx=8, pady=(8, 4))
        btns1 = ttk.Frame(view_box)
        btns1.pack(anchor="w", padx=8, pady=8)
        ttk.Button(btns1, text="Preview в программе", command=self.open_in_app_preview).pack(side="left")
        ttk.Button(btns1, text="Открыть overlay с ползунком", command=self.open_overlay).pack(side="left", padx=6)
        ttk.Button(btns1, text="Открыть до/после", command=self.open_before_after).pack(side="left", padx=6)
        ttk.Button(btns1, text="Открыть картинку для разметки", command=self.open_labeling_image).pack(side="left", padx=6)

        mark_box = ttk.LabelFrame(parent, text="Разметить новые элементы")
        mark_box.grid(row=1, column=0, sticky="ew", padx=10, pady=8)
        ttk.Label(
            mark_box,
            text=(
                "Обводите только то, что действительно появилось или крупно изменилось: надстройки, пристройки, новые объёмы, "
                "новые ряды окон, изменённые входы. Микро-линии не нужны."
            ),
            wraplength=980,
            foreground="#555",
        ).pack(anchor="w", padx=8, pady=(8, 4))
        btns2 = ttk.Frame(mark_box)
        btns2.pack(anchor="w", padx=8, pady=8)
        ttk.Button(btns2, text="Разметить новые элементы…", command=self.open_annotation_window).pack(side="left")
        ttk.Button(btns2, text="Показать на исходном современном фото", command=self.open_marked_original).pack(side="left", padx=6)
        ttk.Button(btns2, text="Открыть экспорт Roboflow", command=self.open_roboflow_export).pack(side="left", padx=6)
        ttk.Button(btns2, text="Открыть папку результата", command=lambda: open_path(Path(self.outdir.get()))).pack(side="left", padx=6)

        info_box = ttk.LabelFrame(parent, text="Файлы результата")
        info_box.grid(row=2, column=0, sticky="nsew", padx=10, pady=8)
        info = (
            "01_overlay_slider.html — наложение с ползунком\n"
            "02_before_after_slider.html — сравнение до/после\n"
            "03_historical_rectified.png — старый фасад после выпрямления\n"
            "04_modern_rectified.png — современный фасад после выпрямления\n"
            "05_comparison_for_labeling.png — картинка для ручной разметки и будущего Roboflow\n"
            "06_marked_rectified.png — обводки на выпрямленном фасаде\n"
            "07_marked_on_original_modern.png — обводки перенесены на исходное современное фото\n"
            "roboflow_export.zip — COCO segmentation dataset для загрузки в Roboflow"
        )
        ttk.Label(info_box, text=info, justify="left", wraplength=980).pack(anchor="nw", padx=8, pady=8)
        parent.rowconfigure(2, weight=1)

    def _build_straight_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(1, weight=1)
        self._row_file(parent, "Фото фасада:", self.straight_img, self.choose_straight_img, 0)
        self._row_save(parent, "Куда сохранить:", self.straight_out, self.choose_straight_out, 1)
        point_frame = ttk.Frame(parent)
        point_frame.grid(row=2, column=0, columnspan=3, sticky="w", padx=10, pady=8)
        ttk.Button(point_frame, text="Указать 4 угла фасада", command=self.pick_straight_corners).pack(side="left")
        ttk.Label(point_frame, textvariable=self.straight_points_status, foreground="#555").pack(side="left", padx=8)
        ttk.Label(
            parent,
            text=(
                "Все 4 точки — только на одном фасаде (не в небе и не на соседнем здании). "
                "Точка 2 — верхний правый угол того же дома, что точка 1. "
                "Основное сравнение двух фото — вкладки 1 → 2 → 3."
            ),
            wraplength=900,
            foreground="#555",
        ).grid(row=3, column=0, columnspan=3, sticky="w", padx=10, pady=8)
        btns = ttk.Frame(parent)
        btns.grid(row=4, column=0, columnspan=3, sticky="w", padx=10, pady=10)
        ttk.Button(btns, text="Выпрямить по 4 углам", command=self.run_straighten_manual).pack(side="left")
        ttk.Button(btns, text="Открыть папку результата", command=lambda: open_path(Path(self.straight_out.get()).parent)).pack(side="left", padx=8)

    def _row_file(self, parent: ttk.Frame, label: str, var: tk.StringVar, command: Callable[[], None], row: int) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(parent, textvariable=var).grid(row=row, column=1, sticky="ew", padx=6, pady=6)
        ttk.Button(parent, text="Выбрать…", command=command).grid(row=row, column=2, sticky="e", padx=8, pady=6)

    def _row_save(self, parent: ttk.Frame, label: str, var: tk.StringVar, command: Callable[[], None], row: int) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(parent, textvariable=var).grid(row=row, column=1, sticky="ew", padx=6, pady=6)
        ttk.Button(parent, text="Сохранить как…", command=command).grid(row=row, column=2, sticky="e", padx=8, pady=6)

    def _row_folder(self, parent: ttk.Frame, label: str, var: tk.StringVar, command: Callable[[], None], row: int) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(parent, textvariable=var).grid(row=row, column=1, sticky="ew", padx=6, pady=6)
        ttk.Button(parent, text="Папка…", command=command).grid(row=row, column=2, sticky="e", padx=8, pady=6)

    # -------------------------- Paths and project -----------------------

    def project_root(self) -> Path:
        return Path(self.project_dir.get())

    def result_root(self) -> Path:
        root = self.project_root() / "result"
        self.outdir.set(str(root))
        return root

    def choose_project_dir(self) -> None:
        path = filedialog.askdirectory(title="Выберите папку проекта дома")
        if path:
            self._load_project_into_workflow(path)

    def _load_legacy_metadata_coords(self, project_dir: Path) -> None:
        for candidate in (project_dir / "house.json", project_dir / "metadata" / "house.json"):
            if not candidate.exists():
                continue
            try:
                data = json.loads(candidate.read_text(encoding="utf-8"))
                addr = str(data.get("address") or "").strip()
                if addr:
                    self.address.set(addr)
                site = str(data.get("site_card_id") or "").strip()
                if site:
                    self.site_card_id.set(site)
                obj = str(data.get("object_name") or "").strip()
                if obj:
                    self.object_name.set(obj)
                lat = data.get("lat")
                lon = data.get("lon")
                if lat is not None and str(lat).strip():
                    self.lat.set(str(lat))
                if lon is not None and str(lon).strip():
                    self.lon.set(str(lon))
                if hasattr(self, "geocode_result") and addr:
                    self.geocode_result.set(f"Открыт проект: {addr}")
                return
            except Exception:
                continue

    def _parse_float_or_none(self, text: str) -> Optional[float]:
        t = str(text).strip().replace(",", ".")
        if not t:
            return None
        try:
            return float(t)
        except ValueError:
            return None

    def _ensure_project_store_attached(self) -> bool:
        if ProjectStore is None:
            return False
        root = self.project_root()
        if not root.exists():
            return False
        try:
            if self.project_store is None or Path(self.project_store.project_dir).resolve() != root.resolve():
                self.project_store = ProjectStore.load(root)
            return True
        except Exception as exc:
            self._log(f"Проект: {exc}\n")
            return False

    def _catalog_entry_matches_house(self, card_id: str) -> bool:
        if not card_id:
            return True
        try:
            from archiview_project_model import load_website_buildings_catalog, _text_matches_catalog  # type: ignore

            catalog = load_website_buildings_catalog(APP_DIR)
            entry = catalog.get(card_id) if isinstance(catalog, dict) else None
            if not isinstance(entry, dict):
                return True
            return bool(
                _text_matches_catalog(
                    card_id=card_id,
                    entry=entry,
                    address=self.address.get(),
                    object_name=self.object_name.get(),
                    folder_name=self.project_root().name,
                )
            )
        except Exception:
            return True

    def _apply_site_card_autofill(self) -> None:
        """Нормализует MOSCOW_NNN и подставляет код/название из каталога сайта."""
        if infer_site_card_id is None or normalize_site_card_id is None:
            return
        root = self.project_root()
        raw = self.site_card_id.get().strip()
        normalized = normalize_site_card_id(raw)  # type: ignore[misc]
        if normalized and normalized != raw.upper():
            self.site_card_id.set(normalized)
        inferred = infer_site_card_id(  # type: ignore[misc]
            root,
            self.address.get(),
            self.object_name.get(),
            APP_DIR,
        )
        current = normalize_site_card_id(self.site_card_id.get())  # type: ignore[misc]
        if inferred and (not current or (raw and not normalized)):
            self.site_card_id.set(inferred)
        card = normalize_site_card_id(self.site_card_id.get()) or inferred  # type: ignore[misc]
        if website_display_name is not None and not self.object_name.get().strip():
            display = website_display_name(card, APP_DIR)
            if display:
                self.object_name.set(display)
        elif card and website_display_name is not None and not self._catalog_entry_matches_house(card):
            pass

    def _sync_house_identity_from_catalog(self) -> None:
        self._apply_site_card_autofill()

    def _bind_house_field_autosave(self) -> None:
        for var in (self.address, self.lat, self.lon, self.object_name, self.site_card_id):
            var.trace_add("write", self._schedule_house_autosave)

    def _schedule_house_autosave(self, *_args: object) -> None:
        if self._suppress_house_autosave:
            return
        if self._house_save_after_id:
            try:
                self.after_cancel(self._house_save_after_id)
            except Exception:
                pass
        self._house_save_after_id = self.after(900, self._autosave_house_fields)

    def _autosave_house_fields(self) -> None:
        self._house_save_after_id = None
        if self._suppress_house_autosave:
            return
        if not self.project_dir.get().strip():
            return
        if self._persist_house_metadata(quiet=True):
            self._update_house_status_label()

    def _update_house_status_label(self) -> None:
        if not hasattr(self, "geocode_result"):
            return
        parts: List[str] = []
        name = self.object_name.get().strip()
        code = self.site_card_id.get().strip().upper()
        addr = self.address.get().strip()
        lat = self.lat.get().strip()
        lon = self.lon.get().strip()
        if name:
            parts.append(name)
        if code:
            parts.append(code)
        if addr:
            parts.append(addr)
        if lat and lon:
            parts.append(f"{lat}, {lon}")
        if parts:
            self.geocode_result.set(" · ".join(parts))
        else:
            self.geocode_result.set("Выберите дом в таблице или укажите точку на карте")
        self._refresh_workflow_steps()

    def _compute_workflow_steps(self) -> List[Dict[str, object]]:
        root = self.project_root()
        proj_name = root.name
        has_project = (
            proj_name not in ("new_house_project", "house_project")
            or (root / "house.json").exists()
            or (root / "metadata" / "house.json").exists()
        )
        lat_s = self.lat.get().strip().replace(",", ".")
        lon_s = self.lon.get().strip().replace(",", ".")
        has_location = False
        if lat_s and lon_s:
            try:
                float(lat_s)
                float(lon_s)
                has_location = True
            except ValueError:
                has_location = False
        has_location = has_location and bool(self.address.get().strip())
        has_hist = bool(self.historical_sources)
        if not has_hist and self.historical_img.get():
            has_hist = Path(self.historical_img.get()).exists()
        has_mod = bool(self.modern_img.get()) and Path(self.modern_img.get()).exists()
        item = self._get_active_historical_item()
        has_corners = bool(self.modern_points_text.strip()) and bool(
            item and item.old_points_text.strip()
        )
        outdir = Path(self.outdir.get()) if self.outdir.get() else root / "result"
        has_rect = (outdir / "03_historical_rectified.png").exists() and (
            outdir / "04_modern_rectified.png"
        ).exists()
        has_markup = self._work_dir_has_saved_markup()
        return [
            {
                "id": "project",
                "done": has_project,
                "title": "1. Дом в «Мои проекты»",
                "hint": proj_name if has_project else "Откройте или создайте «Новый дом…»",
            },
            {
                "id": "location",
                "done": has_location,
                "title": "2. Адрес и координаты (карта)",
                "hint": "Кнопка «Карта / выбрать точку» в данных дома",
            },
            {
                "id": "historical",
                "done": has_hist,
                "title": "3. Историческое фото",
                "hint": "PastVu или файл слева внизу",
            },
            {
                "id": "modern",
                "done": has_mod,
                "title": "4. Современное фото",
                "hint": "Файл или Wikimedia справа",
            },
            {
                "id": "corners",
                "done": has_corners,
                "title": "5. Четыре угла фасада",
                "hint": "«Указать 4 угла» → вкладка «Выпрямление»",
            },
            {
                "id": "rectify",
                "done": has_rect,
                "title": "6. Выпрямление пары",
                "hint": "Вкладка «2. Выпрямление» → большая синяя кнопка",
            },
            {
                "id": "markup",
                "done": has_markup,
                "title": "7. Разметка и результат",
                "hint": "Вкладки «4. Разметка» и «5. Результат»",
            },
        ]

    def _build_workflow_steps_panel(self, parent: ttk.Widget) -> None:
        wf = ttk.LabelFrame(parent, text="Шаги работы — по порядку (✓ готово, → перейти)")
        wf.pack(fill="both", expand=True)
        wf.columnconfigure(0, weight=1)
        self.workflow_steps_container = ttk.Frame(wf)
        self.workflow_steps_container.pack(fill="x", padx=8, pady=6)
        self._workflow_step_rows: List[Tuple[ttk.Label, ttk.Label, ttk.Button]] = []
        for step in self._compute_workflow_steps():
            row = ttk.Frame(self.workflow_steps_container)
            row.pack(fill="x", pady=1)
            mark = ttk.Label(row, width=3, font=("TkDefaultFont", 11, "bold"))
            mark.pack(side="left", anchor="nw")
            text = ttk.Label(row, anchor="w", justify="left")
            text.pack(side="left", fill="x", expand=True, padx=(4, 8))
            sid = str(step["id"])
            btn = ttk.Button(row, text="→", width=3, command=lambda s=sid: self._workflow_go_step(s))
            btn.pack(side="right")
            self._workflow_step_rows.append((mark, text, btn))
        self.workflow_next_hint = ttk.Label(wf, text="", foreground="#0b6bcb", wraplength=900)
        self.workflow_next_hint.pack(anchor="w", padx=8, pady=(0, 8))

    def _refresh_workflow_steps(self) -> None:
        if not hasattr(self, "_workflow_step_rows"):
            return
        steps = self._compute_workflow_steps()
        next_step: Optional[Dict[str, object]] = None
        for i, step in enumerate(steps):
            if i >= len(self._workflow_step_rows):
                break
            mark_lbl, text_lbl, _btn = self._workflow_step_rows[i]
            done = bool(step.get("done"))
            mark_lbl.configure(text="✓" if done else "○", foreground="#087a20" if done else "#888")
            title = str(step.get("title") or "")
            hint = str(step.get("hint") or "")
            text_lbl.configure(text=f"{title} — {hint}", foreground="#333" if done else "#555")
            if not done and next_step is None:
                next_step = step
        if hasattr(self, "workflow_next_hint"):
            if next_step:
                self.workflow_next_hint.configure(
                    text=f"Следующий шаг: {next_step.get('title')} — {next_step.get('hint')}"
                )
            else:
                self.workflow_next_hint.configure(text="Все шаги выполнены. Можно править разметку и экспортировать на сайт.")
        if self._ensure_project_store_attached():
            self.project_store.house.workflow_steps = {
                str(s.get("id", "")): "done" if s.get("done") else "open" for s in steps
            }

    def _workflow_go_step(self, step_id: str) -> None:
        if hasattr(self, "notebook") and hasattr(self, "tab_select"):
            self.notebook.select(self.tab_select)
        if step_id == "project":
            return
        elif step_id == "location":
            self.open_map_picker()
        elif step_id == "historical":
            return
        elif step_id == "modern":
            return
        elif step_id == "corners":
            if hasattr(self, "notebook") and hasattr(self, "tab_rectify"):
                self.notebook.select(self.tab_rectify)
            if hasattr(self, "pick_corners_for_selected_historical"):
                self.pick_corners_for_selected_historical()
            elif hasattr(self, "pick_both_corners"):
                self.pick_both_corners()
        elif step_id == "rectify":
            if hasattr(self, "notebook") and hasattr(self, "tab_rectify"):
                self.notebook.select(self.tab_rectify)
        elif step_id == "markup":
            if hasattr(self, "notebook"):
                if self._work_dir_has_saved_markup() and hasattr(self, "tab_result"):
                    self.notebook.select(self.tab_result)
                    if hasattr(self, "_refresh_result_canvas"):
                        self._refresh_result_canvas()
                elif hasattr(self, "tab_markup"):
                    self.notebook.select(self.tab_markup)
        self._refresh_workflow_steps()

    def _fit_main_window_to_screen(self) -> None:
        self.update_idletasks()
        sw = max(800, int(self.winfo_screenwidth()))
        sh = max(600, int(self.winfo_screenheight()))
        w = min(1180, sw - 40)
        h = min(820, sh - 72)
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(min(880, w), min(560, h))
        self.maxsize(sw, sh)

    def _configure_vertical_pane(
        self,
        pane: ttk.Panedwindow,
        top: tk.Widget,
        bottom: tk.Widget,
        *,
        top_minsize: int = 220,
        bottom_minsize: int = 140,
        initial_top: int = 320,
    ) -> None:
        def apply() -> None:
            try:
                pane.pane(top, minsize=top_minsize)
                pane.pane(bottom, minsize=bottom_minsize)
                total = max(pane.winfo_height(), top_minsize + bottom_minsize + 40)
                pane.sashpos(0, min(max(initial_top, top_minsize), total - bottom_minsize))
            except Exception:
                pass

        self.after(80, apply)
        pane.bind("<Configure>", lambda _e: self.after(50, apply))

    def _persist_house_metadata(self, *, quiet: bool = False) -> bool:
        self._ensure_project_dirs()
        root = self.project_root()
        address = self.address.get().strip()
        if normalize_address_dedupe is not None:
            address = normalize_address_dedupe(address)  # type: ignore[misc]
            if address != self.address.get().strip():
                self.address.set(address)
        lat = self._parse_float_or_none(self.lat.get())
        lon = self._parse_float_or_none(self.lon.get())
        self._apply_site_card_autofill()
        site_card_id = ""
        if normalize_site_card_id is not None:
            site_card_id = normalize_site_card_id(self.site_card_id.get())  # type: ignore[misc]
        if not site_card_id:
            if propose_site_card_id is not None:
                site_card_id = propose_site_card_id(root, address, self.object_name.get(), APP_DIR)  # type: ignore[misc]
            elif infer_site_card_id is not None:
                site_card_id = infer_site_card_id(root, address, self.object_name.get(), APP_DIR)  # type: ignore[misc]
            site_card_id = normalize_site_card_id(site_card_id) if normalize_site_card_id else site_card_id  # type: ignore[misc]
            if site_card_id:
                self.site_card_id.set(site_card_id)
        object_name = self.object_name.get().strip()
        if not object_name and site_card_id and website_display_name is not None:
            object_name = website_display_name(site_card_id, APP_DIR)
            if object_name:
                self.object_name.set(object_name)

        saved = False
        if self._ensure_project_store_attached():
            house = self.project_store.house
            house.address = address
            house.lat = lat
            house.lon = lon
            house.site_card_id = normalize_site_card_id(site_card_id) or site_card_id  # type: ignore[misc]
            if object_name:
                house.object_name = object_name
            house.project_slug = root.name
            house.workflow_steps = {
                str(s.get("id", "")): "done" if s.get("done") else "open"
                for s in self._compute_workflow_steps()
            }
            self.project_store.save()
            saved = True
        else:
            house_json = root / "house.json"
            legacy_json = root / "metadata" / "house.json"
            payload: Dict[str, object] = {}
            if house_json.exists():
                try:
                    payload = json.loads(house_json.read_text(encoding="utf-8"))
                except Exception:
                    payload = {}
            payload.update(
                {
                    "project_id": root.name,
                    "address": address,
                    "lat": lat,
                    "lon": lon,
                    "site_card_id": site_card_id,
                    "object_name": object_name,
                    "project_slug": root.name,
                    "workflow_steps": {
                        str(s.get("id", "")): "done" if s.get("done") else "open"
                        for s in self._compute_workflow_steps()
                    },
                }
            )
            house_json.parent.mkdir(parents=True, exist_ok=True)
            house_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            legacy_json.parent.mkdir(parents=True, exist_ok=True)
            legacy_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            saved = True

        if saved:
            self._refresh_my_projects_panel()
            if not quiet:
                self._update_house_status_label()
            elif lat is not None and lon is not None:
                pass
        return saved

    def _after_projects_deleted(self, deleted_dirs: List[Path]) -> None:
        current = self.project_root().resolve()
        if any(current == d.resolve() for d in deleted_dirs):
            fresh = APP_DIR / "archiview_projects" / "new_house_project"
            fresh.mkdir(parents=True, exist_ok=True)
            self._load_project_into_workflow(fresh)
        self._refresh_my_projects_panel()

    def _result_workdir_hint(self) -> str:
        if not self.outdir.get():
            return ""
        try:
            rel = str(Path(self.outdir.get()).resolve().relative_to(self.project_root().resolve()))
        except Exception:
            rel = Path(self.outdir.get()).name
        if self.project_store:
            cmp = self.project_store.get_active_comparison()
            if cmp and cmp.is_legacy:
                return f"Папка: {rel} (старая разметка result/)"
        return f"Папка: {rel}"

    def _activate_comparison_workdir(self, comparison: "ComparisonSession") -> None:
        if not self.project_store:
            return
        self.project_store.set_active_comparison(comparison.comparison_id)
        work = comparison.work_path(self.project_store.project_dir)
        work.mkdir(parents=True, exist_ok=True)
        current = str(Path(self.outdir.get()).resolve())
        target = str(work.resolve())
        if current != target:
            self.outdir.set(str(work))
            self._clear_markup_cache()
            if hasattr(self, "_rectified_images_cache"):
                self._rectified_images_cache = None
                self._rectified_cache_key = None
            if hasattr(self, "_refresh_compare_canvas"):
                self._refresh_compare_canvas(save=False)
            if hasattr(self, "_refresh_markup_canvas"):
                self._refresh_markup_canvas()
            if hasattr(self, "_refresh_result_canvas"):
                self._refresh_result_canvas()

    def _create_comparison_for_historical_item(self, item: HistoricalSourceItem) -> Optional["ComparisonSession"]:
        if not self._ensure_project_store_attached():
            return None
        if not self.modern_img.get() or not Path(self.modern_img.get()).exists():
            return None
        hist_path = str(Path(item.path).resolve())
        mod_path = str(Path(self.modern_img.get()).resolve())
        hist_photo = self.project_store.ensure_photo_from_path(hist_path, "historical", title=item.label)
        mod_photo = self.project_store.ensure_photo_from_path(mod_path, "modern")
        title = f"{item.label} + {Path(mod_path).name}"
        cmp = self.project_store.create_comparison(
            title=title,
            modern_photo_id=mod_photo.photo_id,
            historical_photo_ids=[hist_photo.photo_id],
            historical_source_key=item.key,
            modern_source_path=mod_path,
        )
        item.comparison_id = cmp.comparison_id
        self._save_historical_sources()
        self._activate_comparison_workdir(cmp)
        self._log(f"Создано сравнение {cmp.comparison_id} для «{item.label}» — чистая папка.\n")
        self._refresh_project_tabs()
        return cmp

    def _offer_new_comparison_for_historical(self, item: HistoricalSourceItem) -> None:
        if not self._ensure_project_store_attached():
            return
        existing = self.project_store.find_comparison_for_sources(item.key, self.modern_img.get())
        if existing:
            item.comparison_id = existing.comparison_id
            self._save_historical_sources()
            self._activate_comparison_workdir(existing)
            return
        if item.comparison_id:
            cmp = self.project_store.get_comparison(item.comparison_id)
            if cmp:
                self._activate_comparison_workdir(cmp)
                return
        current_has_work = self._work_dir_has_saved_markup() or (
            Path(self.outdir.get()) / "03_historical_rectified.png"
        ).exists()
        if current_has_work:
            create_new = messagebox.askyesno(
                "Новое фото — новое сравнение?",
                f"Добавлено историческое фото «{item.label}».\n\n"
                "В текущей папке уже есть выпрямление или разметка от другого фото.\n\n"
                "Создать отдельное сравнение с чистой папкой?\n"
                "(Старая работа сохранится в своём сравнении.)",
            )
            if not create_new:
                self._log(f"Фото «{item.label}» добавлено в список; активная папка не менялась.\n")
                return
        if not self.modern_img.get() or not Path(self.modern_img.get()).exists():
            self._log(f"Фото «{item.label}» добавлено. Выберите современное фото — затем выпрямление.\n")
            return
        self._create_comparison_for_historical_item(item)

    def _work_dir_matches_historical(self, work_dir: Path, item: HistoricalSourceItem) -> bool:
        if self.project_store:
            cmp = self.project_store.find_comparison_for_sources(item.key, self.modern_img.get())
            if cmp:
                return cmp.work_path(self.project_store.project_dir).resolve() == work_dir.resolve()
        for name in ("project_v8.json", "project_v7.json", "project_v6.json"):
            proj = work_dir / name
            if not proj.exists():
                continue
            try:
                data = json.loads(proj.read_text(encoding="utf-8"))
                inputs = data.get("inputs", data)
                hist = inputs.get("historical_image") or inputs.get("old_image") or inputs.get("historical")
                if hist:
                    return str(Path(hist).resolve()) == str(Path(item.path).resolve())
            except Exception:
                continue
        return not (work_dir / "03_historical_rectified.png").exists()

    def _switch_session_for_historical(self, item: HistoricalSourceItem) -> None:
        if not self._ensure_project_store_attached():
            self._clear_markup_cache()
            return
        if item.comparison_id:
            cmp = self.project_store.get_comparison(item.comparison_id)
            if cmp:
                self._activate_comparison_workdir(cmp)
                return
        existing = self.project_store.find_comparison_for_sources(item.key, self.modern_img.get())
        if existing:
            item.comparison_id = existing.comparison_id
            self._save_historical_sources()
            self._activate_comparison_workdir(existing)
            return
        current = Path(self.outdir.get())
        has_work = (current / "03_historical_rectified.png").exists() or self._work_dir_has_saved_markup()
        if has_work and not self._work_dir_matches_historical(current, item):
            if self.modern_img.get() and Path(self.modern_img.get()).exists():
                self._create_comparison_for_historical_item(item)
                return
        self._clear_markup_cache()

    def _ensure_work_session_for_active_pair(self) -> Optional[Path]:
        item = self._get_active_historical_item()
        if not item or not self.modern_img.get() or not Path(self.modern_img.get()).exists():
            return Path(self.outdir.get()) if self.outdir.get() else None
        if not self._ensure_project_store_attached():
            return Path(self.outdir.get())
        self._switch_session_for_historical(item)
        if item.comparison_id:
            cmp = self.project_store.get_comparison(item.comparison_id)
            if cmp:
                return cmp.work_path(self.project_store.project_dir)
        if not self._work_dir_has_saved_markup() and not (Path(self.outdir.get()) / "03_historical_rectified.png").exists():
            cmp = self._create_comparison_for_historical_item(item)
            if cmp:
                return cmp.work_path(self.project_store.project_dir)
        return Path(self.outdir.get())

    def _sync_historical_list_from_folder(self) -> None:
        hist_dir = self.project_root() / "historical_sources"
        if not hist_dir.exists():
            return
        image_ext = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".bmp"}
        for f in sorted(hist_dir.iterdir()):
            if not f.is_file() or f.suffix.lower() not in image_ext:
                continue
            self._add_historical_source(
                str(f),
                f.stem,
                source_type="folder",
                set_active=False,
                save=False,
            )
        if self.historical_sources and not self.active_historical_key:
            self._set_active_historical(self.historical_sources[0], save=False)
        if self.historical_sources:
            self._save_historical_sources()
            self._refresh_historical_sources_tree()

    def _load_modern_from_folder(self) -> None:
        if self.modern_img.get() and Path(self.modern_img.get()).exists():
            return
        mod_dir = self.project_root() / "modern_sources"
        if not mod_dir.exists():
            return
        image_ext = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".bmp"}
        for f in sorted(mod_dir.iterdir()):
            if f.is_file() and f.suffix.lower() in image_ext:
                self.modern_img.set(str(f))
                if hasattr(self, "modern_source_label"):
                    self.modern_source_label.set(f"Современное фото из папки проекта: {f.name}")
                break

    def _load_project_into_workflow(self, project_dir: str | Path) -> None:
        path = Path(project_dir)
        self._suppress_house_autosave = True
        try:
            self.project_dir.set(str(path))
            self._ensure_project_dirs()
            self.project_store = None
            self.site_card_id.set("")
            self.object_name.set("")
            self.address.set("")
            self.lat.set("")
            self.lon.set("")
            if ProjectStore is not None:
                try:
                    self.project_store = ProjectStore.load(path)
                    house = self.project_store.house
                    if house.address:
                        self.address.set(house.address)
                    if house.site_card_id:
                        card = (
                            normalize_site_card_id(house.site_card_id)  # type: ignore[misc]
                            if normalize_site_card_id is not None
                            else house.site_card_id.strip().upper()
                        )
                        self.site_card_id.set(card or house.site_card_id)
                    if house.object_name:
                        self.object_name.set(house.object_name)
                    if house.lat is not None:
                        self.lat.set(str(house.lat))
                    if house.lon is not None:
                        self.lon.set(str(house.lon))
                    work = self.project_store.work_dir_for_active()
                    self.outdir.set(str(work))
                    self._apply_site_card_autofill()
                except Exception as exc:
                    self._log(f"Метаданные проекта: {exc}\n")
                    self.outdir.set(str(path / "result"))
            else:
                self.outdir.set(str(path / "result"))
            self._load_legacy_metadata_coords(path)
            self._sync_house_identity_from_catalog()
            self.historical_sources = []
            self.active_historical_key = ""
            self.old_points_text = ""
            self.modern_points_text = ""
            self.modern_crop_rect_text = ""
            self.historical_img.set("")
            self.modern_img.set("")
            self._clear_markup_cache()
            self._load_historical_sources()
            self._sync_historical_list_from_folder()
            self._load_modern_from_folder()
            active_item = self._get_active_historical_item()
            if active_item:
                self._switch_session_for_historical(active_item)
            self._persist_house_metadata(quiet=True)
            self._refresh_my_projects_panel()
            self._log(f"Открыт проект: {path.name}\n")
            self._update_house_status_label()
            if hasattr(self, "_refresh_compare_source_thumbnails"):
                self.after(0, self._refresh_compare_source_thumbnails)
            if hasattr(self, "_refresh_result_canvas"):
                self.after(50, self._refresh_result_canvas)
        finally:
            self._suppress_house_autosave = False

    def _refresh_my_projects_panel(self) -> None:
        if hasattr(self, "my_projects_panel"):
            self.my_projects_panel.refresh()

    def _allocate_new_project_dir(self, slug: str) -> Path:
        clean = safe_filename(slug.strip(), "house_project") if slug.strip() else "house_project"
        if clean in ("new_house_project", "house_project"):
            clean = time.strftime("house_%Y%m%d_%H%M%S")
        base = APP_DIR / "archiview_projects" / clean
        root = base
        n = 2
        while root.exists():
            root = Path(f"{base}_{n}")
            n += 1
        return root

    def _init_new_project_on_disk(self, root: Path, *, address: str, object_name: str) -> None:
        for sub in ("historical_sources", "modern_sources", "metadata", "comparisons", "result"):
            (root / sub).mkdir(parents=True, exist_ok=True)
        site_id = ""
        if next_site_card_id is not None:
            try:
                site_id = next_site_card_id(APP_DIR)  # type: ignore[misc]
            except Exception:
                site_id = ""
        payload = {
            "project_id": root.name,
            "project_slug": root.name,
            "address": address.strip(),
            "object_name": object_name.strip(),
            "site_card_id": site_id,
            "lat": None,
            "lon": None,
            "workflow_steps": {},
        }
        text = json.dumps(payload, ensure_ascii=False, indent=2)
        (root / "house.json").write_text(text, encoding="utf-8")
        (root / "metadata" / "house.json").write_text(text, encoding="utf-8")

    def new_house_project(self) -> None:
        text = simpledialog.askstring(
            "Новый дом",
            "Введите адрес дома или имя папки проекта\n"
            "(например: Большая Ордынка 17  или  dom_so_zveryami  или  MOSCOW_004):",
            parent=self,
        )
        if text is None:
            return
        text = text.strip()
        if not text:
            return
        # Короткое имя без пробелов — как заданная папка; иначе — адрес и slug из него.
        if re.match(r"^[\w.\-]+$", text, re.UNICODE) and " " not in text:
            slug = text
            address = ""
            object_name = text.replace("_", " ").replace("-", " ")
        else:
            address = text
            object_name = ""
            slug = (
                propose_project_slug("", address, text)  # type: ignore[misc]
                if propose_project_slug is not None
                else safe_filename(address, "house_project")
            )
            if not slug or slug in ("house_project", "new_house_project"):
                slug = safe_filename(address, "house_project")
        root = self._allocate_new_project_dir(slug)
        try:
            self._init_new_project_on_disk(root, address=address, object_name=object_name)
            self._load_project_into_workflow(root)
            self._refresh_my_projects_panel()
            if hasattr(self, "my_projects_panel"):
                self.my_projects_panel.select_by_folder(root.name)
            messagebox.showinfo(
                "Новый дом создан",
                f"Папка проекта:\n{root}\n\nДальше выберите фото PastVu и современное снимок на вкладке «Источники».",
                parent=self,
            )
        except Exception as exc:
            messagebox.showerror("Не удалось создать дом", str(exc), parent=self)

    def open_excel_import_dialog(self) -> None:
        if HouseDatabaseFrame is None:
            messagebox.showwarning(
                "Модуль не найден",
                "Для импорта Excel нужен файл archiview_house_db.py рядом с программой.",
            )
            return
        win = tk.Toplevel(self)
        win.title("Импорт домов из Excel / CSV")
        win.geometry("980x620")
        win.minsize(820, 520)
        frame = HouseDatabaseFrame(
            win,
            project_root=APP_DIR / "archiview_projects",
            on_house_selected=lambda record, paths: self._use_house_from_db(record, paths) or win.destroy(),
            on_log=self._log,
        )
        frame.pack(fill="both", expand=True)

    def choose_result_dir(self) -> None:
        path = filedialog.askdirectory(title="Выберите папку результата")
        if path:
            self.outdir.set(path)

    def _build_houses_tab(self, parent: ttk.Frame) -> None:
        if CombinedHousesTab is None:
            ttk.Label(
                parent,
                text=(
                    "Модули базы домов не найдены.\n\n"
                    "Нужны archiview_house_db.py и archiview_project_ui.py рядом с archiview_gui.py."
                ),
                foreground="red",
                justify="left",
            ).pack(anchor="nw", padx=12, pady=12)
            return

        self.houses_tab_frame = CombinedHousesTab(
            parent,
            project_root=APP_DIR / "archiview_projects",
            on_house_from_db=self._use_house_from_db,
            on_open_project_dir=lambda p: self._open_project_dir(p, go_tab="photos"),
            on_log=self._log,
        )
        self.houses_tab_frame.pack(fill="both", expand=True)

    def _build_photos_tab(self, parent: ttk.Frame) -> None:
        if PhotosTabFrame is None:
            ttk.Label(parent, text="Модуль archiview_project_ui.py не найден.", foreground="red").pack(
                anchor="nw", padx=12, pady=12
            )
            return
        self.photos_tab_frame = PhotosTabFrame(
            parent,
            get_store=self._get_project_store,
            on_photo_added=self._after_project_photo_added,
            on_log=self._log,
        )
        self.photos_tab_frame.pack(fill="both", expand=True)

    def _build_comparisons_tab(self, parent: ttk.Frame) -> None:
        if ComparisonsTabFrame is None:
            ttk.Label(parent, text="Модуль archiview_project_ui.py не найден.", foreground="red").pack(
                anchor="nw", padx=12, pady=12
            )
            return
        self.comparisons_tab_frame = ComparisonsTabFrame(
            parent,
            get_store=self._get_project_store,
            on_open_comparison=self._open_comparison_session,
            on_log=self._log,
        )
        self.comparisons_tab_frame.pack(fill="both", expand=True)

    def _get_project_store(self):
        return self.project_store

    def _refresh_project_tabs(self) -> None:
        self._refresh_my_projects_panel()

    def _attach_project_store(self, project_dir: str | Path) -> None:
        if ProjectStore is None:
            return
        self.project_store = ProjectStore.load(project_dir)
        work = self.project_store.work_dir_for_active()
        self.project_dir.set(str(self.project_store.project_dir))
        self.outdir.set(str(work))
        if self.project_store.house.address:
            self.address.set(self.project_store.house.address)
        if self.project_store.house.lat is not None:
            self.lat.set(str(self.project_store.house.lat))
        if self.project_store.house.lon is not None:
            self.lon.set(str(self.project_store.house.lon))
        self._apply_active_comparison_photos()
        self._ensure_project_dirs()
        self._load_historical_sources()
        self._refresh_my_projects_panel()

    def _open_project_dir(self, project_dir: str | Path, go_tab: str = "result") -> None:
        try:
            self._load_project_into_workflow(project_dir)
            if not hasattr(self, "notebook"):
                return
            tab_map = {
                "sources": getattr(self, "tab_select", None),
                "result": getattr(self, "tab_result", None),
                "compare": getattr(self, "tab_compare", None),
                "markup": getattr(self, "tab_markup", None),
                "rectify": getattr(self, "tab_rectify", None),
            }
            target = tab_map.get(go_tab) or getattr(self, "tab_select", None)
            if target is not None:
                self.notebook.select(target)
            if go_tab == "result" and hasattr(self, "_refresh_result_canvas"):
                self._refresh_result_canvas()
            elif go_tab == "compare" and hasattr(self, "_refresh_compare_canvas"):
                self._refresh_compare_canvas(save=False)
        except Exception as exc:
            messagebox.showerror("Ошибка открытия проекта", str(exc))

    def _compare_source_thumb_path(self, kind: str) -> Optional[Path]:
        outdir = Path(self.outdir.get())
        if kind == "historical":
            candidates = [
                outdir / "03_historical_rectified.png",
                Path(self.historical_img.get()) if self.historical_img.get() else None,
            ]
        else:
            candidates = [
                outdir / "04_modern_rectified.png",
                Path(self.modern_img.get()) if self.modern_img.get() else None,
            ]
        for cand in candidates:
            if cand and cand.exists():
                return cand
        return None

    def _set_photo_thumb(self, label: ttk.Label, path: Optional[Path], caption: str, ref_attr: str) -> None:
        if Image is None or ImageTk is None or not path or not path.exists():
            label.configure(image="", text=f"{caption}\n(нет фото)")
            return
        try:
            pil = Image.open(path).convert("RGB")  # type: ignore[union-attr]
            pil.thumbnail((168, 112))
            photo = ImageTk.PhotoImage(pil)  # type: ignore[union-attr]
            setattr(self, ref_attr, photo)
            label.configure(image=photo, text="")
        except Exception:
            label.configure(image="", text=f"{caption}\n(ошибка загрузки)")

    def _refresh_compare_source_thumbnails(self) -> None:
        if not hasattr(self, "compare_hist_thumb_label"):
            return
        hist = self._compare_source_thumb_path("historical")
        mod = self._compare_source_thumb_path("modern")
        self._set_photo_thumb(self.compare_hist_thumb_label, hist, "Историческое", "_compare_hist_thumb_ref")
        self._set_photo_thumb(self.compare_modern_thumb_label, mod, "Современное", "_compare_modern_thumb_ref")
        hist_name = hist.name if hist else "—"
        mod_name = mod.name if mod else "—"
        if hasattr(self, "compare_thumb_caption"):
            self.compare_thumb_caption.set(f"Сравниваем: {hist_name}  ↔  {mod_name}")

    def _apply_active_comparison_photos(self) -> None:
        if not self.project_store:
            return
        cmp = self.project_store.get_active_comparison()
        if not cmp:
            return
        if cmp.modern_photo_id:
            photo = self.project_store.photos.get(cmp.modern_photo_id)
            if photo:
                path = self.project_store.resolve_photo_path(photo)
                if path:
                    self.modern_img.set(str(path))
        active_hist = cmp.active_historical_photo_id or (
            cmp.historical_photo_ids[0] if cmp.historical_photo_ids else ""
        )
        if active_hist:
            photo = self.project_store.photos.get(active_hist)
            if photo:
                path = self.project_store.resolve_photo_path(photo)
                if path:
                    self.historical_img.set(str(path))

    def _clear_markup_cache(self) -> None:
        self.embedded_annotations = []
        self.current_markup_points = []
        self._annotation_loaded_for = None
        if hasattr(self, "_preview_base_cache"):
            self._preview_base_cache.clear()

    def _work_dir_has_saved_markup(self) -> bool:
        outdir = Path(self.outdir.get())
        ann_path = outdir / "annotations" / "manual_annotations.json"
        if ann_path.exists():
            try:
                data = json.loads(ann_path.read_text(encoding="utf-8"))
                anns = data.get("annotations", [])
                if isinstance(anns, list) and len(anns) > 0:
                    return True
            except Exception:
                pass
        legacy_marked = outdir / "07_marked_on_original_modern.png"
        return legacy_marked.exists()

    def _after_project_photo_added(self, photo) -> None:
        """После добавления фото — предложить новое сравнение, чтобы не смешивать со старой разметкой."""
        if not self.project_store:
            return

        cmp = self.project_store.get_active_comparison()
        cmp_label = cmp.comparison_id if cmp else "result/"
        has_old = self._work_dir_has_saved_markup() or (cmp is not None and cmp.is_legacy)

        if photo.kind == "historical":
            pair_list = self.project_store.list_photos("modern")
            question = (
                f"Добавлено историческое фото {photo.photo_id}.\n\n"
                f"Сейчас активно сравнение «{cmp_label}»"
                + (" — там уже есть разметка." if has_old else ".")
                + "\n\nСоздать новое сравнение для этой пары?\n"
                "Старая разметка в result/ и cmp_legacy_001 не изменится."
            )
        else:
            pair_list = self.project_store.list_photos("historical")
            question = (
                f"Добавлено современное фото {photo.photo_id}.\n\n"
                f"Создать новое сравнение с этим фото?\n"
                "Старая разметка останется в прежнем сравнении."
            )

        if not pair_list:
            messagebox.showinfo(
                "Фото добавлено",
                f"{photo.photo_id} сохранено в проект.\n\n"
                f"Добавьте также {'современное' if photo.kind == 'historical' else 'историческое'} фото, "
                "затем создайте сравнение во вкладке «2. Сравнения».",
            )
            return

        if has_old or cmp is not None:
            create_new = messagebox.askyesno("Новое фото — новое сравнение?", question)
        else:
            create_new = messagebox.askyesno(
                "Создать сравнение?",
                f"Фото {photo.photo_id} добавлено.\n\nСразу создать для него новое сравнение?",
            )

        if not create_new:
            self._log(
                f"Фото {photo.photo_id} только добавлено в библиотеку. "
                f"Активная разметка по-прежнему в «{cmp_label}».\n"
            )
            return

        if photo.kind == "historical":
            modern_id = pair_list[0].photo_id
            hist_ids = [photo.photo_id]
        else:
            modern_id = photo.photo_id
            hist_ids = [pair_list[0].photo_id]

        title = f"{photo.photo_id} + {modern_id if photo.kind == 'historical' else hist_ids[0]}"
        new_cmp = self.project_store.create_comparison(
            title=title,
            modern_photo_id=modern_id,
            historical_photo_ids=hist_ids,
        )
        self.outdir.set(str(new_cmp.work_path(self.project_store.project_dir)))
        self._apply_active_comparison_photos()
        self._clear_markup_cache()
        self._ensure_project_dirs()
        self._log(
            f"Создано новое сравнение {new_cmp.comparison_id} — чистая папка, старая разметка не затронута.\n"
        )
        self._refresh_project_tabs()
        if hasattr(self, "notebook") and hasattr(self, "tab_select"):
            self.notebook.select(self.tab_select)

    def _open_comparison_session(self, comparison) -> None:
        if not self.project_store:
            return
        try:
            self.project_store.set_active_comparison(comparison.comparison_id)
            work = self.project_store.work_dir_for_active()
            self.outdir.set(str(work))
            self._apply_active_comparison_photos()
            self._clear_markup_cache()
            self._ensure_project_dirs()
            self._log(f"Активно сравнение: {comparison.comparison_id} → {work}\n")
            if comparison.is_legacy:
                self._log("Legacy-сравнение использует папку result/ — существующая разметка сохранена.\n")
            if hasattr(self, "notebook") and hasattr(self, "tab_select"):
                self.notebook.select(self.tab_select)
            self._refresh_project_tabs()
        except Exception as exc:
            messagebox.showerror("Ошибка открытия сравнения", str(exc))

    def _use_house_from_db(self, record, paths) -> None:
        """Дом из Excel — создаёт папку и открывает на вкладке «Источники»."""
        try:
            self.address.set(record.address or "")
            self.project_dir.set(str(paths["project_dir"]))
            self.outdir.set(str(paths["result_dir"]))

            if getattr(record, "lat", None) is not None:
                self.lat.set(str(record.lat))
            if getattr(record, "lon", None) is not None:
                self.lon.set(str(record.lon))

            if hasattr(self, "geocode_result"):
                self.geocode_result.set(f"Выбран дом из базы: {record.address}")

            self.current_house_record = record
            self.current_house_paths = paths
            if getattr(record, "object_name", None):
                self.object_name.set(str(record.object_name))
            self._load_project_into_workflow(paths["project_dir"])
            self._persist_house_metadata()
            self._log(f"Выбран дом из базы: {record.address}\n")
            self._log(f"Папка проекта: {paths['project_dir']}\n")
            if hasattr(self, "notebook") and hasattr(self, "tab_select"):
                self.notebook.select(self.tab_select)

        except Exception as exc:
            messagebox.showerror("Ошибка выбора дома", str(exc))

    def _ensure_project_dirs(self) -> None:
        root = self.project_root()
        for sub in ("historical_sources", "modern_sources", "result"):
            (root / sub).mkdir(parents=True, exist_ok=True)

    def _project_slug(self) -> str:
        """Имя папки для нового дома: название объекта или адрес, не имя файла PastVu."""
        if propose_project_slug is not None:
            slug = propose_project_slug(  # type: ignore[misc]
                self.object_name.get(),
                self.address.get(),
                "",
            )
            if slug and slug not in ("house_project", "new_house_project"):
                return slug
        if self.object_name.get().strip():
            return safe_filename(self.object_name.get().strip(), "house_project")
        if self.address.get().strip():
            return safe_filename(self.address.get().strip(), "house_project")
        code = self.site_card_id.get().strip().upper()
        if code and re.match(r"MOSCOW_\d{3}", code):
            return safe_filename(code.lower(), "house_project")
        return "house_project"

    def _project_is_established(self) -> bool:
        """Открытый дом — не переносить в другую папку при карте/адресе/фото."""
        path_s = self.project_dir.get().strip()
        if not path_s:
            return False
        root = Path(path_s)
        if (root / "house.json").exists() or (root / "metadata" / "house.json").exists():
            return True
        return root.name not in ("new_house_project", "house_project", "")

    def _ensure_work_dirs(self) -> None:
        """Обновить только рабочую папку (result/ или comparisons/), не меняя проект."""
        if not self.project_dir.get().strip():
            return
        if self._ensure_project_store_attached():
            work = self.project_store.work_dir_for_active()
            self.outdir.set(str(work))
        else:
            self.outdir.set(str(self.project_root() / "result"))
        self._ensure_project_dirs()

    def _suggest_project_dir(self) -> None:
        """Подобрать папку только для нового дома. Открытый проект — только обновить result/comparisons."""
        if self._project_is_established():
            self._ensure_work_dirs()
            return
        slug = self._project_slug()
        if not slug or slug in ("new_house_project", "house_project"):
            slug = "house_project"
        root = APP_DIR / "archiview_projects" / slug
        if root.resolve() != self.project_root().resolve():
            i = 2
            base = root
            while root.exists() and not (root / "house.json").exists():
                root = Path(f"{base}_{i}")
                i += 1
        self.project_dir.set(str(root))
        self.outdir.set(str(root / "result"))
        self._ensure_project_dirs()

    def _copy_to_project_sources(self, src: str | Path, subfolder: str, prefix: str = "") -> Path:
        self._ensure_project_dirs()
        src_path = Path(src)
        dest_dir = self.project_root() / subfolder
        try:
            if src_path.resolve().parent == dest_dir.resolve():
                return src_path
        except Exception:
            pass
        suffix = src_path.suffix or ".jpg"
        stem = safe_filename(src_path.stem, "photo")
        name = f"{prefix}{stem}{suffix}" if prefix else f"{stem}{suffix}"
        dest = dest_dir / name
        i = 2
        while dest.exists():
            dest = dest_dir / f"{prefix}{stem}_{i}{suffix}"
            i += 1
        shutil.copy2(src_path, dest)
        return dest

    def _open_selected_path(self, text: str) -> None:
        if text and Path(text).exists():
            open_path(Path(text))
        else:
            messagebox.showinfo("Файл не выбран", "Сначала выберите файл.")

    # --------------------------- Environment and threads ----------------

    def _check_environment(self) -> None:
        if cv is None:
            messagebox.showwarning(
                "OpenCV не установлен",
                "OpenCV пока не установлен. Запустите install_windows.bat, затем откройте программу снова.",
            )
        if Image is None or ImageTk is None:
            messagebox.showwarning(
                "Pillow не установлен",
                "Для миниатюр PastVu нужна библиотека Pillow. Запустите install_windows.bat ещё раз.",
            )

    def _log(self, text: str) -> None:
        log = getattr(self, "log", None)
        if log is None:
            return
        try:
            log.insert("end", text)
            log.see("end")
            self.update_idletasks()
        except tk.TclError:
            pass

    def _run_bg(self, title: str, func: Callable[[], object], on_done: Callable[[object], None]) -> None:
        self._log(f"\n{title}…\n")

        def worker() -> None:
            try:
                result = func()
            except Exception as exc:
                err = str(exc)

                def show(msg: str = err) -> None:
                    self._log(f"Ошибка: {msg}\n")
                    messagebox.showerror("Не получилось", msg)

                self.after(0, show)
                return

            def done() -> None:
                on_done(result)

            self.after(0, done)

        threading.Thread(target=worker, daemon=True).start()

    # ------------------------- Geocoding / PastVu ----------------------

    def start_geocode(self) -> None:
        address = self.address.get().strip()
        if not address:
            messagebox.showinfo("Нужен адрес", "Введите адрес или используйте кнопку “Карта / выбрать точку”.")
            return

        def work() -> object:
            return geocode_address(address)

        def done(result: object) -> None:
            lat, lon, display = result  # type: ignore[misc]
            self.lat.set(f"{lat:.7f}")
            self.lon.set(f"{lon:.7f}")
            if display and not self.address.get().strip():
                self.address.set(display)
            self._suggest_project_dir()
            self._sync_house_identity_from_catalog()
            if self._persist_house_metadata(quiet=True):
                self._update_house_status_label()
            else:
                self.geocode_result.set(display)
            self._log(f"Координаты найдены: {lat:.7f}, {lon:.7f}\n")

        self._run_bg("Поиск координат", work, done)

    def _parse_int_or_none(self, text: str) -> Optional[int]:
        t = str(text).strip()
        if not t:
            return None
        return int(t)

    def _looks_non_facade(self, photo: PastVuPhoto) -> bool:
        text = f"{photo.title} {photo.caption}".lower()
        return any(k in text for k in NON_FACADE_KEYWORDS)

    def start_pastvu_search(self) -> None:
        try:
            lat = float(self.lat.get().replace(",", "."))
            lon = float(self.lon.get().replace(",", "."))
        except Exception:
            messagebox.showinfo("Нужны координаты", "Сначала найдите адрес, отметьте точку на карте или введите широту и долготу вручную.")
            return
        distance = int(self.search_distance.get())
        limit = int(self.search_limit.get())
        year_from = self._parse_int_or_none(self.year_from.get())
        year_to = self._parse_int_or_none(self.year_to.get())

        def work() -> object:
            return find_pastvu_nearest(lat, lon, distance=distance, limit=limit, year_from=year_from, year_to=year_to)

        def done(result: object) -> None:
            photos = list(result)  # type: ignore[arg-type]
            before = len(photos)
            if self.exclude_nonfacade.get():
                photos = [p for p in photos if not self._looks_non_facade(p)]
            self.pastvu_photos = photos
            self._render_thumbnails()
            self._log(f"Найдено фото PastVu: {before}; показано после фильтра: {len(self.pastvu_photos)}. Выберите фасад с самым близким ракурсом.\n")
            if not self.pastvu_photos:
                messagebox.showinfo("Фото не найдены", "Попробуйте увеличить радиус поиска, убрать фильтр интерьеров или ограничения по годам.")

        self._run_bg("Поиск фотографий PastVu", work, done)

    def _clear_thumb_area(self) -> None:
        for child in self.thumb_area.inner.winfo_children():
            child.destroy()
        self.pastvu_thumb_refs.clear()

    def _load_thumbnail_async(
        self,
        label: ttk.Label,
        urls: Iterable[str],
        max_size: Tuple[int, int],
        refs: List[object],
        fail_text: str = "миниатюра\nне загрузилась",
    ) -> None:
        """Download thumbnail bytes in a background thread and attach PhotoImage in Tk thread."""
        url_list = [str(u).strip() for u in urls if str(u or "").strip()]

        def worker() -> None:
            raw: Optional[bytes] = None
            for url in url_list:
                try:
                    raw = request_bytes(url, timeout=14)
                    if raw:
                        break
                except Exception:
                    raw = None
            def update() -> None:
                try:
                    if not label.winfo_exists():
                        return
                    if not raw:
                        label.configure(text=fail_text, image="")
                        return
                    pil = Image.open(io.BytesIO(raw)).convert("RGB")  # type: ignore[union-attr]
                    pil.thumbnail(max_size)
                    thumb = ImageTk.PhotoImage(pil)  # type: ignore[union-attr]
                    refs.append(thumb)
                    label.configure(image=thumb, text="")
                except Exception:
                    try:
                        label.configure(text=fail_text, image="")
                    except Exception:
                        pass
            self.after(0, update)
        threading.Thread(target=worker, daemon=True).start()

    def _manual_load_thumbnail(self, label: ttk.Label, urls: Iterable[str], max_size: Tuple[int, int], refs: List[object]) -> None:
        try:
            label.configure(text="загружаю\nминиатюру…", image="")
        except Exception:
            pass
        self._load_thumbnail_async(label, urls, max_size, refs, fail_text="миниатюра\nне загрузилась\nнажмите ещё раз")

    def _render_thumbnails(self) -> None:
        self._clear_thumb_area()
        if Image is None or ImageTk is None:
            ttk.Label(self.thumb_area.inner, text="Не установлен Pillow. Запустите install_windows.bat.").grid(row=0, column=0)
            return
        width = max(1, self.thumb_area.canvas.winfo_width()) if hasattr(self, "thumb_area") else 620
        cols = max(1, min(5, width // 205))
        for idx, photo in enumerate(self.pastvu_photos):
            r = idx // cols
            c = idx % cols
            cell = ttk.Frame(self.thumb_area.inner, relief="ridge", borderwidth=1)
            cell.grid(row=r, column=c, sticky="nsew", padx=5, pady=5)
            lbl = ttk.Label(cell, text="загружаю\nминиатюру…", width=20, anchor="center", justify="center")
            lbl.pack(padx=4, pady=(4, 2), ipadx=4, ipady=18)
            urls = [photo.thumb_url, photo.standard_url, photo.original_url]
            self._load_thumbnail_async(lbl, urls, (180, 125), self.pastvu_thumb_refs)
            caption = ttk.Label(cell, text=photo.caption, wraplength=180, justify="center")
            caption.pack(padx=4, pady=2)
            btns = ttk.Frame(cell)
            btns.pack(padx=4, pady=(2, 5))
            ttk.Button(btns, text="Добавить", command=lambda p=photo: self.select_pastvu_photo(p)).pack(side="left")
            ttk.Button(btns, text="Миниатюра", command=lambda l=lbl, u=urls: self._manual_load_thumbnail(l, u, (180, 125), self.pastvu_thumb_refs)).pack(side="left", padx=4)
            ttk.Button(btns, text="Страница", command=lambda p=photo: webbrowser.open(p.page_url)).pack(side="left", padx=4)

    def select_pastvu_photo(self, photo: PastVuPhoto) -> None:
        self.selected_pastvu = photo
        self._suggest_project_dir()
        downloads = self.project_root() / "historical_sources"
        self._log(f"\nСкачиваю выбранное фото PastVu #{photo.cid} в папку дома…\n")

        def work() -> object:
            return download_pastvu_photo(photo, downloads, prefer_original=False)

        def done(result: object) -> None:
            path = Path(result)  # type: ignore[arg-type]
            label = f"PastVu #{photo.cid}"
            item = self._add_historical_source(str(path), label, source_type="pastvu", pastvu_cid=photo.cid)
            self.selected_source_label.set(f"Добавлено в список: {label}")
            self._log(f"Старое фото сохранено: {path}\n")

        self._run_bg("Скачивание PastVu", work, done)

    def open_selected_pastvu_page(self) -> None:
        if self.selected_pastvu and self.selected_pastvu.page_url:
            webbrowser.open(self.selected_pastvu.page_url)
        else:
            messagebox.showinfo("Фото не выбрано", "Сначала выберите миниатюру PastVu.")

    def _set_coords_from_map(self, lat: float, lon: float) -> None:
        self.lat.set(f"{lat:.7f}")
        self.lon.set(f"{lon:.7f}")
        self.geocode_result.set(f"Точка на карте: {lat:.7f}, {lon:.7f} — определяю адрес…")
        self._suggest_project_dir()
        self._log(f"Координаты с карты: {lat:.7f}, {lon:.7f}\n")

        def work() -> object:
            return reverse_geocode_address(lat, lon)

        def done(result: object) -> None:
            display, short = result  # type: ignore[misc]
            merged = short or display
            if merge_map_address is not None:
                merged = merge_map_address(self.address.get().strip(), merged)  # type: ignore[misc]
            elif normalize_address_dedupe is not None:
                merged = normalize_address_dedupe(merged)  # type: ignore[misc]
            if merged:
                self.address.set(merged)
            hint = ""
            card = ""
            if normalize_site_card_id is not None:
                card = normalize_site_card_id(self.site_card_id.get())  # type: ignore[misc]
            addr_l = (merged or "").lower()
            if card and not self._catalog_entry_matches_house(card):
                parts = [p.strip() for p in (merged or "").split(",") if p.strip()]
                short_name = ", ".join(parts[1:]) if len(parts) > 1 and parts[0].casefold() in ("москва", "moscow", "г москва") else (merged or "")
                if short_name:
                    self.object_name.set(short_name)
                hint = ""
                if card == "MOSCOW_004" and "ордын" in addr_l:
                    hint = " Для Большой Ордынки 17 в каталоге сайта обычно MOSCOW_001, не MOSCOW_004."
                elif card == "MOSCOW_001" and "кривоколен" in addr_l:
                    hint = " Для Кривоколенного в каталоге — MOSCOW_004."
            has_house = _address_has_house_number(merged or "")
            if not has_house and merged:
                extra = simpledialog.askstring(
                    "Номер дома",
                    f"Карта определила улицу, но не номер здания:\n{merged}\n\n"
                    "Введите номер и строение (например 14с3) — они добавятся к адресу:",
                    parent=self,
                )
                if extra and str(extra).strip():
                    hn = str(extra).strip()
                    merged = f"{merged}, {hn}" if hn.lower() not in merged.lower() else merged
                    if normalize_address_dedupe is not None:
                        merged = normalize_address_dedupe(merged)  # type: ignore[misc]
                    self.address.set(merged)
                    has_house = True
            self._apply_site_card_autofill()
            if self._persist_house_metadata(quiet=True):
                self._update_house_status_label()
                self._refresh_my_projects_panel()
                if has_house:
                    msg = f"С карты сохранено в «Данные дома» и в папку проекта:\n{merged}"
                    if hint:
                        msg += f"\n\nВнимание:{hint}"
                    self.geocode_result.set(msg.replace("\n\n", " — "))
                    messagebox.showinfo("Данные с карты сохранены", msg, parent=self)
                else:
                    self.geocode_result.set(
                        f"С карты: {merged} — номер не найден в OSM; введите номер вручную в поле «Адрес»"
                    )
            else:
                self._update_house_status_label()
                self.geocode_result.set(f"Координаты: {lat:.7f}, {lon:.7f} — адрес: {merged}")
            self._log(f"Адрес по карте (папка «{Path(self.project_dir.get()).name}» не менялась): {merged}\n")
            self._refresh_workflow_steps()

        self._run_bg("Адрес по точке на карте", work, done)

    def _ensure_map_callback_server(self) -> str:
        if self._map_server is not None:
            port = self._map_server.server_address[1]
            return f"http://127.0.0.1:{port}/set"
        app = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):  # type: ignore[override]
                try:
                    parsed = urlparse(self.path)
                    qs = parse_qs(parsed.query)
                    lat = float(qs.get("lat", [""])[0])
                    lon = float(qs.get("lon", [""])[0])
                    app.after(0, lambda: app._set_coords_from_map(lat, lon))
                    body = b"OK"
                    self.send_response(200)
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                except Exception as exc:
                    body = str(exc).encode("utf-8")
                    self.send_response(400)
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)

            def log_message(self, _format: str, *_args: object) -> None:
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._map_server = server
        self._map_server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        self._map_server_thread.start()
        port = server.server_address[1]
        return f"http://127.0.0.1:{port}/set"

    def open_map_picker(self) -> None:
        # Opens a Leaflet map in the browser. A click sends coordinates back to this running Tk app via localhost.
        try:
            lat = float(self.lat.get().replace(",", ".")) if self.lat.get().strip() else 55.751244
            lon = float(self.lon.get().replace(",", ".")) if self.lon.get().strip() else 37.618423
        except Exception:
            lat, lon = 55.751244, 37.618423
        callback = self._ensure_map_callback_server()
        self._ensure_project_dirs()
        path = self.project_root() / "pick_point_map.html"
        html_text = f"""<!doctype html><html lang='ru'><head><meta charset='utf-8'>
<title>Выбрать точку здания</title>
<link rel='stylesheet' href='https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'>
<style>body{{font-family:Arial,sans-serif;margin:0}} #map{{height:84vh}} .box{{padding:12px;background:#fff;box-shadow:0 1px 8px #bbb;position:relative;z-index:999}} input{{font-size:18px;width:360px}} button{{font-size:16px}} .ok{{color:#087a20;font-weight:bold}}</style></head>
<body><div class='box'><b>Клик по крыше/контуру здания</b> (не по проезжей части), затем «Передать в программу».<br>
Координаты и адрес с номером дома подставятся в «Данные дома».<br>
<input id='coords' value='{lat:.7f}, {lon:.7f}'><button onclick='sendCoords()'>Передать в программу</button> <span id='status'></span></div>
<div id='map'></div><script src='https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'></script><script>
const cb='{callback}';
const map=L.map('map').setView([{lat:.7f},{lon:.7f}],19);
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',{{maxZoom:20, attribution:'© OpenStreetMap'}}).addTo(map);
let marker=L.marker([{lat:.7f},{lon:.7f}]).addTo(map);
let last={{lat:{lat:.7f},lng:{lon:.7f}}};
function sendCoords(){{
  document.getElementById('coords').value=last.lat.toFixed(7)+', '+last.lng.toFixed(7);
  const img=new Image(); img.src=cb+'?lat='+last.lat.toFixed(7)+'&lon='+last.lng.toFixed(7)+'&t='+(Date.now());
  document.getElementById('status').innerHTML='<span class="ok">передано — ждите адрес в программе</span>';
}}
map.on('click',e=>{{
  last=e.latlng; marker.setLatLng(e.latlng);
  document.getElementById('coords').value=last.lat.toFixed(7)+', '+last.lng.toFixed(7);
  document.getElementById('status').textContent='точка выбрана — нажмите «Передать в программу»';
}});
</script></body></html>"""
        path.write_text(html_text, encoding="utf-8")
        open_path(path)
        messagebox.showinfo(
            "Карта открыта",
            "1. Увеличьте карту и кликните по зданию (крыша/контур), не по улице.\n"
            "2. Нажмите «Передать в программу».\n"
            "3. Если номер дома не подставился — появится окно для ввода (например 14с3).",
        )

    # ------------------------- Modern open imagery ----------------------

    def _get_current_coords(self) -> Tuple[float, float]:
        try:
            lat = float(self.lat.get().replace(",", "."))
            lon = float(self.lon.get().replace(",", "."))
            return lat, lon
        except Exception:
            raise RuntimeError("Сначала найдите адрес, отметьте точку на карте или вручную введите широту и долготу.")

    def load_more_modern_photos(self) -> None:
        try:
            self.modern_search_limit.set(int(self.modern_search_limit.get()) + 30)
        except Exception:
            self.modern_search_limit.set(60)
        self.start_modern_open_search()

    def start_modern_open_search(self) -> None:
        try:
            lat, lon = self._get_current_coords()
            radius = int(self.modern_search_radius.get())
            limit = int(self.modern_search_limit.get())
        except Exception as exc:
            messagebox.showinfo("Нужны координаты", str(exc))
            return
        source = self.modern_source_kind.get()

        def work() -> object:
            if source == "Wikimedia Commons":
                return wikimedia_commons_search(lat, lon, radius, limit)
            if source == "Panoramax":
                return panoramax_search(lat, lon, radius, limit)
            if source == "KartaView":
                return kartaview_search(lat, lon, radius, limit)
            if source == "Mapillary":
                return mapillary_search(lat, lon, radius, limit, self.mapillary_token.get())
            return wikimedia_commons_search(lat, lon, radius, limit)

        def done(result: object) -> None:
            self.open_modern_photos = list(result)  # type: ignore[arg-type]
            self._render_modern_open_thumbnails()
            self._log(f"Найдено современных фото {source}: {len(self.open_modern_photos)}. Выберите ракурс фасада справа.\n")
            if not self.open_modern_photos:
                messagebox.showinfo("Фото не найдены", "Попробуйте увеличить радиус или выбрать другой источник.")

        self._run_bg(f"Поиск современных фото {source}", work, done)

    def _clear_modern_thumb_area(self) -> None:
        if not hasattr(self, "modern_thumb_area"):
            return
        for child in self.modern_thumb_area.inner.winfo_children():
            child.destroy()
        self.open_modern_thumb_refs.clear()

    def _render_modern_open_thumbnails(self) -> None:
        self._clear_modern_thumb_area()
        if Image is None or ImageTk is None:
            ttk.Label(self.modern_thumb_area.inner, text="Не установлен Pillow. Запустите install_windows.bat.").grid(row=0, column=0)
            return
        width = max(1, self.modern_thumb_area.canvas.winfo_width()) if hasattr(self, "modern_thumb_area") else 620
        cols = max(1, min(4, width // 255))
        for idx, photo in enumerate(self.open_modern_photos):
            r = idx // cols
            c = idx % cols
            cell = ttk.Frame(self.modern_thumb_area.inner, relief="ridge", borderwidth=1)
            cell.grid(row=r, column=c, sticky="nsew", padx=5, pady=5)
            lbl = ttk.Label(cell, text="загружаю\nминиатюру…", width=25, anchor="center", justify="center")
            lbl.pack(padx=4, pady=(4, 2), ipadx=4, ipady=20)
            urls = [photo.thumb_url, photo.image_url]
            self._load_thumbnail_async(lbl, urls, (240, 160), self.open_modern_thumb_refs)
            caption = ttk.Label(cell, text=photo.caption, wraplength=240, justify="center")
            caption.pack(padx=4, pady=2)
            btns = ttk.Frame(cell)
            btns.pack(padx=4, pady=(2, 5))
            ttk.Button(btns, text="Выбрать", command=lambda p=photo: self.select_open_modern_photo(p)).pack(side="left")
            ttk.Button(btns, text="Миниатюра", command=lambda l=lbl, u=urls: self._manual_load_thumbnail(l, u, (240, 160), self.open_modern_thumb_refs)).pack(side="left", padx=4)
            ttk.Button(btns, text="Картинка", command=lambda p=photo: webbrowser.open(p.image_url or p.page_url)).pack(side="left", padx=4)
            ttk.Button(btns, text="Страница", command=lambda p=photo: webbrowser.open(p.page_url or "https://kartaview.org/")).pack(side="left", padx=4)

    def _write_source_note(self, source_path: Path, metadata: Dict[str, object]) -> None:
        try:
            meta_path = source_path.with_suffix(source_path.suffix + ".source.json")
            payload = dict(metadata)
            payload["local_image"] = str(source_path)
            payload["saved_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            meta_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            self._log(f"Не удалось сохранить паспорт источника: {exc}\n")

    def _set_modern_image_path(self, path: Path, label: str, metadata: Optional[Dict[str, object]] = None) -> None:
        self.modern_img.set(str(path))
        self.modern_source_label.set(label)
        self.modern_meta = metadata or {}
        if metadata:
            self._write_source_note(path, metadata)
        self.old_points_text = ""
        self.modern_points_text = ""
        self.modern_crop_rect_text = ""
        self.points_status.set("Углы сброшены: выбрано новое современное фото.")

    def select_open_modern_photo(self, photo: OpenStreetPhoto) -> None:
        self._suggest_project_dir()
        downloads = self.project_root() / "modern_sources"
        self._log(f"\nСкачиваю выбранное современное фото {photo.source} {photo.id} в папку дома…\n")

        def work() -> object:
            return download_open_street_photo(photo, downloads)

        def done(result: object) -> None:
            path = Path(result)  # type: ignore[arg-type]
            meta = asdict(photo)
            meta["source_type"] = "open_street_imagery"
            meta["license_warning_ru"] = "Проверьте атрибуцию и лицензию перед публикацией/Roboflow. KartaView и многие файлы Commons требуют указания автора/лицензии."
            self._set_modern_image_path(path, f"Выбрано {photo.source}; сохранено в modern_sources.", meta)
            self._log(f"Современное фото сохранено: {path}\n")

        self._run_bg(f"Скачивание {photo.source}", work, done)

    def paste_modern_from_clipboard(self) -> None:
        if ImageGrab is None or Image is None:
            messagebox.showwarning("Pillow не установлен", "Для вставки картинки из буфера нужна Pillow. Запустите install_windows.bat.")
            return
        try:
            clip = ImageGrab.grabclipboard()
        except Exception as exc:
            messagebox.showerror("Буфер недоступен", f"Не удалось прочитать буфер обмена: {exc}")
            return
        if clip is None:
            messagebox.showinfo("В буфере нет картинки", "Сначала сделайте скриншот Win+Shift+S или скопируйте изображение.")
            return
        self._suggest_project_dir()
        dest_dir = self.project_root() / "modern_sources"
        dest_dir.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        target = dest_dir / f"clipboard_modern_{timestamp}.png"
        try:
            if isinstance(clip, list) and clip:
                # Windows may put copied files in the clipboard.
                src = Path(str(clip[0]))
                if src.exists():
                    copied = self._copy_to_project_sources(src, "modern_sources", prefix="clipboard_file_")
                    self._set_modern_image_path(copied, "Современное фото выбрано из файла в буфере и скопировано в modern_sources.", {"source_type": "clipboard_file"})
                    self._log(f"Файл из буфера скопирован: {copied}\n")
                    return
            if hasattr(clip, "convert"):
                pil = clip.convert("RGB")
                pil.save(target)
                self._set_modern_image_path(target, "Современное фото вставлено из буфера и сохранено в modern_sources.", {"source_type": "clipboard_image"})
                self._log(f"Скрин из буфера сохранён: {target}\n")
                return
        except Exception as exc:
            messagebox.showerror("Не удалось вставить", str(exc))
            return
        messagebox.showinfo("Не картинка", "В буфере обмена не найдено изображение.")

    def crop_modern_img(self) -> None:
        if not self.modern_img.get() or not Path(self.modern_img.get()).exists():
            messagebox.showinfo("Нужно современное фото", "Сначала выберите или вставьте современное фото.")
            return
        src_path = Path(self.modern_img.get())

        def receive(bbox: Tuple[int, int, int, int]) -> None:
            try:
                img = cv_read(src_path)
                x0, y0, x1, y1 = bbox
                crop = img[y0:y1, x0:x1].copy()
                self._suggest_project_dir()
                dest_dir = self.project_root() / "modern_sources"
                dest_dir.mkdir(parents=True, exist_ok=True)
                target = dest_dir / f"cropped_{safe_filename(src_path.stem)}_{time.strftime('%Y%m%d_%H%M%S')}.png"
                cv_write(target, crop)
                meta = dict(self.modern_meta or {})
                meta.update({"source_type": meta.get("source_type", "cropped_modern"), "crop_from": str(src_path), "crop_bbox_xyxy": list(bbox)})
                self._set_modern_image_path(target, "Современное фото обрезано и сохранено в modern_sources.", meta)
                self._log(f"Обрезка сохранена: {target}\n")
            except Exception as exc:
                messagebox.showerror("Не удалось обрезать", str(exc))

        CropWindow(self, str(src_path), "Обрезать современное фото", receive)

    def open_mapillary_nearby(self) -> None:
        try:
            lat, lon = self._get_current_coords()
            webbrowser.open(f"https://www.mapillary.com/app/?lat={lat:.7f}&lng={lon:.7f}&z=18")
        except Exception:
            webbrowser.open("https://www.mapillary.com/app/")

    def open_kartaview_nearby(self) -> None:
        try:
            lat, lon = self._get_current_coords()
            webbrowser.open(f"https://kartaview.org/map/@{lat:.7f},{lon:.7f},18z")
        except Exception:
            webbrowser.open("https://kartaview.org/")

    # ----------------------------- File pickers -------------------------

    def choose_historical_img(self) -> None:
        path = filedialog.askopenfilename(title="Выберите историческое фото", filetypes=IMAGE_TYPES)
        if path:
            self.selected_pastvu = None
            self._suggest_project_dir()
            final_path = path
            try:
                copied = self._copy_to_project_sources(path, "historical_sources", prefix="manual_old_")
                final_path = str(copied)
                self._log(f"Историческое фото скопировано в папку проекта: {copied}\n")
            except Exception as exc:
                self._log(f"Не удалось скопировать историческое фото в проект: {exc}\nИспользую исходный путь.\n")
            label = Path(final_path).name
            item = self._add_historical_source(final_path, label, source_type="file")
            self.selected_source_label.set(f"Добавлено в список: {label}")

    def _historical_sources_json(self) -> Path:
        return self.project_root() / "metadata" / "historical_sources.json"

    def _save_historical_sources(self) -> None:
        try:
            path = self._historical_sources_json()
            path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "modern_points_text": self.modern_points_text,
                "modern_crop_rect_text": self.modern_crop_rect_text,
                "active_key": self.active_historical_key,
                "items": [asdict(item) for item in self.historical_sources],
            }
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _load_historical_sources(self) -> None:
        path = self._historical_sources_json()
        self.historical_sources = []
        self.active_historical_key = ""
        if not path.exists():
            if self.historical_img.get() and Path(self.historical_img.get()).exists():
                p = str(Path(self.historical_img.get()).resolve())
                self._add_historical_source(p, Path(p).name, source_type="legacy", save=False, set_active=True)
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            self.modern_points_text = str(data.get("modern_points_text") or "")
            self.modern_crop_rect_text = str(data.get("modern_crop_rect_text") or "")
            self.active_historical_key = str(data.get("active_key") or "")
            for raw in data.get("items", []):
                if not isinstance(raw, dict) or not raw.get("path"):
                    continue
                resolved = str(Path(raw["path"]).resolve())
                self.historical_sources.append(
                    HistoricalSourceItem(
                        key=str(raw.get("key") or resolved),
                        path=str(raw["path"]),
                        label=str(raw.get("label") or Path(raw["path"]).name),
                        old_points_text=str(raw.get("old_points_text") or ""),
                        crop_rect_text=str(raw.get("crop_rect_text") or ""),
                        source_type=str(raw.get("source_type") or "file"),
                        pastvu_cid=raw.get("pastvu_cid"),
                        comparison_id=str(raw.get("comparison_id") or ""),
                    )
                )
            active = self._get_active_historical_item()
            if active:
                self.historical_img.set(active.path)
                self.old_points_text = active.old_points_text
            elif self.historical_sources:
                self._set_active_historical(self.historical_sources[0], save=False)
            self._refresh_historical_sources_tree()
        except Exception:
            pass

    def _add_historical_source(
        self,
        path: str,
        label: str,
        *,
        source_type: str = "file",
        pastvu_cid: Optional[int] = None,
        set_active: bool = True,
        save: bool = True,
    ) -> HistoricalSourceItem:
        key = str(Path(path).resolve())
        for item in self.historical_sources:
            if item.key == key:
                if set_active:
                    self._set_active_historical(item, save=save)
                return item
        item = HistoricalSourceItem(
            key=key,
            path=path,
            label=label,
            source_type=source_type,
            pastvu_cid=pastvu_cid,
        )
        self.historical_sources.append(item)
        if set_active:
            self._set_active_historical(item, save=save)
        elif save:
            self._save_historical_sources()
            self._refresh_historical_sources_tree()
        if save and set_active:
            self.after(0, lambda i=item: self._offer_new_comparison_for_historical(i))
        return item

    def _get_active_historical_item(self) -> Optional[HistoricalSourceItem]:
        if not self.historical_sources:
            return None
        if self.active_historical_key:
            for item in self.historical_sources:
                if item.key == self.active_historical_key:
                    return item
        return self.historical_sources[0]

    def _set_active_historical(self, item: HistoricalSourceItem, *, save: bool = True) -> None:
        self.active_historical_key = item.key
        self.historical_img.set(item.path)
        self.old_points_text = item.old_points_text
        if item.old_points_text:
            self.points_status.set(f"4 угла заданы для: {item.label}")
        else:
            self.points_status.set(f"Активно: {item.label}. Углы ещё не выбраны.")
        self._refresh_historical_sources_tree()
        self._switch_session_for_historical(item)
        if save:
            self._save_historical_sources()

    def _refresh_historical_sources_tree(self) -> None:
        if not hasattr(self, "hist_sources_tree"):
            return
        tree = self.hist_sources_tree
        tree.delete(*tree.get_children())
        for i, item in enumerate(self.historical_sources):
            active = "●" if item.key == self.active_historical_key else ""
            pts = "Да" if item.old_points_text else "Нет"
            tree.insert("", "end", iid=str(i), values=(active, item.label, pts, item.source_type))

    def _selected_historical_source(self) -> Optional[HistoricalSourceItem]:
        if not hasattr(self, "hist_sources_tree"):
            return self._get_active_historical_item()
        sel = self.hist_sources_tree.selection()
        if not sel:
            return self._get_active_historical_item()
        idx = int(sel[0])
        if 0 <= idx < len(self.historical_sources):
            return self.historical_sources[idx]
        return self._get_active_historical_item()

    def activate_selected_historical_source(self) -> None:
        item = self._selected_historical_source()
        if not item:
            messagebox.showinfo("Список пуст", "Сначала добавьте историческое фото из PastVu или с компьютера.")
            return
        self._set_active_historical(item)

    def remove_selected_historical_source(self) -> None:
        item = self._selected_historical_source()
        if not item:
            return
        if not messagebox.askyesno("Удалить из списка", f"Убрать «{item.label}» из списка сравнения?"):
            return
        self.historical_sources = [x for x in self.historical_sources if x.key != item.key]
        if self.active_historical_key == item.key:
            self.active_historical_key = ""
            self.old_points_text = ""
            if self.historical_sources:
                self._set_active_historical(self.historical_sources[0])
            else:
                self.historical_img.set("")
                self._refresh_historical_sources_tree()
                self._save_historical_sources()
            return
        self._refresh_historical_sources_tree()
        self._save_historical_sources()

    def _historical_sources_for_picker(self) -> List[Dict[str, str]]:
        out: List[Dict[str, str]] = []
        for it in self.historical_sources:
            if Path(it.path).exists():
                out.append(
                    {
                        "path": it.path,
                        "label": it.label,
                        "points": it.old_points_text or "",
                        "crop_rect": it.crop_rect_text or "",
                        "key": it.key,
                    }
                )
        return out

    def _apply_picker_historical_points(self, hist_sources: List[Dict[str, str]]) -> None:
        by_path = {str(s.get("path") or ""): s for s in hist_sources}
        for it in self.historical_sources:
            if it.path in by_path:
                row = by_path[it.path]
                it.old_points_text = str(row.get("points") or "")
                it.crop_rect_text = str(row.get("crop_rect") or "")

    def pick_corners_for_selected_historical(self) -> None:
        item = self._selected_historical_source()
        if not item:
            messagebox.showinfo("Список пуст", "Сначала добавьте историческое фото в список слева.")
            return
        if not Path(item.path).exists():
            messagebox.showinfo("Файл не найден", f"Не найдено: {item.path}")
            return
        if not self.modern_img.get() or not Path(self.modern_img.get()).exists():
            messagebox.showinfo("Нужно современное фото", "Справа выберите современное фото для сравнения.")
            return
        sources = self._historical_sources_for_picker()
        if not sources:
            messagebox.showinfo("Нет файлов", "Нет доступных исторических фото на диске.")
            return
        self._set_active_historical(item, save=False)
        start = next((i for i, s in enumerate(sources) if s["path"] == item.path), 0)

        def receive(
            old_points: str,
            modern_points: str,
            hist_sources: List[Dict[str, str]],
            modern_crop_rect: str,
        ) -> None:
            self._apply_picker_historical_points(hist_sources)
            item.old_points_text = old_points
            self.old_points_text = old_points
            self.modern_points_text = modern_points
            self.modern_crop_rect_text = modern_crop_rect
            self.points_status.set(f"4 угла заданы для: {item.label}")
            if self.modern_points_text:
                self.rectified_status.set("Углы выбраны. Можно выпрямлять на вкладке «Выпрямление».")
            self._save_historical_sources()
            self._refresh_historical_sources_tree()
            self._log(f"4 угла сохранены для {item.label}.\n")
            self._refresh_workflow_steps()

        DualFacadePointPicker(
            self,
            self.modern_img.get(),
            receive,
            historical_sources=sources,
            start_index=start,
            initial_modern_points_text=self.modern_points_text,
            initial_modern_crop_rect_text=self.modern_crop_rect_text,
            lock_modern_when_complete=False,
        )

    def choose_modern_img(self) -> None:
        path = filedialog.askopenfilename(title="Выберите современное фото", filetypes=IMAGE_TYPES)
        if path:
            self.modern_img.set(path)
            self._suggest_project_dir()
            try:
                copied = self._copy_to_project_sources(path, "modern_sources", prefix="modern_")
                self._set_modern_image_path(copied, "Современное фото выбрано с компьютера и скопировано в modern_sources.", {"source_type": "local_file", "original_path": path})
                self._log(f"Современное фото скопировано в папку проекта: {copied}\n")
            except Exception as exc:
                self._set_modern_image_path(Path(path), "Современное фото выбрано с компьютера, но не скопировано в проект.", {"source_type": "local_file", "original_path": path})
                self._log(f"Не удалось скопировать современное фото в проект: {exc}\nИспользую исходный путь.\n")
            self._refresh_workflow_steps()

    # ----------------------------- Points and rectification -------------

    def pick_both_corners(self) -> None:
        item = self._get_active_historical_item()
        if not item or not Path(item.path).exists():
            messagebox.showinfo(
                "Нужно старое фото",
                "Сначала добавьте историческое фото в список на вкладке «Источники» (PastVu или файл).",
            )
            return
        if not self.modern_img.get() or not Path(self.modern_img.get()).exists():
            messagebox.showinfo("Нужно современное фото", "Сначала выберите современное фото.")
            return

        sources = self._historical_sources_for_picker()
        if not sources:
            messagebox.showinfo("Нет файлов", "Нет доступных исторических фото на диске.")
            return
        start = next((i for i, s in enumerate(sources) if s["path"] == item.path), 0)

        def receive(
            old_points: str,
            modern_points: str,
            hist_sources: List[Dict[str, str]],
            modern_crop_rect: str,
        ) -> None:
            self._apply_picker_historical_points(hist_sources)
            item.old_points_text = old_points
            self.old_points_text = old_points
            self.modern_points_text = modern_points
            self.modern_crop_rect_text = modern_crop_rect
            self.points_status.set(f"4 угла заданы для: {item.label}")
            self.rectified_status.set("Углы выбраны. Теперь нажмите “Подготовить выпрямленные фото и overlay”.")
            self._save_historical_sources()
            self._refresh_historical_sources_tree()
            self._log("4 пары углов выбраны в одном окне.\n")

        DualFacadePointPicker(
            self,
            self.modern_img.get(),
            receive,
            historical_sources=sources,
            start_index=start,
            initial_modern_points_text=self.modern_points_text,
            initial_modern_crop_rect_text=self.modern_crop_rect_text,
            lock_modern_when_complete=False,
        )

    def _update_opacity_label(self, _value: object = None) -> None:
        self.old_opacity_label.set(f"Видимость старого фото в overlay: {int(self.old_opacity.get())}%")

    def start_prepare_project(self) -> None:
        if not self.historical_img.get() or not self.modern_img.get():
            messagebox.showinfo("Нужны два фото", "Во вкладке 1 выберите историческое и современное фото.")
            return
        if not self.old_points_text or not self.modern_points_text:
            messagebox.showinfo("Нужны точки", "Во вкладке 2 нажмите “Указать 4 угла на двух фото одновременно”.")
            return
        self._ensure_work_session_for_active_pair()
        self._persist_house_metadata()
        outdir = Path(self.outdir.get())
        pastvu_meta = asdict(self.selected_pastvu) if self.selected_pastvu else {}

        active = self._get_active_historical_item()
        old_crop = (active.crop_rect_text if active else "") or ""
        def work() -> object:
            return prepare_rectified_project(
                Path(self.historical_img.get()),
                Path(self.modern_img.get()),
                self.old_points_text,
                self.modern_points_text,
                outdir,
                old_opacity_percent=int(self.old_opacity.get()),
                pastvu_meta=pastvu_meta,
                modern_meta=self.modern_meta,
                keep_context=bool(self.keep_context.get()),
                old_crop_rect_text=old_crop,
                modern_crop_rect_text=self.modern_crop_rect_text,
            )

        def done(_result: object) -> None:
            self.rectified_status.set(f"Готово. Выпрямленная пара и overlay сохранены: {outdir}")
            self._log(f"Готово. Результаты сохранены в: {outdir}\n")
            messagebox.showinfo(
                "Готово",
                "Выпрямленная пара, overlay, до/после и картинка для разметки созданы.\n"
                "Сначала откройте overlay / до-после и проверьте совпадение. Если фасад вывернулся — заново укажите 4 угла.",
            )
            open_path(outdir)
            self._maybe_auto_export_to_website()

        self._run_bg("Подготовка выпрямленной пары", work, done)

    # ----------------------------- Result opening -----------------------

    def _open_result_file(self, filename: str, missing: str) -> None:
        path = Path(self.outdir.get()) / filename
        if path.exists():
            open_path(path)
        else:
            messagebox.showinfo("Файл ещё не создан", missing)

    def _website_repo_root(self) -> Path:
        return Path(r"C:\Users\Marusia\Projects\chtenie-gorodskoy-pamyati")

    def _resolve_site_card_id_for_export(self) -> str:
        card = ""
        if normalize_site_card_id is not None:
            card = normalize_site_card_id(self.site_card_id.get())  # type: ignore[misc]
        if not card and propose_site_card_id is not None:
            card = propose_site_card_id(  # type: ignore[misc]
                self.project_root(),
                self.address.get(),
                self.object_name.get(),
                APP_DIR,
            )
            if normalize_site_card_id is not None:
                card = normalize_site_card_id(card)  # type: ignore[misc]
        if not card:
            match = re.match(r"(MOSCOW_\d{3})", self.project_root().name.upper())
            if match:
                card = match.group(1)
        return card or ""

    def _sync_export_to_website(self, *, quiet: bool = False, show_dialog: bool = True) -> bool:
        """Копирует result/ в public/explorer/MOSCOW_NNN без ручного ввода кода."""
        card_id = self._resolve_site_card_id_for_export()
        if not card_id:
            if not quiet:
                messagebox.showinfo(
                    "Код сайта не найден",
                    "Укажите «Код на сайте» (MOSCOW_001 …) в «Данные дома» и сохраните.",
                )
            return False
        script = APP_DIR / "copy_to_website.ps1"
        if not script.exists():
            if not quiet:
                messagebox.showerror("Скрипт не найден", f"Не найден:\n{script}")
            return False
        result_dir = str(Path(self.outdir.get()))
        repo = self._website_repo_root()
        cmd = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
            "-CardId",
            card_id,
            "-ResultDir",
            result_dir,
            "-RepoRoot",
            str(repo),
            "-NoPrompt",
        ]

        def work() -> str:
            proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
            if proc.returncode != 0:
                raise RuntimeError(proc.stderr or proc.stdout or f"exit code {proc.returncode}")
            return proc.stdout.strip()

        def done_export(output: object) -> None:
            text = str(output).strip()
            if len(text) > 800:
                text = text[-800:]
            self._log(f"\nНа сайт скопировано ({card_id}): {repo / 'public' / 'explorer' / card_id}\n")
            if show_dialog:
                messagebox.showinfo(
                    "Скопировано на сайт",
                    f"Папка сайта обновлена: public/explorer/{card_id}/\n"
                    f"Код взят из поля «Код на сайте»: {card_id}\n\n"
                    "Дальше в GitHub Desktop: Commit → Push.\n\n" + text,
                )

        self._run_bg(f"Копирование на сайт ({card_id})", work, done_export)
        return True

    def export_to_website(self) -> None:
        """Копирует result/ на сайт — код MOSCOW_NNN из «Данные дома»."""
        self._sync_export_to_website(show_dialog=True)

    def open_in_app_preview(self) -> None:
        try:
            ComparisonPreviewWindow(self, Path(self.outdir.get()))
        except Exception as exc:
            messagebox.showinfo("Preview ещё не готов", str(exc))

    def open_overlay(self) -> None:
        self._open_result_file("01_overlay_slider.html", "Сначала во вкладке 2 подготовьте выпрямленные фото и overlay.")

    def open_before_after(self) -> None:
        self._open_result_file("02_before_after_slider.html", "Сначала во вкладке 2 подготовьте выпрямленные фото и overlay.")

    def open_labeling_image(self) -> None:
        self._open_result_file("05_comparison_for_labeling.png", "Сначала во вкладке 2 подготовьте выпрямленные фото и overlay.")

    def open_marked_original(self) -> None:
        self._open_result_file("07_marked_on_original_modern.png", "Сначала сделайте и сохраните разметку.")

    def open_roboflow_export(self) -> None:
        path = Path(self.outdir.get()) / "roboflow_export.zip"
        if path.exists():
            open_path(path.parent)
        else:
            messagebox.showinfo("Экспорт ещё не создан", "Сначала сделайте и сохраните разметку.")

    def open_annotation_window(self) -> None:
        outdir = Path(self.outdir.get())
        if not (outdir / "05_comparison_for_labeling.png").exists():
            messagebox.showinfo("Нужна подготовка", "Сначала во вкладке 2 подготовьте overlay и картинку для разметки.")
            return
        AnnotationWindow(self, outdir, self._annotation_saved)

    def _annotation_saved(self, outputs: Dict[str, str]) -> None:
        self.last_annotation_outputs = outputs
        self._log("Разметка сохранена.\n")
        self._log(f"На исходном современном фото: {outputs.get('marked_on_original_modern')}\n")
        self._log(f"Экспорт Roboflow: {outputs.get('roboflow_zip')}\n")

    # ----------------------------- Single straighten --------------------

    def choose_straight_img(self) -> None:
        path = filedialog.askopenfilename(title="Выберите фото фасада", filetypes=IMAGE_TYPES)
        if path:
            self.straight_img.set(path)
            p = Path(path)
            self.straight_out.set(str(p.with_name(p.stem + "_rectified.png")))
            self.straight_points = ""
            self.straight_points_status.set("4 угла фасада не выбраны.")

    def choose_straight_out(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Куда сохранить выпрямленный фасад",
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("Все файлы", "*.*")],
        )
        if path:
            self.straight_out.set(path)

    def pick_straight_corners(self) -> None:
        if not self.straight_img.get():
            messagebox.showinfo("Нужно фото", "Сначала выберите фото фасада.")
            return
        def receive(points: str) -> None:
            self.straight_points = points
            self.straight_points_status.set("Выбрано 4 угла фасада.")
        FacadePointPicker(self, self.straight_img.get(), "4 угла фасада", receive)

    def run_straighten_manual(self) -> None:
        if not self.straight_img.get():
            messagebox.showinfo("Нужно фото", "Сначала выберите фото фасада.")
            return
        if not self.straight_points:
            messagebox.showinfo("Нужны 4 угла", "Нажмите “Указать 4 угла фасада” и поставьте точки.")
            return
        if cv is None:
            messagebox.showerror("OpenCV", "Нужен OpenCV (install_windows.bat).")
            return
        try:
            pts = parse_four_points(self.straight_points)
            ok, msg = validate_facade_quad_points(pts)
            if not ok:
                messagebox.showwarning("Проверьте углы", msg)
                return
            img = cv_read(self.straight_img.get())
            out_w, out_h = facade_output_size(pts, pts)
            rect, _ = warp_facade_to_rect(img, pts, out_w, out_h)
            rect, _, _ = crop_white_margins_pair(rect, rect)
            out_path = Path(self.straight_out.get())
            out_path.parent.mkdir(parents=True, exist_ok=True)
            cv_write(out_path, rect)
            self._log(f"\nВыпрямлено по 4 углам → {out_path} ({rect.shape[1]}×{rect.shape[0]} px)\n")
            messagebox.showinfo("Готово", f"Сохранено:\n{out_path}")
            open_path(out_path.parent)
        except Exception as exc:
            messagebox.showerror("Ошибка выпрямления", str(exc))
            self._log(f"Ошибка выпрямления: {exc}\n")


# ---------------------------------------------------------------------------
# v11 embedded workflow: comparison and markup inside tabs, no extra windows
# ---------------------------------------------------------------------------

class AppV11(App):
    """v11 interface: embedded comparison viewer, embedded markup canvas, user result tab."""

    def _build_ui(self) -> None:
        self.compare_mode = tk.StringVar(value="overlay")
        self.markup_background_mode = tk.StringVar(value="overlay")
        self.modern_saturation = tk.IntVar(value=38)
        self.modern_brightness = tk.IntVar(value=86)
        self.old_contrast = tk.IntVar(value=145)
        self.old_brightness = tk.IntVar(value=108)
        self.old_sharpness = tk.IntVar(value=110)
        self.compare_split = tk.IntVar(value=50)
        self.markup_class = tk.StringVar(value="added_floor")
        self.markup_comment = tk.StringVar(value="")
        self.markup_status = tk.StringVar(value="Разметка ещё не начата.")
        self.result_status = tk.StringVar(value="Пользовательский результат ещё не создан.")
        self.embedded_annotations: List[dict] = []
        self.current_markup_points: List[Point] = []
        self._annotation_loaded_for: Optional[str] = None
        self._rectified_images_cache = None
        self._rectified_cache_key: Optional[Tuple[str, str, float, float]] = None
        self._compare_photo_ref = None
        self._markup_photo_ref = None
        self._result_photo_ref = None
        self.compare_display = (1.0, 0, 0, 0, 0)
        self.markup_display = (1.0, 0, 0, 0, 0)
        self.result_display = (1.0, 0, 0, 0, 0)

        title = ttk.Label(
            self,
            text="Archiview CV v11: источники → выпрямление → встроенное сравнение → разметка → результат для пользователя",
            font=("TkDefaultFont", 12, "bold"),
        )
        title.pack(anchor="w", padx=12, pady=(10, 4))

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=6)
        self.tab_select = ttk.Frame(self.notebook)
        self.tab_rectify = ttk.Frame(self.notebook)
        self.tab_compare = ttk.Frame(self.notebook)
        self.tab_markup = ttk.Frame(self.notebook)
        self.tab_result = ttk.Frame(self.notebook)
        self.tab_straight = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_select, text="1. Источники")
        self.notebook.add(self.tab_rectify, text="2. Выпрямление")
        self.notebook.add(self.tab_compare, text="3. Сравнение")
        self.notebook.add(self.tab_markup, text="4. Разметка")
        self.notebook.add(self.tab_result, text="5. Результат")
        self.notebook.add(self.tab_straight, text="6. Отдельно выпрямить фасад")
        self._build_select_tab(self.tab_select)
        self._build_rectify_tab(self.tab_rectify)
        self._build_compare_tab(self.tab_compare)
        self._build_markup_tab(self.tab_markup)
        self._build_result_tab(self.tab_result)
        self._build_straight_tab(self.tab_straight)
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        log_frame = ttk.LabelFrame(self, text="Сообщения программы")
        log_frame.pack(fill="x", padx=12, pady=(0, 10))
        self.log = tk.Text(log_frame, height=7, wrap="word")
        self.log.pack(fill="x", expand=False, padx=8, pady=8)
        self._log("Готово. Начните с вкладки 1: выберите историческое и современное фото.\n")

    # ---------------- v11 comparison tab ----------------

    def _build_compare_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=0)
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(0, weight=1)

        controls = ttk.LabelFrame(parent, text="Настроить вид сравнения")
        controls.grid(row=0, column=0, sticky="ns", padx=(8, 6), pady=8)
        controls.columnconfigure(0, weight=1)
        ttk.Label(
            controls,
            text=(
                "Здесь overlay и до/после встроены прямо во вкладку. "
                "Настроенный вид автоматически становится фоном для разметки во вкладке 4."
            ),
            wraplength=280,
            foreground="#555",
        ).grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 8))

        mode_box = ttk.LabelFrame(controls, text="Режим просмотра")
        mode_box.grid(row=1, column=0, sticky="ew", padx=10, pady=6)
        for value, label in (("overlay", "Overlay"), ("before_after", "До / после"), ("modern", "Только современное"), ("historical", "Только историческое")):
            ttk.Radiobutton(mode_box, text=label, value=value, variable=self.compare_mode, command=self._refresh_compare_canvas).pack(anchor="w", padx=8, pady=2)

        sliders = ttk.LabelFrame(controls, text="Видимость и читаемость")
        sliders.grid(row=2, column=0, sticky="ew", padx=10, pady=6)
        self._v11_scale(sliders, "Видимость старого", self.old_opacity, 0, 100, self._compare_slider_changed)
        self._v11_scale(sliders, "Насыщенность современного", self.modern_saturation, 0, 100, self._compare_slider_changed)
        self._v11_scale(sliders, "Яркость современного", self.modern_brightness, 35, 130, self._compare_slider_changed)
        self._v11_scale(sliders, "Контраст исторического", self.old_contrast, 80, 240, self._compare_slider_changed)
        self._v11_scale(sliders, "Яркость исторического", self.old_brightness, 70, 150, self._compare_slider_changed)
        self._v11_scale(sliders, "Резкость исторического", self.old_sharpness, 50, 220, self._compare_slider_changed)
        self._v11_scale(sliders, "Граница до/после", self.compare_split, 0, 100, self._compare_slider_changed)

        quick = ttk.LabelFrame(controls, text="Пресеты")
        quick.grid(row=3, column=0, sticky="ew", padx=10, pady=6)
        ttk.Button(quick, text="Для анализа", command=self._preset_analysis).pack(fill="x", padx=8, pady=3)
        ttk.Button(quick, text="Больше видно старое", command=self._preset_old_stronger).pack(fill="x", padx=8, pady=3)
        ttk.Button(quick, text="Мягкое наложение", command=self._preset_soft).pack(fill="x", padx=8, pady=3)

        actions = ttk.LabelFrame(controls, text="Действия")
        actions.grid(row=4, column=0, sticky="ew", padx=10, pady=6)
        ttk.Button(actions, text="Обновить просмотр", command=self._refresh_compare_canvas).pack(fill="x", padx=8, pady=3)
        ttk.Button(actions, text="Открыть HTML overlay", command=self.open_overlay).pack(fill="x", padx=8, pady=3)
        ttk.Button(actions, text="Открыть HTML до/после", command=self.open_before_after).pack(fill="x", padx=8, pady=3)
        ttk.Button(actions, text="Открыть папку результата", command=lambda: open_path(Path(self.outdir.get()))).pack(fill="x", padx=8, pady=3)

        self.compare_status = tk.StringVar(value="Сначала во вкладке 2 подготовьте выпрямленную пару.")
        ttk.Label(controls, textvariable=self.compare_status, wraplength=280, foreground="#555").grid(row=5, column=0, sticky="ew", padx=10, pady=(8, 10))

        view = ttk.LabelFrame(parent, text="Встроенный просмотр")
        view.grid(row=0, column=1, sticky="nsew", padx=(6, 8), pady=8)
        view.rowconfigure(0, weight=1)
        view.columnconfigure(0, weight=1)
        self.compare_canvas = tk.Canvas(view, bg="#2e2e2e", highlightthickness=0)
        self.compare_canvas.grid(row=0, column=0, sticky="nsew")
        self.compare_canvas.bind("<Configure>", lambda _e: self._refresh_compare_canvas(save=False))
        self.compare_canvas.bind("<Button-1>", self._compare_canvas_drag_split)
        self.compare_canvas.bind("<B1-Motion>", self._compare_canvas_drag_split)

    def _v11_scale(self, parent: ttk.Frame, label: str, var: tk.IntVar, start: int, end: int, command: Callable[[object], None]) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x", padx=8, pady=2)
        ttk.Label(row, text=label).pack(anchor="w")
        tk.Scale(row, from_=start, to=end, orient="horizontal", variable=var, command=command, showvalue=True, length=260).pack(fill="x")

    def _preset_analysis(self) -> None:
        self.old_opacity.set(68)
        self.modern_saturation.set(38)
        self.modern_brightness.set(86)
        self.old_contrast.set(145)
        self.old_brightness.set(108)
        self.old_sharpness.set(115)
        self.compare_split.set(50)
        self._compare_slider_changed(None)

    def _preset_old_stronger(self) -> None:
        self.old_opacity.set(78)
        self.modern_saturation.set(25)
        self.modern_brightness.set(76)
        self.old_contrast.set(165)
        self.old_brightness.set(112)
        self.old_sharpness.set(130)
        self._compare_slider_changed(None)

    def _preset_soft(self) -> None:
        self.old_opacity.set(55)
        self.modern_saturation.set(55)
        self.modern_brightness.set(95)
        self.old_contrast.set(125)
        self.old_brightness.set(104)
        self.old_sharpness.set(100)
        self._compare_slider_changed(None)

    def _compare_slider_changed(self, _value: object = None) -> None:
        self._update_opacity_label(None)
        self._refresh_compare_canvas(save=True)
        if hasattr(self, "markup_canvas"):
            self._refresh_markup_canvas()

    def _compare_canvas_drag_split(self, event: tk.Event) -> None:
        if self.compare_mode.get() != "before_after":
            return
        scale, ox, oy, iw, ih = self.compare_display
        if iw <= 0:
            return
        pct = int(round((event.x - ox) / max(1, iw) * 100))
        self.compare_split.set(max(0, min(100, pct)))
        self._compare_slider_changed(None)

    # ---------------- v11 markup tab ----------------

    def _build_markup_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=0)
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(0, weight=1)

        tools = ttk.LabelFrame(parent, text="Классы и инструменты разметки")
        tools.grid(row=0, column=0, sticky="ns", padx=(8, 6), pady=8)
        tools.columnconfigure(0, weight=1)
        ttk.Label(
            tools,
            text=(
                "Разметка идёт по выпрямленному холсту. Фон берётся из вкладки 3: "
                "если вы меняете overlay там, здесь он обновляется автоматически."
            ),
            wraplength=285,
            foreground="#555",
        ).grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))

        bg_box = ttk.LabelFrame(tools, text="Фон для рисования")
        bg_box.grid(row=1, column=0, sticky="ew", padx=10, pady=6)
        for value, label in (("overlay", "Настроенный overlay"), ("before_after", "До / после"), ("modern", "Только современное"), ("historical", "Только историческое")):
            ttk.Radiobutton(bg_box, text=label, value=value, variable=self.markup_background_mode, command=self._refresh_markup_canvas).pack(anchor="w", padx=8, pady=2)

        class_box = ttk.LabelFrame(tools, text="Что отмечаем")
        class_box.grid(row=2, column=0, sticky="ew", padx=10, pady=6)
        for key, label in CLASS_LABELS.items():
            ttk.Radiobutton(class_box, text=label, value=key, variable=self.markup_class).pack(anchor="w", padx=8, pady=1)

        comment_box = ttk.LabelFrame(tools, text="Комментарий к области")
        comment_box.grid(row=3, column=0, sticky="ew", padx=10, pady=6)
        ttk.Entry(comment_box, textvariable=self.markup_comment).pack(fill="x", padx=8, pady=8)

        action_box = ttk.LabelFrame(tools, text="Действия")
        action_box.grid(row=4, column=0, sticky="ew", padx=10, pady=6)
        ttk.Button(action_box, text="Закончить область", command=self._finish_markup_polygon).pack(fill="x", padx=8, pady=3)
        ttk.Button(action_box, text="Отменить точку", command=self._undo_markup_point).pack(fill="x", padx=8, pady=3)
        ttk.Button(action_box, text="Удалить последнюю область", command=self._undo_markup_polygon).pack(fill="x", padx=8, pady=3)
        ttk.Button(action_box, text="Очистить всё", command=self._clear_markup_all).pack(fill="x", padx=8, pady=3)
        ttk.Button(action_box, text="Сохранить и показать на фасаде", command=self._save_markup_annotations).pack(fill="x", padx=8, pady=(9, 3))
        ttk.Button(action_box, text="Открыть папку результата", command=lambda: open_path(Path(self.outdir.get()))).pack(fill="x", padx=8, pady=3)

        ttk.Label(tools, textvariable=self.markup_status, wraplength=285, foreground="#555").grid(row=5, column=0, sticky="ew", padx=10, pady=(8, 10))

        view = ttk.LabelFrame(parent, text="Рисуйте прямо здесь: левый клик — точка, Enter/двойной клик — закончить область")
        view.grid(row=0, column=1, sticky="nsew", padx=(6, 8), pady=8)
        view.rowconfigure(0, weight=1)
        view.columnconfigure(0, weight=1)
        self.markup_canvas = tk.Canvas(view, bg="#2e2e2e", highlightthickness=0)
        self.markup_canvas.grid(row=0, column=0, sticky="nsew")
        self.markup_canvas.bind("<Configure>", lambda _e: self._refresh_markup_canvas())
        self.markup_canvas.bind("<Button-1>", self._markup_click)
        self.markup_canvas.bind("<Double-Button-1>", lambda _e: self._finish_markup_polygon())
        self.bind("<Return>", lambda _e: self._finish_markup_polygon())
        self.bind("<BackSpace>", lambda _e: self._undo_markup_point())
        self.bind("<Delete>", lambda _e: self._undo_markup_polygon())

    # ---------------- v11 result tab ----------------

    def _build_result_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=0)
        parent.rowconfigure(0, weight=1)
        view = ttk.LabelFrame(parent, text="Итог для пользователя: современный фасад с отмеченными изменениями")
        view.grid(row=0, column=0, sticky="nsew", padx=(8, 6), pady=8)
        view.rowconfigure(0, weight=1)
        view.columnconfigure(0, weight=1)
        self.result_canvas = tk.Canvas(view, bg="#2e2e2e", highlightthickness=0)
        self.result_canvas.grid(row=0, column=0, sticky="nsew")
        self.result_canvas.bind("<Configure>", lambda _e: self._refresh_result_canvas())

        side = ttk.LabelFrame(parent, text="Легенда и действия")
        side.grid(row=0, column=1, sticky="ns", padx=(6, 8), pady=8)
        ttk.Label(
            side,
            text=(
                "Эта вкладка — не для разметчика, а для показа результата: "
                "что изменилось и на каком месте современного фасада."
            ),
            wraplength=280,
            foreground="#555",
        ).pack(anchor="w", padx=10, pady=(10, 8))
        self.result_legend = tk.Text(side, width=38, height=20, wrap="word")
        self.result_legend.pack(fill="both", expand=True, padx=10, pady=6)
        self.result_legend.configure(state="disabled")
        ttk.Label(side, textvariable=self.result_status, wraplength=280, foreground="#555").pack(anchor="w", padx=10, pady=6)
        ttk.Button(side, text="Обновить результат", command=self._refresh_result_canvas).pack(fill="x", padx=10, pady=3)
        ttk.Button(side, text="Открыть итоговую картинку", command=self.open_marked_original).pack(fill="x", padx=10, pady=3)
        ttk.Button(side, text="Открыть HTML overlay", command=self.open_overlay).pack(fill="x", padx=10, pady=3)
        ttk.Button(side, text="Открыть HTML до/после", command=self.open_before_after).pack(fill="x", padx=10, pady=3)
        ttk.Button(side, text="Открыть Roboflow export", command=self.open_roboflow_export).pack(fill="x", padx=10, pady=3)
        ttk.Button(
            side,
            text="Отправить на сайт (GitHub)…",
            command=self.export_to_website,
        ).pack(fill="x", padx=10, pady=(8, 3))

    # ---------------- image composition and display ----------------

    def _load_rectified_images(self):
        if Image is None:
            raise RuntimeError("Pillow не установлен. Запустите install_windows.bat.")
        old_path = Path(self.outdir.get()) / "03_historical_rectified.png"
        new_path = Path(self.outdir.get()) / "04_modern_rectified.png"
        if not old_path.exists() or not new_path.exists():
            raise RuntimeError("Сначала во вкладке 2 подготовьте выпрямленную пару.")
        key = (str(old_path), str(new_path), old_path.stat().st_mtime, new_path.stat().st_mtime)
        if self._rectified_cache_key == key and self._rectified_images_cache is not None:
            return self._rectified_images_cache
        old = Image.open(old_path).convert("RGB")  # type: ignore[union-attr]
        new = Image.open(new_path).convert("RGB")  # type: ignore[union-attr]
        if new.size != old.size:
            new = new.resize(old.size)
        self._rectified_images_cache = (old, new)
        self._rectified_cache_key = key
        return old, new

    def _prepared_old_pil(self, old):
        img = ImageOps.grayscale(old) if ImageOps is not None else old.convert("L")
        if ImageOps is not None:
            img = ImageOps.autocontrast(img)
        img = img.convert("RGB")
        if ImageEnhance is not None:
            img = ImageEnhance.Contrast(img).enhance(self.old_contrast.get() / 100.0)
            img = ImageEnhance.Brightness(img).enhance(self.old_brightness.get() / 100.0)
            img = ImageEnhance.Sharpness(img).enhance(self.old_sharpness.get() / 100.0)
        return img.convert("RGB")

    def _prepared_modern_pil(self, modern):
        img = modern.copy().convert("RGB")
        if ImageEnhance is not None:
            img = ImageEnhance.Color(img).enhance(self.modern_saturation.get() / 100.0)
            img = ImageEnhance.Brightness(img).enhance(self.modern_brightness.get() / 100.0)
            img = ImageEnhance.Contrast(img).enhance(0.96)
        return img.convert("RGB")

    def _compose_current_view(self, mode: Optional[str] = None):
        old, modern = self._load_rectified_images()
        old_p = self._prepared_old_pil(old)
        modern_p = self._prepared_modern_pil(modern)
        view_mode = mode or self.compare_mode.get()
        if view_mode == "historical":
            return old_p
        if view_mode == "modern":
            return modern_p
        if view_mode == "before_after":
            w, h = old_p.size
            x = int(round(w * self.compare_split.get() / 100.0))
            out = old_p.copy()
            out.paste(modern_p.crop((x, 0, w, h)), (x, 0))
            return out
        return Image.blend(modern_p, old_p, max(0, min(100, int(self.old_opacity.get()))) / 100.0)

    def _show_pil_on_canvas(self, canvas: tk.Canvas, img, photo_attr: str, display_attr: str) -> None:
        cw = max(10, canvas.winfo_width())
        ch = max(10, canvas.winfo_height())
        scale = min(cw / img.width, ch / img.height, 1.0)
        dw = max(1, int(round(img.width * scale)))
        dh = max(1, int(round(img.height * scale)))
        disp = img.resize((dw, dh)) if scale < 1.0 else img
        photo = ImageTk.PhotoImage(disp)  # type: ignore[union-attr]
        setattr(self, photo_attr, photo)
        ox = int((cw - dw) / 2)
        oy = int((ch - dh) / 2)
        setattr(self, display_attr, (scale, ox, oy, dw, dh))
        canvas.delete("all")
        canvas.create_image(ox, oy, image=photo, anchor="nw")

    def _draw_canvas_message(self, canvas: tk.Canvas, text: str) -> None:
        canvas.delete("all")
        canvas.create_text(20, 20, anchor="nw", fill="white", width=max(300, canvas.winfo_width() - 40), text=text)

    def _refresh_compare_canvas(self, save: bool = True) -> None:
        if not hasattr(self, "compare_canvas"):
            return
        try:
            img = self._compose_current_view()
            self._show_pil_on_canvas(self.compare_canvas, img, "_compare_photo_ref", "compare_display")
            if self.compare_mode.get() == "before_after":
                scale, ox, oy, dw, dh = self.compare_display
                x = ox + int(dw * self.compare_split.get() / 100.0)
                self.compare_canvas.create_line(x, oy, x, oy + dh, fill="#ffffff", width=2)
            if save:
                self._save_current_labeling_image(mode=self.compare_mode.get())
            self.compare_status.set("Вид сравнения готов. Этот же вид автоматически используется во вкладке 4 для разметки.")
        except Exception as exc:
            self.compare_status.set(str(exc))
            self._draw_canvas_message(self.compare_canvas, str(exc))

    def _save_current_labeling_image(self, mode: Optional[str] = None) -> None:
        try:
            img = self._compose_current_view(mode=mode or self.compare_mode.get())
            out = Path(self.outdir.get()) / "05_comparison_for_labeling.png"
            out.parent.mkdir(parents=True, exist_ok=True)
            img.save(out)
        except Exception:
            # Do not interrupt slider movement with message boxes.
            pass

    # ---------------- markup methods ----------------

    def _reload_markup_from_disk(self) -> None:
        """Разметка на экране = файл на диске (если нет несохранённых правок)."""
        if getattr(self, "_markup_dirty", False):
            return
        self._annotation_loaded_for = None
        self.current_markup_points = []
        self._ensure_annotations_loaded()
        self._refresh_markup_canvas()

    def _ensure_annotations_loaded(self) -> None:
        outdir = str(Path(self.outdir.get()).resolve())
        if self._annotation_loaded_for == outdir:
            return
        self.embedded_annotations = []
        self.current_markup_points = []
        path = Path(outdir) / "annotations" / "manual_annotations.json"
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                anns = data.get("annotations", [])
                if isinstance(anns, list):
                    self.embedded_annotations = normalize_annotation_list(anns)
                    if len(self.embedded_annotations) < len(anns):
                        self._log(
                            f"Разметка: убрано {len(anns) - len(self.embedded_annotations)} дубликатов в {path.name}\n"
                        )
            except Exception:
                self.embedded_annotations = []
        self._annotation_loaded_for = outdir

    def _refresh_markup_canvas(self) -> None:
        if not hasattr(self, "markup_canvas"):
            return
        self._ensure_annotations_loaded()
        try:
            mode = self.markup_background_mode.get()
            if mode == "overlay":
                img = self._compose_current_view(mode="overlay")
            elif mode == "before_after":
                img = self._compose_current_view(mode="before_after")
            elif mode == "modern":
                img = self._compose_current_view(mode="modern")
            else:
                img = self._compose_current_view(mode="historical")
            self._show_pil_on_canvas(self.markup_canvas, img, "_markup_photo_ref", "markup_display")
            self._draw_markup_vectors()
            self.markup_status.set(f"Областей: {len(self.embedded_annotations)}. Точек в текущей области: {len(self.current_markup_points)}.")
        except Exception as exc:
            self.markup_status.set(str(exc))
            self._draw_canvas_message(self.markup_canvas, str(exc))

    def _draw_markup_vectors(self) -> None:
        if not hasattr(self, "markup_canvas"):
            return
        scale, ox, oy, dw, dh = self.markup_display
        def to_disp(pt: Point) -> Point:
            return (ox + pt[0] * scale, oy + pt[1] * scale)
        for idx, ann in enumerate(self.embedded_annotations, start=1):
            pts = ann.get("polygon", [])
            if len(pts) < 3:
                continue
            cls = ann.get("class", "added_floor")
            color = TK_COLORS.get(cls, "#00aa00")
            flat: List[float] = []
            for p in pts:
                x, y = to_disp((float(p[0]), float(p[1])))
                flat.extend([x, y])
            self.markup_canvas.create_polygon(flat, outline=color, fill="", width=3)
            xs = flat[0::2]
            ys = flat[1::2]
            self.markup_canvas.create_text(sum(xs) / len(xs), sum(ys) / len(ys), text=str(idx), fill=color, font=("TkDefaultFont", 14, "bold"))
        if self.current_markup_points:
            color = TK_COLORS.get(self.markup_class.get(), "#00aa00")
            disp = [to_disp(p) for p in self.current_markup_points]
            for i, (x, y) in enumerate(disp, start=1):
                r = 5
                self.markup_canvas.create_oval(x - r, y - r, x + r, y + r, fill=color, outline="white", width=2)
                self.markup_canvas.create_text(x + 8, y - 8, text=str(i), fill=color, font=("TkDefaultFont", 9, "bold"))
            if len(disp) >= 2:
                flat = [v for xy in disp for v in xy]
                self.markup_canvas.create_line(flat, fill=color, width=2)

    def _markup_click(self, event: tk.Event) -> None:
        scale, ox, oy, dw, dh = self.markup_display
        if dw <= 0 or dh <= 0:
            return
        x = (event.x - ox) / max(scale, 1e-9)
        y = (event.y - oy) / max(scale, 1e-9)
        if x < 0 or y < 0 or x > dw / max(scale, 1e-9) or y > dh / max(scale, 1e-9):
            return
        self.current_markup_points.append((float(x), float(y)))
        self._refresh_markup_canvas()

    def _finish_markup_polygon(self) -> None:
        if not hasattr(self, "markup_canvas"):
            return
        if len(self.current_markup_points) < 3:
            return
        cls = self.markup_class.get()
        self.embedded_annotations.append({
            "id": len(self.embedded_annotations) + 1,
            "class": cls,
            "label_ru": CLASS_LABELS.get(cls, cls),
            "comment": self.markup_comment.get().strip(),
            "polygon": [[float(x), float(y)] for x, y in self.current_markup_points],
        })
        self.markup_comment.set("")
        self.current_markup_points = []
        self._refresh_markup_canvas()

    def _undo_markup_point(self) -> None:
        if self.current_markup_points:
            self.current_markup_points.pop()
        self._refresh_markup_canvas()

    def _undo_markup_polygon(self) -> None:
        if self.embedded_annotations:
            self.embedded_annotations.pop()
        self._refresh_markup_canvas()

    def _clear_markup_all(self) -> None:
        if not self.embedded_annotations and not self.current_markup_points:
            return
        if messagebox.askyesno("Очистить разметку", "Удалить все области разметки на этом проекте?"):
            self.embedded_annotations = []
            self.current_markup_points = []
            self._refresh_markup_canvas()

    def _save_markup_annotations(self) -> None:
        if len(self.current_markup_points) >= 3:
            self._finish_markup_polygon()
        if not self.embedded_annotations:
            messagebox.showinfo("Разметки нет", "Сначала обведите хотя бы одну область.")
            return
        try:
            self.embedded_annotations = normalize_annotation_list(self.embedded_annotations)
            self._save_current_labeling_image(mode=self.markup_background_mode.get())
            outputs = save_annotations_and_exports(Path(self.outdir.get()), self.embedded_annotations)
            self._annotation_saved(outputs)
            self._annotation_loaded_for = None
            if hasattr(self, "_clear_dirty"):
                self._clear_dirty()
            self._refresh_result_canvas()
            if hasattr(self, "notebook"):
                self.notebook.select(self.tab_result)
            messagebox.showinfo("Готово", "Разметка сохранена и перенесена на исходное современное фото.")
            if hasattr(self, "_maybe_auto_export_to_website"):
                self._maybe_auto_export_to_website()
        except Exception as exc:
            messagebox.showerror("Не удалось сохранить разметку", str(exc))

    def _maybe_auto_export_to_website(self) -> None:
        if not getattr(self, "auto_export_website", None) or not self.auto_export_website.get():
            return
        out = Path(self.outdir.get())
        has_export = (
            (out / "04_modern_rectified.png").exists()
            or (out / "07_marked_on_original_modern.png").exists()
            or (out / "08_marked_on_original_modern_labeled.png").exists()
            or (out / "annotations" / "manual_annotations.json").exists()
        )
        if not has_export:
            return
        self._sync_export_to_website(quiet=True, show_dialog=False)

    def _update_result_house_header(self) -> None:
        if not hasattr(self, "result_house_header"):
            return
        parts: List[str] = []
        name = self.object_name.get().strip()
        code = self.site_card_id.get().strip().upper()
        addr = self.address.get().strip()
        folder = Path(self.project_dir.get()).name if self.project_dir.get() else ""
        if name:
            parts.append(name)
        if code:
            parts.append(code)
        if addr:
            parts.append(addr)
        line1 = " · ".join(parts) if parts else "Дом не указан"
        hint = self._result_workdir_hint() if hasattr(self, "_result_workdir_hint") else ""
        if folder:
            line1 = f"{line1}\nПапка: {folder}" + (f" | {hint}" if hint else "")
        elif hint:
            line1 = f"{line1}\n{hint}"
        self.result_house_header.configure(text=line1)

    # ---------------- result methods ----------------

    def _refresh_result_canvas(self) -> None:
        if not hasattr(self, "result_canvas"):
            return
        self._update_result_house_header()
        path = Path(self.outdir.get()) / "07_marked_on_original_modern.png"
        if not path.exists():
            self.result_status.set("После сохранения разметки здесь появится итоговая картинка.")
            self._draw_canvas_message(self.result_canvas, "Пока нет итоговой картинки.\n\nВо вкладке 4 обведите изменения и нажмите “Сохранить и показать на фасаде”.")
            self._update_result_legend()
            return
        try:
            if Image is None:
                raise RuntimeError("Pillow не установлен.")
            img = Image.open(path).convert("RGB")  # type: ignore[union-attr]
            self._show_pil_on_canvas(self.result_canvas, img, "_result_photo_ref", "result_display")
            self.result_status.set(f"Итоговая картинка готова: {path}")
            self._update_result_legend()
        except Exception as exc:
            self.result_status.set(str(exc))
            self._draw_canvas_message(self.result_canvas, str(exc))

    def _update_result_legend(self) -> None:
        if not hasattr(self, "result_legend"):
            return
        self._ensure_annotations_loaded()
        counts: Dict[str, int] = {}
        for ann in self.embedded_annotations:
            cls = ann.get("class", "other_artifact")
            counts[cls] = counts.get(cls, 0) + 1
        lines = ["Легенда:\n"]
        if not counts:
            lines.append("Разметки пока нет.\n")
        else:
            for key, count in counts.items():
                lines.append(f"{count} × {CLASS_LABELS.get(key, key)}\n")
        lines.append("\nФайлы:\n")
        lines.append("07_marked_on_original_modern.png — результат на современном фасаде\n")
        lines.append("06_marked_rectified.png — разметка на выпрямленном фасаде\n")
        lines.append("roboflow_export.zip — датасет для Roboflow\n")
        self.result_legend.configure(state="normal")
        self.result_legend.delete("1.0", "end")
        self.result_legend.insert("1.0", "".join(lines))
        self.result_legend.configure(state="disabled")

    # ---------------- v11 hooks/overrides ----------------

    def _update_opacity_label(self, _value: object = None) -> None:
        self.old_opacity_label.set(f"Видимость старого фото в overlay: {int(self.old_opacity.get())}%")
        if hasattr(self, "compare_canvas"):
            self._refresh_compare_canvas(save=False)

    def start_prepare_project(self) -> None:
        if not self.historical_img.get() or not self.modern_img.get():
            messagebox.showinfo("Нужны два фото", "Во вкладке 1 выберите историческое и современное фото.")
            return
        if not self.old_points_text or not self.modern_points_text:
            messagebox.showinfo("Нужны точки", "Во вкладке 2 нажмите “Указать 4 угла на двух фото одновременно”.")
            return
        self._ensure_work_session_for_active_pair()
        self._persist_house_metadata()
        outdir = Path(self.outdir.get())
        pastvu_meta = asdict(self.selected_pastvu) if self.selected_pastvu else {}

        active = self._get_active_historical_item()
        old_crop = (active.crop_rect_text if active else "") or ""
        def work() -> object:
            return prepare_rectified_project(
                Path(self.historical_img.get()),
                Path(self.modern_img.get()),
                self.old_points_text,
                self.modern_points_text,
                outdir,
                old_opacity_percent=int(self.old_opacity.get()),
                pastvu_meta=pastvu_meta,
                modern_meta=self.modern_meta,
                keep_context=bool(self.keep_context.get()),
                old_crop_rect_text=old_crop,
                modern_crop_rect_text=self.modern_crop_rect_text,
            )

        def done(_result: object) -> None:
            self._rectified_images_cache = None
            self._rectified_cache_key = None
            self.rectified_status.set(f"Готово. Выпрямленная пара и overlay сохранены: {outdir}")
            self._log(f"Готово. Результаты сохранены в: {outdir}\n")
            self._refresh_compare_canvas(save=True)
            self._refresh_markup_canvas()
            self._refresh_workflow_steps()
            if hasattr(self, "notebook"):
                self.notebook.select(self.tab_compare)
            messagebox.showinfo(
                "Готово",
                "Выпрямленная пара создана. Теперь во вкладке 3 настройте overlay/до-после прямо внутри программы.",
            )

        self._run_bg("Подготовка выпрямленной пары", work, done)

    def open_in_app_preview(self) -> None:
        if hasattr(self, "notebook"):
            self.notebook.select(self.tab_compare)
            self._refresh_compare_canvas()

    def open_annotation_window(self) -> None:
        if hasattr(self, "notebook"):
            self.notebook.select(self.tab_markup)
            self._refresh_markup_canvas()

    def _on_tab_changed(self, _event: tk.Event) -> None:
        try:
            current = self.notebook.select()
            if current == str(self.tab_compare):
                self._refresh_compare_canvas(save=False)
            elif current == str(self.tab_markup):
                # When the user moves from “Сравнение” to “Разметка”, start with the same visual mode.
                self.markup_background_mode.set(self.compare_mode.get())
                self._save_current_labeling_image(mode=self.markup_background_mode.get())
                self._refresh_markup_canvas()
            elif current == str(self.tab_result):
                self._refresh_result_canvas()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# v12: faster embedded viewer + readable result labels/comments
# ---------------------------------------------------------------------------

class AppV12(AppV11):
    """v12 interface: throttled previews, display-sized rendering, labels in result tab."""

    def _build_ui(self) -> None:
        self._compare_refresh_job = None
        self._markup_refresh_job = None
        self._result_refresh_job = None
        self._preview_base_cache: Dict[Tuple[object, int, int], Tuple[object, object]] = {}
        super()._build_ui()
        # The v11 canvas bindings refreshed immediately on every resize event. On Windows
        # this can fire dozens of times and makes the program feel frozen, so v12 throttles them.
        if hasattr(self, "compare_canvas"):
            self.compare_canvas.bind("<Configure>", lambda _e: self._schedule_compare_refresh(save=False, delay=120))
        if hasattr(self, "markup_canvas"):
            self.markup_canvas.bind("<Configure>", lambda _e: self._schedule_markup_refresh(delay=120))
        if hasattr(self, "result_canvas"):
            self.result_canvas.bind("<Configure>", lambda _e: self._schedule_result_refresh(delay=120))
        self._log("v12: ускоренный встроенный просмотр включён. Полноразмерное сохранение выполняется только при сохранении разметки.\n")

    # ---------------- throttling helpers ----------------

    def _schedule_compare_refresh(self, save: bool = False, delay: int = 120) -> None:
        if self._compare_refresh_job is not None:
            try:
                self.after_cancel(self._compare_refresh_job)
            except Exception:
                pass
        self._compare_refresh_job = self.after(delay, lambda: self._run_scheduled_compare_refresh(save=save))

    def _run_scheduled_compare_refresh(self, save: bool = False) -> None:
        self._compare_refresh_job = None
        self._refresh_compare_canvas(save=save)

    def _schedule_markup_refresh(self, delay: int = 120) -> None:
        if self._markup_refresh_job is not None:
            try:
                self.after_cancel(self._markup_refresh_job)
            except Exception:
                pass
        self._markup_refresh_job = self.after(delay, self._run_scheduled_markup_refresh)

    def _run_scheduled_markup_refresh(self) -> None:
        self._markup_refresh_job = None
        self._refresh_markup_canvas()

    def _schedule_result_refresh(self, delay: int = 120) -> None:
        if self._result_refresh_job is not None:
            try:
                self.after_cancel(self._result_refresh_job)
            except Exception:
                pass
        self._result_refresh_job = self.after(delay, self._run_scheduled_result_refresh)

    def _run_scheduled_result_refresh(self) -> None:
        self._result_refresh_job = None
        self._refresh_result_canvas()

    def _update_opacity_label(self, _value: object = None) -> None:
        # v11 refreshed the preview here, and _compare_slider_changed refreshed it again.
        # v12 updates only text here; drawing is debounced in _compare_slider_changed.
        self.old_opacity_label.set(f"Видимость старого фото в overlay: {int(self.old_opacity.get())}%")

    def _compare_slider_changed(self, _value: object = None) -> None:
        self._update_opacity_label(None)
        self.compare_status.set("Настройки изменены. Обновляю встроенный просмотр…")
        self._schedule_compare_refresh(save=False, delay=90)

    def _compare_canvas_drag_split(self, event: tk.Event) -> None:
        if self.compare_mode.get() != "before_after":
            return
        scale, ox, oy, iw, ih = self.compare_display
        if iw <= 0:
            return
        pct = int(round((event.x - ox) / max(1, iw) * 100.0))
        pct = max(0, min(100, pct))
        self.compare_split.set(pct)
        self._schedule_compare_refresh(save=False, delay=30)

    # ---------------- fast display-sized preview composition ----------------

    def _resize_filter_fast(self):
        if Image is None:
            return None
        return getattr(getattr(Image, "Resampling", Image), "BILINEAR", 2)

    def _load_preview_base_images(self, canvas: tk.Canvas) -> Tuple[object, object, float, int, int, int, int]:
        if Image is None:
            raise RuntimeError("Pillow не установлен.")
        old, modern = self._load_rectified_images()
        cw = max(10, canvas.winfo_width())
        ch = max(10, canvas.winfo_height())
        # During initial layout Tk sometimes reports a tiny canvas; use a sane preview box.
        if cw < 80 or ch < 80:
            cw, ch = 1100, 760
        scale = min(cw / old.width, ch / old.height)
        if scale > 1.0:
            scale = min(scale, 2.5)
        dw = max(1, int(round(old.width * scale)))
        dh = max(1, int(round(old.height * scale)))
        ox = int((cw - dw) / 2)
        oy = int((ch - dh) / 2)
        key = (self._rectified_cache_key, dw, dh)
        cached = self._preview_base_cache.get(key)
        if cached is not None:
            old_small, modern_small = cached
        else:
            filt = self._resize_filter_fast()
            old_small = old.resize((dw, dh), filt) if old.size != (dw, dh) else old.copy()
            modern_small = modern.resize((dw, dh), filt) if modern.size != (dw, dh) else modern.copy()
            # Keep cache small: only the last few sizes matter.
            if len(self._preview_base_cache) > 4:
                self._preview_base_cache.clear()
            self._preview_base_cache[key] = (old_small, modern_small)
        return old_small, modern_small, float(scale), ox, oy, dw, dh

    def _compose_preview_for_canvas(self, canvas: tk.Canvas, mode: Optional[str] = None) -> Tuple[object, Tuple[float, int, int, int, int]]:
        old_small, modern_small, scale, ox, oy, dw, dh = self._load_preview_base_images(canvas)
        old_p = self._prepared_old_pil(old_small)
        modern_p = self._prepared_modern_pil(modern_small)
        view_mode = mode or self.compare_mode.get()
        if view_mode == "historical":
            out = old_p
        elif view_mode == "modern":
            out = modern_p
        elif view_mode == "before_after":
            x = int(round(dw * self.compare_split.get() / 100.0))
            out = old_p.copy()
            out.paste(modern_p.crop((x, 0, dw, dh)), (x, 0))
        else:
            out = Image.blend(modern_p, old_p, max(0, min(100, int(self.old_opacity.get()))) / 100.0)
        return out, (scale, ox, oy, dw, dh)

    def _put_preview_on_canvas(self, canvas: tk.Canvas, img, photo_attr: str, display_attr: str, display: Tuple[float, int, int, int, int]) -> None:
        photo = ImageTk.PhotoImage(img)  # type: ignore[union-attr]
        setattr(self, photo_attr, photo)
        setattr(self, display_attr, display)
        _scale, ox, oy, _dw, _dh = display
        canvas.delete("all")
        canvas.create_image(ox, oy, image=photo, anchor="nw")

    def _refresh_compare_canvas(self, save: bool = False) -> None:
        if not hasattr(self, "compare_canvas"):
            return
        self._refresh_compare_source_thumbnails()
        try:
            img, display = self._compose_preview_for_canvas(self.compare_canvas, self.compare_mode.get())
            self._put_preview_on_canvas(self.compare_canvas, img, "_compare_photo_ref", "compare_display", display)
            if self.compare_mode.get() == "before_after":
                scale, ox, oy, dw, dh = self.compare_display
                x = ox + int(dw * self.compare_split.get() / 100.0)
                self.compare_canvas.create_line(x, oy, x, oy + dh, fill="#ffffff", width=2)
            if save:
                # Full-resolution save is intentionally rare in v12.
                self._save_current_labeling_image(mode=self.compare_mode.get())
            self.compare_status.set("Вид сравнения готов. При переходе в разметку используется такой же фон, но без тяжёлого пересохранения на каждом движении ползунка.")
        except Exception as exc:
            self.compare_status.set(str(exc))
            self._draw_canvas_message(self.compare_canvas, str(exc))

    # ---------------- faster embedded markup ----------------

    def _refresh_markup_canvas(self) -> None:
        if not hasattr(self, "markup_canvas"):
            return
        self._ensure_annotations_loaded()
        try:
            mode = self.markup_background_mode.get()
            if mode not in {"overlay", "before_after", "modern", "historical"}:
                mode = "overlay"
            img, display = self._compose_preview_for_canvas(self.markup_canvas, mode)
            self._put_preview_on_canvas(self.markup_canvas, img, "_markup_photo_ref", "markup_display", display)
            self._draw_markup_vectors()
            self._update_markup_status_text()
        except Exception as exc:
            self.markup_status.set(str(exc))
            self._draw_canvas_message(self.markup_canvas, str(exc))

    def _update_markup_status_text(self) -> None:
        self.markup_status.set(
            f"Областей: {len(self.embedded_annotations)}. "
            f"Точек в текущей области: {len(self.current_markup_points)}."
        )

    def _draw_markup_vectors(self) -> None:
        if not hasattr(self, "markup_canvas"):
            return
        self.markup_canvas.delete("markup_vector")
        scale, ox, oy, dw, dh = self.markup_display

        def to_disp(pt: Point) -> Point:
            return (ox + pt[0] * scale, oy + pt[1] * scale)

        for idx, ann in enumerate(self.embedded_annotations, start=1):
            pts = ann.get("polygon", [])
            if len(pts) < 3:
                continue
            cls = ann.get("class", "added_floor")
            color = TK_COLORS.get(cls, "#00aa00")
            flat: List[float] = []
            for p in pts:
                x, y = to_disp((float(p[0]), float(p[1])))
                flat.extend([x, y])
            self.markup_canvas.create_polygon(flat, outline=color, fill="", width=3, tags="markup_vector")
            xs = flat[0::2]
            ys = flat[1::2]
            cx = sum(xs) / max(1, len(xs))
            cy = sum(ys) / max(1, len(ys))
            self.markup_canvas.create_text(cx, cy, text=str(idx), fill=color, font=("TkDefaultFont", 14, "bold"), tags="markup_vector")

        if self.current_markup_points:
            color = TK_COLORS.get(self.markup_class.get(), "#00aa00")
            disp = [to_disp(p) for p in self.current_markup_points]
            for i, (x, y) in enumerate(disp, start=1):
                r = 5
                self.markup_canvas.create_oval(x - r, y - r, x + r, y + r, fill=color, outline="white", width=2, tags="markup_vector")
                self.markup_canvas.create_text(x + 8, y - 8, text=str(i), fill=color, font=("TkDefaultFont", 9, "bold"), tags="markup_vector")
            if len(disp) >= 2:
                flat = [v for xy in disp for v in xy]
                self.markup_canvas.create_line(flat, fill=color, width=2, tags="markup_vector")

    def _markup_click(self, event: tk.Event) -> None:
        scale, ox, oy, dw, dh = self.markup_display
        if dw <= 0 or dh <= 0:
            return
        x = (event.x - ox) / max(scale, 1e-9)
        y = (event.y - oy) / max(scale, 1e-9)
        if x < 0 or y < 0 or x > dw / max(scale, 1e-9) or y > dh / max(scale, 1e-9):
            return
        self.current_markup_points.append((float(x), float(y)))
        self._draw_markup_vectors()
        self._update_markup_status_text()

    def _finish_markup_polygon(self) -> None:
        if not hasattr(self, "markup_canvas"):
            return
        if len(self.current_markup_points) < 3:
            return
        cls = self.markup_class.get()
        self.embedded_annotations.append({
            "id": len(self.embedded_annotations) + 1,
            "class": cls,
            "label_ru": CLASS_LABELS.get(cls, cls),
            "comment": self.markup_comment.get().strip(),
            "polygon": [[float(x), float(y)] for x, y in self.current_markup_points],
        })
        self.markup_comment.set("")
        self.current_markup_points = []
        self._draw_markup_vectors()
        self._update_markup_status_text()

    def _undo_markup_point(self) -> None:
        if self.current_markup_points:
            self.current_markup_points.pop()
        self._draw_markup_vectors()
        self._update_markup_status_text()

    def _undo_markup_polygon(self) -> None:
        if self.embedded_annotations:
            self.embedded_annotations.pop()
        self._draw_markup_vectors()
        self._update_markup_status_text()

    def _clear_markup_all(self) -> None:
        if not self.embedded_annotations and not self.current_markup_points:
            return
        if messagebox.askyesno("Очистить разметку", "Удалить все области разметки на этом проекте?"):
            self.embedded_annotations = []
            self.current_markup_points = []
            self._draw_markup_vectors()
            self._update_markup_status_text()

    def _save_markup_annotations(self) -> None:
        if len(self.current_markup_points) >= 3:
            self._finish_markup_polygon()
        if not self.embedded_annotations:
            messagebox.showinfo("Разметки нет", "Сначала обведите хотя бы одну область.")
            return
        try:
            # Full-resolution image for Roboflow/export is created once, here.
            self._save_current_labeling_image(mode=self.markup_background_mode.get())
            outputs = save_annotations_and_exports(Path(self.outdir.get()), self.embedded_annotations)
            self._create_labeled_result_file()
            self._annotation_saved(outputs)
            self._refresh_result_canvas()
            if hasattr(self, "notebook"):
                self.notebook.select(self.tab_result)
            messagebox.showinfo("Готово", "Разметка сохранена. Во вкладке результата области подписаны названиями и комментариями.")
        except Exception as exc:
            messagebox.showerror("Не удалось сохранить разметку", str(exc))

    # ---------------- result labels/comments ----------------

    def _project_json_path(self) -> Optional[Path]:
        outdir = Path(self.outdir.get())
        for name in ("project_v8.json", "project_v7.json", "project_v6.json"):
            p = outdir / name
            if p.exists():
                return p
        return None

    def _result_annotations_in_source(self) -> List[dict]:
        self._ensure_annotations_loaded()
        project_path = self._project_json_path()
        H = None
        if project_path is not None:
            try:
                project = json.loads(project_path.read_text(encoding="utf-8"))
                fb = str(getattr(self, "modern_crop_rect_text", "") or "")
                if not fb:
                    fb = modern_crop_rect_from_metadata_near(Path(self.outdir.get()))
                H = H_rect_to_full_modern_from_project(project, fallback_rect_text=fb)
                if H.shape != (3, 3):
                    H = None
            except Exception:
                H = None
        result: List[dict] = []
        for idx, ann in enumerate(self.embedded_annotations, start=1):
            pts = np.asarray(ann.get("polygon", []), dtype=np.float32)
            if pts.shape[0] < 3:
                continue
            if H is not None:
                try:
                    pts2 = cv.perspectiveTransform(pts.reshape(-1, 1, 2), H).reshape(-1, 2)
                except Exception:
                    pts2 = pts
            else:
                pts2 = pts
            item = dict(ann)
            item["_idx"] = idx
            item["_source_polygon"] = pts2.tolist()
            result.append(item)
        return result

    def _refresh_result_canvas(self) -> None:
        if not hasattr(self, "result_canvas"):
            return
        path = Path(self.outdir.get()) / "07_marked_on_original_modern.png"
        if not path.exists():
            self.result_status.set("После сохранения разметки здесь появится итоговая картинка.")
            self._draw_canvas_message(self.result_canvas, "Пока нет итоговой картинки.\n\nВо вкладке 4 обведите изменения и нажмите “Сохранить и показать на фасаде”.")
            self._update_result_legend()
            return
        try:
            if Image is None:
                raise RuntimeError("Pillow не установлен.")
            img = Image.open(path).convert("RGB")  # type: ignore[union-attr]
            self._show_pil_on_canvas(self.result_canvas, img, "_result_photo_ref", "result_display")
            self._draw_result_labels_on_canvas()
            labeled = Path(self.outdir.get()) / "08_marked_on_original_modern_labeled.png"
            extra = f"\nФайл с подписями: {labeled}" if labeled.exists() else ""
            self.result_status.set(f"Итоговая картинка готова: {path}{extra}")
            self._update_result_legend()
        except Exception as exc:
            self.result_status.set(str(exc))
            self._draw_canvas_message(self.result_canvas, str(exc))

    def _short_comment(self, text: str, limit: int = 90) -> str:
        text = " ".join((text or "").split())
        if len(text) <= limit:
            return text
        return text[: limit - 1].rstrip() + "…"

    def _draw_result_labels_on_canvas(self) -> None:
        if not hasattr(self, "result_canvas"):
            return
        self.result_canvas.delete("result_label")
        scale, ox, oy, dw, dh = self.result_display
        for item in self._result_annotations_in_source():
            pts = item.get("_source_polygon", [])
            if not pts:
                continue
            xs = [float(p[0]) for p in pts]
            ys = [float(p[1]) for p in pts]
            cx = max(0.0, min(dw / max(scale, 1e-9), sum(xs) / len(xs)))
            cy = max(0.0, min(dh / max(scale, 1e-9), sum(ys) / len(ys)))
            x = ox + cx * scale
            y = oy + cy * scale
            cls = item.get("class", "other_artifact")
            color = TK_COLORS.get(cls, "#00aa00")
            label = item.get("label_ru") or CLASS_LABELS.get(cls, cls)
            comment = self._short_comment(item.get("comment", ""))
            text = f"{item.get('_idx', '?')}. {label}"
            if comment:
                text += f"\n{comment}"
            tid = self.result_canvas.create_text(
                x, y, text=text, anchor="center", fill="white",
                font=("TkDefaultFont", 10, "bold"), width=230, tags="result_label"
            )
            bbox = self.result_canvas.bbox(tid)
            if bbox:
                pad = 5
                rect = self.result_canvas.create_rectangle(
                    bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad,
                    fill="#1f1f1f", outline=color, width=2, tags="result_label"
                )
                self.result_canvas.tag_lower(rect, tid)

    def _update_result_legend(self) -> None:
        if not hasattr(self, "result_legend"):
            return
        self._ensure_annotations_loaded()
        lines = ["Области результата:\n"]
        if not self.embedded_annotations:
            lines.append("Разметки пока нет.\n")
        else:
            counts: Dict[str, int] = {}
            for idx, ann in enumerate(self.embedded_annotations, start=1):
                cls = ann.get("class", "other_artifact")
                counts[cls] = counts.get(cls, 0) + 1
                label = ann.get("label_ru") or CLASS_LABELS.get(cls, cls)
                comment = (ann.get("comment") or "").strip()
                lines.append(f"{idx}. {label}\n")
                if comment:
                    lines.append(f"   Комментарий: {comment}\n")
            lines.append("\nИтого по типам:\n")
            for key, count in counts.items():
                lines.append(f"{count} × {CLASS_LABELS.get(key, key)}\n")
        lines.append("\nФайлы:\n")
        lines.append("07_marked_on_original_modern.png — результат на современном фасаде\n")
        lines.append("08_marked_on_original_modern_labeled.png — тот же результат с подписями\n")
        lines.append("06_marked_rectified.png — разметка на выпрямленном фасаде\n")
        lines.append("roboflow_export.zip — датасет для Roboflow\n")
        self.result_legend.configure(state="normal")
        self.result_legend.delete("1.0", "end")
        self.result_legend.insert("1.0", "".join(lines))
        self.result_legend.configure(state="disabled")

    def _font_candidates(self) -> List[Path]:
        candidates: List[Path] = []
        windir = os.environ.get("WINDIR")
        if windir:
            candidates.extend([
                Path(windir) / "Fonts" / "arial.ttf",
                Path(windir) / "Fonts" / "segoeui.ttf",
                Path(windir) / "Fonts" / "tahoma.ttf",
            ])
        candidates.extend([
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
            Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
            Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        ])
        return candidates

    def _load_label_font(self, size: int = 28):
        from PIL import ImageFont
        for p in self._font_candidates():
            try:
                if p.exists():
                    return ImageFont.truetype(str(p), size=size)
            except Exception:
                continue
        return ImageFont.load_default()

    def _create_labeled_result_file(self) -> None:
        try:
            from PIL import Image as PILImage, ImageDraw
            outdir = Path(self.outdir.get())
            src = outdir / "07_marked_on_original_modern.png"
            if not src.exists():
                return
            base = PILImage.open(src).convert("RGBA")
            overlay = PILImage.new("RGBA", base.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            font = self._load_label_font(max(18, int(min(base.size) / 55)))
            for item in self._result_annotations_in_source():
                pts = item.get("_source_polygon", [])
                if not pts:
                    continue
                xs = [float(p[0]) for p in pts]
                ys = [float(p[1]) for p in pts]
                x = int(max(0, min(base.width - 1, sum(xs) / len(xs))))
                y = int(max(0, min(base.height - 1, sum(ys) / len(ys))))
                cls = item.get("class", "other_artifact")
                color = TK_COLORS.get(cls, "#00aa00")
                label = item.get("label_ru") or CLASS_LABELS.get(cls, cls)
                comment = self._short_comment(item.get("comment", ""), 80)
                txt = f"{item.get('_idx', '?')}. {label}"
                if comment:
                    txt += f"\n{comment}"
                try:
                    bbox = draw.multiline_textbbox((x, y), txt, font=font, spacing=4, anchor="mm")
                except TypeError:
                    w, h = draw.multiline_textsize(txt, font=font, spacing=4)
                    bbox = (x - w // 2, y - h // 2, x + w // 2, y + h // 2)
                pad = 10
                x0 = max(0, bbox[0] - pad)
                y0 = max(0, bbox[1] - pad)
                x1 = min(base.width, bbox[2] + pad)
                y1 = min(base.height, bbox[3] + pad)
                draw.rectangle((x0, y0, x1, y1), fill=(25, 25, 25, 215), outline=color, width=3)
                draw.multiline_text((x, y), txt, font=font, fill=(255, 255, 255, 255), spacing=4, anchor="mm")
            labeled = PILImage.alpha_composite(base, overlay).convert("RGB")
            labeled.save(outdir / "08_marked_on_original_modern_labeled.png")
        except Exception as exc:
            self._log(f"Не удалось создать файл с подписями, но основная разметка сохранена: {exc}\n")

    # ---------------- hooks ----------------

    def start_prepare_project(self) -> None:
        super().start_prepare_project()
        self._preview_base_cache.clear()

    def _on_tab_changed(self, _event: tk.Event) -> None:
        try:
            current = self.notebook.select()
            if hasattr(self, "tab_select") and current == str(self.tab_select):
                self._refresh_my_projects_panel()
                self._refresh_workflow_steps()
            elif current == str(self.tab_compare):
                self._schedule_compare_refresh(save=False, delay=60)
            elif current == str(self.tab_markup):
                self.markup_background_mode.set(self.compare_mode.get())
                self._reload_markup_from_disk()
                self._schedule_markup_refresh(delay=60)
            elif current == str(self.tab_result):
                self._schedule_result_refresh(delay=60)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# v13: cleaner result, zoomable markup, simpler modern sources
# ---------------------------------------------------------------------------

class AppV13(AppV12):
    """v13 interface refinements requested after real testing.

    Key changes:
    - result image shows numbered areas only; labels/comments live in the legend below;
    - markup canvas supports mouse-wheel zoom and middle/right-button pan;
    - comparison has both historical and modern visibility sliders;
    - first tab is simplified to Wikimedia Commons + local/clipboard modern sources;
    - KartaView/Panoramax and crop/open-project buttons are removed from the main UI.
    """

    # ---------------- main UI ----------------

    def _build_ui(self) -> None:
        self._compare_refresh_job = None
        self._markup_refresh_job = None
        self._result_refresh_job = None
        self._preview_base_cache: Dict[Tuple[object, int, int], Tuple[object, object]] = {}

        self.compare_mode = tk.StringVar(value="overlay")
        self.markup_background_mode = tk.StringVar(value="overlay")
        self.modern_opacity = tk.IntVar(value=100)
        self.modern_saturation = tk.IntVar(value=38)
        self.modern_brightness = tk.IntVar(value=86)
        self.old_contrast = tk.IntVar(value=145)
        self.old_brightness = tk.IntVar(value=108)
        self.old_sharpness = tk.IntVar(value=110)
        self.compare_split = tk.IntVar(value=50)
        self.markup_class = tk.StringVar(value="added_floor")
        self.markup_comment = tk.StringVar(value="")
        self.markup_status = tk.StringVar(value="Разметка ещё не начата.")
        self.result_status = tk.StringVar(value="Пользовательский результат ещё не создан.")
        self.embedded_annotations: List[dict] = []
        self.current_markup_points: List[Point] = []
        self._annotation_loaded_for: Optional[str] = None
        self._rectified_images_cache = None
        self._rectified_cache_key: Optional[Tuple[str, str, float, float]] = None
        self._compare_photo_ref = None
        self._markup_photo_ref = None
        self._result_photo_ref = None
        self.compare_display = (1.0, 0, 0, 0, 0)
        self.markup_display = (1.0, 0, 0, 0, 0)
        self.result_display = (1.0, 0, 0, 0, 0)
        self.markup_zoom = 1.0
        self.markup_pan_x = 0.0
        self.markup_pan_y = 0.0
        self._markup_pan_start: Optional[Tuple[int, int, float, float]] = None
        self.modern_source_kind.set("Wikimedia Commons")

        self.title(f"Archiview CV {APP_VERSION}")
        try:
            style = ttk.Style(self)
            style.configure("Big.TButton", padding=(8, 6), font=("TkDefaultFont", 10, "bold"))
        except Exception:
            pass

        title = ttk.Label(
            self,
            text="Archiview CV v15: источники → выпрямление → сравнение → разметка",
            font=("TkDefaultFont", 12, "bold"),
        )
        title.pack(anchor="w", padx=12, pady=(10, 4))

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=6)
        self.tab_select = ttk.Frame(self.notebook)
        self.tab_rectify = ttk.Frame(self.notebook)
        self.tab_compare = ttk.Frame(self.notebook)
        self.tab_markup = ttk.Frame(self.notebook)
        self.tab_result = ttk.Frame(self.notebook)
        self.tab_straight = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_select, text="1. Источники")
        self.notebook.add(self.tab_rectify, text="2. Выпрямление")
        self.notebook.add(self.tab_compare, text="3. Сравнение")
        self.notebook.add(self.tab_markup, text="4. Разметка")
        self.notebook.add(self.tab_result, text="5. Результат")
        self.notebook.add(self.tab_straight, text="6. Отдельно выпрямить фасад")
        self._build_select_tab(self.tab_select)
        self._build_rectify_tab(self.tab_rectify)
        self._build_compare_tab(self.tab_compare)
        self._build_markup_tab(self.tab_markup)
        self._build_result_tab(self.tab_result)
        self._build_straight_tab(self.tab_straight)
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        log_frame = ttk.LabelFrame(self, text="Сообщения программы")
        log_frame.pack(fill="x", padx=12, pady=(0, 10))
        self.log = tk.Text(log_frame, height=4, wrap="word")
        self.log.pack(fill="x", expand=False, padx=8, pady=8)

        # Throttled resize handlers from v12.
        self.compare_canvas.bind("<Configure>", lambda _e: self._schedule_compare_refresh(save=False, delay=120))
        self.markup_canvas.bind("<Configure>", lambda _e: self._schedule_markup_refresh(delay=120))
        self.result_canvas.bind("<Configure>", lambda _e: self._schedule_result_refresh(delay=120))
        self._log("v15: откройте дом в «Мои проекты» или добавьте новый — дальше PastVu и 4 угла на этой вкладке.\n")
        self.after(0, self._refresh_my_projects_panel)
        self._fit_main_window_to_screen()

    # ---------------- first tab ----------------

    def _build_select_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        outer_pane = ttk.Panedwindow(parent, orient="vertical")
        outer_pane.grid(row=0, column=0, sticky="nsew", padx=8, pady=6)

        header = ttk.Frame(outer_pane)
        body = ttk.Frame(outer_pane)
        outer_pane.add(header, weight=0)
        outer_pane.add(body, weight=1)
        header.columnconfigure(0, weight=1)
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)

        if MyProjectsPanel is not None:
            self.my_projects_panel = MyProjectsPanel(
                header,
                project_root=APP_DIR / "archiview_projects",
                on_open_project=lambda p: self._open_project_dir(p, go_tab="result"),
                on_new_project=self.new_house_project,
                on_import_excel=self.open_excel_import_dialog,
                on_projects_deleted=self._after_projects_deleted,
                on_log=self._log,
            )
            self.my_projects_panel.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        else:
            ttk.Label(header, text="Модуль списка проектов не найден.", foreground="red").grid(
                row=0, column=0, sticky="w", padx=4, pady=4
            )

        mid_row = ttk.Panedwindow(header, orient="horizontal")
        mid_row.grid(row=1, column=0, sticky="nsew", pady=(0, 6))
        wf_col = ttk.Frame(mid_row)
        house_col = ttk.LabelFrame(
            mid_row,
            text="Данные дома — справа: карта, адрес, код сайта (папка ≠ код сайта)",
        )
        mid_row.add(wf_col, weight=2)
        mid_row.add(house_col, weight=3)
        self._build_workflow_steps_panel(wf_col)

        top = house_col
        top.columnconfigure(1, weight=1)
        ttk.Label(top, text="Папка проекта:").grid(row=0, column=0, sticky="w", padx=8, pady=4)
        ttk.Entry(top, textvariable=self.project_dir).grid(row=0, column=1, sticky="ew", padx=6, pady=4)
        ttk.Button(top, text="Папка…", command=self.choose_project_dir).grid(row=0, column=2, padx=8, pady=4)
        ttk.Label(top, text="Название дома:").grid(row=1, column=0, sticky="w", padx=8, pady=4)
        ttk.Entry(top, textvariable=self.object_name).grid(row=1, column=1, sticky="ew", padx=6, pady=4)
        ttk.Label(top, text="Код на сайте:").grid(row=2, column=0, sticky="w", padx=8, pady=4)
        ttk.Entry(top, textvariable=self.site_card_id, width=14).grid(row=2, column=1, sticky="w", padx=6, pady=4)
        ttk.Label(
            top,
            text="Как в таблице «Код сайта»: MOSCOW_001, MOSCOW_003… (не имя папки и не …_kumaninykh из ссылки)",
            foreground="#666",
            wraplength=520,
        ).grid(row=3, column=0, columnspan=3, sticky="w", padx=8, pady=(0, 4))
        ttk.Label(top, text="Адрес:").grid(row=4, column=0, sticky="w", padx=8, pady=4)
        ttk.Entry(top, textvariable=self.address).grid(row=4, column=1, sticky="ew", padx=6, pady=4)
        ttk.Label(top, text="Координаты:").grid(row=5, column=0, sticky="w", padx=8, pady=4)
        coord_row = ttk.Frame(top)
        coord_row.grid(row=5, column=1, sticky="ew", padx=6, pady=4)
        ttk.Label(coord_row, text="Широта").pack(side="left")
        ttk.Entry(coord_row, textvariable=self.lat, width=14).pack(side="left", padx=(4, 10))
        ttk.Label(coord_row, text="Долгота").pack(side="left")
        ttk.Entry(coord_row, textvariable=self.lon, width=14).pack(side="left", padx=(4, 10))
        btn_row = ttk.Frame(top)
        btn_row.grid(row=6, column=0, columnspan=3, sticky="w", padx=8, pady=4)
        ttk.Button(btn_row, text="Карта / выбрать точку", command=self.open_map_picker).pack(side="left")
        ttk.Button(btn_row, text="Найти координаты по адресу", command=self.start_geocode).pack(side="left", padx=6)
        ttk.Button(btn_row, text="Сохранить", command=self._persist_house_metadata).pack(side="left", padx=6)
        ttk.Label(top, textvariable=self.geocode_result, foreground="#333", wraplength=900).grid(
            row=7, column=0, columnspan=3, sticky="w", padx=8, pady=(2, 6)
        )
        ttk.Label(
            top,
            text="Границы ниже: ↔ историческое/современное, ↕ настройки/миниатюры. Правки сохраняются автоматически.",
            foreground="#555",
            wraplength=900,
        ).grid(row=8, column=0, columnspan=3, sticky="w", padx=8, pady=(0, 8))

        main_pane = ttk.Panedwindow(body, orient="horizontal")
        main_pane.grid(row=0, column=0, sticky="nsew")
        left = ttk.LabelFrame(main_pane, text="Историческое фото: PastVu или файл")
        right = ttk.LabelFrame(main_pane, text="Современное фото: файл, буфер или Wikimedia Commons")
        main_pane.add(left, weight=1)
        main_pane.add(right, weight=1)

        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)
        hist_pane = ttk.Panedwindow(left, orient="vertical")
        hist_pane.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        hist_controls_wrap = ttk.Frame(hist_pane)
        hist_preview = ttk.LabelFrame(hist_pane, text="Миниатюры PastVu — выберите похожий исторический ракурс фасада")
        hist_pane.add(hist_controls_wrap, weight=1)
        hist_pane.add(hist_preview, weight=2)
        hist_scroll = ScrollableFrame(hist_controls_wrap)
        hist_scroll.pack(fill="both", expand=True)
        hist_controls = hist_scroll.inner
        hist_controls.columnconfigure(1, weight=1)
        self._configure_vertical_pane(hist_pane, hist_controls_wrap, hist_preview, top_minsize=240, bottom_minsize=120, initial_top=340)

        ttk.Label(
            hist_controls,
            text="Адрес и координаты — в блоке «Данные дома» выше. Здесь — поиск PastVu по этим координатам.",
            foreground="#555",
            wraplength=560,
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=8, pady=(8, 6))

        filters = ttk.Frame(hist_controls)
        filters.grid(row=1, column=0, columnspan=3, sticky="ew", padx=8, pady=6)
        ttk.Label(filters, text="Радиус PastVu, м:").pack(side="left")
        ttk.Entry(filters, textvariable=self.search_distance, width=6).pack(side="left", padx=(4, 12))
        ttk.Label(filters, text="Лимит:").pack(side="left")
        ttk.Entry(filters, textvariable=self.search_limit, width=5).pack(side="left", padx=(4, 12))
        ttk.Label(filters, text="Годы от:").pack(side="left")
        ttk.Entry(filters, textvariable=self.year_from, width=6).pack(side="left", padx=(4, 6))
        ttk.Label(filters, text="до:").pack(side="left")
        ttk.Entry(filters, textvariable=self.year_to, width=6).pack(side="left", padx=(4, 12))

        pastvu_search_line = ttk.Frame(hist_controls)
        pastvu_search_line.grid(row=2, column=0, columnspan=3, sticky="ew", padx=8, pady=(0, 6))
        ttk.Button(pastvu_search_line, text="Найти фото PastVu", command=self.start_pastvu_search, style="Big.TButton").pack(side="left", fill="x", expand=True)

        ttk.Checkbutton(
            hist_controls,
            text="Скрывать вероятные интерьеры / решётки / детали, не похожие на фасад",
            variable=self.exclude_nonfacade,
        ).grid(row=3, column=0, columnspan=3, sticky="w", padx=8, pady=(0, 6))
        hist_file = ttk.Frame(hist_controls)
        hist_file.grid(row=4, column=0, columnspan=3, sticky="ew", padx=8, pady=(0, 6))
        ttk.Button(hist_file, text="Или выбрать историческое фото с компьютера…", command=self.choose_historical_img).pack(side="left")
        ttk.Button(hist_file, text="Открыть выбранное PastVu", command=self.open_selected_pastvu_page).pack(side="left", padx=6)
        ttk.Label(hist_controls, textvariable=self.selected_source_label, foreground="#555", wraplength=560).grid(row=5, column=0, columnspan=3, sticky="w", padx=8, pady=(0, 6))
        ttk.Label(hist_controls, text="↓ Ниже миниатюры PastVu. Если часть скрыта, потяните границу блока или прокрутите.", foreground="#777").grid(row=6, column=0, columnspan=3, sticky="w", padx=8, pady=(0, 6))

        hist_list = ttk.LabelFrame(
            hist_controls,
            text="Исторические фото для сравнения — можно добавить несколько, у каждого свои 4 угла",
        )
        hist_list.grid(row=7, column=0, columnspan=3, sticky="nsew", padx=8, pady=(0, 8))
        hist_list.columnconfigure(0, weight=1)
        cols = ("active", "label", "points", "source")
        self.hist_sources_tree = ttk.Treeview(hist_list, columns=cols, show="headings", height=5, selectmode="browse")
        self.hist_sources_tree.heading("active", text="")
        self.hist_sources_tree.heading("label", text="Фото")
        self.hist_sources_tree.heading("points", text="4 угла")
        self.hist_sources_tree.heading("source", text="Источник")
        self.hist_sources_tree.column("active", width=24, anchor="center")
        self.hist_sources_tree.column("label", width=220, anchor="w")
        self.hist_sources_tree.column("points", width=60, anchor="center")
        self.hist_sources_tree.column("source", width=80, anchor="center")
        self.hist_sources_tree.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        hist_list_btns = ttk.Frame(hist_list)
        hist_list_btns.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
        ttk.Button(hist_list_btns, text="Указать 4 угла", command=self.pick_corners_for_selected_historical, style="Big.TButton").pack(side="left")
        ttk.Button(hist_list_btns, text="Сделать активным", command=self.activate_selected_historical_source).pack(side="left", padx=6)
        ttk.Button(hist_list_btns, text="Удалить из списка", command=self.remove_selected_historical_source).pack(side="left", padx=6)
        self.hist_sources_tree.bind("<Double-1>", lambda _e: self.activate_selected_historical_source())

        self.thumb_area = ScrollableFrame(hist_preview)
        self.thumb_area.pack(fill="both", expand=True, padx=6, pady=6)

        # Modern pane.
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)
        modern_pane = ttk.Panedwindow(right, orient="vertical")
        modern_pane.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        modern_controls_wrap = ttk.Frame(modern_pane)
        modern_preview = ttk.LabelFrame(modern_pane, text="Миниатюры Wikimedia Commons — выберите современный ракурс, если своих фото нет")
        modern_pane.add(modern_controls_wrap, weight=1)
        modern_pane.add(modern_preview, weight=2)
        modern_scroll = ScrollableFrame(modern_controls_wrap)
        modern_scroll.pack(fill="both", expand=True)
        modern_controls = modern_scroll.inner
        self._configure_vertical_pane(modern_pane, modern_controls_wrap, modern_preview, top_minsize=220, bottom_minsize=120, initial_top=300)
        modern_controls.columnconfigure(1, weight=1)
        self._configure_vertical_pane(outer_pane, header, body, top_minsize=180, bottom_minsize=260, initial_top=260)

        ttk.Label(modern_controls, text="Историческое фото:").grid(row=0, column=0, sticky="w", padx=8, pady=5)
        ttk.Entry(modern_controls, textvariable=self.historical_img).grid(row=0, column=1, sticky="ew", padx=6, pady=5)
        ttk.Button(modern_controls, text="Выбрать…", command=self.choose_historical_img).grid(row=0, column=2, padx=8, pady=5)
        ttk.Label(modern_controls, text="Современное фото:").grid(row=1, column=0, sticky="w", padx=8, pady=5)
        ttk.Entry(modern_controls, textvariable=self.modern_img).grid(row=1, column=1, sticky="ew", padx=6, pady=5)
        ttk.Button(modern_controls, text="Выбрать файл…", command=self.choose_modern_img).grid(row=1, column=2, padx=8, pady=5)
        ttk.Label(modern_controls, textvariable=self.modern_source_label, foreground="#555", wraplength=560).grid(row=2, column=0, columnspan=3, sticky="w", padx=8, pady=(0, 4))

        modern_actions = ttk.Frame(modern_controls)
        modern_actions.grid(row=3, column=0, columnspan=3, sticky="w", padx=8, pady=5)
        ttk.Button(modern_actions, text="Вставить скрин из буфера", command=self.paste_modern_from_clipboard).pack(side="left")

        open_box = ttk.LabelFrame(modern_controls, text="Открытые современные фото рядом с точкой")
        open_box.grid(row=4, column=0, columnspan=3, sticky="ew", padx=8, pady=(8, 4))
        row0 = ttk.Frame(open_box)
        row0.grid(row=0, column=0, columnspan=3, sticky="ew", padx=6, pady=(6, 2))
        ttk.Label(row0, text="Источник: Wikimedia Commons").pack(side="left")
        self.modern_source_kind.set("Wikimedia Commons")
        ttk.Label(row0, text="  Радиус, м:").pack(side="left", padx=(12, 2))
        ttk.Entry(row0, textvariable=self.modern_search_radius, width=6).pack(side="left", padx=(4, 12))
        ttk.Label(row0, text="Показать:").pack(side="left")
        ttk.Entry(row0, textvariable=self.modern_search_limit, width=5).pack(side="left", padx=(4, 12))
        row1 = ttk.Frame(open_box)
        row1.grid(row=1, column=0, columnspan=3, sticky="ew", padx=6, pady=(6, 2))
        ttk.Button(row1, text="Найти современные фото", command=self.start_modern_open_search, style="Big.TButton").pack(side="left", fill="x", expand=True)
        ttk.Button(row1, text="Ещё +30", command=self.load_more_modern_photos).pack(side="left", padx=8)
        ttk.Label(
            open_box,
            text="Commons чаще даёт обычные фотографии зданий с понятной страницей источника. KartaView и Panoramax убраны из интерфейса, потому что на практике часто не дают нужный фасадный ракурс.",
            foreground="#555",
            wraplength=640,
        ).grid(row=2, column=0, columnspan=3, sticky="w", padx=6, pady=(2, 6))
        ttk.Label(modern_controls, text="↓ Ниже миниатюры современных фото. На карточке есть кнопки ‘Миниатюра’, ‘Страница’, ‘Картинка’. Она помогает вручную догрузить превью.", foreground="#777", wraplength=640).grid(row=5, column=0, columnspan=3, sticky="w", padx=8, pady=6)

        self.modern_thumb_area = ScrollableFrame(modern_preview)
        self.modern_thumb_area.pack(fill="both", expand=True, padx=6, pady=6)

        help_text = (
            "Добавьте одно или несколько исторических фото слева и современное справа. "
            "Для каждого исторического фото нажмите «Указать 4 угла», затем вкладка «2. Выпрямление»."
        )
        ttk.Label(modern_controls, text=help_text, wraplength=640, foreground="#333").grid(row=6, column=0, columnspan=3, sticky="w", padx=8, pady=6)
        self.after(0, self._refresh_workflow_steps)

    # ---------------- rectification tab ----------------

    def _build_rectify_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(1, weight=1)
        box = ttk.LabelFrame(parent, text="Обязательный шаг: выпрямить оба фото по одной и той же плоскости фасада")
        box.grid(row=0, column=0, columnspan=3, sticky="ew", padx=10, pady=10)
        box.columnconfigure(1, weight=1)
        self._row_file(box, "Историческое фото:", self.historical_img, self.choose_historical_img, 0)
        self._row_file(box, "Современное фото:", self.modern_img, self.choose_modern_img, 1)
        self._row_folder(box, "Папка результата:", self.outdir, self.choose_result_dir, 2)

        point_frame = ttk.LabelFrame(parent, text="4 угла фасада")
        point_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=10, pady=8)
        ttk.Label(
            point_frame,
            text="Активное историческое фото — из списка на вкладке «Источники». Современные 4 угла задаются один раз и повторно используются.",
            wraplength=980,
            foreground="#555",
        ).pack(anchor="w", padx=8, pady=(8, 4))
        pf_btns = ttk.Frame(point_frame)
        pf_btns.pack(anchor="w", padx=8, pady=8)
        ttk.Button(pf_btns, text="Указать 4 угла на двух фото одновременно", command=self.pick_both_corners, style="Big.TButton").pack(side="left")
        ttk.Label(pf_btns, textvariable=self.points_status, foreground="#555").pack(side="left", padx=10)

        slider_frame = ttk.LabelFrame(parent, text="Overlay")
        slider_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=10, pady=8)
        ttk.Label(slider_frame, textvariable=self.old_opacity_label).pack(anchor="w", padx=8, pady=(8, 0))
        tk.Scale(slider_frame, from_=0, to=100, orient="horizontal", variable=self.old_opacity, command=self._update_opacity_label, length=420, showvalue=False).pack(anchor="w", padx=8, pady=(0, 4))
        ttk.Checkbutton(
            slider_frame,
            text="Показывать весь исходный снимок (4 угла только для наложения; рекомендуется)",
            variable=self.keep_context,
        ).pack(anchor="w", padx=8, pady=(0, 4))
        ttk.Label(
            slider_frame,
            text="После выпрямления пустые белые поля по краям обрезаются автоматически — фасад крупнее на экране.",
            foreground="#555",
            wraplength=900,
        ).pack(anchor="w", padx=8, pady=(0, 8))

        btns = ttk.Frame(parent)
        btns.grid(row=3, column=0, columnspan=3, sticky="ew", padx=10, pady=10)
        btns.columnconfigure(0, weight=1)
        tk.Button(btns, text="ПОДГОТОВИТЬ ВЫПРЯМЛЕННЫЕ ФОТО И СРАВНЕНИЕ", command=self.start_prepare_project, bg="#0b6bcb", fg="white", activebackground="#084f96", activeforeground="white", font=("TkDefaultFont", 10, "bold"), padx=10, pady=8).grid(row=0, column=0, sticky="ew")
        small = ttk.Frame(parent)
        small.grid(row=4, column=0, columnspan=3, sticky="w", padx=10, pady=(0, 8))
        ttk.Button(small, text="Открыть overlay", command=self.open_overlay).pack(side="left")
        ttk.Button(small, text="Открыть до/после", command=self.open_before_after).pack(side="left", padx=6)
        ttk.Button(small, text="Открыть папку результата", command=lambda: open_path(Path(self.outdir.get()))).pack(side="left", padx=6)

        ttk.Label(parent, textvariable=self.rectified_status, font=("TkDefaultFont", 10, "bold")).grid(row=5, column=0, columnspan=3, sticky="w", padx=10, pady=8)
        warning = "Важно: 4 точки должны быть одной и той же плоскостью здания. Расширенный холст не обрезает всё за пределами этих 4 точек — поэтому надстройка или пристройка останется видимой."
        ttk.Label(parent, text=warning, wraplength=980, foreground="#6b4a00").grid(row=6, column=0, columnspan=3, sticky="w", padx=10, pady=8)

    # ---------------- comparison tab ----------------

    def _build_compare_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=0)
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(0, weight=1)
        controls_box = ttk.LabelFrame(parent, text="Настроить вид сравнения")
        controls_box.grid(row=0, column=0, sticky="ns", padx=(8, 6), pady=8)
        controls_box.rowconfigure(0, weight=1)
        controls_box.columnconfigure(0, weight=1)
        controls_scroll = ScrollableFrame(controls_box)
        controls_scroll.grid(row=0, column=0, sticky="nsew")
        controls = controls_scroll.inner
        controls.columnconfigure(0, weight=1)
        ttk.Label(controls, text="Если настройки не помещаются, прокрутите этот блок. Настроенный вид автоматически становится фоном разметки.", wraplength=280, foreground="#555").grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 8))
        mode_box = ttk.LabelFrame(controls, text="Режим просмотра")
        mode_box.grid(row=1, column=0, sticky="ew", padx=10, pady=6)
        for value, label in (("overlay", "Overlay"), ("before_after", "До / после"), ("modern", "Только современное"), ("historical", "Только историческое")):
            ttk.Radiobutton(mode_box, text=label, value=value, variable=self.compare_mode, command=self._refresh_compare_canvas).pack(anchor="w", padx=8, pady=2)
        sliders = ttk.LabelFrame(controls, text="Видимость и читаемость")
        sliders.grid(row=2, column=0, sticky="ew", padx=10, pady=6)
        self._v11_scale(sliders, "Видимость исторического фото", self.old_opacity, 0, 100, self._compare_slider_changed)
        self._v11_scale(sliders, "Видимость современного фото", self.modern_opacity, 0, 100, self._compare_slider_changed)
        self._v11_scale(sliders, "Насыщенность современного", self.modern_saturation, 0, 100, self._compare_slider_changed)
        self._v11_scale(sliders, "Яркость современного", self.modern_brightness, 35, 130, self._compare_slider_changed)
        self._v11_scale(sliders, "Контраст исторического", self.old_contrast, 80, 240, self._compare_slider_changed)
        self._v11_scale(sliders, "Яркость исторического", self.old_brightness, 70, 150, self._compare_slider_changed)
        self._v11_scale(sliders, "Резкость исторического", self.old_sharpness, 50, 220, self._compare_slider_changed)
        self._v11_scale(sliders, "Граница до/после", self.compare_split, 0, 100, self._compare_slider_changed)
        quick = ttk.LabelFrame(controls, text="Пресеты")
        quick.grid(row=3, column=0, sticky="ew", padx=10, pady=6)
        ttk.Button(quick, text="Для анализа", command=self._preset_analysis).pack(fill="x", padx=8, pady=3)
        ttk.Button(quick, text="Больше видно старое", command=self._preset_old_stronger).pack(fill="x", padx=8, pady=3)
        ttk.Button(quick, text="Мягкое наложение", command=self._preset_soft).pack(fill="x", padx=8, pady=3)
        actions = ttk.LabelFrame(controls, text="Действия")
        actions.grid(row=4, column=0, sticky="ew", padx=10, pady=6)
        ttk.Button(actions, text="Обновить просмотр", command=self._refresh_compare_canvas).pack(fill="x", padx=8, pady=3)
        ttk.Button(actions, text="Открыть HTML overlay", command=self.open_overlay).pack(fill="x", padx=8, pady=3)
        ttk.Button(actions, text="Открыть HTML до/после", command=self.open_before_after).pack(fill="x", padx=8, pady=3)
        ttk.Button(actions, text="Открыть папку результата", command=lambda: open_path(Path(self.outdir.get()))).pack(fill="x", padx=8, pady=3)
        self.compare_status = tk.StringVar(value="Сначала во вкладке 2 подготовьте выпрямленную пару.")
        ttk.Label(controls, textvariable=self.compare_status, wraplength=280, foreground="#555").grid(row=5, column=0, sticky="ew", padx=10, pady=(8, 10))

        view = ttk.LabelFrame(parent, text="Встроенный просмотр")
        view.grid(row=0, column=1, sticky="nsew", padx=(6, 8), pady=8)
        view.rowconfigure(1, weight=1)
        view.columnconfigure(0, weight=1)
        thumbs = ttk.LabelFrame(view, text="Сравниваемые фото")
        thumbs.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 6))
        self.compare_thumb_caption = tk.StringVar(value="Миниатюры появятся после выбора фото и выпрямления")
        ttk.Label(thumbs, textvariable=self.compare_thumb_caption, foreground="#555").pack(anchor="w", padx=8, pady=(6, 4))
        thumb_row = ttk.Frame(thumbs)
        thumb_row.pack(fill="x", padx=8, pady=(0, 8))
        hist_box = ttk.Frame(thumb_row)
        hist_box.pack(side="left", padx=(0, 16))
        ttk.Label(hist_box, text="Историческое").pack(anchor="w")
        self.compare_hist_thumb_label = ttk.Label(hist_box, text="(нет фото)", width=22, anchor="center")
        self.compare_hist_thumb_label.pack(pady=4)
        mod_box = ttk.Frame(thumb_row)
        mod_box.pack(side="left")
        ttk.Label(mod_box, text="Современное").pack(anchor="w")
        self.compare_modern_thumb_label = ttk.Label(mod_box, text="(нет фото)", width=22, anchor="center")
        self.compare_modern_thumb_label.pack(pady=4)
        self.compare_canvas = tk.Canvas(view, bg="#2e2e2e", highlightthickness=0)
        self.compare_canvas.grid(row=1, column=0, sticky="nsew")
        self.compare_canvas.bind("<Configure>", lambda _e: self._schedule_compare_refresh(save=False, delay=120))
        self.compare_canvas.bind("<Button-1>", self._compare_canvas_drag_split)
        self.compare_canvas.bind("<B1-Motion>", self._compare_canvas_drag_split)

    def _preset_analysis(self) -> None:
        self.old_opacity.set(68); self.modern_opacity.set(95)
        self.modern_saturation.set(38); self.modern_brightness.set(86)
        self.old_contrast.set(145); self.old_brightness.set(108); self.old_sharpness.set(115)
        self.compare_split.set(50); self._compare_slider_changed(None)

    def _preset_old_stronger(self) -> None:
        self.old_opacity.set(82); self.modern_opacity.set(70)
        self.modern_saturation.set(25); self.modern_brightness.set(76)
        self.old_contrast.set(165); self.old_brightness.set(112); self.old_sharpness.set(130)
        self._compare_slider_changed(None)

    def _preset_soft(self) -> None:
        self.old_opacity.set(50); self.modern_opacity.set(100)
        self.modern_saturation.set(55); self.modern_brightness.set(95)
        self.old_contrast.set(125); self.old_brightness.set(104); self.old_sharpness.set(100)
        self._compare_slider_changed(None)

    def _compose_preview_for_canvas(self, canvas: tk.Canvas, mode: Optional[str] = None) -> Tuple[object, Tuple[float, int, int, int, int]]:
        old_small, modern_small, scale, ox, oy, dw, dh = self._load_preview_base_images(canvas)
        old_p = self._prepared_old_pil(old_small)
        modern_p = self._prepared_modern_pil(modern_small)
        view_mode = mode or self.compare_mode.get()
        if view_mode == "historical":
            out = old_p
        elif view_mode == "modern":
            out = modern_p
        elif view_mode == "before_after":
            x = int(round(dw * self.compare_split.get() / 100.0))
            out = old_p.copy()
            out.paste(modern_p.crop((x, 0, dw, dh)), (x, 0))
        else:
            bg = Image.new("RGB", modern_p.size, (245, 245, 245))  # type: ignore[union-attr]
            out = Image.blend(bg, modern_p, max(0, min(100, int(self.modern_opacity.get()))) / 100.0)
            out = Image.blend(out, old_p, max(0, min(100, int(self.old_opacity.get()))) / 100.0)
        return out, (scale, ox, oy, dw, dh)

    def _compose_current_view(self, mode: Optional[str] = None):
        old, modern = self._load_rectified_images()
        old_p = self._prepared_old_pil(old)
        modern_p = self._prepared_modern_pil(modern)
        view_mode = mode or self.compare_mode.get()
        if view_mode == "historical":
            return old_p
        if view_mode == "modern":
            return modern_p
        if view_mode == "before_after":
            w, h = old_p.size
            x = int(round(w * self.compare_split.get() / 100.0))
            out = old_p.copy()
            out.paste(modern_p.crop((x, 0, w, h)), (x, 0))
            return out
        bg = Image.new("RGB", modern_p.size, (245, 245, 245))  # type: ignore[union-attr]
        out = Image.blend(bg, modern_p, max(0, min(100, int(self.modern_opacity.get()))) / 100.0)
        return Image.blend(out, old_p, max(0, min(100, int(self.old_opacity.get()))) / 100.0)

    # ---------------- markup tab with zoom ----------------

    def _build_markup_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=0)
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(0, weight=1)
        tools_box = ttk.LabelFrame(parent, text="Классы и инструменты разметки")
        tools_box.grid(row=0, column=0, sticky="ns", padx=(8, 6), pady=8)
        tools_scroll = ScrollableFrame(tools_box)
        tools_scroll.pack(fill="both", expand=True)
        tools = tools_scroll.inner
        tools.columnconfigure(0, weight=1)
        ttk.Label(tools, text="Разметка идёт по выпрямленному холсту. Колесо мыши — приближение, средняя или правая кнопка — двигать изображение.", wraplength=285, foreground="#555").grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))
        bg_box = ttk.LabelFrame(tools, text="Фон для рисования")
        bg_box.grid(row=1, column=0, sticky="ew", padx=10, pady=6)
        for value, label in (("overlay", "Настроенный overlay"), ("before_after", "До / после"), ("modern", "Только современное"), ("historical", "Только историческое")):
            ttk.Radiobutton(bg_box, text=label, value=value, variable=self.markup_background_mode, command=self._reset_markup_zoom_and_refresh).pack(anchor="w", padx=8, pady=2)
        class_box = ttk.LabelFrame(tools, text="Что отмечаем")
        class_box.grid(row=2, column=0, sticky="ew", padx=10, pady=6)
        for key, label in CLASS_LABELS.items():
            ttk.Radiobutton(class_box, text=label, value=key, variable=self.markup_class).pack(anchor="w", padx=8, pady=1)
        comment_box = ttk.LabelFrame(tools, text="Комментарий к области")
        comment_box.grid(row=3, column=0, sticky="ew", padx=10, pady=6)
        ttk.Entry(comment_box, textvariable=self.markup_comment).pack(fill="x", padx=8, pady=8)
        action_box = ttk.LabelFrame(tools, text="Действия")
        action_box.grid(row=4, column=0, sticky="ew", padx=10, pady=6)
        ttk.Button(action_box, text="Закончить область", command=self._finish_markup_polygon).pack(fill="x", padx=8, pady=3)
        ttk.Button(action_box, text="Отменить точку", command=self._undo_markup_point).pack(fill="x", padx=8, pady=3)
        ttk.Button(action_box, text="Удалить последнюю область", command=self._undo_markup_polygon).pack(fill="x", padx=8, pady=3)
        ttk.Button(action_box, text="Очистить всё", command=self._clear_markup_all).pack(fill="x", padx=8, pady=3)
        tk.Button(action_box, text="СОХРАНИТЬ РАЗМЕТКУ И ПЕРЕЙТИ К РЕЗУЛЬТАТУ", command=self._save_markup_annotations, bg="#0b7a3b", fg="white", activebackground="#075a2c", activeforeground="white", font=("TkDefaultFont", 9, "bold"), padx=8, pady=8).pack(fill="x", padx=8, pady=(9, 3))
        ttk.Button(action_box, text="Сбросить приближение", command=self._reset_markup_zoom_and_refresh).pack(fill="x", padx=8, pady=3)
        ttk.Button(action_box, text="Открыть папку результата", command=lambda: open_path(Path(self.outdir.get()))).pack(fill="x", padx=8, pady=3)
        ttk.Label(tools, textvariable=self.markup_status, wraplength=285, foreground="#555").grid(row=5, column=0, sticky="ew", padx=10, pady=(8, 10))

        view = ttk.LabelFrame(parent, text="Рисуйте прямо здесь: левый клик — точка; колесо — zoom; правая/средняя кнопка — перемещение")
        view.grid(row=0, column=1, sticky="nsew", padx=(6, 8), pady=8)
        view.rowconfigure(0, weight=1)
        view.columnconfigure(0, weight=1)
        self.markup_canvas = tk.Canvas(view, bg="#2e2e2e", highlightthickness=0)
        self.markup_canvas.grid(row=0, column=0, sticky="nsew")
        self.markup_canvas.bind("<Configure>", lambda _e: self._schedule_markup_refresh(delay=120))
        self.markup_canvas.bind("<Button-1>", self._markup_click)
        self.markup_canvas.bind("<Double-Button-1>", lambda _e: self._finish_markup_polygon())
        self.markup_canvas.bind("<MouseWheel>", self._markup_mousewheel)
        self.markup_canvas.bind("<Button-4>", self._markup_mousewheel)
        self.markup_canvas.bind("<Button-5>", self._markup_mousewheel)
        self.markup_canvas.bind("<ButtonPress-2>", self._markup_pan_begin)
        self.markup_canvas.bind("<B2-Motion>", self._markup_pan_move)
        self.markup_canvas.bind("<ButtonPress-3>", self._markup_pan_begin)
        self.markup_canvas.bind("<B3-Motion>", self._markup_pan_move)
        self.bind("<Return>", lambda _e: self._finish_markup_polygon())
        self.bind("<BackSpace>", lambda _e: self._undo_markup_point())
        self.bind("<Delete>", lambda _e: self._undo_markup_polygon())

    def _reset_markup_zoom_and_refresh(self) -> None:
        self.markup_zoom = 1.0
        self.markup_pan_x = 0.0
        self.markup_pan_y = 0.0
        self._schedule_markup_refresh(delay=30)

    def _markup_current_full_size(self) -> Tuple[int, int]:
        old, _modern = self._load_rectified_images()
        return old.size

    def _markup_base_scale(self) -> float:
        w, h = self._markup_current_full_size()
        cw = max(10, self.markup_canvas.winfo_width())
        ch = max(10, self.markup_canvas.winfo_height())
        return min(cw / float(w), ch / float(h), 1.0)

    def _markup_mousewheel(self, event: tk.Event) -> str:
        try:
            cw = max(10, self.markup_canvas.winfo_width())
            ch = max(10, self.markup_canvas.winfo_height())
            w, h = self._markup_current_full_size()
            base = min(cw / float(w), ch / float(h), 1.0)
            old_zoom = float(self.markup_zoom)
            old_scale = base * old_zoom
            old_ox = (cw - w * old_scale) / 2.0 + self.markup_pan_x
            old_oy = (ch - h * old_scale) / 2.0 + self.markup_pan_y
            img_x = (event.x - old_ox) / max(old_scale, 1e-9)
            img_y = (event.y - old_oy) / max(old_scale, 1e-9)
            direction = 1
            if hasattr(event, "delta") and event.delta:
                direction = 1 if event.delta > 0 else -1
            elif getattr(event, "num", None) == 5:
                direction = -1
            factor = 1.18 if direction > 0 else 1 / 1.18
            new_zoom = max(1.0, min(6.0, old_zoom * factor))
            self.markup_zoom = new_zoom
            new_scale = base * new_zoom
            desired_ox = event.x - img_x * new_scale
            desired_oy = event.y - img_y * new_scale
            self.markup_pan_x = desired_ox - (cw - w * new_scale) / 2.0
            self.markup_pan_y = desired_oy - (ch - h * new_scale) / 2.0
            self._schedule_markup_refresh(delay=20)
        except Exception:
            pass
        return "break"

    def _markup_pan_begin(self, event: tk.Event) -> str:
        self._markup_pan_start = (event.x, event.y, self.markup_pan_x, self.markup_pan_y)
        return "break"

    def _markup_pan_move(self, event: tk.Event) -> str:
        if not self._markup_pan_start:
            return "break"
        x0, y0, px0, py0 = self._markup_pan_start
        self.markup_pan_x = px0 + (event.x - x0)
        self.markup_pan_y = py0 + (event.y - y0)
        self._schedule_markup_refresh(delay=20)
        return "break"

    def _refresh_markup_canvas(self) -> None:
        if not hasattr(self, "markup_canvas"):
            return
        self._ensure_annotations_loaded()
        try:
            mode = self.markup_background_mode.get()
            if mode not in {"overlay", "before_after", "modern", "historical"}:
                mode = "overlay"
            full = self._compose_current_view(mode=mode)
            cw = max(10, self.markup_canvas.winfo_width())
            ch = max(10, self.markup_canvas.winfo_height())
            base = min(cw / float(full.width), ch / float(full.height), 1.0)
            scale = base * float(self.markup_zoom)
            dw = max(1, int(round(full.width * scale)))
            dh = max(1, int(round(full.height * scale)))
            ox = int(round((cw - dw) / 2.0 + self.markup_pan_x))
            oy = int(round((ch - dh) / 2.0 + self.markup_pan_y))
            filt = self._resize_filter_fast()
            disp = full.resize((dw, dh), filt) if full.size != (dw, dh) else full.copy()
            photo = ImageTk.PhotoImage(disp)  # type: ignore[union-attr]
            self._markup_photo_ref = photo
            self.markup_display = (scale, ox, oy, dw, dh)
            self.markup_canvas.delete("all")
            self.markup_canvas.create_image(ox, oy, image=photo, anchor="nw")
            self._draw_markup_vectors()
            self._update_markup_status_text()
        except Exception as exc:
            self.markup_status.set(str(exc))
            self._draw_canvas_message(self.markup_canvas, str(exc))

    def _update_markup_status_text(self) -> None:
        self.markup_status.set(f"Областей: {len(self.embedded_annotations)}. Точек: {len(self.current_markup_points)}. Масштаб: {self.markup_zoom:.1f}×")

    # ---------------- result tab ----------------

    def _build_result_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=0)
        parent.rowconfigure(0, weight=1)
        main = ttk.LabelFrame(parent, text="Итог для пользователя: на фото только номера, подписи — ниже")
        main.grid(row=0, column=0, sticky="nsew", padx=(8, 6), pady=8)
        main.rowconfigure(0, weight=1)
        main.columnconfigure(0, weight=1)
        self.result_canvas = tk.Canvas(main, bg="#2e2e2e", highlightthickness=0)
        self.result_canvas.grid(row=0, column=0, sticky="nsew")
        self.result_canvas.bind("<Configure>", lambda _e: self._schedule_result_refresh(delay=120))
        legend_box = ttk.LabelFrame(main, text="Подписи и комментарии к номерам")
        legend_box.grid(row=1, column=0, sticky="ew", padx=0, pady=(6, 0))
        self.result_legend = tk.Text(legend_box, width=80, height=8, wrap="word")
        self.result_legend.pack(fill="both", expand=False, padx=8, pady=6)
        self.result_legend.configure(state="disabled")

        side = ttk.LabelFrame(parent, text="Действия")
        side.grid(row=0, column=1, sticky="ns", padx=(6, 8), pady=8)
        ttk.Label(side, text="На фасаде показаны только номера областей. Названия элементов и комментарии смотрите в списке под картинкой.", wraplength=280, foreground="#555").pack(anchor="w", padx=10, pady=(10, 8))
        ttk.Label(side, textvariable=self.result_status, wraplength=280, foreground="#555").pack(anchor="w", padx=10, pady=6)
        ttk.Button(side, text="Обновить результат", command=self._refresh_result_canvas).pack(fill="x", padx=10, pady=3)
        ttk.Button(side, text="Открыть итоговую картинку", command=self.open_marked_original).pack(fill="x", padx=10, pady=3)
        ttk.Button(side, text="Открыть HTML overlay", command=self.open_overlay).pack(fill="x", padx=10, pady=3)
        ttk.Button(side, text="Открыть HTML до/после", command=self.open_before_after).pack(fill="x", padx=10, pady=3)
        ttk.Button(side, text="Открыть Roboflow export", command=self.open_roboflow_export).pack(fill="x", padx=10, pady=3)

    def _draw_result_labels_on_canvas(self) -> None:
        # v13 draws compact number badges only. Full text belongs to the legend below.
        if not hasattr(self, "result_canvas"):
            return
        self.result_canvas.delete("result_label")
        scale, ox, oy, dw, dh = self.result_display
        for item in self._result_annotations_in_source():
            pts = item.get("_source_polygon", [])
            if not pts:
                continue
            xs = [float(p[0]) for p in pts]
            ys = [float(p[1]) for p in pts]
            cx = max(0.0, min(dw / max(scale, 1e-9), sum(xs) / len(xs)))
            cy = max(0.0, min(dh / max(scale, 1e-9), sum(ys) / len(ys)))
            x = ox + cx * scale
            y = oy + cy * scale
            cls = item.get("class", "other_artifact")
            color = TK_COLORS.get(cls, "#00aa00")
            r = 13
            self.result_canvas.create_oval(x - r, y - r, x + r, y + r, fill="#1f1f1f", outline=color, width=3, tags="result_label")
            self.result_canvas.create_text(x, y, text=str(item.get("_idx", "?")), fill="white", font=("TkDefaultFont", 10, "bold"), tags="result_label")

    def _refresh_result_canvas(self) -> None:
        if not hasattr(self, "result_canvas"):
            return
        path = Path(self.outdir.get()) / "07_marked_on_original_modern.png"
        if not path.exists():
            self.result_status.set("После сохранения разметки здесь появится итоговая картинка.")
            self._draw_canvas_message(self.result_canvas, "Пока нет итоговой картинки.\n\nВо вкладке 4 обведите изменения и нажмите “Сохранить разметку и перейти к результату”.")
            self._update_result_legend()
            return
        try:
            if Image is None:
                raise RuntimeError("Pillow не установлен.")
            img = Image.open(path).convert("RGB")  # type: ignore[union-attr]
            self._show_pil_on_canvas(self.result_canvas, img, "_result_photo_ref", "result_display")
            self._draw_result_labels_on_canvas()
            legend_file = Path(self.outdir.get()) / "08_marked_on_original_modern_labeled.png"
            extra = f"\nФайл с легендой снизу: {legend_file}" if legend_file.exists() else ""
            self.result_status.set(f"Итоговая картинка готова: {path}{extra}")
            self._update_result_legend()
        except Exception as exc:
            self.result_status.set(str(exc))
            self._draw_canvas_message(self.result_canvas, str(exc))

    def _update_result_legend(self) -> None:
        if not hasattr(self, "result_legend"):
            return
        self._ensure_annotations_loaded()
        lines = ["Области результата:\n"]
        if not self.embedded_annotations:
            lines.append("Разметки пока нет.\n")
        else:
            counts: Dict[str, int] = {}
            for idx, ann in enumerate(self.embedded_annotations, start=1):
                cls = ann.get("class", "other_artifact")
                counts[cls] = counts.get(cls, 0) + 1
                label = ann.get("label_ru") or CLASS_LABELS.get(cls, cls)
                comment = (ann.get("comment") or "").strip()
                lines.append(f"{idx}. {label}\n")
                if comment:
                    lines.append(f"   Комментарий: {comment}\n")
            lines.append("\nИтого по типам:\n")
            for key, count in counts.items():
                lines.append(f"{count} × {CLASS_LABELS.get(key, key)}\n")
        lines.append("\nФайлы:\n")
        lines.append("07_marked_on_original_modern.png — результат на современном фасаде с номерами\n")
        lines.append("08_marked_on_original_modern_labeled.png — итоговая картинка с легендой снизу\n")
        lines.append("roboflow_export.zip — датасет для Roboflow\n")
        self.result_legend.configure(state="normal")
        self.result_legend.delete("1.0", "end")
        self.result_legend.insert("1.0", "".join(lines))
        self.result_legend.configure(state="disabled")

    def _create_labeled_result_file(self) -> None:
        # Create a shareable image: marked facade on top, legend/comments in a white panel below.
        try:
            from PIL import Image as PILImage, ImageDraw
            outdir = Path(self.outdir.get())
            src = outdir / "07_marked_on_original_modern.png"
            if not src.exists():
                return
            base = PILImage.open(src).convert("RGB")
            anns = list(self.embedded_annotations)
            font_title = self._load_label_font(max(18, int(min(base.size) / 55)))
            font_body = self._load_label_font(max(16, int(min(base.size) / 70)))
            # Wrap text to image width.
            max_chars = max(40, int(base.width / max(10, font_body.size * 0.55))) if hasattr(font_body, "size") else 80
            legend_lines: List[str] = ["Легенда изменений:"]
            if not anns:
                legend_lines.append("Разметки пока нет.")
            for idx, ann in enumerate(anns, start=1):
                label = ann.get("label_ru") or CLASS_LABELS.get(ann.get("class", "other_artifact"), str(ann.get("class", "")))
                comment = " ".join((ann.get("comment") or "").split())
                line = f"{idx}. {label}"
                if comment:
                    line += f" — {comment}"
                # Manual wrapping without external dependency.
                words = line.split()
                current = ""
                for word in words:
                    test = (current + " " + word).strip()
                    if len(test) > max_chars and current:
                        legend_lines.append(current)
                        current = "   " + word
                    else:
                        current = test
                if current:
                    legend_lines.append(current)
            line_h = int((font_body.size if hasattr(font_body, "size") else 20) * 1.55)
            panel_h = max(140, 34 + line_h * (len(legend_lines) + 1))
            out = PILImage.new("RGB", (base.width, base.height + panel_h), (255, 255, 255))
            out.paste(base, (0, 0))
            draw = ImageDraw.Draw(out)
            y = base.height + 22
            draw.text((24, y), legend_lines[0], fill=(20, 20, 20), font=font_title)
            y += line_h + 6
            for line in legend_lines[1:]:
                draw.text((24, y), line, fill=(20, 20, 20), font=font_body)
                y += line_h
            out.save(outdir / "08_marked_on_original_modern_labeled.png")
        except Exception as exc:
            self._log(f"Не удалось создать файл с легендой, но основная разметка сохранена: {exc}\n")

    def _save_markup_annotations(self) -> None:
        if len(self.current_markup_points) >= 3:
            self._finish_markup_polygon()
        if not self.embedded_annotations:
            messagebox.showinfo("Разметки нет", "Сначала обведите хотя бы одну область.")
            return
        try:
            self._save_current_labeling_image(mode=self.markup_background_mode.get())
            outputs = save_annotations_and_exports(Path(self.outdir.get()), self.embedded_annotations)
            self._create_labeled_result_file()
            self._annotation_saved(outputs)
            self._refresh_result_canvas()
            if hasattr(self, "notebook"):
                self.notebook.select(self.tab_result)
            messagebox.showinfo("Готово", "Разметка сохранена. Во вкладке результата на фото — номера, а подписи и комментарии — под картинкой.")
        except Exception as exc:
            messagebox.showerror("Не удалось сохранить разметку", str(exc))

    # ---------------- source search hooks ----------------

    def start_modern_open_search(self) -> None:
        self.modern_source_kind.set("Wikimedia Commons")
        super().start_modern_open_search()


# ---------------------------------------------------------------------------
# v14: zoom/pan on markup + result, space hand tool, light labels, tooltips
# ---------------------------------------------------------------------------

class AppV14(AppV13):
    """v14 — навигация по большому фасаду и интерактивный результат."""

    def _build_ui(self) -> None:
        self._space_down = False
        self._markup_dirty = False
        self._result_hover_idx: Optional[int] = None
        self._result_pil = None
        self.result_zoom = 1.0
        self.result_pan_x = 0.0
        self.result_pan_y = 0.0
        self._result_pan_start: Optional[Tuple[int, int, float, float]] = None
        self._tooltip_win: Optional[tk.Toplevel] = None
        super()._build_ui()
        self.title(f"Archiview CV {APP_VERSION}")
        self._bind_space_hand_keys()
        self._upgrade_markup_canvas_navigation()
        self._upgrade_result_canvas_navigation()
        self._log(
            "v14: пробел+ЛКМ — рука (как в Photoshop); колесо — zoom в разметке и результате; "
            "номера без чёрной подложки; наведение на область — подсказка.\n"
        )

    def _bind_space_hand_keys(self) -> None:
        self.bind_all("<KeyPress-space>", self._on_space_press, add="+")
        self.bind_all("<KeyRelease-space>", self._on_space_release, add="+")

    def _widget_accepts_typing(self, widget: tk.Misc) -> bool:
        w: Optional[tk.Misc] = widget
        while w is not None:
            if isinstance(w, (tk.Entry, ttk.Entry, ttk.Combobox)):
                return True
            if isinstance(w, tk.Text) and w is not getattr(self, "log", None):
                return True
            w = getattr(w, "master", None)
        return False

    def _on_space_press(self, event: tk.Event) -> Optional[str]:
        if self._widget_accepts_typing(event.widget):
            return None
        self._space_down = True
        self._set_canvas_cursors("fleur")
        return "break"

    def _on_space_release(self, _event: tk.Event) -> Optional[str]:
        self._space_down = False
        self._set_canvas_cursors("")
        return None

    def _set_canvas_cursors(self, cursor: str) -> None:
        for name in ("markup_canvas", "result_canvas"):
            canvas = getattr(self, name, None)
            if canvas is not None:
                canvas.configure(cursor=cursor)

    def _mark_dirty(self) -> None:
        self._markup_dirty = True
        self._update_markup_status_text()

    def _clear_dirty(self) -> None:
        self._markup_dirty = False
        self._update_markup_status_text()

    def _upgrade_markup_canvas_navigation(self) -> None:
        self.markup_canvas.bind("<B1-Motion>", self._markup_b1_motion, add="+")
        help_old = (
            "Колесо — zoom. Пробел + ЛКМ — двигать изображение. "
            "Средняя/правая кнопка — тоже перемещение."
        )
        # Update first label in tools panel if possible.
        try:
            for child in self.tab_markup.winfo_children():
                if isinstance(child, ttk.LabelFrame):
                    for sub in child.winfo_children():
                        if isinstance(sub, ScrollableFrame):
                            inner = sub.inner
                            for lbl in inner.winfo_children():
                                if isinstance(lbl, ttk.Label) and "Колесо" in str(lbl.cget("text")):
                                    lbl.configure(text=help_old)
        except Exception:
            pass

    def _upgrade_result_canvas_navigation(self) -> None:
        c = self.result_canvas
        c.bind("<MouseWheel>", self._result_mousewheel)
        c.bind("<Button-4>", self._result_mousewheel)
        c.bind("<Button-5>", self._result_mousewheel)
        c.bind("<ButtonPress-1>", self._result_pan_begin, add="+")
        c.bind("<B1-Motion>", self._result_b1_motion, add="+")
        c.bind("<ButtonPress-2>", self._result_pan_begin, add="+")
        c.bind("<B2-Motion>", self._result_pan_move, add="+")
        c.bind("<ButtonPress-3>", self._result_pan_begin, add="+")
        c.bind("<B3-Motion>", self._result_pan_move, add="+")
        c.bind("<Motion>", self._result_motion, add="+")
        c.bind("<Leave>", self._result_leave, add="+")
        if hasattr(self, "result_legend_list"):
            self.result_legend_list.bind("<<ListboxSelect>>", self._result_legend_select)
            self.result_legend_list.bind("<Motion>", self._result_legend_motion)

    def _build_result_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=0)
        parent.rowconfigure(0, weight=1)
        main = ttk.LabelFrame(parent, text="Итог: номера на фасаде, подписи — в списке (наведите на область или строку)")
        main.grid(row=0, column=0, sticky="nsew", padx=(8, 6), pady=8)
        main.rowconfigure(1, weight=1)
        main.columnconfigure(0, weight=1)
        self.result_house_header = ttk.Label(main, text="", wraplength=920, foreground="#222", font=("TkDefaultFont", 10, "bold"))
        self.result_house_header.grid(row=0, column=0, sticky="ew", padx=8, pady=(6, 4))
        self.result_canvas = tk.Canvas(main, bg="#2e2e2e", highlightthickness=0)
        self.result_canvas.grid(row=1, column=0, sticky="nsew")
        self.result_canvas.bind("<Configure>", lambda _e: self._schedule_result_refresh(delay=120))
        legend_box = ttk.LabelFrame(main, text="Легенда: номер · тип · комментарий")
        legend_box.grid(row=2, column=0, sticky="ew", padx=0, pady=(6, 0))
        legend_row = ttk.Frame(legend_box)
        legend_row.pack(fill="both", expand=False, padx=8, pady=6)
        self.result_legend_list = tk.Listbox(legend_row, height=8, activestyle="dotbox")
        legend_scroll = ttk.Scrollbar(legend_row, orient="vertical", command=self.result_legend_list.yview)
        self.result_legend_list.configure(yscrollcommand=legend_scroll.set)
        self.result_legend_list.pack(side="left", fill="both", expand=True)
        legend_scroll.pack(side="right", fill="y")
        self.result_legend = None

        side = ttk.LabelFrame(parent, text="Действия")
        side.grid(row=0, column=1, sticky="ns", padx=(6, 8), pady=8)
        ttk.Label(
            side,
            text="Пробел + ЛКМ — двигать. Колесо — zoom. Наведите на область — подсказка.",
            wraplength=280,
            foreground="#555",
        ).pack(anchor="w", padx=10, pady=(10, 8))
        ttk.Label(side, textvariable=self.result_status, wraplength=280, foreground="#555").pack(anchor="w", padx=10, pady=6)
        ttk.Button(side, text="Сбросить приближение", command=self._reset_result_zoom_and_refresh).pack(fill="x", padx=10, pady=3)
        ttk.Button(side, text="Обновить результат", command=self._refresh_result_canvas).pack(fill="x", padx=10, pady=3)
        ttk.Button(side, text="Открыть итоговую картинку", command=self.open_marked_original).pack(fill="x", padx=10, pady=3)
        ttk.Button(side, text="Открыть HTML overlay", command=self.open_overlay).pack(fill="x", padx=10, pady=3)
        ttk.Button(side, text="Открыть HTML до/после", command=self.open_before_after).pack(fill="x", padx=10, pady=3)
        ttk.Button(side, text="Открыть Roboflow export", command=self.open_roboflow_export).pack(fill="x", padx=10, pady=3)

    def _reset_result_zoom_and_refresh(self) -> None:
        self.result_zoom = 1.0
        self.result_pan_x = 0.0
        self.result_pan_y = 0.0
        self._schedule_result_refresh(delay=30)

    def _result_image_size(self) -> Tuple[int, int]:
        if self._result_pil is not None:
            return self._result_pil.size
        return (1, 1)

    def _result_base_scale(self) -> float:
        w, h = self._result_image_size()
        cw = max(10, self.result_canvas.winfo_width())
        ch = max(10, self.result_canvas.winfo_height())
        return min(cw / float(w), ch / float(h), 1.0)

    def _result_mousewheel(self, event: tk.Event) -> str:
        try:
            cw = max(10, self.result_canvas.winfo_width())
            ch = max(10, self.result_canvas.winfo_height())
            w, h = self._result_image_size()
            base = self._result_base_scale()
            old_zoom = float(self.result_zoom)
            old_scale = base * old_zoom
            old_ox = (cw - w * old_scale) / 2.0 + self.result_pan_x
            old_oy = (ch - h * old_scale) / 2.0 + self.result_pan_y
            img_x = (event.x - old_ox) / max(old_scale, 1e-9)
            img_y = (event.y - old_oy) / max(old_scale, 1e-9)
            direction = 1
            if hasattr(event, "delta") and event.delta:
                direction = 1 if event.delta > 0 else -1
            elif getattr(event, "num", None) == 5:
                direction = -1
            factor = 1.18 if direction > 0 else 1 / 1.18
            new_zoom = max(1.0, min(6.0, old_zoom * factor))
            self.result_zoom = new_zoom
            new_scale = base * new_zoom
            self.result_pan_x = event.x - img_x * new_scale - (cw - w * new_scale) / 2.0
            self.result_pan_y = event.y - img_y * new_scale - (ch - h * new_scale) / 2.0
            self._schedule_result_refresh(delay=20)
        except Exception:
            pass
        return "break"

    def _result_pan_begin(self, event: tk.Event) -> Optional[str]:
        if event.num == 1 and not self._space_down:
            return None
        self._result_pan_start = (event.x, event.y, self.result_pan_x, self.result_pan_y)
        return "break"

    def _result_pan_move(self, event: tk.Event) -> str:
        if not self._result_pan_start:
            return "break"
        x0, y0, px0, py0 = self._result_pan_start
        self.result_pan_x = px0 + (event.x - x0)
        self.result_pan_y = py0 + (event.y - y0)
        self._schedule_result_refresh(delay=20)
        return "break"

    def _result_b1_motion(self, event: tk.Event) -> Optional[str]:
        if self._space_down and self._result_pan_start:
            return self._result_pan_move(event)
        return None

    def _event_to_image_xy(self, event: tk.Event) -> Optional[Tuple[float, float]]:
        scale, ox, oy, dw, dh = self.result_display
        if dw <= 0 or dh <= 0:
            return None
        x = (event.x - ox) / max(scale, 1e-9)
        y = (event.y - oy) / max(scale, 1e-9)
        if x < 0 or y < 0 or x > dw / max(scale, 1e-9) or y > dh / max(scale, 1e-9):
            return None
        return float(x), float(y)

    def _hide_tooltip(self) -> None:
        if self._tooltip_win is not None:
            try:
                self._tooltip_win.destroy()
            except Exception:
                pass
            self._tooltip_win = None

    def _show_tooltip(self, event: tk.Event, lines: List[str]) -> None:
        self._hide_tooltip()
        self._tooltip_win = tw = tk.Toplevel(self)
        tw.wm_overrideredirect(True)
        tw.wm_attributes("-topmost", True)
        text = "\n".join(lines)
        lbl = tk.Label(
            tw,
            text=text,
            justify="left",
            background="#ffffe8",
            foreground="#111",
            relief="solid",
            borderwidth=1,
            padx=8,
            pady=6,
            font=("TkDefaultFont", 10),
        )
        lbl.pack()
        x = event.x_root + 14
        y = event.y_root + 14
        tw.wm_geometry(f"+{x}+{y}")

    def _hit_result_annotation(self, img_xy: Tuple[float, float]) -> Optional[dict]:
        x, y = img_xy
        for item in reversed(self._result_annotations_in_source()):
            poly = [(float(p[0]), float(p[1])) for p in item.get("_source_polygon", [])]
            if len(poly) >= 3 and point_in_polygon(x, y, poly):
                return item
        return None

    def _result_motion(self, event: tk.Event) -> None:
        img_xy = self._event_to_image_xy(event)
        hover_idx: Optional[int] = None
        hover_item: Optional[dict] = None
        if img_xy is not None:
            hover_item = self._hit_result_annotation(img_xy)
            if hover_item is not None:
                hover_idx = int(hover_item.get("_idx", 0))
        if hover_idx != self._result_hover_idx:
            self._result_hover_idx = hover_idx
            self._draw_result_hover_overlay()
        if hover_item is not None:
            label = hover_item.get("label_ru") or CLASS_LABELS.get(hover_item.get("class", ""), "")
            comment = (hover_item.get("comment") or "").strip()
            lines = [f"{hover_item.get('_idx', '?')}. {label}"]
            if comment:
                lines.append(f"Комментарий: {comment}")
            self._show_tooltip(event, lines)
        else:
            self._hide_tooltip()

    def _result_leave(self, _event: tk.Event) -> None:
        self._result_hover_idx = None
        self._draw_result_hover_overlay()
        self._hide_tooltip()

    def _draw_result_hover_overlay(self) -> None:
        if not hasattr(self, "result_canvas"):
            return
        self.result_canvas.delete("result_hover")
        if not self._result_hover_idx:
            return
        for item in self._result_annotations_in_source():
            if int(item.get("_idx", 0)) != int(self._result_hover_idx):
                continue
            scale, ox, oy, _dw, _dh = self.result_display
            poly = item.get("_source_polygon", [])
            flat: List[float] = []
            for p in poly:
                flat.extend([ox + float(p[0]) * scale, oy + float(p[1]) * scale])
            if len(flat) >= 6:
                cls = item.get("class", "other_artifact")
                color = TK_COLORS.get(cls, "#00aa00")
                self.result_canvas.create_polygon(flat, outline=color, fill="", width=5, tags="result_hover")
            break

    def _result_legend_select(self, _event: tk.Event) -> None:
        sel = self.result_legend_list.curselection()
        if not sel:
            return
        line = self.result_legend_list.get(sel[0])
        try:
            idx = int(line.split(".", 1)[0])
        except ValueError:
            return
        self._focus_result_on_index(idx)

    def _result_legend_motion(self, event: tk.Event) -> None:
        idx_widget = self.result_legend_list.nearest(event.y)
        if idx_widget < 0:
            return
        line = self.result_legend_list.get(idx_widget)
        try:
            idx = int(line.split(".", 1)[0])
        except ValueError:
            return
        if idx != self._result_hover_idx:
            self._result_hover_idx = idx
            self._draw_result_hover_overlay()

    def _focus_result_on_index(self, idx: int) -> None:
        for item in self._result_annotations_in_source():
            if int(item.get("_idx", 0)) != int(idx):
                continue
            poly = [(float(p[0]), float(p[1])) for p in item.get("_source_polygon", [])]
            if len(poly) < 3:
                return
            xs = [p[0] for p in poly]
            ys = [p[1] for p in poly]
            cx = sum(xs) / len(xs)
            cy = sum(ys) / len(ys)
            cw = max(10, self.result_canvas.winfo_width())
            ch = max(10, self.result_canvas.winfo_height())
            w, h = self._result_image_size()
            base = self._result_base_scale()
            scale = base * float(self.result_zoom)
            self.result_pan_x = (cw / 2.0) - cx * scale - (cw - w * scale) / 2.0
            self.result_pan_y = (ch / 2.0) - cy * scale - (ch - h * scale) / 2.0
            self._result_hover_idx = idx
            self._schedule_result_refresh(delay=20)
            return

    def _markup_click(self, event: tk.Event) -> Optional[str]:
        if self._space_down:
            self._set_canvas_cursors(self.CURSOR_HAND_GRAB)
            self._markup_pan_start = (event.x, event.y, self.markup_pan_x, self.markup_pan_y)
            return "break"
        super()._markup_click(event)
        self._mark_dirty()
        return None

    def _markup_b1_motion(self, event: tk.Event) -> Optional[str]:
        if self._space_down and self._markup_pan_start:
            return self._markup_pan_move(event)
        return None

    def _finish_markup_polygon(self) -> None:
        super()._finish_markup_polygon()
        self._mark_dirty()

    def _undo_markup_point(self) -> None:
        super()._undo_markup_point()
        self._mark_dirty()

    def _undo_markup_polygon(self) -> None:
        super()._undo_markup_polygon()
        self._mark_dirty()

    def _clear_markup_all(self) -> None:
        super()._clear_markup_all()
        self._mark_dirty()

    def _update_markup_status_text(self) -> None:
        prefix = "● Есть несохранённые изменения · " if getattr(self, "_markup_dirty", False) else ""
        self.markup_status.set(
            prefix
            + f"Областей: {len(self.embedded_annotations)}. "
            f"Точек: {len(self.current_markup_points)}. "
            f"Масштаб: {self.markup_zoom:.1f}×"
        )

    def _draw_result_labels_on_canvas(self) -> None:
        if not hasattr(self, "result_canvas"):
            return
        self.result_canvas.delete("result_label")
        scale, ox, oy, dw, dh = self.result_display
        for item in self._result_annotations_in_source():
            pts = item.get("_source_polygon", [])
            if not pts:
                continue
            xs = [float(p[0]) for p in pts]
            ys = [float(p[1]) for p in pts]
            cx = sum(xs) / len(xs)
            cy = sum(ys) / len(ys)
            x = ox + cx * scale
            y = oy + cy * scale
            cls = item.get("class", "other_artifact")
            color = TK_COLORS.get(cls, "#00aa00")
            _canvas_draw_index_label(
                self.result_canvas,
                x,
                y,
                str(item.get("_idx", "?")),
                color,
                tags="result_label",
            )
        self._draw_result_hover_overlay()

    def _compose_result_pil_from_source(self):
        if Image is None or cv is None:
            raise RuntimeError("Pillow/OpenCV не установлены.")
        project_path = self._project_json_path()
        if project_path is None:
            raise RuntimeError("Сначала подготовьте выпрямленную пару (вкладка 2).")
        project = json.loads(project_path.read_text(encoding="utf-8"))
        modern_path = Path(str(project.get("modern_image") or ""))
        if not modern_path.exists():
            fallback = Path(self.outdir.get()) / "07_marked_on_original_modern.png"
            if fallback.exists():
                return Image.open(fallback).convert("RGB")  # type: ignore[union-attr]
            raise RuntimeError(f"Не найдено исходное современное фото: {modern_path}")
        self._ensure_annotations_loaded()
        modern_bgr = cv_read(modern_path)
        anns = normalize_annotation_list(list(self.embedded_annotations))
        if anns:
            fb = str(getattr(self, "modern_crop_rect_text", "") or "")
            if not fb:
                fb = modern_crop_rect_from_metadata_near(Path(self.outdir.get()))
            H = H_rect_to_full_modern_from_project(project, fallback_rect_text=fb)
            modern_bgr = draw_polygons_on_image(modern_bgr, anns, transform=H, draw_indices=False)
        return Image.fromarray(cv.cvtColor(modern_bgr, cv.COLOR_BGR2RGB))  # type: ignore[union-attr]

    def _refresh_result_canvas(self) -> None:
        if not hasattr(self, "result_canvas"):
            return
        self._update_result_house_header()
        self._ensure_annotations_loaded()
        if not self.embedded_annotations and not (Path(self.outdir.get()) / "07_marked_on_original_modern.png").exists():
            self._result_pil = None
            self.result_status.set("После сохранения разметки здесь появится итоговая картинка.")
            self._draw_canvas_message(
                self.result_canvas,
                "Пока нет итоговой картинки.\n\nВо вкладке 4 обведите изменения и нажмите "
                "«Сохранить разметку и перейти к результату».",
            )
            self._update_result_legend()
            return
        try:
            if Image is None:
                raise RuntimeError("Pillow не установлен.")
            img = self._compose_result_pil_from_source()
            self._result_pil = img
            cw = max(10, self.result_canvas.winfo_width())
            ch = max(10, self.result_canvas.winfo_height())
            w, h = img.size
            base = min(cw / float(w), ch / float(h), 1.0)
            scale = base * float(self.result_zoom)
            dw = max(1, int(round(w * scale)))
            dh = max(1, int(round(h * scale)))
            ox = int(round((cw - dw) / 2.0 + self.result_pan_x))
            oy = int(round((ch - dh) / 2.0 + self.result_pan_y))
            filt = self._resize_filter_fast()
            disp = img.resize((dw, dh), filt) if img.size != (dw, dh) else img.copy()
            photo = ImageTk.PhotoImage(disp)  # type: ignore[union-attr]
            self._result_photo_ref = photo
            self.result_display = (scale, ox, oy, dw, dh)
            self.result_canvas.delete("all")
            self.result_canvas.create_image(ox, oy, image=photo, anchor="nw", tags="result_img")
            self._draw_result_labels_on_canvas()
            legend_file = Path(self.outdir.get()) / "08_marked_on_original_modern_labeled.png"
            extra = f"\nФайл с легендой снизу: {legend_file}" if legend_file.exists() else ""
            self.result_status.set(f"Итог на полном исходном современном фото.{extra}")
            self._update_result_legend()
        except Exception as exc:
            self.result_status.set(str(exc))
            self._draw_canvas_message(self.result_canvas, str(exc))

    def _update_result_legend(self) -> None:
        if not hasattr(self, "result_legend_list"):
            return
        self._ensure_annotations_loaded()
        self.result_legend_list.delete(0, "end")
        if not self.embedded_annotations:
            self.result_legend_list.insert("end", "Разметки пока нет.")
            return
        for idx, ann in enumerate(self.embedded_annotations, start=1):
            label = ann.get("label_ru") or CLASS_LABELS.get(ann.get("class", "other_artifact"), str(ann.get("class", "")))
            comment = (ann.get("comment") or "").strip()
            line = f"{idx}. {label}"
            if comment:
                line += f" — {comment}"
            self.result_legend_list.insert("end", line)

    def _save_markup_annotations(self) -> None:
        super()._save_markup_annotations()
        self._clear_dirty()


# ---------------------------------------------------------------------------
# v15: отдельная линия — курсор-рука, удаление любой области
# ---------------------------------------------------------------------------

class AppV15(AppV14):
    """v15 — рука при перемещении, список областей с удалением любой."""

    CURSOR_HAND_OPEN = "hand2"
    CURSOR_HAND_GRAB = "hand2"
    CURSOR_DEFAULT = ""

    def _build_ui(self) -> None:
        super()._build_ui()
        self.title(f"Archiview CV {APP_VERSION}")
        self._inject_markup_regions_panel()
        self._bind_markup_pan_release()
        self._log(
            "v15: курсор-рука при пробеле и перетаскивании; в списке «Области» можно удалить любую.\n"
        )

    def _bind_markup_pan_release(self) -> None:
        for ev in ("<ButtonRelease-1>", "<ButtonRelease-2>", "<ButtonRelease-3>"):
            self.markup_canvas.bind(ev, self._markup_pan_end, add="+")
        for ev in ("<ButtonRelease-1>", "<ButtonRelease-2>", "<ButtonRelease-3>"):
            self.result_canvas.bind(ev, self._result_pan_end, add="+")

    def _markup_pan_end(self, _event: tk.Event) -> None:
        self._markup_pan_start = None
        self._sync_hand_cursor()

    def _result_pan_end(self, _event: tk.Event) -> None:
        self._result_pan_start = None
        self._sync_hand_cursor()

    def _sync_hand_cursor(self) -> None:
        if self._space_down:
            self._set_canvas_cursors(self.CURSOR_HAND_OPEN)
        else:
            self._set_canvas_cursors(self.CURSOR_DEFAULT)

    def _on_space_press(self, event: tk.Event) -> Optional[str]:
        if self._widget_accepts_typing(event.widget):
            return None
        self._space_down = True
        self._set_canvas_cursors(self.CURSOR_HAND_OPEN)
        return "break"

    def _on_space_release(self, _event: tk.Event) -> Optional[str]:
        self._space_down = False
        self._set_canvas_cursors(self.CURSOR_DEFAULT)
        return None

    def _markup_pan_begin(self, event: tk.Event) -> str:
        self._set_canvas_cursors(self.CURSOR_HAND_GRAB)
        self._markup_pan_start = (event.x, event.y, self.markup_pan_x, self.markup_pan_y)
        return "break"

    def _result_pan_begin(self, event: tk.Event) -> Optional[str]:
        if event.num == 1 and not self._space_down:
            return None
        self._set_canvas_cursors(self.CURSOR_HAND_GRAB)
        self._result_pan_start = (event.x, event.y, self.result_pan_x, self.result_pan_y)
        return "break"

    def _inject_markup_regions_panel(self) -> None:
        tools = self._markup_tools_inner()
        if tools is None:
            return
        for child in tools.winfo_children():
            info = child.grid_info()
            if info.get("row") == 5:
                child.grid(row=6, column=0, sticky="ew", padx=10, pady=(8, 10))
        box = ttk.LabelFrame(tools, text="Области — выберите номер и удалите")
        box.grid(row=5, column=0, sticky="ew", padx=10, pady=6)
        row = ttk.Frame(box)
        row.pack(fill="x", padx=8, pady=6)
        self.markup_regions_list = tk.Listbox(row, height=6, activestyle="dotbox")
        scroll = ttk.Scrollbar(row, orient="vertical", command=self.markup_regions_list.yview)
        self.markup_regions_list.configure(yscrollcommand=scroll.set)
        self.markup_regions_list.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.markup_regions_list.bind("<<ListboxSelect>>", self._on_markup_region_select)
        ttk.Button(
            box,
            text="Удалить выбранную область",
            command=self._delete_selected_markup_region,
        ).pack(fill="x", padx=8, pady=(0, 8))
        self._refresh_markup_regions_list()

    def _markup_tools_inner(self) -> Optional[tk.Widget]:
        for w in self.tab_markup.winfo_children():
            if isinstance(w, ttk.LabelFrame) and "Классы" in str(w.cget("text")):
                for c in w.winfo_children():
                    if hasattr(c, "inner"):
                        return c.inner  # type: ignore[no-any-return]
        return None

    def _refresh_markup_regions_list(self) -> None:
        if not hasattr(self, "markup_regions_list"):
            return
        self.markup_regions_list.delete(0, "end")
        for idx, ann in enumerate(self.embedded_annotations, start=1):
            label = ann.get("label_ru") or CLASS_LABELS.get(ann.get("class", ""), "")
            comment = (ann.get("comment") or "").strip()
            line = f"{idx}. {label}"
            if comment:
                line += f" — {comment}"
            self.markup_regions_list.insert("end", line)

    def _on_markup_region_select(self, _event: tk.Event) -> None:
        sel = self.markup_regions_list.curselection()
        if not sel:
            return
        self._highlight_markup_region_index(sel[0])

    def _highlight_markup_region_index(self, list_index: int) -> None:
        if list_index < 0 or list_index >= len(self.embedded_annotations):
            return
        self.markup_canvas.delete("markup_highlight")
        ann = self.embedded_annotations[list_index]
        scale, ox, oy, _dw, _dh = self.markup_display
        pts = ann.get("polygon", [])
        if len(pts) < 3:
            return
        flat: List[float] = []
        for p in pts:
            flat.extend([ox + float(p[0]) * scale, oy + float(p[1]) * scale])
        color = TK_COLORS.get(ann.get("class", "added_floor"), "#00aa00")
        self.markup_canvas.create_polygon(flat, outline=color, fill="", width=5, tags="markup_highlight")

    def _delete_selected_markup_region(self) -> None:
        sel = self.markup_regions_list.curselection()
        if not sel:
            messagebox.showinfo("Область не выбрана", "Выберите строку в списке «Области».")
            return
        idx = int(sel[0])
        if idx < 0 or idx >= len(self.embedded_annotations):
            return
        ann = self.embedded_annotations[idx]
        label = ann.get("label_ru") or CLASS_LABELS.get(ann.get("class", ""), "")
        if not messagebox.askyesno("Удалить область", f"Удалить область {idx + 1}: {label}?"):
            return
        del self.embedded_annotations[idx]
        for i, a in enumerate(self.embedded_annotations, start=1):
            a["id"] = i
        self._mark_dirty()
        self.markup_canvas.delete("markup_highlight")
        self._draw_markup_vectors()
        self._refresh_markup_regions_list()
        self._update_markup_status_text()

    def _finish_markup_polygon(self) -> None:
        super()._finish_markup_polygon()
        self._refresh_markup_regions_list()

    def _undo_markup_polygon(self) -> None:
        super()._undo_markup_polygon()
        self._refresh_markup_regions_list()

    def _clear_markup_all(self) -> None:
        super()._clear_markup_all()
        self._refresh_markup_regions_list()

    def _ensure_annotations_loaded(self) -> None:
        super()._ensure_annotations_loaded()
        if hasattr(self, "markup_regions_list"):
            self._refresh_markup_regions_list()


if __name__ == "__main__":
    AppV15().mainloop()
