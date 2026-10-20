# Capability-Evolving Agent Architecture
## 可持續能力演化代理人架構
### System Design v1.9

---

# 1. 專案定位

Capability-Evolving Agent Architecture 的核心目標，是建立一種能隨實際使用經驗持續擴展自身能力集合的 Agent 架構。

研究初期不綁定資安、DevOps、企業自動化或其他特定領域，而是先驗證：

> **Agent 是否能辨識自己的能力缺口，自主建立新能力，自主測試與驗證，產生可稽核報告，在管理員確認後正式啟用，並於後續任務重新使用？**

核心循環：

```text
Problem
  ↓
Capability Gap
  ↓
Generate
  ↓
Validate
  ↓
Autonomous Test
  ↓
Test Report
  ↓
Notify Administrator
  ↓
Human Approval
  ↓
Activate
  ↓
Reuse
```

未來商品化後，再進一步擴展：

```text
Local Capability
      ↓
Optional Publish
      ↓
Shared Capability Registry
      ↓
Optional Discovery / Download
      ↓
Local Validation
      ↓
Administrator Approval
      ↓
Local Agent
```

---

# 2. 核心研究假說

傳統 Agent 的能力通常主要來自：

- 底層模型
- 人類提供的工具
- Workflow
- Prompt
- Memory
- RAG

本研究增加另一條成長軸：

## Capability Scaling

底層模型負責：

> 面對未知問題時思考。

Capability Library 負責：

> 保存已經學會如何完成的工作。

Evolution Engine 負責：

> 找出還不會的事情，並嘗試建立能力。

Testing Agent 負責：

> 主動挑戰新能力，確認其可靠程度。

Human Governance 負責：

> 決定新能力是否能正式進入 Agent。

未來 Shared Capability Network 則負責：

> 讓經過允許的能力可以跨 Agent 傳遞。

## 2.1 Experience-to-Capability：將解題經驗固化為可執行能力

本研究進一步將 Capability Evolution 視為一種 **Executable Experience / Procedural Memory** 機制。

一般 Agent 的一次任務通常是：

```text
Problem
→ Reason
→ Use Tools
→ Answer
→ End
```

若下一次再次遇到相同或相似問題，系統可能重新進行大部分推理與工具規劃。

CEAA 的研究假說則是：

```text
Episode
  ↓
Problem-Solving Experience
  ↓
Validated Capability
  ↓
Capability Library
  ↓
Future Reuse
```

也就是：

> **將 Agent 的問題解決經驗轉換為經驗證、可重複使用的可執行能力。**

因此 Capability Library 不只保存「發生過什麼」，而是保存：

- 遇到這類問題時可以怎麼處理
- 需要哪些輸入與工具
- 應執行哪些步驟
- 有哪些限制與風險
- 如何驗證執行結果
- 過去實際使用的成功與失敗證據

這與一般 Conversation Memory / Episodic Memory 不同。

CEAA 更接近：

> **Executable Procedural Memory**

長期可形成：

```text
Task
 ↓
Retrieve Experience / Capability
 ↓
Execute
 ↓
Observe Outcome
 ↓
Update Evidence
 ↓
Evolve if Needed
```

Capability 本身也應累積後續使用證據，例如：

```text
reuse_count
success_count
failure_count
generalization_count
last_used_at
average_latency
average_token_cost
revision_count
```

這些欄位是否直接進入 Capability Schema，可在研究實作階段依需要逐步加入。

## 2.2 Token Efficiency / Cost Amortization Hypothesis

Capability Evolution 的第一次學習成本預期可能高於一般單次 LLM 解題，因為第一次需要額外執行：

```text
Gap Detection
→ Capability Generation
→ Validation
→ Testing
→ Report
→ Approval
→ Store
```

但若 Capability 可以在後續相同或相似任務中被重複使用，則預期：

```text
Retrieve Capability
→ Execute
→ Lightweight Validation
→ Return Result
```

所需的重複推理、規劃、程式生成與驗證成本會降低。

因此本研究新增成本假說：

> **H-cost: Reusable evolved capabilities may incur a higher initial creation cost, but reduce average token consumption and inference cost over repeated or related tasks compared with solving every task from scratch.**

可表示為：

```text
Static Agent:
C_static(N) = N × C_solve

CEAA:
C_CEAA(N) = C_create + Σ C_reuse(i)
```

若 C_create > C_solve，但 C_reuse << C_solve，則隨著重用次數增加，CEAA 的平均任務成本應下降：

```text
Average Cost per Task
= (Capability Creation Cost + Reuse Cost + Maintenance Cost) / N
```

研究上應進一步量測 **Break-even Reuse Count**：

> 一個 Capability 至少需要成功重用多少次，才能抵銷第一次建立能力所增加的成本。

這個假說屬於目前 CEAA 研究範圍，而不是未來 Agent Platform 才驗證的項目。

## 2.3 Reasoning Cost Amortization

CEAA 將 Token Efficiency 的底層問題定義為：**降低重複任務反覆支付的推理成本，而不只是縮短 Prompt。**

一般 Agent 即使曾完成相似任務，仍可能重新讀取 Context、搜尋 Capability、選擇 Tool、試錯與 Retry。這形成 Repeated Reasoning Tax。

```text
Expensive Reasoning
→ Execution Experience
→ Validated Capability / Skill
→ Reusable Execution Path
→ Learned Decision
→ Less Repeated Reasoning
```

對重複任務：

```text
C_avg(N)
= (C_exploration + Σ C_reuse(i) + C_maintenance) / N
```

若 `C_reuse << C_exploration`，則 Experience 與 Reuse 增加時，平均推理成本應下降。

研究核心問題：

> **Can repeated LLM reasoning be progressively amortized into reusable execution knowledge, capabilities, skills, and learned decisions while maintaining or improving task success?**

主要效率目標不只看 Token per Request，而是：

```text
Cost per Successful Task
= (LLM Token Cost + Tool Cost + Compute Cost + Retry Cost)
  / Successful Tasks
```

並同步量測 Reasoning Calls、LLM Call Count、Retry Rate、Latency 與 Success Rate。

## 2.4 Experience as Training Data

Execution Experience 除了用於 Retrieval / Memory，也可作為未來 Decision Model 的訓練資料。

```text
State
├─ Task / Context
├─ Candidate Set
└─ Available Capabilities

Action
├─ Route
├─ Agent / Sub-Agent
├─ Capability / Skill / Tool
└─ Model Selection

Outcome
├─ Success / Failure
├─ Retry / Fallback
├─ Human Correction
└─ Token / Cost / Latency
```

每次執行可近似為 `(state, action, reward, next state)`。Reward 可同時反映成功、Token、Latency、Retry 與 Failure。

因此 Decision Model 的目標不是只模仿過去選了哪個 Tool，而是學習：

> **在目前狀態下，哪個 routing / capability / skill / model decision 能以較低成本可靠完成任務。**

研究演進可採：

```text
Telemetry
→ Dataset
→ Supervised Router
→ Cost-Aware Ranking
→ Contextual Bandit
→ Offline Reinforcement Learning
→ Controlled Deployment
```

Phase 1 的責任仍是建立高品質 Execution Experience dataset；Decision Model 訓練屬後續研究。

## 2.5 Reasoning Compilation Loop

CEAA 長期可將 Capability Evolution 理解為 **Reasoning Compilation**：

> 使用昂貴 LLM reasoning 探索未知問題，再把反覆出現且已驗證的解題經驗逐步編譯成較便宜的 Experience、Capability、Skill 或 Decision Model。

```text
Explore → Execute → Observe → Validate
                     ↓
                 Experience
                     ↓
              Extract / Learn
                     ↓
       Capability / Skill / Decision
                     ↓
                   Reuse
                     ↓
            Measure Cost / Success
                     ↓
          Novelty / Failure → Explore
```

Operational History 因此同時具有：

```text
Observability Evidence
Experience Memory
Training Dataset
Evolution Evidence
```

成功資料描述可重用路徑；失敗、Retry、Fallback 與人工修正則提供 decision boundary 與系統演化證據。

## 2.6 Agent Organization as Reasoning-Space Reduction

當 Capability、Skill、Tool 與 Agent 數量增加，把全域候選集合交給單一 LLM 會增加 Context 與選擇複雜度。

```text
Global Capability Space
→ Manager
→ Agent
→ Sub-Agent
→ Local Skill Set
→ Tool
```

目標是讓：

```text
|C_effective(task)| << |C_global|
```

透過 progressive disclosure、experience retrieval、small decision models 與必要時的大模型 escalation，每一層只處理必要候選。

因此 Agent Organization 不只是 scalability architecture，也是一種 **Reasoning-Space Reduction Architecture**。但 hierarchy 本身也有 overhead，必須用 end-to-end Success、Token、Latency 與 Cost 實證比較。

## 2.7 Long-Term Decision Evolution

長期演化可分為：

```text
Stage A: LLM Exploration
Stage B: Experience-Assisted Decision
Stage C: Small Learned Decision Model
Stage D: Mature Reusable / Deterministic Path
```

成熟路徑逐漸減少大型 LLM 的重複參與；大型 LLM 則更集中於新問題、低信心情境、例外處理與驗證。

因此 CEAA 的長期目標是：

> **讓 Agent 隨使用經驗增加，逐步減少不必要的重複推理，在維持既有驗證與治理邊界的前提下變得更便宜、更快、更可靠。**

---

## 2.8 Adaptive Skill Tiering & Performance Evolution

