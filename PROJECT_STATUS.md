# Capability-Evolving Agent — Project Status

> 本文件用來追蹤目前實際開發階段、已完成的「實作骨架」、尚未執行的驗證工作，以及下一階段規劃。
>
> 重要原則：本文件中的「已完成」若未特別註明，僅代表**程式骨架或測試程式已建立**，不代表已通過 runtime 驗證。

---

## Current Stage

### Phase 1 — Core MVP Skeleton Implementation

**Status:** Skeleton implemented / Tests written / Runtime validation not started.

目前實際狀況：

- Agent 與 API 的核心程式骨架已建立。
- Capability lifecycle、Validation、Testing、Approval、Notification、Audit 等對應模組已建立。
- 單元測試與 full-loop 測試程式已撰寫。
- **尚未實際執行 `pytest`。**
- **尚未啟動 FastAPI 驗證 API。**
- **尚未證明端對端流程可成功執行。**
- **尚未整合真實 LLM、PostgreSQL 或 Docker Sandbox。**

因此目前沒有 runtime evidence 可以宣稱核心循環已跑通。

目標循環仍為：

```text
Gap
 ↓
Generate
 ↓
Validate
 ↓
Test
 ↓
Report
 ↓
Notify
 ↓
Approve
 ↓
Activate
 ↓
Reuse
```

---

# 1. Phase 1 Implementation Skeleton Status

## Agent Layer

- [x] Main Agent 程式骨架
- [x] Evolution Agent 程式骨架
- [x] LangGraph orchestration 定義
- [x] Capability search → execute / evolve branching 程式邏輯
- [x] Evolution flow: generate → validate → test → approval request 程式邏輯
- [ ] 實際執行並驗證 LangGraph 流程

## Domain Layer

- [x] Capability schema
- [x] Capability lifecycle states
- [x] Capability Gap model
- [x] Test Report model
- [x] Approval Record model
- [x] Core Event definitions
- [x] Sharing / tenant-related schema placeholders

## Service Layer

- [x] Capability Service skeleton
- [x] Gap Detection Service skeleton
- [x] Evolution Service skeleton
- [x] Validation Service skeleton
- [x] Testing Service skeleton
- [x] Approval Service skeleton
- [x] Notification Service skeleton
- [x] Capability Execution Service skeleton
- [x] Test Report Store skeleton
- [x] Audit Service skeleton
- [x] Policy Service extension point
- [ ] Runtime behavior verified

## Infrastructure Adapters

- [x] Mock LLM Provider implementation
- [x] SQLite Capability Repository implementation
- [x] In-memory Evolution Queue implementation
- [x] Subprocess Sandbox implementation
- [x] Console Notification Provider implementation
- [ ] All adapters actually executed and verified

## API Layer

- [x] `POST /api/tasks` route code
- [x] Capability query route code
- [x] Evolution queue route code
- [x] Approval route code
- [x] Audit route code
- [ ] FastAPI service actually started
- [ ] API endpoints manually verified

## Tests

- [x] Capability schema test code written
- [x] Capability service / lifecycle test code written
- [x] Full-loop test code written
- [ ] `pytest` actually executed
- [ ] Test suite passes
- [ ] Manual API end-to-end test executed

---

# 2. Runtime Validation Status

目前 **尚未開始 runtime validation**。

以下全部仍待實際執行：

- [ ] Python dependencies verified
- [ ] LangGraph version compatibility verified
- [ ] Windows subprocess sandbox verified
- [ ] SQLite persistence behavior verified
- [ ] Generated capability code execution verified
- [ ] Test report files generated and inspected
- [ ] Console notification flow verified
- [ ] Approval API verified
- [ ] Capability activation verified
- [ ] Capability reuse verified
- [ ] Audit records verified

### Known Validation Risks

1. LangGraph API 版本可能需要調整。
2. Windows subprocess 的 path、encoding 與 generated code execution 尚未實測。
3. SQLite 與 artifact path 尚未實測。
4. 目前所有 full-loop 結果都只是 test code 的預期行為，不是實際測試結果。

---

# 3. Phase 1 Exit Criteria

只有以下全部成立時，才能把 Phase 1 標記為完成：

- [ ] `pytest` 實際執行並通過
- [ ] FastAPI 成功啟動
- [ ] Unknown task 實際建立 Capability Gap
- [ ] Evolution Agent 實際產生 Candidate Capability
- [ ] Validation 實際完成
- [ ] Autonomous Testing 實際產生 Test Report
- [ ] Capability 實際進入 `pending_approval`
- [ ] Administrator approval 實際使 Capability 轉為 `active`
- [ ] 同類 task 實際 reuse 既有 Capability
- [ ] 重複任務沒有建立 duplicate Capability
- [ ] Audit records 實際產生

