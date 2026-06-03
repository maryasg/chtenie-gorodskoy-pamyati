#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archiview CV v15 — вкладки «База домов / Фото / Сравнения»."""
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Callable, List, Optional

try:
    from archiview_house_db import HouseDatabaseFrame, HouseRecord, open_system_path
except Exception:
    HouseDatabaseFrame = None  # type: ignore[assignment,misc]
    HouseRecord = None  # type: ignore[assignment,misc]
    open_system_path = None  # type: ignore[assignment,misc]

from archiview_project_model import ComparisonSession, PhotoSource, ProjectStore, ProjectSummary


class ProjectsOverviewPanel(ttk.LabelFrame):
    """Проекты на диске — статистика по дому."""

    def __init__(
        self,
        parent: tk.Widget,
        project_root: Path,
        on_open_project: Callable[[Path], None],
        on_log: Optional[Callable[[str], None]] = None,
    ) -> None:
        super().__init__(parent, text="Проекты на диске (v15)")
        self.project_root = Path(project_root)
        self.on_open_project = on_open_project
        self.on_log = on_log

        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=6)
        ttk.Button(top, text="Обновить список", command=self.refresh).pack(side="left")
        ttk.Button(top, text="Открыть папку проектов", command=self._open_root).pack(side="left", padx=6)

        cols = ("address", "hist", "mod", "cmp", "status", "updated")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=8, selectmode="browse")
        headers = {
            "address": "Адрес / папка",
            "hist": "Ист.",
            "mod": "Совр.",
            "cmp": "Сравн.",
            "status": "Статус",
            "updated": "Обновлено",
        }
        widths = {"address": 280, "hist": 44, "mod": 44, "cmp": 52, "status": 120, "updated": 140}
        for c in cols:
            self.tree.heading(c, text=headers[c])
            self.tree.column(c, width=widths[c], anchor="w" if c == "address" else "center")
        y = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=y.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=(0, 8))
        y.pack(side="right", fill="y", padx=(0, 8), pady=(0, 8))
        self.tree.bind("<Double-1>", lambda _e: self.open_selected())
        btm = ttk.Frame(self)
        btm.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(btm, text="Открыть выбранный дом", command=self.open_selected).pack(side="left")

        self._summaries: List[ProjectSummary] = []
        self.refresh()

    def _open_root(self) -> None:
        self.project_root.mkdir(parents=True, exist_ok=True)
        if open_system_path:
            open_system_path(self.project_root)

    def refresh(self) -> None:
        self.tree.delete(*self.tree.get_children())
        self._summaries = ProjectStore.scan_projects(self.project_root)
        for i, s in enumerate(self._summaries):
            self.tree.insert(
                "",
                "end",
                iid=str(i),
                values=(
                    s.address,
                    s.historical_count,
                    s.modern_count,
                    s.comparison_count,
                    s.status,
                    (s.updated_at or "")[:19].replace("T", " "),
                ),
            )
        if self.on_log:
            self.on_log(f"Найдено проектов на диске: {len(self._summaries)}\n")

    def open_selected(self) -> None:
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Дом не выбран", "Выберите проект в таблице.")
            return
        summary = self._summaries[int(sel[0])]
        self.on_open_project(summary.project_dir)


class CombinedHousesTab(ttk.Frame):
    """0. База домов — Excel/CSV + проекты на диске."""

    def __init__(
        self,
        parent: tk.Widget,
        project_root: Path,
        on_house_from_db: Callable,
        on_open_project_dir: Callable[[Path], None],
        on_log: Optional[Callable[[str], None]] = None,
    ) -> None:
        super().__init__(parent)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        if HouseDatabaseFrame is None:
            ttk.Label(
                self,
                text="Модуль archiview_house_db.py не найден.",
                foreground="red",
            ).grid(row=0, column=0, sticky="nw", padx=12, pady=12)
        else:
            db_wrap = ttk.LabelFrame(self, text="Импорт из Excel / CSV")
            db_wrap.grid(row=0, column=0, sticky="nsew", padx=8, pady=(8, 4))
            db_wrap.rowconfigure(0, weight=1)
            db_wrap.columnconfigure(0, weight=1)
            self.house_db_frame = HouseDatabaseFrame(
                db_wrap,
                project_root=project_root,
                on_house_selected=on_house_from_db,
                on_log=on_log,
            )
            self.house_db_frame.grid(row=0, column=0, sticky="nsew")

        self.overview = ProjectsOverviewPanel(
            self,
            project_root=project_root,
            on_open_project=on_open_project_dir,
            on_log=on_log,
        )
        self.overview.grid(row=1, column=0, sticky="nsew", padx=8, pady=(4, 8))

    def refresh_overview(self) -> None:
        self.overview.refresh()


