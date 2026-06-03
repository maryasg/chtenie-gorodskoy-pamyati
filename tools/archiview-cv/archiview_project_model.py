#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archiview CV v15 — модель проекта дома (много фото, много сравнений).

Первый проход: хранение и миграция legacy-папок без ломания result/.
Композиты (composites/) — только заготовка каталогов.
"""
from __future__ import annotations

import json
import re
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

SCHEMA_VERSION = "v15.1"

COMPARISON_STATUSES = (
    "draft",
    "reviewed",
    "ready_for_site",
    "published",
    "needs_update",
    "archived",
)

PHOTO_KINDS = ("historical", "modern")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def safe_id(prefix: str, existing: Sequence[str]) -> str:
    nums: List[int] = []
    pat = re.compile(rf"^{re.escape(prefix)}_(\d+)$")
    for item in existing:
        m = pat.match(str(item))
        if m:
            nums.append(int(m.group(1)))
    n = max(nums, default=0) + 1
    return f"{prefix}_{n:03d}"


@dataclass
class HouseProject:
    project_id: str = ""
    address: str = ""
    lat: Optional[float] = None
    lon: Optional[float] = None
    object_name: str = ""
    heritage_status: str = ""
    act_urls: List[str] = field(default_factory=list)
    notes: str = ""
    status: str = "draft"
    published: bool = False
    schema_version: str = SCHEMA_VERSION
    created_at: str = ""
    updated_at: str = ""

    def touch(self) -> None:
        if not self.created_at:
            self.created_at = utc_now_iso()
        self.updated_at = utc_now_iso()

    def to_json(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "HouseProject":
        known = set(cls.__dataclass_fields__.keys())  # type: ignore[attr-defined]
        kwargs = {k: data[k] for k in known if k in data}
        hp = cls(**kwargs)
        if isinstance(data.get("act_urls"), list):
            hp.act_urls = [str(x) for x in data["act_urls"]]
        return hp


@dataclass
class PhotoSource:
    photo_id: str
    kind: str
    title: str = ""
    date_from: Optional[int] = None
    date_to: Optional[int] = None
    source_type: str = "file"
    source_url: str = ""
    license: str = ""
    author: str = ""
    original_path: str = ""
    preview_path: str = ""
    rectified_path: str = ""
    points_path: str = ""
    is_rectified: bool = False
    quality_notes: str = ""
    created_at: str = ""
    updated_at: str = ""
    used_in_comparisons: List[str] = field(default_factory=list)

    def touch(self) -> None:
        if not self.created_at:
            self.created_at = utc_now_iso()
        self.updated_at = utc_now_iso()

    def folder(self, project_dir: Path) -> Path:
        sub = "historical" if self.kind == "historical" else "modern"
        return project_dir / "sources" / sub / self.photo_id

    def to_json(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "PhotoSource":
        known = set(cls.__dataclass_fields__.keys())  # type: ignore[attr-defined]
        kwargs = {k: data[k] for k in known if k in data}
        photo = cls(**kwargs)
        uic = data.get("used_in_comparisons")
        if isinstance(uic, list):
            photo.used_in_comparisons = [str(x) for x in uic]
        return photo


@dataclass
class ComparisonSession:
    comparison_id: str
    title: str = ""
    modern_photo_id: str = ""
    historical_photo_ids: List[str] = field(default_factory=list)
    active_historical_photo_id: str = ""
    overlay_settings: Dict[str, Any] = field(default_factory=dict)
    annotation_count: int = 0
    status: str = "draft"
    is_legacy: bool = False
    work_dir: str = "result"
    created_at: str = ""
    updated_at: str = ""

    def touch(self) -> None:
        if not self.created_at:
            self.created_at = utc_now_iso()
        self.updated_at = utc_now_iso()

    def work_path(self, project_dir: Path) -> Path:
        if self.is_legacy or self.work_dir == "result":
            return project_dir / "result"
        return project_dir / "comparisons" / self.comparison_id

    def to_json(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "ComparisonSession":
        known = set(cls.__dataclass_fields__.keys())  # type: ignore[attr-defined]
        kwargs = {k: data[k] for k in known if k in data}
        cmp = cls(**kwargs)
        hids = data.get("historical_photo_ids")
        if isinstance(hids, list):
            cmp.historical_photo_ids = [str(x) for x in hids]
        return cmp


@dataclass
class ProjectSummary:
    project_dir: Path
    project_id: str
    address: str
    historical_count: int
    modern_count: int
    comparison_count: int
    status: str
    updated_at: str
    has_published: bool


class ProjectStore:
    """Загрузка/сохранение v15-структуры проекта дома."""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = Path(project_dir)
        self.house = HouseProject(project_id=self.project_dir.name)
        self.photos: Dict[str, PhotoSource] = {}
        self.comparisons: Dict[str, ComparisonSession] = {}
        self.active_comparison_id: Optional[str] = None

    # ---------------- paths ----------------

    @property
    def house_json(self) -> Path:
        return self.project_dir / "house.json"

    @property
    def legacy_metadata_json(self) -> Path:
        return self.project_dir / "metadata" / "house.json"

    @property
    def photos_index(self) -> Path:
        return self.project_dir / "sources" / "photos_index.json"

    @property
    def comparisons_index(self) -> Path:
        return self.project_dir / "comparisons" / "index.json"

    def comparison_dir(self, comparison_id: str) -> Path:
        return self.project_dir / "comparisons" / comparison_id

    # ---------------- load / save ----------------

    @classmethod
    def load(cls, project_dir: str | Path) -> "ProjectStore":
        store = cls(Path(project_dir))
        store.ensure_v15_layout()
        store._load_all()
        return store

    @classmethod
    def scan_projects(cls, root: str | Path) -> List[ProjectSummary]:
        root = Path(root)
        if not root.exists():
            return []
        summaries: List[ProjectSummary] = []
        for child in sorted(root.iterdir()):
            if not child.is_dir() or child.name.startswith("."):
                continue
            if child.name in ("new_house_project", "house_project"):
                continue
            try:
                store = cls.load(child)
                summaries.append(store.summary())
            except Exception:
                continue
        summaries.sort(key=lambda s: s.updated_at or "", reverse=True)
        return summaries

    def summary(self) -> ProjectSummary:
        hist = len(self.list_photos("historical"))
        mod = len(self.list_photos("modern"))
        published = any(c.status == "published" for c in self.comparisons.values())
        return ProjectSummary(
            project_dir=self.project_dir,
            project_id=self.house.project_id or self.project_dir.name,
            address=self.house.address or self.project_dir.name,
            historical_count=hist,
            modern_count=mod,
            comparison_count=len(self.comparisons),
            status=self.house.status,
            updated_at=self.house.updated_at or "",
            has_published=published,
        )

    def ensure_v15_layout(self) -> None:
        for sub in (
            "sources/historical",
            "sources/modern",
            "comparisons",
            "composites",
            "exports/site",
            "exports/roboflow",
            "history",
            "historical_sources",
            "modern_sources",
            "result",
            "annotations",
        ):
            (self.project_dir / sub).mkdir(parents=True, exist_ok=True)

    def _load_all(self) -> None:
        self._load_house()
        self._load_photos()
        self._migrate_legacy_photos()
        self._load_comparisons()
        self._migrate_legacy_comparison()
        self._sync_photo_usage()
        self.save()

    def _load_house(self) -> None:
        if self.house_json.exists():
            data = json.loads(self.house_json.read_text(encoding="utf-8"))
            self.house = HouseProject.from_json(data)
            return
        if self.legacy_metadata_json.exists():
            data = json.loads(self.legacy_metadata_json.read_text(encoding="utf-8"))
            self.house = HouseProject(
                project_id=self.project_dir.name,
                address=str(data.get("address") or ""),
                object_name=str(data.get("object_name") or ""),
                notes=str(data.get("notes") or ""),
                lat=_parse_float(data.get("lat")),
                lon=_parse_float(data.get("lon")),
            )
            act = str(data.get("act_url") or "")
            if act:
                self.house.act_urls = [act]
            self.house.touch()
            return
        self.house = HouseProject(project_id=self.project_dir.name, address=self.project_dir.name)
        self.house.touch()

    def _load_photos(self) -> None:
        self.photos.clear()
        if self.photos_index.exists():
            data = json.loads(self.photos_index.read_text(encoding="utf-8"))
            for item in data.get("photos", []):
                photo = PhotoSource.from_json(item)
                self.photos[photo.photo_id] = photo
        for kind in PHOTO_KINDS:
            base = self.project_dir / "sources" / kind
            if not base.exists():
                continue
            for folder in sorted(base.iterdir()):
                if not folder.is_dir():
                    continue
                src_json = folder / "source.json"
                if src_json.exists() and folder.name not in self.photos:
                    self.photos[folder.name] = PhotoSource.from_json(
                        json.loads(src_json.read_text(encoding="utf-8"))
                    )

    def _migrate_legacy_photos(self) -> None:
        legacy_map = (
            ("historical", self.project_dir / "historical_sources"),
            ("modern", self.project_dir / "modern_sources"),
        )
        for kind, folder in legacy_map:
            if not folder.exists():
                continue
            existing_paths = {
                str(Path(p.original_path).resolve()).lower()
                for p in self.photos.values()
                if p.kind == kind and p.original_path
            }
            for f in sorted(folder.iterdir()):
                if not f.is_file() or f.suffix.lower() not in {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".bmp"}:
                    continue
                resolved = str(f.resolve()).lower()
                if resolved in existing_paths:
                    continue
                prefix = "hist" if kind == "historical" else "modern"
                photo_id = safe_id(prefix, [p.photo_id for p in self.photos.values() if p.kind == kind])
                photo = PhotoSource(
                    photo_id=photo_id,
                    kind=kind,
                    title=f.stem,
                    source_type="legacy_folder",
                    original_path=str(f),
                    is_rectified=(self.project_dir / "result" / "03_historical_rectified.png").exists()
                    if kind == "historical"
                    else (self.project_dir / "result" / "04_modern_rectified.png").exists(),
                )
                if kind == "historical" and (self.project_dir / "result" / "03_historical_rectified.png").exists():
                    photo.rectified_path = str(self.project_dir / "result" / "03_historical_rectified.png")
                    photo.is_rectified = True
                if kind == "modern" and (self.project_dir / "result" / "04_modern_rectified.png").exists():
                    photo.rectified_path = str(self.project_dir / "result" / "04_modern_rectified.png")
                    photo.is_rectified = True
                photo.touch()
                self.photos[photo_id] = photo

    def _load_comparisons(self) -> None:
        self.comparisons.clear()
        if self.comparisons_index.exists():
            data = json.loads(self.comparisons_index.read_text(encoding="utf-8"))
            for item in data.get("comparisons", []):
                cmp = ComparisonSession.from_json(item)
                self.comparisons[cmp.comparison_id] = cmp
                cmp_json = self.comparison_dir(cmp.comparison_id) / "comparison.json"
                if cmp_json.exists():
                    file_data = json.loads(cmp_json.read_text(encoding="utf-8"))
                    merged = ComparisonSession.from_json({**cmp.to_json(), **file_data})
                    self.comparisons[cmp.comparison_id] = merged
        cmp_root = self.project_dir / "comparisons"
        if cmp_root.exists():
            for folder in sorted(cmp_root.iterdir()):
                if not folder.is_dir() or folder.name.startswith("."):
                    continue
                if folder.name in self.comparisons:
                    continue
                cmp_json = folder / "comparison.json"
                if cmp_json.exists():
                    self.comparisons[folder.name] = ComparisonSession.from_json(
                        json.loads(cmp_json.read_text(encoding="utf-8"))
                    )

    def _migrate_legacy_comparison(self) -> None:
        result = self.project_dir / "result"
        if not result.exists():
            return
        has_legacy = any(c.is_legacy for c in self.comparisons.values())
        if has_legacy:
            return
        markers = (
            "07_marked_on_original_modern.png",
            "05_comparison_for_labeling.png",
            "03_historical_rectified.png",
            "project_v8.json",
        )
        if not any((result / m).exists() for m in markers):
            return
        cmp_id = "cmp_legacy_001"
        if cmp_id in self.comparisons:
            return
        hist_ids = [p.photo_id for p in self.list_photos("historical")]
        mod_ids = [p.photo_id for p in self.list_photos("modern")]
        cmp = ComparisonSession(
            comparison_id=cmp_id,
            title="Legacy: существующая разметка (result/)",
            modern_photo_id=mod_ids[0] if mod_ids else "",
            historical_photo_ids=hist_ids[:1],
            active_historical_photo_id=hist_ids[0] if hist_ids else "",
            status="reviewed",
            is_legacy=True,
            work_dir="result",
        )
        ann_path = result / "annotations" / "manual_annotations.json"
        if not ann_path.exists():
            ann_path = self.project_dir / "annotations" / "manual_annotations.json"
        if ann_path.exists():
            try:
                ann = json.loads(ann_path.read_text(encoding="utf-8"))
                cmp.annotation_count = len(ann.get("annotations", []))
            except Exception:
                pass
        cmp.touch()
        self.comparisons[cmp_id] = cmp
        self.active_comparison_id = cmp_id

    def _sync_photo_usage(self) -> None:
        for photo in self.photos.values():
            photo.used_in_comparisons = []
        for cmp in self.comparisons.values():
            if cmp.modern_photo_id and cmp.modern_photo_id in self.photos:
                self.photos[cmp.modern_photo_id].used_in_comparisons.append(cmp.comparison_id)
            for hid in cmp.historical_photo_ids:
                if hid in self.photos:
                    self.photos[hid].used_in_comparisons.append(cmp.comparison_id)

    def save(self) -> None:
        self.house.project_id = self.house.project_id or self.project_dir.name
        self.house.touch()
        self.house_json.write_text(
            json.dumps(self.house.to_json(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.photos_index.parent.mkdir(parents=True, exist_ok=True)
        self.photos_index.write_text(
            json.dumps(
                {"schema_version": SCHEMA_VERSION, "photos": [p.to_json() for p in self.photos.values()]},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        for photo in self.photos.values():
            folder = photo.folder(self.project_dir)
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "source.json").write_text(
                json.dumps(photo.to_json(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        cmp_items = [c.to_json() for c in self.comparisons.values()]
        self.comparisons_index.parent.mkdir(parents=True, exist_ok=True)
        self.comparisons_index.write_text(
            json.dumps({"schema_version": SCHEMA_VERSION, "comparisons": cmp_items}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        for cmp in self.comparisons.values():
            if cmp.is_legacy:
                continue
            d = self.comparison_dir(cmp.comparison_id)
            d.mkdir(parents=True, exist_ok=True)
            (d / "comparison.json").write_text(
                json.dumps(cmp.to_json(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    # ---------------- API ----------------

    def list_photos(self, kind: Optional[str] = None) -> List[PhotoSource]:
        items = list(self.photos.values())
        if kind:
            items = [p for p in items if p.kind == kind]
        items.sort(key=lambda p: p.photo_id)
        return items

    def list_comparisons(self) -> List[ComparisonSession]:
        return sorted(self.comparisons.values(), key=lambda c: c.comparison_id)

    def get_comparison(self, comparison_id: str) -> Optional[ComparisonSession]:
        return self.comparisons.get(comparison_id)

    def get_active_comparison(self) -> Optional[ComparisonSession]:
        if self.active_comparison_id:
            return self.comparisons.get(self.active_comparison_id)
        items = self.list_comparisons()
        return items[-1] if items else None

    def add_photo_from_file(self, kind: str, src: str | Path, title: str = "", source_type: str = "file") -> PhotoSource:
        src_path = Path(src)
        if not src_path.exists():
            raise FileNotFoundError(src_path)
        prefix = "hist" if kind == "historical" else "modern"
        photo_id = safe_id(prefix, [p.photo_id for p in self.photos.values() if p.kind == kind])
        folder = self.project_dir / "sources" / ("historical" if kind == "historical" else "modern") / photo_id
        folder.mkdir(parents=True, exist_ok=True)
        dest = folder / f"original{src_path.suffix.lower() or '.jpg'}"
        if src_path.resolve() != dest.resolve():
            shutil.copy2(src_path, dest)
        photo = PhotoSource(
            photo_id=photo_id,
            kind=kind,
            title=title or src_path.stem,
            source_type=source_type,
            original_path=str(dest),
            preview_path=str(dest),
        )
        photo.touch()
        self.photos[photo_id] = photo
        self.save()
        return photo

    def create_comparison(
        self,
        title: str,
        modern_photo_id: str,
        historical_photo_ids: List[str],
        *,
        copy_as_new: bool = True,
    ) -> ComparisonSession:
        cmp_id = safe_id("cmp", list(self.comparisons.keys()))
        if not copy_as_new and self.active_comparison_id and self.active_comparison_id in self.comparisons:
            cmp_id = self.active_comparison_id
        active_hist = historical_photo_ids[0] if historical_photo_ids else ""
        cmp = ComparisonSession(
            comparison_id=cmp_id,
            title=title or f"Сравнение {cmp_id}",
            modern_photo_id=modern_photo_id,
            historical_photo_ids=list(historical_photo_ids),
            active_historical_photo_id=active_hist,
            status="draft",
            is_legacy=False,
            work_dir=f"comparisons/{cmp_id}",
        )
        cmp.touch()
        work = cmp.work_path(self.project_dir)
        work.mkdir(parents=True, exist_ok=True)
        self.comparisons[cmp_id] = cmp
        self.active_comparison_id = cmp_id
        self._sync_photo_usage()
        self.save()
        return cmp

    def duplicate_comparison(self, comparison_id: str) -> ComparisonSession:
        src = self.comparisons.get(comparison_id)
        if not src:
            raise KeyError(comparison_id)
        return self.create_comparison(
            title=f"{src.title} (копия)",
            modern_photo_id=src.modern_photo_id,
            historical_photo_ids=list(src.historical_photo_ids),
            copy_as_new=True,
        )

    def set_active_comparison(self, comparison_id: str) -> ComparisonSession:
        if comparison_id not in self.comparisons:
            raise KeyError(comparison_id)
        self.active_comparison_id = comparison_id
        self.save()
        return self.comparisons[comparison_id]

    def work_dir_for_active(self) -> Path:
        cmp = self.get_active_comparison()
        if cmp:
            path = cmp.work_path(self.project_dir)
            path.mkdir(parents=True, exist_ok=True)
            return path
        legacy = self.project_dir / "result"
        legacy.mkdir(parents=True, exist_ok=True)
        return legacy

    def resolve_photo_path(self, photo: PhotoSource) -> Optional[Path]:
        for candidate in (photo.original_path, photo.rectified_path, photo.preview_path):
            if candidate:
                p = Path(candidate)
                if p.exists():
                    return p
        folder = photo.folder(self.project_dir)
        for name in ("original.jpg", "original.jpeg", "original.png"):
            p = folder / name
            if p.exists():
                return p
        return None


def _parse_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(str(value).replace(",", "."))
    except ValueError:
        return None
