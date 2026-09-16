# Capability-Evolving Agent 技術棧與分階段安裝規劃

## 1. 目前本機條件

### 硬體
- CPU：Intel Core i5-14600K
- RAM：DDR4 80 GB
- GPU：AMD RX 6650 XT
- GPU 不納入主要 LLM 推理路徑

### 已安裝
- LangGraph
- PostgreSQL
- FastAPI
- Git
- Docker

### 推理策略
- Cloud-first
- Primary：NVIDIA NIM
- Secondary：OpenRouter
- 保留 Local LLM Provider 介面

---

# 2. 核心技術棧

## 2.1 開發語言

### 首選
- Python

### 主要用途
- Agent logic
- Evolution Engine
- Capability Builder
- Validation
- LLM Gateway
- Experiment Controller
- Backend API
- Evaluation

第一階段不需要另外加入其他主要語言。

---

## 2.2 Agent Orchestration

### 已安裝
- LangGraph

### 主要用途
- Main Agent
- Capability Gap Detector
- Evolution Agent
- Validator Agent
- Judge / Evaluator
- State transition
- Retry / fallback
- Human approval

目前不建議再加入 CrewAI 或 AutoGen，以避免框架重疊。

---

## 2.3 API / Service Layer

### 已安裝
- FastAPI

### 主要用途
- Agent API
- Capability API
- LLM Gateway API
- Validation API
- Experiment API

建議 API 結構：

```text
/api/tasks
/api/capabilities
/api/evolution
/api/validation
/api/models
/api/experiments
```

---

## 2.4 Structured Data Database

### 已安裝
- PostgreSQL

### 主要儲存內容
- Task
- Agent run
- Capability metadata
- Capability version
- Validation result
- Experiment
- Failure record
- Capability Gap
- Model usage
- Cost / latency
- Reuse history

### 後續擴充
- pgvector

用途：

> 找出以前是否已經學過類似能力。

流程：

```text
New Task
   ↓
Embedding
   ↓
Capability Similarity Search
   ↓
Existing Capability?
```

MVP 階段不需要額外部署 Qdrant 或 Chroma。

---

## 2.5 Capability Artifact Store

### 已安裝
- Git

建議獨立建立：

```text
capability-library/
```

目錄結構：

```text
capabilities/
├── CAP-0001/
│   ├── manifest.yaml
│   ├── implementation.py
│   ├── tests/
│   ├── validation.json
│   └── README.md
│
├── CAP-0002/
└── CAP-0003/
```

分工：

- PostgreSQL：管理 Capability metadata
- Git：管理實際 executable artifact 與版本

---

## 2.6 Capability Schema

這是目前最優先需要定義的核心元件。

### 建議技術
- Pydantic
- JSON Schema
- YAML

Capability 建議欄位：

```text
Capability
├── ID
├── Name
├── Description
├── Inputs
├── Outputs
├── Preconditions
├── Dependencies
├── Implementation
├── Validation
├── Safety
├── Version
└── Status
```

範例：

```yaml
id: CAP-0001
name: csv_column_summary
version: 1.0.0

inputs:
  - csv_file

outputs:
  - statistics

implementation:
  type: python
  entrypoint: main.py

dependencies:
  - pandas

validation:
  minimum_success_rate: 0.9

status: validated
```

---

# 3. LLM Layer

## 3.1 LLM Gateway

### 建議新增
- LiteLLM

主要功能：
- NVIDIA NIM
- OpenRouter
- Provider fallback
- Retry
- Rate limit
- Cost tracking
- OpenAI-compatible API

建議架構：

```text
Agent
  ↓
Internal LLM Gateway
  ↓
LiteLLM
  ├── NVIDIA NIM
  ├── OpenRouter
  └── Local Provider
```

Agent 不應直接綁定特定模型供應商。

---

## 3.2 Cloud LLM Provider

### Primary
- NVIDIA NIM

主要用途：
- Evolution Agent
- Capability generation
- Complex reasoning
- Judge
- Failure analysis

### Secondary
- OpenRouter

