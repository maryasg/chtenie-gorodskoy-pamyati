#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KSP articles workflow panel: topics -> generate -> image prompts -> pack."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, scrolledtext, simpledialog, ttk

from content_period import (
    current_year,
    period_slug,
    plan_json_name,
    plan_txt_name,
    resolve_plan_json,
    resolve_plan_txt,
)

ROOT = Path(__file__).resolve().parent
ARTICLES_HINT = Path.home() / "Projects" / "maryasg-articles_KorolevSP"
MONTHS = (
    "январь",
    "февраль",
    "март",
    "апрель",
    "май",
    "июнь",
    "июль",
    "август",
    "сентябрь",
    "октябрь",
    "ноябрь",
    "декабрь",
)
YEARS = [str(y) for y in range(2025, 2036)]


def resolve_work_root() -> Path:
    """Prefer articles project if scripts live there or nearby."""
    if (ROOT / "content_plan").is_dir() and (ROOT / "generate.py").is_file():
        return ROOT
    if ARTICLES_HINT.is_dir() and (ARTICLES_HINT / "generate.py").is_file():
        return ARTICLES_HINT
    if ARTICLES_HINT.is_dir() and (ARTICLES_HINT / "content_plan").is_dir():
        return ARTICLES_HINT
    return ROOT


WORK = resolve_work_root()


def python_bin() -> str:
    venv = WORK / ".venv" / "Scripts" / "python.exe"
    if venv.is_file():
        return str(venv)
    venv_unix = WORK / ".venv" / "bin" / "python"
    if venv_unix.is_file():
        return str(venv_unix)
    return sys.executable


def open_path(path: Path) -> None:
    path = path.resolve()
    if not path.exists():
        messagebox.showerror("Не найдено", f"Нет файла или папки:\n{path}")
        return
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except OSError as exc:
        messagebox.showerror("Ошибка", str(exc))


def plan_json_path(month: str, year: int) -> Path:
    return resolve_plan_json(WORK / "content_plan", month, year)


def plan_txt_path(month: str, year: int) -> Path:
    return resolve_plan_txt(WORK / "content_plan", month, year)


def topics_txt_template(month: str, year: int, count: int = 10) -> str:
    period = period_slug(month, year)
    lines = [
        f"# Темы статей на {month} {year}",
        "#",
        "# КАК РЕДАКТИРОВАТЬ:",
        "# 1. Ниже напишите темы — по одной на строку.",
        "# 2. Сохраните файл: Ctrl+S (в Блокноте: Файл → Сохранить).",
        "# 3. Вернитесь в панель и нажмите:",
        '#    «Готово: сохранить план для генерации»',
        "#",
        f"# Файл плана для генератора после этого будет:",
        f"#   content_plan\\{period}.json",
        f"# Внутри у каждой темы будут поля month={month} и year={year}.",
        "#",
        "# Строки, начинающиеся с #, не считаются темами.",
        "",
    ]
    for i in range(1, count + 1):
        lines.append(f"Тема {i}: напишите заголовок статьи сюда")
    lines.append("")
    return "\n".join(lines)


def parse_topics_txt(text: str) -> list[str]:
    titles: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # Allow "01. Title" or "Тема 1: Title"
        if line[:2].isdigit() and len(line) > 2 and line[2] in ".)：:":
            line = line[3:].strip()
        elif line.lower().startswith("тема ") and ":" in line:
            line = line.split(":", 1)[1].strip()
        if line and not line.startswith("напишите заголовок"):
            titles.append(line)
    return titles


def write_plan_json(month: str, year: int, titles: list[str]) -> Path:
    folder = WORK / "content_plan"
    folder.mkdir(parents=True, exist_ok=True)
    data = [
        {
            "month": month,
            "year": year,
            "number": f"{i:02d}",
            "title": title,
        }
        for i, title in enumerate(titles, start=1)
    ]
    path = folder / plan_json_name(month, year)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


class WorkflowApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Генератор статей КСП — панель шагов")
        self.geometry("840x800")
        self.minsize(700, 640)
        self.configure(bg="#f7f3ec")

        self.month_var = tk.StringVar(value="октябрь")
        self.year_var = tk.StringVar(value=str(current_year()))
        self.month_var.trace_add("write", lambda *_: self._refresh_plan_hint())
        self.year_var.trace_add("write", lambda *_: self._refresh_plan_hint())
        self._build()
        self._refresh_plan_hint()

    def _selected_year(self) -> int:
        try:
            return int(self.year_var.get().strip())
        except ValueError:
            return current_year()

    def _period(self) -> str:
        return period_slug(self.month_var.get().strip(), self._selected_year())
    def _build(self) -> None:
        pad = {"padx": 16, "pady": 6}
        header = tk.Frame(self, bg="#1f4b3a")
        header.pack(fill="x")
        tk.Label(
            header,
            text="Королёвская стоматологическая поликлиника",
            font=("Segoe UI", 14, "bold"),
            fg="#f7f3ec",
            bg="#1f4b3a",
            pady=10,
        ).pack()
        tk.Label(
            header,
            text="Идите сверху вниз. Шаг 1 — сначала создать темы на месяц.",
            font=("Segoe UI", 10),
            fg="#c8e6d8",
            bg="#1f4b3a",
            pady=2,
        ).pack()

        body = tk.Frame(self, bg="#f7f3ec")
        body.pack(fill="both", expand=True, **pad)

        tk.Label(
            body,
            text=f"Рабочая папка (здесь лежат темы и статьи):\n{WORK}",
            font=("Segoe UI", 9),
            fg="#555",
            bg="#f7f3ec",
            justify="left",
            anchor="w",
        ).pack(fill="x", pady=(0, 8))

        month_row = tk.Frame(body, bg="#f7f3ec")
        month_row.pack(fill="x", pady=(0, 6))
        tk.Label(
            month_row,
            text="Месяц:",
            font=("Segoe UI", 10, "bold"),
            bg="#f7f3ec",
        ).pack(side="left")
        ttk.Combobox(
            month_row,
            textvariable=self.month_var,
            values=MONTHS,
            width=12,
            state="readonly",
        ).pack(side="left", padx=6)
        tk.Label(
            month_row,
            text="Год:",
            font=("Segoe UI", 10, "bold"),
            bg="#f7f3ec",
        ).pack(side="left", padx=(12, 0))
        ttk.Combobox(
            month_row,
            textvariable=self.year_var,
            values=YEARS,
            width=6,
            state="readonly",
        ).pack(side="left", padx=6)
        tk.Label(
            month_row,
            text="(можно выбрать другой год)",
            font=("Segoe UI", 9),
            fg="#666",
            bg="#f7f3ec",
        ).pack(side="left")

        self.plan_hint = tk.Label(
            body,
            text="",
            font=("Segoe UI", 9),
            fg="#1f4b3a",
            bg="#e8f2ec",
            justify="left",
            anchor="w",
            padx=10,
            pady=8,
        )
        self.plan_hint.pack(fill="x", pady=(0, 10))

        # --- Step 1 highlighted ---
        step1 = tk.LabelFrame(
            body,
            text="  Шаг 1. Создать темы на НОВЫЙ месяц  ",
            font=("Segoe UI", 11, "bold"),
            bg="#fffdf8",
            fg="#1f4b3a",
            padx=10,
            pady=8,
        )
        step1.pack(fill="x", pady=5)
        tk.Label(
            step1,
            text=(
                "1) Выберите месяц и год сверху → 2) зелёная кнопка → "
                "3) напишите темы → 4) Ctrl+S → 5) «Готово: сохранить план…»"
            ),
            font=("Segoe UI", 9),
            fg="#666",
            bg="#fffdf8",
            wraplength=740,
            justify="left",
            anchor="w",
        ).pack(fill="x")

        big = tk.Frame(step1, bg="#fffdf8")
        big.pack(fill="x", pady=8)
        tk.Button(
            big,
            text="СОЗДАТЬ ТЕМЫ НА НОВЫЙ МЕСЯЦ",
            font=("Segoe UI", 11, "bold"),
            bg="#1f4b3a",
            fg="#ffffff",
            activebackground="#16382c",
            activeforeground="#ffffff",
            relief="flat",
            padx=16,
            pady=10,
            cursor="hand2",
            command=self.create_new_month_topics,
        ).pack(side="left", padx=(0, 8))
        tk.Button(
            big,
            text="Готово: сохранить план для генерации",
            font=("Segoe UI", 10, "bold"),
            bg="#b45309",
            fg="#ffffff",
            activebackground="#92400e",
            activeforeground="#ffffff",
            relief="flat",
            padx=12,
            pady=10,
            cursor="hand2",
            command=self.save_plan_for_generation,
        ).pack(side="left")

        row1 = tk.Frame(step1, bg="#fffdf8")
        row1.pack(fill="x", pady=4)
        ttk.Button(row1, text="Открыть список тем (.txt)", command=self.open_topics_txt).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(row1, text="Открыть план генерации (.json)", command=self.open_plan_json).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(row1, text="Папка content_plan", command=self.open_content_plan).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(row1, text="Пример старых тем", command=self.open_topics_plan).pack(side="left")

        self._step(
            body,
            "2",
            "Проверить KupiAPI (перед генерацией)",
            "Если тест не проходит — статьи через API не создадутся",
            [
                ("Проверить ключ и API", self.run_test_api),
                ("Открыть .env", self.open_env),
            ],
        )
        self._step(
            body,
            "3",
            "Сгенерировать статьи",
            "Берёт ТОЛЬКО файл content_plan\\месяц_год.json (после «Готово: сохранить план…»)",
            [
                ("Сгенерировать весь месяц (без картинок)", self.generate_month),
                ("Сгенерировать одну статью (номер…)", self.generate_one),
                ("Открыть папку output", self.open_output),
            ],
        )
        self._step(
            body,
            "4",
            "Промпты для картинок",
            "TXT для ChatGPT / генератора обложек",
            [
                ("Собрать промпты (build_image_prompts)", self.build_prompts),
                ("Открыть папку image_prompts", self.open_image_prompts),
                ("Шаблон обложки", self.open_cover_template),
            ],
        )
        self._step(
            body,
            "5",
            "Собрать плоские Word-файлы за месяц",
            "статья01_…_ВК.docx, ТГМАКС.docx и картинки",
            [
                ("Собрать плоские файлы", self.pack_month),
            ],
        )
        self._step(
            body,
            "6",
            "Готовые ручные статьи (июнь–сентябрь)",
            "Кликабельный список Word + промпты",
            [
                ("Июнь", lambda: self.open_manual("июнь")),
                ("Июль", lambda: self.open_manual("июль")),
                ("Август", lambda: self.open_manual("август")),
                ("Сентябрь", lambda: self.open_manual("сентябрь")),
            ],
        )

        help_row = tk.Frame(body, bg="#f7f3ec")
        help_row.pack(fill="x", pady=8)
        ttk.Button(help_row, text="Инструкция для печати", command=self.open_print_help).pack(
            side="left", padx=(0, 8)
        )
        ttk.Button(help_row, text="Открыть HTML-подсказку", command=self.open_html_panel).pack(
            side="left"
        )

        tk.Label(body, text="Журнал:", font=("Segoe UI", 9, "bold"), bg="#f7f3ec", anchor="w").pack(
            fill="x"
        )
        self.log = scrolledtext.ScrolledText(body, height=8, font=("Consolas", 9), wrap="word")
        self.log.pack(fill="both", expand=True, pady=(4, 0))
        self._log(f"Панель запущена. Корень инструментов: {ROOT}")
        self._log(f"Рабочая папка: {WORK}")
        if WORK == ROOT and not (ARTICLES_HINT / "generate.py").is_file():
            self._log(
                "Подсказка: запустите СКОПИРОВАТЬ_В_СТАТЬИ.bat, затем ЗАПУСК_ПАНЕЛИ.bat "
                "из папки maryasg-articles_KorolevSP."
            )

    def _refresh_plan_hint(self) -> None:
        month = self.month_var.get().strip()
        year = self._selected_year()
        period = period_slug(month, year)
        txt_name = plan_txt_name(month, year)
        js_name = plan_json_name(month, year)
        resolved_txt = plan_txt_path(month, year)
        resolved_js = plan_json_path(month, year)
        parts = [
            f"Период: {month} {year}  →  ключ {period}",
            f"Список тем (редактируете):  content_plan\\{txt_name}",
            f"План для генерации (читает шаг 3):  content_plan\\{js_name}",
            f"Статьи будут в:  output\\{period}\\",
        ]
        if resolved_txt.is_file():
            parts.append(f"Список тем: есть ({resolved_txt.name})")
        else:
            parts.append("Список тем: ещё нет — нажмите «СОЗДАТЬ ТЕМЫ НА НОВЫЙ МЕСЯЦ»")
        if resolved_js.is_file():
            try:
                data = json.loads(resolved_js.read_text(encoding="utf-8"))
                n = len(data) if isinstance(data, list) else "?"
            except (OSError, json.JSONDecodeError):
                n = "?"
            parts.append(f"План для генерации: есть ({resolved_js.name}, {n} тем)")
        else:
            parts.append("План для генерации: ещё нет — после тем нажмите «Готово: сохранить план…»")
        if hasattr(self, "plan_hint"):
            self.plan_hint.configure(text="\n".join(parts))

    def _step(
        self,
        parent: tk.Widget,
        num: str,
        title: str,
        hint: str,
        buttons: list[tuple[str, object]],
    ) -> None:
        frame = tk.LabelFrame(
            parent,
            text=f"  Шаг {num}. {title}  ",
            font=("Segoe UI", 10, "bold"),
            bg="#fffdf8",
            fg="#1f4b3a",
            padx=8,
            pady=6,
        )
        frame.pack(fill="x", pady=5)
        tk.Label(
            frame,
            text=hint,
            font=("Segoe UI", 9),
            fg="#666",
            bg="#fffdf8",
            anchor="w",
            wraplength=740,
            justify="left",
        ).pack(fill="x")
        row = tk.Frame(frame, bg="#fffdf8")
        row.pack(fill="x", pady=4)
        for label, cmd in buttons:
            ttk.Button(row, text=label, command=cmd).pack(side="left", padx=(0, 6), pady=2)

    def _log(self, text: str) -> None:
        self.log.insert("end", text.rstrip() + "\n")
        self.log.see("end")

    def _run_async(self, title: str, args: list[str], cwd: Path | None = None) -> None:
        cwd = cwd or WORK

        def worker() -> None:
            self._log(f"\n>>> {title}")
            self._log(" ".join(args))
            try:
                proc = subprocess.run(
                    args,
                    cwd=str(cwd),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                if proc.stdout:
                    self._log(proc.stdout)
                if proc.stderr:
                    self._log(proc.stderr)
                if proc.returncode == 0:
                    self._log(f"OK: {title}")
                else:
                    self._log(f"Ошибка (код {proc.returncode}): {title}")
                    self.after(
                        0,
                        lambda: messagebox.showerror(
                            "Ошибка",
                            f"{title}\nКод: {proc.returncode}\nСмотрите журнал внизу.",
                        ),
                    )
            except OSError as exc:
                self._log(str(exc))
                self.after(0, lambda: messagebox.showerror("Ошибка", str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def create_new_month_topics(self) -> None:
        month = self.month_var.get().strip()
        year = self._selected_year()
        period = period_slug(month, year)
        count_raw = simpledialog.askstring(
            "Сколько статей?",
            f"Месяц: {month}\nГод: {year}\n\nСколько тем создать? (обычно 10)",
            initialvalue="10",
            parent=self,
        )
        if count_raw is None:
            return
        try:
            count = max(1, min(30, int(count_raw.strip())))
        except ValueError:
            count = 10

        folder = WORK / "content_plan"
        folder.mkdir(parents=True, exist_ok=True)
        txt = folder / plan_txt_name(month, year)

        if txt.is_file():
            overwrite = messagebox.askyesno(
                "Файл уже есть",
                f"Уже есть список тем:\n{txt}\n\n"
                "Да = создать заново (старое сотрётся)\n"
                "Нет = просто открыть существующий",
            )
            if not overwrite:
                open_path(txt)
                self._refresh_plan_hint()
                return

        txt.write_text(topics_txt_template(month, year, count), encoding="utf-8")
        self._log(f"Создан список тем: {txt}")
        self._refresh_plan_hint()
        messagebox.showinfo(
            "Темы созданы — что делать дальше",
            "Сейчас откроется простой текстовый файл.\n\n"
            f"ГДЕ ОН ЛЕЖИТ:\n{txt}\n\n"
            "ЧТО СДЕЛАТЬ:\n"
            "1. Замените строки «Тема N: …» на свои заголовки\n"
            "   (по одной теме на строку).\n"
            "2. СОХРАНИТЕ: Ctrl+S\n"
            "   (или Файл → Сохранить).\n"
            "3. Вернитесь в ЭТУ панель.\n"
            "4. Нажмите оранжевую кнопку:\n"
            "   «Готово: сохранить план для генерации».\n\n"
            "После этого появится файл для генератора:\n"
            f"{folder / plan_json_name(month, year)}\n"
            f"(месяц={month}, год={year})\n"
            "Его читает шаг 3 «Сгенерировать статьи».\n"
            f"Статьи попадут в output\\{period}\\",
        )
        open_path(txt)

    def save_plan_for_generation(self) -> None:
        month = self.month_var.get().strip()
        year = self._selected_year()
        period = period_slug(month, year)
        txt = plan_txt_path(month, year)
        if not txt.is_file():
            messagebox.showwarning(
                "Сначала создайте темы",
                "Нажмите зелёную кнопку:\n«СОЗДАТЬ ТЕМЫ НА НОВЫЙ МЕСЯЦ»",
            )
            return
        try:
            text = txt.read_text(encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("Ошибка чтения", str(exc))
            return
        titles = parse_topics_txt(text)
        if not titles:
            messagebox.showwarning(
                "Темы пустые",
                f"В файле нет готовых заголовков:\n{txt}\n\n"
                "Напишите темы по одной на строку, сохраните Ctrl+S\n"
                "и нажмите эту кнопку снова.",
            )
            open_path(txt)
            return
        path = write_plan_json(month, year, titles)
        self._log(f"План для генерации ({len(titles)} тем, {period}): {path}")
        self._refresh_plan_hint()
        messagebox.showinfo(
            "План готов для генерации",
            f"Сохранено {len(titles)} тем.\n\n"
            f"КУДА СОХРАНИЛОСЬ (план для генератора):\n{path}\n\n"
            f"В каждой теме: month={month}, year={year}\n"
            f"Папка статей: output\\{period}\\\n\n"
            "ЧТО ДАЛЬШЕ:\n"
            "→ Шаг 2: проверить KupiAPI\n"
            "→ Шаг 3: «Сгенерировать весь месяц»\n\n"
            "Генератор читает именно этот JSON-файл.",
        )
        open_path(path.parent)

    def open_topics_txt(self) -> None:
        month = self.month_var.get().strip()
        year = self._selected_year()
        txt = plan_txt_path(month, year)
        if not txt.is_file():
            messagebox.showinfo(
                "Файла ещё нет",
                "Сначала нажмите:\n«СОЗДАТЬ ТЕМЫ НА НОВЫЙ МЕСЯЦ»",
            )
            return
        open_path(txt)

    def open_plan_json(self) -> None:
        month = self.month_var.get().strip()
        year = self._selected_year()
        path = plan_json_path(month, year)
        if not path.is_file():
            messagebox.showinfo(
                "Плана ещё нет",
                "Сначала отредактируйте темы и нажмите:\n"
                "«Готово: сохранить план для генерации»",
            )
            return
        open_path(path)

    def open_topics_plan(self) -> None:
        candidates = [
            ROOT / "ПЛАН_ТЕМ_ИЮНЬ_ИЮЛЬ_АВГУСТ_СЕНТЯБРЬ.md",
            WORK / "ПЛАН_ТЕМ_ИЮНЬ_ИЮЛЬ_АВГУСТ_СЕНТЯБРЬ.md",
            WORK / "content_plan" / "ПЛАН_ТЕМ.md",
        ]
        for path in candidates:
            if path.is_file():
                open_path(path)
                self._log(f"Открыт пример тем: {path}")
                return
        messagebox.showinfo("Пример тем", "Файл плана-примера не найден.")

    def open_content_plan(self) -> None:
        folder = WORK / "content_plan"
        folder.mkdir(parents=True, exist_ok=True)
        open_path(folder)

    def open_env(self) -> None:
        env = WORK / ".env"
        example = WORK / ".env.example"
        if env.is_file():
            open_path(env)
        elif example.is_file():
            open_path(example)
            messagebox.showinfo(
                ".env",
                "Открыт .env.example.\nСкопируйте его в .env и вставьте ключ KupiAPI.",
            )
        else:
            messagebox.showwarning(".env", f"Нет .env в\n{WORK}")

    def run_test_api(self) -> None:
        bat = WORK / "test_kupiapi.bat"
        py = WORK / "test_kupiapi.py"
        if bat.is_file() and sys.platform.startswith("win"):
            self._run_async("Проверка KupiAPI", ["cmd", "/c", str(bat)], cwd=WORK)
        elif py.is_file():
            self._run_async("Проверка KupiAPI", [python_bin(), str(py)], cwd=WORK)
        else:
            py2 = ROOT / "test_kupiapi.py"
            if py2.is_file():
                self._run_async("Проверка KupiAPI", [python_bin(), str(py2)], cwd=WORK)
            else:
                messagebox.showerror("Нет файла", "Не найден test_kupiapi.py")

    def generate_month(self) -> None:
        month = self.month_var.get().strip()
        year = self._selected_year()
        period = period_slug(month, year)
        plan = plan_json_path(month, year)
        if not plan.is_file():
            messagebox.showwarning(
                "Нет плана для генерации",
                f"Нет файла:\n{plan}\n\n"
                "Сделайте так:\n"
                "1. Выберите месяц и год\n"
                "2. Зелёная кнопка — создать темы\n"
                "3. Написать темы, Ctrl+S\n"
                "4. Оранжевая кнопка — сохранить план для генерации\n"
                "5. Потом снова шаг 3",
            )
            return
        gen = WORK / "generate.py"
        if not gen.is_file():
            gen = ROOT / "generate.py"
        if not gen.is_file():
            messagebox.showerror("Нет generate.py", f"Скопируйте скрипты в\n{ARTICLES_HINT}")
            return
        self._run_async(
            f"Генерация статей: {period}",
            [
                python_bin(),
                str(gen),
                "--plan",
                str(plan),
                "--year",
                str(year),
                "--skip-images",
            ],
            cwd=WORK,
        )

    def generate_one(self) -> None:
        month = self.month_var.get().strip()
        year = self._selected_year()
        plan = plan_json_path(month, year)
        if not plan.is_file():
            messagebox.showwarning(
                "Нет плана",
                f"Нет файла:\n{plan}\n\nСначала шаг 1: создать темы и сохранить план.",
            )
            return
        number = simpledialog.askstring("Номер статьи", "Номер (например 03):", parent=self)
        if not number:
            return
        number = number.strip().zfill(2)
        gen = WORK / "generate.py"
        if not gen.is_file():
            gen = ROOT / "generate.py"
        self._run_async(
            f"Генерация статьи {number}",
            [
                python_bin(),
                str(gen),
                "--plan",
                str(plan),
                "--year",
                str(year),
                "--number",
                number,
                "--skip-images",
            ],
            cwd=WORK,
        )

    def open_output(self) -> None:
        period = self._period()
        path = WORK / "output" / period
        if path.is_dir():
            open_path(path)
        else:
            # legacy month-only folder
            legacy = WORK / "output" / self.month_var.get().strip()
            if legacy.is_dir():
                open_path(legacy)
                return
            out = WORK / "output"
            out.mkdir(parents=True, exist_ok=True)
            open_path(out)

    def build_prompts(self) -> None:
        bat = WORK / "build_image_prompts.bat"
        py = WORK / "build_image_prompts.py"
        if bat.is_file() and sys.platform.startswith("win"):
            self._run_async("Сборка промптов", ["cmd", "/c", str(bat), "--force"], cwd=WORK)
        elif py.is_file():
            self._run_async(
                "Сборка промптов",
                [python_bin(), str(py), "--force"],
                cwd=WORK,
            )
        else:
            py2 = ROOT / "build_image_prompts.py"
            if py2.is_file():
                self._run_async(
                    "Сборка промптов",
                    [python_bin(), str(py2), "--force"],
                    cwd=WORK,
                )
            else:
                messagebox.showerror("Нет файла", "Не найден build_image_prompts.py")

    def open_image_prompts(self) -> None:
        path = WORK / "image_prompts"
        path.mkdir(parents=True, exist_ok=True)
        open_path(path)

    def open_cover_template(self) -> None:
        for base in (WORK, ROOT):
            for name in ("cover_template.txt", "cover_template_title.txt"):
                path = base / "prompts" / name
                if path.is_file():
                    open_path(path)
                    return
        messagebox.showwarning("Шаблон", "Не найден prompts/cover_template.txt")

    def pack_month(self) -> None:
        period = self._period()
        year = self._selected_year()
        bat = WORK / "СОБРАТЬ_ПЛОСКИЕ_ФАЙЛЫ.bat"
        py = WORK / "pack_month.py"
        if bat.is_file() and sys.platform.startswith("win"):
            self._run_async(
                f"Плоские файлы: {period}",
                ["cmd", "/c", str(bat), period],
                cwd=WORK,
            )
        elif py.is_file():
            self._run_async(
                f"Плоские файлы: {period}",
                [python_bin(), str(py), period],
                cwd=WORK,
            )
        else:
            py2 = ROOT / "pack_month.py"
            if py2.is_file():
                self._run_async(
                    f"Плоские файлы: {period}",
                    [python_bin(), str(py2), self.month_var.get().strip(), str(year)],
                    cwd=WORK,
                )
            else:
                messagebox.showerror("Нет файла", "Не найден pack_month.py")

    def open_manual(self, month: str) -> None:
        folder = ROOT / f"ручные_статьи_{month}"
        listing = folder / "СПИСОК_КЛИКАБЕЛЬНЫЙ.html"
        if listing.is_file():
            open_path(listing)
            self._log(f"Открыт список: {listing}")
        elif folder.is_dir():
            open_path(folder)
        else:
            messagebox.showerror("Нет папки", f"Нет:\n{folder}")

    def open_print_help(self) -> None:
        for base in (WORK, ROOT):
            path = base / "ИНСТРУКЦИЯ_ДЛЯ_ПЕЧАТИ.md"
            if path.is_file():
                open_path(path)
                return
        messagebox.showwarning("Инструкция", "Файл ИНСТРУКЦИЯ_ДЛЯ_ПЕЧАТИ.md не найден")

    def open_html_panel(self) -> None:
        path = ROOT / "ПАНЕЛЬ_РАБОТЫ.html"
        if path.is_file():
            open_path(path)
        else:
            messagebox.showwarning("HTML", f"Нет файла:\n{path}")


def main() -> None:
    app = WorkflowApp()
    app.mainloop()


if __name__ == "__main__":
    main()
