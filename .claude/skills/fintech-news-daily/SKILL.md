---
name: fintech-news-daily
description: 產生每日金融科技新聞日報：以 Asia/Taipei 時區蒐集近 24～72 小時內 AI × 金融科技 × 數據分析交集的新聞、逐篇以原文核對事實與新鮮度、分級來源類型、留存候選新聞追溯紀錄、輸出統一 JSON schema 並產生可發布的靜態 HTML。僅能由使用者輸入 /fintech-news-daily 明確觸發，不會由模型自行判斷觸發。
disable-model-invocation: true
---

# 金融科技新聞日報 (fintech-news-daily)

此技能定義「金融科技新聞日報」的每日產製流程：蒐集 → 核對新鮮度與來源 → 記錄候選追溯 → 驗證 →
存檔 → 產生報告。**本技能只能由使用者明確輸入 `/fintech-news-daily` 觸發，不可由模型自行判斷
觸發。**

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

`selection_window`（見「七、統一 JSON schema」）記錄本次實際使用到的最寬時間窗：若 3 篇都在
24 小時內找齊，記為 `"24h"`；若需放寬到規則 3 或規則 4 才湊齊 3 篇，記為 `"72h"`。「24 小時／
72 小時」的判斷須依「三、新鮮度判定規則」執行，不得僅憑二次報導的刊登日期認定。

## 三、新鮮度判定規則

新鮮度判斷的核心原則：**新鮮度看的是事件本身何時發生或公告，不是哪一篇文章何時被寫出來。**

1. `published_at` 表示**最終選用網頁本身**的發布日期（也就是被引用為「原文」的那個網址的
   刊登日期）。
2. 每篇 article 必須另外記錄 `event_date`：該事件**最早**公開公告或發生的日期，格式為
   `YYYY-MM-DD`。若某公司先發布新聞稿、媒體隔天才報導，`event_date` 是新聞稿日期，
   `published_at` 才是被引用網頁的日期；兩者可以不同。
3. 每篇 article 必須記錄 `freshness_note`：以完整中文句子說明本篇為何仍符合本期新鮮度要求
   （例如說明 `event_date` 與 `published_at` 為何一致或不同、或說明後續報導新增了哪些內容）。
4. **二次報導不得自動重設事件的新鮮度。** 媒體改寫或轉述較早發生的事件，不會讓 `event_date`
   變成二次報導當天；`selection_window`（24h/72h）的判斷必須以 `event_date` 為準，
   而非 `published_at`。
5. 若媒體報導只是改寫**超過 72 小時**的舊新聞稿或舊報導，且**沒有新增事實、數據、採訪或
   實質發展**，該候選**不得入選**，須在候選追溯紀錄中標記淘汰並說明原因。
6. 若後續報導確實包含**新的發展、獨立採訪、新數據或實質分析**，才可以依該後續報導的
   `published_at`（作為呈現用的引用網頁日期）入選，但 `event_date` 仍須填最早的事件發生／
   公告日，並在 `freshness_note` 中具體說明後續報導新增了哪些內容（不可空泛帶過）。
7. 24h/72h 的判斷一律依可驗證的**發布日期**（而非精確到小時的時間）執行。若原文只提供日期、
   未提供具體時間，應採取**保守判斷**（以整日為最小單位），不得聲稱或換算成精確到小時的時間差。

## 四、來源分級

每篇 article 必須記錄 `source_type`，只能是以下四種之一：

| 值 | 定義 |
|---|---|
| `independent_media` | 有編輯或記者處理、具獨立採編內容的媒體報導 |
| `official_source` | 政府機關、監管機構、公司官網或投資人關係頁面 |
| `press_release` | PR Newswire、Business Wire 等企業新聞稿發布平台 |
| `aggregator` | 自動彙整、單純轉載、缺乏獨立採編內容的網頁 |

選題規則：

