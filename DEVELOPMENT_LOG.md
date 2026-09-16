# Capability-Evolving Agent — Development Log

## Purpose

`DEVELOPMENT_LOG.md` 用於記錄專案的**實際開發過程與決策脈絡**。

它與其他文件的角色區分如下：

- `Capability-Evolving Agent Architecture — System Design v1.6.md`：長期系統架構與設計原則
- `Capability_Evolving_Agent_Tech_Stack_v1.md`：技術棧與分階段安裝規劃
- `DEV_PLAN.md`：目前開發計畫、範圍與替換路徑
- `PROJECT_STATUS.md`：目前所處 Phase、完成度與下一步
- `DEVELOPMENT_LOG.md`：詳細記錄「實際做了什麼、為什麼這樣做、遇到什麼問題、如何處理、造成什麼影響」

這份文件應採**持續追加**方式維護，不覆蓋歷史紀錄。

---

# 記錄原則

每次有實質開發、重構、架構調整或重要測試結果時，都應新增一筆紀錄。

每筆紀錄至少應包含：

- 日期
- 開發階段
- 開發目標
- 背景與原因
- 實作內容
- 重要技術決策
- 修改檔案
- 測試 / 驗證狀態
- 問題與限制
- 後續影響
- 下一步
- 關聯文件 / Commit（若有）

建議格式：

```markdown
## YYYY-MM-DD — 紀錄標題

### Phase
Phase X

### 目標
...

### 背景 / 原因
...

### 實作內容
...

### 技術決策
...

### 修改檔案
- ...

### 驗證結果
- ...

### 問題與限制
- ...

### 對後續架構的影響
- ...

### 下一步
- ...

### 關聯
- Commit: ...
- Design: ...
```

---

# Development History

## 2026-09-16 — Phase 1 MVP 架構骨架建立

### Phase
Phase 1 — Core MVP

### 目標

建立 Capability-Evolving Agent 的第一版可執行系統骨架，先驗證核心生命週期：

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

此階段的目標不是接入完整正式基礎設施，而是先確認系統各層責任、資料流與 Agent orchestration 能形成完整閉環。

### 背景 / 原因

設計初期曾考慮直接使用 PostgreSQL、Docker、NVIDIA NIM、OpenRouter、LiteLLM 等正式技術棧，但若一次導入過多基礎設施，會讓研究初期難以區分：

- 問題來自 Capability-Evolving Architecture 本身
- 還是來自外部服務、環境安裝或整合問題

因此決定採用：

> **Implement Simple, Interface for Complex**

先以 mock / in-memory / SQLite / subprocess 方式完成最小閉環，同時保留抽象介面，後續再逐步替換正式 implementation。

### 實作內容

建立主要專案分層：

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

建立：

- `MainAgent`
- `EvolutionAgent`

`MainAgent` 主要流程：

```text
Task
→ Search Capability
→ Existing Capability?
    ├─ Yes → Execute
    └─ No  → Detect Gap → Evolution
```

`EvolutionAgent` 流程：

```text
Generate
→ Validate
→ Test
→ Finalize / Approval Request
```

LangGraph 僅負責 orchestration，主要 Business Logic 放入 Service Layer。

#### Domain Layer

建立：

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

以避免未來做 Enterprise / Sharing / Marketplace 時重新修改核心資料模型。

#### Interface Layer

建立抽象介面：

- `LLMProvider`
- `QueueInterface`
- `SandboxInterface`
- `NotificationProvider`
- `CapabilityRepository`

目的是讓 Agent / Service 不直接依賴具體 Infrastructure。

#### Infrastructure Layer

Phase 1 先使用：

- `MockLLMProvider`
- `InMemoryEvolutionQueue`
- `SqliteCapabilityRepository`
- `SubprocessSandbox`
- `ConsoleNotificationProvider`

這些皆為正式服務的替代實作。

#### Service Layer

建立：

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

使主要系統責任從 Agent orchestration 中分離。

#### API Layer

FastAPI routes 建立：

- `POST /api/tasks`
- Capability 查詢 API
- Evolution Queue API
- Approval API
- Audit API

