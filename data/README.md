# 資料管理

2026-11-13 已選用 [NBA-Player-Movements](https://github.com/linouk23/NBA-Player-Movements)
SportVU 2015–16 追蹤資料作 S1 本機小規模技術驗證；授權仍待確認，不公開散布原始資料。
可下載性、單場 sample、格式與限制見
[評估報告](../docs/sportvu-assessment.md)，原始欄位與輸出草案見
[欄位查核](../docs/sportvu-fields.md) 與 [Backend JSON 規格](../docs/data-contract.md)。

本機既有 `.tools/sportvu-review/0021500476.json` 已用於 Backend 驗證，不需搬移或重複下載。
執行與測試方式見 [S1 Backend](../docs/backend-s1.md)。擴大使用及資料散布範圍仍待確認。

- `raw/`：正式取得的原始資料，保持原樣，不提交 Git。
- `processed/`：清理結果、欄位映射、來源 hash 與品質報告，不提交 Git。
- 根目錄 `outputs/`：匯出資料、圖表、影片與分析結果，不提交 Git。

資料版本、來源 commit、單場 hash、sample 範圍與執行參數已記錄於上述文件；
授權依據仍待補充。組員各自依授權取得資料，程式路徑使用 pathlib，
不寫死磁碟機或個人目錄。測試樣本需先確認可提交範圍；大型 raw 與輸出不進 repository。
