---
name: fintech-news-daily
description: 每日金融科技新聞蒐集、驗證與報告產製流程。當使用者要求「產生今日金融科技新聞日報」、「驗證新聞資料」或「建立新聞報告網頁」時使用此技能。
---

# 金融科技新聞日報 (fintech-news-daily)

此技能定義「金融科技新聞日報」專案的每日工作流程。目標是每天蒐集並驗證 3 篇金融科技新聞，
優先選擇 **AI、金融科技（Fintech）與數據分析** 三者交集的內容，並產出結構化資料與靜態網頁報告。

## 每篇新聞的必要欄位

每篇新聞紀錄（JSON）必須包含：

- `title`：新聞標題
- `source`：新聞來源（媒體/機構名稱）
- `date`：發布日期，格式 `YYYY-MM-DD`
- `url`：原文連結（必須是有效的 `http://` 或 `https://` URL）
- `key_points`：**剛好 3 點** Key Points（字串陣列）
- `mermaid`：一段 Mermaid 圖表語法，描述該則新聞的結構（例如事件關係、影響範圍）
- `tags`（選填）：例如 `["AI", "fintech", "data-analytics"]`，用於標示是否落在三者交集

## 每日流程

1. **蒐集**：找出當日 3 篇金融科技新聞，優先挑選 AI × Fintech × 數據分析交集的內容。
   每篇新聞需可追溯到真實原文連結，禁止捏造或使用示範/佔位資料。
2. **驗證**：使用 `src/validate_news.py` 檢查每篇新聞的欄位完整性、URL 格式、日期格式、
   Key Points 是否恰為 3 點、Mermaid 語法是否非空。
3. **保存歷史資料**：驗證通過後，將當日 3 篇新聞存成 `data/archive/YYYY-MM-DD.json`。
4. **產生報告**：使用 `src/build_report.py` 讀取當日 JSON，產出可發布到 GitHub Pages 的
   靜態 HTML，輸出至 `docs/archive/YYYY-MM-DD.html`，並更新 `docs/index.html` 首頁索引。
5. **記錄**：執行過程的重要訊息（例如驗證失敗、產出結果）記錄到 `logs/`。

## 目前階段限制

專案第一階段僅建立骨架與工具程式碼，**不**執行新聞蒐集、**不**發布網站、**不**設定排程。
這些步驟需在使用者明確要求時才進行。

## 使用方式

```bash
# 驗證某一天的新聞 JSON
python3 src/validate_news.py data/archive/2026-08-12.json

# 由某一天的新聞 JSON 產生靜態 HTML 報告
python3 src/build_report.py data/archive/2026-08-12.json
```