新增兩條相互回饋的演化路徑：**Difficulty-Aware Skill Routing** 與 **Usage-Driven Skill Optimization**。Skill 建立時歸屬 capability_family 並指定初始 tier；同一 family 可同時存在不同能力、成本與風險特性的 Skill 版本。Tier 是適用範圍而非品質保證，須以實測數據校正。

初始分級：L1 Lightweight（模板／確定性流程）、L2 Standard（多步驟整合與驗證）、L3 Advanced（高不確定性與複雜協作）。Skill Registry 增加 `capability_family`、`tier`、`supported_task_types`、`success_rate`、`avg_cost`、`latency`、`risk_class`、`version`、`usage_count`、`retry_rate` 與評估樣本量。

Decision Agent 先估計 task difficulty、risk、success probability 與候選 Skill 的預期總成本，再在成功率與權限約束下選擇執行路徑。不得假設永遠從 L1 開始：低階失敗後升級的重試成本也必須計入。低信心、新型或高風險任務回退至受控 LLM 路徑與既有審核流程。

`SkillOptimizationAgent` 依 Usage Telemetry、失敗率、Retry、Latency、Cost 與預期節省額排序優化候選。優化方向包括 Execution Optimization、Quality Optimization、Capability Specialization；高頻重複的 L3 子任務可提煉成專用低成本 Skill，但須驗證其適用邊界。Optimization Agent 僅產生候選 Skill Version，不可自行啟用或覆寫生產版本；須經 Regression、獨立 Main/Audit Review、Policy Gate、人員核准及可回滾版本治理。

閉環：Task → Difficulty / Risk Estimation → Tier-aware Decision → Skill Execution → Outcome Telemetry → Optimization Candidate → Validation / Approval → Registry Update → Decision Model Learning。主要目標是維持最低成功率與安全門檻下，降低 **Cost per Successful Task**，並記入訓練、測試與維護成本。

---

## 2.9 Skill Packages, Hierarchical Decisions & Execution-Path Experience（2026-10-20 設計增補）

**Status: Design Defined / Not Implemented.** 本節延伸既有 2.5 Reasoning Compilation、2.6 Agent Organization、2.7 Decision Evolution、2.8 Skill Tiering，並使用第 55 節的 Telemetry；不是取代現有 Capability Registry、Manager abstraction 或 Security Gate。**Skill Package 是內部能力組織單位，不等同於第 34 節的能力匯出／分享壓縮套件。**

### 核心問題與責任分層

當 Skill 數量增加，讓 Main Agent 每次逐一考慮所有候選並重新生成完整 Workflow，可能導致路由延遲、Context 成本與選錯路線風險。研究提出三級分工：

```text
Task / Requirements
  → Global Manager / Package Router
      ├─ risk, permission, candidate packages, global decision record
      ├─ single-package route → Package-local Decision
      └─ cross-package task → Governed Workflow Planner → selected Packages
  → Package Manifest (supported tasks, constraints, interfaces, version)
  → Package-local Decision (small model / rules / cache first; LLM on demand)
      ├─ package-scoped experience lookup
      ├─ validated execution-path candidate(s)
      └─ local Skill / Tool / Model / Workflow planning
  → Policy/Permission Check → Skill Execution → Independent Outcome Validation
  → Durable Trace + Decision Rationale + Actual Outcome
  → Experience Distillation (only verified patterns)
      ├─ Validated Execution Path Registry → fast-path reuse
      └─ Decision Experience → future routing / optimization experiments
```

**Global Decision** 決定 Package 或跨 Package 工作流程，保留全域風險、預算、授權和路由結果；**Local Decision** 只決定 Package 內 Skill、Tool、Model、Workflow 和 fallback。Local Decision 可先採規則、已驗證 Path 查詢或小型模型，僅在新型／低信心／高風險情境升級至強模型。Main Agent 不應每次重做 Package 內部規劃，也不必取得所有 Package 的詳細紀錄。

Package 可引用同一 Registry 中的版本化共享 Skill（many-to-many）；不複製或隱式轉移資料權限。Package 可有邏輯隔離的 local experience，但 Phase 1 優先共用 backend-neutral Telemetry Repository，以 `package_id`／`package_version`／`trace_id` 索引；不建立每包獨立資料庫。跨 Package Workflow 必須記錄完整 parent-child decisions，並分別遵守 scope、budget 與 policy。

### 三類分離的研究資產

1. **Capability / Skill Registry**：描述能執行什麼（ID、版本、適用任務、輸入輸出、前置條件、權限和依賴）。
2. **Raw Execution Trace / Path Evidence**：逐次事實紀錄（已選與未選候選、Global/Local decisions、branch/step order、Tool/Skill/Model version、retry/fallback、結果、時間、token/cost）。每次成功與失敗都保留，且與 task / trace correlation 一致。
3. **Curated Validated Execution Path + Decision Experience**：從獨立驗證過的 trace 萃取 task pattern、適用限制、版本相容、具體可重用 DAG / step plan、失效條件、實際效能統計與回退策略。未經驗證的建議不升級為 reusable path。

每次**首次計畫建立**應與 execution plan 同時保存**結構化 Decision Rationale**，但不保存、索取或假設能取得 LLM 私有內部 chain-of-thought。內容是可稽核的**簡短決策依據摘要**：task features、candidate IDs、selection criteria、可檢查 evidence refs、rejected-alternative summary、constraints、predicted outcome / uncertainty、decision model / prompt / policy version。將 `expected_outcome` 與之後獨立觀測的 `observed_outcome` 分開，避免事後合理化或把模型自述當作根因證明。敏感輸入／secret 不進 rationale。

### Fast Path 與失效保護

重複任務先比對 task signature、input schema、package/skill/tool/model versions、前置條件、權限、資料新鮮度、風險和允許成本，再採用已有驗證的 Path；重用的是 **plan，不是舊的 task output / secrets / stale state**。高信心時以 deterministic / lightweight lookup 直接執行，仍保留必要 policy checks 和 output validation。低信心、environment drift、version mismatch、risk escalation、validation failure，則回到完整 Local/Global Planner 或既有 Recovery Flow。不可將模糊相似度當作重用授權。

預期收益是少做重複的多層 LLM planning；額外 package routing 與 lookup 仍有成本，且 Global 選錯 package 可能放大後續錯誤。因此此處屬**待測假說**，不是已驗證加速結果。路線可以有多個版本和候選；在相同安全與正確率門檻下由 Decision policy 依歷史表現選擇，所有優化候選須通過 Regression + Main/Audit + human approval（適用時），禁止覆寫 active path。

### Interface / data contract（依階段導入）

- `SkillPackageManifest`: package ID/version、capability/task coverage、member skill refs、permission scope、risk、dependencies、compatible model/tool versions。
- `PackageRouterInterface`、`LocalDecisionInterface`、`ExecutionPathRepository`、`PathValidationInterface`、`DecisionExperienceRepository`：平台無關的設計介面，**尚無 runtime 實作**。
- `DecisionEvidence`：`decision_id`、`parent_decision_id`、`task_id`、`trace_id`、`package_id?`、`candidate_set`、`selected_target`、`selection_criteria`、`rationale_summary?`、`evidence_refs?`、`expected_outcome?`、`observed_outcome?`、`policy/model_version?`、`confidence?`、`latency?`。未知值必須 null/unavailable，不得猜測。
- `ExecutionPathEvidence`：`path_id`、`path_version`、`parent_path_id?`、step/branch edges、skill/tool/model refs、task signature、input schema、preconditions、validation result、outcome、failure/retry linkage。
- Phase 1 **只實作 trace/decision/step lineage 的最低必要擴充與 schema contract**，若要增加欄位必須 migration + backward compatibility + tests；不把尚未實作的 Manifest、local router、path registry、LLM rationale generation 視為 Phase 1 退出條件。沒有 provenance 的 rationale 必須保留 unavailable。
- Phase 1.5：與實際 provider、policy/sandbox、權限、版本管理及完整 trace 介面整合。
- Phase 2：靜態 Package Manifest / Registry、Package-local lookup、單一 Package 的 Path Registry 與簡單 fast path；語意路由沿用既定 embedding/pgvector 計畫。
- Phase 3：Experience-aware Global+Local Routing、Decision Rationale Outcome Calibration、Path Optimization、Skill Complexity Compression、cross-package benchmark／消融。
- 更遠期：受治理的 Package split/merge／adaptive organization，且必須以觀測資料證明其價值，不自動重組 production。

---


# 3. 核心設計原則

## 3.1 Capability First

Capability 必須是：

- 可執行
- 可驗證
- 可版本管理
- 可稽核
- 可重用
- 可撤銷

---

## 3.2 Validation Before Activation

任何新能力都不得直接啟用。

必須經過：

```text
Generate
→ Validate
→ Test
→ Report
→ Approval
→ Activate
```

---

## 3.3 Human-Governed Evolution

Agent 可以自主建立能力，但正式啟用仍由管理員治理。

研究版與正式版都保留此機制。

---

## 3.4 Sharing Is Opt-In

未來商品化後：

> **任何 Capability 對外分享都必須由使用者或組織明確選擇。**

預設：

```text
share_enabled = false
```

不得因系統自動演化而自動將使用者能力上傳至公共 Registry。

---

## 3.5 Import Is Also Opt-In

使用者也必須可以決定：

- 完全不取得外部 Capability
- 手動瀏覽與下載
- 接收推薦但手動批准
- 未來選擇受控的自動同步