主要用途：
- Free model fallback
- Model comparison
- Benchmark
- NVIDIA endpoint unavailable 時備援

### Optional
後續有需要再加入：
- Groq
- Gemini
- Mistral

第一版不需要全部接入。

---

## 3.3 Local LLM Adapter

目前只需要保留接口，不需要真的部署大型本地模型。

### 建議接口
- OpenAI-compatible API

未來可接：
- Ollama
- llama.cpp
- vLLM
- LM Studio
- Private inference server

目前 RX 6650 XT 不需要納入主要 LLM 推理設計。

---

# 4. Validation Layer

## 4.1 Validation Sandbox

### 已安裝
- Docker

第一階段 Docker 足夠驗證低風險 Capability，例如：
- Python code
- File transformation
- CSV processing
- JSON processing
- API workflow
- Document processing

基本流程：

```text
Candidate Capability
        ↓
Build Temporary Container
        ↓
Run Test Cases
        ↓
Collect Result
        ↓
Destroy Container
```

### 後續高風險隔離選項
- gVisor
- Firecracker
- Kata Containers

目前不需要安裝。

---

## 4.2 Capability Evaluation

### 第一階段
- pytest

用途：
- Deterministic test
- Functional correctness
- Regression test
- Input/output verification

原則：

> 能用 deterministic ground truth 驗證，就不要優先依賴 LLM Judge。

### 第二階段
- DeepEval

用途：
- LLM output evaluation
- Agent behavior evaluation
- Trajectory evaluation
- Semantic quality

---

# 5. Observability 與 Experiment Tracking

## 5.1 Agent Observability

### 建議第二階段加入
- Arize Phoenix

替代方案：
- Langfuse

主要記錄：
- Agent path
- LLM calls
- Prompt
- Tool call
- Latency
- Token
- Failure
- Capability selected
- Capability generated

研究導向優先建議 Phoenix。

---

## 5.2 Experiment Tracking

### 建議第三階段加入
- MLflow

紀錄：

```text
Experiment ID
Model
Agent Version
Capability Library Version
Task Set
Success Rate
Token Cost
Latency
Seed
Validation Result
```

角色區分：

- Phoenix：看 Agent 怎麼跑
- MLflow：比較不同實驗結果

---

# 6. Evolution Queue

## 初期

直接使用 PostgreSQL table 即可。

狀態範例：

```text
pending
analyzing
generating
validating
approved
rejected
```

## 後續需要背景工作時

加入：
- Redis
- RQ

架構：

```text
Main Agent
   ↓
Capability Gap
   ↓
Queue
   ↓
Evolution Worker
```

再更大型時才考慮：
- Celery
- Dramatiq

---

# 7. Artifact Storage

## 初期
- Local filesystem

適合存放：
- Test data
- Validation logs
- Generated artifacts
- Benchmark data
- Agent outputs

## 後期
- MinIO

適合：
- S3-compatible object storage
- 大量 artifact
- Experiment dataset
- Validation output

目前不需要安裝。

---

# 8. UI / Dashboard

## 第一階段
不需要專用 UI。

可先使用：
- CLI
- FastAPI Swagger
- Logs
- PostgreSQL

## 後期
- Streamlit

可顯示：
- Capability Library Size
- Task Success Rate
- Capability Generated
- Reuse Rate
- Validation Pass Rate
- Model Cost
- Generalization Rate

---

# 9. Secrets Management

## 初期
使用：

```text
.env
+
.gitignore
```

儲存：
- NVIDIA API Key
- OpenRouter API Key

## 後續
可升級為：
- SOPS
- Infisical
- HashiCorp Vault

---

# 10. 最終建議架構

