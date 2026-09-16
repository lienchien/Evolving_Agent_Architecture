# Capability-Evolving Agent — Project Status

> 本文件用來追蹤目前實際開發階段、已完成項目、待驗證項目與下一階段規劃。
>
> 設計原則與長期架構請參考：
> - `Capability-Evolving Agent Architecture — System Design v1.6.md`
> - `Capability_Evolving_Agent_Tech_Stack_v1.md`
> - `DEV_PLAN.md`

---

## Current Stage

### Phase 1 — Core MVP Skeleton

**Status:** Code skeleton implemented, runtime validation pending.

目前已完成 Agent 與 API 核心骨架，並建立端對端測試案例，但尚未在實際 Python 執行環境執行 `pytest` 或啟動 FastAPI 服務。

核心目標流程：

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

# 1. Phase 1 Completion Status

## Agent Layer

- [x] Main Agent
- [x] Evolution Agent
- [x] LangGraph orchestration
- [x] Capability search → execute / evolve branching
- [x] Evolution flow: generate → validate → test → approval request

## Domain Layer

- [x] Capability schema
- [x] Capability lifecycle states
- [x] Capability Gap model
- [x] Test Report model
- [x] Approval Record model
- [x] Core Event definitions
- [x] Sharing / tenant-related schema placeholders retained

## Service Layer

- [x] Capability Service
- [x] Gap Detection Service
- [x] Evolution Service
- [x] Validation Service
- [x] Testing Service
- [x] Approval Service
- [x] Notification Service
- [x] Capability Execution Service
- [x] Test Report Store
- [x] Audit Service
- [x] Policy Service stub / extension point

## Infrastructure Adapters

- [x] Mock LLM Provider
- [x] SQLite Capability Repository
- [x] In-memory Evolution Queue
- [x] Subprocess Sandbox
- [x] Console Notification Provider

## API Layer

- [x] `POST /api/tasks`
- [x] Capability query endpoints
- [x] Evolution queue endpoint
- [x] Approval endpoints
- [x] Audit endpoint

## Tests

- [x] Capability schema tests
- [x] Capability service / lifecycle tests
- [x] Full-loop test: unknown task → evolve → approval → activate → reuse
- [ ] Execute full pytest suite in real environment
- [ ] Start FastAPI and manually test Swagger / API flow

---

# 2. Current Runtime Status

## Implemented but not yet runtime-verified

- [ ] Python dependency installation verified
- [ ] LangGraph version compatibility verified
- [ ] Windows subprocess sandbox execution verified
- [ ] SQLite runtime behavior verified
- [ ] Test report files verified on disk
- [ ] Notification flow manually verified
- [ ] Approval API manually verified
- [ ] Reuse behavior manually verified through API

### Known validation risks

1. LangGraph API compatibility may require minor adjustment depending on the installed version.
2. Windows subprocess behavior, paths, encoding, and generated code execution still require an actual run.
3. SQLite file location and local artifact paths should be verified during the first real execution.

---

# 3. Phase 1 Exit Criteria

Phase 1 is considered complete only when all of the following are true:

- [ ] `pytest` passes
- [ ] FastAPI starts successfully
- [ ] Unknown task creates a Capability Gap
- [ ] Evolution Agent generates a Candidate Capability
- [ ] Validation completes successfully
- [ ] Autonomous testing produces a Test Report
- [ ] Capability enters `pending_approval`
- [ ] Administrator approval changes Capability to `active`
- [ ] Same task family reuses the existing Capability
- [ ] No duplicate Capability is generated for the repeated task
- [ ] Audit records are generated for key lifecycle operations

---

# 4. Next Stage — Phase 1.5 Real Infrastructure Integration

**Planned status:** Not started.

Goal: replace Phase 1 mock / lightweight adapters with actual infrastructure while preserving existing interfaces.

## LLM Integration

- [ ] Add LiteLLM adapter
- [ ] Add NVIDIA NIM configuration
- [ ] Add OpenRouter configuration
- [ ] Provider fallback / health check
- [ ] Keep `MockLLMProvider` for deterministic tests

Target transition:

```text
MockLLMProvider
       ↓
LiteLLMProvider
 ├─ NVIDIA NIM
 └─ OpenRouter
```

## Database Integration

- [ ] Implement PostgreSQL Capability Repository
- [ ] Database migration strategy
- [ ] Replace SQLite in runtime configuration
- [ ] Retain SQLite for lightweight tests if useful

## Sandbox Integration

- [ ] Implement Docker Sandbox adapter
- [ ] Container resource limits
- [ ] Temporary filesystem isolation
- [ ] Network policy decision
- [ ] Cleanup behavior

Target transition:

```text
SubprocessSandbox
       ↓
DockerSandbox
```

## Autonomous Testing Improvements

- [ ] Functional tests
- [ ] Boundary tests
- [ ] Failure cases
- [ ] Regression tests
- [ ] Generalization tests
- [ ] Safety tests
- [ ] Performance metrics
- [ ] Human-readable report improvements

---

# 5. Phase 2 — Capability Retrieval and Reuse Intelligence

**Status:** Planned.

Goal: move from exact / task-family matching to semantic capability retrieval.

- [ ] Install / enable pgvector
- [ ] Define Embedding Provider interface
- [ ] Generate Capability embeddings
- [ ] Semantic Capability search
- [ ] Compatibility filtering
- [ ] Capability ranking
- [ ] Reuse metrics
- [ ] Duplicate capability prevention improvements

Target flow:

```text
Task
 ↓
Embedding
 ↓
Semantic Capability Search
 ↓
Compatibility Filter
 ↓
Reuse or Capability Gap
```

---

