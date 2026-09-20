# Capability-Evolving Agent — Development Log

## Purpose

`DEVELOPMENT_LOG.md` 用於記錄專案的**實際開發過程、設計決策、實作內容與驗證證據**。

與其他文件的角色區分：

- `Capability-Evolving Agent Architecture — System Design v1.6.md`：長期系統架構與設計原則
- `Capability_Evolving_Agent_Tech_Stack_v1.md`：技術棧與分階段導入規劃
- `DEV_PLAN.md`：目前開發方案與下一步
- `PROJECT_STATUS.md`：目前所處階段與完成度
- `DEVELOPMENT_LOG.md`：實際做了什麼、為什麼這樣做、修改了什麼，以及是否真的驗證成功

本文件採**持續追加**方式維護。

---

# Recording Rules

每筆紀錄應盡量包含：

- 日期
- Phase
- 目標
- 背景 / 原因
- 實作內容
- 技術決策
- 修改檔案
- 驗證狀態
- 問題與限制
- 對後續架構的影響
- 下一步
- 關聯 Commit / 文件

特別注意：

> **Implementation 與 Validation 必須分開記錄。**

例如：

- `Implemented` = 程式碼已建立
- `Test Written` = 測試程式已撰寫
- `Executed` = 已實際執行
- `Verified` = 已有成功結果與證據

截至 2026-09-18，核心、API 與併發測試已 Executed / Verified（25 passed）。
下列歷史紀錄保留當時狀態；最新進度見本文件末尾及 `PROJECT_STATUS.md`。

---

# Development History

## 2026-09-16 — Phase 1 MVP 架構骨架建立

### Phase

Phase 1 — Core MVP Skeleton Implementation

### 目標

建立 Capability-Evolving Agent 的第一版程式骨架，使核心生命週期在程式結構上有完整對應：

```text
Gap
→ Generate
→ Validate
→ Test
→ Report
→ Notify
→ Approve
→ Activate
→ Reuse
```

此階段目標是建立可供後續執行與驗證的 implementation skeleton，**不是宣稱上述閉環已經跑通**。

### 背景 / 原因

若研究初期直接同時整合 PostgreSQL、Docker、NVIDIA NIM、OpenRouter、LiteLLM 等正式 infrastructure，出現問題時很難判斷問題來自：

- Capability-Evolving Architecture
- Agent orchestration
- 外部 API
- Database
- Sandbox
- 環境配置

因此採用：

> **Implement Simple, Interface for Complex**

先建立 mock / in-memory / SQLite / subprocess 版本的骨架，再逐步取得 runtime evidence。

### 實作內容

建立主要分層：

```text
src/
├── agents/
├── api/
├── domain/
├── infrastructure/
├── interfaces/
├── services/
├── config.py
└── main.py
```

#### Agent Layer

已建立程式碼：

- `MainAgent`
- `EvolutionAgent`

預期 Main Agent flow：

```text
Task
→ Search Capability
→ Existing Capability?
    ├─ Yes → Execute
    └─ No  → Detect Gap → Evolution
```

預期 Evolution Agent flow：

```text
Generate
→ Validate
→ Test
→ Approval Request
```

以上流程目前只有 code-level implementation，尚未實際執行。

#### Domain Layer

已建立：

- Capability
- CapabilityGap
- TestReport
- ApprovalRecord
- Event definitions

Capability Schema 已預留：

- Version
- Lifecycle
- Tenant / Owner / Organization
- Scope
- Sharing Policy
- Validation requirements
- Safety requirements
- Trust level

#### Interface Layer

已建立：

- `LLMProvider`
- `QueueInterface`
- `SandboxInterface`
- `NotificationProvider`
- `CapabilityRepository`

設計目的為讓 Agent / Service 不直接依賴具體 infrastructure。

#### Infrastructure Layer

已建立替代實作：

- `MockLLMProvider`
- `InMemoryEvolutionQueue`
- `SqliteCapabilityRepository`
- `SubprocessSandbox`
- `ConsoleNotificationProvider`

