#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Month + year helpers for KSP content plans."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path


def current_year() -> int:
    return datetime.now().year


def normalize_month(month: str) -> str:
    return str(month).strip().lower()


def normalize_year(year: int | str | None, default: int | None = None) -> int | None:
    if year is None or year == "":
        return default
    try:
        value = int(str(year).strip())
    except (TypeError, ValueError):
        return default
    if 2000 <= value <= 2100:
        return value
    return default


def period_slug(month: str, year: int | None) -> str:
    """Folder/file stem: октябрь_2026 or октябрь."""
    month = normalize_month(month)
    year = normalize_year(year)
    if year is None:
        return month
    return f"{month}_{year}"


def parse_period_arg(text: str) -> tuple[str, int | None]:
    """Parse 'октябрь', 'октябрь_2026', 'октябрь 2026'."""
    raw = str(text).strip().lower().replace("-", "_")
    if not raw:
        raise ValueError("Пустой месяц")
    m = re.fullmatch(r"([а-яё]+)[_\s]+(\d{4})", raw)
    if m:
        return m.group(1), normalize_year(m.group(2))
    m = re.fullmatch(r"([а-яё]+)", raw)
    if m:
        return m.group(1), None
    # Fallback: last _YYYY
    m = re.fullmatch(r"(.+)_(\d{4})", raw)
    if m:
        return m.group(1).strip(), normalize_year(m.group(2))
    return raw, None


def item_year(item: dict, default: int | None = None) -> int | None:
    return normalize_year(item.get("year"), default=default)


def item_period(item: dict, default_year: int | None = None) -> str:
    month = normalize_month(item.get("month", ""))
    year = item_year(item, default=default_year)
    return period_slug(month, year)


def plan_json_name(month: str, year: int | None) -> str:
    return f"{period_slug(month, year)}.json"


def plan_txt_name(month: str, year: int | None) -> str:
    return f"темы_{period_slug(month, year)}.txt"


def resolve_plan_json(plan_dir: Path, month: str, year: int | None) -> Path:
    """Prefer month_year.json; fall back to month.json for old plans."""
    month = normalize_month(month)
    year = normalize_year(year)
    if year is not None:
        with_year = plan_dir / plan_json_name(month, year)
        if with_year.is_file():
            return with_year
    legacy = plan_dir / f"{month}.json"
    if legacy.is_file():
        return legacy
    if year is not None:
        return plan_dir / plan_json_name(month, year)
    return legacy


def resolve_plan_txt(plan_dir: Path, month: str, year: int | None) -> Path:
    month = normalize_month(month)
    year = normalize_year(year)
    if year is not None:
        with_year = plan_dir / plan_txt_name(month, year)
        if with_year.is_file():
            return with_year
    legacy = plan_dir / f"темы_{month}.txt"
    if legacy.is_file():
        return legacy
    if year is not None:
        return plan_dir / plan_txt_name(month, year)
    return legacy
