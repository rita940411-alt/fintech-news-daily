#!/usr/bin/env python3
"""驗證每日金融科技新聞 JSON 檔案是否符合結構規範。

用法:
    python3 validate_news.py <path/to/YYYY-MM-DD.json>

驗證規則:
    - 檔案內容須為一個 JSON 陣列，且恰好包含 3 篇新聞。
    - 每篇新聞須包含 title / source / date / url / key_points / mermaid。
    - date 須符合 YYYY-MM-DD 格式且為合法日期。
    - url 須為 http:// 或 https:// 開頭的合法網址。
    - key_points 須為恰好 3 個非空字串組成的陣列。
    - mermaid 須為非空字串。
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse

REQUIRED_FIELDS = ("title", "source", "date", "url", "key_points", "mermaid")
REQUIRED_KEY_POINTS = 3
REQUIRED_ARTICLES_PER_DAY = 3


class ValidationError(Exception):
    """代表一筆驗證失敗，附帶可讀的錯誤訊息。"""


def _validate_non_empty_str(value: object, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field_name} 必須是非空字串")


def _validate_date(value: object) -> None:
    _validate_non_empty_str(value, "date")
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValidationError(f"date 格式錯誤，須為 YYYY-MM-DD: {value!r}") from exc


def _validate_url(value: object) -> None:
    _validate_non_empty_str(value, "url")
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValidationError(f"url 不是合法的 http/https 網址: {value!r}")


def _validate_key_points(value: object) -> None:
    if not isinstance(value, list) or len(value) != REQUIRED_KEY_POINTS:
        raise ValidationError(
            f"key_points 須恰好包含 {REQUIRED_KEY_POINTS} 點，實際: {value!r}"
        )
    for i, point in enumerate(value):
        _validate_non_empty_str(point, f"key_points[{i}]")


def validate_article(article: dict, index: int) -> list[str]:
    """驗證單篇新聞，回傳錯誤訊息清單（空清單代表通過）。"""
    errors: list[str] = []

    if not isinstance(article, dict):
        return [f"第 {index} 篇新聞不是一個物件 (object)"]

    for field in REQUIRED_FIELDS:
        if field not in article:
            errors.append(f"第 {index} 篇新聞缺少必要欄位: {field}")

    checks = {
        "title": lambda v: _validate_non_empty_str(v, "title"),
        "source": lambda v: _validate_non_empty_str(v, "source"),
        "date": _validate_date,
        "url": _validate_url,
        "key_points": _validate_key_points,
        "mermaid": lambda v: _validate_non_empty_str(v, "mermaid"),
    }

    for field, check in checks.items():
        if field not in article:
            continue
        try:
            check(article[field])
        except ValidationError as exc:
            errors.append(f"第 {index} 篇新聞 {exc}")

    return errors


def validate_daily_file(path: Path) -> list[str]:
    """驗證整天的新聞 JSON 檔案，回傳所有錯誤訊息（空清單代表通過）。"""
    errors: list[str] = []

    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"無法讀取檔案 {path}: {exc}"]

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return [f"{path} 不是合法的 JSON: {exc}"]

    if not isinstance(data, list):
        return [f"{path} 的內容必須是 JSON 陣列"]

    if len(data) != REQUIRED_ARTICLES_PER_DAY:
        errors.append(
            f"每日新聞須恰好 {REQUIRED_ARTICLES_PER_DAY} 篇，實際 {len(data)} 篇"
        )

    for i, article in enumerate(data, start=1):
        errors.extend(validate_article(article, i))

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json_file", type=Path, help="每日新聞 JSON 檔案路徑")
    args = parser.parse_args(argv)

    errors = validate_daily_file(args.json_file)

    if errors:
        print(f"驗證失敗 ({len(errors)} 個問題):", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"驗證通過: {args.json_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