1. 每期 3 篇之中，**至少 2 篇**須為 `independent_media`。
2. `official_source` 與 `press_release` **合計最多 1 篇**。
3. `aggregator` **原則上不得**作為最終引用來源。
4. 新聞稿（`press_release`）可以用來確認企業公告的事實，但寫入 `key_points` /
   `selected_reason` 時**必須刪除宣傳性用詞**（例如「advance AI innovation」之類的自我宣傳
   語句不可直接轉譯），且必須在 `source_type` 上如實標示為 `press_release`，不得因為轉載到
   其他網站而誤標為 `independent_media`。
5. 新聞稿被轉載到 StockTitan、TipRanks、MarketScreener 等網站，**不代表它變成獨立媒體報導**。
   採用這類轉載頁面前，必須實際核對該網站是否新增了採訪、查證或獨立分析內容：
   - 若只是逐字或近乎逐字轉載新聞稿，`source_type` 仍應標記為 `press_release`（或視轉載網站
     性質標記為 `aggregator`），不得標記為 `independent_media`。
   - 若該網站的記者確實補充了採訪、數據查核或獨立分析，才可標記為 `independent_media`，並在
     `freshness_note` 或 `selected_reason` 中具體指出新增了什麼內容。

## 五、搜尋與驗證流程

1. 先使用 `WebSearch` 蒐集**至少 8 篇**候選新聞（含最終未採用的候選），並依「六、候選新聞
   追溯記錄」逐篇記錄。
2. 去除報導相同事件的重複新聞（在候選紀錄中以 `duplicate_of` 標示）。
3. 對每篇候選新聞使用 `WebFetch` 開啟原文。
4. 逐篇核對以下項目，全部相符才可採用：
   - 原文可以正常開啟
   - 標題相符
   - 來源相符
   - 發布日期相符
   - 公司與機構名稱相符
   - 金額、比例及其他關鍵數字相符
5. **搜尋結果摘要（snippet）不能當成最終事實來源**，一切以 `WebFetch` 開啟後的原文內容為準。
6. 對每篇候選額外核對「三、新鮮度判定規則」與「四、來源分級」：判斷 `event_date`、
   `source_type`，並確認是否為改寫超過 72 小時舊聞而未新增內容（若是，淘汰）。
7. 無法開啟、無法核對一致、新鮮度不合格，或來源分級不合格（例如會導致 `aggregator` 被選為
   最終來源）的候選，必須捨棄並從候選清單遞補下一篇，直到湊齊 3 篇通過核對、且整體符合
   「四、來源分級」選題規則（至少 2 篇 `independent_media`、`official_source` 與
   `press_release` 合計最多 1 篇）的新聞，或依「選題規則第 5 點」判定失敗。

## 六、候選新聞追溯記錄

每次執行必須將實際檢視過的候選新聞（含未採用者）寫入
`data/audit/YYYY-MM-DD-candidates.json`，作為可驗證的追溯依據，**不得只在日誌寫「已搜尋 8+
篇」這種無法逐筆驗證的結論性文字**。

### 根層欄位

| 欄位 | 型別 | 說明 |
|---|---|---|
| `report_date` | string, `YYYY-MM-DD` | 對應的報告日期 |
| `searched_at` | string, ISO 8601（含時區偏移） | 完成候選蒐集的時間 |
| `timezone` | string，固定為 `"Asia/Taipei"` | 時區 |
| `candidate_count` | integer | 候選篇數，**必須等於** `candidates` 陣列實際筆數 |
| `candidates` | array，至少 8 個 candidate 物件 | 本次實際檢視過的候選新聞 |

### candidate 物件欄位

| 欄位 | 型別 | 說明 |
|---|---|---|
| `title` | string | 候選新聞標題 |
| `source` | string | 候選新聞來源 |
| `url` | string，`https://` | 候選新聞網址 |
| `published_at` | string, `YYYY-MM-DD` | 該候選網頁本身的發布日期 |
| `event_date` | string, `YYYY-MM-DD` | 該候選對應事件的最早公開公告或發生日期 |
| `source_type` | string，見「四、來源分級」四種值之一 | 來源分級 |
| `fetch_status` | string，`"success"` 或 `"failed"` | 是否成功以 `WebFetch` 開啟並核對原文 |
| `decision` | string，`"selected"` 或 `"rejected"` | 本篇是否最終入選 |
| `rejection_reason` | string 或 `null` | `decision` 為 `"rejected"` 時必須說明具體淘汰原因（重複、無法開啟、日期不符、內容不足、來源分級不合格等）；`decision` 為 `"selected"` 時為 `null` |
| `duplicate_of` | string 或 `null` | 若本篇與清單中另一篇報導相同事件，填入該篇的 `url`；否則為 `null` |