任何外部能力都不能下載後立即執行。

---

## 3.6 Imported Capability Is Untrusted by Default

即使某個 Capability 已在其他環境驗證：

> **進入新的 Agent 後仍視為未受信任。**

必須重新執行：

```text
Compatibility Check
→ Local Validation
→ Local Test Report
→ Administrator Approval
→ Activation
```

---

## 3.7 Model Independent

底層模型透過 LLM Provider Interface 使用。

---

## 3.8 Infrastructure Independent

核心 Business Logic 不直接依賴：

- NVIDIA
- OpenRouter
- Docker
- PostgreSQL
- Redis
- 特定 Notification Provider

---

## 3.9 Implement Simple, Interface for Complex

現在只做必要功能。

但所有未來重要功能先保留 Interface 與資料結構。

---

## 3.10 Everything Is Versioned

包含：

- Capability
- Schema
- Artifact
- Test Plan
- Test Report
- Approval
- Model
- Prompt
- Policy
- Import
- Export
- Publication

---

## 3.11 Generated Artifacts Are Untrusted by Default

不論是新生成的 Capability、Workflow 或未來 Sub-Agent，只因為成功生成、編譯或通過 Builder 自身測試，都不得因此取得信任。

> **Generation success is not trust evidence. Trust must be earned through independent functional, security, runtime, and governance evidence.**

---

## 3.12 Independent Dual-Agent Cross-Validation

新生成 Artifact 在進入正式核准前，必須至少由兩個彼此獨立的角色進行交叉驗證：

- **Main Agent Review**：確認功能、需求、架構、整合與權限範圍是否符合原始意圖。
- **Audit Agent Review**：以不信任 Artifact 的立場進行安全、權限、資料流、依賴、越權與濫用風險檢查。

兩個 reviewer 的第一次判斷應獨立完成，避免彼此結論造成 anchoring。

---

## 3.13 Fail Closed and Mandatory Human Escalation

交叉驗證採 fail-closed 原則：

```text
AUTO_CONTINUE
iff
Main Review = PASS
AND
Audit Review = PASS
```

以下任一狀態都必須停止自動流程：

- FAIL
- ERROR
- UNKNOWN
- timeout
- reviewer disagreement

並立即產生 Validation Incident，通知 Human Administrator 進行確認。

> **任何一方沒有明確 PASS，都不得自動進入啟用流程。**

安全驗證失敗不得因功能驗證成功而被多數決覆蓋。

---

# 4. 高階系統架構

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
                                       Evolution Service
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

未來商品化擴充：

```text
                  Local Capability Registry
                          │
             ┌────────────┴────────────┐
             │                         │
        Export / Publish          Import / Discover
             │                         │
             ▼                         ▼
      Sharing Gateway       Capability Acquisition
             │                         │
             └──────────┬──────────────┘
                        ▼
              Shared Capability Registry
```

此區目前只保留設計，不列入 MVP。

---

# 5. Main Agent Service

主要責任：

- 理解任務
- 搜尋 Capability
- 呼叫 Capability Executor
- 評估執行結果
- 回報失敗
- 產生 Failure Context

Main Agent 不具有：

- 直接修改 Capability
- 直接啟用 Capability
- 直接上傳 Capability

的權限。

---

# 6. Capability Gap Detector

主要 Gap 類型：

- Missing Capability
- Insufficient Capability
- Integration Gap
- Reliability Gap
- Efficiency Gap
- Safety Gap

Gap 成立後建立：

**CapabilityGap Record**

並送往 Evolution Queue。

---

# 7. Evolution Queue

初期：

- PostgreSQL

未來：

- Redis
- RabbitMQ
- Kafka

核心只依賴：

```text
QueueInterface
```

---

# 8. Evolution Service

主要流程：

1. 讀取 Capability Gap
2. 分析 Failure Record
3. 搜尋現有能力
4. 搜尋必要知識
5. 產生解法
6. 建立 Candidate Capability
7. 建立基礎 Test Specification
8. 送交 Validation
9. 根據測試回饋 Revision
10. 完成後交由 Registry 管理

Evolution Service 無權直接 Activate 或 Publish。

---

# 8A. Evolution Construction and Secure Verification Pipeline

本節補足 CEAA 從「已確認缺少 Skill / 需要建立 Sub-Agent」到「真正產生可驗證程式 Artifact」之間的 execution architecture。

核心責任分離：

```text
Main Agent
= 定義需要什麼

Evolution Planner
= 決定要建立哪種 Artifact 與產生 Build Specification

Code Evolution Runtime / Builder Agent
= 實際閱讀 Repository、修改程式、建立測試、執行除錯

Main + Audit Cross-Validation
= 獨立確認功能正確性與安全性

Policy / Human Governance
= 決定是否允許正式進入 Registry / Activation
```

完整流程：

```text
Capability Gap / Agent Gap Confirmed
            ↓
      Evolution Planner
            ↓
      Build Specification
            ↓
     Code Evolution Runtime
            ↓
   Ephemeral Builder Agent
            ↓
Inspect → Plan → Code → Test → Debug → Revise
            ↓
      Candidate Artifact
            ↓
================================================
          Secure Evolution Gate
================================================
      ↓                     ↓
Main Agent Review       Audit Agent Review
      └──────────────┬──────────────┘
                     ↓
              Cross-Validation
                     ↓
          ┌──────────┴──────────┐
          │                     │
     PASS + PASS            Anything Else
          │                     │
          ▼                     ▼
 Independent Runtime       BLOCK AUTOMATION
 Testing / Security              ↓
          │               Human Admin Alert
          │                     ↓
          │             Review / Revision
          │                     ↓
          └────────────── Full Revalidation
                     ↓
                 Policy
                     ↓
             Human Approval
                     ↓
           Registry / Activate
```

## 8A.1 Build Specification

Main Agent 不直接要求 Builder 自由發揮，而應先產生結構化 Build Specification，作為 Main Agent 與 Builder Runtime 之間的契約。

至少應描述：

```text
build_id
artifact_type
goal
inputs
outputs
required_interfaces
allowed_dependencies
allowed_tools
forbidden_actions
acceptance_criteria
resource_budget
target_repository
base_revision
requested_permissions
```

## 8A.2 Code Evolution Runtime

Code Evolution Runtime 是可替換的 software-engineering execution layer。

介面方向：

```text
CodeBuilderRuntime
├─ Pi 1.x Builder Adapter           (preferred evaluation candidate)
├─ OpenCode Builder Adapter         (alternative candidate)
├─ Codex-like Builder Adapter
├─ Native / Other Coding Agent Adapter
└─ Future Local Builder Adapter
```

CEAA 核心不得綁死單一 coding-agent framework。

**技術候選（尚未選定）：** Pi 1.x 與 OpenCode 均可作為 Phase 1.5 的 Builder Runtime reference implementation。OpenCode 以 SDK / HTTP server / coding agent / sub-agent 能力作為候選整合路徑；實際支援的 session、model switching、tool permission、trace、usage 與 isolation 行為必須以固定版本進行 adapter compatibility test。

候選選型應在相同 task set、provider/model、budget、workspace policy 下比較：Skill / AgentArtifact 建立成功率、first-pass tests、修復迭代、token/cost、latency、API/SDK integration overhead、recoverability、audit provenance 與 sandbox enforcement。不得因某 runtime 自帶 reviewer / agent 權限設定就跳過 CEAA 的 Main/Audit 獨立驗證、Docker sandbox、Policy Engine 或 Human Approval。

**Status: Technology candidate only — not integrated or validated.**

Builder 的典型循環：

```text
Inspect Repository
→ Plan
→ Edit Code
→ Write / Update Tests
→ Run Tests
→ Observe Failure
→ Revise
→ Repeat Until Exit Condition
```

Builder 必須受 max iterations、runtime、token / cost budget、test-run budget 與 sandbox policy 限制。

## 8A.3 Ephemeral Builder and Isolated Workspace

Builder 預設應為 ephemeral，不直接操作 production branch、production registry、真實 credential 或不受限資料。

建議執行邊界：

```text
Base Revision
    ↓
Temporary Git Branch / Worktree
    ↓
Isolated Workspace / Sandbox
    ↓
Builder writes candidate only
```

典型權限：

```text
repository.read       = allow
workspace.write       = allow
run.tests             = allow

git.push.main         = deny
registry.activate     = deny
production.db.write   = deny
raw.credentials       = deny
```

## 8A.4 Candidate Artifact Contract

Builder 的輸出不是自然語言宣告「完成」，而是版本化 Candidate Artifact 與完整 BuildResult。

至少包含：

```text
source / git diff / commit
manifest
tests
dependency changes
build log
test results
known limitations
security notes
builder provenance
model / provider provenance
resource usage
```

Skill 生成主要產生 CapabilityArtifact；未來 Sub-Agent 生成主要產生 AgentArtifact。

Sub-Agent 應優先組合已驗證 Capability；只有缺少必要能力時才遞迴觸發 Skill Generation，而不是每次從零重寫所有功能。

## 8A.5 Independent Main Agent Review

Main Agent Reviewer 主要回答：

- 是否真正補上原始 Gap
- 是否符合 Build Specification
- 是否遵守架構與介面
- 是否引入不必要功能或依賴
- 是否要求超出需求的權限
- 是否與既有 Capability / Agent 重複
- 是否能正確整合回原始任務流程

Main Agent Review 不具有單獨放行權。

## 8A.6 Independent Audit Agent Review

