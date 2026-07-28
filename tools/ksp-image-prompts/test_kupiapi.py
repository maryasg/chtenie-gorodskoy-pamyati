#!/usr/bin/env python3
"""Быстрая проверка KupiAPI: какие GPT-модели реально отвечают."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).resolve().parent

# GPT models for KupiAPI Python SDK (not Cursor kupi-* aliases).
TEST_MODELS = [
    "gpt-5.4-mini",
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-5.4",
    "chatgpt-4o-latest",
    "gpt-4-turbo",
    "gpt-5.4-nano",
]


def main() -> int:
    load_dotenv(ROOT / ".env")
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    base_url = os.getenv("OPENAI_BASE_URL", "https://kupiapi.ru/v1").strip()

    print(f"Base URL: {base_url}")
    if not api_key:
        print("Нет OPENAI_API_KEY в .env")
        return 1
    if not api_key.startswith("rk_live_"):
        print("Внимание: ключ должен начинаться с rk_live_ (ключ из kupiapi.ru/cabinet)")
    print(f"Ключ: {api_key[:10]}...{api_key[-4:]}")
    print()

    client = OpenAI(api_key=api_key, base_url=base_url)
    ok: list[str] = []
    bad: list[str] = []

    for model in TEST_MODELS:
        print(f"=== {model} ===")
        try:
            kwargs = {
                "model": model,
                "messages": [{"role": "user", "content": "Ответь одним словом: ок"}],
            }
            if not model.startswith(("gpt-5.", "gpt-5.5")):
                kwargs["temperature"] = 0
            response = client.chat.completions.create(**kwargs)
            text = (response.choices[0].message.content or "").strip()
            print(f"OK: {text[:80]}")
            ok.append(model)
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL: {exc}")
            bad.append(model)
        print()

    print("======== ИТОГ ========")
    print("Работают:", ", ".join(ok) if ok else "нет")
    print("Не работают:", ", ".join(bad) if bad else "нет")
    if ok:
        print()
        print("Поставьте в .env:")
        print(f"TEXT_MODEL={ok[0]}")
        if len(ok) > 1:
            print(f"TEXT_MODEL_FALLBACK={','.join(ok[1:])}")
        return 0

    print()
    print("Ни одна GPT-модель не ответила.")
    print("Проверьте баланс: https://kupiapi.ru/cabinet")
    print("И напишите в поддержку KupiAPI с этим логом.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
