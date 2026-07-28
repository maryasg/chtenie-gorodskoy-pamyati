#!/usr/bin/env python3
"""Собрать vk.docx/telegram.docx и плоские .docx в папке месяца."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from docx_export import write_text_docx

ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "output"

CYRILLIC_TO_LATIN = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "e",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "h",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "sch",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
}


def slugify(title: str, max_len: int = 40) -> str:
    lowered = title.lower().strip()
    chars: list[str] = []
    for ch in lowered:
        if ch in CYRILLIC_TO_LATIN:
            chars.append(CYRILLIC_TO_LATIN[ch])
        elif ch.isalnum():
            chars.append(ch)
        else:
            chars.append("-")
    slug = "".join(chars)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")[:max_len].rstrip("-")


def topic_title(md_text: str, fallback: str) -> str:
    for line in md_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            title = stripped.lstrip("#").strip()
            if title:
                return title
    return fallback


def flat_docx_name(number: str, month: str, year: int, label: str, title: str) -> str:
    slug = slugify(title) or "bez-nazvaniya"
    return f"статья{number}_{month}_{year}_{label}_{slug}.docx"


def export_docx(output_root: Path, filter_month: str | None = None, year: int | None = None) -> int:
    month_root = output_root
    if filter_month:
        month_root = output_root / filter_month.strip()
        if not month_root.is_dir():
            print(f"Папки нет: {month_root}")
            print("Сначала сгенерируйте тексты, например:")
            print(f"  python generate.py --plan content_plan\\{filter_month.strip()}.json --skip-images")
            return 1

    export_year = year or datetime.now().year
    count = 0
    for folder in sorted(month_root.rglob("*")):
        if not folder.is_dir():
            continue
        vk_md = folder / "vk.md"
        tg_md = folder / "telegram.md"
        if not vk_md.exists() or not tg_md.exists():
            continue
        vk_text = vk_md.read_text(encoding="utf-8")
        tg_text = tg_md.read_text(encoding="utf-8")
        write_text_docx(vk_text, folder / "vk.docx")
        write_text_docx(tg_text, folder / "telegram.docx")

        if filter_month:
            month = filter_month.strip()
            number = folder.name.split("-", 1)[0].zfill(2)
            title = topic_title(vk_text, folder.name)
            flat_root = output_root / month
            write_text_docx(vk_text, flat_root / flat_docx_name(number, month, export_year, "ВК", title))
            write_text_docx(tg_text, flat_root / flat_docx_name(number, month, export_year, "ТГМАКС", title))
        count += 1
        print(folder.relative_to(output_root))

    print(f"Готово: {count} папок")
    if count and filter_month:
        month = filter_month.strip()
        print()
        print(f"Плоские Word-файлы собраны в: output\\{month}\\")
        print(f"Пример: статья01_{month}_{export_year}_ВК_....docx")
        print(f"Пример: статья01_{month}_{export_year}_ТГМАКС_....docx")
    if count == 0:
        print()
        print("Документов Word (.docx) нет, потому что нет готовых статей (.md) в output\\.")
        print("Промпты для картинок лежат в image_prompts\\ — это не Word.")
        print()
        if filter_month:
            month = filter_month.strip()
            print("Сгенерируйте тексты за месяц:")
            print(f"  python generate.py --plan content_plan\\{month}.json --skip-images")
            print("Затем снова:")
            print(f"  export_docx.bat --filter-month {month}")
        else:
            print("Пример:")
            print("  python generate.py --plan content_plan\\июнь.json --skip-images")
            print("  export_docx.bat --filter-month июнь")
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Export existing markdown articles to docx")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--filter-month", metavar="МЕСЯЦ", help="Только месяц, например: июнь")
    parser.add_argument("--year", type=int, default=datetime.now().year, help="Год в имени плоских файлов")
    args = parser.parse_args()
    return export_docx(args.output, filter_month=args.filter_month, year=args.year)


if __name__ == "__main__":
    raise SystemExit(main())
