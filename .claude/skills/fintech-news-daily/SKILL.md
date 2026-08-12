---
name: fintech-news-daily
description: 產生每日金融科技新聞日報：以 Asia/Taipei 時區蒐集近 24～72 小時內 AI × 金融科技 × 數據分析交集的新聞、逐篇以原文核對事實、輸出統一 JSON schema 並產生可發布的靜態 HTML。僅能由使用者輸入 /fintech-news-daily 明確觸發，不會由模型自行判斷觸發。
disable-model-invocation: true
---

# 金融科技新聞日報 (fintech-news-daily)

此技能定義「金融科技新聞日報」的每日產製流程：蒐集 → 核對 → 驗證 → 存檔 → 產生報告。
**本技能只能由使用者明確輸入 `/fintech-news-daily` 觸發，不可由模型自行判斷觸發。**

## 一、時區

所有日期、時間邏輯（含「近 24 小時」「近 72 小時」的判斷）一律以 **Asia/Taipei** 為準。

## 二、選題規則

1. 每次固定選出 3 篇報導**不同事件**的新聞（不可為同一事件的重複報導）。
2. 優先選擇近 24 小時內發布的新聞。
3. 近 24 小時不足 3 篇時，放寬到近 72 小時。
4. 仍不足 3 篇時，以 72 小時內的一般重大金融科技新聞補足。
5. 若最終仍無法湊足 3 篇可驗證新聞，**工作必須失敗並明確告知使用者**，不得使用舊聞、假資料
   或自行捏造內容頂替。
6. 優先主題（依相關性排序）：
   - AI 金融分析、風控與決策模型
   - 金融資料治理與模型治理
   - 監理科技與 AI 法規
   - 金融機構 AI 或數據分析應用
   - 金融科技產業調查與統計
7. 單純募資、品牌宣傳或產品廣告類新聞不優先選入，除非內容明確涉及 AI、資料平台或分析能力。

`selection_window`（見下方 schema）記錄本次實際使用到的最寬時間窗：
若 3 篇都在 24 小時內找齊，記為 `"24h"`；若需放寬到規則 3 或規則 4 才湊齊 3 篇，記為 `"72h"`。

## 三、搜尋與驗證流程

1. 先使用 `WebSearch` 蒐集至少 8 篇候選新聞。
2. 去除報導相同事件的重複新聞。
3. 對每篇候選新聞使用 `WebFetch` 開啟原文。
4. 逐篇核對以下項目，全部相符才可採用：
   - 原文可以正常開啟
   - 標題相符
   - 來源相符
   - 發布日期相符
   - 公司與機構名稱相符
   - 金額、比例及其他關鍵數字相符
5. **搜尋結果摘要（snippet）不能當成最終事實來源**，一切以 `WebFetch` 開啟後的原文內容為準。
6. 無法開啟或無法核對一致的文章必須捨棄，並從候選清單遞補下一篇，直到湊齊 3 篇通過核對的新聞，
   或依「選題規則第 5 點」判定失敗。

## 四、統一 JSON schema

這是本專案唯一的資料格式，`src/validate_news.py` 與 `src/build_report.py` 皆以此 schema 為準，
**不得另外使用不同名稱表示同一欄位**。

### 根層欄位

| 欄位 | 型別 | 說明 |
|---|---|---|
| `report_date` | string, `YYYY-MM-DD` | 報告日期 |
| `generated_at` | string, ISO 8601（含時區偏移，如 `+08:00`） | 報告產生時間 |
| `timezone` | string，固定為 `"Asia/Taipei"` | 時區 |
| `selection_window` | string，`"24h"` 或 `"72h"` | 本次選題實際使用的時間窗 |
| `articles` | array，固定 3 個 article 物件 | 當日新聞 |

### article 物件欄位

| 欄位 | 型別 | 說明 |
|---|---|---|
| `title_zh` | string | 中文標題 |
| `title_original` | string | 原文標題（若原文本身為中文則與 `title_zh` 相同） |
| `source` | string | 新聞來源（媒體/機構名稱） |
| `url` | string，必須是 `https://` | 原文連結 |
| `published_at` | string, `YYYY-MM-DD` | 原文發布日期 |
| `verified_at` | string, ISO 8601（含時區偏移） | 完成第三節「搜尋與驗證流程」核對的時間 |
| `selected_reason` | string | 為何選入本篇，需對應「選題規則」中的優先主題 |
| `key_points` | array，固定 3 個完整中文句子 | 見「五、Key Points 規格」 |
| `mermaid` | string，以 `flowchart TD` 開頭 | 見「六、Mermaid 規格」 |

