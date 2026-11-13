# 開發文件

本規劃以 `Basketball_Tactical_Analysis_Video_Proposal_v6` 為主要依據；與 HW1 不同之處，
依 v6 決定範圍。文件中的模組、資料格式與工作項目均為開發規劃，目前尚未實作。

| 文件 | 用途 |
| --- | --- |
| [需求與簡報比較](requirements.md) | 來源摘要、兩版差異、階段範圍與需求對照 |
| [系統架構與分工](architecture.md) | Backend／Frontend 邊界、資料流程與技術建議 |
| [資料交換規格](data-contract.md) | S1 JSON 草案、座標與時間定義、缺漏處理 |
| [S1 實作計畫](s1-plan.md) | 工作順序、交付物、測試與完成條件 |
| [SportVU 候選來源評估](sportvu-assessment.md) | 可下載性、單場 sample、品質與 S1–S3 適用性 |
| [SportVU 原始欄位](sportvu-fields.md) | 實測 raw 欄位、解讀依據與未知項目 |

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
| 資料集 | 使用者指定 SportVU 公開 repository 為候選，已抽查一場 | 正式採用待使用者決定，未擴大下載 |
| 影片流程 | Homography、偵測與追蹤保留為擴充 | v6 第 5 頁，非 S1 前置條件 |
| S2／S3 | S2 可獨立展示；S3 以 S2 的證據與知識規則生成解釋 | v6 第 3、5 頁 |
| Backend 介面 | 優先定義位置、隊伍、時間、球與軌跡的 JSON | 依實測 SportVU 結構，區分來源與衍生欄位 |
| Frontend | 組員尚無既定技術或現成程式；暫定 HTML／JavaScript／Canvas | 保留組員選型彈性，傳輸及部署未定 |
| 資料格式 | `schema_version: 0.2.0`，見資料交換規格 | 候選來源對照草案；未實作或凍結 |

## 待確認事項

| 編號 | 問題 | 由誰確認 | 影響 |
| --- | --- | --- | --- |
| Q1 | 是否正式採用候選 SportVU，以及授權／課程使用範圍 | 使用者與組員 | 尚未開始 importer |
| Q2 | raw 欄位已抽查；顯示方向、時間間隙、重疊／異常處理仍待確認 | Backend，兩人確認 | 阻擋品質規則與轉換定案 |
| Q3 | Frontend 自行選型；HTML／JavaScript／Canvas 僅暫定，傳輸方式待確認 | Frontend，兩人確認 | 本階段不建立 Frontend 或整套服務架構 |
| Q4 | 課程截止日、展示設備、可投入時間、首批示範片段 | 兩人 | 決定範圍、片段數量及時程 |
| Q5 | raw 無戰術標籤；是否採人工判讀或驗證外部動作註解 | 兩人 | 決定 S2 是否追加少數戰術辨識 |
| Q6 | S3 的知識來源、評估人員、LLM 使用方式與費用 | 兩人，S2 後處理 | 不阻擋 S1 |

Q1、Q2 未確認前，可討論介面或以明確標示的示意資料規劃畫面；示意資料不能作為真實資料
接入或 S1 最低交付已完成的證據。規格調整由兩人共同確認，更新文件後再開始相應功能。
