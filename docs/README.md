# 開發文件

本規劃以 `Basketball_Tactical_Analysis_Video_Proposal_v6` 為主要依據；與 HW1 不同之處，
依 v6 決定範圍。文件中的模組、資料格式與工作項目均為開發規劃，目前尚未實作。

| 文件 | 用途 |
| --- | --- |
| [需求與簡報比較](requirements.md) | 來源摘要、兩版差異、階段範圍與需求對照 |
| [系統架構與分工](architecture.md) | Backend／Frontend 邊界、資料流程與技術建議 |
| [資料交換規格](data-contract.md) | S1 JSON 草案、座標與時間定義、缺漏處理 |
| [S1 實作計畫](s1-plan.md) | 工作順序、交付物、測試與完成條件 |

## Repository 基準狀態

檢查日期：2026-11-12。規劃開始時的 commit 為 `fea8b01`，本機 `main` 與 `origin/main`
一致，工作目錄乾淨；遠端 `alex520623/basketball-tactics` 為 Private。

- Python 3.12.14、NumPy 2.3.4、pandas 2.3.3、pytest 8.4.2。
- `pip check` 通過，現有 4 個環境測試通過。
- `src/basketball_tactics/` 只有套件骨架，尚無資料讀取、分析或網頁功能。
- `data/raw/`、`data/processed/`、`outputs/` 只有 `.gitkeep`，未發現資料集檔案。
- 尚無 Frontend、API server、LLM 整合或產品功能測試；macOS 尚待實機驗證。

簡報原始回應、PDF 與檢視用圖片暫存於本機 `.tools/planning-review/`，受 `.gitignore`
排除。這些暫存檔案不納入版本管理；文件以原始 Google Slides 連結及頁碼引用來源。

## 規劃決策

| 項目 | 決定／建議 | 依據與狀態 |
| --- | --- | --- |
| 最低交付 | S1：既有追蹤資料的 2D 球場、位置與軌跡時間變化 | v6 第 5、6 頁，已確定 |
| 資料集 | 保留原先選定資料集，名稱與檔案待補 | 不另選資料集 |
| 影片流程 | Homography、偵測與追蹤保留為擴充 | v6 第 5 頁，非 S1 前置條件 |
| S2／S3 | S2 可獨立展示；S3 以 S2 的證據與知識規則生成解釋 | v6 第 3、5 頁 |
| S1 架構 | Python 匯出 JSON，網頁讀取並呈現 | 工程建議，待前後端共同確認 |
| Frontend | HTML／CSS／JavaScript＋Canvas，先完成本機展示 | 技術建議；若組員已有框架，保留資料規格再調整 |
| 資料格式 | `schema_version: 0.1.0`，見資料交換規格 | 草案，取得 sample 後再確認 |

## 待確認事項

| 編號 | 問題 | 由誰確認 | 影響 |
| --- | --- | --- | --- |
| Q1 | 原先資料集的名稱、來源、版本、授權、sample 路徑 | Backend／資料持有者 | 阻擋真實資料 importer 與 S1 整合 |
| Q2 | 球場尺寸與單位、時間欄位、採樣方式、球員／球 ID、隊伍與回合資訊 | Backend 盤點 sample，兩人確認 | 阻擋座標與時間轉換定案 |
| Q3 | Frontend 是否已有框架或現成程式，是否接受 JSON 檔案介面 | Frontend，兩人確認 | 決定介面載入方式與工具需求 |
| Q4 | 課程截止日、展示設備、可投入時間、首批示範片段 | 兩人 | 決定範圍、片段數量及時程 |
| Q5 | 是否有戰術標籤、持球與攻守標註，能否安排人工判讀 | 兩人 | 決定 S2 能做到描述性分析或少數戰術辨識 |
| Q6 | S3 的知識來源、評估人員、LLM 使用方式與費用 | 兩人，S2 後處理 | 不阻擋 S1 |

Q1、Q2 未確認前，可討論介面或以明確標示的示意資料規劃畫面；示意資料不能作為真實資料
接入或 S1 最低交付已完成的證據。規格調整由兩人共同確認，更新文件後再開始相應功能。
