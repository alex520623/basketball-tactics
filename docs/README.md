# 開發文件

本規劃以 `Basketball_Tactical_Analysis_Video_Proposal_v6` 為主要依據；與 HW1 不同之處，
依 v6 決定範圍。S1 Backend 已實作單場解析與 JSON 匯出；Frontend、S2 與 S3 尚未實作。

| 文件 | 用途 |
| --- | --- |
| [需求與簡報比較](requirements.md) | 來源摘要、兩版差異、階段範圍與需求對照 |
| [系統架構與分工](architecture.md) | Backend／Frontend 邊界、資料流程與技術建議 |
| [資料交換規格](data-contract.md) | S1 JSON 草案、座標與時間定義、缺漏處理 |
| [S1 實作計畫](s1-plan.md) | 工作順序、交付物、測試與完成條件 |
| [S1 Backend 執行與交接](backend-s1.md) | 命令、測試、記憶體實測與 Frontend 交付限制 |
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
| 資料集 | 2026-11-13 已選 SportVU 2015–16 作 S1 本機小規模驗證 | 授權待確認，不公開散布 raw；使用既有單場 sample |
| 影片流程 | Homography、偵測與追蹤保留為擴充 | v6 第 5 頁，非 S1 前置條件 |
| S2／S3 | S2 可獨立展示；S3 以 S2 的證據與知識規則生成解釋 | v6 第 3、5 頁 |
| Backend 介面 | 優先定義位置、隊伍、時間、球與軌跡的 JSON | 依實測 SportVU 結構，區分來源與衍生欄位 |
| Frontend | 組員尚無既定技術或現成程式；暫定 HTML／JavaScript／Canvas | 保留組員選型彈性，傳輸及部署未定 |
| 資料格式 | `schema_version: 0.2.0`，見資料交換規格 | Backend 已產生 525 影格的真實事件 JSON |

## 待確認事項

| 編號 | 問題 | 由誰確認 | 影響 |
| --- | --- | --- | --- |
| Q1 | 已核定 S1 本機小規模技術驗證；擴大使用與散布授權仍待確認 | 使用者與組員 | 不擴大下載或公開 raw |
| Q2 | 已記錄 120 ms 間隙及品質政策；顯示方向與其他比賽品質仍待確認 | Backend，兩人確認 | 不假定來源原點或所有事件皆完整 |
| Q3 | Frontend 自行選型；HTML／JavaScript／Canvas 僅暫定，傳輸方式待確認 | Frontend，兩人確認 | 本階段不建立 Frontend 或整套服務架構 |
| Q4 | 課程截止日、展示設備、可投入時間、首批示範片段 | 兩人 | 決定範圍、片段數量及時程 |
| Q5 | raw 無戰術標籤；是否採人工判讀或驗證外部動作註解 | 兩人 | 決定 S2 是否追加少數戰術辨識 |
| Q6 | S3 的知識來源、評估人員、LLM 使用方式與費用 | 兩人，S2 後處理 | 不阻擋 S1 |

目前 Backend 已可交付本機真實資料，完整 S1 畫面仍待 Frontend 實作與共同驗收。
原始資料、完整輸出與測試暫存不納入 Git；規格調整須更新文件並通知另一端。