Audit Agent 必須以 adversarial / untrusted-artifact 立場檢查：

- privilege escalation
- unauthorized tool or data access
- cross-branch access
- credential / secret exposure
- dangerous process / shell execution
- unsafe network behavior
- data exfiltration
- dependency / supply-chain risk
- persistence outside approved scope
- prompt / tool injection paths
- permission bypass through capability composition
- recursive child-Agent privilege bypass

Audit Agent 不得因 Main Agent 認為功能正確而降低安全門檻。

## 8A.7 Frontier-Model Verification

高風險語意驗證可路由到前沿模型，特別是需要理解 control flow、data flow、permission boundary、tool chaining、prompt behavior 與 indirect privilege escalation 的情況。

推薦原則：

```text
Builder
→ coding-specialized / cost-efficient model

Main Functional / Architecture Review
→ strong frontier model

Audit Security Review
→ independently invoked strong frontier model
```

若可行，Main Reviewer 與 Audit Reviewer 應採不同 provider / model family；若使用同一模型，也應使用獨立 inference、不同 system role 與隔離 context。

模型驗證不能取代 deterministic security controls。

## 8A.8 Deterministic + Semantic Security

Secure Evolution Gate 應組合兩類 evidence：

```text
Deterministic Security
+
Semantic Security Review
```

Deterministic evidence 可包含：

- unit / integration / regression tests
- lint / type checks
- SAST
- dependency vulnerability scan
- secret scan
- policy assertions
- sandbox execution
- filesystem diff
- network observation
- resource limits

Semantic review 則由強模型分析 intent、architecture、control flow、data flow、side effects、permission boundaries 與 Agent behavior。

## 8A.9 Security Challenge Generation

Audit Agent 不只閱讀程式，也應能產生 adversarial test cases，再交由 sandbox / testing runtime 執行。

候選案例包括：

- malformed input
- prompt injection
- unauthorized file access
- cross-branch access
- privilege escalation
- secret probing
- network exfiltration
- resource exhaustion
- unsafe tool chaining
- recursive delegation abuse

Audit Agent 因此同時扮演 Security Reviewer 與 Adversarial Test Generator。

## 8A.10 Mandatory Human Escalation

Main Agent 與 Audit Agent 的交叉驗證決策矩陣：

| Main Review | Audit Review | System Action |
|---|---|---|
| PASS | PASS | Continue to remaining tests / approval |
| PASS | FAIL | Block + Human Admin Notification |
| FAIL | PASS | Block + Human Admin Notification |
| FAIL | FAIL | Block + Human Admin Notification |
| ERROR / UNKNOWN / TIMEOUT | any | Block + Human Admin Notification |
| any | ERROR / UNKNOWN / TIMEOUT | Block + Human Admin Notification |

強制規則：

> **No generated artifact may proceed automatically unless both the Main Agent and Audit Agent independently return PASS. Any FAIL, ERROR, UNKNOWN, timeout, or disagreement triggers mandatory human review.**

Human Administrator 可採取：

- Reject
- Request Revision
- Mark Finding as False Positive with recorded justification
- Quarantine

前期設計不提供繞過 Secure Evolution Gate 的 unrestricted Force Activate。

若 Human 判定為 false positive，仍應記錄理由並重新執行完整 validation；Human decision 不直接取代重新驗證。

## 8A.11 Validation Incident Report

任何交叉驗證異常都必須建立可稽核 Incident Record，至少保存：

```text
artifact_id / version
build_id
requested_by
builder identity / model
main review result / evidence
audit review result / evidence
failure category
affected permissions / data
code diff / artifact hash
test evidence
recommended action
human decision
revision lineage
timestamps / trace_id
```

Notification Service 必須支援至少以下事件：

```text
ValidationFailure
CrossValidationDisagreement
SecurityFinding
PolicyViolation
ArtifactQuarantined
HumanReviewRequired
```

## 8A.12 Revision Requires Full Revalidation

任何 Builder 修正都產生新的 Artifact version，並重新執行 Main Review、Audit Review、deterministic tests 與必要的 adversarial tests。

不得只重跑先前失敗的單一檢查。

```text
Candidate v1
→ Finding
→ Revision
→ Candidate v2
→ Full Secure Evolution Gate
```

## 8A.13 Future Sub-Agent Construction

未來 Agent Gap 已確認後，可共用相同 Code Evolution Runtime，但輸出為 AgentArtifact。

AgentArtifact 應至少包含：

```text
Agent Manifest
Role / Goal / Responsibility
System Instructions
Capability Bindings
Tool Bindings
Model Policy
Memory Policy
Data Scope
Permission Scope
Delegation Policy
Child Creation Policy
Resource Budget
Tests / Evaluation
Lifecycle Policy
```

Sub-Agent Secure Evolution Gate 除一般程式安全外，還必須證明：

```text
P_child ⊆ P_parent ⊆ P_root
G_child ⊆ G_parent ⊆ G_root
```

並驗證無法透過 Tool chaining、Capability composition、Data Gateway 或再建立 child Agent 間接繞過上述 ceiling。

---

# 9. Capability 定義

Capability 是：

> **可以被 Agent 重複執行，並具有明確輸入、輸出、依賴、風險、驗證與版本資訊的能力單元。**

可能形式：

- Python
- API
- Workflow
- Tool Sequence
- Agent Workflow
- Container
- Domain Procedure

---

# 10. Capability Schema

至少包含：

```text
schema_version
capability_id
capability_version

name
description

tenant_id
owner_id
organization_id
scope

task_family

inputs
outputs
preconditions

dependencies
implementation

validation_requirements
safety_requirements

compatibility
trust_level

status

sharing_policy
distribution_metadata

created_at
updated_at
```

---

# 11. Capability Identity

使用穩定 ID：

```text
CAP-000001
```

Identity 與名稱、版本、儲存位置分離。

---

# 12. Capability Versioning

至少分為：

```text
schema_version
capability_version
```

未來 Sharing Registry 也必須保留完整版本。

---

# 13. Capability Lifecycle

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

外部能力另外增加：

```text
Discovered
 ↓
Downloaded
 ↓
Imported
 ↓
Local Validation
 ↓
Local Testing
 ↓
Pending Approval
 ↓
Active
```

---

# 14. Capability Executor

統一透過：

```text
CapabilityExecutor
```

未來支援：

- PythonExecutor
- APIExecutor
- WorkflowExecutor
- ContainerExecutor
- AgentExecutor
- PluginExecutor

---

# 15. Capability Composition

Capability 可依賴其他 Capability。

例如：

```text
CSV Reader
+
Analyzer
+
Report Generator
        ↓
Automated Analysis Capability
```

因此保留：

```text
dependencies
child_capabilities
composition_type
```

---

# 16. Capability Registry

Registry 管理：

- Identity
- Version
- Status
- Ownership
- Scope
- Validation
- Test Report
- Approval
- Trust
- Compatibility
- Dependency
- Sharing Policy
- Publication State
- Revocation

---

# 17. Capability Testing Agent

Testing Agent 與 Evolution Agent 分離。

Evolution：

> 建立能力。

Testing：

> 嘗試證明能力可能在哪裡失敗。

---

# 18. Autonomous Test Plan

測試類型包括：

- Functional
- Boundary
- Failure
- Regression
- Generalization
- Safety
- Performance

---

# 19. Validation Service

接口：

```text
validate(
    capability,
    test_suite,
    validation_context
) -> ValidationResult
```

第一版 Sandbox：

**Docker**

---

# 20. Capability Test Report

每個 Capability Version 必須產生：

```text
test_report.json
test_report.md
```

內容包含：

- Test cases
- Pass rate
- Failed cases
- Generalization
- Regression
- Safety
- Performance
- Known limitations
- Risk level
- Recommended action

---

# 21. Capability Artifact

建議：

```text
CAP-000001/
├── manifest.yaml
├── implementation/
├── tests/
├── test_plan.yaml
├── test_report.json
├── test_report.md
├── validation/
├── changelog.md
└── README.md
```

---

# 22. Human Approval Gate

新能力完成測試後：

```text
Pending Approval
```

管理員可以：

- Approve
- Reject
- Request Revision
- Approve With Restrictions

---

# 23. Notification Service

保留：

```text
NotificationService
```

Provider 可包括：

- Console
- Email
- Webhook
- Slack
- Teams
- Mobile Push

新能力 Ready for Review 必須通知管理員。

---

# 24. Approval Service

接口：

```text
request_approval()
approve()
reject()
request_revision()
approve_with_restrictions()
```

Notification 不具有 Activation 權限。

---

# 25. Event Contract

核心事件：

```text
CapabilityGapCreated
CapabilityGenerated
BuildSpecificationCreated
BuilderStarted
CandidateArtifactCreated
MainReviewCompleted
AuditReviewCompleted
CrossValidationCompleted
HumanReviewRequired
ValidationIncidentCreated
ArtifactQuarantined

ValidationStarted
ValidationCompleted

CapabilityTestingStarted
CapabilityTestingCompleted

CapabilityReportGenerated

CapabilityReadyForReview
CapabilityApproved
CapabilityRejected

CapabilityActivated
CapabilityDeprecated
CapabilityRevoked
```

未來 Sharing 新增：

```text
CapabilityExportRequested
CapabilityExported

CapabilityPublishRequested
CapabilityPublished
CapabilityPublishRejected

CapabilityDiscovered
CapabilityDownloadRequested
CapabilityDownloaded

CapabilityImportStarted
CapabilityImported

CapabilityLocalValidationStarted
CapabilityLocalValidationCompleted

SharedCapabilityRevoked
SharedCapabilityUpdateAvailable
```

