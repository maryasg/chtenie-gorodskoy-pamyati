#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archiview CV v15 — вкладки «База домов / Фото / Сравнения»."""
from __future__ import annotations

import shutil
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Callable, Dict, List, Optional, Tuple

try:
    from PIL import Image, ImageTk
except Exception:
    Image = None  # type: ignore[assignment,misc]
    ImageTk = None  # type: ignore[assignment,misc]

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


class ComparisonPairPickerDialog(tk.Toplevel):
    """Выбор исторического и современного фото для нового сравнения (с превью)."""

    def __init__(self, parent: tk.Widget, store: ProjectStore) -> None:
        super().__init__(parent)
        self.store = store
        self.result: Optional[Tuple[str, str, str, str]] = None
        self.title("Новое сравнение — выбор фото")
        self.geometry("920x620")
        self.minsize(780, 520)
        self._photo_ref: Optional[object] = None
        self._hist_options: List[Dict[str, str]] = []
        self._mod_options: List[Dict[str, str]] = []

        ttk.Label(
            self,
            text="Слева — историческое, справа — современное. Можно выбрать выпрямленное modern из другого сравнения.",
            wraplength=880,
        ).pack(anchor="w", padx=12, pady=(10, 6))

        lists = ttk.Frame(self)
        lists.pack(fill="both", expand=True, padx=12, pady=6)
        lists.columnconfigure(0, weight=1)
        lists.columnconfigure(1, weight=1)
        lists.rowconfigure(0, weight=1)

        hist_box = ttk.LabelFrame(lists, text="Историческое")
        mod_box = ttk.LabelFrame(lists, text="Современное")
        hist_box.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        mod_box.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        hist_box.rowconfigure(0, weight=1)
        mod_box.rowconfigure(0, weight=1)
        hist_box.columnconfigure(0, weight=1)
        mod_box.columnconfigure(0, weight=1)

        self.hist_list = tk.Listbox(hist_box, height=12, exportselection=False)
        self.mod_list = tk.Listbox(mod_box, height=12, exportselection=False)
        self.hist_list.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self.mod_list.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self.hist_list.bind("<<ListboxSelect>>", lambda _e: self._update_preview())
        self.mod_list.bind("<<ListboxSelect>>", lambda _e: self._update_preview())

        preview_box = ttk.LabelFrame(self, text="Превью выбранной пары")
        preview_box.pack(fill="x", padx=12, pady=6)
        self.preview_label = ttk.Label(preview_box, text="Выберите фото в списках", anchor="center")
        self.preview_label.pack(fill="x", padx=8, pady=8)

        btns = ttk.Frame(self)
        btns.pack(anchor="e", padx=12, pady=(0, 12))
        ttk.Button(btns, text="Отмена", command=self._cancel).pack(side="right")
        ttk.Button(btns, text="Создать сравнение", command=self._ok).pack(side="right", padx=8)

        self._fill_options()
        if self._hist_options:
            self.hist_list.selection_set(0)
        if self._mod_options:
            self.mod_list.selection_set(0)
        self._update_preview()
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._cancel)

    def _fill_options(self) -> None:
        self.hist_list.delete(0, "end")
        self.mod_list.delete(0, "end")
        self._hist_options = []
        self._mod_options = []
        for photo in self.store.list_photos("historical"):
            path = self.store.resolve_photo_path(photo)
            if not path:
                continue
            label = photo.title or photo.photo_id
            self._hist_options.append(
                {
                    "photo_id": photo.photo_id,
                    "path": str(path),
                    "label": label,
                    "kind": "original",
                }
            )
            self.hist_list.insert("end", label)
        for photo in self.store.list_photos("modern"):
            path = self.store.resolve_photo_path(photo)
            if not path:
                continue
            label = f"Оригинал: {photo.title or photo.photo_id}"
            self._mod_options.append(
                {
                    "photo_id": photo.photo_id,
                    "path": str(path),
                    "label": label,
                    "kind": "original",
                }
            )
            self.mod_list.insert("end", label)
        for cmp in self.store.list_comparisons():
            work = cmp.work_path(self.store.project_dir)
            rect = work / "04_modern_rectified.png"
            if not rect.exists():
                continue
            suffix = " (legacy)" if cmp.is_legacy else ""
            label = f"Выпрямленное modern — {cmp.comparison_id}{suffix}"
            mod_id = cmp.modern_photo_id or (self.store.list_photos("modern")[0].photo_id if self.store.list_photos("modern") else "")
            self._mod_options.append(
                {
                    "photo_id": mod_id,
                    "path": str(rect),
                    "label": label,
                    "kind": "rectified",
                }
            )
            self.mod_list.insert("end", label)

    def _selected_option(self, listbox: tk.Listbox, options: List[Dict[str, str]]) -> Optional[Dict[str, str]]:
        sel = listbox.curselection()
        if not sel:
            return None
        idx = int(sel[0])
        if 0 <= idx < len(options):
            return options[idx]
        return None

    def _preview_image(self, hist: Dict[str, str], mod: Dict[str, str]) -> None:
        if Image is None or ImageTk is None:
            self.preview_label.configure(
                image="",
                text=f"Историческое:\n{hist['label']}\n\nСовременное:\n{mod['label']}",
            )
            return
        try:
            hi = Image.open(hist["path"]).convert("RGB")
            mo = Image.open(mod["path"]).convert("RGB")
            hi.thumbnail((360, 220))
            mo.thumbnail((360, 220))
            gap = 12
            canvas = Image.new("RGB", (hi.width + mo.width + gap, max(hi.height, mo.height)), (240, 240, 240))
            canvas.paste(hi, (0, 0))
            canvas.paste(mo, (hi.width + gap, 0))
            self._photo_ref = ImageTk.PhotoImage(canvas)
            self.preview_label.configure(image=self._photo_ref, text="")
        except Exception as exc:
            self.preview_label.configure(image="", text=f"Не удалось показать превью: {exc}")

    def _update_preview(self) -> None:
        hist = self._selected_option(self.hist_list, self._hist_options)
        mod = self._selected_option(self.mod_list, self._mod_options)
        if not hist or not mod:
            self.preview_label.configure(image="", text="Выберите оба фото")
            return
        self._preview_image(hist, mod)

    def _ok(self) -> None:
        hist = self._selected_option(self.hist_list, self._hist_options)
        mod = self._selected_option(self.mod_list, self._mod_options)
        if not hist or not mod:
            messagebox.showinfo("Нужны два фото", "Выберите историческое и современное фото.", parent=self)
            return
        self.result = (hist["photo_id"], hist["path"], mod["photo_id"], mod["path"])
        self.grab_release()
        self.destroy()

    def _cancel(self) -> None:
        self.result = None
        self.grab_release()
        self.destroy()


