#!/usr/bin/env python3
"""將每日金融科技新聞 JSON 轉換成可發布至 GitHub Pages 的靜態 HTML。

用法:
    python3 build_report.py <path/to/YYYY-MM-DD.json>

行為:
    - 先呼叫 validate_news.validate_daily_file 確認資料合法，不合法就中止、不產生檔案。
    - 產生單日報告頁面 docs/archive/YYYY-MM-DD.html。
    - 重新掃描 docs/archive/*.html，重建首頁索引 docs/index.html。

僅使用 Python 3 標準函式庫（json / pathlib / html / datetime / argparse）。
"""

from __future__ import annotations

import argparse
import json
import sys
from html import escape
from pathlib import Path

from validate_news import validate_daily_file

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_ARCHIVE_DIR = REPO_ROOT / "docs" / "archive"
DOCS_INDEX_PATH = REPO_ROOT / "docs" / "index.html"

MERMAID_CDN = "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<title>金融科技新聞日報 - {date}</title>
<script src="{mermaid_cdn}"></script>
<script>mermaid.initialize({{ startOnLoad: true }});</script>
<style>
  body {{ font-family: -apple-system, "Noto Sans TC", sans-serif; max-width: 860px;
          margin: 2rem auto; padding: 0 1rem; line-height: 1.6; }}
  article {{ border-bottom: 1px solid #ddd; padding: 1.5rem 0; }}
  h1 {{ font-size: 1.5rem; }}
  h2 {{ font-size: 1.2rem; margin-bottom: 0.2rem; }}
  .meta {{ color: #666; font-size: 0.9rem; margin-bottom: 0.8rem; }}
  ul {{ margin-top: 0.3rem; }}
  a.back {{ display: inline-block; margin-bottom: 1.5rem; }}
</style>
</head>
<body>
<a class="back" href="../index.html">&larr; 回首頁</a>
<h1>金融科技新聞日報 - {date}</h1>
{articles}
</body>
</html>
"""

ARTICLE_TEMPLATE = """<article>
  <h2>{title}</h2>
  <div class="meta">來源: {source} | 日期: {date} | <a href="{url}" target="_blank" rel="noopener noreferrer">原文連結</a></div>
  <ul>
{key_points}
  </ul>
  <pre class="mermaid">
{mermaid}
  </pre>
</article>
"""

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<title>金融科技新聞日報</title>
<style>
  body {{ font-family: -apple-system, "Noto Sans TC", sans-serif; max-width: 860px;
          margin: 2rem auto; padding: 0 1rem; line-height: 1.6; }}
  li {{ margin: 0.3rem 0; }}
</style>
</head>
<body>
<h1>金融科技新聞日報</h1>
<ul>
{entries}
</ul>
</body>
</html>
"""


def render_article(article: dict) -> str:
    key_points_html = "\n".join(
        f"    <li>{escape(point)}</li>" for point in article["key_points"]
    )
    return ARTICLE_TEMPLATE.format(
        title=escape(article["title"]),
        source=escape(article["source"]),
        date=escape(article["date"]),
        url=escape(article["url"]),
        key_points=key_points_html,
        mermaid=article["mermaid"],
    )


def build_daily_page(json_path: Path) -> Path:
    errors = validate_daily_file(json_path)
    if errors:
        raise ValueError(
            f"{json_path} 未通過驗證，無法產生報告:\n" + "\n".join(f"  - {e}" for e in errors)
        )

    articles = json.loads(json_path.read_text(encoding="utf-8"))
    report_date = json_path.stem  # 期望檔名為 YYYY-MM-DD.json

    articles_html = "\n".join(render_article(a) for a in articles)
    page_html = PAGE_TEMPLATE.format(
        date=escape(report_date), mermaid_cdn=MERMAID_CDN, articles=articles_html
    )

    DOCS_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DOCS_ARCHIVE_DIR / f"{report_date}.html"
    out_path.write_text(page_html, encoding="utf-8")
    return out_path


def rebuild_index() -> Path:
    dates = sorted(
        (p.stem for p in DOCS_ARCHIVE_DIR.glob("*.html")),
        reverse=True,
    )
    entries = "\n".join(
        f'  <li><a href="archive/{d}.html">{escape(d)}</a></li>' for d in dates
    )
    if not entries:
        entries = "  <li>尚無已發布的日報</li>"

    index_html = INDEX_TEMPLATE.format(entries=entries)
    DOCS_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOCS_INDEX_PATH.write_text(index_html, encoding="utf-8")
    return DOCS_INDEX_PATH


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json_file", type=Path, help="每日新聞 JSON 檔案路徑")
    args = parser.parse_args(argv)

    try:
        out_path = build_daily_page(args.json_file)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    index_path = rebuild_index()
    print(f"已產生: {out_path}")
    print(f"已更新索引: {index_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
