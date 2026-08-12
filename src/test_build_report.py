#!/usr/bin/env python3
"""build_report.py 的 unittest 測試（僅用標準函式庫，皆使用 tempfile 暫存目錄）。

用法:
    python3 -m unittest discover -s src -p "test_*.py"
    python3 src/test_build_report.py
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_report  # noqa: E402
from test_validate_news import make_report_data  # noqa: E402


class BuildReportPositiveTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.tmp_path = Path(self._tmpdir.name)
        self.json_path = self.tmp_path / "latest.json"
        self.archive_dir = self.tmp_path / "docs" / "archive"
        self.index_path = self.tmp_path / "docs" / "index.html"

    def _write_json(self, data: dict) -> None:
        self.json_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def test_build_report_produces_archive_and_index(self) -> None:
        self._write_json(make_report_data())
        archive_path, index_path = build_report.build_report(
            self.json_path, archive_dir=self.archive_dir, index_path=self.index_path
        )
        self.assertTrue(archive_path.exists())
        self.assertTrue(index_path.exists())
        self.assertEqual(archive_path.name, "2026-08-12.html")

    def test_output_contains_source_type_labels(self) -> None:
        self._write_json(make_report_data())
        archive_path, _ = build_report.build_report(
            self.json_path, archive_dir=self.archive_dir, index_path=self.index_path
        )
        html = archive_path.read_text(encoding="utf-8")
        # make_report_data 的三篇分別為 independent_media / independent_media / press_release
        self.assertIn("獨立媒體報導", html)
        self.assertIn("企業新聞稿", html)

    def test_output_contains_freshness_note(self) -> None:
        data = make_report_data()
        data["articles"][0]["freshness_note"] = "獨家新鮮度測試字串 12345"
        self._write_json(data)
        archive_path, _ = build_report.build_report(
            self.json_path, archive_dir=self.archive_dir, index_path=self.index_path
        )
        html = archive_path.read_text(encoding="utf-8")
        self.assertIn("獨家新鮮度測試字串 12345", html)

    def test_output_contains_event_date(self) -> None:
        data = make_report_data()
        data["articles"][0]["event_date"] = "2026-08-06"
        self._write_json(data)
        archive_path, _ = build_report.build_report(
            self.json_path, archive_dir=self.archive_dir, index_path=self.index_path
        )
        html = archive_path.read_text(encoding="utf-8")
        self.assertIn("2026-08-06", html)

    def test_unknown_source_type_label_falls_back_to_raw_value(self) -> None:
        self.assertEqual(
            build_report.SOURCE_TYPE_LABELS.get("not_a_real_type", "not_a_real_type"),
            "not_a_real_type",
        )

    def test_no_leftover_tmp_files_after_successful_build(self) -> None:
        self._write_json(make_report_data())
        build_report.build_report(
            self.json_path, archive_dir=self.archive_dir, index_path=self.index_path
        )
        leftover = list(self.archive_dir.glob(".*.tmp")) + list(
            self.index_path.parent.glob(".*.tmp")
        )
        self.assertEqual(leftover, [])

    def test_html_escaping_of_special_characters(self) -> None:
        data = make_report_data()
        data["articles"][0]["title_zh"] = '<script>alert(1)</script> & "測試"'
        data["articles"][0]["freshness_note"] = "含 <b>標籤</b> 與 & 符號"
        self._write_json(data)
        archive_path, _ = build_report.build_report(
            self.json_path, archive_dir=self.archive_dir, index_path=self.index_path
        )
        html = archive_path.read_text(encoding="utf-8")
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<b>標籤</b>", html)

    def test_mermaid_flowchart_code_is_embedded_inline(self) -> None:
        self._write_json(make_report_data())
        archive_path, _ = build_report.build_report(
            self.json_path, archive_dir=self.archive_dir, index_path=self.index_path
        )
        html = archive_path.read_text(encoding="utf-8")
        self.assertIn('<pre class="mermaid">', html)
        self.assertIn("flowchart TD", html)

    def test_mermaid_container_wraps_each_diagram(self) -> None:
        self._write_json(make_report_data())
        archive_path, _ = build_report.build_report(
            self.json_path, archive_dir=self.archive_dir, index_path=self.index_path
        )
        html = archive_path.read_text(encoding="utf-8")
        self.assertEqual(html.count('<div class="mermaid-container">'), 3)

    def test_mermaid_container_css_has_overflow_x_auto(self) -> None:
        self._write_json(make_report_data())
        archive_path, _ = build_report.build_report(
            self.json_path, archive_dir=self.archive_dir, index_path=self.index_path
        )
        html = archive_path.read_text(encoding="utf-8")
        self.assertIn("overflow-x: auto", html)

    def test_no_zoom_modal_markup_or_javascript_remains(self) -> None:
        self._write_json(make_report_data())
        archive_path, index_path = build_report.build_report(
            self.json_path, archive_dir=self.archive_dir, index_path=self.index_path
        )
        for path in (archive_path, index_path):
            html = path.read_text(encoding="utf-8")
            for forbidden in (
                "zoom-overlay",
                "zoom-content",
                "zoom-close",
                "openZoom",
                "closeZoom",
                "modal-open",
                "mermaid-wrap",
            ):
                self.assertNotIn(forbidden, html, f"{forbidden!r} 不應出現在 {path}")


class BuildReportNegativeTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.tmp_path = Path(self._tmpdir.name)
        self.json_path = self.tmp_path / "latest.json"
        self.archive_dir = self.tmp_path / "docs" / "archive"
        self.index_path = self.tmp_path / "docs" / "index.html"

    def _write_json(self, data: dict) -> None:
        self.json_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def test_missing_event_date_raises_value_error(self) -> None:
        data = make_report_data()
        del data["articles"][0]["event_date"]
        self._write_json(data)
        with self.assertRaises(ValueError):
            build_report.build_report(
                self.json_path, archive_dir=self.archive_dir, index_path=self.index_path
            )

    def test_invalid_source_type_distribution_raises_value_error(self) -> None:
        data = make_report_data()
        data["articles"][0]["source_type"] = "press_release"
        # articles[0] 與 articles[2] 皆為 press_release，且 independent_media 剩 1 篇
        self._write_json(data)
        with self.assertRaises(ValueError):
            build_report.build_report(
                self.json_path, archive_dir=self.archive_dir, index_path=self.index_path
            )

    def test_failed_validation_does_not_overwrite_existing_html(self) -> None:
        self._write_json(make_report_data())
        build_report.build_report(
            self.json_path, archive_dir=self.archive_dir, index_path=self.index_path
        )
        original_index_content = self.index_path.read_text(encoding="utf-8")
        original_archive_content = (self.archive_dir / "2026-08-12.html").read_text(
            encoding="utf-8"
        )

        bad_data = make_report_data()
        del bad_data["articles"][0]["source_type"]
        self._write_json(bad_data)
        with self.assertRaises(ValueError):
            build_report.build_report(
                self.json_path, archive_dir=self.archive_dir, index_path=self.index_path
            )

        self.assertEqual(
            self.index_path.read_text(encoding="utf-8"), original_index_content
        )
        self.assertEqual(
            (self.archive_dir / "2026-08-12.html").read_text(encoding="utf-8"),
            original_archive_content,
        )


if __name__ == "__main__":
    unittest.main()
