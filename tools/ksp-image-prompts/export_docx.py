#!/usr/bin/env python3
"""Собрать vk.docx и telegram.docx из уже существующих .md (автор: user)."""

from __future__ import annotations

import argparse
from pathlib import Path

from docx_export import write_text_docx

ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "output"


def main() -> int:
    parser = argparse.ArgumentParser(description="Export existing markdown articles to docx")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--filter-month", metavar="МЕСЯЦ", help="Только месяц, например: июнь")
    args = parser.parse_args()

    month_root = args.output
    if args.filter_month:
        month_root = args.output / args.filter_month.strip()
        if not month_root.is_dir():
            print(f"Папки нет: {month_root}")
            print("Сначала сгенерируйте тексты, например:")
            print(f"  python generate.py --plan content_plan\\{args.filter_month.strip()}.json --skip-images")
            return 1

    count = 0
    for folder in sorted(month_root.rglob("*")):
        if not folder.is_dir():
            continue
        vk_md = folder / "vk.md"
        tg_md = folder / "telegram.md"
        if not vk_md.exists() or not tg_md.exists():
            continue
        write_text_docx(vk_md.read_text(encoding="utf-8"), folder / "vk.docx")
        write_text_docx(tg_md.read_text(encoding="utf-8"), folder / "telegram.docx")
        count += 1
        print(folder.relative_to(args.output))

    print(f"Готово: {count} папок")
    if count == 0:
        print()
        print("Документов Word (.docx) нет, потому что нет готовых статей (.md) в output\\.")
        print("Промпты для картинок лежат в image_prompts\\ — это не Word.")
        print()
        if args.filter_month:
            month = args.filter_month.strip()
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


if __name__ == "__main__":
    raise SystemExit(main())
