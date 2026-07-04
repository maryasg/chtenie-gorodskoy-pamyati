#!/usr/bin/env python3
"""Собрать плоские файлы: месяц01_июнь_как-остановить_вк.rtf, ..._телеграм.txt."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_PLAN_DIR = ROOT / "content_plan"
DEFAULT_OUTPUT = ROOT / "output"


def escape_rtf(text: str) -> str:
    parts: list[str] = []
    for ch in text.replace("\r\n", "\n"):
        if ch == "\n":
            parts.append("\\par\n")
            continue
        code = ord(ch)
        if ch == "\\":
            parts.append("\\\\")
        elif ch == "{":
            parts.append("\\{")
        elif ch == "}":
            parts.append("\\}")
        elif code < 128:
            parts.append(ch)
        else:
            signed = code if code <= 32767 else code - 65536
            parts.append(f"\\u{signed}?")
    return "".join(parts)


def write_rtf(text: str, path: Path) -> None:
    body = escape_rtf(text.strip())
    rtf = (
        r"{\rtf1\ansi\ansicpg1251\deff0"
        r"{\fonttbl{\f0\fswiss Arial;}}"
        r"\f0\fs24 "
        f"{body}"
        r"}"
    )
    path.write_text(rtf, encoding="utf-8")


def find_topic_folder(month_dir: Path, number: str) -> Path | None:
    prefix = f"{number.zfill(2)}-"
    matches = sorted(p for p in month_dir.iterdir() if p.is_dir() and p.name.startswith(prefix))
    return matches[0] if matches else None


def load_plan_items(plan_path: Path, month: str) -> list[dict]:
    data = json.loads(plan_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Ожидался список тем в {plan_path}")
    items = [item for item in data if str(item.get("month", "")).strip() == month]
    items.sort(key=lambda item: str(item.get("number", "")).zfill(2))
    return items


INVALID_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|]+')
WORD_SPLIT = re.compile(r"[\s,;—–\-]+")


def resolve_title(topic_folder: Path, plan_title: str) -> str:
    """Заголовок из статьи (# в .md), иначе из плана."""
    for md_name in ("vk.md", "telegram.md"):
        md_path = topic_folder / md_name
        if not md_path.exists():
            continue
        for line in md_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                heading = stripped.lstrip("#").strip()
                if heading:
                    return heading
    return plan_title


def title_suffix(title: str, words: int = 2, max_len: int = 40) -> str:
    """Первые слова заголовка по-русски для хвоста имени файла."""
    tokens = [token for token in WORD_SPLIT.split(title.strip()) if token]
    snippet = tokens[:words]
    if not snippet:
        return ""
    text = "-".join(snippet).lower()
    text = INVALID_FILENAME_CHARS.sub("", text)
    if len(text) > max_len:
        text = text[:max_len].rstrip("-")
    return text


def flat_base(number: str, month: str, title: str = "") -> str:
    core = f"месяц{number.zfill(2)}_{month}"
    suffix = title_suffix(title)
    return f"{core}_{suffix}" if suffix else core


def cleanup_old_flat_files(flat_dir: Path, number: str, month: str) -> None:
    """Удалить старые плоские файлы этой статьи (в т.ч. .ARTICLE)."""
    prefix = f"месяц{number.zfill(2)}_{month}"
    img_prefix = f"картинка_{prefix}"
    for path in list(flat_dir.iterdir()):
        if not path.is_file():
            continue
        name = path.name
        if name.startswith(prefix) or name.startswith(img_prefix):
            path.unlink()


def write_article_list(items: list[dict], dest: Path, month: str) -> Path:
    lines = [f"Список статей — {month}", ""]
    for item in items:
        number = str(item["number"]).strip().zfill(2)
        title = str(item["title"]).strip()
        lines.append(f"{number}. {title}")
    path = dest / f"список_статей_{month}.txt"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def pack_month(
    month: str,
    plan_path: Path,
    output_root: Path,
    dest_dir: Path | None = None,
    list_only: bool = False,
) -> tuple[int, int, list[str]]:
    items = load_plan_items(plan_path, month)
    if not items:
        raise SystemExit(f"В {plan_path} нет тем для месяца «{month}»")

    month_output = output_root / month
    flat_dir = dest_dir or month_output
    flat_dir.mkdir(parents=True, exist_ok=True)

    write_article_list(items, flat_dir, month)

    if list_only:
        print(f"Список: {flat_dir / f'список_статей_{month}.txt'}")
        return 0, len(items), []

    packed = 0
    missing: list[str] = []

    for item in items:
        number = str(item["number"]).strip().zfill(2)
        plan_title = str(item["title"]).strip()

        topic_folder = find_topic_folder(month_output, number) if month_output.is_dir() else None
        if topic_folder is None:
            missing.append(f"{number}: нет папки в {month_output} — {plan_title}")
            continue

        title = resolve_title(topic_folder, plan_title)
        base = flat_base(number, month, title)

        vk_md = topic_folder / "vk.md"
        tg_md = topic_folder / "telegram.md"
        cover_src = topic_folder / "cover.png"

        if not vk_md.exists() or not tg_md.exists():
            missing.append(f"{number}: нет vk.md/telegram.md в {topic_folder.name}")
            continue

        cleanup_old_flat_files(flat_dir, number, month)

        write_rtf(vk_md.read_text(encoding="utf-8"), flat_dir / f"{base}_вк.rtf")
        (flat_dir / f"{base}_телеграм.txt").write_text(
            tg_md.read_text(encoding="utf-8").strip() + "\n",
            encoding="utf-8",
        )

        image_dst = flat_dir / f"картинка_{base}.png"
        if cover_src.exists():
            shutil.copyfile(cover_src, image_dst)
        else:
            missing.append(f"{number}: нет cover.png — скопированы только тексты")

        packed += 1
        print(f"{number} -> {base}_вк.rtf, {base}_телеграм.txt")

    return packed, len(items), missing


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Плоские файлы: месяц01_июнь_<слова>_вк.rtf, ..._телеграм.txt, картинка_....png",
    )
    parser.add_argument("month", help="Месяц, например: июнь")
    parser.add_argument(
        "--plan",
        type=Path,
        help="JSON с темами (по умолчанию content_plan/<месяц>.json)",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Корень output/")
    parser.add_argument(
        "--dest",
        type=Path,
        help="Куда положить плоские файлы (по умолчанию output/<месяц>/)",
    )
    parser.add_argument(
        "--list-only",
        action="store_true",
        help="Только список_статей_<месяц>.txt из плана, без статей",
    )
    args = parser.parse_args()

    month = args.month.strip()
    plan_path = args.plan or (DEFAULT_PLAN_DIR / f"{month}.json")
    if not plan_path.is_file():
        print(f"Нет плана: {plan_path}")
        return 1

    flat_dir = args.dest or (args.output / month)

    packed, total, missing = pack_month(
        month=month,
        plan_path=plan_path,
        output_root=args.output,
        dest_dir=args.dest,
        list_only=args.list_only,
    )

    print()
    if args.list_only:
        print(f"Готово: список из {total} тем")
        return 0

    print(f"Собрано: {packed} из {total}")
    if packed:
        print()
        print(f"Папка: {flat_dir.resolve()}")
        print("Файлы:")
        print(f"  месяц01_{month}_<слова>_вк.rtf")
        print(f"  месяц01_{month}_<слова>_телеграм.txt")
        print(f"  картинка_месяц01_{month}_<слова>.png")
    if missing:
        print()
        print("Замечания:")
        for line in missing:
            print(f"  - {line}")
        if packed == 0:
            print()
            print("=" * 50)
            print("ПЛОСКИХ ФАЙЛОВ НЕТ — сначала нужны статьи в подпапках.")
            print()
            print("В output\\{0}\\ должны быть папки вида:".format(month))
            print("  output\\{0}\\01-kak-...\\vk.md".format(month))
            print("  output\\{0}\\01-kak-...\\telegram.md".format(month))
            print()
            print("Промпты в image_prompts\\{0}\\ — это НЕ статьи.".format(month))
            print()
            print("Сгенерируйте тексты:")
            print(f"  python generate.py --plan content_plan\\{month}.json --skip-images")
            print()
            print("Или одной командой (из папки статей):")
            print(f"  СОБРАТЬ_ПЛОСКИЕ_ФАЙЛЫ.bat {month}")
            print("=" * 50)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