目前僅代表 adapter code 已存在，尚未 runtime 驗證。

#### Service Layer

已建立：

- CapabilityService
- GapDetectionService
- EvolutionService
- ValidationService
- TestingService
- PolicyService
- ApprovalService
- NotificationService
- CapabilityExecutionService
- TestReportStore
- AuditService

#### API Layer

已建立 FastAPI route code：

- `POST /api/tasks`
- Capability query endpoints
- Evolution Queue endpoint
- Approval endpoints
- Audit endpoint

FastAPI server 尚未實際啟動。

### 測試程式

已撰寫：

```text
tests/test_capability_schema.py
tests/test_capability_service.py
tests/test_full_loop.py
```

`test_full_loop.py` 的預期情境為：

```text
Unknown Task
→ Gap
→ Generate Capability
→ Validate
→ Test
→ Pending Approval
→ Approve
→ Active
→ Reuse
```

但目前這只是**測試程式所描述的預期行為**，並不是已經取得的測試結果。

### 重要技術決策

#### 1. LangGraph 只作 Orchestration

Business Logic 放在 Service Layer，以降低 framework coupling。

#### 2. SQLite 先取代 PostgreSQL

先降低 Phase 1 的 infrastructure complexity，後續透過 repository interface 替換。

#### 3. Mock LLM 先取代真實 LLM

先降低模型不確定性；目前也尚未實際執行 Mock Provider flow。

#### 4. Subprocess 先取代 Docker Sandbox

只作為第一輪 execution-path 驗證工具，不視為正式安全邊界。

#### 5. Human Approval 從研究階段開始保留

新 Capability 預期生命週期：

```text
Generated
→ Validated
→ Tested
→ Test Report
→ Pending Approval
→ Administrator Approval
→ Active
```

### 驗證狀態

截至目前：

```text
Architecture / design       Available
Program skeleton            Implemented
Test code                   Written
pytest                      NOT executed
FastAPI runtime             NOT started
Full end-to-end loop        NOT verified
Generated capability run    NOT verified
Test report generation      NOT verified
Approval / activation       NOT verified
Reuse                       NOT verified
Real LLM                    NOT integrated
PostgreSQL                  NOT integrated
Docker Sandbox              NOT integrated
```

目前正式狀態：

> **Phase 1 Skeleton Implemented / Runtime Validation Pending**

### 問題與限制

1. Mock LLM 尚未實際執行，因此目前不能證明 generation flow 正常。
2. Subprocess sandbox 尚未實測 Windows path / encoding / execution behavior。
3. SQLite persistence 尚未實測。
4. LangGraph API compatibility 尚未確認。
5. Full-loop test 尚未執行。
6. Testing Agent 目前仍是基礎骨架，尚未進入完整 adversarial / generalization testing。

### 對後續架構的影響

目前的**設計方向**決定繼續採用：

```text
Agent
→ Service
→ Interface
→ Infrastructure Adapter
```

但這個邊界是否能在實際 runtime 中順利工作，仍需 Phase 1 validation 驗證。

### 下一步

先完成：

> **First Verified End-to-End Run**

再考慮進入 Phase 1.5。

---

## 2026-09-16 — Capability 自主測試、Test Report 與人工治理納入核心設計

### Phase

Phase 1 — Governance Skeleton

### 目標

將 Capability Evolution 的設計從：

```text
Generate → Validate → Store
```

改成：

```text
Generate
→ Validate
→ Autonomous Test
→ Test Report
→ Notify
→ Human Approval
→ Activate
```

### 背景 / 原因

如果 Agent 能自行建立能力，卻沒有獨立測試與人工治理，未來研究與正式產品都缺乏：

- 可稽核性
- 可靠性
- 人類控制
- 回溯依據

因此 Testing、Report、Notification、Approval 被提升為核心生命週期元件。

### 實作狀態

目前已建立對應 service / model / route skeleton，但尚未執行 runtime validation。

