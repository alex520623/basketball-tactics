# 籃球戰術分析系統（basketball-tactics）

MM 課程兩人專案。目前只有開發環境與版本管理骨架，尚未實作產品功能。

## 範圍與分工

| 階段 | 預定內容 | 目前狀態 |
| --- | --- | --- |
| S1 | 既有籃球追蹤資料、2D 球場、球員軌跡視覺化 | 待資料集確認，未開發 |
| S2 | 球員時空關係、移動模式及基礎戰術分析 | 未開發 |
| S3 | 串接 LLM，產生有資料依據的戰術解釋 | 未開發 |

主要分工：一位負責資料處理與戰術分析；另一位負責視覺化與互動介面。
資料集沿用原先選定方案，待確認後記錄在 [data/README.md](data/README.md)。
目前沒有下載資料、選擇視覺化框架或設定任何 LLM/API Key。

## 專案結構

```text
basketball-tactics/
├── data/
│   ├── README.md
│   ├── raw/                 # 本機原始資料，不進 Git
│   └── processed/           # 本機中間資料，不進 Git
├── outputs/                 # 本機輸出，不進 Git
├── src/basketball_tactics/   # Python 套件骨架
├── tests/                   # 環境 smoke tests
├── .vscode/                 # 專案層級的 Python/pytest 建議
├── .python-version          # Python 3.12
├── pyproject.toml           # 套件安裝與 pytest 設定
├── requirements.txt         # 最少直接依賴與 editable 安裝
└── README.md
```

初期套件只有 NumPy 2.3.4、pandas 2.3.3、pytest 8.4.2，以及本專案的 editable
安裝。建置使用 setuptools 80.9.0。直接依賴版本固定；間接依賴尚未完整鎖定，
不同平台或日期的解析結果可能不同，不能視為逐位元相同的環境。

## 每台電腦的前置準備

1. 安裝 Git、Python **3.12.x**（含 pip 與 venv）及 VS Code。
2. 要建立 GitHub repository 或用 CLI 登入，另外安裝 GitHub CLI（`gh`）。
3. VS Code 安裝 Microsoft Python 與 Pylance 擴充套件。
4. 私人 repository 須由有權限的帳號登入；另一位組員需先接受 collaborator 邀請。