### 技術決策

#### 1. LangGraph 只作 Orchestration

不將大量 Business Logic 直接寫進 node。

原因：

未來若改用其他 Agent Framework 或 Durable Workflow Engine，不需要重寫整套核心邏輯。

#### 2. SQLite 先取代 PostgreSQL

雖然正式架構規劃使用 PostgreSQL，但 Phase 1 使用 SQLite，降低初始 runtime dependency。

後續透過 `CapabilityRepository` interface 替換成 PostgreSQL。

#### 3. Mock LLM 先取代真實 LLM

使用 Mock Provider 先驗證 workflow。

後續目標：

```text
MockLLMProvider
→ LiteLLMProvider
→ NVIDIA NIM / OpenRouter
```

#### 4. Subprocess 先取代 Docker Sandbox

Phase 1 先以 Python subprocess 測試產生的 Capability。

這不是正式安全邊界，只是用來驗證：

- generated implementation
- functional test
- execution path

正式版本會改成 Docker-based sandbox，後期高風險場景再考慮 gVisor / Firecracker / VM。

#### 5. 人工 Approval 從研究版開始保留

新 Capability 不允許：

```text
Generated → Active
```

而必須：

```text
Generated
→ Validated
→ Tested
→ Test Report
→ Pending Approval
→ Administrator Approval
→ Active
```

此設計從研究階段即保留，未來正式商品化不需重新設計治理流程。

### 修改 / 建立檔案

主要建立：

```text
src/agents/main_agent.py
src/agents/evolution_agent.py

src/domain/capability.py
src/domain/gap.py
src/domain/report.py
src/domain/approval.py
src/domain/events.py

src/interfaces/llm.py
src/interfaces/queue.py
src/interfaces/sandbox.py
src/interfaces/notification.py
src/interfaces/repository.py

src/infrastructure/mock_llm.py
src/infrastructure/memory_queue.py
src/infrastructure/sqlite_repository.py
src/infrastructure/subprocess_sandbox.py
src/infrastructure/console_notification.py

src/services/capability_service.py
src/services/gap_detection_service.py
src/services/evolution_service.py
src/services/validation_service.py
src/services/testing_service.py
src/services/policy_service.py
src/services/approval_service.py
src/services/notification_service.py
src/services/execution_service.py
src/services/report_store.py
src/services/audit_service.py

src/api/routes/tasks.py
src/api/routes/capabilities.py
src/api/routes/evolution.py
src/api/routes/approvals.py
src/api/routes/audit.py

src/main.py
```

並建立測試：

```text
tests/test_capability_schema.py
tests/test_capability_service.py
tests/test_full_loop.py
```

### 驗證狀態

目前：

- 程式骨架：完成
- Test cases：完成
- 實際 `pytest`：尚未執行
- FastAPI runtime：尚未啟動驗證
- 真實 LLM：尚未接入
- PostgreSQL：尚未接入
- Docker sandbox：尚未接入

因此目前應視為：

> **Architecture Skeleton Complete / Runtime Validation Pending**

### 問題與限制

1. Mock LLM 只能證明 workflow，不代表真實 LLM 能穩定產生 Capability。
2. subprocess sandbox 不具備正式隔離能力。
3. SQLite 不代表未來 PostgreSQL persistence / concurrency 行為。
4. Capability Search 目前仍以 task family / 簡單邏輯為主，尚未做 semantic retrieval。
5. 自主 Testing Agent 目前屬基礎版，還沒有完整 adversarial / generalization test generation。

### 對後續架構的影響

Phase 1 已確認專案應繼續採用：

```text
Agent
→ Service
→ Interface
→ Infrastructure Adapter
```

而不是：

```text
Agent
→ Database / Docker / NVIDIA API
```

這個邊界會直接沿用至正式版本。

### 下一步

進入：

**Phase 1.5 — Real Infrastructure Integration**

預計依序處理：

1. 實際執行 pytest / API，確認骨架可跑
2. LiteLLM Provider
3. NVIDIA NIM / OpenRouter
4. PostgreSQL Repository
5. Docker Sandbox
6. 更完整 Autonomous Testing

