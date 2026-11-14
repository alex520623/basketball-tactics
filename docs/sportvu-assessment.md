# SportVU 資料來源評估

資料來源為
[linouk23/NBA-Player-Movements](https://github.com/linouk23/NBA-Player-Movements)，
查核版本為 `f7d4cf2c7e607029abfd5715a0d4073bedae328e`。
此來源已用於 S1 的單場解析與球場回放，使用範圍見 [資料準備](../data/README.md)。
以下下載與全場統計為 2026-11-12 的查核結果；event 2 的 Backend 結果見 [執行文件](backend-s1.md)。

來源版本、檔案 hash 與統計紀錄見 [sportvu-audit.json](sportvu-audit.json)。

## 結論

技術上適合以單場、單一事件的短片段開始 S1，也能支援 S2 的描述性時空分析。
S3 可在已驗證的量測與規則上產生解釋，但原始追蹤檔本身不提供戰術答案或專家解釋。
完整戰術辨識需要額外標註、評估與資料清理，不能因為有球員座標就視為已解決。

這是與 Pointwise／Cervone 研究相同類型的 SportVU 追蹤資料，不代表與原論文使用了
相同比賽、年份、清理流程或標註。尤其 2015–16 比賽不是 2014 年論文的原始比賽資料。

## 下載狀態與範圍

2026-11-12 查核時，GitHub API 檔案樹與 raw 下載均可用。查核只下載一場壓縮檔與少量讀取程式／metadata，
未 clone 整個 repository，也未進行全資料集下載。

| 項目 | 此次查核結果 |
| --- | --- |
| `.7z` 檔案數 | 636；是檔案數，不保證每個檔案都有完整可用比賽 |
| 壓縮檔合計 | 3,793,503,906 bytes，約 3.79 GB／3.53 GiB |
| 檔名所示日期 | 2015-10-27 至 2016-01-23，並非完整 2015–16 球季 |
| 典型壓縮大小 | 約 6 MB；一般格式檔名組的中位數為 6,078,946 bytes |
| 已發現異常大小 | 4 個檔案僅 32 bytes；另有 1 個僅 2,350 bytes，未將它們當作可用 sample |
| 命名異常 | 10 個檔名帶有多餘的 `2016.NBA.Raw.SportVU.Game.Logs` 前綴；日期仍可識別 |
| 版本狀態 | 調查的 master commit 日期為 2016-09-19，是歷史資料快照 |

數字由固定版本的完整 Git 檔案樹計算，該回應 `truncated=false`。未逐場解壓，所以
不能宣稱所有檔案都可用，也不能由檔案清單推得每場資料完整率。

原始路徑見 [資料目錄](https://github.com/linouk23/NBA-Player-Movements/tree/master/data/2016.NBA.Raw.SportVU.Game.Logs)。
下載時使用上述版本的指定單場檔案，無需 clone 整個資料庫。

## 已驗證的單場 sample

[12.30.2015.LAL.at.BOS.7z](https://github.com/linouk23/NBA-Player-Movements/blob/master/data/2016.NBA.Raw.SportVU.Game.Logs/12.30.2015.LAL.at.BOS.7z)
已實際下載、核對 Git blob SHA，並成功解壓。

| 項目 | 值 |
| --- | --- |
| 比賽 | Los Angeles Lakers at Boston Celtics，2015-12-30 |
| Game ID／JSON | `0021500476`／`0021500476.json` |
| 壓縮大小 | 6,149,333 bytes（約 6.15 MB） |
| 解壓大小 | 102,875,951 bytes（約 102.88 MB／98.11 MiB） |
| 壓縮檔 SHA-256 | `8e622df1fe6909773617a5691a94925bf5624375e106da5801c28fd252890e78` |
| JSON SHA-256 | `5ad649c3b741cc45c01c586cbf073d56d67da0f2315fe7acedb477bc43116036` |
| 事件 | 489，其中 484 個有 moments、5 個為空 |
| S1 測試片段 | `events[1]`，`eventId="2"`，第 1 節，525 個 moments |
| 視窗時間 | timestamp 差 20,959 ms；game clock 從 719.47 至 698.20 秒 |

此片段的 timestamp 嚴格遞增，相鄰差為 39、40 或 41 ms，每筆均有球與 10 名球員。
已完成 Backend 與回放介面的串接測試；攻守方向與戰術意義仍待人工核對。
`event_index=1` 與 `eventId="2"` 是不同欄位；該視窗不能直接稱為完整進攻回合。

下載、解壓與放置步驟見 [資料準備](../data/README.md)。建議將原檔放在
`data/raw/0021500476.json`，再執行 Backend 匯出；已有同一檔案時可指定其實際路徑。

## 單場資料品質實測

以下僅針對這一場，不推廣為全資料集統計。計數以原始事件視窗為單位，包含重疊。

| 檢查項目 | 結果與影響 |
| --- | --- |
| 原始 moments 合計 | 209,431 |
| 唯一 `(period, timestamp, game_clock)` 鍵 | 82,276；原始計數約為唯一鍵計數的 2.55 倍 |
| entities 數量 | 208,079 個 moment 有 11 筆；1,314 個有 10 筆；38 個只有 1 筆 |
| 球缺失 | 1,311 個 moment 找不到 `team_id=-1, player_id=-1` |
| 球員數 | 209,390 個 moment 有 10 人，3 個有 9 人，38 個無球員 |
| shot clock | 19,855 個 moment 為 null |
| timestamp 間隔 | 最常見為 39、40、41 ms；2 個事件出現非嚴格遞增 timestamp |
| 比賽時鐘 | 有停止、回調與較大跳動；不能只用倒數 game clock 當播放時間或去重鍵 |
| 座標範圍 | 所有 entity 的 x 約 -5.87 至 99.43，y 約 -3.10 至 53.65 |
| 未知欄位 | 每個 moment 的第 5 個元素（索引 4）均為 null，語意不明 |

場外座標可能來自發球、邊線活動或追蹤誤差；不能全部刪除，也不能直接夾回場內。
重疊統計尚不是正式去重成果；實作時須比較時間與 entity 狀態，保留事件來源關聯，
再決定衝突解法。同秒 game clock 可對應多個不同 timestamp，不能直接去掉其中的動作。
原 repository 的 [重複片段 issue](https://github.com/linouk23/NBA-Player-Movements/issues/9)
也記錄了事件重疊問題。

## 對 S1、S2、S3 的適用性

| 階段 | 評估 | 可做的內容與條件 |
| --- | --- | --- |
| S1 | 資料條件足夠 | 有球員與隊伍 ID、名單、x/y、球位置、節次與時間；先選一段完整視窗完成 2D 動態展示 |
| S2 描述性分析 | 可行，需清理 | 距離、移動、隊形／空間分布與球員關係；要先處理重疊、時間間隙、換人、場外與座標方向 |
| S2 戰術分類 | 原始檔不足以直接監督學習 | 沒有 Pick-and-Roll、Horns 等戰術標籤，也沒有直接的持球者、傳球或攻守標記；需規則、人工標註或另行驗證的外部標註 |
| S3 解釋 | 條件式可行 | 用 S2 證據、時間範圍與知識規則支援文字解釋；LLM 不提供真實標籤，也不補造位置與判斷依據 |
| 完整自動辨識／改善建議 | 不能只靠此來源保證完成 | 還需可靠的事件切分、任務標註、評估案例與專家判讀；EPV 研究重現也需要額外條件 |

追蹤 JSON 只含事件 ID，沒有事件文字說明、比分、出手結果或戰術名稱。
play-by-play 若要加入，應視為額外來源，先驗證是否可取得、ID 對齊及時鐘偏移；此次未下載。

另找到同源研究 [Supola et al. (2023)](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0281467)
的 S1 File，文章說明有 462 段序列的動作／事件註解，並可藉 game ID 與時間連到此 repository。
這是後續可評估的補充線索：此次未下載、未核對涵蓋範圍，也不等同已有完整戰術分類標籤。

## 限制與採用前決定

- **資料規模與記憶體**：單場文字檔約 103 MB；解析成 Python 物件會再膨脹。S1 只處理
  單場與短片段，避免一次讀入整個球季。若所有檔案有相似壓縮比，解壓總量可能為數十 GB，
  此為單場比例的量級推估，未量測全庫。
- **缺少標註**：event 不等於 possession，球最靠近誰也不等於已確認誰持球；不能把推測當真值。
- **切分與評估洩漏**：同一段動作出現在多個事件，不能隨機以 event 分訓練／測試而不檢查
  重疊。日後辨識宜按不重疊時間區段或比賽分組，人工確認類別。
- **來源文件有限**：原作者的展示程式有位置與名單映射，但不是正式 schema。`Ball.py` 把
  第 5 個 entity 數值命名為 radius，用於畫球大小；不能據此當作真實球半徑。
- **影像與方向**：原始 JSON 沒有同步影片、場地校正矩陣、進攻方向與戰術意圖；身分／
  隊伍不等於進攻／防守角色。畫面方向需在單場 sample 上再核對。
- **授權待確認**：固定版本檔案樹未見 LICENSE，GitHub license metadata 為 null；
  [原始資料授權 issue #15](https://github.com/linouk23/NBA-Player-Movements/issues/15) 仍為 Open。
  公開可下載不代表已確認課程使用或再散布授權，需與課程要求及可取得的來源授權說明核對。

此來源已用於 S1 的指定單場與 `eventId="2"`，Backend 與球場回放均已實作。
後續資料使用範圍依 [資料管理](../data/README.md)，其他比賽與進階分析需另作驗證。

原始欄位見 [SportVU 欄位查核](sportvu-fields.md)；Backend 輸出見
[資料交換規格 0.2.0](data-contract.md)。
