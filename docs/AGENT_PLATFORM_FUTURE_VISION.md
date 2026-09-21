# Agent Platform — Future Productization Vision

> **Document Status:** Future Direction / Conceptual Target Architecture  
> **Version:** v0.2  
> **Current Relationship to CEAA:** This document does **not** redefine the current CEAA research scope. It describes a possible platform architecture that may be developed **after** the current research validates the capability-evolution hypothesis.

---

## 1. Purpose

The current Capability-Evolving Agent Architecture (CEAA) project is primarily a research prototype.

Its immediate goal is to validate whether an Agent can:

1. detect a capability gap,
2. generate a new executable capability,
3. validate and test that capability,
4. produce auditable evidence,
5. obtain human approval,
6. activate the capability, and
7. reuse it in future tasks.

The long-term platform direction described in this document is conditional on that research producing useful and reproducible results.

The intended evolution is:

```text
Research Hypothesis
        ↓
CEAA Prototype
        ↓
Runtime / Experiment Validation
        ↓
Quantitative Evaluation
        ↓
Capability Evolution Mechanism Confirmed
        ↓
Architecture Stabilization
        ↓
Agent Platform Productization
```

Therefore:

- **CEAA now = research and validation of capability evolution**
- **Agent Platform later = productization and system-level scaling of the validated mechanism**

This separation is intentional.

---

## 2. Long-Term Product Vision

The long-term goal is to build an Agent Platform that allows external applications and enterprise systems to consume Agent capabilities without having to independently manage:

- foundation-model providers,
- tool integrations,
- memory,
- workflow orchestration,
- permissions,
- credentials,
- sandboxing,
- audit,
- approval,
- retries,
- observability,
- and capability evolution.

External systems should be able to submit a standardized task and receive a governed result.

Conceptually:

```text
External System
      ↓
Access Layer
      ↓
Control Plane
      ↓
Agent Runtime
      ↓
Security & Governance
      ↓
Tool / Data Gateway
      ↓
Models / Tools / Data
```

CEAA may later become the platform's **Capability Evolution Engine**.

---

## 3. High-Level Architecture

```text
┌──────────────────────────────────────────────┐
│              External Systems               │
│                                              │
│  Horizon   News Map   Security Agent   SaaS  │
│  Internal Apps   Enterprise Systems   Apps   │
└──────────────────────┬───────────────────────┘
                       │
                 API / SDK / MCP
                       │
┌──────────────────────▼───────────────────────┐
│              Agent Platform                 │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │        Integration / Access Layer      │  │
│  │ REST API / SDK / MCP / Webhook / Event│  │
│  └───────────────────┬────────────────────┘  │
│                      │                       │
│  ┌───────────────────▼────────────────────┐  │
│  │          Agent Control Plane           │  │
│  │                                        │  │
│  │ Task Router                            │  │
│  │ Agent Registry                         │  │
│  │ Workflow / Multi-Agent Orchestration   │  │
│  │ Model Router                           │  │
│  │ State / Session Management             │  │
│  └───────────────────┬────────────────────┘  │
│                      │                       │
│  ┌───────────────────▼────────────────────┐  │
│  │          Agent Runtime Layer           │  │
│  │                                        │  │
│  │ Agent Execution                        │  │
│  │ Tool Calling                           │  │
│  │ Memory                                 │  │
│  │ Planning / Reasoning                   │  │
│  │ Retry / Recovery                       │  │
│  └───────────────────┬────────────────────┘  │
│                      │                       │
│  ┌───────────────────▼────────────────────┐  │
│  │     Capability Evolution Engine        │  │
│  │                                        │  │
│  │ Capability Search                      │  │
│  │ Gap Detection                          │  │
│  │ Capability Generation                  │  │
│  │ Validation / Testing                   │  │
│  │ Registry / Versioning                  │  │
│  │ Reuse / Deprecation / Revocation       │  │
│  └───────────────────┬────────────────────┘  │
│                      │                       │
│  ┌───────────────────▼────────────────────┐  │
│  │          Security & Governance         │  │
│  │                                        │  │
│  │ Policy Engine                          │  │
│  │ Permission Control                     │  │
│  │ Credential Vault                       │  │
│  │ Human Approval                         │  │
│  │ Sandbox                                │  │
│  │ Audit / Rollback                       │  │
│  └───────────────────┬────────────────────┘  │
│                      │                       │
│  ┌───────────────────▼────────────────────┐  │
│  │          Tool / Data Gateway           │  │
│  │                                        │  │
│  │ API / DB / Files / Browser / MCP       │  │
│  │ Cloud Services / Internal Systems      │  │
│  └───────────────────┬────────────────────┘  │
│                                              │
│  Cross-cutting: Observability / Cost / Trace │
└──────────────────────┼───────────────────────┘
                       │
┌──────────────────────▼───────────────────────┐
│        Models / Tools / Data Sources         │
│                                              │
│ OpenAI / Gemini / Claude / Local Models      │
│ DB / API / Cloud / Browser / Enterprise Data│
└──────────────────────────────────────────────┘
```

