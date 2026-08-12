# CLAUDE.md

本檔案提供 Claude Code 在此專案中工作時的指引。

## 專案概述

「金融科技新聞日報」是一個自動化專案，目標是每天：

1. 蒐集並驗證 3 篇金融科技新聞，優先選擇 **AI、金融科技（Fintech）與數據分析** 交集的內容。
2. 每篇輸出標題、來源、日期、原文連結、3 點 Key Points、以及描述新聞結構的 Mermaid 圖。
3. 保存每日 JSON 歷史資料到 `data/archive/`。
4. 產生可發布到 GitHub Pages 的靜態 HTML 到 `docs/`。
5. （未來）在本機 Mac 上設定每日自動執行（例如透過 launchd 或 cron）。

詳細每日工作流程定義在 `.claude/skills/fintech-news-daily/SKILL.md`。

## 硬性規則

- **禁止捏造新聞資料。** 不可產生假新聞、示範新聞或 placeholder 內容。所有新聞必須有可追溯
  的真實原文連結。若無法取得真實新聞，應明確告知使用者，而不是生成假資料頂替。
- **Python 一律優先使用標準函式庫**，避免引入第三方套件；若確有必要才需與使用者確認。
- **所有檔案使用 UTF-8** 編碼。
- 新聞資料須先通過 `src/validate_news.py` 驗證才能寫入 `data/archive/` 或用於產生報告。
- 未經使用者明確要求，不要自動執行新聞蒐集、發布網站或設定排程。

## 專案結構

參見 `README.md` 中「專案結構」章節的完整說明。

## 開發慣例

- 新聞 JSON 檔名格式：`data/archive/YYYY-MM-DD.json`，內容為包含 3 篇新聞物件的 JSON 陣列。
- 每篇新聞物件的欄位規範，參見 `src/validate_news.py` 中的 `REQUIRED_FIELDS`。
- 報告產生流程：`data/archive/*.json` → (`validate_news.py` 驗證) → `build_report.py` → `docs/archive/*.html` + `docs/index.html`。