class PhotosTabFrame(ttk.Frame):
    """1. Фото — исторические и современные источники проекта."""

    def __init__(
        self,
        parent: tk.Widget,
        get_store: Callable[[], Optional[ProjectStore]],
        on_log: Optional[Callable[[str], None]] = None,
    ) -> None:
        super().__init__(parent)
        self.get_store = get_store
        self.on_log = on_log
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(3, weight=1)

        ttk.Label(
            self,
            text="Фото хранятся отдельно и не перезаписывают старые сравнения. "
            "Legacy-папки historical_sources / modern_sources подхватываются автоматически.",
            wraplength=920,
            foreground="#555",
        ).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 6))

        self._build_section(self, 1, "historical", "Исторические фото", self.add_historical_file)
        self._build_section(self, 3, "modern", "Современные фото", self.add_modern_file)

        btm = ttk.Frame(self)
        btm.grid(row=4, column=0, sticky="ew", padx=10, pady=8)
        ttk.Button(btm, text="Обновить списки", command=self.refresh).pack(side="left")

    def _build_section(self, parent, row, kind, title, add_cmd) -> None:
        box = ttk.LabelFrame(parent, text=title)
        box.grid(row=row, column=0, sticky="nsew", padx=10, pady=6)
        box.columnconfigure(0, weight=1)
        box.rowconfigure(1, weight=1)
        actions = ttk.Frame(box)
        actions.grid(row=0, column=0, sticky="ew", padx=8, pady=6)
        ttk.Button(actions, text="Добавить файл…", command=add_cmd).pack(side="left")
        cols = ("id", "year", "source", "rect", "used", "comment")
        tree = ttk.Treeview(box, columns=cols, show="headings", height=6)
        tree.heading("id", text="ID")
        tree.heading("year", text="Год")
        tree.heading("source", text="Источник")
        tree.heading("rect", text="Выпрямлено")
        tree.heading("used", text="Сравнения")
        tree.heading("comment", text="Комментарий")
        for c, w in zip(cols, (80, 70, 120, 80, 160, 220)):
            tree.column(c, width=w, anchor="w")
        tree.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        if kind == "historical":
            self.hist_tree = tree
        else:
            self.mod_tree = tree

    def _require_store(self) -> Optional[ProjectStore]:
        store = self.get_store()
        if store is None:
            messagebox.showinfo(
                "Сначала выберите дом",
                "Откройте дом во вкладке «0. База домов», затем вернитесь сюда.",
            )
        return store

    def add_historical_file(self) -> None:
        store = self._require_store()
        if not store:
            return
        path = filedialog.askopenfilename(
            title="Добавить историческое фото",
            filetypes=[("Изображения", "*.jpg *.jpeg *.png *.tif *.tiff *.webp *.bmp"), ("Все", "*.*")],
        )
        if path:
            photo = store.add_photo_from_file("historical", path)
            self._log(f"Добавлено историческое фото: {photo.photo_id}\n")
            self.refresh()

    def add_modern_file(self) -> None:
        store = self._require_store()
        if not store:
            return
        path = filedialog.askopenfilename(
            title="Добавить современное фото",
            filetypes=[("Изображения", "*.jpg *.jpeg *.png *.tif *.tiff *.webp *.bmp"), ("Все", "*.*")],
        )
        if path:
            photo = store.add_photo_from_file("modern", path)
            self._log(f"Добавлено современное фото: {photo.photo_id}\n")
            self.refresh()

    def _fill_tree(self, tree: ttk.Treeview, photos: List[PhotoSource]) -> None:
        tree.delete(*tree.get_children())
        for p in photos:
            year = ""
            if p.date_from:
                year = str(p.date_from)
                if p.date_to and p.date_to != p.date_from:
                    year += f"–{p.date_to}"
            tree.insert(
                "",
                "end",
                values=(
                    p.photo_id,
                    year or "—",
                    p.source_type,
                    "Да" if p.is_rectified else "Нет",
                    ", ".join(p.used_in_comparisons) or "—",
                    p.quality_notes or p.title,
                ),
            )

    def refresh(self) -> None:
        store = self.get_store()
        if not store:
            self.hist_tree.delete(*self.hist_tree.get_children())
            self.mod_tree.delete(*self.mod_tree.get_children())
            return
        self._fill_tree(self.hist_tree, store.list_photos("historical"))
        self._fill_tree(self.mod_tree, store.list_photos("modern"))

    def _log(self, text: str) -> None:
        if self.on_log:
            self.on_log(text)


