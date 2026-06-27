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
    args = parser.parse_args()

    count = 0
    for folder in sorted(args.output.rglob("*")):
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
