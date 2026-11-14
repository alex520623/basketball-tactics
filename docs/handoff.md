# 換電腦交接指南

這份指南用來在另一台 Windows 或 macOS 電腦接續 S1 開發。
程式從 GitHub 取得；比賽原檔另外準備；Python 環境在新電腦重新建立。

## 先取得正確版本

目前整合版本在 **`handoff/s1-development`**，包含球場回放與整場多事件驗證。
`main` 尚未包含這些功能。交接分支整合以下兩份工作，沒有將它們合併至 main：

| 工作 | 原分支／PR | 整合基準 |
| --- | --- | --- |
| 球場回放與文件修正 | `feat/s1-local-viewer`，[PR #3](https://github.com/alex520623/basketball-tactics/pull/3) | `df80b8e` |
| 全場多事件驗證 | `test/s1-multi-event-validation`，[PR #5](https://github.com/alex520623/basketball-tactics/pull/5) | `3b8bd9c` |

先檢查新電腦是否有 Git 與 Python 3.12：

```powershell
# Windows
git --version
py -3.12 --version
```

```bash
# macOS
git --version
python3.12 --version
```

找不到命令時先完成安裝。此 repository 為 Private，clone 時須使用有存取權限的 GitHub 帳號。
若已安裝 GitHub CLI，可先執行 `gh auth login --hostname github.com --git-protocol https --web`。
GitHub 登入須由本人在新電腦完成，不複製原電腦的憑證。

第一次取得專案：

```bash
git clone --branch handoff/s1-development https://github.com/alex520623/basketball-tactics.git
cd basketball-tactics
git status --short --branch
```

已經 clone 過時，先用 `git status` 確認有沒有未提交修改，保留自己的工作再切分支。
執行 `git fetch origin` 後，首次取得交接分支用
`git switch --track origin/handoff/s1-development`；已存在則用 `git switch handoff/s1-development`，
再執行 `git pull --ff-only`。確認目前分支名稱正確，才繼續安裝。

## 準備這一場比賽

只需要 **2015-12-30 湖人對塞爾提克**，檔名 `0021500476.json`，約 103 MB。
可使用原電腦準備的私人移轉 ZIP，或依 [資料準備](../data/README.md) 取得同一單場原檔。
移轉 ZIP 只包含原始 JSON 與簡短說明，程式仍由 GitHub 取得。

將 ZIP 複製到新電腦，解壓至剛 clone 的專案根目錄，應得到：

```text
basketball-tactics/
└── data/raw/0021500476.json
```

不要複製舊 `.venv`、Python 安裝目錄、整個 `.tools` 或整份工作目錄。
已有同名原檔時先核對 SHA-256，不要直接覆蓋：

```powershell
# Windows
Get-FileHash data/raw/0021500476.json -Algorithm SHA256
```

```bash
# macOS
shasum -a 256 data/raw/0021500476.json
```

預期值：

```text
5ad649c3b741cc45c01c586cbf073d56d67da0f2315fe7acedb477bc43116036
```

資料使用範圍維持 [資料準備文件](../data/README.md#使用範圍) 的限制，原檔與移轉包不放進 GitHub。

## Windows 安裝、匯出與測試

以下命令都在專案根目錄執行。若已有 `.venv`，先確認其 Python 為 3.12，不直接重建覆蓋。

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check

.\.venv\Scripts\python.exe -m basketball_tactics.cli `
  --input data/raw/0021500476.json `
  --event-id 2 `
  --output-dir outputs/s1-event-2 `
  --gap-threshold-ms 120 `
  --source-commit f7d4cf2c7e607029abfd5715a0d4073bedae328e `
  --expected-sha256 5ad649c3b741cc45c01c586cbf073d56d67da0f2315fe7acedb477bc43116036

$env:SPORTVU_SAMPLE = (Resolve-Path data/raw/0021500476.json).Path
$env:SPORTVU_EXPORT = (Resolve-Path outputs/s1-event-2).Path
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m basketball_tactics.preview --data-dir outputs/s1-event-2
```

## macOS 安裝、匯出與測試

以下命令都在專案根目錄執行。若已有 `.venv`，先確認其 Python 為 3.12，不直接重建覆蓋。

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check

.venv/bin/python -m basketball_tactics.cli \
  --input data/raw/0021500476.json \
  --event-id 2 \
  --output-dir outputs/s1-event-2 \
  --gap-threshold-ms 120 \
  --source-commit f7d4cf2c7e607029abfd5715a0d4073bedae328e \
  --expected-sha256 5ad649c3b741cc45c01c586cbf073d56d67da0f2315fe7acedb477bc43116036

export SPORTVU_SAMPLE="$(pwd)/data/raw/0021500476.json"
export SPORTVU_EXPORT="$(pwd)/outputs/s1-event-2"
.venv/bin/python -m pytest -q
.venv/bin/python -m basketball_tactics.preview --data-dir outputs/s1-event-2
```

若輸出目錄已存在，可直接使用該匯出，略過 CLI 命令；需要重新產生時請用新目錄名稱，
並同步調整 `SPORTVU_EXPORT` 與 preview 的 `--data-dir`。程式不覆蓋既有輸出。

服務啟動後，在該電腦瀏覽器開啟 `http://127.0.0.1:8000/`。保留終端機，Ctrl+C 停止。
若 8000 port 被使用，另加 `--port 8001`，並開啟對應網址。
Node.js 不是執行回放的必要條件；若已安裝 Node.js 22+，可另外執行 JS 測試：

```bash
node --test tests/test_viewer_model.mjs
```

## 接手時應看到的結果

- 2026-11-14 原 Windows 環境：Python **52 passed**、JavaScript **7 passed**，無 skip；pip check 通過。
- eventId="2" 匯出：525 影格、20,959 ms、10 名球員與球；有 24 筆場外位置警告。
- 整場驗證：489 個事件，482 個可轉換、5 個空事件、2 個 timestamp 衝突事件被拒絕。
- 看到 `skipped` 時，先檢查資料檔與環境變數路徑。明確指定的檔案不存在或 hash 不符會失敗。
- 另一台電腦與 macOS 尚待實際執行，不應把原電腦結果當成新電腦已通過。

下一步先核對新電腦的回放與測試結果，再用 event 29、80、265 檢查缺球、缺球員與空時鐘。
這三份匯出可依 [多事件驗證文件](multi-event-validation.md) 重新產生。
S2、S3、LLM 與其他比賽的下載尚未開始。

## 後續修改與切換電腦

這次交接先從整合分支接續，新增工作使用自己的分支：

```bash
git switch -c feat/你的工作名稱
```

每位開發者在 repository 內設定自己的 Git 姓名與驗證過的 email；只使用 `git config --local`。
切換電腦前，將程式變更 commit 並 push；資料與輸出留在各自電腦。
另一台電腦先確認工作目錄乾淨，再 fetch、切換同一工作分支並 `git pull --ff-only`。
從交接分支開始的修改，PR 先以 `handoff/s1-development` 為目標，讓審閱只包含新增的變更。
PR #3 與 #5 完成審閱並合併 main 後，再同步 main 並調整後續 PR 的目標。
合併 main 前透過 PR 審閱，不直接將交接分支或功能分支合併至 main。
