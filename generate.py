#!/usr/bin/env python3
"""Generate VK/Telegram articles and cover images for KSP content plan."""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

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


@dataclass
class TopicOutputs:
    month_dir: Path
    vk_md: Path
    tg_md: Path
    cover: Path
    prompt: Path
    meta: Path

    @property
    def vk_docx(self) -> Path:
        return self.vk_md.with_suffix(".docx")

    @property
    def tg_docx(self) -> Path:
        return self.tg_md.with_suffix(".docx")

    @property
    def texts_exist(self) -> bool:
        return self.vk_md.exists() and self.tg_md.exists()


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
    slug = re.sub(r"-+", "-", "".join(chars)).strip("-")
    return slug[:max_len].rstrip("-")


def month_dir(output_root: Path, month: str) -> Path:
    return output_root / month


def build_outputs(
    output_root: Path,
    month: str,
    number: str,
    year: str,
    title: str,
    image_ext: str,
) -> TopicOutputs:
    dest = month_dir(output_root, month)
    dest.mkdir(parents=True, exist_ok=True)
    slug = slugify(title)
    num = number.zfill(2)
    article = f"статья{num}"
    return TopicOutputs(
        month_dir=dest,
        vk_md=dest / f"{article}_{month}_{year}_ВК_{slug}.md",
        tg_md=dest / f"{article}_{month}_{year}_ТГМАКС_{slug}.md",
        cover=dest / f"{article}_{slug}.{image_ext}",
        prompt=dest / f"{article}_{month}_{year}_промпт_{slug}.txt",
        meta=dest / f"{article}_{month}_{year}_meta_{slug}.json",
    )


