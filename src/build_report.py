#!/usr/bin/env python3
"""將金融科技新聞日報 JSON 轉換成可發布至 GitHub Pages 的靜態 HTML。

用法:
    python3 build_report.py [path/to/report.json]

不指定路徑時，預設讀取 data/latest.json。

行為:
    - 先呼叫 validate_news.validate_daily_file 確認資料合法，不合法就中止、不寫入任何檔案
      （既有的 docs/index.html、docs/archive/*.html 維持不變）。
    - 產生 docs/archive/YYYY-MM-DD.html（檔名日期取自 JSON 內的 report_date 欄位）。
    - 產生 docs/index.html（顯示最新報告內容，並附上歷史日報清單）。
    - 所有輸出一律先寫入暫存檔，成功後才以原子操作取代正式檔案。

僅使用 Python 3 標準函式庫（json / pathlib / html / datetime / tempfile / os / argparse）。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from html import escape
from pathlib import Path

from validate_news import DEFAULT_DATA_PATH, validate_daily_file

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_ARCHIVE_DIR = REPO_ROOT / "docs" / "archive"
DOCS_INDEX_PATH = REPO_ROOT / "docs" / "index.html"

MERMAID_CDN = "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"

SOURCE_TYPE_LABELS = {
    "independent_media": "獨立媒體報導",
    "official_source": "官方來源",
    "press_release": "企業新聞稿",
    "aggregator": "轉載/聚合網站",
}

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>金融科技新聞日報 - {report_date}</title>
<script src="{mermaid_cdn}"></script>
<script>mermaid.initialize({{ startOnLoad: true }});</script>
<style>
  body {{ font-family: -apple-system, "Noto Sans TC", sans-serif; max-width: 860px;
          margin: 2rem auto; padding: 0 1rem; line-height: 1.6; }}
  article {{ border-bottom: 1px solid #ddd; padding: 1.5rem 0; }}
  h1 {{ font-size: 1.5rem; margin-bottom: 0.2rem; }}
  h2 {{ font-size: 1.2rem; margin-bottom: 0.2rem; }}
  .subtitle {{ color: #666; font-size: 0.85rem; margin-bottom: 1.5rem; }}
  .meta {{ color: #666; font-size: 0.9rem; margin-bottom: 0.8rem; }}
  .source-type-badge {{ display: inline-block; padding: 0.1rem 0.5rem; border-radius: 999px;
                          font-size: 0.75rem; background: #eee; color: #333;
                          margin-left: 0.4rem; }}
  .freshness-note {{ color: #666; font-size: 0.85rem; margin-bottom: 0.8rem;
                       font-style: italic; }}
  ul {{ margin-top: 0.3rem; }}
  a.back {{ display: inline-block; margin-bottom: 1.5rem; }}
  .archive-list {{ margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #ddd; }}
  .mermaid-container {{ width: 100%; max-width: 100%; overflow-x: auto;
                          background: #ffffff; padding: 16px; border-radius: 12px;
                          box-sizing: border-box; }}
  .mermaid-container svg {{ display: block; max-width: 100%; height: auto; }}
</style>
</head>
<body>
{nav}<h1>金融科技新聞日報 - {report_date}</h1>
<div class="subtitle">產生時間: {generated_at}</div>
{articles}
{archive_links}
</body>
</html>
"""

ARTICLE_TEMPLATE = """<article>
  <h2>{title_zh}</h2>
  <div class="meta">來源: {source}<span class="source-type-badge">{source_type_label}</span> | 發布日期: {published_at} | 事件日期: {event_date} | <a href="{url}" target="_blank" rel="noopener noreferrer">原文連結</a></div>
  <div class="freshness-note">新鮮度說明: {freshness_note}</div>
  <ul>
{key_points}
  </ul>
  <div class="mermaid-container">
    <pre class="mermaid">
{mermaid}
    </pre>
  </div>
</article>
"""

ARCHIVE_LIST_TEMPLATE = """<div class="archive-list">
  <h2>歷史日報</h2>
  <ul>
{entries}
  </ul>
</div>
"""