---

## 4. Architectural Principles

### 4.1 External Systems Must Not Depend on Internal Agent Details

An external application should not need to know:

- which model is being used,
- which Agent handles the task,
- which tools are called,
- how memory is stored,
- how retries are implemented,
- how capabilities are validated.

It should provide a standardized request such as:

```text
Task
Context
Required capability
Permission scope
Expected output
```

Example:

```text
Task:
Evaluate current global energy stress.

Permission:
Read-only external data.

Output:
Structured risk assessment.
```

---

### 4.2 Control Plane and Runtime Must Remain Separate

The Control Plane determines **how a task should be executed**.

The Runtime performs the actual execution.

```text
Control Plane
= decide what should happen

Runtime
= perform the work
```

This separation allows future scale-out into multiple workers and heterogeneous runtimes.

---

### 4.3 Agents Should Not Own Credentials

Agents should never directly receive long-lived production credentials.

Preferred flow:

```text
Agent
 ↓
Execution Grant / Temporary Capability Token
 ↓
Tool Gateway
 ↓
Credential Vault
 ↓
External API
```

A grant should be:

- task-scoped,
- capability-scoped,
- permission-scoped,
- time-limited,
- auditable,
- revocable.

Example:

```yaml
agent: macro_agent
task_id: TASK-123
expires_at: 2026-09-20T13:00:00Z

allow:
  - web.search
  - market_data.read

deny:
  - database.write
  - email.send
```

---

### 4.4 Security & Governance Is a Core Platform Capability

Governance should not be a late-stage add-on.

Every meaningful action may follow:

```text
Agent proposes action
       ↓
Policy Engine
       ↓
Permission Check
       ↓
Risk Classification
       ↓
Auto Execute
or
Human Approval
or
Deny
```

Example policy:

```yaml
agent: research_agent

allow:
  - web.search
  - database.read

approval_required:
  - email.send

deny:
  - database.delete
  - shell.admin
```

---

### 4.5 Tool Access Should Be Centralized

Agents should not independently integrate arbitrary external systems.

Preferred flow:

```text
Agent
 ↓
Tool / Data Gateway
 ↓
External System
```

The gateway centralizes:

- authentication,
- authorization,
- credentials,
- rate limiting,
- logging,
- cost tracking,
- timeout,
- retry,
- security scanning,
- input/output policy enforcement.

---

### 4.6 Observability Is Cross-Cutting

Observability should span every major subsystem rather than exist as an isolated layer.

Each task should eventually have identifiers such as:

```text
trace_id
task_id
session_id
agent_id
workflow_id
model_id
capability_id
tool_call_id
policy_decision_id
```

The platform should ultimately expose metrics such as:

- Task Success Rate
- Agent Success Rate
- Capability Reuse Rate
- Tool Failure Rate
- Model Cost
- Token Usage
- Latency
- Retry Count
- Human Approval Rate
- Security Alerts
- Rollback Count

---

## 5. Subsystem Definitions

### 5.1 Integration / Access Layer

Purpose:

> Provide stable external interfaces while hiding internal Agent implementation details.

Potential interfaces:

- REST API
- Python SDK
- TypeScript SDK
- MCP
- Webhook
- Event Bus
- Message Queue

Responsibilities:

- authentication,
- request validation,
- tenant resolution,
- task normalization,
- rate limiting,
- idempotency,
- response formatting.

---

### 5.2 Agent Control Plane

Purpose:

> Decide how an incoming task should be executed.

Potential responsibilities:

- Task Router
- Agent Registry
- Model Router
- Workflow Registry
- Multi-Agent Orchestration
- Session / State ownership
- Capability requirements
- Policy assignment
- resource allocation

Conceptual flow:

```text
Incoming Task
    ↓
Task Classification
    ↓
Choose Agent
    ↓
Choose Workflow
    ↓
Choose Model
    ↓
Assign Capabilities / Tools
    ↓
Apply Policy
    ↓
Dispatch Runtime
```

---

### 5.3 Agent Runtime

Purpose:

> Execute the task determined by the Control Plane.

Potential responsibilities:

- Agent Execution
- Planning
- Reasoning
- Memory
- State
- Tool Calling
- Retry
- Recovery
- Multi-Step Execution
- Checkpointing
- Runtime cancellation

LangGraph-type orchestration belongs here as one possible runtime implementation, not as the platform itself.

---

### 5.4 Capability Evolution Engine

Purpose:

> Allow the platform to accumulate validated, reusable capabilities.

This subsystem is the most direct future evolution of the current CEAA research.

Potential flow:

```text
Capability Search
      ↓
Capability Missing / Insufficient
      ↓
Gap Detection
      ↓
Generate Candidate
      ↓
Validate
      ↓
Autonomous Test
      ↓
Test Report
      ↓
Policy / Human Approval
      ↓
Activate
      ↓
Reuse
```

Possible future responsibilities:

- Capability Registry
- Versioning
- Provenance
- Compatibility
- Trust level
- Generalization evidence
- Regression testing
- Deprecation
- Revocation
- Rollback
- Sharing / Import / Export

The platform should only adopt this subsystem after the current CEAA research provides sufficient evidence that the mechanism is useful.

---

### 5.5 Security & Governance Plane

Purpose:

> Control what Agents and capabilities are allowed to do.

Potential components:

- Policy Engine
- Permission Service
- Credential Vault
- Human Approval
- Sandbox
- Audit
- Rollback
- Risk Classification
- Execution Grant Service

Core principle:

> Capability availability does not imply execution permission.

---

### 5.6 Tool / Data Gateway

Purpose:

> Provide a controlled boundary between Agents and external resources.

Potential adapters:

- REST API
- Database
- File Storage
- Browser
- MCP
- GitHub
- Email
- Calendar
- AWS / GCP / Azure
- Enterprise ERP / MES / CRM

The gateway should eventually support unified:

- policy enforcement,
- credential brokering,
- logging,
- quotas,
- timeout,
- retry,
- caching,
- cost measurement.

---

## 6. Current CEAA Mapping to the Future Platform

The current CEAA implementation can later map into platform components without redefining the current research scope.

| Current CEAA Component | Possible Future Platform Role |
|---|---|
| MainAgent | Runtime / early Control Plane boundary |
| EvolutionAgent | Capability Evolution Engine |
| CapabilityService | Capability Registry |
| TestingService | Capability Validation / Testing |
| ApprovalService | Governance Plane |
| PolicyService | Governance Plane |
| SubprocessSandbox | Security Plane prototype |
| FastAPI | Access Layer prototype |
| SQLite Repository | Persistence prototype |
| MockLLMProvider | Model Gateway placeholder |
| AuditService | Governance / Observability |
| ResearchMetricsService（feature candidate，尚未合併 dev） | Token/cost observability and experiment data foundation |

This mapping is directional, not a commitment to preserve the current implementation unchanged.

---

## 7. Reference Applications

The future platform may be validated through multiple reference applications rather than building separate Agent infrastructures for each project.

### 7.1 Horizon