def find_outputs_by_number(month_folder: Path, number: str) -> TopicOutputs | None:
    num = number.zfill(2)
    article = f"статья{num}"
    vk_matches = sorted(month_folder.glob(f"{article}_*_ВК_*.md"))
    tg_matches = sorted(month_folder.glob(f"{article}_*_ТГМАКС_*.md"))
    if not vk_matches or not tg_matches:
        return None
    vk_md = vk_matches[0]
    tg_md = tg_matches[0]
    cover_matches = sorted(month_folder.glob(f"{article}_*.*"))
    cover = next((p for p in cover_matches if p.suffix.lower() in {".png", ".jpg", ".jpeg"}), vk_md)
    prompt_matches = sorted(month_folder.glob(f"{article}_*_промпт_*.txt"))
    meta_matches = sorted(month_folder.glob(f"{article}_*_meta_*.json"))
    return TopicOutputs(
        month_dir=month_folder,
        vk_md=vk_md,
        tg_md=tg_md,
        cover=cover if cover.suffix.lower() in {".png", ".jpg", ".jpeg"} else month_folder / f"{article}_cover.png",
        prompt=prompt_matches[0] if prompt_matches else month_folder / f"{article}_prompt.txt",
        meta=meta_matches[0] if meta_matches else month_folder / f"{article}_meta.json",
    )


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def load_plan(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("content_plan.json must be a JSON array")
    return data


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
    if "ТЕКСТ СТАТЬИ" not in template:
        raise RuntimeError("cover_template.txt must contain placeholder ТЕКСТ СТАТЬИ")
    return template.replace("ТЕКСТ СТАТЬИ", telegram_text)


def generate_cover_bytes(
    client: OpenAI,
    model: str,
    size: str,
    prompt: str,
) -> bytes:
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
        return base64.b64decode(item.b64_json)

    if item.url:
        return requests.get(item.url, timeout=120).content

    raise RuntimeError("Image API returned no image data")


def save_cover_image(image_bytes: bytes, dest: Path, image_ext: str) -> None:
    ext = image_ext.lower().lstrip(".")
    if ext in {"jpg", "jpeg"}:
        from PIL import Image

        image = Image.open(io.BytesIO(image_bytes))
        if image.mode in {"RGBA", "P"}:
            background = Image.new("RGB", image.size, (255, 255, 255))
            if image.mode == "P":
                image = image.convert("RGBA")
            background.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
            image = background
        elif image.mode != "RGB":
            image = image.convert("RGB")
        image.save(dest, format="JPEG", quality=92, optimize=True)
        return

    dest.write_bytes(image_bytes)


def write_docx(path: Path, text: str) -> None:
    from docx import Document

    document = Document()
    for line in text.splitlines():
        document.add_paragraph(line)
    document.save(path)


def write_text_outputs(
    outputs: TopicOutputs,
    vk_text: str,
    tg_text: str,
    cover_prompt: str,
    also_docx: bool,
) -> None:
    outputs.vk_md.write_text(vk_text + "\n", encoding="utf-8")
    outputs.tg_md.write_text(tg_text + "\n", encoding="utf-8")
    outputs.prompt.write_text(cover_prompt + "\n", encoding="utf-8")
    if also_docx:
        write_docx(outputs.vk_docx, vk_text)
        write_docx(outputs.tg_docx, tg_text)


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


def extract_hashtag_line(text: str) -> str | None:
    for line in reversed(text.splitlines()):
        if line.strip().startswith("#"):
            return line.strip()
    return None


def validate_article(text: str, platform: str, min_len: int, max_len: int) -> list[str]:
    issues: list[str] = []
    length = len(text)

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
    if "ТЕКСТ СТАТЬИ" in prompt:
        issues.append("cover prompt: остался плейсхолдер ТЕКСТ СТАТЬИ")
    if f"[{telegram_text}]" not in prompt:
        issues.append("cover prompt: текст статьи должен быть в квадратных скобках [...]")
    if "стетоскоп" not in prompt.lower():
        issues.append("cover prompt: нет напоминания про отсутствие стетоскопов")
    return issues


def validate_outputs(outputs: TopicOutputs, skip_image: bool) -> list[str]:
    issues: list[str] = []

    for path in (outputs.vk_md, outputs.tg_md, outputs.prompt, outputs.meta):
        if not path.exists():
            issues.append(f"нет файла {path.name}")

    if not skip_image and not outputs.cover.exists():
        issues.append(f"нет файла {outputs.cover.name}")

    if outputs.vk_md.exists():
        issues.extend(validate_article(outputs.vk_md.read_text(encoding="utf-8"), "VK", 2500, 3000))

    if outputs.tg_md.exists():
        issues.extend(validate_article(outputs.tg_md.read_text(encoding="utf-8"), "Telegram", 1200, 1500))

    if outputs.tg_md.exists() and outputs.prompt.exists():
        issues.extend(
            validate_cover_prompt(
                outputs.prompt.read_text(encoding="utf-8"),
                outputs.tg_md.read_text(encoding="utf-8"),
            )
        )

    return issues


def save_meta(
    dest: Path,
    *,
    month: str,
    number: str,
    title: str,
    year: str,
    files: dict[str, str],
    generated_at: str,
    text_model: str,
    image_model: str | None,
    validation_issues: list[str],
) -> None:
    payload = {
        "month": month,
        "number": number,
        "year": year,
        "title": title,
        "files": files,
        "generated_at": generated_at,
        "text_model": text_model,
        "image_model": image_model,
        "validation_issues": validation_issues,
    }
    dest.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def process_topic(
    text_client: OpenAI,
    image_client: OpenAI,
    item: dict,
    output_root: Path,
    year: str,
    text_model: str,
    image_model: str,
    image_size: str,
    image_ext: str,
    also_docx: bool,
    skip_image: bool,
    images_only: bool,
    force: bool,
) -> list[str]:
    month = str(item["month"]).strip()
    number = str(item["number"]).strip().zfill(2)
    title = str(item["title"]).strip()
    outputs = build_outputs(output_root, month, number, year, title, image_ext)

    generated_at = datetime.now(timezone.utc).isoformat()
    print(f"\n=== {month}/{number} — {title} ===")
    print(f"Папка: {outputs.month_dir}")

    cover_exists = outputs.cover.exists()

    if images_only or (outputs.texts_exist and not skip_image and not cover_exists):
        if not outputs.tg_md.exists():
            found = find_outputs_by_number(outputs.month_dir, number)
            if found:
                outputs = found
            else:
                print("Пропуск: нет Telegram-файла — сначала сгенерируйте тексты")
                return [f"{number}: нет Telegram-файла для обложки"]

        if images_only and cover_exists and not force:
            print(f"Пропуск: {outputs.cover.name} уже есть (используйте --force)")
            issues = validate_outputs(outputs, skip_image=False)
            return issues

        tg_text = outputs.tg_md.read_text(encoding="utf-8").strip()
        if outputs.prompt.exists() and not force:
            cover_prompt = outputs.prompt.read_text(encoding="utf-8").strip()
        else:
            cover_prompt = build_cover_prompt(tg_text)
            outputs.prompt.write_text(cover_prompt + "\n", encoding="utf-8")

        print(f"Генерация обложки ({image_model}, {image_size}) -> {outputs.cover.name}")
        image_bytes = generate_cover_bytes(image_client, image_model, image_size, cover_prompt)
        save_cover_image(image_bytes, outputs.cover, image_ext)

        issues = validate_outputs(outputs, skip_image=False)
        save_meta(
            outputs.meta,
            month=month,
            number=number,
            title=title,
            year=year,
            files={
                "vk": outputs.vk_md.name,
                "telegram": outputs.tg_md.name,
                "cover": outputs.cover.name,
                "prompt": outputs.prompt.name,
            },
            generated_at=generated_at,
            text_model=text_model,
            image_model=image_model,
            validation_issues=issues,
        )
        if issues:
            print("Проверка качества: есть замечания")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("Проверка качества: OK")
        return issues

    if not force and outputs.texts_exist:
        print("Пропуск: файлы уже есть (используйте --force или --images-only)")
        issues = validate_outputs(outputs, skip_image=skip_image)
        return issues

    vk_prompt = load_text(PROMPTS_DIR / "vk_system.txt")
    tg_prompt = load_text(PROMPTS_DIR / "telegram_system.txt")

    print("Генерация VK...")
    vk_text = generate_article(text_client, text_model, vk_prompt, title)

    print("Генерация Telegram...")
    tg_text = generate_article(text_client, text_model, tg_prompt, title, vk_text=vk_text)

    cover_prompt = build_cover_prompt(tg_text)
    write_text_outputs(outputs, vk_text, tg_text, cover_prompt, also_docx)
    print(f"  {outputs.vk_md.name}")
    print(f"  {outputs.tg_md.name}")
    if also_docx:
        print(f"  {outputs.vk_docx.name}")
        print(f"  {outputs.tg_docx.name}")

    if not skip_image:
        print(f"Генерация обложки ({image_model}, {image_size}) -> {outputs.cover.name}")
        image_bytes = generate_cover_bytes(image_client, image_model, image_size, cover_prompt)
        save_cover_image(image_bytes, outputs.cover, image_ext)

    issues = validate_outputs(outputs, skip_image=skip_image)
    save_meta(
        outputs.meta,
        month=month,
        number=number,
        title=title,
        year=year,
        files={
            "vk": outputs.vk_md.name,
            "telegram": outputs.tg_md.name,
            "cover": outputs.cover.name,
            "prompt": outputs.prompt.name,
        },
        generated_at=generated_at,
        text_model=text_model,
        image_model=None if skip_image else image_model,
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
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN, help="Path to content_plan.json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output directory")
    parser.add_argument("--number", help="Generate only one topic number, e.g. 03")
    parser.add_argument("--title", help='Любая тема без content_plan.json')
    parser.add_argument("--month", default="май", help="Месяц для папки output при --title")
    parser.add_argument("--filter-month", metavar="МЕСЯЦ", help="Только темы этого месяца из плана")
    parser.add_argument("--year", help="Год в имени файла (по умолчанию: OUTPUT_YEAR или текущий)")
    parser.add_argument("--skip-images", action="store_true", help="Без обложки")
    parser.add_argument("--images-only", action="store_true", help="Только обложки")
    parser.add_argument("--also-docx", action="store_true", help="Дополнительно сохранить .docx для Word")
    parser.add_argument("--force", action="store_true", help="Перегенерировать даже если файлы есть")
    return parser.parse_args()


def main() -> int:
    load_dotenv(ROOT / ".env")
    args = parse_args()

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key and not args.images_only:
        print("Ошибка: задайте OPENAI_API_KEY в файле .env", file=sys.stderr)
        return 1

    if args.images_only and not os.getenv("IMAGE_API_KEY", api_key).strip():
        print("Ошибка: для --images-only нужен IMAGE_API_KEY или OPENAI_API_KEY", file=sys.stderr)
        return 1

    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
    image_base = os.getenv("IMAGE_BASE_URL", base_url).strip()
    text_model = os.getenv("TEXT_MODEL", "gpt-4o-mini").strip()
    image_model = os.getenv("IMAGE_MODEL", "dall-e-3").strip()
    image_size = os.getenv("IMAGE_SIZE", "1792x1024").strip()
    image_ext = os.getenv("IMAGE_FORMAT", "jpg").strip().lower().lstrip(".")
    year = (args.year or os.getenv("OUTPUT_YEAR") or str(datetime.now().year)).strip()
    also_docx = args.also_docx or os.getenv("ALSO_DOCX", "").strip().lower() in {"1", "true", "yes"}

    if args.images_only and args.skip_images:
        print("Ошибка: нельзя одновременно --images-only и --skip-images", file=sys.stderr)
        return 1

    try:
        text_client, image_client = make_clients()
    except ValueError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1

    print(f"Тексты API: {base_url}")
    print(f"Картинки API: {image_base}")
    print(f"Тексты: {text_model} | Картинки: {image_model} | Формат: {image_ext}")

    if args.title:
        number = (args.number or "99").strip().zfill(2)
        plan = [{"month": args.month.strip(), "number": number, "title": args.title.strip()}]
    else:
        plan = load_plan(args.plan)
        if args.filter_month:
            wanted_month = args.filter_month.strip().lower()
            plan = [item for item in plan if str(item.get("month", "")).strip().lower() == wanted_month]
            if not plan:
                print(f"Темы месяца «{wanted_month}» не найдены", file=sys.stderr)
                return 1
        if args.number:
            wanted = args.number.strip().zfill(2)
            plan = [item for item in plan if str(item.get("number", "")).strip().zfill(2) == wanted]
            if not plan:
                print(f"Тема {wanted} не найдена", file=sys.stderr)
                return 1

    all_issues: list[str] = []
    for item in plan:
        issues = process_topic(
            text_client,
            image_client,
            item,
            args.output,
            year=year,
            text_model=text_model,
            image_model=image_model,
            image_size=image_size,
            image_ext=image_ext,
            also_docx=also_docx,
            skip_image=args.skip_images,
            images_only=args.images_only,
            force=args.force,
        )
        all_issues.extend(issues)

    print("\n=== Итог ===")
    print(f"Тем обработано: {len(plan)}")
    print(f"Замечаний проверки: {len(all_issues)}")
    return 0 if not all_issues else 2


if __name__ == "__main__":
    raise SystemExit(main())
