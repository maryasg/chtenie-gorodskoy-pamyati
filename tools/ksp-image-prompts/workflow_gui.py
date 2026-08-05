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


def plan_path(month: str) -> Path:
    return WORK / "content_plan" / f"{month}.json"


def manual_dir(month: str) -> Path:
    return ROOT / f"ручные_статьи_{month}"


TEMPLATE_PLAN = [
    {
        "month": "октябрь",
        "number": "01",
        "title": "Заголовок первой статьи",
    },
    {
        "month": "октябрь",
        "number": "02",
        "title": "Заголовок второй статьи",
    },
]


class WorkflowApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Генератор статей КСП — панель шагов")
        self.geometry("780x720")
        self.minsize(640, 560)
        self.configure(bg="#f7f3ec")

        self.month_var = tk.StringVar(value="октябрь")
        self._build()

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
            text="Кликайте по шагам сверху вниз",
            font=("Segoe UI", 10),
            fg="#c8e6d8",
            bg="#1f4b3a",
            pady=2,
        ).pack()

        body = tk.Frame(self, bg="#f7f3ec")
        body.pack(fill="both", expand=True, **pad)

        tk.Label(
            body,
            text=f"Рабочая папка:\n{WORK}",
            font=("Segoe UI", 9),
            fg="#555",
            bg="#f7f3ec",
            justify="left",
            anchor="w",
        ).pack(fill="x", pady=(0, 8))

        month_row = tk.Frame(body, bg="#f7f3ec")
        month_row.pack(fill="x", pady=(0, 10))
        tk.Label(month_row, text="Месяц:", font=("Segoe UI", 10, "bold"), bg="#f7f3ec").pack(
            side="left"
        )
        ttk.Combobox(
            month_row,
            textvariable=self.month_var,
            values=MONTHS,
            width=14,
            state="readonly",
        ).pack(side="left", padx=8)

        self._step(
            body,
            "1",
            "Написать темы на новый месяц",
            "Откройте план или создайте JSON в content_plan",
            [
                ("Открыть план тем (Markdown)", self.open_topics_plan),
                ("Создать / открыть JSON месяца", self.create_or_open_plan),
                ("Открыть папку content_plan", self.open_content_plan),
            ],
        )
        self._step(
            body,
            "2",
            "Проверить KupiAPI (перед генерацией)",
            "Если тест красный — статьи через API не пойдут",
            [
                ("Проверить ключ и API", self.run_test_api),
                ("Открыть .env", self.open_env),
            ],
        )
        self._step(
            body,
            "3",
            "Сгенерировать статьи",
            "Берёт темы из content_plan\\месяц.json",
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
        self.log = scrolledtext.ScrolledText(body, height=10, font=("Consolas", 9), wrap="word")
        self.log.pack(fill="both", expand=True, pady=(4, 0))
        self._log(f"Панель запущена. Корень инструментов: {ROOT}")
        if WORK != ROOT:
            self._log(f"Проект статей: {WORK}")
        else:
            self._log(
                "Подсказка: скопируйте скрипты через СКОПИРОВАТЬ_В_СТАТЬИ.bat "
                "в maryasg-articles_KorolevSP — тогда генерация пойдёт там."
            )

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
        tk.Label(frame, text=hint, font=("Segoe UI", 9), fg="#666", bg="#fffdf8", anchor="w").pack(
            fill="x"
        )
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

    def open_topics_plan(self) -> None:
        candidates = [
            ROOT / "ПЛАН_ТЕМ_ИЮНЬ_ИЮЛЬ_АВГУСТ_СЕНТЯБРЬ.md",
            WORK / "ПЛАН_ТЕМ_ИЮНЬ_ИЮЛЬ_АВГУСТ_СЕНТЯБРЬ.md",
            WORK / "content_plan" / "ПЛАН_ТЕМ.md",
        ]
        for path in candidates:
            if path.is_file():
                open_path(path)
                self._log(f"Открыт план тем: {path}")
                return
        messagebox.showinfo(
            "План тем",
            "Файла плана пока нет.\nСоздайте JSON через кнопку «Создать / открыть JSON месяца».",
        )

    def create_or_open_plan(self) -> None:
        month = self.month_var.get().strip()
        folder = WORK / "content_plan"
        folder.mkdir(parents=True, exist_ok=True)
        path = plan_path(month)
        if not path.is_file():
            data = []
            for i in range(1, 11):
                data.append(
                    {
                        "month": month,
                        "number": f"{i:02d}",
                        "title": f"Заголовок статьи {i} — замените на свою тему",
                    }
                )
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            self._log(f"Создан шаблон: {path}")
            messagebox.showinfo(
                "Создан файл тем",
                f"Создан:\n{path}\n\nЗамените заголовки на свои темы и сохраните файл.",
            )
        open_path(path)

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
            # fall back to tools copy
            py2 = ROOT / "test_kupiapi.py"
            if py2.is_file():
                self._run_async("Проверка KupiAPI", [python_bin(), str(py2)], cwd=WORK)
            else:
                messagebox.showerror("Нет файла", "Не найден test_kupiapi.py")

    def generate_month(self) -> None:
        month = self.month_var.get().strip()
        plan = plan_path(month)
        if not plan.is_file():
            messagebox.showwarning(
                "Нет плана",
                f"Сначала создайте темы:\n{plan}\n\nШаг 1 → «Создать / открыть JSON месяца».",
            )
            return
        gen = WORK / "generate.py"
        if not gen.is_file():
            gen = ROOT / "generate.py"
        if not gen.is_file():
            messagebox.showerror("Нет generate.py", f"Скопируйте скрипты в\n{ARTICLES_HINT}")
            return
        self._run_async(
            f"Генерация статей: {month}",
            [python_bin(), str(gen), "--plan", str(plan), "--skip-images"],
            cwd=WORK,
        )

    def generate_one(self) -> None:
        month = self.month_var.get().strip()
        plan = plan_path(month)
        if not plan.is_file():
            messagebox.showwarning("Нет плана", f"Нет файла:\n{plan}")
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
                "--number",
                number,
                "--skip-images",
            ],
            cwd=WORK,
        )

    def open_output(self) -> None:
        month = self.month_var.get().strip()
        path = WORK / "output" / month
        if path.is_dir():
            open_path(path)
        else:
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
        month = self.month_var.get().strip()
        bat = WORK / "СОБРАТЬ_ПЛОСКИЕ_ФАЙЛЫ.bat"
        py = WORK / "pack_month.py"
        if bat.is_file() and sys.platform.startswith("win"):
            self._run_async(
                f"Плоские файлы: {month}",
                ["cmd", "/c", str(bat), month],
                cwd=WORK,
            )
        elif py.is_file():
            self._run_async(
                f"Плоские файлы: {month}",
                [python_bin(), str(py), month],
                cwd=WORK,
            )
        else:
            py2 = ROOT / "pack_month.py"
            if py2.is_file():
                self._run_async(
                    f"Плоские файлы: {month}",
                    [python_bin(), str(py2), month],
                    cwd=WORK,
                )
            else:
                messagebox.showerror("Нет файла", "Не найден pack_month.py")

    def open_manual(self, month: str) -> None:
        folder = manual_dir(month)
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
    # Ensure template exists next to tools for copy script
    template = ROOT / "ШАБЛОН_ТЕМ_МЕСЯЦА.json"
    if not template.is_file():
        template.write_text(
            json.dumps(TEMPLATE_PLAN, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    app = WorkflowApp()
    app.mainloop()


if __name__ == "__main__":
    main()