Primary validation areas:

- complex reasoning,
- multi-agent orchestration,
- model routing,
- long-running analysis,
- structured decision output.

---

### 7.2 News Map

Primary validation areas:

- event-driven ingestion,
- information extraction,
- global data processing,
- continuous updates,
- external data integration.

---

### 7.3 Cybersecurity Evolution Agent

Primary validation areas:

- sandbox,
- policy enforcement,
- adversarial testing,
- rollback,
- permission boundaries,
- capability evolution under high-risk conditions.

These applications should consume platform capabilities rather than duplicate the platform internally.

---

## 8. Event-Driven Long-Running Agent Runtime

### 8.1 Why This Matters

As Agent systems evolve from short request/response interactions into long-running autonomous workflows, the platform must support execution that may last minutes, hours, or longer.

A simple synchronous pattern:

```text
External System
      ↓
Request
      ↓
Agent
      ↓
Final Response
```

is not sufficient for tasks that involve:

- multi-step planning,
- multiple tool calls,
- background execution,
- human approval,
- retries,
- partial failures,
- checkpoint / resume,
- multi-agent coordination,
- asynchronous external events,
- and long-running research or operational workflows.

The future platform should therefore treat Agent execution as an **event-driven runtime**, not merely an API request.

Conceptually:

```text
External System
      │
      ├── Control API / SDK / MCP
      │        │
      │        ▼
      │   Submit / Cancel / Resume Task
      │
      ▼
Agent Control Plane
      │
      ▼
Agent Runtime
      │
      ├── task.started
      ├── plan.created
      ├── tool.requested
      ├── tool.completed
      ├── approval.required
      ├── checkpoint.created
      ├── retry.scheduled
      ├── partial.result
      ├── task.failed
      └── task.completed
               │
               ▼
         Event Stream
               │
               ▼
        External Systems
```

The platform should separate:

```text
Control Interface
= submit, cancel, pause, resume, approve

Event Interface
= observe what is happening during execution
```

This allows external applications to interact with long-running Agents without blocking on a single synchronous response.

---

### 8.2 Event Stream as a First-Class Platform Interface

REST API, SDK, and MCP remain appropriate for task submission and control.

However, long-running execution may require additional runtime communication mechanisms such as:

- WebSocket,
- Server-Sent Events,
- gRPC streaming,
- message queues,
- event buses,
- or durable event logs.

The platform should not commit prematurely to one transport.

Instead, it should define a stable internal **Agent Event Model** and allow multiple transport adapters.

Example event envelope:

```json
{
  "event_id": "EVT-123",
  "task_id": "TASK-456",
  "trace_id": "TRACE-789",
  "agent_id": "research_agent",
  "type": "tool.completed",
  "timestamp": "2026-09-21T10:00:00Z",
  "payload": {}
}
```

Potential event categories:

```text
Lifecycle
  task.created
  task.started
  task.paused
  task.resumed
  task.cancelled
  task.completed
  task.failed

Planning
  plan.created
  plan.updated

Execution
  step.started
  step.completed
  tool.requested
  tool.completed
  tool.failed

Governance
  policy.checked
  approval.required
  approval.granted
  approval.denied

Reliability
  checkpoint.created
  retry.scheduled
  recovery.started
  rollback.started
  rollback.completed

Output
  partial.result
  artifact.created
  final.result
```

The event model should remain implementation-independent so that the runtime can later move between local execution, containers, distributed workers, or cloud-native infrastructure.

---

### 8.3 Durable State and Checkpointing

Long-running Agents should not depend on one in-memory process surviving for the entire task.

The platform should eventually support durable state transitions:

```text
Task State
   ↓
Checkpoint
   ↓
Persist
   ↓
Process Failure / Restart
   ↓
Recover
   ↓
Resume From Safe State
```

Potential checkpoint contents:

- current workflow node,
- completed steps,
- pending tool calls,
- Agent memory snapshot,
- intermediate artifacts,
- policy decisions,
- approval state,
- model / capability versions,
- retry metadata.

This creates a foundation for:

- crash recovery,
- worker migration,
- pause / resume,
- human-in-the-loop workflows,
- long-running jobs,
- reproducibility,
- audit,
- and controlled rollback.

---

### 8.4 Human Approval as an Asynchronous Runtime Event

Human approval should not be implemented as a blocking prompt inside an Agent process.

Preferred model:

```text
Agent proposes high-risk action
        ↓
Runtime emits approval.required
        ↓
Task enters WAITING_FOR_APPROVAL
        ↓
Human / Policy System responds
        ↓
approval.granted or approval.denied
        ↓
Runtime resumes from checkpoint
```

This makes approval compatible with:

- mobile interfaces,
- enterprise dashboards,
- asynchronous operations,
- external workflow systems,
- delayed human decisions,
- and distributed execution.

The same architecture can later support machine approval, organizational policy approval, or multi-party approval.

---

### 8.5 Reliability as a Research and Product Direction

The long-term research question is not only:

> Can an Agent autonomously complete a task?

A more important platform-level question is:

> **How can long-running autonomous Agents be executed as reliable, observable, controllable, and recoverable event-driven systems?**

This creates several future research directions:

1. **Event Model Design**  
   What is the minimum event schema required to represent Agent execution across heterogeneous runtimes?

2. **State and Checkpoint Semantics**  
   Which Agent states must be durable, and when is a checkpoint safe to resume?

3. **Failure Recovery and Rollback**  
   How should an Agent recover from model errors, tool failures, partial side effects, or worker crashes?

4. **Human-in-the-Loop Orchestration**  
   How should approval and intervention be represented without tightly coupling the runtime to a UI?

5. **Multi-Agent Event Coordination**  
   How should parent / child tasks, shared state, dependency events, and cancellation propagate across Agents?

6. **Observability and Replay**  
   Can event traces support debugging, reproducibility, post-incident analysis, and deterministic or semi-deterministic replay?

7. **Security Boundaries**  
   How should untrusted external events, tool outputs, and Agent-generated actions be validated before they influence future execution?

---

### 8.6 Relationship to Distributed Systems

This direction moves the platform into the intersection of:

```text
Agent Systems
      +
Workflow Engines
      +
Distributed Systems
      +
Security / Governance
      +
Event-Driven Architecture
```

The long-term differentiation of the platform does not need to be:

> "a smarter Agent."

It may instead be:

> **an infrastructure layer that allows autonomous Agents to run for long periods while remaining observable, governable, resumable, and safe.**

This is especially relevant once external systems depend on the platform for operational tasks rather than one-shot generation.

---

### 8.7 Possible Future Architecture Extension

The high-level architecture may eventually evolve from:

```text
External System
      ↓
API
      ↓
Agent
      ↓
Result
```

toward:

```text
                    External Systems
                     │            ▲
                     │            │
          Control API / SDK / MCP │ Event Stream
                     │            │
                     ▼            │
              Agent Control Plane
                     │
                     ▼
                 Runtime
           ┌─────────┼─────────┐
           │         │         │
       State     Checkpoint   Events
           │         │         │
           └─────────┼─────────┘
                     │
              Security / Policy
                     │
                     ▼
              Tool / Data Gateway
```

Possible technology candidates include:

- REST / MCP for control,
- gRPC streaming / WebSocket / SSE for live runtime events,
- Kafka / NATS / RabbitMQ / cloud queues for durable asynchronous events,
- PostgreSQL or event stores for durable state,
- distributed workers for runtime execution.

These are **technology candidates**, not current implementation decisions.

The platform should first define the required semantics and only then select infrastructure.

---

### 8.8 Reference Application Validation

The existing reference applications can validate this event-driven runtime from different angles.

**Horizon**

```text
Long-running research
→ multiple data sources
→ partial analysis
→ scenario updates
→ resumable execution
```

**News Map**

```text
Continuous external events
→ ingestion
→ classification
→ cross-event linking
→ map updates
```

**Cybersecurity Evolution Agent**

```text
Continuous monitoring
→ adversarial events
→ policy decisions
→ approval / containment
→ rollback / recovery
```

