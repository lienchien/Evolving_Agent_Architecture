# Capability-Evolving Agent — Security Audit Log

## Purpose

`SECURITY_AUDIT_LOG.md` 用於記錄專案**歷次程式碼安全檢測（漏洞／風險掃描）的稽核紀錄**，
供未來稽核追溯「何時查過、查了哪裡、用什麼方法、發現什麼、後續狀態如何」。

與其他文件的角色區分：

- `DEVELOPMENT_LOG.md`：實際開發過程、設計決策與功能驗證證據
- `PROJECT_STATUS.md`：目前所處階段與完成度
- `docs/API_CONCURRENCY.md`：API 行為與併發升級條件
- `docs/SECURITY_AUDIT_LOG.md`（本文件）：安全性檢測紀錄，含已發現風險的持續追蹤狀態

本文件採**持續追加**方式維護，不覆寫或刪除歷史紀錄；風險狀態變更（例如修復完成）
以新增紀錄或更新對應項目的「狀態」欄位表示，並保留變更時間點。

---

# Recording Rules（固定格式，後續每次檢測皆比照本格式記錄）

每次檢測建立一筆新的 `## YYYY-MM-DD — <檢測主題>` 紀錄，並包含以下固定欄位：

- **檢測範圍（Scope）**：本次實際檢視的目錄／檔案／模組，以及排除項目
- **檢測方法（Method）**：如何檢測（人工程式碼審查、依賴掃描、動態測試、git diff review 等），
  以及本次未涵蓋的方法（例如「未執行依賴 CVE 掃描」「非 git diff 比對，因目錄非 git repo」）
- **執行者（Performed By）**：執行檢測的人／助理身分與模型版本
- **基準狀態（Baseline）**：檢測當下的專案版本依據（git commit hash，或若無版本控制則記錄
  檢測當下的檔案快照依據，例如目錄清單或關鍵檔案的最後修改時間）
- **發現摘要（Summary）**：本次發現項目數，依嚴重度（Critical／High／Medium／Low）分類統計
- **詳細發現（Findings）**：逐項記錄，每項固定包含：
  | 欄位 | 說明 |
  |---|---|
  | 編號 | 本次紀錄內的流水號，格式 `<日期>-<序號>`，例如 `2026-09-22-01` |
  | 檔案:行號 | 對應程式碼位置 |
  | 分類 | 例如 sandbox-escape、missing-authn-authz、injection、supply-chain |
  | 嚴重度 | Critical／High／Medium／Low |
  | 描述 | 風險內容一句話說明 |
  | 觸發情境 | 具體會導致問題的輸入／狀態 |
  | 狀態 | Open／Accepted Risk（已知並刻意延後）／Planned（已排入計畫）／Fixed |
  | 對應計畫 | 若非 Fixed，說明排入哪個階段或有無 TODO 標記位置 |
- **已排除項目（Ruled Out）**：本次有specifically檢查但未發現問題的風險類別（例如 SQL injection、
  path traversal），列出以證明稽核涵蓋範圍，而非遺漏
- **本次檢測限制（Caveats）**：本次方法本身的侷限（例如僅靜態審查、未做滲透測試、未涵蓋
  未來才會接入的元件）
- **下次建議觸發時機（Next Trigger）**：什麼情況下應該重新檢測（例如「接入真實 LLM provider
  前」「對外開放服務前」「新增認證機制後」）
- **關聯文件**：本次檢測相關的其他文件連結

---

# Audit History

## 2026-09-22 — Phase 1 現況程式碼安全檢測

### 檢測範圍（Scope）

`src/` 全部原始碼（約 2,500 行，49 個 `.py` 檔），涵蓋 `agents`、`api`、`domain`、
`infrastructure`、`interfaces`、`services`、`config.py`、`main.py`；另檢視 `requirements.txt`。
未涵蓋：`tests/`、`docs/` 內容本身、前端／UI（本專案目前無前端）。

### 檢測方法（Method）

人工原始碼審查，鎖定以下風險面向：程式碼執行／沙盒隔離（`subprocess_sandbox.py`）、
SQL injection（`sqlite_repository.py` 全部查詢語法）、API 認證與授權（`api/routes/*`、
`api/dependencies.py`）、路徑穿越（報告檔案寫入、`capability_id` 產生方式）、
危險函式使用（`eval`／`exec`／`pickle`／`os.system`／`shell=True` 等全庫關鍵字掃描）、
依賴版本鎖定情形（`requirements.txt`）。