因此這一項目前是：

> **Governance flow implemented at code level, not yet verified.**

### 技術決策

- Testing 與 Evolution 職責分離
- Test Report 應永久保存並綁定 Capability Version
- Notification 只負責通知，不具有 activation 權限
- Approval Service 才能改變 Capability lifecycle

### 下一步

第一輪 runtime validation 必須確認：

- Test Report 是否真的產生
- notification 是否真的送出
- approval 是否真的改變狀態
- audit 是否真的留下紀錄

---

## 2026-09-16 — Capability Sharing / Import / Marketplace 架構預留

### Phase

Future Productization — Reserved Architecture

### 目標

保留未來商品化後：

- 上傳 Capability
- 選擇是否分享 Capability
- 搜尋其他人的 Capability
- 下載外部 Capability
- 將外部 Capability 加入自己的 Agent

的架構空間。

### 目前決策

此區塊目前定義為：

> **Future Reserved Development**

Phase 1 不實作：

- Import
- Export
- Publish
- Discover
- Sync
- Marketplace

只保留 schema / interface extension point。

### 核心安全原則

未來任何外部 Capability 都必須視為 Untrusted，不能因為其他使用者已有測試報告就直接啟用。

預期流程：

```text
Import
→ Compatibility Check
→ Local Validation
→ Local Testing
→ Test Report
→ Administrator Approval
→ Active
```

分享預設為 opt-in，不自動上傳使用者 Capability。

### 驗證狀態

此區目前只有 architecture reservation，尚未實作、尚未測試。

---

## 2026-09-16 — 專案狀態文件校正

### Phase

Project Governance

### 原因

發現部分文件使用「完成」、「完整循環」等字眼，可能讓人誤以為 Phase 1 已經實際跑通。

實際狀況是：

> **目前只完成 implementation skeleton 與 test code，尚未進行任何 runtime testing。**

### 修正

統一文件用語：

- `Skeleton Implemented`
- `Test Code Written`
- `Runtime Validation Pending`

避免使用：

- `MVP Complete`
- `Full Loop Verified`
- `Phase 1 Complete`

直到實際測試證據存在。

### 下一里程碑

```text
First Verified End-to-End Run
```

只有這個里程碑完成後，才開始 Phase 1.5 Real Infrastructure Integration。

---

## 2026-09-16 — 補上 Testing Failed / Revision Requested 自動迴圈

### Phase

Phase 1 — Governance Skeleton（補完）

### 目標

讓 `README.md` / `README.zh-TW.md` 中畫出的兩條例外生命週期路徑：

```text
Testing → Failed → Evolution Queue
Pending Approval → Revision Requested → Evolution Queue
```

從「文件描述的預期行為」變成「程式碼實際實作的行為」。

### 背景 / 原因

重新檢查專案文件時發現：`src/domain/capability.py` 的 `CapabilityStatus` 當時沒有 `FAILED` 或 `REVISION_REQUESTED` 狀態，`TestingService` 永遠把結果導向 `TESTED`，`ApprovalService.request_revision()` 實際上是轉回 `DRAFT` 而非文件描述的 `Revision Requested`。這是文件與程式碼不一致，且不只是「尚未驗證」，而是「根本沒實作」，違反專案一貫要求的「不要用完成式描述未完成的事」原則。

### 實作內容

