#!/usr/bin/env python3
"""Собрать файлы промптов для обложек (ChatGPT / DALL·E) по всем темам плана."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROMPTS_DIR = ROOT / "prompts"
DEFAULT_PLAN = ROOT / "content_plan" / "all.json"
DEFAULT_OUTPUT = ROOT / "image_prompts"
DEFAULT_ARTICLES_OUTPUT = ROOT / "output"

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


def slugify(title: str, max_len: int = 48) -> str:
    lowered = title.lower().strip()
    chars: list[str] = []
    for ch in lowered:
        if ch in CYRILLIC_TO_LATIN:
            chars.append(CYRILLIC_TO_LATIN[ch])
        elif ch.isalnum():
            chars.append(ch)
        else:
            chars.append("-")
    slug = re.sub(r"-+", "-", "".join(chars)).strip("-")
    return slug[:max_len].rstrip("-")


def load_plan(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{path} must be a JSON array")
    return data


def topic_slug_path(month: str, number: str, title: str) -> str:
    return f"{str(number).strip().zfill(2)}-{slugify(title)}"


def build_prompt(
    *,
    title: str,
    telegram_text: str | None,
    title_template: str,
    article_template: str,
) -> str:
    if telegram_text and telegram_text.strip():
        return article_template.replace("[ТЕКСТ СТАТЬИ]", telegram_text.strip())
    return title_template.replace("[ТЕМА СТАТЬИ]", title.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description="Build image prompt files for all content plan topics")
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN, help="Path to content plan JSON")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Directory for image prompt files",
    )
    parser.add_argument(
        "--articles-output",
        type=Path,
        default=DEFAULT_ARTICLES_OUTPUT,
        help="Generated articles folder (uses telegram.md when present)",
    )
    parser.add_argument("--filter-month", metavar="МЕСЯЦ", help="Only one month, e.g. май")
    parser.add_argument("--force", action="store_true", help="Overwrite existing prompt files")
    args = parser.parse_args()

    title_template = (PROMPTS_DIR / "cover_template_title.txt").read_text(encoding="utf-8").strip()
    article_template = (PROMPTS_DIR / "cover_template.txt").read_text(encoding="utf-8").strip()

    plan = load_plan(args.plan)
    if args.filter_month:
        wanted = args.filter_month.strip().lower()
        plan = [item for item in plan if str(item.get("month", "")).strip().lower() == wanted]
        if not plan:
            raise SystemExit(f"Темы месяца «{wanted}» не найдены в {args.plan}")

    written = 0
    skipped = 0
    from_article = 0

    for item in plan:
        month = str(item["month"]).strip()
        number = str(item["number"]).strip().zfill(2)
        title = str(item["title"]).strip()
        rel = topic_slug_path(month, number, title)
        dest = args.output / month / f"{rel}.txt"
        dest.parent.mkdir(parents=True, exist_ok=True)

        if dest.exists() and not args.force:
            skipped += 1
            continue

        tg_path = args.articles_output / month / rel / "telegram.md"
        telegram_text = tg_path.read_text(encoding="utf-8").strip() if tg_path.exists() else None
        if telegram_text:
            from_article += 1

        prompt = build_prompt(
            title=title,
            telegram_text=telegram_text,
            title_template=title_template,
            article_template=article_template,
        )
        dest.write_text(prompt + "\n", encoding="utf-8")
        written += 1

    index_lines = [
        "# Индекс промптов для обложек",
        "",
        f"Всего тем в плане: {len(plan)}",
        f"Создано файлов: {written}",
        f"Пропущено (уже есть): {skipped}",
        f"С текстом из telegram.md: {from_article}",
        "",
        "| Месяц | № | Файл | Тема |",
        "|-------|---|------|------|",
    ]
    for item in plan:
        month = str(item["month"]).strip()
        number = str(item["number"]).strip().zfill(2)
        title = str(item["title"]).strip()
        rel = topic_slug_path(month, number, title)
        index_lines.append(f"| {month} | {number} | `{month}/{rel}.txt` | {title} |")

    index_path = args.output / "INDEX.md"
    index_path.write_text("\n".join(index_lines) + "\n", encoding="utf-8")

    print(f"Готово: {written} файлов в {args.output}")
    if skipped:
        print(f"Пропущено: {skipped} (используйте --force для перезаписи)")
    print(f"Индекс: {index_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
