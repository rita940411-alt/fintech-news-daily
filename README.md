# 金融科技新聞日報 (fintech-news-daily)

自動化蒐集、核對並發布每日金融科技新聞的專案。每天以 **Asia/Taipei** 時區挑選 3 篇報導不同
事件的新聞，優先選擇 **AI、金融科技（Fintech）與數據分析** 交集的內容，逐篇以原文核對事實，
輸出統一格式的 JSON 歷史資料，並產生可發布至 GitHub Pages 的靜態 HTML 報告，每篇新聞附上
Mermaid `flowchart TD` 結構圖。

## 專案結構

```
.
├── .claude/skills/fintech-news-daily/SKILL.md   # Skill 定義：選題規則、搜尋與驗證流程、統一 JSON schema、Key Points 與 Mermaid 規格
├── src/
│   ├── validate_news.py                          # 驗證報告 JSON 是否符合統一 schema
│   └── build_report.py                            # 將驗證通過的 JSON 轉換為靜態 HTML 報告
├── data/
│   ├── latest.json                                 # build_report.py 預設讀取的當前報告來源（尚未產生）
│   └── archive/                                    # 每日新聞歷史資料 (YYYY-MM-DD.json)，逐日累積存檔，不覆寫
├── docs/                                           # GitHub Pages 發布內容
│   ├── index.html                                  # 最新一日報告（由 build_report.py 產生，尚未產生）
│   └── archive/                                    # 每日報告網頁 (YYYY-MM-DD.html)
├── logs/                                           # 執行紀錄（新聞蒐集/驗證/產報告過程中的日誌）
├── CLAUDE.md                                       # 給 Claude Code 的專案規則與工作指引
├── README.md                                       # 本檔案
└── .gitignore
```

### 各檔案/資料夾用途

- **`.claude/skills/fintech-news-daily/SKILL.md`**
  定義「金融科技新聞日報」的完整工作流程：時區、選題規則、`WebSearch` / `WebFetch` 搜尋與
  原文核對流程、統一 JSON schema、Key Points 規格、Mermaid 規格。此 Skill 設定
  `disable-model-invocation: true`，只能由使用者輸入 `/fintech-news-daily` 明確觸發。

- **`src/validate_news.py`**
  獨立可執行的驗證腳本。檢查報告 JSON 根層欄位（`report_date` / `generated_at` /
  `timezone` / `selection_window` / `articles`）與每篇 article 欄位（`title_zh` /
  `title_original` / `source` / `url` / `published_at` / `verified_at` /
  `selected_reason` / `key_points` / `mermaid`）是否完整、型別是否正確、URL 是否為
  HTTPS 且不重複、日期與時間格式是否合法、`key_points` 是否恰 3 點且不重複、`mermaid`
  是否以 `flowchart TD` 開頭。驗證失敗回傳非 0 exit code。用法：
  ```bash
  python3 src/validate_news.py                      # 驗證 data/latest.json（預設）
  python3 src/validate_news.py data/archive/YYYY-MM-DD.json   # 驗證指定的歷史檔案
  ```

- **`src/build_report.py`**
  讀取 `data/latest.json`（預設路徑），先呼叫 `validate_news` 的驗證邏輯，驗證失敗則中止且
  不覆寫既有 HTML；驗證通過才產生 `docs/index.html`（最新報告 + 歷史日報清單）與
  `docs/archive/YYYY-MM-DD.html`（檔名日期取自 JSON 內的 `report_date`）。輸出一律先寫暫存
  檔、成功後再原子取代正式檔案。所有新聞文字皆做 HTML escaping，原文連結使用
  `target="_blank"` 與 `rel="noopener noreferrer"`，Mermaid 圖表可點擊放大並完整縮放於
  視窗內。用法：
  ```bash
  python3 src/build_report.py                       # 讀取 data/latest.json（預設）
  ```

- **`data/latest.json`**
  `build_report.py` 預設讀取的來源檔案，內容應與當日 `data/archive/YYYY-MM-DD.json` 相同。
  目前尚未產生任何資料。

- **`data/archive/`**
  每日新聞的永久歷史資料（JSON），檔名格式為 `YYYY-MM-DD.json`，一天一份、不覆寫，作為長期
  歷史紀錄。目前為空，尚未有任何每日資料。

- **`docs/`**
  GitHub Pages 發布用的靜態網站根目錄。`docs/index.html` 顯示最新一日報告，`docs/archive/`
  存放每日報告的永久連結頁面。目前尚未產生任何頁面。

- **`logs/`**
  執行過程中的日誌檔案（例如新聞蒐集紀錄、原文核對結果、驗證錯誤、產報告結果），用於除錯與
  追蹤每日自動化執行狀況。

- **`CLAUDE.md`**
  提供給 Claude Code 的專案規則，例如禁止捏造新聞、Python 標準函式庫優先、UTF-8 編碼、
  資料驗證流程、schema 一致性等硬性規範。

- **`.gitignore`**
  排除 Python 快取檔、系統檔案、日誌檔、環境變數檔等不需版本控制的檔案。

## 新聞資料格式

`data/latest.json` 與 `data/archive/YYYY-MM-DD.json` 皆為**單一 JSON 物件**（非陣列），
完整欄位定義見 `.claude/skills/fintech-news-daily/SKILL.md` 第四節「統一 JSON schema」：

- 根層：`report_date`、`generated_at`、`timezone`（固定 `"Asia/Taipei"`）、
  `selection_window`（`"24h"` 或 `"72h"`）、`articles`（固定 3 篇）。
- 每篇 article：`title_zh`、`title_original`、`source`、`url`（須為 https）、
  `published_at`、`verified_at`、`selected_reason`、`key_points`（固定 3 個完整中文句子）、
  `mermaid`（以 `flowchart TD` 開頭）。

## 目前進度

專案目前完成骨架建立與統一規格制定（Git 初始化、目錄結構、Skill 定義、驗證與報告產生工具
程式碼）。**尚未**進行新聞蒐集、網站發布或排程設定，這些將於使用者以 `/fintech-news-daily`
明確觸發後才進行。

## 需求環境

- Python 3（僅使用標準函式庫，無額外套件依賴）