These use cases can serve as practical validation environments for the same shared runtime rather than creating separate execution models.

---

## 9. Research-to-Platform Development Path

### Stage 1 — Research Validation

Current focus.

Goal:

> Determine whether validated reusable capability accumulation improves Agent performance.

Key work:

- capability-gap detection,
- capability generation,
- validation,
- autonomous testing,
- human governance,
- activation,
- reuse,
- quantitative evaluation.

No requirement to build a complete platform.

---

### Stage 2 — Capability Evolution Engine

Only after positive research results.

Goal:

> Convert the research prototype into a stable engineering subsystem.

Potential work:

- stronger interfaces,
- PostgreSQL,
- semantic retrieval,
- Docker / stronger sandbox,
- background workers,
- observability,
- reliability,
- versioned capability artifacts,
- trust / compatibility.

---

### Stage 3 — Agent Platform Foundation

Goal:

> Build the minimum reusable platform around the validated evolution engine.

Suggested order:

1. Access Layer
2. Agent Control Plane
3. Runtime abstraction
4. Tool / Data Gateway
5. Security & Governance Plane
6. Observability
7. Capability Evolution Engine integration

---

### Stage 4 — Multi-Application Platform

Goal:

> Let multiple applications consume the same platform.

Reference applications:

- Horizon
- News Map
- Cybersecurity Agent
- other internal applications

---

### Stage 5 — Enterprise Productization

Possible future areas:

- multi-tenant architecture,
- tenant-specific policies,
- SSO / IAM,
- organization-level capability registries,
- billing / quotas,
- SLA / reliability,
- distributed runtime workers,
- managed deployment,
- enterprise connectors.

---

### Stage 6 — Capability Distribution

Long-term only.

Possible areas:

- capability import/export,
- shared registry,
- signed capability packages,
- organization sharing,
- opt-in public sharing,
- synchronization,
- marketplace,
- collective capability network.

All imported capabilities remain untrusted until locally validated.

---

## 10. Scope Boundary

This document must not be used to claim that the current CEAA implementation already provides an Agent Platform.

The following are **future concepts**, not current implementation claims:

- full Control Plane,
- Agent Registry,
- Model Router,
- multi-agent platform orchestration,
- SDK,
- MCP server,
- Credential Vault,
- distributed Tool Gateway,
- enterprise IAM,
- distributed runtime,
- multi-tenant platform,
- marketplace.

The current project should continue to prioritize research validation.

---

## 11. Decision Gate for Platformization

Platform development should begin only after sufficient evidence exists that the CEAA mechanism is worth productizing.

Suggested decision questions:

1. Does capability reuse measurably improve repeated-task performance?
2. Does Medium Model + Evolution approach or outperform stronger static baselines in relevant tasks?
3. Can generated capabilities generalize beyond the exact task that created them?
4. Can regression and failure rates be controlled?
5. Is human-review workload acceptable?
6. Can unsafe or low-quality capabilities be reliably blocked?
7. Is the cost of capability creation recovered through later reuse?
8. Does the capability library remain manageable as it grows?

If the answers are not satisfactory, research should continue before platform expansion.

---

## 12. Long-Term Architectural Summary

The long-term product concept can be summarized as:

```text
External Applications
        │
        ▼
Access Layer
        │
        ▼
Control Plane
        │
        ▼
Agent Runtime
        │
        ├──────── Capability Evolution Engine
        │
        ▼
Security & Governance
        │
        ▼
Tool / Data Gateway
        │
        ▼
Models / Tools / Data
```

And the project evolution as:

```text
CEAA Research
      ↓
Validated Capability Evolution
      ↓
Capability Evolution Engine
      ↓
Agent Platform
      ↓
Reference Applications
      ↓
Enterprise Productization
```

---

## 13. Current Recommendation

For now:

> **Do not expand the current CEAA implementation into the entire platform.**

Continue the current research until runtime, experimental, generalization, safety, and reuse evidence are strong enough to justify platformization.

This document should serve as the **starting architecture reference** when that transition begins.
