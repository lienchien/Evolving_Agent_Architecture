# Capability-Evolving Agent — Phase 1 MVP Development Plan

## Current Status

**Phase 1 Skeleton Implemented / Runtime Validation Pending**

目前 repo 已建立 Phase 1 所需的主要程式骨架與測試程式，包括 Main Agent、Evolution Agent、Capability lifecycle、Validation / Testing、Approval、Notification、Audit、FastAPI routes，以及 full-loop 測試程式。

但目前必須明確區分：

- **程式骨架已建立**
- **測試程式已撰寫**
- **尚未實際執行 `pytest`**
- **尚未啟動 FastAPI**
- **尚未驗證端對端流程**
- **尚未取得任何 runtime evidence**

因此目前不能宣稱 MVP 已完成或核心流程已跑通。

`.env.example` 因權限設定的 deny rule 被擋下，目前 repo 使用 `env.example`；實際使用時再複製為 `.env`。

---

## Context

目前階段的目標是建立 Capability-Evolving Agent 的最小實作骨架，讓以下核心生命週期在程式結構上都有明確對應：

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

現階段只代表上述流程已有對應程式碼與 test code，**不代表流程已成功執行**。

Sharing / Import / Export / Marketplace / Collective Capability Network 維持 **Future Reserved**，目前只保留必要 schema 與 extension point，不納入 Phase 1 runtime validation。

Phase 1 採用簡化 infrastructure：

- Mock LLM
- SQLite
- In-memory Queue
- Python subprocess sandbox
- Console notification

目的是先降低外部依賴，再進行第一次完整 runtime 驗證。

---

## Phase 1 Scope

### 本階段實作

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

### 本階段暫不實作

- Export
- Import
- Publish
- Discover
- Sync
- Marketplace
- Collective Network
- 真實 PostgreSQL runtime adapter
- Docker Sandbox
- LiteLLM / NVIDIA NIM / OpenRouter
- pgvector
- Phoenix / MLflow
- Redis / RQ

---

## Project Structure

```text
Evolving_Agent_Architecture/
├── DEV_PLAN.md
├── PROJECT_STATUS.md
├── DEVELOPMENT_LOG.md
├── requirements.txt
├── env.example
├── pytest.ini
├── src/
│   ├── main.py
│   ├── config.py
│   ├── domain/
│   │   ├── capability.py
│   │   ├── gap.py
│   │   ├── report.py
│   │   ├── approval.py
│   │   └── events.py
│   ├── interfaces/
│   │   ├── llm.py
│   │   ├── queue.py
│   │   ├── sandbox.py
│   │   ├── notification.py
│   │   └── repository.py
│   ├── infrastructure/
│   │   ├── mock_llm.py
│   │   ├── memory_queue.py
│   │   ├── sqlite_repository.py
│   │   ├── subprocess_sandbox.py
│   │   └── console_notification.py
│   ├── services/
│   │   ├── capability_service.py
│   │   ├── gap_detection_service.py
│   │   ├── evolution_service.py
│   │   ├── validation_service.py
│   │   ├── testing_service.py
│   │   ├── policy_service.py
│   │   ├── approval_service.py
│   │   ├── notification_service.py
│   │   ├── execution_service.py
│   │   ├── report_store.py
│   │   └── audit_service.py
│   ├── agents/
│   │   ├── main_agent.py
│   │   └── evolution_agent.py
│   └── api/routes/
│       ├── tasks.py
│       ├── capabilities.py
│       ├── evolution.py
│       ├── approvals.py
│       └── audit.py
└── tests/
    ├── test_capability_schema.py
    ├── test_capability_service.py
    └── test_full_loop.py
```

---

## Core Component Intent

### Capability Schema

目前已建立對應 schema 與 lifecycle state，包含版本、scope、sharing policy、validation requirements、safety requirements 等欄位。

這些結構目前只完成 code-level 定義，尚未 runtime 驗證 serialization / persistence / transition behavior。

### Main Agent

預期流程：

```text
Task
→ Search Capability
→ Found?
   ├─ Yes → Execute
   └─ No  → Gap → Evolution
```

目前已有 LangGraph 定義，但尚未實際 invoke 驗證。

### Evolution Agent

預期流程：

```text
Generate
→ Validate
→ Test
→ Finalize / Approval Request
```

目前已有流程程式碼，但尚未實際執行。

### Mock LLM

Mock Provider 目前只用來提供 deterministic capability generation behavior，目的在降低第一輪測試變數。

它尚未實際跑過，因此目前不能宣稱 Generate 流程已被證明。

### Validation / Testing

Subprocess Sandbox、ValidationService、TestingService 已實作骨架。

預期功能包括：

- 執行 generated implementation
- functional test
- boundary / additional test
- Test Report 產生

目前都尚待實際 runtime 驗證。

### Registry / Approval / Notification

Capability lifecycle、Approval、Console Notification 與 Audit 都已有對應程式碼。

