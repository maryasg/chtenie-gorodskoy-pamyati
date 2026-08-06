#!/usr/bin/env python3
"""Мини-проверка KupiAPI одной моделью — для отладки."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

api_key = os.getenv("OPENAI_API_KEY", "").strip()
base_url = os.getenv("OPENAI_BASE_URL", "").strip()
model = (sys.argv[1] if len(sys.argv) > 1 else os.getenv("TEXT_MODEL", "deepseek-chat")).strip()

print("=== Диагностика KupiAPI ===")
print(f"Папка:     {ROOT}")
print(f".env есть: {(ROOT / '.env').exists()}")
print(f"BASE_URL:  {base_url!r}")
print(f"KEY set:   {bool(api_key)}")
print(f"KEY start: {api_key[:10]!r}" if api_key else "KEY start: ''")
print(f"KEY len:   {len(api_key)}")
print(f"MODEL:     {model!r}")
print()

if not api_key:
    print("ОШИБКА: нет OPENAI_API_KEY")
    raise SystemExit(1)
if not base_url:
    print("ОШИБКА: нет OPENAI_BASE_URL")
    raise SystemExit(1)
if not api_key.startswith("rk_live_"):
    print("ВНИМАНИЕ: ключ не начинается с rk_live_")

client = OpenAI(api_key=api_key, base_url=base_url)
try:
    kwargs = {
        "model": model,
        "messages": [{"role": "user", "content": "Ответь одним словом: ок"}],
    }
    if not model.startswith(("gpt-5.", "gpt-5.5")):
        kwargs["temperature"] = 0
    print("Отправляю запрос...")
    response = client.chat.completions.create(**kwargs)
    text = (response.choices[0].message.content or "").strip()
    print("УСПЕХ:", text)
except Exception as exc:  # noqa: BLE001
    print("ОШИБКА:", type(exc).__name__)
    print(exc)
    raise SystemExit(2)
