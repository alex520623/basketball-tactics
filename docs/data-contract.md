# Backend JSON 資料交換規格

狀態：**0.2.0 本機 S1 Backend 已實作**。2026-11-13 使用者決定採用 SportVU 作本機小規模
技術驗證，授權仍待確認；Frontend 技術與整合方式未定。本版已實作解析與匯出，沒有 API 或 Frontend。
0.1.0 的純示意公尺／左下角設定由本版取代。

原始欄位與確認程度見 [SportVU 欄位查核](sportvu-fields.md)，下載與品質結果見
[候選來源評估](sportvu-assessment.md)。

## 原則與傳遞方式

- 保留來源的比賽、事件、球隊與球員 ID；輸出用字串，球衣號碼不代替 player ID。
- S1 優先保留 source x／y 的 feet 原值，不先換公尺或鏡射。單位是外部格式資料佐證，
  不是 JSON 自帶的欄位。原點與 y 軸對應畫面的方向仍待核對。
- 保留 timestamp、game clock、shot clock 三者；衍生播放時間必須註明基準。
- 軌跡由 Backend 依 ID 與時間建構，不能當作原檔已有的欄位。
- 球缺失用 null，缺席球員不補點，不以 `(0,0)` 或最近球員代替觀測值。
- 使用標準 UTF-8 JSON，不含 NaN／Infinity，也不把 null 改成 0。

邏輯上定義「片段清單 manifest」與「片段 clip」。檔案模式下，path 相對於 manifest 解析，
如 `clips/id.json`。是否使用本機檔案、HTTP 或 API 傳遞，待 Frontend 選型後共同決定；
此時不要求任何 server 或網址已存在。

## 欄位說明與來源對照

下表區分來源值、外部參考與衍生資訊，避免將工程規格當成原始資料供應的標註。

| 輸出欄位 | 型別 | 來源／定義 |
| --- | --- | --- |
| `schema_version` | string | 衍生：0.2.0；不相容版本須明示 |
| `clip_id` | string | 衍生片段 ID，使用安全檔名字元；不是 eventId |
| `provenance` | object | 來源檔名、hash、commit，與是否為合成／截取資料的 metadata |
| `game.game_id`／`game_date` | string | 來源 gameid／gamedate |
| `source_event.event_id` | string | 來源 events[i].eventId，不是戰術或完整回合 ID |
| `source_event.event_index` | integer | 原始 events 的零起算索引 |
| `source_event.start_moment_index`／`end_moment_index` | integer | 原始 moments 截取範圍，起訖均包含 |
| `coordinate_system` | object | feet、source frame、球場參考尺寸及方向確認狀態；為參考與轉換 metadata |
| `teams[]` | array | home／visitor 的 teamid、name、abbreviation；side 來自物件所屬主／客隊 |
| `players[]` | array | 本 clip 出現的 playerid、firstname、lastname、jersey、position，欄名改為 snake_case |
| `frames[]` | array | 衍生逐影格文件，對應所選 moments，保留來源索引 |
| `trajectories[]` | array | 衍生的球員／球軌跡分段索引 |
| `quality.warnings[]` | array | 衍生品質訊息：缺球、缺員、時間中斷、場外或身分衝突等 |

每個 frame：

| 欄位 | 型別／null 規則 | 原始來源或計算 |
| --- | --- | --- |
| `frame_index` | 從 0 連續增加的 integer | 輸出索引，原始 JSON 沒有正式 frame ID |
| `t_ms` | 從 0 嚴格遞增的 integer | 合法連續片段中 moment[1] 減片段起始 moment[1] |
| `source_moment_index` | integer | 原始事件的 moment 零起算位置 |
| `source_timestamp_ms` | integer | moment[1] 原值，不代表已校正至影片或 play-by-play |
| `period` | integer | moment[0]；不預先排除延長賽 |
| `game_clock_s` | number 或 null | moment[2]，本節剩餘秒數；缺失／無效時為 null 並警告，不能取代 timestamp |
| `shot_clock_s` | number 或 null | moment[3] 原值 |
| `source_aux` | 原始 JSON 值；sample 為 null | moment[4]，語意未知，不指定為 confidence／possession |
| `players[]` | array，可空 | 該影格有效球員點，不用固定順序或固定筆數假設 |
| `players[].player_id`／`team_id` | string | entity[1]／entity[0]，供 ID 與隊伍連接 |
| `players[].x`／`y` | finite number | entity[2]／entity[3]，保留 source feet，場外亦保留並標記 |
| `players[].position_z_raw` | number 或 null | entity[4] 原值；sample 為 0，不視為人體高度 |
| `players[].break_before` | boolean | 衍生：本點前是否切斷軌跡 |
| `ball` | object 或 null | 由 team_id、player_id 皆為 -1 識別，不假設永遠位於陣列第一筆 |
| `ball.x`／`y`／`z` | finite number；z 無值時 null | 球 entity[2:5]；z 的高度語意有外部格式佐證，保留原值 |
| `ball.break_before` | boolean | 衍生：球軌跡是否重新開始 |