---

# 26. Audit Trail

需記錄：

- Generate
- Build Specification
- Builder execution / revision
- Candidate Artifact creation
- Main Agent Review
- Audit Agent Review
- Cross-Validation decision
- Human Escalation / Incident decision
- Validate
- Test
- Report
- Notify
- Approve
- Activate
- Import
- Export
- Publish
- Download
- Update
- Rollback
- Revoke

---

# 27. Service Layer

建議：

```text
MainAgentService
GapDetectionService
EvolutionService
EvolutionPlannerService
CodeBuilderService
SecureEvolutionGateService
CrossValidationService
ValidationIncidentService

CapabilityService
CapabilityExecutionService

ValidationService
TestingService

PolicyService
ApprovalService
NotificationService
```

未來保留：

```text
CapabilityImportService
CapabilityExportService
CapabilityPublishingService
CapabilityDiscoveryService
CapabilitySyncService
```

這些目前只定義邊界，不實作完整功能。

---

# 28. LLM Architecture

```text
Agent
 ↓
Internal LLM Gateway
 ↓
Routing Policy
 ↓
LiteLLM
 ├─ NVIDIA NIM
 ├─ OpenRouter
 └─ LocalLLMProvider
```

---

# 29. Local LLM Readiness

預留：

```text
LocalLLMProvider
```

未來可接：

- Ollama
- llama.cpp
- vLLM
- LM Studio

---

# 30. Storage Separation

### Metadata

PostgreSQL

### Artifact

Git + Filesystem

### Vector

pgvector

### Test Report

Git / Filesystem

### Experiment

PostgreSQL → MLflow

未來 Shared Registry 為獨立服務。

---

# 31. Capability Scope

保留：

```text
private
local
organization
global
```

### Private

只屬於特定使用者。

### Local

只屬於目前 Agent。

### Organization

組織內共享。

### Global

允許未來發布至共享 Registry。

Scope 本身不代表已經允許分享。

---

# 32. Sharing Policy

新增：

```text
sharing_policy
```

可能狀態：

```text
private_only
manual_share
organization_only
global_opt_in
```

預設：

```text
private_only
```

---

# 33. Capability Upload / Import — Future Reserved

## 狀態

**Reserved for Future Development**

研究 MVP 不實作完整 Marketplace。

但現在必須保留：

```text
CapabilityImportService
```

未來允許使用者：

> 將外部 Capability 加入自己的 Agent。

來源可能包括：

- Local file
- Organization Registry
- Global Capability Registry
- Trusted partner
- Capability Marketplace

---

# 34. Capability Upload Package

未來 Capability 可採標準套件：

```text
capability-package/
├── manifest.yaml
├── implementation/
├── tests/
├── test_report.json
├── test_report.md
├── dependencies.lock
├── signature.json
└── README.md
```

未來可封裝為：

```text
.cap
```

或其他標準格式。

目前只保留 Packaging Interface。

---

# 35. Imported Capability 安全流程

任何外部 Capability：

```text
Downloaded
     ↓
Signature Check
     ↓
Manifest Validation
     ↓
Dependency Inspection
     ↓
Compatibility Check
     ↓
Static Safety Check
     ↓
Local Sandbox Validation
     ↓
Testing Agent
     ↓
Local Test Report
     ↓
Administrator Approval
     ↓
Active
```

因此：

> **別人的測試報告只能作為參考，不能取代本機驗證。**

---

# 36. Capability Publish / Sharing — Future Reserved

新增：

```text
CapabilityPublishingService
```

未來使用者可以選擇：

> 是否願意把自己的 Agent 新學到的能力分享出去。

預設：

```text
publish = false
```

---

# 37. Publishing Flow

未來可能流程：

```text
Local Active Capability
       ↓
User Selects Share
       ↓
Publish Request
       ↓
Privacy / Secret Scan
       ↓
Environment Neutralization
       ↓
Generalization Check
       ↓
Security Review
       ↓
Package Generation
       ↓
Signature
       ↓
Shared Capability Registry
```

---

# 38. Environment Neutralization

Capability 不可以把使用者環境直接分享出去。

發布前需要移除：

- Local paths
- Hostnames
- IP addresses
- Credentials
- Tokens
- Internal API URLs
- Customer IDs
- Private configuration
- Private datasets

因此 Future Publishing Pipeline 必須包含：

**Sanitization / Neutralization**

---

# 39. Sharing Consent

分享必須有明確 Consent Record：

```text
consent_id
user_id
capability_id
capability_version
sharing_scope
approved_at
revocable
```

使用者未同意時，不得發布。

---

# 40. Capability Discovery — Future Reserved

未來新增：

```text
CapabilityDiscoveryService
```

Agent 或使用者可以搜尋：

```text
"What capabilities exist for CSV repair?"
```

Registry 回傳：

- Capability
- Version
- Description
- Publisher
- Trust Score
- Validation Count
- Supported Environment
- Dependencies
- Risk Level

---

# 41. External Capability Recommendation

未來 Main Agent 遇到 Gap 時，可以：

```text
Local Search
      ↓
No Suitable Capability
      ↓
Ask Shared Registry
      ↓
Candidate External Capability
      ↓
Recommend to User
```

但不能直接安裝。

必須由使用者確認：

```text
Would you like to acquire this capability?
```

---

# 42. Capability Acquisition Modes

未來商品化可提供：

### Mode A — Isolated

```text
External Capability = Disabled
Sharing = Disabled
```

適合高安全企業。

### Mode B — Manual

使用者手動：

- Search
- Download
- Share

### Mode C — Recommended

Agent 可以推薦，但使用者批准。

### Mode D — Organization Managed

由公司管理員控制內部 Capability Registry。

### Mode E — Managed Sync

未來成熟後可以允許：

> 特定 Trusted Capability 自動取得更新。

但仍受 Policy Engine 控制。

---

# 43. Capability Update

外部 Capability 未來可能有：

```text
CAP-001
v1.0
 ↓
v1.1
 ↓
v2.0
```

Local Agent 必須能選擇：

- Ignore
- Review Update
- Test Update
- Approve Update
- Rollback

不能強制自動更新。

---

# 44. Shared Capability Revocation

若 Global Registry 發現：

- Security issue
- Malware
- Dangerous behavior
- Severe bug

可發布：

```text
CapabilityRevocationNotice
```

Local Agent 應：

1. 提醒管理員
2. 標記 affected Capability
3. 停止新任務使用或依 Policy 處理
4. 提供 rollback

---

# 45. Shared Capability Trust Model

未來可建立：

**Capability Trust Score**

依據：

- Publisher reputation
- Validation count
- Cross-environment success
- Regression history
- Security scan
- User feedback
- Revocation history

但 Trust Score 永遠不能替代本機 validation。

---

# 46. Capability Provenance

所有 Capability 必須保留來源：

```text
origin:
    local_generated
    manual_created
    imported
    organization_shared
    global_shared
```

外部 Capability 另外保存：

```text
source_registry
publisher
original_capability_id
original_version
imported_at
```

---

# 47. Fork Capability

使用者取得別人的 Capability 後，可能自行修改。

因此未來支援：

```text
Fork
```

例如：

```text
Global CAP-120
      ↓
Import
      ↓
Local Fork
      ↓
CAP-LOCAL-32
```

保留：

```text
parent_capability_id
parent_version
```

---

# 48. Capability Lineage

未來 Capability 可能形成：

```text
Original
   ↓
Fork
   ↓
Improved
   ↓
Published Variant
```

因此 Registry 應保留：

**Capability Lineage**

這對研究 Agent 的能力演化路徑也有價值。

---

# 49. Capability Marketplace — Future Reserved

正式商品化後，可以進一步演進成：

**Capability Marketplace**

但目前不列入研究開發。

未來 Marketplace 可能支援：

- Free Capability
- Private Capability
- Organization Capability
- Verified Capability
- Vendor Capability

現階段只保留 Architecture Extension Point。

---

# 50. Collective Capability Network

更長期可以形成：

```text
Agent A
  ↓
Learns Capability X
  ↓
User Opt-In Share
  ↓
Global Registry
  ↓
Agent B discovers X
  ↓
User Opt-In Download
  ↓
Local Validation
  ↓
Agent B gains X
```

這形成：

> **Capability-level collective learning**

不需要交換模型權重。

---

# 51. Privacy Boundary

共享的是：

- Capability implementation
- Generic workflow
- Validation metadata
- Compatibility
- Generic tests

不共享：

- Raw user data
- Conversation history
- Enterprise logs
- Credentials
- Internal topology
- Private configuration
- Local memory

---

# 52. Tenant Readiness

Schema 從第一版保留：

```text
tenant_id
organization_id
owner_id
scope
sharing_policy
```

研究階段使用 default tenant。

---

# 53. Policy Engine

未來增加：

```text
can_import()
can_export()
can_publish()
can_download()
can_sync()
can_share_globally()
```

與既有：

```text
can_generate()
can_validate()
can_execute()
can_activate()
```

整合。

---

# 54. Notification 擴展

Future Sharing Events 也使用 Notification Service。

例如：

- External capability available
- Capability update available
- Publication approved
- Publication rejected
- Shared capability revoked
- Organization capability published

---

# 55. Observability Contract

標準 Metadata：

```text
run_id
task_id
agent_id

capability_id
capability_version

experiment_id

model_id
tenant_id
trace_id
```

