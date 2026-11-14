# S1 本機球場預覽

2026-11-14：以既有 Backend JSON 0.2.0 匯出建立第一個可操作畫面。
僅供本機小規模驗證，不包含 S2、戰術標籤、持球者推論、LLM 或影片追蹤。
Frontend 組員可以沿用此頁或另選技術，Backend 資料介面未變更。

## 檔案與介面

| 檔案 | 用途 |
| --- | --- |
| `frontend/index.html` | 頁面與可鍵盤操作的控制項 |
| `frontend/styles.css` | 桌面與窄螢幕排版 |
| `frontend/app.mjs` | JSON 載入、Canvas 繪圖、播放與球員選取 |
| `frontend/model.mjs` | 規格檢查、依時間取影格、軌跡分段與座標映射 |
| `src/basketball_tactics/preview.py` | 只監聽 127.0.0.1 的本機靜態服務 |
| `tests/test_preview.py` | 真實匯出 HTTP 路由、HEAD、Host 與路徑限制測試 |
| `tests/test_viewer_model.mjs` | 真實片段與明確故障注入的資料邏輯測試 |

服務只提供 `/`、三個前端資產、`/data/manifest.json` 與 manifest 列出的
`/data/clips/*.json`。不提供原始比賽檔、資料夾列表、`.env` 或 Git 內容。
啟動前檢查每個資產不超過 10 MiB，片段路徑不得離開指定資料夾。
這是本機開發工具，沒有正式 API、帳號、寫入功能或遠端存取設定。

## 啟動

在 repository 根目錄完成 README 的 Python 環境安裝。先依 [Backend 文件](backend-s1.md)
產生 `outputs/s1-event-2/manifest.json` 與 clips；缺少真實資料時不產生替代畫面。
raw 與衍生輸出不進 Git，另一台電腦需自行取得允許使用的單場資料並執行匯出。

```powershell
.\.venv\Scripts\python.exe -m basketball_tactics.preview --data-dir outputs/s1-event-2
```

```bash
.venv/bin/python -m basketball_tactics.preview --data-dir outputs/s1-event-2
```

用瀏覽器開啟終端機顯示的 `http://127.0.0.1:8000/`，保留終端機，Ctrl+C 停止。
若 port 已被使用，另加 `--port 8001`，再開啟對應網址。
修改 HTML／CSS／JS 後重新整理瀏覽器；修改 Python 服務或匯出清單後重啟服務。
直接雙擊 HTML 不支援此載入方式。預覽不需要 Node.js、npm 或額外 Python 套件。

## 操作與資料意義

- 播放／暫停、時間拖曳、回到開頭、前後一格、0.25／0.5／1／2 倍速；片尾自動停止。
- 軌跡可隱藏或顯示最近 1／3／5 秒、完整片段；選球員名單或球場上的點可聚焦球員。
- 資料觀測可展開警告，點擊有本片段 frame_index 的項目可跳到該影格。
- 時間控制採 `t_ms`，取不晚於游標時間的最近影格；不插值、不強制固定 40 ms。
  game clock 與 shot clock 另行顯示，不作播放時間軸。切至背景分頁會暫停。
- 軌跡使用 Backend 的 segments，不跨缺漏或 break_before 連線；倒回時不保留未來點。
  缺球時不繪球，球員缺席時不繪該點，名單標示此影格缺少位置。
- 畫面保持 94:50 來源場地比例與 feet 數值，周圍留 6 ft；場外點不夾回界內。
  超出留白的點可能在畫布外，仍可從名單數值與警告查閱。
- 預設以來源 x 向右、y 向下檢視；上下翻轉只改畫面，不修改 JSON。
  來源方向仍未確認，不以所在半場推斷攻守、持球者或完整進攻回合。
- 球場線條依 [NBA 場地規則](https://official.nba.com/rule-no-1-court-dimensions-equipment/)
  畫參考幾何；不是從影片校正得到。球的位置只畫 2D，未用 z 模擬球的大小或高度。
  球衣號碼、球員身分與隊伍取自 Backend，顏色固定依 teams 順序。

## 測試與重現

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
node --test tests/test_viewer_model.mjs
```

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m pip check
node --test tests/test_viewer_model.mjs
```

JS 測試需 Node.js 22+，本次使用 24.19.0。`SPORTVU_EXPORT` 可指定同一 event 2 匯出的
其他目錄，`SPORTVU_SAMPLE` 指定原始單場。未設定且本機沒有 sample／匯出時，對應案例
明確 skip；明確設定卻缺檔或格式不符則失敗。沒有將 raw fixture 或完整輸出提交 Git。

本次 Windows 結果：Python **37 passed**（含原有 28 案例），JS **7 passed**，無 skip；
`pip check` 通過。JS 逐一檢查全部 524 個非固定間隔邊界，並驗證視窗軌跡、缺漏中斷、
錯誤版本／路徑、異常值、負座標及畫面翻轉；故障注入使用真實事件複本，未作展示資料。

驗證片段為 2015-12-30 LAL @ BOS，原始 eventId="2"，525 影格、20,959 ms、10 人與球。
39／40／41 ms 間隔原樣使用，24 筆負 x 警告原樣呈現。畫面影格編號從 1 開始，
Backend 的 frame_index 從 0 開始，例如畫面「影格 393」對應 frame_index=392。

瀏覽器人工操作已確認：逐格、時間滑桿、播放／暫停與片尾停止、球員名單選取、速度與
軌跡選單、軌跡開關、上下翻轉、警告跳至影格 393。暫停後時間保持不動，名單顯示
Larry Nance Jr. 的 x=-0.2 ft，而非夾回 0。1440×1000 桌面與 375×812 窄螢幕已檢查，
窄螢幕沒有水平溢出；測試時瀏覽器未記錄 JS error／warning。
本機畫面紀錄在 `outputs/viewer-qa/s1-preview.jpg`，不提交 Git。

尚待雙人共同驗收：與來源畫面核對座標方向、課堂展示範圍與授權，以及實驗室電腦／macOS
實機重建。單片段測試不等於所有比賽都已驗證；多片段切換介面已支援，但尚無多片段真實
匯出作瀏覽器驗收。正式 Frontend 技術、分享方式與部署仍待組員確認。
