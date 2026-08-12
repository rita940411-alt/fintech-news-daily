#!/usr/bin/env python3
"""驗證金融科技新聞日報 JSON 是否符合統一 schema。

用法:
    python3 validate_news.py [path/to/report.json]

不指定路徑時，預設驗證 data/latest.json。

Schema 定義於 .claude/skills/fintech-news-daily/SKILL.md 第四節。根層必須是一個 JSON
物件（非陣列），包含 report_date / generated_at / timezone / selection_window / articles。

驗證規則:
    - JSON 是否可解析。
    - 根層欄位是否完整：report_date, generated_at, timezone, selection_window, articles。
    - report_date 為 YYYY-MM-DD；generated_at 為含時區的 ISO 8601 datetime。
    - timezone 固定為 "Asia/Taipei"；selection_window 固定為 "24h" 或 "72h"。
    - articles 是否剛好 3 篇，且每篇的 url 互不重複。
    - 每篇 article 必須包含 title_zh / title_original / source / url / published_at /
      verified_at / selected_reason / key_points / mermaid。
    - url 必須是 https。
    - published_at 為 YYYY-MM-DD；verified_at 為含時區的 ISO 8601 datetime。
    - key_points 恰好 3 點、皆為非空字串、且彼此不重複。
    - mermaid 為非空字串且以 "flowchart TD" 開頭。
    - 欄位型別錯誤（例如該是字串卻是數字）視為驗證失敗。

驗證失敗時回傳非 0 的 exit code；驗證成功回傳 0。
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_PATH = REPO_ROOT / "data" / "latest.json"

ROOT_REQUIRED_FIELDS = (
    "report_date",
    "generated_at",
    "timezone",
    "selection_window",
    "articles",
)
ARTICLE_REQUIRED_FIELDS = (
    "title_zh",
    "title_original",
    "source",
    "url",
    "published_at",
    "verified_at",
    "selected_reason",
    "key_points",
    "mermaid",
)

REQUIRED_TIMEZONE = "Asia/Taipei"
VALID_SELECTION_WINDOWS = ("24h", "72h")
REQUIRED_ARTICLES_COUNT = 3
REQUIRED_KEY_POINTS_COUNT = 3
MERMAID_REQUIRED_PREFIX = "flowchart TD"


class ValidationError(Exception):
    """代表一筆驗證失敗，附帶可讀的錯誤訊息。"""


def _validate_non_empty_str(value: object, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field_name} 必須是非空字串")


def _validate_date(value: object, field_name: str) -> None:
    _validate_non_empty_str(value, field_name)
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValidationError(
            f"{field_name} 格式錯誤，須為 YYYY-MM-DD: {value!r}"
        ) from exc


def _validate_iso_datetime_with_tz(value: object, field_name: str) -> None:
    _validate_non_empty_str(value, field_name)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError(
            f"{field_name} 不是合法的 ISO 8601 datetime（需含時區偏移，例如 +08:00）: {value!r}"
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValidationError(f"{field_name} 缺少時區資訊: {value!r}")


def _validate_timezone(value: object) -> None:
    if value != REQUIRED_TIMEZONE:
        raise ValidationError(
            f"timezone 須固定為 {REQUIRED_TIMEZONE!r}，實際: {value!r}"
        )


def _validate_selection_window(value: object) -> None:
    if value not in VALID_SELECTION_WINDOWS:
        raise ValidationError(
            f"selection_window 須為 {VALID_SELECTION_WINDOWS!r}，實際: {value!r}"
        )


def _validate_https_url(value: object) -> None:
    _validate_non_empty_str(value, "url")
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValidationError(f"url 必須是 https 開頭的合法網址: {value!r}")


def _validate_key_points(value: object) -> None:
    if not isinstance(value, list) or len(value) != REQUIRED_KEY_POINTS_COUNT:
        raise ValidationError(
            f"key_points 須恰好包含 {REQUIRED_KEY_POINTS_COUNT} 點，實際: {value!r}"
        )
    for i, point in enumerate(value):
        _validate_non_empty_str(point, f"key_points[{i}]")
    if len(set(value)) != len(value):
        raise ValidationError("key_points 三點不可重複")


def _validate_mermaid(value: object) -> None:
    _validate_non_empty_str(value, "mermaid")
    if not value.strip().startswith(MERMAID_REQUIRED_PREFIX):
        raise ValidationError(f"mermaid 必須以 {MERMAID_REQUIRED_PREFIX!r} 開頭")


def validate_article(article: object, index: int) -> list[str]:
    """驗證單篇新聞，回傳錯誤訊息清單（空清單代表通過）。"""
    errors: list[str] = []

    if not isinstance(article, dict):
        return [f"第 {index} 篇新聞不是一個物件 (object)"]

    for field in ARTICLE_REQUIRED_FIELDS:
        if field not in article:
            errors.append(f"第 {index} 篇新聞缺少必要欄位: {field}")

    checks = {
        "title_zh": lambda v: _validate_non_empty_str(v, "title_zh"),
        "title_original": lambda v: _validate_non_empty_str(v, "title_original"),
        "source": lambda v: _validate_non_empty_str(v, "source"),
        "url": _validate_https_url,
        "published_at": lambda v: _validate_date(v, "published_at"),
        "verified_at": lambda v: _validate_iso_datetime_with_tz(v, "verified_at"),
        "selected_reason": lambda v: _validate_non_empty_str(v, "selected_reason"),
        "key_points": _validate_key_points,
        "mermaid": _validate_mermaid,
    }

    for field, check in checks.items():
        if field not in article:
            continue
        try:
            check(article[field])
        except ValidationError as exc:
            errors.append(f"第 {index} 篇新聞 {exc}")

    return errors


def validate_report_data(data: object) -> list[str]:
    """驗證整份報告（已解析的 JSON 物件），回傳所有錯誤訊息（空清單代表通過）。"""
    errors: list[str] = []

    if not isinstance(data, dict):
        return ["根層資料必須是一個 JSON 物件（object），而非陣列或其他型別"]

    for field in ROOT_REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"根層缺少必要欄位: {field}")

    root_checks = {
        "report_date": lambda v: _validate_date(v, "report_date"),
        "generated_at": lambda v: _validate_iso_datetime_with_tz(v, "generated_at"),
        "timezone": _validate_timezone,
        "selection_window": _validate_selection_window,
    }
    for field, check in root_checks.items():
        if field not in data:
            continue
        try:
            check(data[field])
        except ValidationError as exc:
            errors.append(str(exc))

    articles = data.get("articles")
    if not isinstance(articles, list):
        errors.append("articles 必須是 JSON 陣列")
        return errors

    if len(articles) != REQUIRED_ARTICLES_COUNT:
        errors.append(
            f"articles 須恰好 {REQUIRED_ARTICLES_COUNT} 篇，實際 {len(articles)} 篇"
        )

    for i, article in enumerate(articles, start=1):
        errors.extend(validate_article(article, i))

    urls = [
        article["url"]
        for article in articles
        if isinstance(article, dict) and isinstance(article.get("url"), str)
    ]
    if len(urls) != len(set(urls)):
        errors.append("articles 的 url 不可重複")

    return errors


def validate_daily_file(path: Path) -> list[str]:
    """讀取並驗證報告 JSON 檔案，回傳所有錯誤訊息（空清單代表通過）。"""
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"無法讀取檔案 {path}: {exc}"]

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return [f"{path} 不是合法的 JSON: {exc}"]

    return validate_report_data(data)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "json_file",
        type=Path,
        nargs="?",
        default=DEFAULT_DATA_PATH,
        help=f"報告 JSON 檔案路徑（預設: {DEFAULT_DATA_PATH}）",
    )
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
