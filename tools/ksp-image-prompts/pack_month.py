#!/usr/bin/env python3
"""Собрать плоские файлы за месяц: месяц01_июнь.rtf, .txt, картинка_месяц01_июнь.png."""

from __future__ import annotations

import argparse
import json
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


def flat_base(number: str, month: str) -> str:
    return f"месяц{number.zfill(2)}_{month}"


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
        title = str(item["title"]).strip()
        base = flat_base(number, month)

        topic_folder = find_topic_folder(month_output, number) if month_output.is_dir() else None
        if topic_folder is None:
            missing.append(f"{number}: нет папки в {month_output} — {title}")
            continue

        vk_md = topic_folder / "vk.md"
        tg_md = topic_folder / "telegram.md"
        cover_src = topic_folder / "cover.png"

        if not vk_md.exists() or not tg_md.exists():
            missing.append(f"{number}: нет vk.md/telegram.md в {topic_folder.name}")
            continue

        write_rtf(vk_md.read_text(encoding="utf-8"), flat_dir / f"{base}.rtf")
        shutil.copyfile(tg_md, flat_dir / f"{base}.txt")

        image_dst = flat_dir / f"картинка_{base}.png"
        if cover_src.exists():
            shutil.copyfile(cover_src, image_dst)
        else:
            missing.append(f"{number}: нет cover.png — скопированы только тексты")

        packed += 1
        print(f"{number} -> {base}.*")

    return packed, len(items), missing


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Плоские файлы в папке месяца: месяц01_июнь.rtf, .txt, картинка_месяц01_июнь.png",
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
    if missing:
        print()
        print("Замечания:")
        for line in missing:
            print(f"  - {line}")
        if packed == 0:
            print()
            print("Сначала сгенерируйте тексты:")
            print(f"  python generate.py --plan content_plan\\{month}.json --skip-images")
            print("Затем снова:")
            print(f"  pack_month.bat {month}")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