目前仍需實際驗證：

- `pending_approval`
- approve → active
- notification output
- audit record

### FastAPI

API routes 已建立，但 server 尚未啟動過。

---

## Test Plan

目前已有：

- `tests/test_capability_schema.py`
- `tests/test_capability_service.py`
- `tests/test_full_loop.py`

這代表**測試程式已撰寫**，不是測試已通過。

### First Runtime Validation

第一輪必須實際完成：

```text
pip install -r requirements.txt
pytest
uvicorn src.main:app --reload
```

然後驗證：

1. Unknown task 產生 Gap
2. Evolution 產生 Candidate Capability
3. Validation 實際執行
4. Testing 實際產生 Test Report
5. Capability 進入 `pending_approval`
6. Approval 後變成 `active`
7. 第二次同類 task reuse 既有 Capability
8. Audit 與 notification 實際產生

---

## Known Risks Before First Run

- LangGraph API compatibility
- Windows subprocess path / encoding behavior
- generated Python code execution
- SQLite path / persistence behavior
- test report filesystem path
- lifecycle transition defects
- API dependency / DI wiring defects

在第一輪 runtime validation 前，以上都屬於未驗證風險。

---

## Phase 1 Exit Criteria

Phase 1 只有在以下條件成立時才可標示完成：

- `pytest` passes
- FastAPI starts successfully
- Full capability lifecycle actually runs
- Test Report is actually generated
- Approval actually activates Capability
- Reuse is actually demonstrated
- Audit / notification evidence exists

在此之前，統一稱為：

> **Phase 1 Skeleton Implemented / Runtime Validation Pending**

---

## 補充：Failed / Revision Requested 自動迴圈（已實作）

複查文件時發現 README 畫了兩條例外路徑（`Testing → Failed → Evolution Queue`、`Pending Approval → Revision Requested → Evolution Queue`），但當時 `CapabilityStatus` 沒有對應狀態、程式也沒有自動迴圈邏輯。現已補上：

- `CapabilityStatus` 新增 `FAILED`、`REVISION_REQUESTED` 兩個狀態，並更新 `capability_service.py` 的合法轉換表。
- `TestingService.run_autonomous_tests()`：只要 functional test 有任何一項沒過，直接判定 `FAILED`（不再送進 `pending_approval` 打擾管理員）；只有 boundary test 失敗則維持原本 `TESTED → pending_approval`，交給人類看報告判斷。
- `EvolutionAgent`：`test` 節點後改成條件邊，只有狀態是 `TESTED` 才會走到 `finalize`（送審），`FAILED` 直接結束該次演化。
- `ApprovalService.request_revision()`：改成轉成 `REVISION_REQUESTED`（原本誤轉回 `DRAFT`）。
- 「回到 Evolution Queue」的實際機制：`FAILED`／`REVISION_REQUESTED` 都不算 `find_active_by_task_family()` 的命中對象，所以下一次同 `task_family` 的任務進來時，`GapDetectionService` 會重新判定為 gap，`MainAgent` 會照原本流程把新 gap 送進 `InMemoryEvolutionQueue` 再跑一次完整 Evolution，產生一個全新的 Capability（新 `capability_id`）。這是 Phase 1（還沒有背景 worker）下最貼近文件描述、又不用另外做輪詢/重試機制的做法。
- 新增 `tests/test_capability_failure_and_revision.py`：用一個故意產生錯誤結果的假 LLM Provider 驗證 FAILED 路徑，並驗證 revision-requested 後重新提交任務會產生新的 Capability。
- 測試共用的 wiring 邏輯抽到 `tests/support.py`，`test_full_loop.py` 改為呼叫它。

同樣尚未實際執行 `pytest` 驗證，屬於程式碼層級的補完，不是 runtime evidence。

---

## Next Stage — Phase 1.5 Real Infrastructure Integration

只有 Phase 1 runtime validation 成功後才開始。

預計順序：

1. MockLLMProvider → LiteLLMProvider
2. NVIDIA NIM / OpenRouter
3. SQLite → PostgreSQL
4. SubprocessSandbox → DockerSandbox
5. 擴充 autonomous testing / generalization testing

Phase 2 再加入：

- pgvector
- semantic capability retrieval
- observability
- experiment tracking

---

## Future Adapter Replacement

```text
MockLLMProvider
→ LiteLLMProvider
→ NVIDIA NIM / OpenRouter
```

```text
SqliteCapabilityRepository
→ PostgreSQLCapabilityRepository
```

```text
SubprocessSandbox
→ DockerSandbox
```

```text
InMemoryEvolutionQueue
→ Redis / RQ
```

```text
Task-family matching
→ pgvector semantic retrieval
```

核心原則仍是：

> **Agent → Service → Interface → Infrastructure Adapter**

但此架構目前仍處於 implementation skeleton 階段，尚待第一次實際執行驗證。
