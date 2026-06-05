#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archiview CV v15 — модель проекта дома (много фото, много сравнений).

Первый проход: хранение и миграция legacy-папок без ломания result/.
Композиты (composites/) — заготовка каталогов на будущее.
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
    "discarded",
)

COMPARISON_STATUS_LABELS: Dict[str, str] = {
    "draft": "Черновик",
    "reviewed": "Проверено",
    "ready_for_site": "Готово к сайту",
    "published": "На сайте",
    "needs_update": "Нужно обновить",
    "archived": "В архиве",
    "discarded": "К удалению",
}


def comparison_status_label(status: str) -> str:
    return COMPARISON_STATUS_LABELS.get(status, status or "Черновик")

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
    site_card_id: str = ""
    address: str = ""
    lat: Optional[float] = None
    lon: Optional[float] = None
    object_name: str = ""
    heritage_status: str = ""
    act_urls: List[str] = field(default_factory=list)
    notes: str = ""
    status: str = "draft"
    published: bool = False
    project_slug: str = ""
    workflow_steps: Dict[str, str] = field(default_factory=dict)
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
        ws = data.get("workflow_steps")
        if isinstance(ws, dict):
            hp.workflow_steps = {str(k): str(v) for k, v in ws.items()}
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
    historical_source_key: str = ""
    modern_source_path: str = ""
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
    site_card_id: str
    object_name: str
    address: str
    historical_count: int
    modern_count: int
    comparison_count: int
    status: str
    updated_at: str
    has_published: bool
    has_markup: bool = False

    @property
    def display_title(self) -> str:
        if self.object_name.strip():
            return self.object_name.strip()
        if self.site_card_id.strip():
            name = website_display_name(self.site_card_id)
            if name:
                return name
        if self.address.strip() and self.address.strip() not in (self.project_dir.name, self.project_id):
            return self.address.strip()
        return self.project_dir.name


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
        site_card_id = normalize_site_card_id(self.house.site_card_id) or infer_site_card_id(
            self.project_dir,
            self.house.address,
            self.house.object_name,
        )
        return ProjectSummary(
            project_dir=self.project_dir,
            project_id=self.house.project_id or self.project_dir.name,
            site_card_id=site_card_id,
            object_name=self.house.object_name or "",
            address=self.house.address or self.project_dir.name,
            historical_count=hist,
            modern_count=mod,
            comparison_count=len(self.comparisons),
            status=self.house.status,
            updated_at=self.house.updated_at or "",
            has_published=published,
            has_markup=project_has_markup(self.project_dir),
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
        self.active_comparison_id = None
        if self.comparisons_index.exists():
            data = json.loads(self.comparisons_index.read_text(encoding="utf-8"))
            active = data.get("active_comparison_id")
            if isinstance(active, str) and active.strip():
                self.active_comparison_id = active.strip()
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
        self.refresh_comparison_stats()
        if self.active_comparison_id and self.active_comparison_id not in self.comparisons:
            self.active_comparison_id = None

    def refresh_comparison_stats(self) -> None:
        for cmp in self.comparisons.values():
            work = cmp.work_path(self.project_dir)
            ann = work / "annotations" / "manual_annotations.json"
            count = 0
            if ann.exists():
                try:
                    data = json.loads(ann.read_text(encoding="utf-8"))
                    anns = data.get("annotations", [])
                    if isinstance(anns, list):
                        count = len(anns)
                except Exception:
                    pass
            cmp.annotation_count = count

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
            json.dumps(
                {
                    "schema_version": SCHEMA_VERSION,
                    "active_comparison_id": self.active_comparison_id or "",
                    "comparisons": cmp_items,
                },
                ensure_ascii=False,
                indent=2,
            ),
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

    def find_comparison_for_sources(
        self,
        historical_source_key: str = "",
        modern_source_path: str = "",
    ) -> Optional[ComparisonSession]:
        hist_key = str(Path(historical_source_key).resolve()) if historical_source_key else ""
        mod_key = str(Path(modern_source_path).resolve()) if modern_source_path else ""
        for cmp in self.list_comparisons():
            cmp_hist = str(Path(cmp.historical_source_key).resolve()) if cmp.historical_source_key else ""
            cmp_mod = str(Path(cmp.modern_source_path).resolve()) if cmp.modern_source_path else ""
            if hist_key and cmp_hist == hist_key:
                if not mod_key or not cmp_mod or cmp_mod == mod_key:
                    return cmp
            if mod_key and cmp_mod == mod_key and hist_key and cmp_hist == hist_key:
                return cmp
        return None

    def ensure_photo_from_path(self, src: str | Path, kind: str, title: str = "") -> PhotoSource:
        src_path = Path(src)
        resolved = str(src_path.resolve()).lower()
        for photo in self.photos.values():
            if photo.kind != kind:
                continue
            for candidate in (photo.original_path, photo.preview_path, photo.rectified_path):
                if candidate and str(Path(candidate).resolve()).lower() == resolved:
                    return photo
        return self.add_photo_from_file(kind, src_path, title=title or src_path.stem)

    def create_comparison(
        self,
        title: str,
        modern_photo_id: str,
        historical_photo_ids: List[str],
        *,
        copy_as_new: bool = True,
        historical_source_key: str = "",
        modern_source_path: str = "",
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
            historical_source_key=historical_source_key,
            modern_source_path=modern_source_path,
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
        cmp = self.comparisons[comparison_id]
        if cmp.status == "discarded":
            raise ValueError("discarded_comparison")
        self.active_comparison_id = comparison_id
        if cmp.status == "draft":
            cmp.status = "reviewed"
            cmp.touch()
        self.save()
        return cmp

    def set_comparison_status(self, comparison_id: str, status: str) -> ComparisonSession:
        if comparison_id not in self.comparisons:
            raise KeyError(comparison_id)
        if status not in COMPARISON_STATUSES:
            status = "draft"
        cmp = self.comparisons[comparison_id]
        if cmp.is_legacy and status == "discarded":
            raise ValueError("legacy_protected")
        cmp.status = status
        cmp.touch()
        if status == "discarded" and self.active_comparison_id == comparison_id:
            self.active_comparison_id = None
            for other in reversed(self.list_comparisons()):
                if other.comparison_id != comparison_id and other.status != "discarded":
                    self.active_comparison_id = other.comparison_id
                    break
        self.save()
        return cmp

    def delete_comparison(self, comparison_id: str) -> None:
        cmp = self.comparisons.get(comparison_id)
        if not cmp:
            raise KeyError(comparison_id)
        if cmp.is_legacy:
            raise ValueError("legacy_protected")
        if cmp.status != "discarded":
            raise ValueError("not_marked_discarded")
        work = cmp.work_path(self.project_dir)
        if work.exists() and work.is_dir() and not cmp.is_legacy:
            shutil.rmtree(work)
        del self.comparisons[comparison_id]
        if self.active_comparison_id == comparison_id:
            self.active_comparison_id = None
            for other in reversed(self.list_comparisons()):
                if other.status != "discarded":
                    self.active_comparison_id = other.comparison_id
                    break
        self._sync_photo_usage()
        self.save()

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


def _work_dir_has_markup(work_dir: Path) -> bool:
    ann = work_dir / "annotations" / "manual_annotations.json"
    if ann.exists():
        try:
            data = json.loads(ann.read_text(encoding="utf-8"))
            anns = data.get("annotations", [])
            if isinstance(anns, list) and len(anns) > 0:
                return True
        except Exception:
            pass
    return (work_dir / "07_marked_on_original_modern.png").exists()


def project_has_markup(project_dir: Path) -> bool:
    root = Path(project_dir)
    if _work_dir_has_markup(root / "result"):
        return True
    cmp_root = root / "comparisons"
    if cmp_root.exists():
        for folder in cmp_root.iterdir():
            if folder.is_dir() and _work_dir_has_markup(folder):
                return True
    return False


_WEBSITE_BUILDINGS_CACHE: Optional[Dict[str, Dict[str, Any]]] = None


def load_website_buildings_catalog(app_dir: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
    global _WEBSITE_BUILDINGS_CACHE
    if _WEBSITE_BUILDINGS_CACHE is not None:
        return _WEBSITE_BUILDINGS_CACHE
    candidates = []
    if app_dir is not None:
        candidates.append(Path(app_dir) / "website_buildings.json")
    here = Path(__file__).resolve().parent
    candidates.append(here / "website_buildings.json")
    for path in candidates:
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    _WEBSITE_BUILDINGS_CACHE = data
                    return data
            except Exception:
                continue
    _WEBSITE_BUILDINGS_CACHE = {}
    return _WEBSITE_BUILDINGS_CACHE


def website_display_name(site_card_id: str, app_dir: Optional[Path] = None) -> str:
    card = normalize_site_card_id(site_card_id)
    if not card:
        return ""
    entry = load_website_buildings_catalog(app_dir).get(card, {})
    if isinstance(entry, dict):
        return str(entry.get("displayName") or entry.get("name") or "").strip()
    return ""


_SITE_CARD_RE = re.compile(r"MOSCOW_(\d{3})", re.IGNORECASE)


def normalize_site_card_id(value: str) -> str:
    """Только MOSCOW_001 … MOSCOW_999 — не buildingId и не MOSCOW_001_KUMANIN."""
    s = str(value or "").strip().upper()
    if not s:
        return ""
    m = _SITE_CARD_RE.search(s.replace("-", "_"))
    if not m:
        return ""
    return f"MOSCOW_{m.group(1)}"


def _catalog_slug(building_id: str, card_id: str) -> str:
    bid = str(building_id or "").strip().lower()
    cid = str(card_id or "").strip().lower()
    if bid.startswith(f"{cid}_"):
        return bid[len(cid) + 1 :]
    return bid


def _text_matches_catalog(
    *,
    card_id: str,
    entry: Dict[str, Any],
    address: str,
    object_name: str,
    folder_name: str,
) -> bool:
    display = str(entry.get("displayName") or entry.get("name") or "").strip().lower()
    building_id = str(entry.get("buildingId") or "").strip().lower()
    slug = _catalog_slug(building_id, card_id)
    addr_l = str(address or "").lower()
    name_l = str(object_name or "").lower()
    folder_l = str(folder_name or "").lower().replace("-", "_")

    if display:
        if display in addr_l or display in name_l or name_l in display:
            return True
        for chunk in re.split(r"[\s/(),]+", display):
            if len(chunk) >= 5 and chunk in name_l:
                return True
    if slug and len(slug) >= 4:
        if slug in folder_l or slug in name_l.replace(" ", "_"):
            return True
    if building_id and building_id in folder_l.replace(" ", "_"):
        return True
    keywords: Dict[str, List[str]] = {
        "MOSCOW_001": ("куманин", "ордынк", "ардов", "kumanin"),
        "MOSCOW_002": ("тургенев", "читальн", "turgenev"),
        "MOSCOW_003": ("звер", "чистопруд", "zver", "so_zver"),
        "MOSCOW_004": ("кривоколен", "krivokol"),
    }
    for kw in keywords.get(str(card_id).upper(), []):
        if kw in name_l or kw in addr_l or kw in folder_l:
            return True
    return False


def infer_site_card_id(
    project_dir: Path,
    address: str = "",
    object_name: str = "",
    app_dir: Optional[Path] = None,
) -> str:
    """Код карточки сайта MOSCOW_NNN из каталога website_buildings.json."""
    app = app_dir or Path(__file__).resolve().parent
    folder_name = project_dir.name
    stored = ""
    house_json = project_dir / "house.json"
    if house_json.exists():
        try:
            data = json.loads(house_json.read_text(encoding="utf-8"))
            stored = normalize_site_card_id(str(data.get("site_card_id") or ""))
        except Exception:
            stored = ""
    if stored:
        return stored

    catalog = load_website_buildings_catalog(app)
    for card_id, entry in catalog.items():
        cid = normalize_site_card_id(str(card_id))
        if not cid or not isinstance(entry, dict):
            continue
        if _text_matches_catalog(
            card_id=cid,
            entry=entry,
            address=address,
            object_name=object_name,
            folder_name=folder_name,
        ):
            return cid

    folder_u = folder_name.upper()
    m = re.match(r"^(MOSCOW_\d{3})", folder_u)
    if m:
        return m.group(1)
    return ""


_BUILDING_TYPE_WORDS = frozenset(
    {
        "yes",
        "house",
        "residential",
        "commercial",
        "retail",
        "apartments",
        "industrial",
        "garage",
        "school",
        "church",
        "roof",
    }
)

_HOUSE_PART_RE = re.compile(r"^\s*(\d+[\w/\-]*)\s*$", re.IGNORECASE)


def house_number_from_nominatim(addr: Dict[str, Any]) -> str:
    """Номер дома и строение из ответа Nominatim (OSM address)."""
    hn = str(addr.get("house_number") or addr.get("housenumber") or "").strip()
    unit = str(addr.get("unit") or addr.get("addr:unit") or "").strip()
    bld = str(addr.get("building") or "").strip()
    if bld.lower() in _BUILDING_TYPE_WORDS:
        bld = ""
    if hn and unit:
        if unit.startswith(("с", "к", "стр", "/")) and not hn.endswith(unit.lstrip("сск/")):
            return f"{hn}{unit}" if unit[0].isdigit() or unit[0] in "сск/" else f"{hn}, {unit}"
        if unit not in hn:
            return f"{hn}, {unit}"
    if hn and bld and bld not in hn:
        if len(bld) <= 6 and any(ch.isdigit() for ch in bld):
            if bld[0].isdigit() or bld.startswith(("с", "к")):
                return f"{hn}{bld}" if not hn[-1].isalpha() else f"{hn}, {bld}"
    if hn:
        return hn
    if bld and any(ch.isdigit() for ch in bld):
        return bld
    return ""


def osm_tags_to_address_dict(tags: Dict[str, Any]) -> Dict[str, str]:
    """Теги здания OSM (Overpass) → поля как у Nominatim."""
    return {
        "house_number": str(tags.get("addr:housenumber") or tags.get("housenumber") or "").strip(),
        "road": str(
            tags.get("addr:street")
            or tags.get("addr:place")
            or tags.get("addr:road")
            or tags.get("name")
            or ""
        ).strip(),
        "city": str(tags.get("addr:city") or tags.get("addr:state") or "Москва").strip(),
        "unit": str(tags.get("addr:unit") or tags.get("addr:flats") or "").strip(),
        "building": str(tags.get("building:part") or "").strip(),
    }


def format_nominatim_short_address(addr: Dict[str, Any], *, default_city: str = "Москва") -> str:
    city = str(
        addr.get("city")
        or addr.get("town")
        or addr.get("village")
        or addr.get("municipality")
        or addr.get("state")
        or default_city
    ).strip()
    street = str(
        addr.get("road")
        or addr.get("pedestrian")
        or addr.get("footway")
        or addr.get("street")
        or addr.get("residential")
        or ""
    ).strip()
    house = house_number_from_nominatim(addr)
    parts: List[str] = []
    if city:
        parts.append(city)
    if street:
        line = street if not house else f"{street}, {house}"
        parts.append(line)
    elif house:
        parts.append(house)
    return ", ".join(parts)


def _merge_house_fragments(fragments: List[str]) -> str:
    if not fragments:
        return ""
    best = ""
    for frag in fragments:
        f = frag.strip()
        if len(f) > len(best):
            best = f
    return best


def normalize_address_dedupe(address: str) -> str:
    """Один адрес без повторов города/улицы/номера дома."""
    text = " ".join((address or "").split()).strip()
    if not text:
        return ""
    parts = [p.strip() for p in text.replace(";", ",").split(",") if p.strip()]
    unique: List[str] = []
    seen: set[str] = set()
    for part in parts:
        key = part.casefold()
        if key in seen:
            continue
        seen.add(key)
        unique.append(part)
    if not unique:
        return ""
    rebuilt: List[str] = []
    house_buf: List[str] = []
    for part in unique:
        if _HOUSE_PART_RE.match(part) or (part and part[0].isdigit()):
            house_buf.append(part)
            continue
        if house_buf:
            rebuilt.append(_merge_house_fragments(house_buf))
            house_buf = []
        rebuilt.append(part)
    if house_buf:
        rebuilt.append(_merge_house_fragments(house_buf))
    return ", ".join(rebuilt)


def address_location_key(address: str) -> str:
    """Ключ для поиска дублей адреса между папками проектов."""
    norm = normalize_address_dedupe(address).casefold()
    if not norm:
        return ""
    parts = [p.strip() for p in norm.split(",") if p.strip()]
    if parts and parts[0] in ("москва", "moscow", "г москва"):
        parts = parts[1:]
    return ", ".join(parts)


def merge_map_address(existing: str, new_from_map: str) -> str:
    """Адрес с карты + уже введённый номер дома (если клик был по улице)."""
    old = normalize_address_dedupe(existing)
    new = normalize_address_dedupe(new_from_map)
    if not old:
        return new
    if not new:
        return old

    def house_token(text: str) -> str:
        for part in reversed([p.strip() for p in text.split(",") if p.strip()]):
            if _HOUSE_PART_RE.match(part) or (part and part[0].isdigit()):
                return part
        return ""

    def street_key(text: str) -> str:
        parts = [p.strip() for p in text.split(",") if p.strip()]
        for part in parts:
            if not (_HOUSE_PART_RE.match(part) or (part and part[0].isdigit())):
                if part.casefold() not in ("москва", "moscow", "г москва"):
                    return part.casefold()
        return ""

    sk_old = street_key(old)
    sk_new = street_key(new)
    if sk_new and sk_old and sk_new != sk_old:
        return new
    h_old = house_token(old)
    h_new = house_token(new)
    if h_old and not h_new and (not sk_new or sk_new == sk_old or sk_new in sk_old):
        if h_old not in new:
            return normalize_address_dedupe(f"{new}, {h_old}")
        return old
    return new if len(new) >= len(old) else old


try:
    from archiview_house_db import safe_slug
except Exception:

    def safe_slug(text: str, max_len: int = 90) -> str:  # type: ignore[misc]
        s = re.sub(r"[^a-zA-Z0-9]+", "_", str(text or "").strip().lower())
        s = re.sub(r"_+", "_", s).strip("_")
        return (s or "house_project")[:max_len]


def propose_project_slug(object_name: str = "", address: str = "", fallback: str = "house_project") -> str:
    """Имя папки на диске: «дом_со_зверями» или «moscow_chistoprudny_14s3»."""
    name = str(object_name or "").strip()
    if name and name.lower() not in ("дом", "объект", "house"):
        slug = safe_slug(name)
        if slug and slug != "house_project":
            return slug
    addr = str(address or "").strip()
    if addr:
        slug = safe_slug(addr)
        if slug and slug != "house_project":
            return slug
    return safe_slug(fallback)


def next_site_card_id(app_dir: Optional[Path] = None) -> str:
    """Следующий свободный MOSCOW_NNN для нового дома на сайте."""
    catalog = load_website_buildings_catalog(app_dir)
    nums: List[int] = []
    for key in catalog.keys():
        m = re.match(r"MOSCOW_(\d+)", str(key).upper())
        if m:
            nums.append(int(m.group(1)))
    n = max(nums, default=0) + 1
    return f"MOSCOW_{n:03d}"


def propose_site_card_id(
    project_dir: Path,
    address: str = "",
    object_name: str = "",
    app_dir: Optional[Path] = None,
) -> str:
    """Код карточки сайта: из каталога или новый MOSCOW_NNN."""
    existing = infer_site_card_id(project_dir, address, object_name, app_dir)
    if existing:
        return existing
    return next_site_card_id(app_dir)
