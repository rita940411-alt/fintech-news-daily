# 金融科技新聞日報 (fintech-news-daily)

自動化蒐集、核對並發布每日金融科技新聞的專案。每天以 **Asia/Taipei** 時區挑選 3 篇報導不同
事件的新聞，優先選擇 **AI、金融科技（Fintech）與數據分析** 交集的內容，逐篇以原文核對事實，
輸出統一格式的 JSON 歷史資料，並產生可發布至 GitHub Pages 的靜態 HTML 報告，每篇新聞附上
Mermaid `flowchart TD` 結構圖。

## 專案結構

```
.
├── .claude/skills/fintech-news-daily/SKILL.md   # Skill 定義：選題規則、新鮮度判定、來源分級、候選追溯、搜尋與驗證流程、統一 JSON schema、Key Points 與 Mermaid 規格
├── src/
│   ├── validate_news.py                          # 驗證報告 JSON 與候選追溯 JSON 是否符合統一 schema
│   ├── build_report.py                            # 將驗證通過的 JSON 轉換為靜態 HTML 報告
│   ├── test_validate_news.py                       # validate_news.py 的 unittest 測試（tempfile-based）
│   └── test_build_report.py                        # build_report.py 的 unittest 測試（tempfile-based）
├── data/
│   ├── latest.json                                 # build_report.py 預設讀取的當前報告來源
│   ├── archive/                                    # 每日新聞歷史資料 (YYYY-MM-DD.json)，逐日累積存檔，不覆寫
│   └── audit/                                      # 每日候選新聞追溯紀錄 (YYYY-MM-DD-candidates.json)，至少 8 篇，含未採用者與淘汰原因
├── docs/                                           # GitHub Pages 發布內容
│   ├── index.html                                  # 最新一日報告（由 build_report.py 產生）
│   └── archive/                                    # 每日報告網頁 (YYYY-MM-DD.html)
├── logs/                                           # 執行紀錄（候選總數、逐篇選取/淘汰結果、驗證與產報告結果）
├── CLAUDE.md                                       # 給 Claude Code 的專案規則與工作指引
├── README.md                                       # 本檔案
└── .gitignore
```

### 各檔案/資料夾用途

- **`.claude/skills/fintech-news-daily/SKILL.md`**
  定義「金融科技新聞日報」的完整工作流程：時區、選題規則、新鮮度判定規則、來源分級、候選新聞
  追溯記錄、`WebSearch` / `WebFetch` 搜尋與原文核對流程、統一 JSON schema、Key Points 規格、
  Mermaid 規格。此 Skill 設定 `disable-model-invocation: true`，只能由使用者輸入
  `/fintech-news-daily` 明確觸發。

- **`src/validate_news.py`**
  獨立可執行的驗證腳本，同時支援兩種資料：

  1. **報告 JSON**（預設模式）：檢查根層欄位（`report_date` / `generated_at` / `timezone` /
     `selection_window` / `articles`）與每篇 article 欄位（`title_zh` / `title_original` /
     `source` / `source_type` / `url` / `published_at` / `event_date` / `verified_at` /
     `freshness_note` / `selected_reason` / `key_points` / `mermaid`）是否完整、型別是否
     正確，`source_type` 是否為合法枚舉值，URL 是否為 HTTPS 且不重複，日期與時間格式是否
     合法，`key_points` 是否恰 3 點且不重複，`mermaid` 是否以 `flowchart TD` 開頭，並檢查
     整期 3 篇 `source_type` 分布：至少 2 篇 `independent_media`、`official_source` 與
     `press_release` 合計最多 1 篇。
  2. **候選新聞追溯 JSON**（`--candidates` 模式）：檢查根層欄位（`report_date` /
     `searched_at` / `timezone` / `candidate_count` / `candidates`）與每筆 candidate 欄位
     （`title` / `source` / `url` / `published_at` / `event_date` / `source_type` /
     `fetch_status` / `decision` / `rejection_reason` / `duplicate_of`），確認
     `candidate_count` 等於實際筆數、候選數至少 8 筆、`decision` 為 `rejected` 時必須有
     `rejection_reason`。

  驗證失敗回傳非 0 exit code。用法：
  ```bash
  python3 src/validate_news.py                      # 驗證 data/latest.json（預設）
  python3 src/validate_news.py data/archive/YYYY-MM-DD.json   # 驗證指定的歷史檔案
  python3 src/validate_news.py --candidates data/audit/YYYY-MM-DD-candidates.json  # 驗證候選追溯紀錄
  ```