未來加入：

```text
registry_id
publisher_id
source_capability_id
```

---

## 55.1 Failure-driven Self-Recovery Architecture（2026-10-19 設計增補）

**狀態：Approved Design / Planned / Not Implemented。** 本節屬 v1.9 設計基準的增補，延續既有 Manager、Telemetry、Experience Memory 與 Secure Evolution Gate，不代表目前 Runtime 已具備自主診斷或修復功能。

### 目標與架構定位

系統在任務失敗且安全重試達上限後，不立即將整個任務視為不可恢復，而是建立結構化 Failure Episode，由 Failure Analysis Manager 選擇必要的診斷 Agent，定位失敗環節、提出修復候選並通過獨立驗證，最後安全恢復或升級給人類管理員。這形成第四條**研究性演化路徑 Reliability Evolution**，與 Capability / Decision / Performance Evolution 共享 Experience Memory 和 Telemetry。

```text
Task → Manager / Router → Agent / Skill / Tool Execution
                                    ↓
                             Result Validator
                         ┌──────────┴──────────┐
                       PASS                  FAIL
                         ↓                     ↓
                   Final Outcome       Failure Classifier
                                               ↓
                                         Retry Controller
                              ┌────────────────┴────────────────┐
                         safe & budgeted                exhausted / unsafe
                              ↓                                ↓
                        bounded retry              Failure Analysis Manager
                                                            ↓
                                        select Trace / Root Cause / Tool /
                                        Skill / Environment diagnosis agents
                                                            ↓
                                             Root-cause evidence + Repair Plan
                                                            ↓
                                           Sandbox + Regression + Policy Gate
                                                            ↓
                                            Main/Audit Secure Evolution Gate
                                           ┌────────────────┴───────────────┐
                                      PASS / authorized             FAIL / UNKNOWN
                                           ↓                              ↓
                                   checkpoint resume              halt / human escalation
                                           ↓                              ↓
                                     Result Validator          Incident / Audit
                                           └────────────┬─────────────────┘
                                                        ↓
                                       Raw History + Recovery Outcome
                                                        ↓
                                       Curated Experience Memory (only
                                       after independent validation)
```

### 分層責任與契約

- **Retry Controller**：區分 transient / semantic / policy / authorization / side-effect / permanent failure；判斷冪等性、是否已部分成功、backoff、retry 次數、deadline 與成本上限。非冪等操作不可盲目重試。
- **Failure Analysis Manager**：依 error taxonomy、歷史經驗、預算與風險，選擇一個或多個專業診斷 Agent；不要求每次啟動全部 Agent。
- **Diagnostic Agents**：Trace、Root Cause、Tool/API、Skill、Environment 等角色只提出可追溯證據與假說；不得因 LLM 自評而認定根因已證實。
- **Repair Planner**：產生版本化 `RecoveryPlan`、候選變更、風險與 rollback/checkpoint；不得直接修改 production。
- **Recovery Gate**：沿用既有 policy、sandbox、deterministic tests、Main/Audit independent review、human escalation；缺失證據、timeout、審查衝突或未知結果一律 fail closed。
- **Experience Memory**：Raw failure/failed repair 全部保留；只有獨立驗證成功且經治理允許的修復流程，才可提升為可重用 Recovery Skill。

Phase 1 的 backend-neutral interface contract：`RetryPolicyInterface`、`FailureAnalysisInterface`、`RecoveryPlannerInterface`、`RecoveryGateInterface`、`RecoveryOutcomeRepository`。資料契約至少包括 `FailureContext`、`RetryDecision`、`RecoveryPlan`、`RecoveryOutcome`，與既有 `execution_traces`、`execution_failures`、`recovery_attempts`、`routing_decisions` 以 task/trace/failure ID 關聯。所有 token、latency、repair cost 與 validation result 都應記錄；不可取得的值保持 unavailable。

### 階段落地

| 階段 | 功能 | 完成判準 |
|---|---|---|
| Phase 1 | Interface / data contracts、failure lineage、bounded retry policy、Mock contract tests；完成既有 telemetry runtime wiring | 能保存失敗→重試→上限→待診斷事件，重啟可查詢；**不需**自主診斷 Agent |
| Phase 1.5 | Real provider、sandbox、policy、gate、audit、checkpoint 與 human escalation hooks | 失敗候選不得繞過治理；unsafe/unknown case fail closed |
| Phase 2 | Single Failure Analysis Agent + Repair Planning MVP、受控修復、curated recovery experience | 能在故障注入任務上產生可驗證診斷、候選修復與安全結案 |
| Phase 3 | 多 Agent 選擇式診斷、experience-aware recovery routing、縱向實驗 | 以獨立 holdout benchmark 驗證品質、成本、恢復與回歸率 |

### 不變的治理限制

Retry、repair cycles、time/cost budget 與 recursive delegation 必須有明確上限；任何恢復均不得提升權限或擴大資料存取；需要處理未知 side effect、重複提交及 rollback。修復 Candidate 必須重新通過完整驗證；高風險操作保留 Human Administrator 核准權。Phase 1 先蒐集原始資料，禁止將未驗證的診斷寫成「成功經驗」。

---

# 56. 研究指標

核心研究指標：

- Task Success Rate
- Capability Generation Success Rate
- Validation Pass Rate
- Testing Pass Rate
- Approval Rate
- Reuse Rate
- Generalization Rate
- Regression Rate
- Repeated Failure Rate
- Cost
- Latency

### 56.1 Token / Cost Efficiency Metrics

為驗證 Capability Reuse 是否能降低長期推理成本，每次 LLM interaction 與 task execution 應盡可能記錄：

```text
task_id
task_family
capability_id
capability_version
capability_created
capability_reused
input_tokens
output_tokens
reasoning_tokens
total_tokens
llm_call_count
latency
task_success
```

若 Provider 不提供 reasoning token，必須記錄為 unavailable，而不是推估。

Capability 建立階段需另外彙總：

```text
gap_detection_tokens
generation_tokens
validation_tokens
testing_tokens
revision_tokens
report_tokens
total_capability_creation_tokens
```

Capability 重用階段需彙總：

```text
retrieval_tokens
routing_tokens
reuse_reasoning_tokens
validation_tokens
response_tokens
total_capability_reuse_tokens
```

主要衍生指標：

```text
Average Tokens per Task
Token Saving = Static Agent Tokens - CEAA Tokens
Token Saving Rate = 1 - (CEAA Tokens / Static Agent Tokens)
Break-even Reuse Count = first N where cumulative CEAA cost < cumulative static-agent cost
```

除了 Token，也同步記錄：

- LLM Call Count
- Latency
- Capability Execution Time
- Capability Revision Cost
- Failure / Retry Cost
- Provider Monetary Cost（若 Provider 可取得可靠計價資訊）

研究結果不得只比較第一次 Capability Creation；必須比較一段任務序列的 cumulative cost 與 average cost。

### 56.2 Reuse Similarity Levels

為避免只證明「完全相同問題的快取效果」，重用實驗至少區分：

#### Exact Repetition

幾乎相同的任務，只改變極少量輸入。

#### Near-Similar

同一 task family、核心程序相同，但資料或問題內容不同。

#### Generalized

需要相同核心能力，但場景、輸入結構或上下文有明顯改變。

研究需分別觀察：

- 是否成功找到既有 Capability
- 是否能直接 reuse
- 是否需要 adaptation / revision
- token 是否仍低於 solve-from-scratch baseline
- success rate 是否維持
- 是否因過度重用造成 regression

未來 Sharing 研究可以增加：

- Capability Transfer Success Rate
- Cross-Environment Generalization
- External Capability Reuse Rate
- Import Rejection Rate
- Shared Capability Regression Rate
- Time-to-Capability-Adoption

但目前不屬於 Phase 1。

---

# 57. 本機條件

目前硬體：

- Intel Core i5-14600K
- DDR4 80 GB
- AMD RX 6650 XT

已安裝：

- LangGraph
- PostgreSQL
- FastAPI
- Git
- Docker

採用：

**Cloud-First Reasoning**

---

# 58. Phase 1 — Core MVP

新增：

- LiteLLM
- pytest
- NVIDIA NIM
- OpenRouter

確認：

- Pydantic

完成：

```text
Capability Schema
Main Agent
Gap Detector
Evolution Agent
Validation Service
Testing Agent
Test Report
Capability Registry
Notification Interface
Approval API
Token / Cost Measurement Foundation
Execution Experience & Evolution Telemetry Foundation
```

Phase 1 的 Token / Cost Measurement Foundation 包含：

- 為每個 task 建立不可重複的 `task_id`；
- 持久化每次 LLM interaction 的 phase、provider/model、token usage、可靠的 provider cost、
  latency、success 與 error；
- 持久化 task 是否建立／重用 Capability、最終 outcome、LLM call count、總延遲與
  capability execution time；
- 提供 task、interaction 與 summary API，並支援以明確的 static baseline 計算
  average tokens、saving rate 與 break-even reuse count；
- Provider 未回報的 token（尤其 reasoning token）必須保存為 unavailable，不得推估。

此量測基礎已合併至 `dev`。Phase 1 建立可驗證的量測管線，不宣稱 Mock LLM 已提供真實 token 證據，也不取代
Phase 3 的跨模型、跨相似度與長任務序列正式實驗。

