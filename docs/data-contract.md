# S1 資料交換規格

狀態：**0.1.0 草案**，尚未實作 importer、匯出或 Frontend loader。這份規格是工程提案，
不是簡報已指定的資料欄位；取得原先選定資料集的 sample 後，由前後端共同確認。

## 檔案與載入

| 檔案 | 用途 |
| --- | --- |
| `outputs/demo/data/manifest.json` | 資料集與可用片段清單 |
| `outputs/demo/data/clips/{clip_id}.json` | 單一片段的場地、球員與逐影格位置 |
| `data/processed/` 下的品質報告 | Backend 保存原始來源、欄位映射、轉換參數及異常統計 |

Frontend 先讀取 `/data/manifest.json`。清單內 `path` 相對於 manifest URL 解析，
例如 `clips/example-clip.json` 對應 `/data/clips/example-clip.json`。
路徑須在 `data/` 下，不能含 `..` 或指向外部網址。這些是未來靜態展示的讀取路徑，
目前沒有已上線的 API endpoint。

檔案使用 UTF-8、標準 JSON；數值不可為 NaN 或 Infinity。ID 一律為字串，避免
JavaScript 數值精度或前置零造成身分變更。S1 每次載入一個短片段；若過大，先縮短展示
時間範圍，避免直接匯出整場或未記錄地降低採樣率。

## 共同欄位與定義

| 範圍 | 欄位 | 型別與規則 |
| --- | --- | --- |
| 兩種檔案 | `schema_version` | 字串，草案為 `0.1.0`；不相容版本須顯示錯誤，不靜默套用 |
| manifest | `dataset` | `{id, name, version, is_synthetic}`；版本未知時用 null 並記錄原因 |
| manifest | `clips` | 陣列；每筆含 `clip_id, label, path, duration_ms, frame_count` |
| clip | `clip_id` | 與 manifest 一致，採安全檔名字元 `A-Z a-z 0-9 _ -` |
| clip | `provenance` | 來源資料集、版本、原始檔 SHA-256、來源片段 ID、合成資料旗標及轉換摘要 |
| clip | `court` | 長寬、單位、原點、軸向、全／半場與場地規則；詳見座標段落 |
| clip | `timeline` | `duration_ms, nominal_sample_interval_ms, continuity_gap_ms` |
| clip | `teams` | `{team_id, label}` 陣列；無隊伍資料可為空陣列 |
| clip | `players` | `{player_id, team_id, label}` 陣列；未知隊伍為 null，label 僅供顯示 |
| clip | `frames` | 按 `t_ms` 嚴格遞增的影格陣列，至少一筆 |
| clip | `quality.warnings` | `{code, message, frame_index, player_id}` 陣列；不適用的定位欄位為 null |

`provenance` 至少包含 `dataset_id, dataset_version, is_synthetic, source_file_sha256,
source_segment_id, transform_description`。真實展示必須能以來源檔 hash 與片段定位回原始資料；
沒有來源片段 ID 時，以可重現的來源範圍寫入轉換紀錄。不得把無來源的示意資料標成真實資料。

### 座標

- 標準分析單位建議為公尺；`court.unit` 固定為 `m`，`length` 與 `width` 必須大於 0。
- 原點為左下角，x 沿場地長度增加、y 沿寬度增加。顯示端將 y 轉成畫布向下的方向，
  並保持等比例，不改變標準資料。
- `scope` 為 `full` 或 `half`；長寬描述實際表示範圍。半場資料不得鏡射補成未觀測的全場。
- `rule_set` 為來源可確認的規則名稱或 null；場地線條與尺寸須由來源／聯盟規則確認，
  不能預設為 NBA 或 FIBA。未知規則須在介面標示，不繪製假定的精確線條。
- 原始單位、原點、軸向與縮放係數保存在 Backend 轉換紀錄；未知單位或尺度不能直接
  當成公尺。先確認 Q2，再輸出真實資料的標準座標。
- 全／半場、影像座標及攻守方向是不同概念。S1 保持來源可核對的方向，不推測攻守、
  持球者或每節換邊；日後如需進攻方向正規化，另外保存轉換資訊。

### 時間

- `frame_index` 是輸出片段內從 0 起的連續整數，不等於原始影格編號。
- `t_ms` 是距片段第一筆有效樣本的毫秒數，第一筆為 0，之後嚴格遞增。
- `duration_ms` 等於最後一筆 `t_ms`；單影格片段為 0，介面只顯示靜態位置。
- `source_frame_id` 保留來源編號，無值時為 null；`source_clock` 可為 null，或
  `{period, remaining_s}`，保留比賽節次與倒數時間，不能直接當作遞增的播放時間。
- 原始時間若在換節、回合或攝影區段重置，先分段再建立相對時間；不可跨重置直接排序。
- `nominal_sample_interval_ms` 是確認過的採樣間隔，非均勻或未知時為 null。
- `continuity_gap_ms` 為正數，定義連續軌跡可接受的最大時間間隙；依實際採樣與品質設定，
  不是畫面 FPS。取得資料前不先填入通用閾值。

### 逐影格內容與缺漏

