# S1 Backend：執行與交接

驗證日期：2026-11-13。SportVU 2015–16 已選為 S1 本機小規模技術驗證來源，授權仍待確認。
只處理既有單場檔案，不提供整庫下載、Frontend、戰術辨識、LLM 或訓練功能。

## 程式入口

| 檔案 | 功能 |
| --- | --- |
| `src/basketball_tactics/sportvu.py` | 串流讀取單場，依 eventId 選事件，驗證來源與 hash |
| `src/basketball_tactics/backend.py` | 位置與時間映射、品質處理、軌跡分段、manifest 與 clip 匯出 |
| `src/basketball_tactics/cli.py` | 本機命令列入口與錯誤回報 |
| `tests/test_sportvu_backend.py` | 真實事件回歸測試及真實資料複本的故障注入 |

解析使用 [ijson](https://pypi.org/project/ijson/)，依序建立單個 event，而非整場 JSON 的 Python
物件。掃至檔案結尾以檢查 JSON 完整性與重複 eventId；記憶體主要隨最大 event 與選定
event 大小增加。來源 hash 以串流計算，不讀入全部檔案 bytes。一次僅處理指定單場。

## Sample 與安裝

本機既有檔案為 `.tools/sportvu-review/0021500476.json`，未重新下載。比賽是
2015-12-30 Lakers at Celtics，SHA-256：

```text
5ad649c3b741cc45c01c586cbf073d56d67da0f2315fe7acedb477bc43116036
```

其他電腦先取得同一單場原檔，來源與壓縮檔 hash 見 [資料評估](sportvu-assessment.md)。
不要 clone 全部 636 個壓縮檔；原始檔保留本機，不能提交 Git。

在專案根目錄安裝依賴：

```powershell
# Windows
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

```bash
# macOS
.venv/bin/python -m pip install -r requirements.txt
```

## 匯出

以下讀取原始 `eventId="2"`，不是 `events[2]`，也不把它稱為完整進攻回合。
輸出目錄必須尚不存在；這台電腦已產生 `outputs/s1-event-2/`，若重跑，請換成
`outputs/s1-event-2-rerun/` 等新名稱，程式不覆蓋既有輸出。

```powershell
.\.venv\Scripts\python.exe -m basketball_tactics.cli `
  --input .tools/sportvu-review/0021500476.json `
  --event-id 2 `
  --output-dir outputs/s1-event-2 `
  --gap-threshold-ms 120 `
  --source-commit f7d4cf2c7e607029abfd5715a0d4073bedae328e `
  --expected-sha256 5ad649c3b741cc45c01c586cbf073d56d67da0f2315fe7acedb477bc43116036
```

```bash
.venv/bin/python -m basketball_tactics.cli \
  --input .tools/sportvu-review/0021500476.json \
  --event-id 2 \
  --output-dir outputs/s1-event-2 \
  --gap-threshold-ms 120 \
  --source-commit f7d4cf2c7e607029abfd5715a0d4073bedae328e \
  --expected-sha256 5ad649c3b741cc45c01c586cbf073d56d67da0f2315fe7acedb477bc43116036
```

`--gap-threshold-ms` 必填；120 ms 是本次採用的工程參數，約為 nominal 40 ms 的三倍，
不是 SportVU 來源標註，也不會把 timestamp 強制改成 40 ms。`--coordinate-limit-ft`
預設 1000，作為極端數值保護，可明確調整；94×50 邊界外的合理位置仍保留並警告。
commit 未提供時輸出 null；只有確認過來源版本才傳入該參數。

輸出為 JSON 0.2.0：

```text
outputs/s1-event-2/
├── manifest.json
└── clips/
    └── 0021500476-e2-s001.json
```

manifest 的 path 相對於 manifest 所在目錄。若事件有間隙、timestamp 回退或跨節，輸出
多個 `s001`、`s002` clip，每個從 t_ms=0 開始，均保留原始 eventId、timestamp 與 moment
索引。來源衝突、空事件、hash 不符或格式無法讀取會回報失敗，不發布完整輸出目錄。

## 本次實測

| 項目 | 結果 |
| --- | --- |
| 來源 | `0021500476.json`，102,875,951 bytes |
| eventId／event_index | `"2"`／1 |
| 輸出 clip | 1，525 影格、20,959 ms |
| 時間間隔 | 39 ms：129 次；40 ms：267 次；41 ms：128 次 |
| 人員與球 | 每影格 10 人與 1 球，10 人 metadata，11 條 entity 軌跡 |
| 品質警告 | 24 次 OUT_OF_COURT，均為 player ID `1626204` 的負 x 值，影格 392–415 |
| 清理結果 | 本事件無丟棄 moment、無 timestamp 去重，場外位置原樣保留 |
| clip 大小 | 732,056 bytes，約 715 KiB |
| Windows 記憶體 | 單次匯出峰值工作集約 31 MiB，含 Python／parser；約 4.2 秒 |
| 測試 | 28 passed，pip check 通過 |

記憶體與時間僅為本次單場、單程序量測，不是全資料或所有平台的保證。macOS 尚未實測。
場外位置不能據此判定是發球或誤追蹤，畫面與戰術意義仍需人工核對。

## 測試

```powershell
# 使用既有預設 sample，或將 SPORTVU_SAMPLE 設為同一真實檔案的其他路徑
$env:SPORTVU_SAMPLE = (Resolve-Path .tools/sportvu-review/0021500476.json).Path
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
```

```bash
SPORTVU_SAMPLE="/absolute/path/0021500476.json" .venv/bin/python -m pytest -q
.venv/bin/python -m pip check
```

測試逐影格核對所有原始 ID、位置與三種時間資訊，並檢查來源 hash、實際非固定間隔、
軌跡、manifest 及拒絕覆蓋。另將真實片段複本作明確故障注入，驗證缺球、缺員、非有限／
極端座標、重複 ID、空時鐘、壞 moment、重複 timestamp、回退、跨節與時間間隙。
沒有提交 raw fixture，也沒有以合成資料代替正式 sample。

預設 sample 不在新 clone 內；未提供 sample 時 Backend 測試會明確 skip，不能視為 Backend
驗證通過。若明確設定 SPORTVU_SAMPLE 卻不存在，則測試失敗；hash 不同也失敗。

## Frontend 交接

已可在本機交付完整 manifest 與 clip JSON，格式見 [欄位規格](data-contract.md)。
Frontend 可以依 teams、players、frames、trajectories 讀取真實事件，不需要了解原始 tuple。
傳輸與框架選型仍由組員確認，資料不放進公開網站或 Git。

- 位置單位是 feet，保留 source 軸向；display_orientation 仍為 unconfirmed。
- 畫面應使用 t_ms；比賽倒數與 shot clock 另作標籤。
- 缺球用 null，缺席球員沒有點；依 break_before／segments 中斷軌跡，不跨缺漏連線。
- 展示品質警告；場外點可保留在有邊界留白的畫面，不能靜默改寫數值。
- 此交付是 Backend 資料已可供整合，不代表 S1 網頁與畫面驗收已完成。