# 6. Phase 3 — Research Evaluation and Observability

**Status:** Planned.

- [ ] Arize Phoenix or equivalent tracing
- [ ] DeepEval
- [ ] MLflow
- [ ] Standard run / task / capability / experiment IDs
- [ ] Token tracking
- [ ] Latency tracking
- [ ] Cost tracking
- [ ] Capability generation success metrics
- [ ] Reuse rate
- [ ] Generalization rate
- [ ] Regression rate
- [ ] Repeated failure rate

Research baseline groups:

| Group | Model | Capability Evolution |
|---|---|---|
| A | Strong | No |
| B | Medium | No |
| C | Medium | Yes |
| D | Strong | Yes |

Core question:

> Can capability accumulation improve long-horizon Agent performance even when model intelligence remains unchanged?

---

# 7. Phase 4 — Background Evolution

**Status:** Planned.

- [ ] Redis
- [ ] RQ or alternative worker layer
- [ ] Background Evolution Worker
- [ ] Background Testing Worker
- [ ] Notification Worker
- [ ] Retry / failure handling
- [ ] Queue observability

Target architecture:

```text
Main Agent
   ↓
Capability Gap
   ↓
Queue
   ↓
Evolution Worker
   ↓
Validation / Testing
```

---

# 8. Phase 5 — Stronger Isolation

**Status:** Future.

Potential options:

- [ ] gVisor
- [ ] Firecracker
- [ ] Kata Containers

Only one or more will be selected if actual risk requirements justify them.

Docker remains the default low-risk validation environment.

---

# 9. Phase 6 — Admin / Research Dashboard

**Status:** Future.

Potential UI:

- Streamlit for research stage
- Formal web admin console for product stage

Planned views:

- [ ] Capability list
- [ ] Capability lifecycle
- [ ] Test reports
- [ ] Pending approvals
- [ ] Audit trail
- [ ] Notifications
- [ ] Capability reuse metrics
- [ ] Model / cost metrics

---

# 10. Phase 7 — Local LLM Support

**Status:** Reserved.

Architecture interface should remain available even though the current AMD RX 6650 XT is not used as the primary LLM execution path.

Potential future providers:

- Ollama
- llama.cpp
- vLLM
- LM Studio
- Private OpenAI-compatible inference server

---

# 11. Phase 8 — Enterprise Domain Validation

**Status:** Future research.

Potential controlled domains:

- File processing
- Data transformation
- IT automation
- DevOps troubleshooting
- Internal workflows
- Enterprise procedures

Purpose:

Validate whether the same Capability Evolution Engine generalizes across domains.

---

# 12. Phase 9 — Cybersecurity Extension

**Status:** Future high-difficulty validation domain.

Potential components:

- MITRE ATT&CK
- Atomic Red Team
- Wazuh
- Sysmon
- Velociraptor
- Zeek
- Suricata
- CALDERA
- Cyber Range

Core Evolution / Testing / Approval / Notification lifecycle should remain unchanged.

---

# 13. Phase 10 — Capability Sharing Infrastructure

**Status:** Future Reserved Development.

No full implementation should be added during the current MVP stages.

Reserved future services:

- CapabilityImportService
- CapabilityExportService
- CapabilityPublishingService
- CapabilityDiscoveryService
- CapabilitySyncService
- SharedCapabilityRegistry

Required future mechanisms:

- Package format
- Signature / integrity verification
- Sanitization / environment neutralization
- Compatibility validation
- Provenance
- Capability lineage
- Consent / sharing policy
- Local re-validation before activation

Default principle:

> Capability sharing and acquisition are opt-in.

External capabilities are untrusted until locally validated and approved.

---

# 14. Phase 11 — Capability Marketplace / Collective Network

**Status:** Long-term productization.

Possible components:

- Capability Marketplace
- Organization Registry
- Global Registry
- Publisher verification
- Capability reputation / trust
- Subscription / update model
- Cross-Agent capability transfer

Long-term concept:

```text
Agent A learns Capability X
        ↓
User opts in to share
        ↓
Shared Registry
        ↓
Agent B discovers X
        ↓
User opts in to acquire
        ↓
Local Validation
        ↓
Administrator Approval
        ↓
Agent B gains Capability X
```

---

# 15. Development Priority

Current priority order:

1. **Run and verify Phase 1 MVP**
2. Fix runtime defects
3. Replace Mock LLM with real provider integration
4. Replace SQLite with PostgreSQL
5. Replace subprocess sandbox with Docker
6. Improve autonomous tests and reports
7. Add semantic retrieval with pgvector
8. Add experiment tracking and observability
9. Background evolution workers
10. Only then move toward domain extensions and capability sharing

---

# 16. Current Summary

```text
Design                       ✓
Core architecture skeleton   ✓
Main Agent                   ✓
Evolution Agent              ✓
Capability lifecycle         ✓
Validation abstraction       ✓
Autonomous testing skeleton  ✓
Test report skeleton         ✓
Human approval               ✓
Notification abstraction     ✓
Audit skeleton               ✓
FastAPI                      ✓
Unit / lifecycle tests       ✓
End-to-end test definition   ✓

Actual runtime validation    Pending
Real cloud LLM               Pending
PostgreSQL runtime adapter   Pending
Docker sandbox               Pending
Semantic retrieval           Pending
Research observability       Pending
Background workers           Pending
Sharing / Marketplace        Future Reserved
```

---

## Immediate Next Milestone

**Milestone: Phase 1 Runtime Validation**

Success condition:

> A real execution proves the full loop `Gap → Generate → Validate → Test → Report → Notify → Approve → Activate → Reuse` works end-to-end before any major infrastructure expansion is introduced.
