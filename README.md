# Capability-Evolving Agent Architecture

**Language:** English | [繁體中文](README.zh-TW.md)

![Status](https://img.shields.io/badge/status-experimental-orange)
![Phase](https://img.shields.io/badge/phase-1--verified-blue)
![Validation](https://img.shields.io/badge/automated%20tests-25%20passed-green)

> [!WARNING]
> This experimental research prototype has passed automated core, API, concurrency, and standalone Uvicorn/HTTP validation. Authentication, data-access controls, enforced execution restrictions, and production hardening remain pending; it is not production-ready.

A research-oriented Agent architecture that explores whether an AI agent can **identify missing capabilities, generate new executable capabilities, validate and test them, produce auditable reports, request human approval, activate approved capabilities, and reuse them in future tasks**.

The long-term goal is to study whether Agent performance can scale through **capability accumulation**, rather than depending only on stronger foundation models.

---

## Project Status

> **Current Stage (2026-09-20): Phase 1 Verification Complete; Production Hardening Pending**

The repository currently contains the architecture skeleton, core domain models, services, interfaces, Agent orchestration, API routes, and test code for the Phase 1 MVP.

The latest full test run passed **25 tests**, with one existing Starlette/AnyIO deprecation warning. TestClient HTTP flows, SQLite transactions, subprocess execution and cross-process persistence have been exercised. An independent Uvicorn process also completed the task, report, approval, reuse and restart-persistence HTTP flow successfully.

See [project status](PROJECT_STATUS.md), [development log](DEVELOPMENT_LOG.md) and [API concurrency behavior](docs/API_CONCURRENCY.md). Architecture diagrams below describe the broader design: the current synchronous implementation handles each request's own gap directly; the queue is reserved for future background workers. Reports, approvals and audit records now share SQLite storage.

The [token/cost research contract](docs/TOKEN_COST_RESEARCH.md) is documented on `dev`.
Its implementation and 28-test evidence remain on `feature/token-cost-research` (`ca08851`) and
have not been merged; the current `dev` runtime still has 25 tests and no `/api/research/*` routes.

Current status:

```text
Design                       ✓
Architecture skeleton        ✓
Main Agent                   ✓
Evolution Agent              ✓
Capability lifecycle         ✓
Validation abstraction       ✓
Testing skeleton             ✓
Test report structure        ✓
Human approval flow          ✓
Notification abstraction     ✓
Audit skeleton               ✓
FastAPI routes               ✓
Unit / lifecycle tests       ✓
End-to-end test definition   ✓

pytest execution             25 passed
FastAPI TestClient tests     Passed
Mock core loop               Passed
Standalone Uvicorn / HTTP    Passed
Token/cost research contract Documented (feature code pending)
Real LLM integration         Pending
PostgreSQL runtime adapter   Pending
Docker sandbox               Pending
Semantic retrieval           Pending
Observability                Pending
Background workers           Pending
Capability sharing           Future Reserved
Marketplace                  Future Reserved
```

The next development decision is:

> **Review the token/cost measurement feature for runtime integration, then continue production hardening**

The following core flow has passed automated mock tests and standalone server verification:

```text
Task
→ Capability Search
→ Capability Gap
→ Generate
→ Validate
→ Autonomous Test
→ Test Report
→ Notify Administrator
→ Human Approval
→ Activate
→ Reuse
```

---

# 1. Research Motivation

Most current Agent systems improve mainly through:

- stronger language models
- manually added tools
- workflow redesign
- prompt engineering
- memory
- RAG
- model fine-tuning

This project explores an additional scaling dimension:

## Capability Scaling

The main research hypothesis is:

> **An Agent may improve over time by accumulating validated reusable capabilities, even if the underlying model remains unchanged.**

The architecture separates two different growth mechanisms:

### Model Scaling

Improves the Agent's ability to reason about new or unknown problems.

### Capability Scaling

Improves the Agent's ability to reuse previously learned and validated solutions.

A long-term experiment may compare:

| Group | Model | Capability Evolution |
|---|---|---|
| A | Strong | No |
| B | Medium | No |
| C | Medium | Yes |
| D | Strong | Yes |

A key research question is whether:

> **Medium Model + Capability Evolution**

can approach or outperform:

> **Strong Model + Static Capabilities**

on repeated or long-horizon tasks.

---

# 2. Core Concept

The architecture treats a **Capability** as a first-class system object.

A Capability is not just a prompt or memory entry. It is intended to be:

- executable
- inspectable
- testable
- versioned
- auditable
- reusable
- rollback-able
- portable

A Capability may eventually represent:

- Python code
- API workflow
- tool sequence
- data-processing pipeline
- Agent workflow
- containerized service
- domain-specific procedure
- enterprise automation
- security detection or response logic

The core loop is:

```text
Problem
  ↓
Capability Gap
  ↓
Generate Candidate Capability
  ↓
Validate
  ↓
Autonomous Testing
  ↓
Test Report
  ↓
Human Review
  ↓
Approve / Reject / Revise
  ↓
Activate
  ↓
Reuse
```

---

# 3. High-Level Architecture

```text
                         User / Task
                              │
                              ▼
                       Main Agent Service
                              │
                      Capability Search
                              │
              ┌───────────────┴───────────────┐
              │                               │
      Existing Capability             Capability Missing
              │                               │
              ▼                               ▼
     Capability Executor              Gap Detection
                                              │
                                       Evolution Queue
                                              │
                                       Evolution Agent
                                              │
                                      Capability Builder
                                              │
                                      Validation Service
                                              │
                                   Capability Testing Agent
                                              │
                                         Test Report
                                              │
                                         Policy Engine
                                              │
                                     Capability Registry
                                              │
                                      Pending Approval
                                              │
                                     Notification Service
                                              │
                                        Administrator
                                              │
                                      Approval Service
                                              │
                                        Active Capability
```

The architecture follows a key boundary rule:

> **Agent logic should not directly depend on infrastructure implementations.**

Preferred dependency direction:

```text
Agent
→ Service
→ Interface
→ Infrastructure Adapter
```

Instead of:

```text
Agent
→ Database / Docker / Vendor API
```

---

# 4. Core Design Principles

## Capability First

The long-term system asset is the Capability Library, not only conversation history.

## Validation Before Activation

Generated capabilities must never become active immediately.

They must pass validation and testing first.

## Human-Governed Evolution

The Agent may autonomously generate and test capabilities, but new capabilities require administrator approval before first activation.

## Model Independent

The Agent architecture must not be tied to one model provider.

## Infrastructure Independent

Core logic should remain independent from PostgreSQL, Docker, Redis, NVIDIA NIM, OpenRouter, or any specific framework implementation.

## Implement Simple, Interface for Complex

Early implementations may be simple, but interfaces should support future scale.

## Everything Is Versioned

The design intends to version:

- Capability
- Capability schema
- test plan
- test report
- prompt
- model
- policy
- experiment
- artifact

## External Capabilities Are Untrusted by Default

Future imported capabilities must be locally validated before activation.

---

# 5. Capability Lifecycle

Planned lifecycle:

```text
Draft
 ↓
Candidate
 ↓
Validating
 ↓
Testing
 ↓
Tested
 ↓
Pending Approval
 ↓
Approved
 ↓
Active
 ↓
Deprecated
 ↓
Revoked
 ↓
Archived
```

If testing fails:

```text
Testing
 ↓
Failed
 ↓
Evolution Queue
```

If the administrator requests revision:

```text
Pending Approval
 ↓
Revision Requested
 ↓
Evolution Queue
```

---

# 6. Autonomous Testing and Test Reports

Testing is intentionally separated from capability generation.

The Evolution Agent is responsible for creating capabilities.

The Testing Agent is responsible for challenging them.

Planned test categories include:

- Functional Test
- Boundary Test
- Failure Test
- Regression Test
- Generalization Test
- Safety Test
- Performance Test

Each Capability version is intended to produce both:

```text
test_report.json
```

and:

```text
test_report.md
```

The report should eventually include:

- Capability ID and version
- test environment
- test cases
- pass rate
- failed cases
- regression result
- generalization score
- safety result
- performance metrics
- known limitations
- risk level
- recommended action

---

# 7. Human Approval and Notification

A capability that passes automated validation still does not automatically become active.

It enters:

```text
Pending Approval
```

The system then notifies an administrator.

The administrator may:

- Approve
- Reject
- Request Revision
- Approve With Restrictions

Notification and approval are deliberately separated:

```text
CapabilityReadyForReview
        ↓
Notification Service
        ↓
Administrator
        ↓
Approval Service
        ↓
Policy Engine
        ↓
Capability Registry
```

Future notification providers may include:

- Console
- Email
- Webhook
- Slack
- Microsoft Teams
- Mobile Push

---

# 8. Current Repository Structure

```text
Evolving_Agent_Architecture/
├── README.md
├── README.zh-TW.md
├── Capability-Evolving Agent Architecture — System Design v1.6.md
├── Capability_Evolving_Agent_Tech_Stack_v1.md
├── DEV_PLAN.md
├── PROJECT_STATUS.md
├── DEVELOPMENT_LOG.md
├── requirements.txt
├── env.example
├── pytest.ini
│
├── src/
│   ├── main.py
│   ├── config.py
│   │
│   ├── agents/
│   │   ├── main_agent.py
│   │   └── evolution_agent.py
│   │
│   ├── domain/
│   │   ├── capability.py
│   │   ├── gap.py
│   │   ├── report.py
│   │   ├── approval.py
│   │   └── events.py
│   │
│   ├── interfaces/
│   │   ├── llm.py
│   │   ├── queue.py
│   │   ├── sandbox.py
│   │   ├── notification.py
│   │   └── repository.py
│   │
│   ├── infrastructure/
│   │   ├── mock_llm.py
│   │   ├── memory_queue.py
│   │   ├── sqlite_repository.py
│   │   ├── subprocess_sandbox.py
│   │   └── console_notification.py
│   │
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
│   │
│   └── api/
│       └── routes/
│           ├── tasks.py
│           ├── capabilities.py
│           ├── evolution.py
│           ├── approvals.py
│           └── audit.py
│
└── tests/
    ├── test_capability_schema.py
    ├── test_capability_service.py
    └── test_full_loop.py
```

---

# 9. Current Phase 1 Implementation

The current implementation intentionally uses lightweight local adapters to validate architecture before introducing external infrastructure.

Current adapters:

| Interface | Phase 1 Implementation |
|---|---|
| LLM Provider | `MockLLMProvider` |
| Queue | `InMemoryEvolutionQueue` |
| Capability Repository | SQLite |
| Sandbox | Python subprocess |
| Notification | Console |

These are temporary implementations.

The intended long-term transition is:

```text
MockLLMProvider
→ LiteLLMProvider
→ NVIDIA NIM / OpenRouter / Local Provider
```

```text
SQLite
→ PostgreSQL
```

```text
SubprocessSandbox
→ DockerSandbox
→ stronger isolation if required
```

```text
InMemoryQueue
→ Redis / RQ
```

---

# 10. Current Technology Stack

Current code dependencies include:

- Python
- FastAPI
- Pydantic
- LangGraph
- pytest
- httpx
- SQLite

Planned technologies include:

### LLM Layer

- LiteLLM
- NVIDIA NIM
- OpenRouter
- future local OpenAI-compatible provider

### Persistence

- PostgreSQL
- pgvector

### Validation

- Docker
- future gVisor / Firecracker / Kata Containers if required

### Evaluation and Observability

- Arize Phoenix or equivalent
- DeepEval
- MLflow

### Background Processing

- Redis
- RQ

### UI

- Streamlit for research-stage dashboard
- formal admin UI for productization

---

# 11. Phase 1 Runtime Validation

Automated tests have been executed successfully: 25 passed, 1 existing dependency warning. This includes controlled races, 24 concurrent requests across two apps, and independent Python processes. It is not a production load benchmark.

Validation commands (in an environment with requirements installed):

```bash
pip install -r requirements.txt
pytest
```

Start API:

```bash
uvicorn src.main:app --reload
```

Then inspect:

```text
http://localhost:8000/docs
```

The automated suite covers the flow below. Repeat it against a standalone server and record the evidence before marking Phase 1 complete:

1. an unknown task creates a Capability Gap
2. the Evolution Agent creates a candidate Capability
3. validation executes successfully
4. autonomous testing produces a report
5. the Capability enters `pending_approval`
6. administrator approval activates it
7. a repeated task reuses the same Capability
8. no duplicate Capability is generated
9. audit records exist for review requests and approval decisions

---

# 12. Roadmap

## Phase 1 — Core MVP Skeleton

**Current stage**

- architecture skeleton
- Main Agent
- Evolution Agent
- lifecycle models
- validation abstraction
- testing abstraction
- approval
- notification
- audit
- API
- tests written

Still required:

- standalone Uvicorn / HTTP validation and retained runtime evidence
- long-running load and crash-recovery validation

---

## Phase 1.5 — Real Infrastructure Integration

Planned:

- LiteLLM adapter
- NVIDIA NIM
- OpenRouter
- PostgreSQL repository
- Docker sandbox
- improved autonomous tests

Goal:

> Replace mock infrastructure without changing core Agent logic.

---

## Phase 2 — Capability Retrieval and Reuse Intelligence

Planned:

- pgvector
- Embedding Provider
- semantic capability search
- compatibility filtering
- ranking
- duplicate prevention
- reuse metrics

Target flow:

```text
Task
 ↓
Embedding
 ↓
Capability Search
 ↓
Compatibility Filter
 ↓
Reuse or Gap
```

---

## Phase 3 — Research Evaluation and Observability

Planned:

- Agent tracing
- experiment tracking
- token / cost / latency metrics
- capability generation success rate
- capability reuse rate
- generalization rate
- regression rate
- repeated failure rate

Potential tools:

- Phoenix
- DeepEval
- MLflow

---

## Phase 4 — Background Evolution

Planned:

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

Possible stack:

- Redis
- RQ

This allows capability evolution to continue without blocking normal Agent execution.

---

## Phase 5 — Stronger Isolation

Potential future sandbox options:

- gVisor
- Firecracker
- Kata Containers
- VM-based validation

These will only be introduced when the risk profile requires stronger isolation.

---

## Phase 6 — Admin / Research Dashboard

Planned views:

- Capability Registry
- lifecycle state
- test reports
- pending approvals
- audit trail
- notifications
- reuse metrics
- cost / latency metrics

---

## Phase 7 — Local LLM Support

Future providers may include:

- Ollama
- llama.cpp
- vLLM
- LM Studio
- private OpenAI-compatible inference servers

The architecture intends to keep local and cloud models interchangeable through provider abstractions.

---

## Phase 8 — Enterprise Domain Validation

Potential controlled domains:

- file processing
- data transformation
- IT automation
- DevOps troubleshooting
- workflow automation
- enterprise procedures

Purpose:

> Verify that Capability Evolution generalizes across domains rather than working only for one task type.

---

## Phase 9 — Cybersecurity Extension

Cybersecurity is planned as a later high-difficulty validation domain rather than the initial MVP.

Possible components:

- MITRE ATT&CK
- Atomic Red Team
- Wazuh
- Sysmon
- Velociraptor
- Zeek
- Suricata
- CALDERA
- Cyber Range

The same lifecycle should remain:

```text
Generate
→ Validate
→ Test
→ Report
→ Human Approval
→ Activate
```

---

# 13. Future Reserved — Capability Sharing

Capability sharing is intentionally **not part of the current MVP**.

The architecture reserves space for future productization where users may choose whether to:

- share newly learned capabilities
- export capabilities
- import external capabilities
- discover community capabilities
- synchronize trusted capabilities

Potential future services:

```text
CapabilityImportService
CapabilityExportService
CapabilityPublishingService
CapabilityDiscoveryService
CapabilitySyncService
SharedCapabilityRegistry
```

Sharing must be opt-in.

Default principle:

```text
sharing_enabled = false
```

External capabilities must be considered untrusted until locally validated.

---

# 14. Future Capability Transfer Flow

Potential future publishing flow:

```text
Local Active Capability
       ↓
User Opt-In
       ↓
Privacy / Secret Scan
       ↓
Environment Neutralization
       ↓
Generalization Check
       ↓
Package
       ↓
Signature
       ↓
Shared Capability Registry
```

Potential acquisition flow:

```text
Shared Registry
      ↓
User Opt-In Download
      ↓
Signature Check
      ↓
Compatibility Check
      ↓
Local Sandbox Validation
      ↓
Testing Agent
      ↓
Local Test Report
      ↓
Administrator Approval
      ↓
Active Capability
```

A capability validated elsewhere is **not automatically trusted locally**.

---

# 15. Future Capability Marketplace

Long-term productization may include a Capability Marketplace supporting:

- private capabilities
- organization capabilities
- global capabilities
- verified publishers
- trust / reputation metadata
- version updates
- capability lineage
- forks
- revocation notices

Long-term concept:

```text
Agent A learns Capability X
        ↓
User chooses to share
        ↓
Shared Registry
        ↓
Agent B discovers X
        ↓
User chooses to acquire
        ↓
Local Validation
        ↓
Administrator Approval
        ↓
Agent B gains Capability X
```

This may enable:

> **Capability-level collective learning without exchanging model weights.**

---

# 16. Security and Governance Principles

The project is designed to preserve several governance boundaries from the beginning:

- generated capabilities are not automatically trusted
- new capabilities require validation
- new capabilities require human approval before activation
- external capabilities require local re-validation
- sharing is opt-in
- capability origin and lineage should be recorded
- capabilities must support revocation
- capability execution should move toward sandbox isolation
- important lifecycle actions should be auditable

Future enterprise and cybersecurity deployments may additionally require:

- digital signatures
- artifact integrity validation
- secret scanning
- tenant isolation
- stronger sandboxing
- role-based approval
- organization policy engines

---

# 17. Documentation

The repository uses separate documents for different project-management purposes.

| Document | Purpose |
|---|---|
| `README.md` | English project overview and entry point |
| `README.zh-TW.md` | Traditional Chinese project overview and entry point |
| `Capability-Evolving Agent Architecture — System Design v1.6.md` | Long-term system architecture and design principles |
| `Capability_Evolving_Agent_Tech_Stack_v1.md` | Technology stack and phased adoption plan |
| `DEV_PLAN.md` | Current implementation plan and replacement paths |
| `PROJECT_STATUS.md` | Current development stage, completion state, and milestones |
| `DEVELOPMENT_LOG.md` | Detailed development history, decisions, changes, and validation results |

The intended documentation rule is:

- Architecture decisions belong in the System Design
- Technology decisions belong in the Tech Stack
- Near-term work belongs in DEV_PLAN
- Current progress belongs in PROJECT_STATUS
- Actual historical development work belongs in DEVELOPMENT_LOG

---

# 18. Development Philosophy

The project intentionally avoids introducing all production infrastructure at once.

The development sequence is:

```text
Architecture Skeleton
        ↓
Verified Local MVP
        ↓
Real Infrastructure
        ↓
Semantic Capability Reuse
        ↓
Research Evaluation
        ↓
Background Evolution
        ↓
Enterprise Validation
        ↓
High-Risk Domain Validation
        ↓
Capability Sharing / Productization
```

The guiding principle is:

> **Implement simple, interface for complex.**

The objective is to keep the architecture evolvable without forcing premature infrastructure complexity.

---

# 19. Long-Term Vision

The long-term vision is not simply an Agent that can write tools.

It is an Agent system with a governed capability-learning lifecycle:

```text
Discover Gap
→ Learn
→ Build
→ Test
→ Explain
→ Govern
→ Activate
→ Reuse
```

Future productization may extend this into:

```text
Share
→ Discover
→ Transfer
→ Validate Locally
→ Adopt
```

The conceptual separation is:

### Foundation Model

Handles novel reasoning.

### Capability Library

Stores what the Agent has already learned how to do.

### Evolution Engine

Identifies what the Agent cannot yet do and attempts to create new capabilities.

### Testing Layer

Challenges generated capabilities and produces evidence.

### Governance Layer

Keeps humans in control of activation and sharing.

The research goal is to determine whether this architecture can enable an Agent to improve continuously through **validated capability accumulation**, without requiring continuous model retraining.

---

## Current Immediate Priority

The project is currently focused on one thing:

> **Verify the standalone API and retain runtime evidence for the already-tested core loop.**

See [DEV_PLAN.md](DEV_PLAN.md) for the remaining Phase 1 work before real infrastructure integration.
