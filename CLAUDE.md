# CLAUDE.md

本檔案提供 Claude Code 在此專案中工作時的指引。

## 專案概述

「金融科技新聞日報」是一個自動化專案，目標是每天：

1. 以 **Asia/Taipei** 時區，蒐集並核對 3 篇金融科技新聞，優先選擇
   **AI、金融科技（Fintech）與數據分析** 交集的內容。
2. 每篇輸出中文標題、原文標題、來源、日期、原文連結、選入理由、3 點 Key Points、以及描述
   新聞結構的 Mermaid `flowchart TD` 圖。
3. 保存每日 JSON 歷史資料到 `data/archive/`，並同步寫入 `data/latest.json`。
4. 產生可發布到 GitHub Pages 的靜態 HTML 到 `docs/`。
5. （未來）在本機 Mac 上設定每日自動執行（例如透過 launchd 或 cron）。

完整每日工作流程、選題規則、搜尋與驗證流程、統一 JSON schema、Key Points 與 Mermaid 規格，
定義在 `.claude/skills/fintech-news-daily/SKILL.md`。此技能設定
`disable-model-invocation: true`，**只能由使用者輸入 `/fintech-news-daily` 明確觸發**，
不可由模型自行判斷觸發。

## 硬性規則

- **禁止捏造新聞資料。** 不可產生假新聞、示範新聞或 placeholder 內容。所有新聞必須有可追溯
  的真實原文連結，且經過原文核對（見 SKILL.md 第三節）。若無法湊齊 3 篇可驗證新聞，流程必須
  失敗並告知使用者，不得用舊聞、假資料頂替。
- **Python 一律優先使用標準函式庫**，避免引入第三方套件；若確有必要才需與使用者確認。
- **所有檔案使用 UTF-8** 編碼。
- 新聞資料須先通過 `src/validate_news.py` 驗證才能寫入 `data/`、`data/archive/` 或用於產生
  報告；`src/build_report.py` 內部也會在產生 HTML 前重新呼叫同一套驗證邏輯，驗證失敗時不得
  覆蓋既有的正常 HTML。
- 未經使用者明確要求，不要自動執行新聞蒐集、發布網站或設定排程。

## 專案結構

參見 `README.md` 中「專案結構」章節的完整說明。

## 開發慣例

- 統一 JSON schema（根層為單一物件，非陣列）定義在
  `.claude/skills/fintech-news-daily/SKILL.md` 第四節，`src/validate_news.py` 的
  `ROOT_REQUIRED_FIELDS` / `ARTICLE_REQUIRED_FIELDS` 是同一份 schema 的程式碼版本，
  兩者欄位名稱必須保持一致，不得各自使用不同名稱代表同一欄位。
- `data/archive/YYYY-MM-DD.json`：當日新聞的永久歷史紀錄，一天一份，不覆寫。
- `data/latest.json`：`src/build_report.py` 預設讀取的來源，內容應與當日
  `data/archive/YYYY-MM-DD.json` 相同。
- 報告產生流程：`data/latest.json` → (`validate_news.py` 驗證) → `build_report.py` →
  `docs/archive/YYYY-MM-DD.html`（檔名日期取自 JSON 內的 `report_date`）+ `docs/index.html`。
- `build_report.py` 輸出一律先寫暫存檔，再以 `os.replace` 原子取代正式檔案。