`data/latest.json` 與 `data/archive/YYYY-MM-DD.json` 皆使用此根層 schema（單一 JSON 物件，
而非陣列）。`data/archive/YYYY-MM-DD.json` 為當日的永久歷史紀錄；`data/latest.json` 為
`src/build_report.py` 讀取的當前報告來源，內容應與當日的 `data/archive/YYYY-MM-DD.json` 相同。

## 五、Key Points 規格

`key_points` 固定 3 點，且：

1. 第 1 點：發生什麼事。
2. 第 2 點：規模、數字、技術或參與者。
3. 第 3 點：意義、影響、風險或下一步。

規則：
- 三點內容不可重複。
- 每一點必須是**完整中文句子**（非片語或關鍵字堆疊）。
- 不得使用空泛形容詞（如「備受矚目」「意義重大」）取代具體事實，須寫出可核對的具體內容。

## 六、Mermaid 規格

- 圖表類型固定使用 `flowchart TD`。
- 每張圖包含 5～10 個節點。
- 節點文字簡潔（避免整句塞入節點）。
- 節點標籤使用安全的 Mermaid 引號格式，例如 `A["文字"]`，避免特殊符號造成解析錯誤。
- 節點內不得放 HTML 標籤（例如 `<br/>`）。
- 顏色語意固定：
  - **灰色**：核心事件節點
  - **綠色、紫色**：不同分支路徑（例如不同影響對象或後續發展）
  - **藍色**：結果或影響
  - **橘色**：風險、限制或治理事項
- 每張圖必須用 `classDef` 定義上述樣式並套用到對應節點，全部圖表使用一致的顏色定義。

語法骨架範例（僅示意 `classDef` 與引號寫法，**非新聞內容**）：

```
flowchart TD
    A["核心事件"]:::gray
    A --> B["分支一"]:::green
    A --> C["分支二"]:::purple
    B --> D["結果或影響"]:::blue
    C --> E["風險或治理事項"]:::orange

    classDef gray fill:#9e9e9e,color:#ffffff;
    classDef green fill:#4caf50,color:#ffffff;
    classDef purple fill:#9c27b0,color:#ffffff;
    classDef blue fill:#2196f3,color:#ffffff;
    classDef orange fill:#ff9800,color:#ffffff;
```

`src/validate_news.py` 只機械檢查 `mermaid` 是否以 `flowchart TD` 開頭；節點數量、顏色語意、
`classDef` 是否套用等屬於內容品質規則，由本技能在產製新聞時自行遵守，驗證程式無法完全以程式
判斷圖表語意是否正確。

## 七、每日流程

1. **蒐集與核對**：依「二、選題規則」與「三、搜尋與驗證流程」找出 3 篇新聞。找不到齊 3 篇
   通過核對的新聞則整個流程失敗，明確告知使用者，不寫入任何檔案。
2. **組裝資料**：依「四、統一 JSON schema」組裝成單一 JSON 物件。
3. **驗證**：執行 `python3 src/validate_news.py <檔案路徑>` 確認結構正確；驗證失敗則修正或
   視為整體流程失敗，不得略過驗證直接發佈。
4. **保存歷史資料**：驗證通過後，寫入 `data/archive/YYYY-MM-DD.json`（永久保存），並同步寫入
   `data/latest.json`（內容相同，供報告產生器讀取）。
5. **產生報告**：執行 `python3 src/build_report.py`（預設讀取 `data/latest.json`），產出
   `docs/index.html` 與 `docs/archive/YYYY-MM-DD.html`。
6. **記錄**：執行過程中的重要訊息（例如核對失敗、驗證錯誤、產出結果）記錄到 `logs/`。

## 使用方式

```bash
# 驗證 data/latest.json（預設路徑）
python3 src/validate_news.py

# 驗證指定的歷史檔案
python3 src/validate_news.py data/archive/2026-08-12.json

# 由 data/latest.json（預設路徑）產生靜態 HTML 報告
python3 src/build_report.py
```

## 目前階段限制

本技能文件與工具程式碼已完成，但**尚未**實際執行新聞蒐集、驗證、發佈或排程。這些步驟需在
使用者以 `/fintech-news-daily` 明確觸發後才進行。