class ComparisonsTabFrame(ttk.Frame):
    """2. Сравнения — отдельные сессии, legacy result/ не перезаписывается."""

    def __init__(
        self,
        parent: tk.Widget,
        get_store: Callable[[], Optional[ProjectStore]],
        on_open_comparison: Callable[[ComparisonSession], None],
        on_log: Optional[Callable[[str], None]] = None,
        on_need_photos: Optional[Callable[[], None]] = None,
        *,
        compact: bool = False,
        tree_height: Optional[int] = None,
    ) -> None:
        super().__init__(parent)
        self.get_store = get_store
        self.on_open_comparison = on_open_comparison
        self.on_log = on_log
        self.on_need_photos = on_need_photos
        self._compact = compact
        self._tree_height = tree_height
        self._items: List[ComparisonSession] = []
        self.hide_legacy = tk.BooleanVar(value=True)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        ttk.Label(
            self,
            text=(
                "У дома одно активное сравнение (★) — с него идут углы, выпрямление и разметка. "
                "Новые сравнения только вручную: «Создать новое…». "
                "cmp_legacy_001 — зеркало старой папки result/; можно скрыть галочкой ниже."
            ),
            wraplength=920,
            foreground="#555",
        ).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 6))

        cols = ("id", "modern", "historical", "ann", "status", "updated", "title")
        if self._tree_height is not None:
            cmp_height = self._tree_height
        else:
            cmp_height = 6 if self._compact else 12
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=cmp_height, selectmode="browse")
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

        filter_row = ttk.Frame(self)
        filter_row.grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 4))
        ttk.Checkbutton(
            filter_row,
            text="Скрыть cmp_legacy_001 и другие legacy (старая папка result/)",
            variable=self.hide_legacy,
            command=self.refresh,
        ).pack(side="left")

        btm = ttk.Frame(self)
        btm.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        ttk.Button(btm, text="Обновить", command=self.refresh).pack(side="left")
        ttk.Button(btm, text="Открыть сравнение", command=self.open_selected).pack(side="left", padx=6)
        ttk.Button(btm, text="Создать новое…", command=self.create_new).pack(side="left", padx=6)
        if self.on_need_photos is not None:
            ttk.Button(btm, text="Добавить фото…", command=self.on_need_photos).pack(side="left", padx=6)
        ttk.Button(btm, text="Дублировать", command=self.duplicate_selected).pack(side="left", padx=6)
        ttk.Button(btm, text="Сделать текущим ★", command=self.make_active).pack(side="left", padx=6)
        ttk.Button(btm, text="Пометить «к удалению»", command=self.mark_discarded).pack(side="left", padx=6)
        ttk.Button(btm, text="Снять пометку", command=self.unmark_discarded).pack(side="left", padx=6)
        ttk.Button(btm, text="Удалить помеченные…", command=self.delete_discarded).pack(side="left", padx=6)

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
        all_items = store.list_comparisons()
        self._items = [c for c in all_items if not (self.hide_legacy.get() and c.is_legacy)]
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
        has_modern = bool(store.list_photos("modern")) or any(
            (c.work_path(store.project_dir) / "04_modern_rectified.png").exists()
            for c in store.list_comparisons()
        )
        if not store.list_photos("historical") or not has_modern:
            messagebox.showinfo(
                "Нужны фото",
                "Сначала добавьте историческое и современное фото на вкладке «1. Источники».\n\n"
                "Для второго сравнения можно выбрать уже выпрямленное modern из другого сравнения.",
            )
            if self.on_need_photos:
                self.on_need_photos()
            return
        title = simpledialog.askstring("Новое сравнение", "Название сравнения:", parent=self)
        if title is None:
            return
        dialog = ComparisonPairPickerDialog(self, store)
        self.wait_window(dialog)
        if not dialog.result:
            return
        hist_id, hist_path, mod_id, mod_path = dialog.result
        hist_photo = store.ensure_photo_from_path(hist_path, "historical")
        if Path(mod_path).name == "04_modern_rectified.png":
            mod_photo = store.ensure_photo_from_path(mod_path, "modern", title=f"rectified_{Path(mod_path).parent.name}")
        else:
            mod_photo = store.ensure_photo_from_path(mod_path, "modern")
        cmp = store.create_comparison(
            title=title.strip() or "Новое сравнение",
            modern_photo_id=mod_photo.photo_id,
            historical_photo_ids=[hist_photo.photo_id],
            historical_source_key=str(Path(hist_path).resolve()),
            modern_source_path=str(Path(mod_path).resolve()),
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
        *,
        compact: bool = False,
        tree_height: Optional[int] = None,
    ) -> None:
        super().__init__(parent, text="Мои проекты")
        self.project_root = Path(project_root)
        self.on_open_project = on_open_project
        self.on_new_project = on_new_project
        self.on_import_excel = on_import_excel
        self.on_projects_deleted = on_projects_deleted
        self.on_log = on_log
        self._compact = compact
        self.columnconfigure(0, weight=1)
        if compact:
            self.rowconfigure(1, weight=0)
        else:
            self.rowconfigure(1, weight=1)

        top = ttk.Frame(self)
        top.grid(row=0, column=0, sticky="ew", padx=8, pady=6)
        ttk.Button(top, text="Открыть", command=self.open_selected).pack(side="left")
        ttk.Button(top, text="Обновить", command=self.refresh).pack(side="left", padx=6)
        ttk.Button(top, text="Новый дом…", command=self.on_new_project).pack(side="left", padx=6)
        ttk.Button(top, text="Импорт Excel/CSV…", command=self.on_import_excel).pack(side="left", padx=6)
        if not compact:
            ttk.Button(top, text="Удалить выбранные…", command=self.delete_selected).pack(side="left", padx=(12, 0))
            ttk.Button(top, text="Удалить без разметки…", command=self.delete_without_markup).pack(side="left", padx=6)

        cols = ("site_id", "name", "address", "folder", "markup", "updated")
        if tree_height is not None:
            panel_tree_height = tree_height
        else:
            panel_tree_height = 3 if compact else 4
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=panel_tree_height, selectmode="extended")
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
        self.tree.grid(row=1, column=0, sticky="nsew" if not compact else "ew", padx=(8, 0), pady=(0, 8))
        y = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        y.grid(row=1, column=1, sticky="ns", pady=(0, 8))
        self.tree.configure(yscrollcommand=y.set)
        self.tree.bind("<Double-1>", lambda _e: self.open_selected())

        self._summaries: List[ProjectSummary] = []
        self.after(0, self.refresh)

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