- `CapabilityStatus` 新增 `FAILED`、`REVISION_REQUESTED`，並更新 `capability_service.py` 的合法轉換表（`TESTING → {TESTED, FAILED}`、`PENDING_APPROVAL → {APPROVED, ARCHIVED, REVISION_REQUESTED}`，`FAILED`/`REVISION_REQUESTED` 皆可再轉 `ARCHIVED`）。
- `TestingService.run_autonomous_tests()`：以 functional test 是否全部通過作為硬性關卡 —— 全過才進 `TESTED`（走向人工審核），只要有一項沒過就直接判定 `FAILED`，`recommended_action` 改為 `regenerate`。boundary test 失敗仍只記錄在報告中，不影響這個關卡（維持人類自行判斷）。
- `EvolutionAgent`：`test` 節點後改成條件邊，只有狀態為 `TESTED` 才會進入 `finalize`（請求審核）；`FAILED` 直接結束，不會打擾管理員。
- `ApprovalService.request_revision()`：目標狀態由 `DRAFT` 改成 `REVISION_REQUESTED`。
- 沒有新增背景 worker 或額外的 queue 輪詢機制。「回到 Evolution Queue」是透過既有機制自然達成：`FAILED`／`REVISION_REQUESTED` 都不符合 `find_active_by_task_family()` 的查詢條件，所以下一次同 `task_family` 的任務一進來，`GapDetectionService` 就會重新判定為 gap，`MainAgent` 沿用原本的 `queue.enqueue()` → `queue.dequeue()` → `EvolutionAgent.run()` 流程處理，產生一個全新版本的 Capability。

### 修改檔案

```text
src/domain/capability.py
src/services/capability_service.py
src/services/testing_service.py
src/services/approval_service.py
src/agents/evolution_agent.py
src/main.py
tests/support.py（新增，抽出共用 wiring）
tests/test_full_loop.py（改用 tests/support.py）
tests/test_capability_failure_and_revision.py（新增）
```

### 技術決策

- Functional test 失敗 = 硬性關卡（自動判定失敗，不進人工審核）；Boundary test 失敗 = 軟性訊號（仍進 pending_approval，寫進報告讓人判斷）。理由：如果 LLM 生成的程式碼連自己宣稱要滿足的基本功能測試都不過，讓管理員審核沒有意義。
- 不引入新的背景 worker 或顯式的 queue draining 邏輯，改為讓既有的「找不到 ACTIVE capability 就視為 gap」邏輯自然承接重新演化的需求 —— 符合 Phase 1「還沒有背景 worker」的邊界，也避免過度設計。

### 驗證狀態

同樣是 **Implemented，尚未 Executed / Verified**。新增的兩個測試案例（`test_failed_functional_test_marks_capability_failed`、`test_revision_requested_reopens_the_gap`）尚未實際跑過 `pytest`。

### 問題與限制

1. 沿用既有限制：LangGraph 版本相容性、Windows subprocess 行為、SQLite 行為都還沒實測。
2. `FAILED` / `REVISION_REQUESTED` 的舊 Capability 記錄目前只是留著（可轉 `ARCHIVED`），沒有自動清理或封存流程，也沒有 API 路由觸發封存。
3. 沒有實作「重試上限」；理論上如果 Mock/LLM 持續產生錯誤程式碼，每次任務都會產生一筆新的 `FAILED` Capability 記錄，不會停止。Phase 1.5 接上真實 LLM 後應評估是否需要重試次數上限或退避策略。

### 下一步

不變：仍是先取得 **First Verified End-to-End Run**，這次的修改只是讓程式碼行為對齊文件敘述，屬於同一個里程碑範圍內的補完。

---

## 2026-09-17～18 — 首次測試、API feature、資安檢查與併發修復

### Phase / 目標

Phase 1 — 將核心程式從骨架推進至可驗證的 HTTP API，修復併發資料一致性。
分支：`codex/feature-api-integration`，基於 `c71bf0c`；建立時原
`feature/capability-registry` 與 `dev` 同指該提交。本次未合併或修改 main。

### 環境與第一次執行

- 最初只檢查到系統 Python，缺少 pytest/langgraph/httpx；重新檢查確認專案 `.venv`
  已存在，Python 3.14.3、pytest 9.1.1，以及 FastAPI、Pydantic、LangGraph、httpx 可用。
- 測試收集成功取得 6 項；實際執行曾因預設 pytest 暫存目錄存取被拒而出現 setup errors。
- 指定專案內可寫暫存目錄並停用 cache 後得到 `6 passed in 0.87s`。
  此錯誤屬環境權限問題，未以修改產品邏輯解決。

