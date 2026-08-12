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
  的真實原文連結，且經過原文核對（見 SKILL.md 第五節）。若無法湊齊 3 篇可驗證新聞，流程必須
  失敗並告知使用者，不得用舊聞、假資料頂替。
- **新鮮度判定看事件本身，不是二次報導的刊登日。** `event_date`（事件最早公告/發生日）與
  `published_at`（最終引用網頁的發布日）是兩個不同欄位，`selection_window`（24h/72h）一律以
  `event_date` 判定；改寫超過 72 小時舊聞、未新增事實或分析的報導不得入選。詳見 SKILL.md
  第三節「新鮮度判定規則」。
- **來源分級不得造假。** 每篇 article 的 `source_type` 須誠實標示為
  `independent_media` / `official_source` / `press_release` / `aggregator` 之一；新聞稿被
  轉載到其他網站不代表它變成獨立媒體報導。每期 3 篇須至少 2 篇 `independent_media`，
  `official_source` 與 `press_release` 合計最多 1 篇，`aggregator` 原則上不得作為最終來源。
  詳見 SKILL.md 第四節「來源分級」。
- **候選新聞必須留下可追溯紀錄。** 每次執行須將實際檢視過的至少 8 篇候選（含未採用者）寫入
  `data/audit/YYYY-MM-DD-candidates.json`，並在 `logs/YYYY-MM-DD.log` 記錄可與該檔案交叉
  核對的候選總數與逐篇選取/淘汰結果；禁止只寫「已搜尋 8+ 篇」這類無法驗證的結論性文字。少於
  8 篇候選時，流程失敗，不得產生或覆寫正式檔案。詳見 SKILL.md 第六節「候選新聞追溯記錄」。
- **Python 一律優先使用標準函式庫**，避免引入第三方套件；若確有必要才需與使用者確認。
- **所有檔案使用 UTF-8** 編碼。
- 新聞資料須先通過 `src/validate_news.py` 驗證才能寫入 `data/`、`data/archive/` 或用於產生
  報告；`src/build_report.py` 內部也會在產生 HTML 前重新呼叫同一套驗證邏輯，驗證失敗時不得
  覆蓋既有的正常 HTML。第 4～8 步（驗證、寫候選紀錄、存檔、產報告、寫日誌）必須全部成功才可
  原子取代既有正式檔案，任一步驟失敗不得留下半完成或驗證失敗的正式檔案。
- 未經使用者明確要求，不要自動執行新聞蒐集、發布網站或設定排程。

## 專案結構

參見 `README.md` 中「專案結構」章節的完整說明。

## 開發慣例

- 統一 JSON schema（根層為單一物件，非陣列）定義在
  `.claude/skills/fintech-news-daily/SKILL.md` 第七節，`src/validate_news.py` 的
  `ROOT_REQUIRED_FIELDS` / `ARTICLE_REQUIRED_FIELDS` 是同一份 schema 的程式碼版本，
  兩者欄位名稱必須保持一致，不得各自使用不同名稱代表同一欄位。article 欄位含
  `event_date`（事件最早公告/發生日）、`source_type`（來源分級枚舉值）、
  `freshness_note`（新鮮度說明），三者缺一不可。
- 候選新聞追溯紀錄的 schema 定義在 SKILL.md 第六節，程式碼版本是
  `src/validate_news.py` 的 `CANDIDATE_ROOT_REQUIRED_FIELDS` / `CANDIDATE_REQUIRED_FIELDS`。
- `data/archive/YYYY-MM-DD.json`：當日新聞的永久歷史紀錄，一天一份，不覆寫。
- `data/latest.json`：`src/build_report.py` 預設讀取的來源，內容應與當日
  `data/archive/YYYY-MM-DD.json` 相同。
- `data/audit/YYYY-MM-DD-candidates.json`：當日實際檢視過的候選新聞追溯紀錄（至少 8 篇，含
  未採用者與淘汰原因），供人工或後續稽核與 `logs/YYYY-MM-DD.log` 交叉核對。
- 報告產生流程：`data/latest.json` → (`validate_news.py` 驗證，含來源分級組合規則) →
  `build_report.py` → `docs/archive/YYYY-MM-DD.html`（檔名日期取自 JSON 內的 `report_date`，
  顯示來源分級標籤與 `freshness_note`）+ `docs/index.html`。每張 Mermaid 圖表以
  `.mermaid-container` 卡片直接內嵌顯示（響應式、`overflow-x: auto` 橫向捲動），**不**提供
  點擊放大或彈出視窗（modal）功能，避免放大／縮小互動邏輯導致的顯示問題。
- `build_report.py` 輸出一律先寫暫存檔，再以 `os.replace` 原子取代正式檔案。