要求：

1. `candidate_count` 必須等於 `candidates` 實際筆數，兩者不一致視為紀錄有誤。
2. 少於 8 篇候選時，工作失敗，不得產生或覆寫任何正式報告檔案。
3. `logs/YYYY-MM-DD.log` 必須記錄：候選總數、每篇候選的選取或淘汰結果（可簡述，但需可對照
   `data/audit/YYYY-MM-DD-candidates.json` 逐筆查核）、以及 `validate_news.py` 與
   `build_report.py` 的實際執行結果（含成功或失敗訊息）。
4. 不得在日誌只寫「已搜尋 8+ 篇候選」這類無法逐筆驗證的結論性文字；日誌內容須能與候選追溯
   檔案交叉核對。

## 七、統一 JSON schema

這是本專案唯一的資料格式，`src/validate_news.py` 與 `src/build_report.py` 皆以此 schema 為準，
**不得另外使用不同名稱表示同一欄位**。

### 根層欄位

| 欄位 | 型別 | 說明 |
|---|---|---|
| `report_date` | string, `YYYY-MM-DD` | 報告日期 |
| `generated_at` | string, ISO 8601（含時區偏移，如 `+08:00`） | 報告產生時間 |
| `timezone` | string，固定為 `"Asia/Taipei"` | 時區 |
| `selection_window` | string，`"24h"` 或 `"72h"` | 本次選題實際使用的時間窗（依 `event_date` 判定） |
| `articles` | array，固定 3 個 article 物件 | 當日新聞 |

### article 物件欄位

| 欄位 | 型別 | 說明 |
|---|---|---|
| `title_zh` | string | 中文標題 |
| `title_original` | string | 原文標題（若原文本身為中文則與 `title_zh` 相同） |
| `source` | string | 新聞來源（媒體/機構名稱） |
| `source_type` | string，見「四、來源分級」四種值之一 | 來源分級 |
| `url` | string，必須是 `https://` | 最終引用的原文連結 |
| `published_at` | string, `YYYY-MM-DD` | 最終選用網頁本身的發布日期 |
| `event_date` | string, `YYYY-MM-DD` | 該事件最早公開公告或發生的日期，見「三、新鮮度判定規則」 |
| `verified_at` | string, ISO 8601（含時區偏移） | 完成第五節「搜尋與驗證流程」核對的時間 |
| `freshness_note` | string | 說明本篇為何仍符合本期新鮮度要求，見「三、新鮮度判定規則」 |
| `selected_reason` | string | 為何選入本篇，需對應「選題規則」中的優先主題 |
| `key_points` | array，固定 3 個完整中文句子 | 見「八、Key Points 規格」 |
| `mermaid` | string，以 `flowchart TD` 開頭 | 見「九、Mermaid 規格」 |

`data/latest.json` 與 `data/archive/YYYY-MM-DD.json` 皆使用此根層 schema（單一 JSON 物件，
而非陣列）。`data/archive/YYYY-MM-DD.json` 為當日的永久歷史紀錄；`data/latest.json` 為
`src/build_report.py` 讀取的當前報告來源，內容應與當日的 `data/archive/YYYY-MM-DD.json` 相同。

`src/validate_news.py` 除了逐篇欄位型別檢查，也會檢查整期 3 篇 `source_type` 的分布是否符合
「四、來源分級」選題規則（至少 2 篇 `independent_media`、`official_source` 與 `press_release`
合計最多 1 篇）；不符合視為驗證失敗。

## 八、Key Points 規格

`key_points` 固定 3 點，且：

1. 第 1 點：發生什麼事。
2. 第 2 點：規模、數字、技術或參與者。
3. 第 3 點：意義、影響、風險或下一步。