## 時間與軌跡分段

`timeline.time_basis` 為 source_timestamp_delta，duration_ms 等於最後一筆 t_ms。
nominal_interval_ms=40 來自 sample 與 25 Hz 格式參考，不代表每筆恰隔 40 ms。
gap_threshold_ms 是工程品質參數，不是來源欄位；尚未定案可為 null，正式匯出及驗收前
須記錄採用的閾值與理由，不能用未定參數宣稱清理已完成。

timestamp 回退、跨節或來源中斷須先分段。同 timestamp 且 entity 狀態相同的重複點，
可在保留來源索引後去重；狀態衝突則記錄並停止或隔離，不靜默覆蓋。
同 game clock 可有不同 timestamp 與持續移動，不能單以 `(period, game_clock)` 去重。

每個 trajectories 項目包含 entity_type（player／ball）、entity_id 與 segments。
球使用規格代號 ball；球員使用原 player ID。segments 以包含起訖的 start_frame_index、
end_frame_index 指向 frames，座標以 frames 為唯一來源，避免重複資料不一致。
段內每影格都必須有該 entity 的有效位置；第一點 break_before 為 true，其餘為 false。
缺漏、ID 衝突或超過已確認時間間隙就另開一段，不插值、不跨缺漏連線。

players metadata 要收集整個 clip 出現的球員，不能只取第一影格；team_id 以各位置來源值
對照球隊 metadata。名單 position 不代表當下進攻／防守角色。Frontend 可據這些索引繪製
軌跡，不必依賴 SportVU tuple 的索引或重做資料清理。

## 欄位映射範例

以下為文件中的規格映射例，數值取自已抽查 sample 的 `events[1].moments[0:2]`。
這不是已實作 exporter 的結果，也不是正式採用宣告或完整展示片段。
兩個 moments 相隔 39 ms；完整候選事件為 525 個 moments、20,959 ms，不可混用。

### 片段清單

```json
{
  "schema_version": "0.2.0",
  "dataset": {"id": "sportvu-2015-16-candidate", "name": "NBA-Player-Movements", "version": "f7d4cf2c7e607029abfd5715a0d4073bedae328e", "adoption_status": "pending"},
  "clips": [
    {"clip_id": "0021500476-e2-preview", "label": "LAL at BOS：event 2 前兩個 moments（規格映射例）", "path": "clips/0021500476-e2-preview.json", "duration_ms": 39, "frame_count": 2}
  ]
}
```

### 片段資料