每筆 frame 包含 `frame_index, t_ms, source_frame_id, source_clock, players, ball`。
`players` 每筆為 `{player_id, x, y, break_before}`，位置為有限數值，ID 須出現在球員清單，
同一影格不可重複同一 ID。不同球員共用相同來源時間是正常情況，應合成同一輸出影格。

| 情況 | Backend 行為 | Frontend 行為 |
| --- | --- | --- |
| 某球員該影格無有效位置 | 不輸出該球員點，記錄警告；不以 `(0,0)` 補值 | 隱藏當下位置；再次出現時重啟軌跡 |
| 時間間隙大於閾值，或來源區段中斷 | 重新出現的點設 `break_before: true` | 不連接中斷兩端 |
| 第一個有效點 | `break_before: true` | 從此點開始一段軌跡 |
| 無球位置 | `ball: null` | 不顯示球；不由最近球員推測球的位置 |
| 有球位置 | `ball: {x, y, z, break_before}`；沒有高度時 z 為 null | S1 只顯示 x、y，高度不影響 2D 位置 |
| 無隊伍／姓名 | ID 保持穩定，隊伍為 null，label 可用來源 ID | 顯示未知隊伍或 ID，不假造球員姓名 |
| 座標超界、重複 ID、時間無法解讀 | 依已確認規則拒收或隔離，品質報告說明 | 不自行夾回場內或猜測正確數值 |

如果來源只有追蹤 ID，必須說明它代表追蹤軌跡而非已確認的真實球員身分。
不固定要求每影格 10 人；依來源確認預期參與者，記錄缺漏，而非把未知身分補滿。
S1 不做座標插值，避免在缺漏區段產生看似真實的動作。

## 純示意範例

下列兩段 JSON 只示範契約，**不是選定資料集、測試成果或真實比賽片段**。兩位球員、
28×15 公尺與 1 秒採樣均為示意值，不據此指定聯盟、資料集或實際採樣方式。

### manifest.json

```json
{
  "schema_version": "0.1.0",
  "dataset": {
    "id": "illustrative-only",
    "name": "規格示意",
    "version": null,
    "is_synthetic": true
  },
  "clips": [
    {
      "clip_id": "example-clip",
      "label": "示意片段",
      "path": "clips/example-clip.json",
      "duration_ms": 1000,
      "frame_count": 2
    }
  ]
}
```

### clips/example-clip.json

```json
{
  "schema_version": "0.1.0",
  "clip_id": "example-clip",
  "provenance": {
    "dataset_id": "illustrative-only",
    "dataset_version": null,
    "is_synthetic": true,
    "source_file_sha256": null,
    "source_segment_id": null,
    "transform_description": "純規格示意，未接入資料集"
  },
  "court": {
    "unit": "m",
    "length": 28,
    "width": 15,
    "origin": "bottom_left",
    "x_axis": "length",
    "y_axis": "width",
    "scope": "full",
    "rule_set": null
  },
  "timeline": {
    "duration_ms": 1000,
    "nominal_sample_interval_ms": 1000,
    "continuity_gap_ms": 1500
  },
  "teams": [],
  "players": [
    {"player_id": "p1", "team_id": null, "label": "示意球員 1"},
    {"player_id": "p2", "team_id": null, "label": "示意球員 2"}
  ],
  "frames": [
    {
      "frame_index": 0,
      "t_ms": 0,
      "source_frame_id": null,
      "source_clock": null,
      "players": [
        {"player_id": "p1", "x": 10, "y": 6, "break_before": true},
        {"player_id": "p2", "x": 12, "y": 8, "break_before": true}
      ],
      "ball": null
    },
    {
      "frame_index": 1,
      "t_ms": 1000,
      "source_frame_id": null,
      "source_clock": null,
      "players": [
        {"player_id": "p1", "x": 11, "y": 6.5, "break_before": false},
        {"player_id": "p2", "x": 12.5, "y": 8, "break_before": false}
      ],
      "ball": null
    }
  ],
  "quality": {
    "warnings": [
      {"code": "SYNTHETIC_EXAMPLE", "message": "純示意資料", "frame_index": null, "player_id": null}
    ]
  }
}
```

## 介面驗收與後續相容性

Backend 驗證上述欄位、時間單調、ID 對照、空值與範圍；Frontend 檢查版本與載入結果，
顯示格式錯誤、檔案不存在或空片段等狀態。缺漏不應導致假球員、假球位置或跨間隙軌跡。
manifest 與 clip 的 ID、資料來源、版本、長度與影格數須一致。

格式更動以 PR 記錄，前後端一起更新範例與驗證。草案期間修改也須記錄版本；不能
只更名欄位而不通知另一端。取得真實 sample 前，0.1.0 不視為已凍結的開發契約。

S2 結果預計另存分析檔，至少包含 `clip_id, analysis_version, method, parameters,
time_range_ms, player_ids, evidence`；缺乏標籤時保存模式描述，不填入假定戰術答案。
S3 解釋預計引用分析與規則的 ID，保存文字、限制與引用關係。完整分析介面於 S2 開始前
再定義，S1 Frontend 不要求這些檔案存在。
