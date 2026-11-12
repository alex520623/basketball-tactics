# 籃球戰術分析系統

MM 課程專案，透過籃球追蹤資料分析球員移動與戰術，並以視覺化呈現分析結果。

目前已完成 Python 開發環境與專案結構，功能開發尚未開始。資料集沿用原先選定方案，
名稱、來源與版本待確認後補入 [資料說明](data/README.md)。

## 開發階段

| 階段 | 內容 | 狀態 |
| --- | --- | --- |
| S1 | 追蹤資料整理、2D 球場與球員軌跡視覺化 | 待資料集確認 |
| S2 | 球員時空關係、移動模式與基礎戰術分析 | 尚未開發 |
| S3 | 串接 LLM，產生有資料依據的戰術解釋 | 尚未開發 |

分工分為資料處理與戰術分析，以及視覺化與互動介面。

## 專案結構

```text
basketball-tactics/
├── data/
│   ├── README.md            # 資料來源與取得方式
│   ├── raw/                 # 原始資料
│   └── processed/           # 處理後資料
├── outputs/                 # 圖表與分析輸出
├── src/basketball_tactics/   # Python 程式
├── tests/                   # 環境測試
├── .vscode/                 # 編輯器設定
├── .python-version
├── pyproject.toml
└── requirements.txt
```

資料集與輸出檔案保留在各自的電腦，不提交 Git。資料取得方式與欄位定義記錄在
`data/README.md`，供組員建立相同的資料環境。

## 環境安裝

需要 Git 與 Python **3.12.x**。主要套件為 NumPy、pandas 與 pytest，版本由
`requirements.txt` 指定；建置設定見 `pyproject.toml`。間接依賴尚未完整鎖定。

此 repository 為 Private，組員須先接受協作邀請。首次 clone 時，依 Git 的提示登入
有存取權限的 GitHub 帳號。若使用 GitHub CLI，可先執行：

```bash
gh auth login --hostname github.com --git-protocol https --web
```

### Windows（PowerShell）

```powershell
git clone https://github.com/alex520623/basketball-tactics.git
cd basketball-tactics
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest
```

若沒有 `py`，可在確認 `python --version` 為 3.12 後，改用 `python -m venv .venv`。

已安裝 uv 時，也可使用專案內的 Python 建立環境，再執行上述 pip 與 pytest 命令：

```powershell
uv python install 3.12 --install-dir .tools/python --no-bin --no-registry --cache-dir .uv-cache
$projectPython = Get-ChildItem .tools/python -Filter python.exe -Recurse | Select-Object -First 1 -ExpandProperty FullName
& $projectPython -m venv .venv
```

### macOS（Terminal）

先安裝符合電腦架構的 Python 3.12，再執行：

```bash
git clone https://github.com/alex520623/basketball-tactics.git
cd basketball-tactics
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
.venv/bin/python -m pytest
```

每台電腦各自建立 `.venv`。目前 Windows 環境已驗證，macOS 尚待實機驗證。
現有 4 個測試檢查 Python 版本、虛擬環境、套件匯入與 NumPy/pandas 相容性。

### VS Code

開啟 `basketball-tactics` 資料夾，安裝 Python 與 Pylance 擴充套件，透過
**Python: Select Interpreter** 選擇 `.venv` 的 Python。測試可由 Testing 面板執行。

## 合作流程

每台電腦在 clone 後設定自己的提交者資訊，填入實際名稱與 GitHub 驗證過的 email
（或 noreply email）：

```bash
git config --local user.name "YOUR NAME"
git config --local user.email "YOUR EMAIL"
```

`main` 保留可執行的版本，各項工作使用獨立分支。例如：

- `feat/data-loading`：資料讀取與處理。
- `feat/trajectory-view`：球員軌跡視覺化。
- `fix/...`：錯誤修正。
- `docs/...`：文件更新。

開始工作前同步 `main`，再建立自己的分支：

```bash
git switch main
git pull --ff-only origin main
git switch -c feat/data-loading
```

完成修改後執行測試，使用 `git add` 加入相關檔案，以 `git diff --cached` 檢查內容，
再 commit 並執行 `git push -u origin HEAD`。透過 Pull Request 說明變更與測試結果，
由另一位組員審閱後合併。

切換電腦前，先將工作分支 commit 並 push。另一台電腦確認工作目錄乾淨後，執行
`git fetch origin`，切換到同一分支，再以 `git pull --ff-only` 同步。若為首次取得分支，
可使用 `git switch --track origin/實際分支名`。

`.venv`、`.env`、原始資料、快取及輸出均由 `.gitignore` 排除。提交前仍須檢查程式與文件
是否含有 API Key 或其他憑證；10 MiB 以上檔案先確認儲存方式，再決定是否納入版本管理。
