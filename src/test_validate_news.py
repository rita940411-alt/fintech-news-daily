#!/usr/bin/env python3
"""validate_news.py 的 unittest 測試（僅用標準函式庫，含 tempfile-based CLI 測試）。

用法:
    python3 -m unittest discover -s src -p "test_*.py"
    python3 src/test_validate_news.py
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import validate_news  # noqa: E402


def make_article(**overrides: object) -> dict:
    article = {
        "title_zh": "測試標題",
        "title_original": "Test Title",
        "source": "Test Source",
        "source_type": "independent_media",
        "url": "https://example.com/news/test",
        "published_at": "2026-08-10",
        "event_date": "2026-08-10",
        "verified_at": "2026-08-12T15:23:03+08:00",
        "freshness_note": "事件公告日與引用網頁發布日相同，屬 72 小時內首次公開報導。",
        "selected_reason": "符合 AI 與金融科技交集主題。",
        "key_points": ["第一點事實。", "第二點事實。", "第三點事實。"],
        "mermaid": "flowchart TD\n    A[\"事件\"]:::gray\n\n    classDef gray fill:#9e9e9e,color:#ffffff;",
    }
    article.update(overrides)
    return article


def make_report_data(**root_overrides: object) -> dict:
    articles = [
        make_article(
            source_type="independent_media",
            url="https://example.com/news/a",
        ),
        make_article(
            source_type="independent_media",
            url="https://example.com/news/b",
        ),
        make_article(
            source_type="press_release",
            url="https://example.com/news/c",
        ),
    ]
    data = {
        "report_date": "2026-08-12",
        "generated_at": "2026-08-12T15:23:03+08:00",
        "timezone": "Asia/Taipei",
        "selection_window": "72h",
        "articles": articles,
    }
    data.update(root_overrides)
    return data


def make_candidate(**overrides: object) -> dict:
    candidate = {
        "title": "候選標題",
        "source": "Candidate Source",
        "url": "https://example.com/candidate/1",
        "published_at": "2026-08-10",
        "event_date": "2026-08-10",
        "source_type": "independent_media",
        "fetch_status": "success",
        "decision": "rejected",
        "rejection_reason": "報導同一事件，與另一篇候選重複。",
        "duplicate_of": None,
    }
    candidate.update(overrides)
    return candidate


def make_candidates_data(count: int = 8, **root_overrides: object) -> dict:
    candidates = [
        make_candidate(
            url=f"https://example.com/candidate/{i}",
            decision="rejected",
            rejection_reason="示範淘汰原因。",
        )
        for i in range(count)
    ]
    data = {
        "report_date": "2026-08-12",
        "searched_at": "2026-08-12T15:23:03+08:00",
        "timezone": "Asia/Taipei",
        "candidate_count": count,
        "candidates": candidates,
    }
    data.update(root_overrides)
    return data


class ValidateReportDataPositiveTests(unittest.TestCase):
    def test_valid_report_passes(self) -> None:
        errors = validate_news.validate_report_data(make_report_data())
        self.assertEqual(errors, [])

    def test_valid_report_with_three_independent_media_passes(self) -> None:
        data = make_report_data()
        data["articles"][2]["source_type"] = "independent_media"
        errors = validate_news.validate_report_data(data)
        self.assertEqual(errors, [])

    def test_valid_report_with_official_source_instead_of_press_release_passes(self) -> None:
        data = make_report_data()
        data["articles"][2]["source_type"] = "official_source"
        errors = validate_news.validate_report_data(data)
        self.assertEqual(errors, [])


class ValidateReportDataNegativeTests(unittest.TestCase):
    def test_missing_event_date_fails(self) -> None:
        data = make_report_data()
        del data["articles"][0]["event_date"]
        errors = validate_news.validate_report_data(data)
        self.assertTrue(any("event_date" in e for e in errors))

    def test_missing_source_type_fails(self) -> None:
        data = make_report_data()
        del data["articles"][0]["source_type"]
        errors = validate_news.validate_report_data(data)
        self.assertTrue(any("source_type" in e for e in errors))

    def test_missing_freshness_note_fails(self) -> None:
        data = make_report_data()
        del data["articles"][0]["freshness_note"]
        errors = validate_news.validate_report_data(data)
        self.assertTrue(any("freshness_note" in e for e in errors))

    def test_invalid_source_type_value_fails(self) -> None:
        data = make_report_data()
        data["articles"][0]["source_type"] = "blog_post"
        errors = validate_news.validate_report_data(data)
        self.assertTrue(any("source_type" in e for e in errors))

    def test_invalid_event_date_format_fails(self) -> None:
        data = make_report_data()
        data["articles"][0]["event_date"] = "2026/08/10"
        errors = validate_news.validate_report_data(data)
        self.assertTrue(any("event_date" in e for e in errors))

    def test_empty_freshness_note_fails(self) -> None:
        data = make_report_data()
        data["articles"][0]["freshness_note"] = "   "
        errors = validate_news.validate_report_data(data)
        self.assertTrue(any("freshness_note" in e for e in errors))

    def test_less_than_two_independent_media_fails(self) -> None:
        data = make_report_data()
        data["articles"][0]["source_type"] = "press_release"
        # articles[2] 已經是 press_release，此時只有 1 篇 independent_media
        errors = validate_news.validate_report_data(data)
        self.assertTrue(any("independent_media" in e for e in errors))

    def test_official_source_plus_press_release_over_limit_fails(self) -> None:
        data = make_report_data()
        data["articles"][0]["source_type"] = "official_source"
        # articles[0]=official_source, articles[2]=press_release -> 合計 2 篇，超過上限 1
        errors = validate_news.validate_report_data(data)
        self.assertTrue(
            any("official_source" in e and "press_release" in e for e in errors)
        )

    def test_aggregator_reduces_independent_media_below_minimum(self) -> None:
        data = make_report_data()
        data["articles"][1]["source_type"] = "aggregator"
        # 只剩 1 篇 independent_media（articles[0]），articles[2] 仍是 press_release
        errors = validate_news.validate_report_data(data)
        self.assertTrue(any("independent_media" in e for e in errors))

    def test_duplicate_urls_fail(self) -> None:
        data = make_report_data()
        data["articles"][1]["url"] = data["articles"][0]["url"]
        errors = validate_news.validate_report_data(data)
        self.assertTrue(any("url 不可重複" in e for e in errors))

    def test_wrong_key_points_count_fails(self) -> None:
        data = make_report_data()
        data["articles"][0]["key_points"] = ["只有一點"]
        errors = validate_news.validate_report_data(data)
        self.assertTrue(any("key_points" in e for e in errors))

    def test_mermaid_without_prefix_fails(self) -> None:
        data = make_report_data()
        data["articles"][0]["mermaid"] = "graph TD\n    A --> B"
        errors = validate_news.validate_report_data(data)
        self.assertTrue(any("flowchart TD" in e for e in errors))

    def test_wrong_timezone_fails(self) -> None:
        data = make_report_data(timezone="UTC")
        errors = validate_news.validate_report_data(data)
        self.assertTrue(any("timezone" in e for e in errors))

    def test_wrong_selection_window_fails(self) -> None:
        data = make_report_data(selection_window="48h")
        errors = validate_news.validate_report_data(data)
        self.assertTrue(any("selection_window" in e for e in errors))

    def test_non_https_url_fails(self) -> None:
        data = make_report_data()
        data["articles"][0]["url"] = "http://example.com/news/a"
        errors = validate_news.validate_report_data(data)
        self.assertTrue(any("url" in e for e in errors))


class ValidateCandidatesDataPositiveTests(unittest.TestCase):
    def test_valid_candidates_passes(self) -> None:
        errors = validate_news.validate_candidates_data(make_candidates_data())
        self.assertEqual(errors, [])

    def test_selected_candidate_with_null_rejection_reason_passes(self) -> None:
        data = make_candidates_data()
        data["candidates"][0]["decision"] = "selected"
        data["candidates"][0]["rejection_reason"] = None
        errors = validate_news.validate_candidates_data(data)
        self.assertEqual(errors, [])

    def test_duplicate_of_pointing_to_another_url_passes(self) -> None:
        data = make_candidates_data()
        data["candidates"][1]["duplicate_of"] = data["candidates"][0]["url"]
        errors = validate_news.validate_candidates_data(data)
        self.assertEqual(errors, [])


class ValidateCandidatesDataNegativeTests(unittest.TestCase):
    def test_fewer_than_eight_candidates_fails(self) -> None:
        data = make_candidates_data(count=7)
        errors = validate_news.validate_candidates_data(data)
        self.assertTrue(any("至少須有" in e for e in errors))

    def test_candidate_count_mismatch_fails(self) -> None:
        data = make_candidates_data()
        data["candidate_count"] = 9
        errors = validate_news.validate_candidates_data(data)
        self.assertTrue(any("candidate_count" in e for e in errors))

    def test_rejected_without_reason_fails(self) -> None:
        data = make_candidates_data()
        data["candidates"][0]["decision"] = "rejected"
        data["candidates"][0]["rejection_reason"] = None
        errors = validate_news.validate_candidates_data(data)
        self.assertTrue(any("rejection_reason" in e for e in errors))

    def test_selected_with_non_null_reason_fails(self) -> None:
        data = make_candidates_data()
        data["candidates"][0]["decision"] = "selected"
        data["candidates"][0]["rejection_reason"] = "不應該有原因"
        errors = validate_news.validate_candidates_data(data)
        self.assertTrue(any("rejection_reason" in e for e in errors))

    def test_invalid_fetch_status_fails(self) -> None:
        data = make_candidates_data()
        data["candidates"][0]["fetch_status"] = "pending"
        errors = validate_news.validate_candidates_data(data)
        self.assertTrue(any("fetch_status" in e for e in errors))

    def test_invalid_decision_fails(self) -> None:
        data = make_candidates_data()
        data["candidates"][0]["decision"] = "maybe"
        errors = validate_news.validate_candidates_data(data)
        self.assertTrue(any("decision" in e for e in errors))

    def test_missing_event_date_fails(self) -> None:
        data = make_candidates_data()
        del data["candidates"][0]["event_date"]
        errors = validate_news.validate_candidates_data(data)
        self.assertTrue(any("event_date" in e for e in errors))

    def test_invalid_source_type_fails(self) -> None:
        data = make_candidates_data()
        data["candidates"][0]["source_type"] = "blog"
        errors = validate_news.validate_candidates_data(data)
        self.assertTrue(any("source_type" in e for e in errors))


class ValidateNewsCliTests(unittest.TestCase):
    """透過 subprocess 呼叫 CLI，驗證 tempfile 中的報告 JSON 與候選 JSON。"""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.tmp_path = Path(self._tmpdir.name)
        self.script_path = Path(__file__).resolve().parent / "validate_news.py"

    def _run_cli(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(self.script_path), *args],
            capture_output=True,
            text=True,
        )

    def test_cli_valid_report_exits_zero(self) -> None:
        report_path = self.tmp_path / "report.json"
        report_path.write_text(
            json.dumps(make_report_data(), ensure_ascii=False), encoding="utf-8"
        )
        result = self._run_cli(str(report_path))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("驗證通過", result.stdout)

    def test_cli_invalid_report_exits_nonzero(self) -> None:
        data = make_report_data()
        del data["articles"][0]["event_date"]
        report_path = self.tmp_path / "report.json"
        report_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        result = self._run_cli(str(report_path))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("event_date", result.stderr)

    def test_cli_valid_candidates_exits_zero(self) -> None:
        candidates_path = self.tmp_path / "candidates.json"
        candidates_path.write_text(
            json.dumps(make_candidates_data(), ensure_ascii=False), encoding="utf-8"
        )
        result = self._run_cli("--candidates", str(candidates_path))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("驗證通過", result.stdout)

    def test_cli_too_few_candidates_exits_nonzero(self) -> None:
        candidates_path = self.tmp_path / "candidates.json"
        candidates_path.write_text(
            json.dumps(make_candidates_data(count=5), ensure_ascii=False),
            encoding="utf-8",
        )
        result = self._run_cli("--candidates", str(candidates_path))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("至少須有", result.stderr)


class DeepcopyIsolationSanityTest(unittest.TestCase):
    """確認測試輔助函式回傳的是獨立物件，避免測試間互相污染。"""

    def test_make_report_data_returns_independent_copies(self) -> None:
        a = make_report_data()
        b = make_report_data()
        a["articles"][0]["title_zh"] = "改過的標題"
        self.assertNotEqual(a["articles"][0]["title_zh"], b["articles"][0]["title_zh"])
        self.assertEqual(copy.deepcopy(b), make_report_data())


if __name__ == "__main__":
    unittest.main()