```text
                        Cloud
                          │
                ┌─────────┴─────────┐
                │                   │
            NVIDIA NIM         OpenRouter
                │                   │
                └─────────┬─────────┘
                          │
                     LiteLLM
                          │
                   LLM Gateway
                          │
══════════════════════════════════════════

                     FastAPI
                        │
                     LangGraph
                        │
       ┌────────────────┼─────────────────┐
       │                │                 │
  Main Agent       Gap Detector     Evolution Agent
       │                                  │
       │                           Capability Builder
       │                                  │
       └──────────────┐                   │
                      ▼                   ▼
                Capability Library     Validator
                      │                   │
              PostgreSQL + pgvector     Docker
                      │                   │
                      └───────┬───────────┘
                              │
                             Git
```

後續逐步加入：

```text
Phoenix
MLflow
pytest
DeepEval
Redis / RQ
```

---

# 11. 分階段安裝規劃

## Phase 0 — 已完成

本機目前已有：

- LangGraph
- PostgreSQL
- FastAPI
- Git
- Docker

這些已足夠開始開發核心系統。

---

## Phase 1 — MVP 必裝

### 目標
先讓 Agent 能建立一項新能力。

### 建議新增
- LiteLLM
- pytest
- NVIDIA NIM API 設定
- OpenRouter API 設定

### 同時確認
- Pydantic

FastAPI 通常已經依賴 Pydantic，但仍建議確認版本。

### 開發內容
- Capability Schema
- Main Agent
- Evolution Agent
- Validator
- 基礎 Capability Library

---

## Phase 2 — Capability Retrieval

### 目標
讓新任務可以找到並重用既有 Capability。

### 新增
- pgvector
- Embedding Provider

### 開發內容

```text
Task
  ↓
Semantic Search
  ↓
Existing Capability
  ↓
Reuse
```

---

## Phase 3 — Research Evaluation

### 目標
正式比較 Evolution 前後差異。

### 新增
- Arize Phoenix
- DeepEval
- MLflow

### 分工

```text
Phoenix
→ Agent tracing

pytest / DeepEval
→ Quality evaluation

MLflow
→ Experiment comparison
```

---

## Phase 4 — Background Evolution

### 目標
Evolution 不再阻塞 Main Agent。

### 新增
- Redis
- RQ

架構：

```text
Main Agent
   ↓
Capability Gap
   ↓
Evolution Queue
   ↓
Evolution Worker
```

---

## Phase 5 — Stronger Sandbox

### 目標
允許驗證更高風險、不可信程式碼。

### 擇一加入
- gVisor
- Firecracker
- Kata Containers

不需要全部安裝。

一般低風險 Capability 仍使用 Docker。

---

## Phase 6 — Research Dashboard

### 新增
- Streamlit

### 主要顯示
- Capability Growth
- Task Success Rate
- Reuse Rate
- Generalization
- Validation Rate
- Token Cost
- Model Comparison

---

## Phase 7 — Local LLM

目前不需要執行。

等未來硬體升級或需要 local-only inference 時，再擇一加入：

- Ollama
- vLLM
- llama.cpp

目前只需要先保留：

```text
LocalLLMProvider
```

介面。

---

## Phase 8 — Enterprise Domain Extension

當 Capability-Evolving Agent 核心架構驗證成功後，再加入企業場景，例如：

- IT Support
- DevOps troubleshooting
- Data Pipeline Recovery
- Workflow Automation
- Internal Ticket Handling

---

## Phase 9 — Cybersecurity Extension

只有通用 Capability-Evolving Agent 驗證成立後，再建立資安實驗環境。

可能新增：
- Wazuh
- Sysmon
- Velociraptor
- Atomic Red Team
- Zeek
- Suricata
- MITRE CALDERA
- Proxmox / Hyper-V Cyber Range

這些目前全部可以暫緩。

---

# 12. 現階段真正需要新增的項目

第一階段建議只增加：

```text
LiteLLM
pytest
NVIDIA NIM API
OpenRouter API
```

然後直接開始完成：

```text
Capability Schema
        ↓
Capability Gap Detection
        ↓
Evolution Agent
        ↓
Validation
        ↓
Capability Library
        ↓
Reuse
```

目前最重要的研究問題不是工具是否足夠，而是：

> **Agent 是否真的可以自行發現能力缺口、建立新的 Capability、驗證並保存，並在後續任務中重複使用。**