class ComparisonsTabFrame(ttk.Frame):
    """2. Сравнения — отдельные сессии, legacy result/ не перезаписывается."""

    def __init__(
        self,
        parent: tk.Widget,
        get_store: Callable[[], Optional[ProjectStore]],
        on_open_comparison: Callable[[ComparisonSession], None],
        on_log: Optional[Callable[[str], None]] = None,
    ) -> None:
        super().__init__(parent)
        self.get_store = get_store
        self.on_open_comparison = on_open_comparison
        self.on_log = on_log
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        ttk.Label(
            self,
            text="Каждое сравнение — отдельная папка. Существующая разметка в result/ сохраняется как cmp_legacy_001.",
            wraplength=920,
            foreground="#555",
        ).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 6))

        cols = ("id", "modern", "historical", "ann", "status", "updated", "title")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=12, selectmode="browse")
        headers = {
            "id": "ID",
            "modern": "Совр. фото",
            "historical": "Ист. фото",
            "ann": "Разметок",
            "status": "Статус",
            "updated": "Обновлено",
            "title": "Название",
        }
        widths = {"id": 110, "modern": 90, "historical": 140, "ann": 70, "status": 110, "updated": 130, "title": 260}
        for c in cols:
            self.tree.heading(c, text=headers[c])
            self.tree.column(c, width=widths[c], anchor="w")
        self.tree.grid(row=1, column=0, sticky="nsew", padx=10, pady=6)
        y = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        y.grid(row=1, column=1, sticky="ns", pady=6)
        self.tree.configure(yscrollcommand=y.set)
        self.tree.bind("<Double-1>", lambda _e: self.open_selected())

        btm = ttk.Frame(self)
        btm.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        ttk.Button(btm, text="Обновить", command=self.refresh).pack(side="left")
        ttk.Button(btm, text="Открыть сравнение", command=self.open_selected).pack(side="left", padx=6)
        ttk.Button(btm, text="Создать новое…", command=self.create_new).pack(side="left", padx=6)
        ttk.Button(btm, text="Дублировать", command=self.duplicate_selected).pack(side="left", padx=6)

        self._items: List[ComparisonSession] = []

    def _require_store(self) -> Optional[ProjectStore]:
        store = self.get_store()
        if store is None:
            messagebox.showinfo("Сначала выберите дом", "Откройте дом во вкладке «0. База домов».")
        return store

    def refresh(self) -> None:
        store = self.get_store()
        self.tree.delete(*self.tree.get_children())
        self._items = []
        if not store:
            return
        self._items = store.list_comparisons()
        for i, c in enumerate(self._items):
            mark = " (legacy)" if c.is_legacy else ""
            self.tree.insert(
                "",
                "end",
                iid=str(i),
                values=(
                    c.comparison_id + mark,
                    c.modern_photo_id or "—",
                    ", ".join(c.historical_photo_ids) or "—",
                    c.annotation_count,
                    c.status,
                    (c.updated_at or "")[:19].replace("T", " "),
                    c.title,
                ),
            )

    def _selected(self) -> Optional[ComparisonSession]:
        sel = self.tree.selection()
        if not sel:
            return None
        return self._items[int(sel[0])]

    def open_selected(self) -> None:
        cmp = self._selected()
        if not cmp:
            messagebox.showwarning("Не выбрано", "Выберите сравнение в таблице.")
            return
        self.on_open_comparison(cmp)

    def create_new(self) -> None:
        store = self._require_store()
        if not store:
            return
        mods = store.list_photos("modern")
        hists = store.list_photos("historical")
        if not mods:
            messagebox.showwarning("Нет фото", "Сначала добавьте современное фото во вкладке «1. Фото».")
            return
        if not hists:
            messagebox.showwarning("Нет фото", "Сначала добавьте историческое фото во вкладке «1. Фото».")
            return
        title = simpledialog.askstring("Новое сравнение", "Название сравнения:", parent=self)
        if title is None:
            return
        cmp = store.create_comparison(
            title=title.strip() or "Новое сравнение",
            modern_photo_id=mods[0].photo_id,
            historical_photo_ids=[hists[0].photo_id],
        )
        self._log(f"Создано сравнение {cmp.comparison_id} (отдельная папка, result/ не тронут).\n")
        self.refresh()
        self.on_open_comparison(cmp)

    def duplicate_selected(self) -> None:
        store = self._require_store()
        cmp = self._selected()
        if not store or not cmp:
            messagebox.showwarning("Не выбрано", "Выберите сравнение для копии.")
            return
        new_cmp = store.duplicate_comparison(cmp.comparison_id)
        self._log(f"Создана копия: {new_cmp.comparison_id}\n")
        self.refresh()

    def _log(self, text: str) -> None:
        if self.on_log:
            self.on_log(text)
