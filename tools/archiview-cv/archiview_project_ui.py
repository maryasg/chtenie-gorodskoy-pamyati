#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archiview CV v15 — вкладки «База домов / Фото / Сравнения»."""
from __future__ import annotations

import shutil
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Callable, Dict, List, Optional

try:
    from archiview_house_db import HouseDatabaseFrame, HouseRecord, open_system_path
except Exception:
    HouseDatabaseFrame = None  # type: ignore[assignment,misc]
    HouseRecord = None  # type: ignore[assignment,misc]
    open_system_path = None  # type: ignore[assignment,misc]

from archiview_project_model import (
    ComparisonSession,
    PhotoSource,
    ProjectStore,
    ProjectSummary,
    comparison_status_label,
)


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
        on_photo_added: Optional[Callable[[PhotoSource], None]] = None,
        on_log: Optional[Callable[[str], None]] = None,
    ) -> None:
        super().__init__(parent)
        self.get_store = get_store
        self.on_photo_added = on_photo_added
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
            if self.on_photo_added:
                self.on_photo_added(photo)
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
            if self.on_photo_added:
                self.on_photo_added(photo)
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
            text=(
                "У дома одно активное сравнение (★) — с него идут углы, выпрямление и разметка. "
                "Старую папку result/ не трогаем (cmp_legacy_001). Лишние cmp_XXX можно пометить «К удалению» и удалить."
            ),
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
        ttk.Button(btm, text="Сделать текущим ★", command=self.make_active).pack(side="left", padx=6)
        ttk.Button(btm, text="Пометить «к удалению»", command=self.mark_discarded).pack(side="left", padx=6)
        ttk.Button(btm, text="Снять пометку", command=self.unmark_discarded).pack(side="left", padx=6)
        ttk.Button(btm, text="Удалить помеченные…", command=self.delete_discarded).pack(side="left", padx=6)

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
        store.refresh_comparison_stats()
        self._items = store.list_comparisons()
        active = store.active_comparison_id
        for i, c in enumerate(self._items):
            prefix = "★ " if c.comparison_id == active else ""
            suffix = " (legacy)" if c.is_legacy else ""
            self.tree.insert(
                "",
                "end",
                iid=str(i),
                values=(
                    prefix + c.comparison_id + suffix,
                    c.modern_photo_id or "—",
                    ", ".join(c.historical_photo_ids) or "—",
                    c.annotation_count,
                    comparison_status_label(c.status),
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

    def make_active(self) -> None:
        store = self._require_store()
        cmp = self._selected()
        if not store or not cmp:
            messagebox.showwarning("Не выбрано", "Выберите сравнение в таблице.")
            return
        if cmp.status == "discarded":
            messagebox.showwarning("Нельзя", "Сначала снимите пометку «К удалению».")
            return
        try:
            store.set_active_comparison(cmp.comparison_id)
        except ValueError:
            messagebox.showwarning("Нельзя", "Это сравнение помечено к удалению.")
            return
        self._log(f"Текущее сравнение: {cmp.comparison_id} (вкладки 2–5 работают с его папкой).\n")
        self.refresh()
        self.on_open_comparison(cmp)

    def mark_discarded(self) -> None:
        store = self._require_store()
        cmp = self._selected()
        if not store or not cmp:
            messagebox.showwarning("Не выбрано", "Выберите сравнение.")
            return
        if cmp.is_legacy:
            messagebox.showwarning("Защищено", "Старую разметку в result/ (legacy) удалять нельзя.")
            return
        if cmp.annotation_count > 0:
            if not messagebox.askyesno(
                "Есть разметка",
                f"В {cmp.comparison_id} уже {cmp.annotation_count} зон разметки.\n"
                "Всё равно пометить «К удалению»?",
                parent=self,
            ):
                return
        store.set_comparison_status(cmp.comparison_id, "discarded")
        self._log(f"Помечено к удалению: {cmp.comparison_id}\n")
        self.refresh()

    def unmark_discarded(self) -> None:
        store = self._require_store()
        cmp = self._selected()
        if not store or not cmp:
            messagebox.showwarning("Не выбрано", "Выберите сравнение.")
            return
        if cmp.status != "discarded":
            messagebox.showinfo("Не помечено", "Статус не «К удалению».")
            return
        store.set_comparison_status(cmp.comparison_id, "draft")
        self._log(f"Пометка снята: {cmp.comparison_id}\n")
        self.refresh()

    def delete_discarded(self) -> None:
        store = self._require_store()
        if not store:
            return
        doomed = [c for c in store.list_comparisons() if c.status == "discarded" and not c.is_legacy]
        if not doomed:
            messagebox.showinfo("Нет помеченных", "Сначала пометьте лишние сравнения «К удалению».")
            return
        names = ", ".join(c.comparison_id for c in doomed)
        if not messagebox.askyesno(
            "Удалить папки",
            f"Безвозвратно удалить {len(doomed)} сравнение(й) и их папки?\n{names}",
            parent=self,
        ):
            return
        for c in doomed:
            try:
                store.delete_comparison(c.comparison_id)
                self._log(f"Удалено: {c.comparison_id}\n")
            except ValueError as exc:
                self._log(f"Не удалось удалить {c.comparison_id}: {exc}\n")
        self.refresh()

    def _log(self, text: str) -> None:
        if self.on_log:
            self.on_log(text)


class MyProjectsPanel(ttk.LabelFrame):
    """Список проектов на диске — на вкладке «Источники»."""

    PROTECTED_FOLDERS = frozenset({"new_house_project", "house_project"})

    def __init__(
        self,
        parent: tk.Widget,
        project_root: Path,
        on_open_project: Callable[[Path], None],
        on_new_project: Callable[[], None],
        on_import_excel: Callable[[], None],
        on_projects_deleted: Optional[Callable[[List[Path]], None]] = None,
        on_log: Optional[Callable[[str], None]] = None,
    ) -> None:
        super().__init__(parent, text="Мои проекты")
        self.project_root = Path(project_root)
        self.on_open_project = on_open_project
        self.on_new_project = on_new_project
        self.on_import_excel = on_import_excel
        self.on_projects_deleted = on_projects_deleted
        self.on_log = on_log
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        top = ttk.Frame(self)
        top.grid(row=0, column=0, sticky="ew", padx=8, pady=6)
        ttk.Button(top, text="Открыть", command=self.open_selected).pack(side="left")
        ttk.Button(top, text="Обновить", command=self.refresh).pack(side="left", padx=6)
        ttk.Button(top, text="Новый дом…", command=self.on_new_project).pack(side="left", padx=6)
        ttk.Button(top, text="Импорт Excel/CSV…", command=self.on_import_excel).pack(side="left", padx=6)
        ttk.Button(top, text="Удалить выбранные…", command=self.delete_selected).pack(side="left", padx=(12, 0))
        ttk.Button(top, text="Удалить без разметки…", command=self.delete_without_markup).pack(side="left", padx=6)

        cols = ("site_id", "name", "address", "folder", "markup", "updated")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=4, selectmode="extended")
        self.tree.heading("site_id", text="Код сайта")
        self.tree.heading("name", text="Название дома")
        self.tree.heading("address", text="Адрес")
        self.tree.heading("folder", text="Папка")
        self.tree.heading("markup", text="Разметка")
        self.tree.heading("updated", text="Обновлено")
        self.tree.column("site_id", width=90, anchor="center")
        self.tree.column("name", width=160, anchor="w")
        self.tree.column("address", width=220, anchor="w")
        self.tree.column("folder", width=140, anchor="w")
        self.tree.column("markup", width=70, anchor="center")
        self.tree.column("updated", width=110, anchor="center")
        self.tree.grid(row=1, column=0, sticky="nsew", padx=(8, 0), pady=(0, 8))
        y = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        y.grid(row=1, column=1, sticky="ns", pady=(0, 8))
        self.tree.configure(yscrollcommand=y.set)
        self.tree.bind("<Double-1>", lambda _e: self.open_selected())

        self._summaries: List[ProjectSummary] = []

    def refresh(self) -> None:
        self.tree.delete(*self.tree.get_children())
        self._summaries = ProjectStore.scan_projects(self.project_root)
        seen_codes: Dict[str, str] = {}
        dup_lines: List[str] = []
        for s in self._summaries:
            code = (s.site_card_id or "").strip().upper()
            if not code:
                continue
            folder = s.project_dir.name
            if code in seen_codes and seen_codes[code] != folder:
                dup_lines.append(f"  {code}: «{seen_codes[code]}» и «{folder}»")
            else:
                seen_codes[code] = folder
        for i, s in enumerate(self._summaries):
            site_id = s.site_card_id or "—"
            name = s.display_title
            address = s.address if s.address not in (s.project_dir.name, s.project_id, name) else "—"
            markup = "Да" if s.has_markup else "—"
            self.tree.insert(
                "",
                "end",
                iid=str(i),
                values=(
                    site_id,
                    name,
                    address,
                    s.project_dir.name,
                    markup,
                    (s.updated_at or "")[:19].replace("T", " "),
                ),
            )
        if self.on_log:
            self.on_log(f"Найдено проектов: {len(self._summaries)}\n")
            if dup_lines:
                self.on_log(
                    "Внимание: один код сайта в нескольких папках (лишние можно удалить):\n"
                    + "\n".join(dup_lines)
                    + "\n"
                )

    def select_by_folder(self, folder_name: str) -> None:
        for i, s in enumerate(self._summaries):
            if s.project_dir.name == folder_name:
                iid = str(i)
                self.tree.selection_set(iid)
                self.tree.focus(iid)
                self.tree.see(iid)
                return

    def open_selected(self) -> None:
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Проект не выбран", "Выберите дом в таблице или дважды щёлкните по строке.")
            return
        summary = self._summaries[int(sel[0])]
        self.on_open_project(summary.project_dir)

    def _selected_summaries(self) -> List[ProjectSummary]:
        sel = self.tree.selection()
        if not sel:
            return []
        out: List[ProjectSummary] = []
        for item in sel:
            idx = int(item)
            if 0 <= idx < len(self._summaries):
                out.append(self._summaries[idx])
        return out

    def _delete_summaries(self, summaries: List[ProjectSummary], *, prompt: str) -> None:
        if not summaries:
            messagebox.showinfo("Ничего не выбрано", "Выберите один или несколько домов в таблице (Ctrl+клик).")
            return
        lines = []
        blocked = []
        to_delete: List[ProjectSummary] = []
        for s in summaries:
            if s.project_dir.name in self.PROTECTED_FOLDERS:
                blocked.append(s.project_dir.name)
                continue
            mark = " [есть разметка!]" if s.has_markup else ""
            lines.append(f"• {s.project_dir.name}{mark}")
            to_delete.append(s)
        if blocked:
            messagebox.showwarning(
                "Служебные папки",
                "Папки new_house_project и house_project не удаляются.\n\n" + "\n".join(blocked),
            )
        if not to_delete:
            return
        text = prompt + "\n\n" + "\n".join(lines[:20])
        if len(lines) > 20:
            text += f"\n… и ещё {len(lines) - 20}"
        text += "\n\nПапки будут удалены с диска без корзины."
        if not messagebox.askyesno("Подтвердите удаление", text):
            return
        deleted: List[Path] = []
        errors: List[str] = []
        for s in to_delete:
            try:
                shutil.rmtree(s.project_dir)
                deleted.append(s.project_dir)
            except Exception as exc:
                errors.append(f"{s.project_dir.name}: {exc}")
        if deleted and self.on_log:
            self.on_log(f"Удалено проектов: {len(deleted)}\n")
        if errors:
            messagebox.showerror("Часть папок не удалена", "\n".join(errors))
        elif deleted:
            messagebox.showinfo("Готово", f"Удалено папок: {len(deleted)}")
        self.refresh()
        if deleted and self.on_projects_deleted:
            self.on_projects_deleted(deleted)

    def delete_selected(self) -> None:
        self._delete_summaries(
            self._selected_summaries(),
            prompt="Удалить выбранные проекты?",
        )

    def delete_without_markup(self) -> None:
        empty = [s for s in self._summaries if not s.has_markup and s.project_dir.name not in self.PROTECTED_FOLDERS]
        if not empty:
            messagebox.showinfo("Нечего удалять", "Нет проектов без разметки (или только служебные папки).")
            return
        names = ", ".join(s.project_dir.name for s in empty[:8])
        extra = f" и ещё {len(empty) - 8}" if len(empty) > 8 else ""
        if not messagebox.askyesno(
            "Удалить экспериментальные?",
            f"Найдено проектов без разметки: {len(empty)}.\n{names}{extra}\n\nУдалить все такие папки?",
        ):
            return
        self._delete_summaries(empty, prompt="Удалить все проекты без разметки?")
