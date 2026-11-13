# 資料管理

目前正在評估使用者指定的 [NBA-Player-Movements](https://github.com/linouk23/NBA-Player-Movements)
SportVU 2015–16 追蹤資料，尚未正式採用。可下載性、單場 sample、格式與限制見
[評估報告](../docs/sportvu-assessment.md)，原始欄位與輸出草案見
[欄位查核](../docs/sportvu-fields.md) 與 [Backend JSON 規格](../docs/data-contract.md)。

已抽查的一場原檔暫存在本機 `.tools/sportvu-review/`，未作為正式開發資料匯入。
原 repository 未見明確授權，正式採用前需確認課程使用及資料散布範圍。

- `raw/`：正式取得的原始資料，保持原樣，不提交 Git。
- `processed/`：清理結果、欄位映射、來源 hash 與品質報告，不提交 Git。
- 根目錄 `outputs/`：匯出資料、圖表、影片與分析結果，不提交 Git。

正式採用後補上資料版本、來源 commit、授權依據、單場下載與解壓方式、檔案 hash、
可重現的 sample 範圍及必要參數。組員各自依授權取得資料，程式路徑使用 pathlib，
不寫死磁碟機或個人目錄。測試樣本需先確認可提交範圍；大型 raw 與輸出不進 repository。