- **`src/build_report.py`**
  讀取 `data/latest.json`（預設路徑），先呼叫 `validate_news` 的驗證邏輯，驗證失敗則中止且
  不覆寫既有 HTML；驗證通過才產生 `docs/index.html`（最新報告 + 歷史日報清單）與
  `docs/archive/YYYY-MM-DD.html`（檔名日期取自 JSON 內的 `report_date`），每篇文章附上來源
  分級標籤（`source_type`）與新鮮度說明（`freshness_note`）。輸出一律先寫暫存檔、成功後再
  原子取代正式檔案。所有新聞文字皆做 HTML escaping，原文連結使用 `target="_blank"` 與
  `rel="noopener noreferrer"`，Mermaid 圖表以 `.mermaid-container` 卡片直接內嵌顯示於新聞
  卡片內（響應式：`width: 100%`、`overflow-x: auto` 橫向捲動、白底圓角卡片），不提供點擊
  放大功能。用法：
  ```bash
  python3 src/build_report.py                       # 讀取 data/latest.json（預設）
  ```

- **`src/test_validate_news.py`、`src/test_build_report.py`**
  以 Python 標準函式庫 `unittest` + `tempfile` 撰寫的測試，涵蓋新 schema 欄位
  （`event_date` / `source_type` / `freshness_note`）與來源分級組合規則的正向、反向測試，
  以及 `build_report.py` 的驗證失敗不覆寫、原子寫入與 HTML 內容正確性測試。用法：
  ```bash
  python3 -m unittest discover -s src -p "test_*.py"
  ```

- **`data/latest.json`**
  `build_report.py` 預設讀取的來源檔案，內容應與當日 `data/archive/YYYY-MM-DD.json` 相同。

- **`data/archive/`**
  每日新聞的永久歷史資料（JSON），檔名格式為 `YYYY-MM-DD.json`，一天一份、不覆寫，作為長期
  歷史紀錄。

- **`data/audit/`**
  每日候選新聞追溯紀錄（JSON），檔名格式為 `YYYY-MM-DD-candidates.json`，記錄當次實際檢視過
  的至少 8 篇候選新聞（含未採用者、淘汰原因與重複標記），供人工或後續稽核與
  `logs/YYYY-MM-DD.log` 交叉核對，一天一份、不覆寫。

- **`docs/`**
  GitHub Pages 發布用的靜態網站根目錄。`docs/index.html` 顯示最新一日報告，`docs/archive/`
  存放每日報告的永久連結頁面。

- **`logs/`**
  執行過程中的日誌檔案，須記錄候選總數、每篇候選的選取或淘汰結果（可與
  `data/audit/YYYY-MM-DD-candidates.json` 交叉核對）、以及 `validate_news.py` 與
  `build_report.py` 的實際執行結果，不得只寫「已搜尋 8+ 篇」這類無法驗證的結論性文字。

- **`CLAUDE.md`**
  提供給 Claude Code 的專案規則，例如禁止捏造新聞、Python 標準函式庫優先、UTF-8 編碼、
  資料驗證流程、schema 一致性等硬性規範。

- **`.gitignore`**
  排除 Python 快取檔、系統檔案、日誌檔、環境變數檔等不需版本控制的檔案。

## 新聞資料格式

`data/latest.json` 與 `data/archive/YYYY-MM-DD.json` 皆為**單一 JSON 物件**（非陣列），
完整欄位定義見 `.claude/skills/fintech-news-daily/SKILL.md` 第七節「統一 JSON schema」：

- 根層：`report_date`、`generated_at`、`timezone`（固定 `"Asia/Taipei"`）、
  `selection_window`（`"24h"` 或 `"72h"`，依 `event_date` 判定）、`articles`（固定 3 篇）。
- 每篇 article：`title_zh`、`title_original`、`source`、`source_type`
  （`independent_media` / `official_source` / `press_release` / `aggregator` 之一）、
  `url`（須為 https）、`published_at`（最終引用網頁發布日）、`event_date`（事件最早公告/
  發生日）、`verified_at`、`freshness_note`（新鮮度說明）、`selected_reason`、`key_points`
  （固定 3 個完整中文句子）、`mermaid`（以 `flowchart TD` 開頭）。
- 每期 3 篇 `source_type` 組合須符合：至少 2 篇 `independent_media`，`official_source` 與
  `press_release` 合計最多 1 篇，`aggregator` 原則上不得作為最終來源。

`data/audit/YYYY-MM-DD-candidates.json` 為候選新聞追溯紀錄，完整欄位定義見 SKILL.md 第六節
「候選新聞追溯記錄」：根層含 `report_date`、`searched_at`、`timezone`、`candidate_count`、
`candidates`（至少 8 筆，每筆含 `title` / `source` / `url` / `published_at` / `event_date` /
`source_type` / `fetch_status` / `decision` / `rejection_reason` / `duplicate_of`）。

## 目前進度

專案目前完成骨架建立與統一規格制定（Git 初始化、目錄結構、Skill 定義、驗證與報告產生工具
程式碼、新鮮度判定與來源分級規則、候選新聞追溯機制、對應測試）。新聞產製流程僅於使用者以
`/fintech-news-daily` 明確觸發後才執行。

## 需求環境

- Python 3（僅使用標準函式庫，無額外套件依賴）