規則：
- 三點內容不可重複。
- 每一點必須是**完整中文句子**（非片語或關鍵字堆疊）。
- 不得使用空泛形容詞（如「備受矚目」「意義重大」）取代具體事實，須寫出可核對的具體內容。
- 若來源 `source_type` 為 `press_release`，第 3 點（意義、影響、風險或下一步）**只能寫原文
  明確陳述的事實**，不得寫成對業界趨勢的推論或延伸判斷（例如不得寫「顯示產業正加速導入」這類
  非原文直接支持的綜合推論）。

## 九、Mermaid 規格

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

`src/build_report.py` 將每張圖表直接內嵌顯示於該篇新聞卡片內的 `.mermaid-container`
容器中（響應式：`width: 100%`、`overflow-x: auto` 橫向捲動、白底圓角卡片），不提供點擊放大
或彈出視窗（modal）功能；圖表內容需自行維持精簡、清晰，避免依賴放大檢視才能閱讀。

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

## 十、每日流程

1. **蒐集候選**：依「五、搜尋與驗證流程」第 1 點蒐集至少 8 篇候選，逐篇記錄於
   「六、候選新聞追溯記錄」所定義的結構中（先在記憶體/暫存中準備，尚未寫檔）。
2. **核對與篩選**：依「二、選題規則」「三、新鮮度判定規則」「四、來源分級」「五、搜尋與驗證
   流程」核對每篇候選，選出 3 篇皆通過核對、新鮮度合格、來源分級組合合規的不同事件新聞。
   找不到齊 3 篇合格新聞則整個流程失敗，明確告知使用者，不寫入任何正式檔案（包含
   `data/audit/` 候選記錄也不得以未完成狀態覆寫既有檔案）。
3. **組裝資料**：依「七、統一 JSON schema」組裝成單一 JSON 物件。
4. **驗證**：執行 `python3 src/validate_news.py <檔案路徑>` 確認結構、新鮮度欄位與來源分級
   規則皆正確；驗證失敗則修正或視為整體流程失敗，不得略過驗證直接發佈。
5. **寫入候選追溯紀錄**：驗證通過後，才寫入 `data/audit/YYYY-MM-DD-candidates.json`（完整
   候選清單，含未採用者與淘汰原因）。
6. **保存歷史資料**：寫入 `data/archive/YYYY-MM-DD.json`（永久保存），並同步寫入
   `data/latest.json`（內容相同，供報告產生器讀取）。
7. **產生報告**：執行 `python3 src/build_report.py`（預設讀取 `data/latest.json`），產出
   `docs/index.html` 與 `docs/archive/YYYY-MM-DD.html`，網頁需顯示每篇的來源分級標籤與
   `freshness_note`。
8. **記錄**：將候選總數、每篇候選的選取/淘汰結果、以及 `validate_news.py` 與
   `build_report.py` 的執行結果記錄到 `logs/YYYY-MM-DD.log`，內容須可與
   `data/audit/YYYY-MM-DD-candidates.json` 交叉核對，不得只寫結論性文字。
9. 第 4～8 步必須全部成功才可原子取代既有正式檔案（`data/latest.json`、
   `data/archive/YYYY-MM-DD.json`、`docs/index.html`、`docs/archive/YYYY-MM-DD.html`、
   `logs/YYYY-MM-DD.log`）；任一步驟失敗，不得留下半完成或驗證失敗的正式檔案，既有正常檔案
   保持不變。

## 使用方式

```bash
# 驗證 data/latest.json（預設路徑）
python3 src/validate_news.py

# 驗證指定的歷史檔案
python3 src/validate_news.py data/archive/2026-08-12.json

# 驗證候選新聞追溯紀錄
python3 src/validate_news.py --candidates data/audit/2026-08-12-candidates.json

# 由 data/latest.json（預設路徑）產生靜態 HTML 報告
python3 src/build_report.py
```

## 目前階段限制

本技能文件與工具程式碼已完成，但每日執行仍需在使用者以 `/fintech-news-daily` 明確觸發後才
進行。任何一次執行若無法湊齊 3 篇符合新鮮度、來源分級與原文核對規則的新聞，該次執行必須失敗
並明確告知使用者，不得以舊聞、假資料或推論內容頂替。