```json
{
  "schema_version": "0.2.0",
  "clip_id": "0021500476-e2-preview",
  "provenance": {"source_file": "0021500476.json", "source_file_sha256": "5ad649c3b741cc45c01c586cbf073d56d67da0f2315fe7acedb477bc43116036", "source_commit": "f7d4cf2c7e607029abfd5715a0d4073bedae328e", "is_synthetic": false, "is_excerpt": true},
  "game": {"game_id": "0021500476", "game_date": "2015-12-30"},
  "source_event": {"event_id": "2", "event_index": 1, "start_moment_index": 0, "end_moment_index": 1},
  "coordinate_system": {"unit": "ft", "unit_basis": "external_format_reference", "frame": "source", "court_length": 94, "court_width": 50, "court_size_basis": "reference_geometry", "display_orientation": "unconfirmed"},
  "timeline": {"time_basis": "source_timestamp_delta", "source_timestamp_origin_ms": 1451522482002, "duration_ms": 39, "nominal_interval_ms": 40, "gap_threshold_ms": null},
  "teams": [
    {"side": "home", "team_id": "1610612738", "name": "Boston Celtics", "abbreviation": "BOS"},
    {"side": "visitor", "team_id": "1610612747", "name": "Los Angeles Lakers", "abbreviation": "LAL"}
  ],
  "players": [
    {"player_id": "101161", "first_name": "Amir", "last_name": "Johnson", "jersey": "90", "position": "F"},
    {"player_id": "202738", "first_name": "Isaiah", "last_name": "Thomas", "jersey": "4", "position": "G"},
    {"player_id": "202340", "first_name": "Avery", "last_name": "Bradley", "jersey": "0", "position": "G"},
    {"player_id": "203109", "first_name": "Jae", "last_name": "Crowder", "jersey": "99", "position": "F"},
    {"player_id": "203096", "first_name": "Jared", "last_name": "Sullinger", "jersey": "7", "position": "C-F"},
    {"player_id": "977", "first_name": "Kobe", "last_name": "Bryant", "jersey": "24", "position": "F-G"},
    {"player_id": "201579", "first_name": "Roy", "last_name": "Hibbert", "jersey": "17", "position": "C"},
    {"player_id": "101150", "first_name": "Lou", "last_name": "Williams", "jersey": "23", "position": "G"},
    {"player_id": "203903", "first_name": "Jordan", "last_name": "Clarkson", "jersey": "6", "position": "G"},
    {"player_id": "1626204", "first_name": "Larry", "last_name": "Nance Jr.", "jersey": "7", "position": "F"}
  ],
  "frames": [
    {
      "frame_index": 0,
      "t_ms": 0,
      "source_moment_index": 0,
      "source_timestamp_ms": 1451522482002,
      "period": 1,
      "game_clock_s": 719.47,
      "shot_clock_s": 15.5,
      "source_aux": null,
      "players": [
        {"player_id": "101161", "team_id": "1610612738", "x": 51.91985, "y": 26.55836, "position_z_raw": 0.0, "break_before": true},
        {"player_id": "202738", "team_id": "1610612738", "x": 66.15059, "y": 28.9238, "position_z_raw": 0.0, "break_before": true},
        {"player_id": "202340", "team_id": "1610612738", "x": 48.30817, "y": 15.47903, "position_z_raw": 0.0, "break_before": true},
        {"player_id": "203109", "team_id": "1610612738", "x": 43.18509, "y": 33.07181, "position_z_raw": 0.0, "break_before": true},
        {"player_id": "203096", "team_id": "1610612738", "x": 56.97831, "y": 25.40036, "position_z_raw": 0.0, "break_before": true},
        {"player_id": "977", "team_id": "1610612747", "x": 42.72761, "y": 34.50613, "position_z_raw": 0.0, "break_before": true},
        {"player_id": "201579", "team_id": "1610612747", "x": 48.15678, "y": 28.32863, "position_z_raw": 0.0, "break_before": true},
        {"player_id": "101150", "team_id": "1610612747", "x": 30.31294, "y": 29.20461, "position_z_raw": 0.0, "break_before": true},
        {"player_id": "203903", "team_id": "1610612747", "x": 34.20393, "y": 24.47888, "position_z_raw": 0.0, "break_before": true},
        {"player_id": "1626204", "team_id": "1610612747", "x": 43.46494, "y": 15.96169, "position_z_raw": 0.0, "break_before": true}
      ],
      "ball": {"x": 44.12405, "y": 29.72198, "z": 3.55411, "break_before": true}
    },
    {
      "frame_index": 1,
      "t_ms": 39,
      "source_moment_index": 1,
      "source_timestamp_ms": 1451522482041,
      "period": 1,
      "game_clock_s": 719.43,
      "shot_clock_s": 15.49,
      "source_aux": null,
      "players": [
        {"player_id": "101161", "team_id": "1610612738", "x": 52.11714, "y": 26.58173, "position_z_raw": 0.0, "break_before": false},
        {"player_id": "202738", "team_id": "1610612738", "x": 66.03941, "y": 28.91028, "position_z_raw": 0.0, "break_before": false},
        {"player_id": "202340", "team_id": "1610612738", "x": 48.30541, "y": 15.47497, "position_z_raw": 0.0, "break_before": false},
        {"player_id": "203109", "team_id": "1610612738", "x": 42.96816, "y": 32.79416, "position_z_raw": 0.0, "break_before": false},
        {"player_id": "203096", "team_id": "1610612738", "x": 57.00947, "y": 25.3812, "position_z_raw": 0.0, "break_before": false},
        {"player_id": "977", "team_id": "1610612747", "x": 42.67159, "y": 34.52646, "position_z_raw": 0.0, "break_before": false},
        {"player_id": "201579", "team_id": "1610612747", "x": 48.15679, "y": 28.47307, "position_z_raw": 0.0, "break_before": false},
        {"player_id": "101150", "team_id": "1610612747", "x": 30.33207, "y": 29.19656, "position_z_raw": 0.0, "break_before": false},
        {"player_id": "203903", "team_id": "1610612747", "x": 34.2055, "y": 24.54264, "position_z_raw": 0.0, "break_before": false},
        {"player_id": "1626204", "team_id": "1610612747", "x": 43.36916, "y": 15.99698, "position_z_raw": 0.0, "break_before": false}
      ],
      "ball": {"x": 43.69531, "y": 29.67979, "z": 3.75717, "break_before": false}
    }
  ],
  "trajectories": [
    {
      "entity_type": "player",
      "entity_id": "101161",
      "segments": [
        {"start_frame_index": 0, "end_frame_index": 1}
      ]
    },
    {
      "entity_type": "player",
      "entity_id": "202738",
      "segments": [
        {"start_frame_index": 0, "end_frame_index": 1}
      ]
    },
    {
      "entity_type": "player",
      "entity_id": "202340",
      "segments": [
        {"start_frame_index": 0, "end_frame_index": 1}
      ]
    },
    {
      "entity_type": "player",
      "entity_id": "203109",
      "segments": [
        {"start_frame_index": 0, "end_frame_index": 1}
      ]
    },
    {
      "entity_type": "player",
      "entity_id": "203096",
      "segments": [
        {"start_frame_index": 0, "end_frame_index": 1}
      ]
    },
    {
      "entity_type": "player",
      "entity_id": "977",
      "segments": [
        {"start_frame_index": 0, "end_frame_index": 1}
      ]
    },
    {
      "entity_type": "player",
      "entity_id": "201579",
      "segments": [
        {"start_frame_index": 0, "end_frame_index": 1}
      ]
    },
    {
      "entity_type": "player",
      "entity_id": "101150",
      "segments": [
        {"start_frame_index": 0, "end_frame_index": 1}
      ]
    },
    {
      "entity_type": "player",
      "entity_id": "203903",
      "segments": [
        {"start_frame_index": 0, "end_frame_index": 1}
      ]
    },
    {
      "entity_type": "player",
      "entity_id": "1626204",
      "segments": [
        {"start_frame_index": 0, "end_frame_index": 1}
      ]
    },
    {
      "entity_type": "ball",
      "entity_id": "ball",
      "segments": [
        {"start_frame_index": 0, "end_frame_index": 1}
      ]
    }
  ],
  "quality": {
    "warnings": [
      {"code": "EXCERPT_ONLY", "message": "僅包含事件前兩個 moments；不是完整展示視窗或正式匯出結果。"}
    ]
  }
}
```