### API 實作

- 建立可注入 container 的 app factory、依賴取得函式及可設定的測試報告目錄。
- 加入 Capability/TestReport response model、status/task_family 篩選、offset/limit 分頁。
- 未知能力核准回 404；不合法狀態及後續的樂觀鎖衝突回 409；政策拒絕回 403。
- 新增 HTTP 整合測試，驗證建立、查詢報告、核准、重用、要求修訂及限制 metadata。
- 修正測試產物寫入專案目錄的副作用，測試使用獨立資料庫與報告目錄。
- 此階段測試結果：9 passed。

### 資安審查與 container 修復

審查發現 request-time lazy container 初始化沒有同步保護；受控雙執行緒測試
重現建立兩個 container、app.state 只保留其中一個，可能遺失另一實例的治理資料。

改由 FastAPI lifespan 在接收請求前初始化；請求只讀取 container。
未執行 startup 的預設 app 回 503，不在請求端重新建立；注入實例保持不變。
加入首次併發、注入保留與未啟動路徑測試後：12 passed。

同時確認匿名核准、caller-controlled reviewer、完整資料暴露、restrictions 未執行、
無配額及一般 subprocess 缺乏隔離等限制。依開發階段決策，本輪保留授權與資料控制
現狀，在 approvals/capabilities/audit/tasks 路由加入 `TODO(security)`，未宣稱安全驗證通過。

### 併發問題重現與修復決策

| 問題 | 修復前證據 | 實作 |
|---|---|---|
| 決策覆蓋 | 受控交錯中 approve/reject 均回 200，archived 被覆蓋成 active | revision 條件更新；失敗 409；核准的最終狀態與限制一次提交 |
| 任務配錯 | CSV 與文字請求從共用 queue 取到彼此的 gap | Phase 1 同步直接執行自己的 gap |
| 重複能力 | 24 同類請求產生 24 能力，全部可啟用 | SQLite 短交易預留 draft；partial unique index 限制每 family 一個 open 能力 |
| 跨實例不一致 | 共用 SQLite 的另一 app 查得到 capability，但 report 404、audit 為空 | 版本化報告、核准、audit 全部持久化到同一 SQLite |

治理資料持久化後，決策狀態、restrictions、ApprovalRecord、Audit 在同一交易提交，
audit 寫入失敗會全部回滾。SQLite 連線也改為明確 close，避免依賴 GC 釋放檔案。
schema 升級保留舊紀錄；若有多個同 family open 能力，明確拒絕啟動而不自動刪除資料。

### 驗證證據

- 實作過程的完整／目標測試依序驗證；最終完整套件為 **25 passed, 1 warning in 6.84s**。
- 命令：`.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider --basetemp=<全新可寫目錄>`。
- 24 同類 HTTP 請求跨兩個 app：一個生成、一個 capability ID；24 次核准為 1 成功＋23 個 409。
- 不同任務並行時各自拿到正確 task_family 的能力。
- 4 個獨立 Python 程序預留同 family：只有一個 owner；並行核准只有一個成功與一筆成功紀錄。
- 另一 app、重啟及新程序均能查到 Report、ApprovalRecord 與 Audit。
- 注入 audit 寫入失敗確認整筆交易回滾；亦驗證過期更新拒絕及舊 schema migration。
- 警告為既有 Starlette/AnyIO `BlockingPortal` alias 棄用，不影響測試結果。
- 臨時資料庫、報告與測試目錄已清理；未拿較早提交的範例報告冒充本次測試證據。

### 修改範圍與後續

主要檔案：`src/main.py`、`src/api/`、`src/agents/`、`src/domain/capability.py`、
`src/domain/errors.py`、`src/interfaces/repository.py`、SQLite adapter、相關 service、
`tests/support.py`、`tests/test_api.py`、`tests/test_concurrency.py`。