Python 請用 [官方下載](https://www.python.org/downloads/)，或使用已安裝的 uv。
Git 與 GitHub CLI 分別見 [Git](https://git-scm.com/downloads) 與
[GitHub CLI](https://cli.github.com/)。不需要把 `.venv` 或 Python 安裝目錄同步到 Git。

## Windows 11：clone 後重建（PowerShell）

將下方 `OWNER` 換成實際 GitHub repository 擁有者；遠端尚未建立時不能 clone。

```powershell
git clone https://github.com/OWNER/basketball-tactics.git
cd basketball-tactics
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest
```

如果沒有 `py`，但 `python --version` 確認是 3.12，可改用 `python -m venv .venv`。
上述命令直接指定虛擬環境的 Python，因此不需要更改 PowerShell 執行原則或啟用腳本。

若已安裝 uv，且要完全使用專案內的 Python（本次 ASUS 筆電採此方式）：

```powershell
uv python install 3.12 --install-dir .tools/python --no-bin --no-registry --cache-dir .uv-cache
$projectPython = Get-ChildItem .tools/python -Filter python.exe -Recurse | Select-Object -First 1 -ExpandProperty FullName
& $projectPython -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest
```

`.tools/`、`.uv-cache/` 和 `.venv/` 都只保留在本機。每個 clone 各自建立一次環境；
不要把其他電腦的虛擬環境複製過來。已有 `.venv` 時先確認用途，不要直接刪除或覆蓋。

## macOS：clone 後重建（Terminal，含 Apple Silicon）

先安裝適合該 Mac 架構的 Python 3.12；不要依賴系統內建的 Python。

```bash
git clone https://github.com/OWNER/basketball-tactics.git
cd basketball-tactics
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
.venv/bin/python -m pytest
```

兩個平台執行 `pytest` 都應有 **4 個測試通過**。測試僅確認 Python 版本、虛擬環境、
本機套件匯入及 NumPy/pandas 相容性，沒有籃球分析功能或真實資料依賴。
本次只有 Windows 可供實測；macOS 步驟需在 Mac 上實際驗證。

## VS Code

用「Open Folder」開啟 **basketball-tactics 這個子資料夾**，或在該目錄執行 `code .`。
執行「Python: Select Interpreter」，選擇本專案 `.venv` 的 Python；Windows 是
`.venv/Scripts/python.exe`，macOS 是 `.venv/bin/python`。若原本已有選擇，請手動重選。
Testing 面板可探索並執行 `tests/`。不需要更改 VS Code 全域設定。

## 初次 Git 身分與 GitHub 同步

Git 提交身分與 GitHub 登入是兩件事。請填自己的顯示名稱及 email，僅設於此 repository：

```bash
git config --local user.name "YOUR NAME"
git config --local user.email "YOUR VERIFIED OR NOREPLY EMAIL"
git config --local --get user.name
git config --local --get user.email
```

email 可使用 GitHub Settings → Emails 提供的 noreply 地址；不要猜帳號或地址。
若這個 clone 已有 `.git`，不要再次 `git init`。初始 repository 的 `main` 已由初始化建立。

GitHub CLI 尚未安裝時，請先依官方安裝方式安裝；Windows 亦可自行執行
`winget install --id GitHub.cli --exact`，安裝後重開 Terminal。這是使用者自行安裝步驟，
本專案不會自動更動全域系統設定。

登入需本人在自己的 Terminal 完成，不要把 token、密碼或裝置驗證碼貼進程式或聊天：

```bash
gh auth login --hostname github.com --git-protocol https --web
gh auth status --hostname github.com
gh api user --jq .login
```

確認目前登入的是預期帳號。以下命令由初始化者執行**一次**，不要在每台 clone 上重跑。
若遠端已存在，先確認其擁有者、內容及 private 狀態，再連接；不要覆寫既有 repository。

### 提交與上傳前檢查

先從專案根目錄執行：

```bash
git status --short --untracked-files=all
git check-ignore .venv/check .env .env.local .tools/check data/raw/check.csv data/processed/check.csv outputs/check.png
git add .gitignore .gitattributes .python-version .vscode README.md requirements.txt pyproject.toml src tests data outputs
git diff --cached --check
git diff --cached --stat
git diff --cached
```

逐一查看暫存檔案，確認只有專案程式與文件。API Key 寫在 `.py` 或文件裡仍可能被上傳；
`.gitignore` 不會自動偵測內容，也不會移除已追蹤檔案。不要使用 `git add -f` 加入資料或密鑰。
本專案採 **10 MiB** 的人工審查門檻；超過門檻先停止上傳並決定外部儲存方式。

Windows 檢查暫存檔案大小（輸出應為空）：

```powershell
git diff --cached --name-only | ForEach-Object {
    $item = Get-Item -LiteralPath $_
    if ($item.Length -ge 10MB) { $item | Select-Object FullName, Length }
}
```

macOS 檢查暫存檔案大小（輸出應為空）：

```bash
git diff --cached --name-only -z | while IFS= read -r -d '' file; do
  if [ "$(stat -f%z "$file")" -ge 10485760 ]; then printf '%s\n' "$file"; fi
done
```

確認 Git 身分、測試、差異與敏感資訊檢查均完成後，才建立初始 commit：

```bash
git commit -m "chore: initialize basketball tactics project"
```

只有在尚無遠端 repository 時才建立 private repository（建立與推送刻意分開，先驗證隱私）：

```bash
gh repo create basketball-tactics --private --source=. --remote=origin
gh repo view --json nameWithOwner,url,isPrivate
git remote -v
```

確認 `isPrivate` 為 `true`、擁有者正確且本機待推送內容已檢查，再執行：

```bash
git push -u origin main
gh repo view --json url,isPrivate
git status --short --branch
```

若已建立空的遠端 repository，使用實際 URL 執行
`git remote add origin https://github.com/OWNER/basketball-tactics.git`，不要重複建立。
若遠端不是空的，先 fetch 並檢查歷史；不要 force push 或盲目合併。
初始化完成後，repo 擁有者到 GitHub Settings → Collaborators 邀請另一位組員。
若帳號方案可用，為 `main` 設定 PR 與審核規則；否則以兩人約定遵守以下流程。

## 兩人合作與多台電腦

保留單一穩定 `main`，不另建長期 `develop`。除了第一次初始化，兩人都在短期分支開發：

- 資料／分析：`feat/data-<topic>`、`feat/analysis-<topic>`。
- 視覺化／介面：`feat/viz-<topic>`、`feat/ui-<topic>`。
- 修正與文件：`fix/<topic>`、`docs/<topic>`。

每項工作先同步 main，再建分支；分支以功能命名，避免兩人共用同一工作分支。

```bash
git switch main
git pull --ff-only origin main
git switch -c feat/data-<topic>
# 編輯、執行 pytest，檢查差異，僅加入相關檔案
git add <specific-files>
git diff --cached
git commit -m "feat: describe the change"
git push -u origin HEAD
```

以上 `<topic>`、`<specific-files>` 都是需替換的說明文字，請勿原樣執行。
在 GitHub 建立 Pull Request，附測試結果，由另一位組員審閱後合併至 `main`。
共同修改套件需求或資料欄位前先溝通；新的環境依賴也要更新文件。

切換到實驗室電腦或 Mac 前，先在目前工作分支 commit／push；私人 repository 同樣不要推送密鑰。
到另一台電腦，先確認 `git status` 沒有尚未處理的變更，執行 `git fetch origin`，再切到該分支
（首次可用 `git switch --track origin/實際分支名`），以 `git pull --ff-only` 同步。
有衝突或 pull 失敗就先處理，不要 force push。每台電腦各有自己的 Git 身分、登入與 `.venv`。

## 官方操作參考

- [Python venv](https://docs.python.org/3.12/library/venv.html)：虛擬環境應在各台電腦重建。
- [GitHub CLI 登入](https://cli.github.com/manual/gh_auth_login)。
- [GitHub CLI 建立 repository](https://cli.github.com/manual/gh_repo_create)。
