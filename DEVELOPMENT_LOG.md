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

目前專案仍停留在：

> **Implemented / Test Written，尚未 Executed / Verified**

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