未涵蓋：依賴套件已知 CVE 掃描（如 `pip-audit`）、動態滲透測試／模糊測試、
執行期資源耗盡（DoS）壓力測試、`tests/` 測試程式本身的安全性。本目錄非 git repository，
故非 git diff／PR 比對式審查，而是對目前檔案全量狀態的快照式審查。

### 執行者（Performed By）

Claude Code（Sonnet 5, `claude-sonnet-5`），使用者 talent4925@gmail.com 請求執行。

### 基準狀態（Baseline）

無 git 版本控制；以 2026-09-22 16:33 目錄快照為準（`ls -la` 顯示之檔案最後修改時間）。

### 發現摘要（Summary）

共 3 項發現：Critical 1、High 1、Low 1。Medium 0。

### 詳細發現（Findings）

| 編號 | 檔案:行號 | 分類 | 嚴重度 | 描述 | 狀態 | 對應計畫 |
|---|---|---|---|---|---|---|
| 2026-09-22-01 | [subprocess_sandbox.py:47](../src/infrastructure/subprocess_sandbox.py#L47) | sandbox-escape | Critical | 生成的能力程式碼以同一台主機、無隔離的 Python subprocess 執行，僅有逾時限制，無檔案系統／網路／CPU／記憶體隔離 | Accepted Risk | 已在 `PROJECT_STATUS.md`／`DEV_PLAN.md` 記錄為已知限制；排入 Phase 1.5（真實 provider 前）與 Phase 5（gVisor/Firecracker/Kata 強化隔離） |
| 2026-09-22-02 | [tasks.py:29](../src/api/routes/tasks.py#L29) 等（approvals.py、capabilities.py、research.py 同類） | missing-authn-authz | High | 所有 API（任務提交、能力查詢、核准／拒絕、研究指標）無身分驗證與授權；`reviewer` 欄位由呼叫端自填 | Accepted Risk | 程式碼內已有 `TODO(security)` 標記；排入 Phase 1.5「認證、管理員角色與 tenant/owner/scope 資料控制」 |
| 2026-09-22-03 | [requirements.txt:1](../requirements.txt#L1) | supply-chain | Low | 所有依賴僅以 `>=` 下限宣告，無上限或 lockfile，建置結果不可重現 | Open | 尚未排入既有階段計畫；建議後續導入 lockfile（如 `requirements.lock` 或 `uv.lock`） |

### 已排除項目（Ruled Out）

- **SQL Injection**：`sqlite_repository.py` 全部查詢皆使用參數化語法（`?` placeholder），
  未發現字串拼接組 SQL 的情形（僅 `_OPEN_STATUSES` 為程式內固定常數，非外部輸入）。
- **路徑穿越（Path Traversal）**：`capability_id` 由伺服器端 `uuid.uuid4()` 產生
  （`CAP-{uuid4().hex[:8]}`），非使用者可控字串，`testing_service.py` 寫入報告檔案時
  以此為目錄名稱，不受外部輸入影響。
- **危險函式（eval/exec/pickle/os.system/shell=True）**：全庫關鍵字掃描僅命中
  `subprocess_sandbox.py` 的 `subprocess.run`（已列為 Finding 01），無其餘命中。
- **CORS 設定風險**：目前未掛載 `CORSMiddleware`，非公開跨網域 API，無過寬 CORS 設定問題。

### 本次檢測限制（Caveats）

僅為靜態人工審查，非自動化掃描（無 SAST/DAST 工具產出的交叉驗證）；未執行依賴套件的
已知 CVE 掃描；未針對 Mock 元件被置換為真實 LLM／PostgreSQL／Docker adapter 後的行為做評估
（屆時應重新檢測）。

### 下次建議觸發時機（Next Trigger）

- 接入任一真實 LLM provider（LiteLLM／NVIDIA NIM／OpenRouter）之前，重新評估 Finding 01。
- 服務對外（非 localhost／非開發環境）開放之前，重新評估 Finding 02，並確認認證機制已到位。
- 新增或修改任何 SQL 組字串、檔案路徑組合、`subprocess`／`eval`／反序列化相關程式碼時。
- 每次 Phase 邊界（Phase 1.5、Phase 2…）收尾時，作為例行稽核項目。

### 關聯文件

[PROJECT_STATUS.md](../PROJECT_STATUS.md)、[DEV_PLAN.md](../DEV_PLAN.md)、
[DEVELOPMENT_LOG.md](../DEVELOPMENT_LOG.md)