Phase 1 同時必須建立 **Execution Experience & Evolution Telemetry Foundation**。這不是 Adaptive Agent Organization 本身，而是未來 Experience Memory、system diagnosis、Capability / Agent / Organization Evolution 所依賴的歷史證據層。最低應保存：

- task / trace identity；
- routing decision 與 parent decision；
- candidate set、selected target、node type 與 routing depth；
- execution success / failure、raw exception 與 normalized failure category；
- retry / fallback / recovery outcome；
- latency、token、cost 與 final outcome correlation；
- restart-persistent evidence，並與既有 token / cost metrics 使用一致 identity。

因此目前狀態為 **Phase 1 In Progress / Core Baseline Verified**。既有 28-test baseline 不再代表整個 Phase 1 Complete；Telemetry Foundation 完成並驗證後才進入 Phase 1.5。

---

# 59. Phase 2 — Capability Retrieval

新增：

- pgvector
- Embedding Provider

完成：

```text
Capability Search
Similarity Retrieval
Reuse
```

---

# 60. Phase 3 — Research Evaluation

新增：

- Phoenix
- DeepEval
- MLflow

Phase 3 在 Phase 1 已建立的量測與持久化基礎上，正式執行
**Token Efficiency / Cost Amortization Experiment**，並與既有正確率、Reuse、
Generalization、Regression 等指標一起分析。

至少比較：

```text
Baseline A: Strong Model + Static Capabilities
Baseline B: Medium Model + Static Capabilities
Experimental C: Medium Model + Evolving Capabilities
Optional D: Strong Model + Evolving Capabilities
```

針對每個 task family 準備一系列任務：

```text
Q1  → First encounter / possible capability creation
Q2  → Exact or near-similar reuse
Q3  → Near-similar reuse
...
Qn  → Generalized reuse
```

每一題都記錄：

```text
task success
capability created / reused / revised
input tokens
output tokens
reasoning tokens if available
total tokens
LLM call count
latency
retry count
provider cost if available
```

主要比較：

1. 第一次新能力建立成本是否高於 baseline。
2. 第二次之後的 reuse token 是否下降。
3. 平均 token/task 是否隨 reuse 次數增加而下降。
4. cumulative CEAA cost 何時低於 static baseline。
5. Exact / Near-Similar / Generalized 三種任務中的節省程度。
6. Token 節省是否以成功率下降為代價。
7. Capability revision / maintenance 是否侵蝕長期成本優勢。
8. 不同模型強度下，Capability Evolution 是否能降低對大型模型重複推理的依賴。

### HYSET — Set-Level Tool Retrieval Baseline（後續實驗）

參考論文：Hong, Xinyi, Pinjun Dong, Xinyang Yu, and Binyan Jiang (2026), *Tools Are Not Islands: Set-Level Tool Retrieval for LLM Agents via Query-Conditioned Hyperedge Prediction*, arXiv:2607.25718。
- Paper: https://arxiv.org/abs/2607.25718
- Code: https://github.com/stormwther18/HYSET

HYSET 將 Tool Set 作為整體評分單位，納入工具間的共同使用關係及集合大小相關的相容性；此方法定位為 CEAA Tool Selection 的外部研究 baseline，不等同於 CEAA 的 Experience-aware Decision Model。

後續實驗在相同任務、工具庫、執行環境與預算限制下比較：

1. LLM-only Tool Selection：由 LLM 直接選擇工具。
2. Independent Top-K Retrieval：逐一排序工具並取 Top-K。
3. HYSET Set-Level Retrieval：依原論文與公開實作重現。
4. CEAA Experience-aware Decision Model：使用歷史執行結果選擇 Agent / Skill / Tool。
5. Ablation：CEAA 移除 Experience、移除 Cost-aware Ranking，以及移除階層式 Routing。

評估指標：Recall@K、COMP@K、Tool Set Exact Match、End-to-End Task Success、LLM Calls、Total Tokens、Latency、Retry Count、Cost per Successful Task；額外量測不同 Experience / Reuse Count 下的學習曲線與 Break-even Point。

公平比較要求：固定資料切分、模型與工具版本；區分訓練與測試任務，避免 Experience Leakage；將訓練、索引建立與維護成本納入長期成本分析。HYSET 與 CEAA 解決的問題範圍不同，需另外報告 Tool-Selection-only 與 End-to-End 兩組實驗結果。

### Adaptive Skill Tiering & Performance Evolution — Additional Experiments

**Experiment A — Difficulty-Aware Skill Routing**：在相同 task families 與任務難度分層下，比較 (A1) Always-L3、(A2) Always-L1 with escalation、(A3) Rule-based Tier Routing、(A4) Learned Difficulty/Cost-aware Routing；記錄 task success、tier-selection accuracy、escalation/retry rate、latency、total cost、Cost per Successful Task，並依風險與難度分組。

**Experiment B — Usage-Driven Skill Optimization**：比較 (B1) No Optimization、(B2) Periodic Optimization、(B3) Frequency-only Prioritization、(B4) Frequency × Expected Saving × Confidence / Failure-impact Prioritization。追蹤 skill version、usage/reuse count、regression failures、quality、latency、maintenance/training cost、cumulative saving 與 break-even count；包含高階 Skill 專用化為低成本 Skill 的案例。

**Experiment C — Skill Complexity Compression（研究假設）**：驗證原本需要 L3 複雜推理與多工具協作的 Skill，是否能透過重複執行、經驗累積及版本迭代，在明確限定的相同任務範圍內，逐漸達到 L2 甚至 L1 的執行成本，同時維持成功率、輸出品質與可靠性。

實驗分組：C1 原始 L3 Skill；C2 固定週期優化版本；C3 Experience-driven Skill Optimization 版本；C4 原生 L1/L2 Skill（如適用）。分開記錄 Capability Level 與 Execution Cost Tier，避免將成本下降誤判為能力下降，或將專用化能力誤認為完整泛化能力。

評估指標：Skill Compression Ratio（原始與優化版本的 Cost per Successful Task 比值）、Capability Retention Rate、成功率、延遲、LLM/Tool Calls、重試率、優化與維護成本、累積淨節省、Break-even Reuse Count。採用固定的領域內測試與領域外回歸測試，繪製迭代次數對成本與品質的曲線，並檢查安全與相容性退化。成本下降及能力保留均屬待驗證假設，不預設必然成功。

**新增實驗目的**：評估 CEAA 能否在核心架構、模組介面及治理邊界保持穩定時，透過 Decision Evolution 與 Skill Complexity Compression，持續降低整體 Cost per Successful Task，而不犧牲已驗證的任務能力與安全性。

**共同控制**：固定測試集、模型、工具版本與資源限制；按時間切分 Experience，避免測試資料洩漏；報告統計不確定性及不同難度／風險子群；所有優化版本必須通過既有 Secure Evolution Gate、獨立審核與人員核准，不得將實驗自動套用至生產。

Phase 3 應產生至少以下圖表或結果：

```text
Cumulative Tokens vs. Number of Tasks
Average Tokens per Task vs. Reuse Count
Task Success Rate vs. Reuse Similarity
Latency vs. Reuse Count
Capability Creation Cost vs. Lifetime Reuse Saving
Break-even Reuse Count by Task Family
```

此實驗的目標不是預設 CEAA 一定更省 Token，而是實證：

> **Capability accumulation 是否能將一次高成本學習，轉換成後續較低成本的可重用執行經驗。**

---

### Hierarchical Skill Packages × Decision Rationale × Validated Path Reuse — New Research Experiment

**研究目的**：驗證 Skill 增長時，分層 Package Routing + Package-local Experience 是否可以透過避免重複多層推論，降低端到端 latency、tokens 與 **Cost per Successful Task**；並驗證第一次規劃保存的**結構化 Decision Rationale**是否比只有 execution path 的紀錄多提供可量化的決策改進。與既有 Decision Evolution、Skill Tiering / Complexity Compression、Failure-driven Recovery 實驗整合，**不取代**其 baseline。

**研究假說**：H-P1 分層路由在大 Skill Pool 中勝過 flat route（扣除額外 lookup / local decision 開銷）；H-P2 validated plan reuse 對 exact / near-similar 任務比每次重新規劃有效；H-P3 rationale + expected/observed comparison 改善 routing error diagnosis 和未來 selection accuracy；H-P4 local experience 的益處隨使用次數增長，但有冷啟動與 drift 的失效邊界。

**統一實驗組**（同樣的 task family、相同模型與版本、工具、風險政策、資源配額及成功 oracle）：

- A：Flat Agent → 全量 Skill routing，每次重新規劃。
- B：Global Package Router → Local Decision，但不存取 Experience。
- C：B + Raw Execution Path History（僅 path evidence，不含 rationale 或已驗證快取）。
- D：C + Validated Execution Path Registry / fast path。
- E：D + structured Decision Rationale + predicted-vs-observed feedback + experience-aware policies（完整 CEAA candidate）。

**控制與消融**：另外移除 local memory、rationale、path validator、fast path、version/permission matching、lightweight router、fallback；固定 retry/policy 以避免安全差異干擾比較。分層檢查 package selection error、local selection error、跨 package coordination error、unavailable skill、distribution shift、new environment、false-positive match、cache staleness。候選方案與決策理由不得包含隱藏推理；所有評估以 externally validated outcome 為準。

**工作負載**：Exact / Near-similar / Generalized，1→N 相同 task-family 序列、不同 package 數量與 skill 數量（含跨包任務）；新型與 high-risk 任務獨立分析。train/dev/holdout 按 task family 和時間切分，避免 Experience Leakage。每次執行留下 trace、rationale summary、decision model/version、candidate IDs、predicted outcome、actual outcome、cache hit/miss、lookups、validation 與全部成本。

