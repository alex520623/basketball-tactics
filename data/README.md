# 資料管理

S1 使用 [NBA-Player-Movements](https://github.com/linouk23/NBA-Player-Movements)
提供的 NBA SportVU 2015–16 追蹤資料。
可下載性、單場 sample、格式與限制見
[評估報告](../docs/sportvu-assessment.md)，原始欄位與輸出草案見
[欄位查核](../docs/sportvu-fields.md) 與 [Backend JSON 規格](../docs/data-contract.md)。

## 準備開發資料

1. 第一個測試片段為 2015-12-30 Lakers at Celtics，game ID `0021500476`、eventId="2"。
2. 依 [單場 sample 說明](../docs/sportvu-assessment.md#已驗證的單場-sample) 取得並解壓該場檔案。
   只需這一場，不必下載全部比賽。已有相同原檔時可直接使用，不必重複下載。
3. 建議放置於 `data/raw/0021500476.json`；若檔案在其他位置，將匯出命令的 `--input`
   改為實際路徑。以文件記錄的 SHA-256 核對檔案。
4. 依 [S1 Backend](../docs/backend-s1.md) 匯出 JSON，再依 [球場回放](../docs/local-viewer.md) 啟動介面。

Git clone 只取得程式與文件，不包含比賽原檔或完整衍生 JSON。每位組員須在各自電腦完成
上述步驟，使用相同來源 hash、eventId 與轉換參數，才能重現相同片段。

## 儲存位置

- `raw/`：正式取得的原始資料，保持原樣，不提交 Git。
- `processed/`：清理結果、欄位映射、來源 hash 與品質報告，不提交 Git。
- 根目錄 `outputs/`：匯出資料、圖表、影片與分析結果，不提交 Git。

## 使用範圍

資料授權仍待確認。目前僅進行開發電腦上的小規模技術驗證，不公開散布原始資料或完整衍生
JSON，也不將其部署到公開網站。擴大資料使用、共享及課堂展示範圍前，須先確認來源授權。

資料版本、來源 commit、單場 hash、sample 範圍與執行參數已記錄於上述文件。
組員各自依允許範圍取得資料，程式路徑使用 pathlib，
不寫死磁碟機或個人目錄。測試樣本需先確認可提交範圍；大型 raw 與輸出不進 repository。
