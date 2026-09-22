# Capability-Evolving Agent Architecture

**語言：** [English](README.md) | 繁體中文

![Status](https://img.shields.io/badge/status-experimental-orange)
![Phase](https://img.shields.io/badge/phase-1--verified-blue)
![Validation](https://img.shields.io/badge/automated%20tests-28%20passed-green)

> [!WARNING]
> 本實驗性研究原型已通過核心、API、併發自動化測試及獨立 Uvicorn/HTTP 驗證；認證、資料存取控制、執行限制強制套用與 production hardening 仍待完成，尚非 production-ready 系統。

這是一個研究導向的 Agent 架構，探索 AI Agent 是否能夠**辨識自身缺少的能力、建立新的可執行能力、進行驗證與測試、產生可稽核報告、請求人類核准、啟用通過的能力，並在未來任務中重複使用**。

長期目標是研究：Agent 的效能是否能透過 **Capability Accumulation（能力累積）**持續成長，而不只依賴更強的基礎模型。

---

## 專案狀態

> **目前階段（2026-09-20）：Phase 1 已驗證，並加入 Token／費用研究量測基礎**

目前 repository 已包含 Phase 1 MVP 所需的架構骨架、核心 domain model、service、interface、Agent orchestration、API route 與測試程式。

最近完整測試為 **28 passed**，另有一項既有 Starlette/AnyIO 棄用警告。除已驗證的 HTTP 與持久化流程外，Phase 1 現在會為 token efficiency／cost amortization 研究記錄 task 層級成本觀測與每次 LLM interaction；provider 未回報的 token 明確維持 unavailable，不以字數或其他方式估算。

詳見[專案狀態](PROJECT_STATUS.md)、[開發紀錄](DEVELOPMENT_LOG.md)及[API 併發行為](docs/API_CONCURRENCY.md)。下方架構圖包含長期設計：目前同步演化直接處理自己的 gap，queue 預留給未來背景 worker；報告、核准與 audit 已共用 SQLite 儲存。

[Token／費用研究契約](docs/TOKEN_COST_RESEARCH.md)已同步到 `dev`。程式實作及其 28 項
測試證據仍位於 `feature/token-cost-research`（`ca08851`），尚未合併；目前 `dev`
runtime 仍為 25 項測試，沒有 `/api/research/*` 路由。

目前狀態：

```text
設計文件                         ✓
架構骨架                         ✓
Main Agent                      ✓
Evolution Agent                 ✓
Capability lifecycle            ✓
Validation abstraction          ✓
Testing skeleton                ✓
Test report structure           ✓
Human approval flow             ✓
Notification abstraction        ✓
Audit skeleton                  ✓
FastAPI routes                  ✓
Unit / lifecycle tests          ✓
End-to-end test definition      ✓

pytest 實際執行                  28 passed
FastAPI TestClient 測試          Passed
Mock 核心循環                   Passed
獨立 Uvicorn / HTTP             Passed
Token／費用量測基礎              Passed
真實 Provider Usage 資料         Pending
真實 LLM 整合                    Pending
PostgreSQL runtime adapter      Pending
Docker sandbox                  Pending
Semantic retrieval              Pending
Observability                   Pending
Background workers              Pending
Capability sharing              Future Reserved
Marketplace                     Future Reserved
```

下一個研究里程碑是：

> **真實 provider token／費用擷取與受控 baseline 比較**

完整 mock 流程與獨立伺服器路徑皆已通過；Phase 1 現在也會保存比較首次建立與後續重用所需的量測資料：

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
→ 持久化 LLM interaction 與 task cost metrics
→ 以明確 baseline 比較 cumulative CEAA usage
```

量測語意、API 與 Phase 1 基礎／Phase 3 正式實驗的邊界，見
[Token／費用研究量測](docs/TOKEN_COST_RESEARCH.md)。

---

# 1. 研究動機

目前多數 Agent 系統主要透過以下方式提升能力：

- 更強的語言模型
- 人工加入工具
- Workflow 重構
- Prompt Engineering
- Memory
- RAG
- 模型 Fine-tuning

本專案希望探索另一個成長維度：

## Capability Scaling

核心研究假說是：

> **即使底層模型保持不變，Agent 仍可能透過累積經驗證、可重用的能力而持續提升。**

本架構將兩種成長機制分開：

### Model Scaling

提升 Agent 面對未知問題時的推理能力。

### Capability Scaling

提升 Agent 重複使用過去已學會、已驗證解法的能力。

未來可能設計下列比較實驗：

| Group | Model | Capability Evolution |
|---|---|---|
| A | Strong | No |
| B | Medium | No |
| C | Medium | Yes |
| D | Strong | Yes |

核心研究問題之一是：

> **Medium Model + Capability Evolution**

是否能在重複任務或長期任務中接近甚至超過：

> **Strong Model + Static Capabilities**

---

# 2. 核心概念

本架構將 **Capability** 視為一等系統物件（first-class system object）。

Capability 並不只是 Prompt 或 Memory，而應具備：

- 可執行
- 可檢查
- 可測試
- 可版本管理
- 可稽核
- 可重用
- 可回滾
- 可攜移

未來 Capability 可能代表：

- Python 程式碼
- API Workflow
- Tool Sequence
- Data Processing Pipeline
- Agent Workflow
- Containerized Service
- Domain-specific Procedure
- Enterprise Automation
- Security Detection / Response Logic

核心循環：

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

# 3. 高階系統架構

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

本架構遵守一個核心邊界原則：

> **Agent logic 不應直接依賴具體 Infrastructure implementation。**

建議依賴方向：

```text
Agent
→ Service
→ Interface
→ Infrastructure Adapter
```

而不是：

```text
Agent
→ Database / Docker / Vendor API
```

---

# 4. 核心設計原則

## Capability First

長期真正累積的系統資產是 Capability Library，而不只是對話紀錄。

## Validation Before Activation

新產生的 Capability 不得立即啟用。

必須先通過驗證與測試。

## Human-Governed Evolution

Agent 可以自主建立與測試 Capability，但新能力第一次正式啟用前仍需要管理員核准。

## Model Independent

Agent 架構不得綁定單一模型供應商。

## Infrastructure Independent

核心邏輯應與 PostgreSQL、Docker、Redis、NVIDIA NIM、OpenRouter 或任何特定 framework implementation 解耦。

## Implement Simple, Interface for Complex

早期 implementation 可以簡單，但 interface 必須保留未來擴充能力。

## Everything Is Versioned

規劃版本化的物件包括：

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

未來匯入的外部 Capability，在本地驗證完成之前一律視為不受信任。

---

# 5. Capability Lifecycle

規劃生命週期：

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

如果測試失敗：

```text
Testing
 ↓
Failed
 ↓
Evolution Queue
```

如果管理員要求修改：

```text
Pending Approval
 ↓
Revision Requested
 ↓
Evolution Queue
```

---

# 6. 自主測試與 Test Report

Testing 與 Capability Generation 刻意分離。

Evolution Agent 負責建立 Capability。

Testing Agent 負責挑戰 Capability，嘗試找出它可能失敗的地方。

規劃中的測試類型包括：

- Functional Test
- Boundary Test
- Failure Test
- Regression Test
- Generalization Test
- Safety Test
- Performance Test

每一個 Capability version 預期產生：

```text
test_report.json
```

以及：

```text
test_report.md
```

Test Report 未來應包含：

- Capability ID 與版本
- 測試環境
- Test Cases
- Pass Rate
- Failed Cases
- Regression Result
- Generalization Score
- Safety Result
- Performance Metrics
- Known Limitations
- Risk Level
- Recommended Action

---

# 7. Human Approval 與 Notification

即使 Capability 通過自動驗證，也不會自動進入 Active。

它會先進入：

```text
Pending Approval
```

接著系統通知管理員。

管理員可以：

- Approve
- Reject
- Request Revision
- Approve With Restrictions

Notification 與 Approval 被刻意分離：

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

未來 Notification Provider 可包括：

- Console
- Email
- Webhook
- Slack
- Microsoft Teams
- Mobile Push

---

# 8. 目前 Repository 結構

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

# 9. 目前 Phase 1 Implementation

目前 implementation 刻意使用較輕量的 local adapter，先驗證架構，再導入外部 infrastructure。

目前 adapter：

| Interface | Phase 1 Implementation |
|---|---|
| LLM Provider | `MockLLMProvider` |
| Queue | `InMemoryEvolutionQueue` |
| Capability Repository | SQLite |
| Sandbox | Python subprocess |
| Notification | Console |

以上皆為暫時 implementation。

預計長期轉換路徑：

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

# 10. 目前技術棧

目前程式依賴包括：

- Python
- FastAPI
- Pydantic
- LangGraph
- pytest
- httpx
- SQLite

規劃中的技術包括：

### LLM Layer

- LiteLLM
- NVIDIA NIM
- OpenRouter
- 未來本地 OpenAI-compatible Provider

### Persistence

- PostgreSQL
- pgvector

### Validation

- Docker
- 未來視需求加入 gVisor / Firecracker / Kata Containers

### Evaluation and Observability

- Arize Phoenix 或同等工具
- DeepEval
- MLflow

### Background Processing

- Redis
- RQ

### UI

- 研究階段使用 Streamlit
- 商品化後使用正式 Admin UI

---

# 11. Phase 1 Runtime Validation

自動化測試已實際通過：28 passed，另有一項既有套件警告。包含受控競爭、跨兩個 app 的 24 請求併發、獨立 Python 程序，以及 Token／費用量測持久化與 amortization 計算；不代表 production 負載基準，也不代表目前 Mock provider 已證明可節省真實 token。

驗證指令（在已安裝相依套件的環境中）：

```bash
pip install -r requirements.txt
pytest
```

啟動 API：

```bash
uvicorn src.main:app --reload
```

然後查看：

```text
http://localhost:8000/docs
```

自動化套件已涵蓋以下流程；需再對獨立伺服器操作並保存證據，才標記 Phase 1 完成：

1. 未知任務建立 Capability Gap
2. Evolution Agent 建立 Candidate Capability
3. Validation 成功執行
4. Autonomous Testing 產生 Test Report
5. Capability 進入 `pending_approval`
6. 管理員核准後 Capability 進入 `active`
7. 相同類型任務能重用既有 Capability
8. 不會為重複任務建立重複 Capability
9. 送審與核准決策留有 Audit Record

---

# 12. Roadmap

## Phase 1 — Core MVP Skeleton

**目前階段**

已建立：

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

尚需完成：

- 獨立 Uvicorn / HTTP 驗證及 runtime 證據留存
- 長時間負載與程序中止復原驗證

---

## Phase 1.5 — Real Infrastructure Integration

規劃：

- LiteLLM adapter
- NVIDIA NIM
- OpenRouter
- PostgreSQL repository
- Docker sandbox
- 更完整的 autonomous tests

目標：

> 在不修改核心 Agent logic 的情況下，把 mock infrastructure 替換成真實 infrastructure。

---

## Phase 2 — Capability Retrieval and Reuse Intelligence

規劃：

- pgvector
- Embedding Provider
- semantic capability search
- compatibility filtering
- ranking
- duplicate prevention
- reuse metrics

目標流程：

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

規劃：

- Agent tracing
- experiment tracking
- token / cost / latency metrics
- capability generation success rate
- capability reuse rate
- generalization rate
- regression rate
- repeated failure rate

可能使用：

- Phoenix
- DeepEval
- MLflow

---

## Phase 4 — Background Evolution

規劃：

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

可能使用：

- Redis
- RQ

這讓 Capability Evolution 不會阻塞正常 Agent 執行。

---

## Phase 5 — Stronger Isolation

未來可能的 Sandbox：

- gVisor
- Firecracker
- Kata Containers
- VM-based validation

只有在風險需求提高時才導入更強隔離。

---

## Phase 6 — Admin / Research Dashboard

規劃畫面：

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

未來可能支援：

- Ollama
- llama.cpp
- vLLM
- LM Studio
- Private OpenAI-compatible inference server

架構目標是透過 Provider abstraction，讓 local 與 cloud model 可以互換。

---

## Phase 8 — Enterprise Domain Validation

可能的受控領域：

- File Processing
- Data Transformation
- IT Automation
- DevOps Troubleshooting
- Workflow Automation
- Enterprise Procedures

目的：

> 驗證 Capability Evolution 是否能跨領域泛化，而不是只適用於單一任務類型。

---

## Phase 9 — Cybersecurity Extension

Cybersecurity 被規劃為後期高難度驗證領域，而不是初始 MVP。

可能元件：

- MITRE ATT&CK
- Atomic Red Team
- Wazuh
- Sysmon
- Velociraptor
- Zeek
- Suricata
- CALDERA
- Cyber Range

核心 lifecycle 應保持：

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

Capability Sharing **刻意不納入目前 MVP**。

架構先預留未來商品化後，讓使用者可以自行選擇是否：

- 分享新學到的 Capability
- Export Capability
- Import 外部 Capability
- Discover Community Capability
- 同步 Trusted Capability

未來可能的 service：

```text
CapabilityImportService
CapabilityExportService
CapabilityPublishingService
CapabilityDiscoveryService
CapabilitySyncService
SharedCapabilityRegistry
```

分享必須採 opt-in。

預設原則：

```text
sharing_enabled = false
```

所有外部 Capability 在本地驗證前都必須視為不受信任。

---

# 14. 未來 Capability Transfer Flow

可能的 Publish 流程：

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

可能的取得流程：

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

即使 Capability 已在其他環境通過驗證，也**不代表在本地可以直接信任**。

---

# 15. 未來 Capability Marketplace

長期商品化可能包含 Capability Marketplace，支援：

- private capabilities
- organization capabilities
- global capabilities
- verified publishers
- trust / reputation metadata
- version updates
- capability lineage
- forks
- revocation notices

長期概念：

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

這可能形成：

> **不交換模型權重的 Capability-level collective learning。**

---

# 16. Security 與 Governance 原則

本專案從一開始就保留以下治理邊界：

- generated capability 不會自動被信任
- 新 capability 必須經過 validation
- 新 capability 啟用前必須經過 human approval
- external capability 必須重新做 local validation
- sharing 採 opt-in
- capability origin 與 lineage 應被保存
- capability 必須支援 revocation
- capability execution 應逐步移往 sandbox isolation
- 關鍵 lifecycle action 必須可稽核

未來 Enterprise 與 Cybersecurity deployment 可能另外需要：

- digital signatures
- artifact integrity validation
- secret scanning
- tenant isolation
- stronger sandboxing
- role-based approval
- organization policy engines

---

# 17. 文件管理

Repository 以不同文件負責不同的專案管理用途。

| 文件 | 用途 |
|---|---|
| `README.md` | 英文專案入口與總覽 |
| `README.zh-TW.md` | 繁體中文專案入口與總覽 |
| `Capability-Evolving Agent Architecture — System Design v1.6.md` | 長期系統架構與設計原則 |
| `Capability_Evolving_Agent_Tech_Stack_v1.md` | 技術棧與分階段導入規劃 |
| `DEV_PLAN.md` | 目前 implementation plan 與替換路徑 |
| `PROJECT_STATUS.md` | 目前開發階段、完成狀態與里程碑 |
| `DEVELOPMENT_LOG.md` | 詳細開發歷程、決策、修改與驗證結果 |

文件維護原則：

- Architecture decision → System Design
- Technology decision → Tech Stack
- 近期工作 → DEV_PLAN
- 目前進度 → PROJECT_STATUS
- 已實際發生的歷史開發 → DEVELOPMENT_LOG

---

# 18. Development Philosophy

本專案刻意避免一開始就導入所有 Production Infrastructure。

開發順序：

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

核心原則：

> **Implement simple, interface for complex.**

目標是在不過早增加 infrastructure complexity 的前提下，讓架構仍能持續演進。

---

# 19. 長期願景

長期目標並不只是建立一個「會自己寫工具的 Agent」。

而是建立具有完整治理能力的 Capability Learning Lifecycle：

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

未來商品化後可能再延伸：

```text
Share
→ Discover
→ Transfer
→ Validate Locally
→ Adopt
```

概念上的分工：

### Foundation Model

負責面對新的、未知的問題進行推理。

### Capability Library

保存 Agent 已經學會如何完成的事情。

### Evolution Engine

辨識 Agent 還不會的事情，並嘗試建立新的 Capability。

### Testing Layer

挑戰新產生的 Capability，並產生可驗證的 evidence。

### Governance Layer

讓人類保有對 Capability 啟用與分享的最終控制權。

本研究最終希望驗證：

> Agent 是否能在不持續重新訓練模型的情況下，透過**經驗證的 Capability 累積**持續提升自身能力。

---

## 目前立即優先事項

目前專案只應優先處理一件事：

> **驗證獨立 API，為已通過自動化測試的核心流程補齊 runtime 證據。**

實際 infrastructure 整合前的 Phase 1 收尾工作見 [DEV_PLAN.md](DEV_PLAN.md)。


---

## 使用授權

本 Repository 公開的主要目的為 **求職作品集展示、研究交流、技術評估與教育性檢視**。

本專案採 **Source-Available（原始碼可見）** 授權，**不是一般意義上的 Open Source License**。你可以閱讀、研究，並在個人、教育、研究或評估用途下於本機執行程式；若要用於商業正式環境、重新散布、再授權、提供 Hosted Service，或作為競爭性商業產品的基礎，需另行取得著作權人書面授權。

完整條款請見 [LICENSE](LICENSE)。

第三方函式庫、模型、API、資料集與其他依賴項目，仍分別受其原有授權與使用條款約束。

