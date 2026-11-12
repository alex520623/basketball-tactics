# SportVU 原始欄位查核

以下已核對 `0021500476.json` 全場結構與原 repository 讀取程式，僅保證此次 sample 的觀察，
不宣稱其他比賽完全相同。來源版本、大小與 hash 見 [評估報告](sportvu-assessment.md)。

## 根物件與事件

| 原始路徑 | sample 型別／內容 | 意義與注意事項 |
| --- | --- | --- |
| `gameid` | 字串，`0021500476` | 比賽 ID，保留前置零 |
| `gamedate` | 字串，`2015-12-30` | 比賽日期，不直接當作 UTC timestamp 的日期 |
| `events` | 489 筆物件陣列 | 事件視窗，有重疊及空 moments，不等於完整進攻回合 |
| `events[i].eventId` | 字串 | 來源事件 ID，不是陣列索引，也不是戰術標籤 |
| `events[i].home`／`visitor` | 物件 | 主／客隊 metadata 與球員名單 |
| `events[i].moments` | 陣列，可為空 | 時間序列，每筆為 6 個元素的 tuple |

這場 489 個 event 的欄位集合均只有 `eventId, home, visitor, moments`。
沒有事件名稱、得分、傳球、持球者或戰術類別欄位。

## 球隊與球員名單

| 原始欄位（home／visitor 下） | sample 型別 | 意義 |
| --- | --- | --- |
| `teamid` | 整數 | 球隊 ID；輸出可轉字串，但須保留來源值 |
| `name` | 字串 | 例：Boston Celtics、Los Angeles Lakers |
| `abbreviation` | 字串 | BOS、LAL |
| `players` | 物件陣列 | sample 首事件兩隊各 13 人；名單不代表同時在場 |
| `players[j].playerid` | 整數 | 與位置 tuple 的 player ID 連接 |
| `players[j].firstname`／`lastname` | 字串 | 球員姓名 |
| `players[j].jersey` | 字串 | 球衣號碼，如 `"0"`、`"24"`；不是唯一識別碼 |
| `players[j].position` | 字串 | 名單位置，如 G、F-G、C-F；不是當下戰術角色 |

主隊 `teamid=1610612738`，客隊 `1610612747`。例如 Avery Bradley 的 player ID 為
`202340`，Kobe Bryant 為 `977`。以 ID 連接名單與位置，不以 entity 順序或球衣號碼連接。
原始讀取邏輯可參考 [Event.py](https://github.com/linouk23/NBA-Player-Movements/blob/master/Event.py)
與 [Player.py](https://github.com/linouk23/NBA-Player-Movements/blob/master/Player.py)。

## moment tuple

```text
[
  period,
  timestamp,
  game_clock,
  shot_clock,
  unknown,
  entities
]
```

| 索引 | sample 值／型別 | 查核結果 |
| --- | --- | --- |
| `[0]` | 1–4，整數 | 節次；本場無延長賽，其他場不限制為 4 |
| `[1]` | 13 位整數，如 `1451522482002` | timestamp，解讀為 epoch 毫秒與比賽日期一致；相鄰多為 39／40／41 ms。外部原始 API client 及逐欄分析亦將此欄解讀為 timestamp，但原 repository 無 vendor schema |
| `[2]` | 數值，如 `719.47` | 本節剩餘秒數；會停表、修正或跳動 |
| `[3]` | 數值或 null，如 `15.5` | shot clock 剩餘秒數，不可假設永遠有值或單調 |
| `[4]` | 全場均為 null | 語意未確認，保留 raw 值，不命名為 confidence 或 possession |
| `[5]` | entities 陣列 | 通常球＋10 人，但 sample 存在缺球或缺球員 |

`Moment.py` 直接讀取 `[0]`、`[2]`、`[3]`，並假設 `[5][0]` 為球。sample 中有缺球影格，
因此正式 importer 不應直接照抄這項假設，而應檢查 entity 的 ID。

時間語意的交叉參考為原始 API client 的 [Moment 定義](https://github.com/bttmly/nba-movement#moment)
與 [逐欄資料分析](https://danvatterott.com/creating-videos-of-nba-action-with-sportsvu-data.html)。
兩者是格式參考，不代表舊 NBA API 目前仍能使用。S1 播放時間建議以 sample timestamp 差建立，
並保留倒數時鐘作顯示；timestamp 並不等於可無誤對齊外部影片或 play-by-play 的時鐘。

## entity tuple 與座標

```text
[team_id, player_id, x, y, component_4]
```

| 索引 | 球員 | 球 |
| --- | --- | --- |
| `[0]` | 球隊 ID | sample 為 -1 |
| `[1]` | 球員 ID | sample 為 -1 |
| `[2]`、`[3]` | x、y | x、y |
| `[4]` | 全場球員均為 0.0，不視為人體高度 | 連續變化的第 3 座標，格式資料將其解釋為 z／高度；sample 約 0.0001–16.67621 |

原始 sample 的第一個球位置為 `[-1, -1, 44.12405, 29.72198, 3.55411]`；
Avery Bradley 同時的位置為 `[1610612738, 202340, 48.30817, 15.47903, 0.0]`。
球以兩個 -1 的 ID 識別，球員以 player ID 追蹤，不依賴陣列先後位置。

原 [Ball.py](https://github.com/linouk23/NBA-Player-Movements/blob/master/Ball.py) 將 component_4
命名為 radius 並用於動畫大小；[第一手資料分析](https://danvatterott.com/creating-videos-of-nba-action-with-sportsvu-data.html)
及原始 API client 的 [Coordinate 定義](https://github.com/bttmly/nba-movement#coordinate)
則解讀為 z。輸出會保留該 raw 值，z 語意記錄為外部格式佐證；S1 僅依 x／y 定位，
不把它用來估算球的物理半徑。

### 單位與方向的確認程度

- JSON 沒有內建單位、場地長寬或座標原點 metadata。
- [使用同源 SportVU 的原始研究](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0281467)
  明述單位為 feet、採樣為 25 Hz。原展示程式也以長度 94、寬度 50 的球場範圍疊圖，
  並多留發球空間。Backend 草案優先保留 feet 原值，標明單位依據而非聲稱是 JSON 欄位。
- nominal 25 Hz 不等於每筆恰隔 40 ms。不要用 frame index × 40 覆蓋實際 timestamp 差。
- source 原點與 y 軸對應畫面的方向，仍須在正式採用後用場地與片段核對。
  不沿用舊草案的「已確認左下角」假設，也不自動鏡射成統一進攻方向。
- x／y 可在場外；Backend 保留來源值並標記，不靜默刪除或夾值。

## 沒有確認為來源欄位的資訊

此 JSON 沒有正式 frame ID、逐球員速度／加速度、軌跡物件、持球者、進攻方、守方、傳球事件、
戰術名稱、戰術信心分數或自然語言解釋。軌跡須由相同 player ID 的時間序列建構；
其他項目若後續加入，必須標成衍生計算、規則推論、人工標註或額外資料來源。

公開研究另有動作／事件註解線索，見評估報告；它不改變原始 JSON 本身沒有戰術標籤的事實。
