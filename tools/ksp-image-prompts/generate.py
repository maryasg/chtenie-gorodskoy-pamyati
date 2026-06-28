#!/usr/bin/env python3
"""Generate VK/Telegram articles and cover images for KSP content plan."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from docx_export import write_text_docx

ROOT = Path(__file__).resolve().parent
PROMPTS_DIR = ROOT / "prompts"
DEFAULT_PLAN = ROOT / "content_plan.json"
DEFAULT_OUTPUT = ROOT / "output"

PHONE = "8 (499) 490-55-55"
BOOKING_URL = "https://clck.ru/3N8E8Q"
REQUIRED_HASHTAGS = (
    "#КоролёвскаяСтоматологическаяПоликлиника",
    "#КоролёвскаяСтоматология",
    "#стоматологияКоролёв",
)

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

DANGEROUS_PATTERNS = [
    r"\bнавсегда избав",
    r"\bгарантированн",
    r"\b100\s*%",
    r"мг\s*в\s*\d+",
    r"\bтаблетк",
    r"\bантибиотик",
    r"\bдозировк",
    r"http[s]?://(?!clck\.ru/3N8E8Q)",
    r"\bpubmed\b",
    r"\bdoi\b",
]


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


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def load_plan(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("content_plan.json must be a JSON array")
    return data


def topic_dir(output_root: Path, month: str, number: str, title: str) -> Path:
    return output_root / month / f"{number}-{slugify(title)}"


def generate_article(
    client: OpenAI,
    model: str,
    system_prompt: str,
    title: str,
    vk_text: str | None = None,
) -> str:
    user_parts = [f"Тема статьи: {title}"]
    if vk_text:
        user_parts.append(
            "Ниже версия для ВКонтакте. Сделай сокращённую версию для Telegram в том же стиле:\n\n"
            + vk_text
        )
    response = client.chat.completions.create(
        model=model,
        temperature=0.7,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "\n\n".join(user_parts)},
        ],
    )
    text = response.choices[0].message.content
    if not text:
        raise RuntimeError("Empty response from text model")
    return text.strip()


def build_cover_prompt(telegram_text: str) -> str:
    template = load_text(PROMPTS_DIR / "cover_template.txt")
    return template.replace("[ТЕКСТ СТАТЬИ]", telegram_text)


def generate_cover(
    client: OpenAI,
    model: str,
    size: str,
    prompt: str,
    dest: Path,
) -> None:
    import base64

    import requests

    response = client.images.generate(
        model=model,
        prompt=prompt,
        size=size,  # type: ignore[arg-type]
        quality="standard",
        n=1,
    )
    item = response.data[0]

    if item.b64_json:
        dest.write_bytes(base64.b64decode(item.b64_json))
        return

    if item.url:
        dest.write_bytes(requests.get(item.url, timeout=120).content)
        return

    raise RuntimeError("Image API returned no image data")


def make_clients() -> tuple[OpenAI, OpenAI]:
    text_key = os.getenv("OPENAI_API_KEY", "").strip()
    text_base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()

    image_key = os.getenv("IMAGE_API_KEY", text_key).strip()
    image_base = os.getenv("IMAGE_BASE_URL", text_base).strip()

    if not text_key:
        raise ValueError("OPENAI_API_KEY is not set")

    text_client = OpenAI(api_key=text_key, base_url=text_base)
    image_client = OpenAI(api_key=image_key, base_url=image_base)
    return text_client, image_client


def count_chars(text: str) -> int:
    return len(text)


def extract_hashtag_line(text: str) -> str | None:
    for line in reversed(text.splitlines()):
        if line.strip().startswith("#"):
            return line.strip()
    return None


def validate_article(text: str, platform: str, min_len: int, max_len: int) -> list[str]:
    issues: list[str] = []
    length = count_chars(text)

    if length < min_len:
        issues.append(f"{platform}: объём {length} символов (нужно {min_len}–{max_len})")
    elif length > max_len:
        issues.append(f"{platform}: объём {length} символов (нужно {min_len}–{max_len})")

    if PHONE not in text:
        issues.append(f"{platform}: нет телефона для записи")

    if BOOKING_URL not in text:
        issues.append(f"{platform}: нет ссылки на онлайн-запись")

    hashtag_line = extract_hashtag_line(text)
    if not hashtag_line:
        issues.append(f"{platform}: нет строки с хэштегами")
    else:
        for tag in REQUIRED_HASHTAGS:
            if tag not in hashtag_line:
                issues.append(f"{platform}: отсутствует хэштег {tag}")
        if "\n" in hashtag_line:
            issues.append(f"{platform}: хэштеги должны быть одной строкой")

    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            issues.append(f"{platform}: подозрительная фраза по шаблону /{pattern}/")

    if not text.strip().startswith("🦷"):
        issues.append(f"{platform}: статья должна начинаться с 🦷")

    if "✨" not in text:
        issues.append(f"{platform}: нет финальной фразы с ✨")

    return issues


def validate_cover_prompt(prompt: str, telegram_text: str) -> list[str]:
    issues: list[str] = []
    if telegram_text not in prompt:
        issues.append("cover prompt: не подставлен текст Telegram-статьи")
    if "[ТЕКСТ СТАТЬИ]" in prompt:
        issues.append("cover prompt: остался плейсхолдер [ТЕКСТ СТАТЬИ]")
    if "стетоскоп" not in prompt.lower():
        issues.append("cover prompt: нет напоминания про отсутствие стетоскопов")
    return issues


def validate_outputs(topic_path: Path, skip_image: bool) -> list[str]:
    issues: list[str] = []
    vk_path = topic_path / "vk.md"
    tg_path = topic_path / "telegram.md"
    prompt_path = topic_path / "image_prompt.txt"
    cover_path = topic_path / "cover.png"
    meta_path = topic_path / "meta.json"

    for path in (vk_path, tg_path, prompt_path, meta_path):
        if not path.exists():
            issues.append(f"нет файла {path.name}")

    if not skip_image and not cover_path.exists():
        issues.append("нет файла cover.png")

    if vk_path.exists():
        issues.extend(validate_article(vk_path.read_text(encoding="utf-8"), "VK", 2500, 3000))

    if tg_path.exists():
        issues.extend(validate_article(tg_path.read_text(encoding="utf-8"), "Telegram", 1200, 1500))

    if tg_path.exists() and prompt_path.exists():
        issues.extend(
            validate_cover_prompt(
                prompt_path.read_text(encoding="utf-8"),
                tg_path.read_text(encoding="utf-8"),
            )
        )

    return issues


def save_article_docx(dest: Path, vk_text: str, tg_text: str) -> None:
    write_text_docx(vk_text, dest / "vk.docx")
    write_text_docx(tg_text, dest / "telegram.docx")


def save_meta(
    dest: Path,
    *,
    month: str,
    number: str,
    title: str,
    validation_issues: list[str],
) -> None:
    payload = {
        "month": month,
        "number": number,
        "title": title,
        "created_by": "user",
        "validation_issues": validation_issues,
    }
    dest.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def process_topic(
    text_client: OpenAI,
    image_client: OpenAI,
    item: dict,
    output_root: Path,
    text_model: str,
    image_model: str,
    image_size: str,
    skip_image: bool,
    images_only: bool,
    force: bool,
) -> list[str]:
    month = str(item["month"]).strip()
    number = str(item["number"]).strip().zfill(2)
    title = str(item["title"]).strip()
    dest = topic_dir(output_root, month, number, title)
    dest.mkdir(parents=True, exist_ok=True)

    print(f"\n=== {month}/{number} — {title} ===")
    print(f"Папка: {dest}")

    vk_path = dest / "vk.md"
    tg_path = dest / "telegram.md"
    prompt_path = dest / "image_prompt.txt"
    cover_path = dest / "cover.png"

    if images_only or (vk_path.exists() and tg_path.exists() and not skip_image and not cover_path.exists()):
        if not tg_path.exists():
            print("Пропуск: нет telegram.md — сначала сгенерируйте тексты")
            return [f"{number}: нет telegram.md для обложки"]

        if images_only and cover_path.exists() and not force:
            print("Пропуск: cover.png уже есть (используйте --force)")
            issues = validate_outputs(dest, skip_image=False)
            save_meta(
                dest / "meta.json",
                month=month,
                number=number,
                title=title,
                validation_issues=issues,
            )
            return issues

        tg_text = tg_path.read_text(encoding="utf-8").strip()
        vk_text = vk_path.read_text(encoding="utf-8").strip() if vk_path.exists() else ""
        if vk_text and tg_text:
            save_article_docx(dest, vk_text, tg_text)
        if prompt_path.exists() and not force:
            cover_prompt = prompt_path.read_text(encoding="utf-8").strip()
        else:
            cover_prompt = build_cover_prompt(tg_text)
            prompt_path.write_text(cover_prompt + "\n", encoding="utf-8")

        print(f"Генерация обложки ({image_model}, {image_size})...")
        generate_cover(image_client, image_model, image_size, cover_prompt, cover_path)

        issues = validate_outputs(dest, skip_image=False)
        save_meta(
            dest / "meta.json",
            month=month,
            number=number,
            title=title,
            validation_issues=issues,
        )
        if issues:
            print("Проверка качества: есть замечания")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("Проверка качества: OK")
        return issues

    if not force and vk_path.exists() and tg_path.exists():
        print("Пропуск: файлы уже есть (используйте --force или --images-only)")
        save_article_docx(dest, vk_path.read_text(encoding="utf-8"), tg_path.read_text(encoding="utf-8"))
        issues = validate_outputs(dest, skip_image=skip_image)
        save_meta(
            dest / "meta.json",
            month=month,
            number=number,
            title=title,
            validation_issues=issues,
        )
        return issues

    vk_prompt = load_text(PROMPTS_DIR / "vk_system.txt")
    tg_prompt = load_text(PROMPTS_DIR / "telegram_system.txt")

    print("Генерация VK...")
    vk_text = generate_article(text_client, text_model, vk_prompt, title)
    vk_path.write_text(vk_text + "\n", encoding="utf-8")

    print("Генерация Telegram...")
    tg_text = generate_article(text_client, text_model, tg_prompt, title, vk_text=vk_text)
    tg_path.write_text(tg_text + "\n", encoding="utf-8")
    save_article_docx(dest, vk_text, tg_text)

    cover_prompt = build_cover_prompt(tg_text)
    prompt_path.write_text(cover_prompt + "\n", encoding="utf-8")

    if not skip_image:
        print(f"Генерация обложки ({image_model}, {image_size})...")
        generate_cover(image_client, image_model, image_size, cover_prompt, cover_path)

    issues = validate_outputs(dest, skip_image=skip_image)
    save_meta(
        dest / "meta.json",
        month=month,
        number=number,
        title=title,
        validation_issues=issues,
    )

    if issues:
        print("Проверка качества: есть замечания")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("Проверка качества: OK")

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="KSP content generator")
    parser.add_argument(
        "--plan",
        type=Path,
        default=DEFAULT_PLAN,
        help="Path to content_plan.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output directory",
    )
    parser.add_argument(
        "--number",
        help="Generate only one topic number, e.g. 03",
    )
    parser.add_argument(
        "--title",
        help='Любая тема без content_plan.json, например: "Кровоточивость дёсен"',
    )
    parser.add_argument(
        "--month",
        default="май",
        help="Месяц для папки output при --title (по умолчанию: май)",
    )
    parser.add_argument(
        "--filter-month",
        metavar="МЕСЯЦ",
        help="Только темы этого месяца из плана, например: май",
    )
    parser.add_argument(
        "--skip-images",
        action="store_true",
        help="Generate texts and prompt only, without cover image",
    )
    parser.add_argument(
        "--images-only",
        action="store_true",
        help="Generate cover images only (requires existing telegram.md)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even if output files already exist",
    )
    return parser.parse_args()


def months_for_pack(args: argparse.Namespace, plan: list[dict]) -> list[str]:
    if args.images_only:
        return []
    if args.filter_month:
        return [args.filter_month.strip()]
    plan_path = args.plan
    if plan_path.name not in ("content_plan.json", "all.json") and plan_path.suffix == ".json":
        return [plan_path.stem]
    if args.title:
        return [args.month.strip()]
    months = sorted({str(item.get("month", "")).strip() for item in plan if item.get("month")})
    return months if len(months) == 1 else []


def pack_after_generate(args: argparse.Namespace, plan: list[dict]) -> None:
    from pack_month import pack_month as run_pack_month

    for month in months_for_pack(args, plan):
        plan_path = args.plan
        month_plan = ROOT / "content_plan" / f"{month}.json"
        if month_plan.is_file():
            plan_path = month_plan
        if not plan_path.is_file():
            print(f"\nПропуск плоских файлов: нет плана для «{month}»")
            continue
        print(f"\n=== Плоские файлы: {month} ===")
        packed, total, missing = run_pack_month(
            month=month,
            plan_path=plan_path,
            output_root=args.output,
        )
        print(f"Готово: {packed} из {total} в {args.output / month}")
        if packed:
            print("Примеры: месяц01_{0}_..._вк.rtf, ..._телеграм.txt".format(month))


def main() -> int:
    load_dotenv(ROOT / ".env")
    args = parse_args()

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key and not args.images_only:
        print("Ошибка: задайте OPENAI_API_KEY в файле .env", file=sys.stderr)
        print("Скопируйте .env.example в .env и вставьте ключ.", file=sys.stderr)
        return 1

    if args.images_only and not os.getenv("IMAGE_API_KEY", api_key).strip():
        print("Ошибка: для --images-only нужен IMAGE_API_KEY или OPENAI_API_KEY", file=sys.stderr)
        return 1

    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
    image_base = os.getenv("IMAGE_BASE_URL", base_url).strip()
    text_model = os.getenv("TEXT_MODEL", "gpt-4o-mini").strip()
    image_model = os.getenv("IMAGE_MODEL", "dall-e-3").strip()
    image_size = os.getenv("IMAGE_SIZE", "1792x1024").strip()

    if args.images_only and args.skip_images:
        print("Ошибка: нельзя одновременно --images-only и --skip-images", file=sys.stderr)
        return 1

    if image_size != "1792x1024" and image_model == "dall-e-3":
        print("Предупреждение: для 16:9 у dall-e-3 используйте IMAGE_SIZE=1792x1024")

    try:
        text_client, image_client = make_clients()
    except ValueError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        print("Скопируйте .env.example в .env и вставьте ключ.", file=sys.stderr)
        return 1

    print(f"Тексты API: {base_url}")
    print(f"Картинки API: {image_base}")
    print(f"Тексты: {text_model} | Картинки: {image_model}")

    if args.title:
        number = (args.number or "99").strip().zfill(2)
        plan = [{"month": args.month.strip(), "number": number, "title": args.title.strip()}]
        print(f"Режим одной темы: {args.title.strip()}")
    else:
        plan = load_plan(args.plan)
        if args.filter_month:
            wanted_month = args.filter_month.strip().lower()
            plan = [item for item in plan if str(item.get("month", "")).strip().lower() == wanted_month]
            if not plan:
                print(f"Темы месяца «{wanted_month}» не найдены в {args.plan}", file=sys.stderr)
                return 1
            print(f"Фильтр по месяцу: {wanted_month} ({len(plan)} тем)")
        if args.number:
            wanted = args.number.strip().zfill(2)
            plan = [item for item in plan if str(item.get("number", "")).strip().zfill(2) == wanted]
            if not plan:
                print(f"Тема с номером {wanted} не найдена в {args.plan}", file=sys.stderr)
                return 1

    all_issues: list[str] = []
    for item in plan:
        issues = process_topic(
            text_client,
            image_client,
            item,
            args.output,
            text_model=text_model,
            image_model=image_model,
            image_size=image_size,
            skip_image=args.skip_images,
            images_only=args.images_only,
            force=args.force,
        )
        all_issues.extend(issues)

    print("\n=== Итог ===")
    print(f"Тем обработано: {len(plan)}")
    print(f"Замечаний проверки: {len(all_issues)}")

    if not args.images_only:
        pack_after_generate(args, plan)

    return 0 if not all_issues else 2


if __name__ == "__main__":
    raise SystemExit(main())