**主要指標**：end-to-end Task Success、validated plan reuse correctness、package/skill/path selection accuracy、error propagation、routing tokens、global/local routing latency、p50/p95 total latency、fast-path hit rate、hit/miss fallback cost、TTFT（如有）、total tokens、Cost per Successful Task、rationale recording overhead、regression/unsafe reuse rate、cold-start / break-even reuse count、樣本數與置信區間。分析決策記錄長度與資訊價值，禁止僅因 candidate count 減少就宣稱加速。對照最短可行流程與 no-package baseline。

**Phase 1 限制**：只準備可追溯資料契約與可測試的 Telemetry foundation，不要求這些實驗在 Phase 1 完成。Phase 2 PoC 驗證 replay / fast-path contract，Phase 3 正式測試成效。


### Failure-driven Self-Recovery / Reliability Evolution — Experiment Design（新增）

**研究目的與假說**

- **H-R1（Recovery）**：在相同故障分布與成本限制下，達 retry 上限後啟動根因診斷及受控修復，能否比 fixed retry / fallback 提高 end-to-end task success 與 recovery success？
- **H-R2（Efficiency）**：選擇性啟動單一／多個專業診斷 Agent，能否在維持成功率與安全性的前提下，降低 Cost per Successful Task、平均恢復時間與不必要的診斷開銷？
- **H-R3（Learning）**：經驗證的修復紀錄沉澱為 Recovery Skill 後，能否隨同類故障重現次數增加，降低 repeated failure rate、分析 Token 與恢復成本？
- **H-R4（Governance）**：獨立安全審核與回歸測試，能否減少錯誤修復與新增缺陷，而不使恢復成本或人工作業負擔超出可接受門檻？

**實驗機制（Phase 2 單 Agent PoC；Phase 3 完整比較）**

1. 建立具可重現種子的 fault-injection benchmark：provider timeout / 429、network interruption、tool schema mismatch、bad tool selection、skill semantic error、stale cache、permission denial、partial side effect、dependency failure、ambiguous completion；另設不可自動修復的 negative controls。
2. 每組使用相同任務、模型版本、工具權限、硬體、failure seeds、時間/成本上限與 success oracle；依 fault category、severity、task family 分層，train/dev/test 與 holdout 分離，避免 Experience Leakage。
3. Baselines：**B0** no retry；**B1** fixed bounded retry；**B2** retry + rule-based fallback；**B3** retry + single diagnosis Agent；**B4** retry + selective multi-Agent diagnosis；**B5 CEAA** adaptive diagnosis + Experience Memory + validated Recovery Skills + governance。
4. 每次執行完整記錄：trace / original failure / retry lineage / diagnosis agents / proposed root cause / candidate repair / gate decision / checkpoint / final outcome / token / latency / cost / human intervention。對未能恢復的任務亦保留資料。
5. 消融：移除 Experience Memory、specialist routing、root-cause evidence、regression gate、checkpointing、cost-aware budget、Recovery Skill reuse；並比較不同 retry cap、repair-cycle cap、故障難度與 L1/L3 Skill 等級。
6. 縱向實驗：對相同 fault family 反覆注入新樣本，觀察 Recovery Skill 從昂貴診斷流程轉成低成本重用後，是否維持能力、安全性與跨環境泛化。

**主要指標與判準**

- End-to-End Task Success、Recovery Success Rate（以符合恢復資格的 failure episode 為分母）、Correct Root Cause Rate（由外部 oracle / evidence 判定）、Repeated Failure Rate、MTTR / P95 recovery latency。
- Cost per Successful Task = 所有執行、重試、診斷、修復、驗證與治理成本 / 成功任務數；另報告 Recovery Cost、Token、Tool Calls、human review time、break-even reuse count。
- Unsafe Repair Rate、Regression Rate、False Repair Rate、Unauthorized Action Rate、Human Escalation Rate；安全問題不可因平均成功率提高而被忽略。
- 對成功率與成本提供重複試驗、置信區間及依 failure family 分層結果；不可只以單次 demo 或單一成功案例宣稱 Self-Recovery 有效。

**實驗預期驗證的研究貢獻**：驗證「失敗→診斷→受控修復→可重用恢復經驗」是否能形成可量化、可治理的 Reliability Evolution 閉環，並檢查 Recovery Skill Complexity Compression 是否可在保持修復能力的情況下降低後續成本。這是**待驗證假說**，非既有實驗結果。

---

# 61. Phase 4 — Background Evolution

新增：

- Redis
- RQ

讓：

- Evolution
- Testing
- Notification

進入 background worker。

---

# 62. Phase 5 — Stronger Sandbox

需要時再加入：

- gVisor
- Firecracker
- Kata Containers

---

# 63. Phase 6 — Admin Dashboard

未來加入：

- Streamlit
- 或正式 Web UI

管理：

- Capability
- Reports
- Approval
- Notifications

---

# 64. Phase 7 — Local LLM

未來硬體適合時加入：

- Ollama
- llama.cpp
- vLLM

---

# 65. Phase 8 — Enterprise Validation

驗證：

- File processing
- Data workflows
- IT automation
- DevOps
- Enterprise procedures

---

# 66. Phase 9 — Cybersecurity Extension

加入：

- MITRE ATT&CK
- Wazuh
- Sysmon
- Velociraptor
- Atomic Red Team
- Zeek
- Suricata
- CALDERA
- Cyber Range

---

# 67. Phase 10 — Capability Sharing Infrastructure

## Future Reserved Development

此階段目前只進行架構預留。

未來開發：

```text
CapabilityImportService
CapabilityExportService
CapabilityPublishingService
CapabilityDiscoveryService
CapabilitySyncService

SharedCapabilityRegistry
```

以及：

```text
Capability Package
Signature
Trust Model
Sanitization
Compatibility Validation
```

---

# 68. Phase 11 — Capability Marketplace

## Long-Term Productization

可能建立：

```text
Capability Marketplace
Organization Registry
Global Registry
Publisher Verification
Capability Reputation
Capability Subscription
```

目前完全不列入 MVP。

---

# 69. 專案演進路線

```text
Single Process
     ↓
Modular Monolith
     ↓
Background Workers
     ↓
Multi-Agent System
     ↓
Enterprise Deployment
     ↓
Multi-Tenant Platform
     ↓
Shared Capability Registry
     ↓
Capability Marketplace
     ↓
Collective Capability Network
```

---

# 70. 建議專案結構

```text
src/
├── agents/
│   ├── main/
│   ├── evolution/
│   └── testing/
│
├── services/
│   ├── capability/
│   ├── gap_detection/
│   ├── evolution/
│   ├── validation/
│   ├── testing/
│   ├── policy/
│   ├── approval/
│   └── notification/
│
├── domain/
│   ├── capability/
│   ├── task/
│   ├── experiment/
│   ├── report/
│   ├── approval/
│   └── events/
│
├── interfaces/
│   ├── llm/
│   ├── storage/
│   ├── sandbox/
│   ├── queue/
│   ├── notification/
│   ├── registry/
│   └── observability/
│
├── infrastructure/
│   ├── postgres/
│   ├── git/
│   ├── docker/
│   ├── litellm/
│   └── pgvector/
│
├── future/
│   ├── capability_import/
│   ├── capability_export/
│   ├── shared_registry/
│   ├── capability_sync/
│   └── marketplace/
│
├── api/
├── schemas/
└── config/
```

`future/` 中的內容在目前階段只保留：

- Interface
- Schema
- ADR
- Placeholder

不實作完整 Business Logic。

---

# 71. 現階段的重要邊界

目前需要真的做：

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

目前只需要預留：

```text
Export
Import
Publish
Discover
Sync
Marketplace
Collective Network
```

這兩部分必須明確分開。

---

# 72. 商品化後的使用者控制

未來產品至少應讓使用者設定：

```text
Allow capability sharing?
[Yes / No]

Allow external capability discovery?
[Yes / No]

Allow capability recommendations?
[Yes / No]

Allow capability downloads?
[Manual / Organization Only / Trusted Sources]

Allow automatic updates?
[No / Notify Only / Trusted Capabilities]
```

預設使用最保守設定。

---

# 73. 最終能力流

本地學習：

```text
Task
 ↓
Gap
 ↓
Evolution
 ↓
Validation
 ↓
Testing
 ↓
Report
 ↓
Approval
 ↓
Local Capability
```

可選分享：

```text
Local Capability
 ↓
User Opt-In
 ↓
Sanitize
 ↓
Package
 ↓
Publish
```

可選取得：

```text
Shared Registry
 ↓
User Opt-In
 ↓
Download
 ↓
Local Validation
 ↓
Local Testing
 ↓
Report
 ↓
Approval
 ↓
Local Agent
```

---

# 74. 最終願景

Capability-Evolving Agent 不只是一個：

> 能自己建立工具的 Agent。

而是一個完整的能力生命週期系統：

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

未來商品化後，再增加：

```text
Share
→ Discover
→ Transfer
→ Validate Locally
→ Adopt
```

因此最終可以形成：

> **一個讓每個 Agent 都能獨立成長，同時又可以在使用者明確授權下交換經過驗證能力的 Capability Ecosystem。**

模型本身可以保持可替換。

Agent 的真正長期資產則變成：

> **它累積、驗證並被允許使用的 Capability Library。**
