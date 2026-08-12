# 金融科技新聞日報 (fintech-news-daily)

自動化蒐集、驗證並發布每日金融科技新聞的專案。每天挑選 3 篇新聞，優先選擇
**AI、金融科技（Fintech）與數據分析** 交集的內容，輸出結構化 JSON 歷史資料，
並產生可發布至 GitHub Pages 的靜態 HTML 報告，每篇新聞附上 Mermaid 結構圖。

## 專案結構

```
.
├── .claude/skills/fintech-news-daily/SKILL.md   # Claude Code 技能定義：每日新聞蒐集/驗證/產報告的工作流程
├── src/
│   ├── validate_news.py                          # 驗證每日新聞 JSON 是否符合欄位與格式規範
│   └── build_report.py                            # 將驗證通過的每日 JSON 轉換為靜態 HTML 報告
├── data/archive/                                   # 每日新聞歷史資料 (YYYY-MM-DD.json)，逐日累積存檔
├── docs/                                           # GitHub Pages 發布內容（首頁 index.html 由 build_report.py 產生）
│   └── archive/                                    # 每日報告網頁 (YYYY-MM-DD.html)
├── logs/                                           # 執行紀錄（新聞蒐集/驗證/產報告過程中的日誌）
├── CLAUDE.md                                       # 給 Claude Code 的專案規則與工作指引
├── README.md                                       # 本檔案
└── .gitignore
```

### 各檔案/資料夾用途

- **`.claude/skills/fintech-news-daily/SKILL.md`**
  定義「金融科技新聞日報」的每日工作流程：蒐集 → 驗證 → 存檔 → 產生報告。
  說明每篇新聞需具備的欄位規範與品質要求。

- **`src/validate_news.py`**
  獨立可執行的驗證腳本。檢查每日新聞 JSON 是否恰有 3 篇、每篇是否包含
  `title` / `source` / `date` / `url` / `key_points`（恰 3 點）/ `mermaid`，
  以及日期格式與 URL 格式是否合法。用法：
  ```bash
  python3 src/validate_news.py data/archive/YYYY-MM-DD.json
  ```

- **`src/build_report.py`**
  讀取通過驗證的每日新聞 JSON，產生靜態 HTML 報告頁面（含 Mermaid 圖表渲染），
  輸出到 `docs/archive/YYYY-MM-DD.html`，並重建 `docs/index.html` 首頁索引，
  以利透過 GitHub Pages 發布。用法：
  ```bash
  python3 src/build_report.py data/archive/YYYY-MM-DD.json
  ```

- **`data/archive/`**
  每日新聞的原始結構化資料（JSON），檔名格式為 `YYYY-MM-DD.json`，
  作為長期歷史紀錄與報告產生的資料來源。目前為空，尚未有任何每日資料。

- **`docs/`**
  GitHub Pages 發布用的靜態網站根目錄。`docs/archive/` 存放每日報告頁面，
  `docs/index.html` 由 `build_report.py` 自動重建，列出所有已產生的日報連結。
  目前尚未產生任何頁面。

- **`logs/`**
  執行過程中的日誌檔案（例如新聞蒐集紀錄、驗證錯誤、產報告結果），
  用於除錯與追蹤每日自動化執行狀況。

- **`CLAUDE.md`**
  提供給 Claude Code 的專案規則，例如禁止捏造新聞、Python 標準函式庫優先、
  UTF-8 編碼、資料驗證流程等硬性規範。

- **`.gitignore`**
  排除 Python 快取檔、系統檔案、日誌檔等不需版本控制的檔案。

## 新聞資料格式

每日 JSON 檔案（`data/archive/YYYY-MM-DD.json`）為包含 3 個物件的陣列，每個物件格式如下：

```json
{
  "title": "新聞標題",
  "source": "新聞來源",
  "date": "YYYY-MM-DD",
  "url": "https://example.com/article",
  "key_points": ["重點一", "重點二", "重點三"],
  "mermaid": "graph TD; A[事件] --> B[影響]",
  "tags": ["AI", "fintech", "data-analytics"]
}
```

## 目前進度

專案目前僅完成骨架建立（Git 初始化、目錄結構、驗證與報告產生工具程式碼）。
**尚未**進行新聞蒐集、網站發布或排程設定，這些將於後續階段依需求進行。

## 需求環境

- Python 3（僅使用標準函式庫，無額外套件依賴）
