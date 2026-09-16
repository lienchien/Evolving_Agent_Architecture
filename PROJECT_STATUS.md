# Capability-Evolving Agent — Project Status

> 本文件用來追蹤目前實際開發階段、已完成的「實作骨架」、尚未執行的驗證工作，以及下一階段規劃。
>
> 重要原則：本文件中的「已完成」若未特別註明，僅代表**程式骨架或測試程式已建立**，不代表已通過 runtime 驗證。

---

## Current Stage

### Phase 1 — Core MVP Skeleton Implementation

**Status:** Skeleton implemented / Failure & revision routing implemented / Tests written / Ready for first runtime validation.

目前實際狀況：

- Agent 與 API 的核心程式骨架已建立。
- Capability lifecycle、Validation、Testing、Approval、Notification、Audit 等對應模組已建立。
- Main Agent 與 Evolution Agent wiring 已同步。
- `FAILED` 與 `REVISION_REQUESTED` lifecycle 已補齊。
- Evolution Agent 已具備 test 後的條件分流：`TESTED → finalize / approval`、`FAILED → END`。
- Functional test failure 會直接標記 Capability 為 `FAILED`，不進人工 approval。
- `request_revision` 會轉入 `REVISION_REQUESTED`，後續同 task family 任務會重新觸發 evolution。
- 單元測試、full-loop 測試、failure path 測試與 revision path 測試程式已撰寫。
- Test Report 的 failed test 描述已依實際 `test_type` 區分，不再將所有失敗一律標記為 boundary failure。
- **尚未實際執行 `pytest`。**
- **尚未啟動 FastAPI 驗證 API。**
- **尚未取得端對端 runtime evidence。**
- **尚未整合真實 LLM、PostgreSQL 或 Docker Sandbox。**

因此目前仍不能宣稱 MVP 已完成或核心循環已跑通；但 Phase 1 code-level skeleton 已具備進入第一次 runtime validation 的條件。

目標循環：

```text
Task
 ↓
Capability Search
 ↓
Gap
 ↓
Generate
 ↓
Validate
 ↓
Test
 ├─ FAILED → END / future re-evolution
 └─ TESTED
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
- [x] Evolution flow: generate → validate → test → conditional finalize
- [x] Testing 失敗（functional test 未通過）自動判定為 `FAILED`，跳過 approval request
- [x] `request_revision` 轉為 `REVISION_REQUESTED`
- [x] Evolution Agent / main container / test support dependency wiring 一致
- [ ] 實際執行並驗證 LangGraph 流程

## Domain Layer

- [x] Capability schema
- [x] Capability lifecycle states
- [x] `FAILED` lifecycle state
- [x] `REVISION_REQUESTED` lifecycle state
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
- [x] Functional vs boundary failed-test descriptions
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
- [x] Full-loop happy-path test code written
- [x] Functional-test failure path test code written
- [x] Revision-requested re-evolution test code written
- [x] Shared test wiring extracted to `tests/support.py`
- [ ] `pytest` actually executed
- [ ] Test suite passes
- [ ] Manual API end-to-end test executed

---

# 2. Runtime Validation Status

目前 **尚未開始正式 runtime validation**，但 code-level blockers 已完成第一輪修正，下一步應直接進入第一次 `pytest`。

以下仍待實際執行：

- [ ] Python dependencies verified
- [ ] LangGraph version compatibility verified
- [ ] Windows subprocess sandbox verified
- [ ] SQLite persistence behavior verified
- [ ] Generated capability code execution verified
- [ ] Happy-path full loop verified
- [ ] Functional failure path verified
- [ ] Revision-requested path verified
- [ ] Test report files generated and inspected
- [ ] Failed-test descriptions inspected
- [ ] Console notification flow verified
- [ ] Approval API verified
- [ ] Capability activation verified
- [ ] Capability reuse verified
- [ ] Audit records verified

### Known Validation Risks

1. LangGraph API 版本仍可能需要依實際安裝版本微調。
2. Windows subprocess 的 path、encoding 與 generated code execution 尚未實測。
3. SQLite 與 artifact path 尚未實測。
4. Failure / revision lifecycle 雖已完成 code-level routing，但尚未由 pytest 證明。
5. 目前沒有 retry limit；若真實 LLM 持續產生失敗 Capability，未來可能需要 retry / backoff policy。

---

# 3. Phase 1 Exit Criteria

只有以下全部成立時，才能把 Phase 1 標記為完成：

- [ ] `pytest` 實際執行並通過
- [ ] FastAPI 成功啟動
- [ ] Unknown task 實際建立 Capability Gap
- [ ] Evolution Agent 實際產生 Candidate Capability
- [ ] Validation 實際完成
- [ ] Autonomous Testing 實際產生 Test Report
- [ ] Functional failure 實際進入 `FAILED` 並跳過 approval
- [ ] Revision request 實際進入 `REVISION_REQUESTED` 並可觸發下一輪 evolution
- [ ] Capability 實際進入 `pending_approval`
- [ ] Administrator approval 實際使 Capability 轉為 `active`
- [ ] 同類 task 實際 reuse 既有 Capability
- [ ] 重複任務沒有建立 duplicate Active Capability
- [ ] Audit records 實際產生

### Phase 1 Completion Rule

在以上條件完成前，不使用：

- `Phase 1 Complete`
- `MVP Complete`
- `End-to-End Verified`
- `Full Loop Proven`

目前統一使用：

> **Phase 1 Skeleton Implemented / Ready for Runtime Validation**

---

# 4. Immediate Next Milestone — First Runtime Validation

目前最高優先級不是增加新功能，而是第一次真正執行：

```bash
pytest
```

第一輪應至少驗證三條路徑：

```text
A. Happy Path
Unknown Task → Gap → Generate → Validate → Test → Pending Approval → Approve → Active → Reuse

B. Failure Path
Generated Capability → Functional Test Fail → FAILED → No Approval

C. Revision Path
Pending Approval → Revision Requested → Next Same Task → New Evolution
```

第一輪 pytest 通過後，再啟動 FastAPI 做 API-level validation。

完整 Phase 1 milestone 最後仍需留下：

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

- [ ] More boundary tests
- [ ] More failure cases
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
FAILED routing                  Implemented, not runtime-verified
REVISION_REQUESTED routing      Implemented, not runtime-verified
Capability lifecycle code       Implemented, not runtime-verified
Validation abstraction          Implemented, not runtime-verified
Testing skeleton                Implemented, not runtime-verified
Failed-test reporting           Refined, not runtime-verified
Test report skeleton            Implemented, not runtime-verified
Human approval code             Implemented, not runtime-verified
Notification abstraction        Implemented, not runtime-verified
Audit skeleton                  Implemented, not runtime-verified
FastAPI routes                  Implemented, server not started
Happy-path test code            Written, not executed
Failure-path test code          Written, not executed
Revision-path test code         Written, not executed

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

> **The Phase 1 code skeleton is ready for first runtime validation, but it is still not a verified MVP.**

下一個重要成果是：

> **Run `pytest` and obtain the first runtime evidence.**