def render_article(article: dict) -> str:
    key_points_html = "\n".join(
        f"    <li>{escape(point)}</li>" for point in article["key_points"]
    )
    source_type_label = SOURCE_TYPE_LABELS.get(
        article["source_type"], article["source_type"]
    )
    return ARTICLE_TEMPLATE.format(
        title_zh=escape(article["title_zh"]),
        source=escape(article["source"]),
        source_type_label=escape(source_type_label),
        published_at=escape(article["published_at"]),
        event_date=escape(article["event_date"]),
        freshness_note=escape(article["freshness_note"]),
        url=escape(article["url"]),
        key_points=key_points_html,
        mermaid=escape(article["mermaid"]),
    )


def render_archive_links(archive_dir: Path = DOCS_ARCHIVE_DIR) -> str:
    if archive_dir.exists():
        dates = sorted((p.stem for p in archive_dir.glob("*.html")), reverse=True)
    else:
        dates = []

    if dates:
        entries = "\n".join(
            f'    <li><a href="archive/{d}.html">{escape(d)}</a></li>' for d in dates
        )
    else:
        entries = "    <li>尚無歷史日報</li>"

    return ARCHIVE_LIST_TEMPLATE.format(entries=entries)


def render_page(
    data: dict, *, is_archive_page: bool, archive_dir: Path = DOCS_ARCHIVE_DIR
) -> str:
    articles_html = "\n".join(render_article(a) for a in data["articles"])
    nav_html = (
        '<a class="back" href="../index.html">&larr; 回首頁</a>\n' if is_archive_page else ""
    )
    archive_links_html = "" if is_archive_page else render_archive_links(archive_dir)

    return PAGE_TEMPLATE.format(
        report_date=escape(data["report_date"]),
        generated_at=escape(data["generated_at"]),
        mermaid_cdn=MERMAID_CDN,
        nav=nav_html,
        articles=articles_html,
        archive_links=archive_links_html,
    )


def _write_atomic(path: Path, content: str) -> None:
    """先寫入同目錄下的暫存檔，成功後再以原子操作取代正式檔案。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def build_report(
    json_path: Path,
    *,
    archive_dir: Path = DOCS_ARCHIVE_DIR,
    index_path: Path = DOCS_INDEX_PATH,
) -> tuple[Path, Path]:
    """驗證並產生 <archive_dir>/YYYY-MM-DD.html 與 <index_path>。

    archive_dir / index_path 預設為正式的 docs/archive、docs/index.html；可覆寫以指向
    暫存測試目錄。驗證失敗時拋出 ValueError，且不會寫入或覆蓋任何既有的 HTML 檔案。
    """
    errors = validate_daily_file(json_path)
    if errors:
        raise ValueError(
            f"{json_path} 未通過驗證，無法產生報告:\n"
            + "\n".join(f"  - {e}" for e in errors)
        )

    data = json.loads(json_path.read_text(encoding="utf-8"))
    report_date = data["report_date"]

    archive_path = archive_dir / f"{report_date}.html"
    _write_atomic(archive_path, render_page(data, is_archive_page=True))

    # 索引頁需要看到剛寫入的當日 archive 檔案，因此在其後才產生。
    _write_atomic(
        index_path, render_page(data, is_archive_page=False, archive_dir=archive_dir)
    )

    return archive_path, index_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "json_file",
        type=Path,
        nargs="?",
        default=DEFAULT_DATA_PATH,
        help=f"報告 JSON 檔案路徑（預設: {DEFAULT_DATA_PATH}）",
    )
    parser.add_argument(
        "--archive-dir",
        type=Path,
        default=DOCS_ARCHIVE_DIR,
        help=f"輸出 archive HTML 的目錄（預設: {DOCS_ARCHIVE_DIR}）",
    )
    parser.add_argument(
        "--index-file",
        type=Path,
        default=DOCS_INDEX_PATH,
        help=f"輸出 index.html 的路徑（預設: {DOCS_INDEX_PATH}）",
    )
    args = parser.parse_args(argv)

    try:
        archive_path, index_path = build_report(
            args.json_file, archive_dir=args.archive_dir, index_path=args.index_file
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"已產生: {archive_path}")
    print(f"已產生: {index_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