## 驗收與範圍

- manifest 與 clip 的版本、ID、影格數、時間長度須一致；檔案 path 不含 `..` 或外部網址。
- 每影格 player ID 不重複且有 metadata；缺球不能導致球與球員錯位。
- 場外、缺漏、事件重疊與未知欄位均有紀錄，不把合理場外座標直接刪掉或夾回場內。
- 不輸出假定的持球者、攻守方、戰術類別、信心值、傳球或改善建議。
- 本版不決定 Frontend 框架、HTTP API、部署方式或整套系統選型。

## 實作補充：連續 clip 與品質資訊

完整執行方式與本次 525 影格輸出見 [S1 Backend](backend-s1.md)。上方兩影格範例保留作
欄位映射說明，不代表目前完整輸出；正式匯出 gap_threshold_ms 一定是指定的正整數。

- 時間間隔大於指定門檻、timestamp 回退或跨節會分成多個 clip；每個保留同一來源
  eventId 與原始 moment 範圍，不把不連續時間重新排序或偽裝成一個回合。
- 同 timestamp 且完整 moment 相同者去重；若資料衝突，直接失敗，避免默選一筆。
- 壞 timestamp／moment 移除並記錄；其後有效點中斷軌跡。缺球、無效位置、重複 entity ID
  亦不補點，重新出現時建立新段。缺失的倒數時鐘輸出 null，不製造時間值。
- 有限且合理的場外座標保持原值；超過 coordinate_limit_ft（預設 1000）的極端 x／y 點
  移除並警告。此為工程保護參數，不是球場邊界或供應商規格；不聲稱能偵測所有追蹤誤差。
- quality 新增 policy 與 summary，記錄門檻、缺漏處理及來源事件的輸入／丟棄／去重／分段統計。
  warnings 的 scope 為 source_event，跨 clip 共用來源事件警告；每筆保留 source_moment_index，
  frame_index 只在該來源點位於當前 clip 時有值，否則為 null。
- source_file_sha256 以串流計算；沒有確認過 source_commit 時用 null。manifest 標記
  adoption_status=local_s1_validation、license_status=unconfirmed、usage_scope=local_small_scale。

以上為補足未定品質政策與可觀測性的欄位，保留 0.2.0 的核心物件結構；Frontend 應能忽略
額外品質 metadata，但必須處理 null 與多 clip。後續不相容改動再更新 schema version。

S2／S3 的速度、距離、模式與解釋另定衍生結果格式，需標示計算方法與證據來源。
其他比賽仍須驗證，不能只憑單場 sample 宣稱全庫相容。