### Phase 1 Completion Rule

在以上條件完成前，不使用：

- `Phase 1 Complete`
- `MVP Complete`
- `End-to-End Verified`
- `Full Loop Proven`

目前統一使用：

> **Phase 1 Skeleton Implemented / Runtime Validation Pending**

---

# 4. Immediate Next Milestone — First Verified End-to-End Run

目前最高優先級不是增加新功能，而是取得第一份 runtime evidence。

成功條件：

```text
Task
→ Gap
→ Generate
→ Validate
→ Test
→ Report
→ Notify
→ Approve
→ Activate
→ Reuse
```

上述流程必須實際執行一次並留下：

- pytest result
- runtime log
- generated Capability artifact
- Test Report
- Approval record
- Audit record
- reuse result

完成後才進入 Phase 1.5。

---

# 5. Phase 1.5 — Real Infrastructure Integration

**Status:** Not started.

前置條件：Phase 1 runtime validation 通過。

## LLM Integration

- [ ] LiteLLM adapter
- [ ] NVIDIA NIM configuration
- [ ] OpenRouter configuration
- [ ] Provider fallback / health check
- [ ] 保留 MockLLMProvider 作 deterministic test

## Database Integration

- [ ] PostgreSQL Capability Repository
- [ ] Database migration strategy
- [ ] Runtime configuration switching

## Sandbox Integration

- [ ] Docker Sandbox adapter
- [ ] Resource limits
- [ ] Temporary filesystem isolation
- [ ] Network policy
- [ ] Cleanup behavior

## Testing Improvements

- [ ] Boundary tests
- [ ] Failure cases
- [ ] Regression tests
- [ ] Generalization tests
- [ ] Safety tests
- [ ] Performance metrics

---

# 6. Later Phases

## Phase 2 — Capability Retrieval and Reuse Intelligence

**Status:** Planned.

- pgvector
- Embedding Provider
- Semantic Capability Search
- Compatibility filtering
- Ranking
- Duplicate prevention

## Phase 3 — Research Evaluation and Observability

**Status:** Planned.

- Phoenix / equivalent tracing
- DeepEval
- MLflow
- Token / latency / cost tracking
- Capability generation success metrics
- Reuse / generalization / regression metrics

## Phase 4 — Background Evolution

**Status:** Planned.

- Redis
- RQ or equivalent worker
- Evolution Worker
- Testing Worker
- Notification Worker

## Phase 5 — Stronger Isolation

**Status:** Future.

Potential options: gVisor / Firecracker / Kata Containers.

## Phase 6 — Admin / Research Dashboard

**Status:** Future.

## Phase 7 — Local LLM Support

**Status:** Reserved.

## Phase 8 — Enterprise Domain Validation

**Status:** Future research.

## Phase 9 — Cybersecurity Extension

**Status:** Future high-difficulty validation domain.

## Phase 10 — Capability Sharing Infrastructure

**Status:** Future Reserved Development.

Reserved services:

- CapabilityImportService
- CapabilityExportService
- CapabilityPublishingService
- CapabilityDiscoveryService
- CapabilitySyncService
- SharedCapabilityRegistry

## Phase 11 — Capability Marketplace / Collective Network

**Status:** Long-term productization.

---

# 7. Current Summary

```text
Design documents                Available
Architecture skeleton           Implemented, not runtime-verified
Main Agent code                 Implemented, not runtime-verified
Evolution Agent code            Implemented, not runtime-verified
Capability lifecycle code       Implemented, not runtime-verified
Validation abstraction          Implemented, not runtime-verified
Testing skeleton                Implemented, not runtime-verified
Test report skeleton            Implemented, not runtime-verified
Human approval code             Implemented, not runtime-verified
Notification abstraction        Implemented, not runtime-verified
Audit skeleton                  Implemented, not runtime-verified
FastAPI routes                  Implemented, server not started
Unit test code                  Written, not executed
End-to-end test code            Written, not executed

Runtime evidence                None yet
Real cloud LLM                  Not started
PostgreSQL runtime adapter      Not started
Docker sandbox                  Not started
Semantic retrieval              Not started
Research observability          Not started
Background workers              Not started
Sharing / Marketplace           Future Reserved
```

---

## Current Project State

> **The project currently has an implementation skeleton, not a verified MVP.**

下一個重要成果不是新增更多模組，而是取得：

> **First Verified End-to-End Run**