class HouseWorkflowWizardFrame(ttk.Frame):
    """Вкладка 0: дом, метаданные, сравнения ★."""

    def __init__(
        self,
        parent: tk.Widget,
        project_root: Path,
        get_store: Callable[[], Optional[ProjectStore]],
        on_house_selected: Callable[[Path], None],
        on_comparison_opened: Callable[[ComparisonSession], None],
        on_new_project: Callable[[], None],
        on_import_excel: Callable[[], None],
        on_projects_deleted: Optional[Callable[[List[Path]], None]] = None,
        on_log: Optional[Callable[[str], None]] = None,
        build_house_panel: Optional[Callable[[ttk.Widget], None]] = None,
        on_persist_house: Optional[Callable[[], None]] = None,
        on_need_photos: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(parent)
        self.project_root = Path(project_root)
        self.get_store = get_store
        self.on_house_selected = on_house_selected
        self.on_comparison_opened = on_comparison_opened
        self.on_new_project = on_new_project
        self.on_import_excel = on_import_excel
        self.on_projects_deleted = on_projects_deleted
        self.on_log = on_log
        self.build_house_panel = build_house_panel
        self.on_persist_house = on_persist_house
        self.on_need_photos = on_need_photos
        self._house_label = tk.StringVar(value="Дом не выбран")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self)
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))
        header.columnconfigure(0, weight=1)
        ttk.Label(
            header,
            text="Дом и сравнение ★",
            font=("TkDefaultFont", 12, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="Выберите дом, сохраните данные, создайте или выберите сравнение. Фото и тип пары — на вкладке «1. Источники».",
            wraplength=980,
            foreground="#555",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        self._build_main_page()

    def _build_main_page(self) -> None:
        wrap = ttk.Frame(self)
        wrap.grid(row=1, column=0, sticky="nsew", padx=8, pady=6)
        wrap.columnconfigure(0, weight=1)
        wrap.rowconfigure(0, weight=1)
        wrap.rowconfigure(2, weight=1)

        top_split = ttk.Panedwindow(wrap, orient="horizontal")
        top_split.grid(row=0, column=0, sticky="nsew", padx=4, pady=(0, 6))
        houses_wrap = ttk.Frame(top_split)
        meta_wrap = ttk.LabelFrame(top_split, text="Данные дома")
        top_split.add(houses_wrap, weight=2)
        top_split.add(meta_wrap, weight=3)
        houses_wrap.columnconfigure(0, weight=1)
        houses_wrap.rowconfigure(0, weight=1)
        meta_wrap.columnconfigure(0, weight=1)

        if MyProjectsPanel is not None:
            self.projects_panel = MyProjectsPanel(
                houses_wrap,
                project_root=self.project_root,
                on_open_project=self._house_opened,
                on_new_project=self.on_new_project,
                on_import_excel=self.on_import_excel,
                on_projects_deleted=self.on_projects_deleted,
                on_log=self.on_log,
                tree_height=8,
            )
            self.projects_panel.grid(row=0, column=0, sticky="nsew")
        else:
            self.projects_panel = None

        if self.build_house_panel is not None:
            self.build_house_panel(meta_wrap)
        else:
            ttk.Label(meta_wrap, text="Форма данных дома недоступна.", foreground="#777").pack(
                anchor="w", padx=8, pady=8
            )

        save_row = ttk.Frame(wrap)
        save_row.grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 4))
        ttk.Button(save_row, text="Обновить список домов", command=self.refresh_projects).pack(side="left")
        ttk.Button(save_row, text="Сохранить данные дома", command=self._persist_house).pack(side="left", padx=8)
        ttk.Label(save_row, textvariable=self._house_label, foreground="#333").pack(side="left", padx=12)

        cmp_box = ttk.LabelFrame(wrap, text="Сравнения проекта — ★ = активное (разметка и экспорт)")
        cmp_box.grid(row=2, column=0, sticky="nsew", padx=4, pady=4)
        cmp_box.columnconfigure(0, weight=1)
        cmp_box.rowconfigure(0, weight=1)
        self.comparisons_panel = ComparisonsTabFrame(
            cmp_box,
            get_store=self.get_store,
            on_open_comparison=self._comparison_opened,
            on_log=self.on_log,
            on_need_photos=self.on_need_photos,
            compact=True,
            tree_height=9,
        )
        self.comparisons_panel.grid(row=0, column=0, sticky="nsew")

    def _persist_house(self) -> None:
        if self.on_persist_house:
            self.on_persist_house()

    def refresh_projects(self) -> None:
        if self.projects_panel is not None:
            self.projects_panel.refresh()

    def refresh_comparisons(self) -> None:
        if hasattr(self, "comparisons_panel"):
            self.comparisons_panel.refresh()

    def _house_opened(self, path: Path) -> None:
        self.on_house_selected(path)
        self.refresh_comparisons()
        if self.on_persist_house:
            self.on_persist_house()

    def _comparison_opened(self, comparison: ComparisonSession) -> None:
        self.on_comparison_opened(comparison)

    def refresh_summary(
        self,
        *,
        house_text: str = "",
        comparison_text: str = "",
        work_dir: str = "",
        historical_path: str = "",
        modern_path: str = "",
    ) -> None:
        if house_text:
            self._house_label.set(house_text)

    def show_step(self, step: int = 1) -> None:
        """Совместимость: одна страница, только обновить списки."""
        self.refresh_projects()
        self.refresh_comparisons()