同步更新 README（雙語）、PROJECT_STATUS、DEV_PLAN；新增
[API_CONCURRENCY.md](docs/API_CONCURRENCY.md) 記錄 API 語意、遷移與操作限制。
本紀錄與 API/併發修復一起提交；可用 `git log -- DEVELOPMENT_LOG.md` 追溯對應 commit。

仍待完成：獨立 Uvicorn/HTTP 驗證、長時間壓力測試、強制終止後名額復原、授權與資料
控制、真正限制執行及隔離。跨主機部署不在本次範圍。Phase 1.5 仍未開始。
目前狀態為 **自動化核心/API/併發驗證通過，獨立伺服器驗證待完成**。

---

## 2026-09-20 — dev 同步、完整回歸與獨立 Uvicorn/HTTP 驗證

### 分支與基準

- 在乾淨工作樹切換至 `dev`，以 `git pull --ff-only origin dev` 更新。
- `dev` 由 `c71bf0c` fast-forward 至 `773df54`（`Merge feature/api-integration into dev`），
  驗證結束時與 `origin/dev` 同步，沒有修改 `main` 或建立額外 merge commit。
- 驗證期間建立的 SQLite、pytest 暫存目錄、runtime log 與報告副本均使用隔離目錄；
  完成核對後已清理，未納入版本控制。

### 完整 pytest

- 環境：專案 `.venv`、Python 3.14.3、pytest 9.1.1。
- 使用專案內唯一可寫的 `--basetemp` 並停用 pytest cache，完整收集 25 項測試。
- 結果：**25 passed, 1 warning in 6.82s**。
- 唯一警告為 Starlette TestClient 引用已棄用的 AnyIO `BlockingPortal` alias；
  沒有產品程式錯誤或測試失敗。

### 獨立 Uvicorn / HTTP 驗證

以真正的獨立 Uvicorn 程序綁定 loopback 隨機連接埠，不使用 TestClient，完成：

1. `GET /openapi.json` 確認 lifespan 啟動完成。
2. `POST /api/tasks` 產生文字統計能力，取得 `capability_pending_approval`。
3. 經 HTTP 查詢 capability 與 test report，確認狀態 `pending_approval`、pass rate 100%。
4. `POST /api/approvals/{id}/approve` 後狀態成為 `active`。
5. 再次提交同 task family，重用相同能力並得到 `word_count = 3`。
6. 經 `GET /api/audit` 取得 2 筆紀錄：request approval 與 approve。
7. 停止 Uvicorn、使用相同 SQLite 路徑重新啟動，再次經 HTTP 查詢並執行。

首次啟動與重啟的 access log 中上述請求皆為 HTTP 200；process log 皆顯示
application startup complete，未出現 traceback 或伺服器錯誤。驗證程序最後已停止，
loopback 連接埠確認不再接受連線。

### 報告與持久化證據

- HTTP 與檔案副本中的報告一致：pass rate 100%、risk level `low`、
  functional `basic_sentence` 與 boundary `empty_text` 均通過。
- `test_report.json` 與 `test_report.md` 均存在且可讀；SQLite 內的版本化報告也可於
  Uvicorn 重啟後由 HTTP 取得。
- 重啟後 capability 仍為 `active`，audit 數量仍為 2，能力仍可正確執行。
- 直接核對隔離 SQLite：Capability 1、TestReport 1、ApprovalRecord 1、AuditEntry 2。
- 前兩次驗證腳本中曾分別誤用 task response 狀態名稱，以及將 PowerShell 回傳的 JSON
  陣列再包成單一物件；對照 API 契約與 SQLite 後修正驗證腳本，最終以全新資料庫
  從頭通過。這兩項是驗證腳本斷言問題，不是產品資料遺失。

### 結論與剩餘限制

Phase 1 定義的核心、HTTP、併發、跨程序持久化及獨立伺服器驗證均已有執行證據。
這不代表 production-ready：認證／授權、tenant/owner/scope 控制、可信 reviewer、
restrictions 強制執行、真正 sandbox、生成租約復原、長時間負載與跨主機部署仍未完成。