---

## 2026-09-16 — 新增 Capability 測試報告與人工治理流程

### Phase
Phase 1 — Core Governance Design

### 目標

將 Capability Evolution 從單純的：

```text
Generate → Validate → Store
```

提升為：

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

如果 Agent 可以自行產生能力，但沒有獨立測試、報告與人工確認，未來正式應用會缺乏：

- 可稽核性
- 可靠性
- 人類治理
- 回溯依據

因此 Testing / Report / Approval / Notification 被提升為核心 Capability Lifecycle，而不是商品化後再增加的附加功能。

### 技術決策

#### Testing Agent 與 Evolution Agent 分離

Evolution Agent：

> 負責建立能力。

Testing Agent：

> 負責嘗試找出能力是否會失敗。

避免「能力建立者自行判定成功」的設計偏差。

#### Test Report 永久保存

每一個 Capability Version 都應保留自己的：

```text
test_report.json
test_report.md
```

未來管理員 Approval、Regression、Rollback 都依此追蹤。

#### Notification 與 Approval 分離

Notification 只負責告知管理員。

Approval Service 才具有修改 Capability lifecycle 的權限。

### 下一步

後續正式 Infrastructure Integration 時，必須確保 Test Report、Notification、Approval 不因替換底層服務而消失。

---

## 2026-09-16 — Capability Sharing / Import / Marketplace 架構預留

### Phase
Future Productization — Reserved Architecture

### 目標

保留未來商品化後讓使用者：

- 上傳自己的 Capability
- 選擇是否分享 Capability
- 搜尋其他人的 Capability
- 下載外部 Capability
- 將外部 Capability 安裝到自己的 Agent

的架構空間。

### 背景 / 原因

Capability-Evolving Agent 若商品化，Capability Library 本身可能形成平台級資產。

長期可能出現：

```text
Agent A learns Capability X
→ User Opt-In Share
→ Shared Registry
→ Agent B discovers X
→ User Opt-In Download
→ Local Validation
→ Agent B gains X
```

這代表 Agent 之間可以進行：

> **Capability-level collective learning**

而不需要交換模型權重。

### 目前決策

此功能目前定義為：

> **Future Reserved Development**

研究 MVP 不實作完整：

- Import
- Export
- Publish
- Discover
- Sync
- Marketplace

但 Capability Schema 先保留：

- `scope`
- `sharing_policy`
- `origin`
- `parent_capability_id`
- `distribution_metadata`

並預留未來服務邊界：

- CapabilityImportService
- CapabilityExportService
- CapabilityPublishingService
- CapabilityDiscoveryService
- CapabilitySyncService

### 安全原則

外部 Capability 一律視為 Untrusted。

即使已有其他環境測試報告，進入本地 Agent 仍必須：

```text
Import
→ Compatibility Check
→ Local Validation
→ Local Testing
→ Local Test Report
→ Administrator Approval
→ Active
```

### 下一步

此區目前不進入實作，等待核心 Capability-Evolving Architecture 完成研究驗證後再開發。

---

# Pending Log Entries

後續應持續新增：

- Phase 1 首次 Runtime Validation
- Phase 1.5 LiteLLM 整合
- NVIDIA NIM 整合
- OpenRouter fallback 整合
- PostgreSQL Repository migration
- Docker Sandbox migration
- Phase 2 pgvector semantic retrieval
- Phoenix / MLflow integration
- Autonomous Generalization Testing
- Capability Sharing prototype

---

# Maintenance Rule

當以下任一事件發生時，應更新本文件：

- 新增一個核心 Service / Agent
- 替換 Infrastructure Provider
- Capability Lifecycle 有變更
- 重大 Bug / Failure 被發現
- 做出重要架構取捨
- Phase 完成
- Benchmark / Experiment 得到重要結果
- 安全模型改變
- Future Reserved 功能開始實作

`DEVELOPMENT_LOG.md` 的目標不是只列完成事項，而是保留：

> **這個系統是怎麼一步一步被設計、修改、驗證與演進出來的。**
