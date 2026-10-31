# Capability-Evolving Agent — Phase 1 Development Plan

更新日期：2026-10-31

## 目前基準

**Phase 1 — Complete on `dev`：Core Baseline 與 Execution Experience & Evolution Telemetry 正式退出條件均已驗證。**

Phase 1 feature 分支為 `feature/provider-failure-stage`，已合併至 `dev`；既有 Core Baseline 與 Token／費用研究
功能已完成驗證。Telemetry 的 backend-neutral domain／repository、
SQLite schema v1、runtime writing、bounded retry、Recovery contracts 與 summary/filter API 已建立；
provider failure stage、受治理 alternate-target fallback、並行 correlation 與 durable missing-event detection
已完成正式驗收。Phase 1 在 `dev` 完成。
合併後 `dev` 的完整測試為 **59 passed, 1 warning**（2026-10-31）。
實作仍採 Mock LLM、SQLite、Python subprocess 與 Console Notification。
本輪實際過程見 [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md)，完成度見
[PROJECT_STATUS.md](PROJECT_STATUS.md)。

## 核心設計補充：Cross-domain Context-Aware Adaptive Decision（2026-10-26；Design Only）

**研究總目標：** CEAA 不固化於任何單一應用；面對任務、環境與限制變動，動態評估候選 Skill／Package／Plan／策略（包括不執行及升級人工），比較效用、風險、機會成本與資源使用，選擇在當下資訊下相對適當的可行方案，再由獨立驗證結果與決策歷史驅動受控調整。此為設計與待驗證假說，不是當前已驗證的正期望值或獲利能力。

**階段整合；不擴大現有 Phase 1 退出條件：**

- **Phase 1（既有 Telemetry 工作）：** 保留 task/trace、候選與路由結果、policy、執行結果、版本與錯誤連結。未來的 context snapshot/reference、目標／約束、替代候選與 optional expected-vs-observed 可先定義可擴充契約；**不要求立即增加完整市場／領域資料接入、Regime Detector 或 Decision Optimizer**。
- **Phase 1.5（安全治理）：** 現有身分、權限、隔離、Audit 和 Human Approval 管理延伸至環境資料與決策執行；跨領域資料不得越權混用。
- **Phase 2（受控 PoC）：** 設計 domain-neutral `ContextSnapshot`、`DecisionObjective`、`CandidateAction`、`RiskAssessment`、`DecisionEvidence` 與可替換 Domain Adapter；優先以 deterministic/rule-based baseline 檢驗上下文條件、候選適用性、abstain/fallback 與策略路由。概念漂移偵測與環境分類為研究候選，非必須先搭建完整金融預測引擎。
- **Phase 3（跨場景評估）：** 至少兩個異質領域，含穩定／變動／資料缺失／Out-of-Distribution 情境；比較固定 Workflow、單一策略、無 Context、Context-aware Router、含歷史回饋等消融。量測 verified task utility/success、risk violations、opportunity cost proxy、recovery/adaptation latency、decision stability、calibration、false reuse、CPS（含檢索／審核／路由成本）、跨領域遷移工時；正式實驗事先定義 oracle、風險預算、共同資訊邊界與停損條件，避免未來資訊洩漏。
- **長期（視實驗結果）：** 將跨場景適應延伸至自適應 Agent 組織及更大規模系統；高風險領域保留專屬政策與人類控制，不宣稱所有場景都能自動最佳化。

**實驗判準：** 相對最佳是「在給定資訊／可行候選／目標／治理限制下的決策品質」，不是事後挑出最高報酬路徑；改善幅度需相對明確 baseline，且在完整成本與風險約束下成立。

---

## 開發方向基準（Direction Baseline / Scope Guard，2026-10-26）

> **決策：固定核心研究問題、系統邊界與階段順序；不凍結技術選型、實驗假說或必要的安全修正。**
>
> 核心目標：建立**跨領域、環境感知、風險受控的自適應決策架構**，在當前資訊、權限、資源及不確定性條件下比較可行候選（含 abstain／human escalation），尋找相對較佳的決策，並以獨立結果驗證和持久化經驗驅動調整。**不宣稱全域最優、正報酬或任務成功保證。**

### 固定的架構原則（Design Invariants）

1. **Domain-neutral Core**：Task/Objective、Context、Decision、Capability、Risk/Policy、Outcome/Evidence 的共用契約不內建任何金融、新聞、DevOps 或企業業務規則；領域差異放在可替換的 Adapter / Skill Package / Validator。
2. **Decision before execution**：保留候選方案、選擇依據（可稽核的結構摘要，非模型隱藏推理）、適用條件、風險／機會成本、限制及版本。無合格候選時允許放棄、延期、Fallback 或交由人工。
3. **Governed capability evolution**：新能力與新版本必須通過獨立測試、Policy / Secure Evolution Gate 與必要人工核准；任何 Decision/Memory 重用不得繞過授權與當次結果驗證。
4. **Raw evidence first**：成功、失敗、路由、Retry/Fallback、成本、實際結果都持久記錄；Raw History 與 Curated/Validated Experience 分離，支持失效分析與可重現實驗。
5. **Measurable relative improvement**：相對最佳解只在明確任務目標、可得資訊、候選與約束下成立；新機制須與固定 Workflow／無 Memory／純規則／LLM baseline 做公平對照，衡量品質、尾端風險、成本與適應能力。
6. **Interface-first and replaceable infrastructure**：維持 Agent → Service → Interface → Infrastructure Adapter，不綁特定模型、資料庫、框架、Builder 或硬體。

### 固定的交付順序與階段門檻

| 順序 | 當前或目標工作 | 進入下一階段前的證據 |
| --- | --- | --- |
| **Phase 1 — 已完成（`dev`）** | 完成 Execution Telemetry Runtime、Recovery contracts、Routing/候選、成功與失敗、Retry/Fallback、Task/Trace 關聯、Summary API、重啟持久性及 Token/Cost 對齊 | Runtime wiring、bounded retry、recovery contracts、provider failure stage、受治理 alternate-target fallback、並行 correlation 與 missing-event 正式驗收均已通過並合併至 `dev` |
| **Phase 1.5 — 原定下一階段** | 真實 LLM/usage、PostgreSQL、隔離 Sandbox、受控 Builder、Main/Audit 與 Policy/Human Escalation | 依既定安全、治理及受控生成驗證門檻；不因新增願景降低 Gate |
| **Phase 2 — 最小自適應決策 PoC** | Memory Router/Decision Model、Validated Path、Skill Packages、最小 Domain-neutral Context/Objective/Candidate/Risk contracts，受限候選策略選擇與 Fallback | 示範當下 Context 改變時，能依適用條件安全改選、拒絕或 Replan；保留審核和輸入新鮮度 |
| **Phase 3 — 正式研究驗證** | 至少兩個異質場景、環境漂移/OOD、完整對照與消融、Cost per Successful Task、穩定性及安全失效率 | 事前訂好 oracle、資訊邊界、風險預算；以樣本外驗證檢查是否優於 baseline，允許負面結論 |
| **更長期 — 證據驅動擴展** | Adaptive Organization、常駐監測／回復、edge/robots、Marketplace、商業化 | 依前述實驗、安全及運維成本結果逐步決定；不預先列為當前 MVP 範圍 |

### 變更控制（避免 Scope Creep）

- **固定的是 North Star 與架構約束，不是某項策略或技術。** 可替換 LLM、資料庫、Builder、Agent 組織形態或具體演算法；不修改核心目標。
- 任何新增提案都應先回答：對哪個核心假說有幫助？依賴哪個階段？所需資料／成本／安全條件？驗證指標與退出標準為何？
- 不直接插入 Phase 1 工作清單：可與現有 Telemetry Contract 低成本相容的概念先保留為 optional 欄位；其他放入 Phase 2+ / Future Backlog。
- 若需調整階段順序或退出條件，必須留下 **ADR / rationale、影響範圍、風險、替代方案、回滾與核准紀錄**；安全修正與已證明不成立的假說可以觸發變更。
- 每次完成一階段，以經驗證證據決定是否進入下一階段；避免因新研究構想而永遠延後基礎建設交付。

**Implementation status：此節是開發方向與治理基準，不代表新增 Runtime 功能或測試結果。**

---

## 已完成的工作

1. 建立可注入的 `create_app()`，container 在 lifespan 接收請求前初始化。
2. 定義能力／報告回應模型，補上不存在能力 404、狀態競爭 409 等錯誤回應。
3. 加入 status/task_family 篩選、offset/limit 分頁與 TestClient HTTP 整合測試。
4. 以 revision 條件更新與 SQLite 交易避免決策覆蓋，並原子保存核准及 audit。
5. 同步演化直接處理本次 gap，保證請求與 capability 配對。
6. 原子預留生成名額，唯一索引限制每個 task_family 的處理中／待核准／active 能力。
7. 將 Report、ApprovalRecord、Audit 改為共享 SQLite 儲存並驗證多程序行為。
8. 明確標記暫緩的授權、資料隔離、限制執行與資源管制項目。
9. 以獨立 Uvicorn 程序完成外部 HTTP 全流程，核對 runtime log、JSON/Markdown 報告、
   SQLite 治理資料，以及停止／重啟後的能力重用與資料持久化。
10. 將 H-cost 研究提前納入 Phase 1：持久化 task 與 LLM interaction 指標，提供
    明細／summary API，資料完整且有 baseline 時才計算 saving 與 break-even reuse count。
11. 建立 Execution Telemetry database foundation：五個 domain models、backend-neutral
    repository contract、SQLite schema/migration/indexes、WAL、restart persistence 與 contract tests。

上述行為與資料庫升級細節以 [API_CONCURRENCY.md](docs/API_CONCURRENCY.md) 為準。
授權與資料控制本輪不啟用；既有安全註記需保留。

## 已整合基礎：Token／費用研究量測

研究契約與實作均已納入 `dev`，詳見 [TOKEN_COST_RESEARCH.md](docs/TOKEN_COST_RESEARCH.md)。原 Token/Cost Core Baseline 為 **28 passed, 1 warning**；目前功能分支已把 task 與 interaction 接到同一 `trace_id`，並納入 54-test Phase 1 回歸。

後續接入真實 provider 前仍應重新檢查：

1. task／LLM interaction 指標是否符合真實 provider adapter 的 usage envelope；
2. unavailable token 不估算、首次待核准 task 不誤算成功的研究語意；
3. metrics API 的認證／tenant scope 風險是否接受於目前開發階段；
4. SQLite 新表、摘要查詢與 failure observation 對既有併發及 migration 的影響；
5. Feature 的 28 項測試及獨立 Uvicorn research endpoint 驗證是否需在合併前重跑。

## 已完成里程碑：獨立 API Runtime 驗證

2026-09-20 使用隔離資料庫與報告目錄啟動 Uvicorn，在同機 loopback 介面完成：

1. 提交未知 task，確認待核准 capability 與報告。
2. 查詢 capability 與 test report，核對待核准狀態及 100% pass rate。
3. 經 HTTP 核准，核對 active 狀態、ApprovalRecord 與 Audit。
4. 核准後再次提交相同 family，確認重用原能力及正確輸出。
5. 重啟服務並用相同 database path 查詢能力、報告與 audit，再次成功執行。
6. 核對 HTTP 200、runtime log、通知輸出、JSON/Markdown 報告與 SQLite 筆數；
   完成後停止服務並清理隔離測試資料。

結果為能力 `active`、報告 pass rate 100%／risk `low`、重啟前後 audit 均為 2，
隔離 SQLite 保存 1 Capability、1 TestReport、1 ApprovalRecord、2 AuditEntry。
完整執行紀錄見 [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md)。

## Phase 1 必做功能：Execution Experience & Evolution Telemetry Foundation

目前資料庫 foundation 已在 `feature/execution-telemetry-database` 完成：

- `execution_traces`
- `routing_decisions`
- `execution_observations`
- `execution_failures`
- `recovery_attempts`
- `telemetry_schema_migrations`

詳細 schema、SQLite／PostgreSQL adapter 邊界與驗證見
[TELEMETRY_DATABASE.md](docs/TELEMETRY_DATABASE.md)。目前 service／runtime wiring、有界重試、
Recovery contracts、failure aggregation、查詢增量與 provider failure stage 已完成；仍不能在
既定並行／missing-event 驗收已完成，Phase 1 已在 `dev` 標記完成；下一階段為 Phase 1.5。

這不是未來才做的 Adaptive Agent Organization 功能，而是**現在就必須建立的研究資料基礎**。

目的不是讓系統立即自動 Split / Merge Agent，而是從目前的單一／早期 routing 流程開始，持續保存**完整 operational history**。Raw exception、成功 execution、retry、fallback、routing decision 都是未來可分析的資料，不要求先完成 root-cause diagnosis 才保存。

除了回答單一 task 為什麼失敗，也必須能回答 population-level 問題：

- 某個 exception 為什麼持續大量重複？是否集中在特定 Agent / Skill / Tool / environment？
- failure count 的 denominator 是多少，實際 failure rate 是否惡化？
- 哪一層做錯決策？
- 正確候選是否曾經出現在 candidate set？
- 錯誤是 routing、skill selection、tool execution、policy、provider 還是 runtime failure？
- retry / fallback 是否成功修復？
- capability 數量增加後，selection error 是否上升？
- token、latency、cost 與錯誤率之間的關係為何？

最低資料契約應保留：

~~~text
Task / Trace
 ↓
Routing Decision
 ├─ layer / node
 ├─ candidate set
 ├─ selected candidate
 ├─ confidence / score (if available)
 └─ decision latency
 ↓
Execution
 ├─ Agent / Skill / Tool
 ├─ retry / fallback
 └─ policy decision
 ↓
Outcome
 ├─ success / failure
 ├─ failure stage
 ├─ failure category
 ├─ error code / normalized reason
 └─ human correction / final resolution
 ↓
Research Metrics
 ├─ token usage
 ├─ latency
 ├─ cost
 └─ capability reuse / generation
~~~

建議新增的持久化概念：

- `routing_decisions`
- append-only / durable execution observations（成功與失敗都保留）
- `execution_failures` 或等價的 normalized failure observation
- task / trace correlation ID
- parent decision / routing depth
- candidate count 與 candidate identifiers
- selected target
- routing confidence / score（若 router 可提供）
- failure stage / category / recoverable
- retry count / fallback target
- final outcome

資料模型必須允許目前只有一層 routing，也能在未來自然擴充成：

~~~text
Root
→ Manager
→ Agent
→ Sub-Agent
→ Skill
→ Tool
~~~

也就是現在蒐集的不只是 **future organization experiments 的 longitudinal baseline**，也是未來 Experience Memory、system diagnosis 與 Evolution Signal 的原始歷史資料層。

資料概念：

~~~text
Raw Operational History
   ├─→ Episode Resolution → Curated Experience Memory
   └─→ Population Mining → Systemic Pattern → Evolution Signal
~~~

Raw data 不因為重複而失去價值；大量重複本身可能正是需要檢查或演化的訊號。

### 實作原則

1. **先觀測，不自動重組。** 現階段不實作自動 Split / Merge / Create / Retire。
2. **錯誤資料不可只存在 log。** 需要結構化、可查詢、可與 task / interaction 關聯。
3. **保留完整成功與失敗母體。** 10 萬筆 exception 本身可能是重要訊號，但仍需成功 execution 作 denominator，才能區分高頻低比例與真正高 failure rate。
4. **Raw failure 不需先被解決才有價值。** 未分類／未解決 exception 仍應保留，後續可用 clustering、frequency、trend、correlation 回推 systemic problem。
4. **未知值不可猜測。** 沒有 confidence、token 或 cost 時保存 unavailable / null。
6. **failure taxonomy 要穩定。** 原始 exception 可保留，但研究分析應使用 normalized category。
7. **避免保存敏感 payload。** 優先保存 identifier、metadata、hash / summary 與分類結果。
8. **Telemetry failure 不應改變主要 task outcome。** 但應有可觀測的 instrumentation failure 記錄。
9. **Schema 從單層開始但支援遞迴。** 透過 parent decision / depth / node type 避免未來重做資料模型。

### 第一階段驗收

- 成功 task 可查到完整 task → routing → execution → outcome 關聯。
- routing / capability miss / tool failure / provider failure 至少可區分。
- retry / fallback 可追蹤到原始失敗。
- 可統計 success count、failure count、failure rate、exception recurrence、wrong-selection proxy、retry recovery rate。
- 可對大量 raw exceptions 依 type / path / environment / time window 做聚合，找出 repeated/systemic failure clusters。
- 可依 task family / capability / selected target / failure category 查詢。
- 與既有 `llm_interactions`、`task_cost_metrics` 共用 task / trace correlation。
- 測試覆蓋成功、失敗、retry、缺失 metrics、持久化與重啟讀回。
- 後續可直接加入 Manager / Sub-Agent routing decision，而不需破壞 schema。

這項工作應與真實 provider usage / baseline runner 並列為下一個工程里程碑，而不是延後到未來的 Observability Phase。

---

## Phase 1 更新後退出條件

Phase 1 不再以既有 28-test Core Baseline 作為完整退出點。既有結果保留為 **Core Baseline Verified**，但必須完成以下 telemetry foundation 才能正式標記 Phase 1 Complete：

- [x] Core capability evolution loop、approval、reuse、persistence 與 concurrency baseline。
- [x] Task / LLM interaction token-cost measurement foundation。
- [x] Durable execution observation schema，可保存 success / failure / retry / fallback。
- [x] Task / trace / routing decision correlation。
- [x] Candidate set、selected target、routing depth / parent decision（適用時）持久化。
- [x] Normalized failure stage / category：routing／selection／tool／validation／provider 已接入且不保存敏感 exception message；capability generation 與 boundary-test generation 皆映射至 provider stage。
- [x] Retry / fallback 與原始 failure 關聯：bounded retry 與合格 alternate-target runtime fallback 均已完成。
- [x] Success denominator 與 failure recurrence / failure-rate 聚合。
- [x] 可依 task family / capability / target / exception type / time window 查詢 operational history。
- [x] Restart 後 telemetry 仍可讀回。
- [x] 成功、失敗、retry、缺失 metrics、持久化與 correlation 測試。
- [x] Telemetry 與既有 `llm_interactions` / `task_cost_metrics` 使用一致 task / trace identity。
- [x] 並行 task 的 trace／decision／observation／cost correlation 無交叉污染，重啟後一致。
- [x] Completed trace 核心事件缺失可由 summary 偵測，且重啟後仍可重建。

完成後 Phase 1 才可重新標記為 **Complete**，並進入 Phase 1.5 的 real infrastructure / hardening。

---

## Failure-driven Self-Recovery — Phased System Design (2026-10-19)

**Decision: Approved for system design / Planned; NOT implemented.** This section extends the current System Design v1.9 baseline without claiming runtime capability or changing the v1.9 architecture artifact. Implementation must remain behind governance gates.

### Motivation and flow

When an execution fails, a bounded Retry Controller may retry only when the operation is safe and recoverable. If retries are exhausted (or an error is non-retryable), emit a durable failure event and invoke a diagnostic workflow. A Failure Analysis Manager may select one or more specialized agents based on failure category and cost/risk budget; a Repair Planner proposes candidate remediations; an independent Recovery Gate verifies permissions, regression evidence, and side effects before resuming from a safe checkpoint or escalating to a human.

```text
Task → Execution → Result Validator
                    ├─ PASS → Outcome / Experience Telemetry
                    └─ FAIL → Failure Classification / Retry Controller
                                 ├─ Safe + within attempt/time/cost budgets → bounded retry
                                 └─ Exhausted / unsafe → Failure Analysis Manager
                                      → Trace / Root Cause / Tool / Skill / Environment analysis (selective)
                                      → Repair Plan / Candidate (isolated)
                                      → Policy + Sandbox + Regression + Secure Recovery Gate
                                           ├─ PASS → safe checkpoint resume → validation
                                           └─ FAIL / UNKNOWN / risky → halt + human escalation
                                      → durable Recovery Outcome / Experience Memory candidate
```

### Phase 1 — interfaces and evidence foundation (required now)

Build upon existing `execution_traces`, `routing_decisions`, `execution_observations`, `execution_failures`, `recovery_attempts`; do not introduce a parallel logging silo.

- Define backend-neutral contracts (design names, not yet code): `RetryPolicyInterface`, `FailureAnalysisInterface`, `RecoveryPlannerInterface`, `RecoveryGateInterface`, `RecoveryOutcomeRepository`.
- Minimal structures: `FailureContext` (task/trace/span, failure_id, stage, normalized category, sanitized exception metadata, skill/tool/model/version, checkpoint), `RetryDecision` (recoverable, retry_count/max_retries, idempotency/side-effect status, remaining time/cost budgets, backoff), `RecoveryPlan` (candidate action, scope, risk, evidence requirements, rollback), `RecoveryOutcome` (diagnosis, attempted remediation, gate decision, validation, resolution, cost/latency).
- Durable event lineage: original failure → retry attempts → escalation/analysis → candidate repair → gate decision → final outcome. Keep both successful and failed executions as denominator for population analysis.
- Distinguish retryable transient errors from semantic, policy, authorization, state/side-effect and permanent errors. Non-idempotent actions must not be blindly retried; ambiguous completion must first be reconciled.
- Contract tests with Mock diagnostics: bounded retry, retry exhaustion, unsafe retry blocked, failed/unknown gate fails closed, budget exhaustion, restart-persistent correlation, redacted payloads. **No autonomous repair Agent required for Phase 1 exit.**
- Implemented on `feature/telemetry-runtime-wiring`: `RetryPolicyInterface`, `FailureAnalysisInterface`, `RecoveryPlannerInterface`, `RecoveryGateInterface`, `RecoveryOutcomeRepository`; the minimum retry/recovery data contracts; fail-closed bounded retry and denied/unknown gates; budget/retry exhaustion; unsafe-retry blocking; durable lineage; restart persistence and redaction tests. `feature/provider-failure-stage` adds explicit provider-operation errors, maps capability/boundary-test generation failures to sanitized provider-stage telemetry, provides a bounded alternate-target fallback restricted to explicit same-scope, input-compatible, idempotent active capabilities, and completes formal concurrent/missing-event exit verification. Phase 1 is complete and merged into `dev`.

### Phase 1.5 — integration hardening

Connect contracts to real provider fallback/health checks, sandbox execution, identity/policy enforcement, audit and existing Main + Audit Secure Evolution Gate; add time/cost budgets, checkpoint/resume and human escalation hooks. Repair candidates must not mutate production or bypass approval.

### Phase 2 — single-agent diagnostic MVP (planned)

Implement a bounded Failure Analysis Agent with trace/context retrieval, normalized root-cause hypothesis and evidence, repair plan proposal, safe sandbox validation, human-reviewed remediation where needed, and curated Recovery Experience Memory. Compare against fixed retry-only and rule-based fallback baselines. Only validated successful repairs become reusable Recovery Skills.

### Phase 3 — multi-agent adaptive recovery and experiments (planned)

Add selective specialist diagnosis (Trace / Root Cause / Tool/API / Skill / Environment), experience-aware diagnosis routing, repair candidate ranking and cost-aware recovery. Evaluate fixed retry, retry+fallback, single-diagnosis-agent and multi-agent selective diagnosis under the same injected-failure workload. Ablate experience memory, diagnosis routing, independent regression gate and specialized agents. Track recovery success, mean time to recovery, repeated failure rate, repair regression, false repair, human escalation, end-to-end task success and **cost per successful task** including diagnosis/repair overhead and amortized optimization cost.

### Non-negotiable governance and stopping conditions

- No unbounded recursive repair loops; separate retry limit, repair-cycle limit, time/cost ceilings and cancellation.
- Fail closed on missing evidence, permission denial, Main/Audit disagreement, timeout or unknown security outcome; notify Human Administrator.
- Maintain independent reviewer context and full provenance/versioning; repaired artifacts pass complete gate again.
- Protect secrets/PII in trace and memory; no unauthorized tool access or privilege escalation.
- Keep raw operational history separate from curated, validated recovery experience.
- Treat **Reliability Evolution** as a research track integrated with Capability, Decision and Performance Evolution; do not claim proven autonomous improvement before experiments.

---

## Hierarchical Skill Packages / Decision & Execution-Path Memory — Phased Integration (2026-10-20)

**Design accepted / Not implemented.** 將「首次規劃記錄候選、選擇依據與預期結果，後續以 package-local experience 重用已驗證執行路線」納入 v1.9 設計；沿用既有 Manager Decision Layer、Skill Tiering、Telemetry、Experience Memory、Secure Evolution Gate。此處的內部 Skill Package **不同於匯出／分享用 Capability Package**。

### Phase 1（與既有 Telemetry 合併，不擴張至完整 Package 功能）

- 現有 `execution_traces` / `routing_decisions` / `execution_observations` / `execution_failures` / `recovery_attempts` 作為唯一 raw evidence source。先完成既有 runtime wiring、成功與失敗的 denominator、summary API 和 restart correlation。
- Trace / Decision contract **應可表達** global/local routing、parent decision、node type、`package_id?`、`package_version?`、`path_id?`、`step_id?`、`parent_step_id?`、branch/sequence、candidate/selected target、model/policy/version、failure/retry linkage；Phase 1 可從單層 null package 開始。
- 第一次規劃的 **Decision Rationale** 使用 *structural summary*，不是模型隱藏的 chain-of-thought：task features、候選方案、選擇標準與證據引用、未選原因簡述、限制、預期成本／風險／效果與不確定性；實際觀測另記錄 `observed_outcome`。Phase 1 定義 optional fields / adapter-neutral envelope / tests；**不要求新的 LLM rationale generator**。
- Domain + repository contract tests：缺失值 null、task/trace/parent linkage、step ordering、failure path、sanitization、schema migration、restart read-back、版本相容；schema 新欄位若需要，使用 additive migration，絕不直接改寫已部署 v1 schema。
- **退出邊界不變**：不要求 Package Registry、Local Decision Agent、Validated Path Registry、fast-path execution、adaptive optimization 或完整 cross-package orchestration；它們是未來階段項目。

### Phase 1.5（既定 Real Infrastructure / Governance 工作整合）

實際 LLM provider usage、sandbox、policy permission、trace/audit identity 與完整 artifact/version provenance 接上可選 package/path metadata；避免 local decision 越權、跨租戶讀取 experience 或繞過 Main/Audit gate。

### Phase 2（與既有 Capability Retrieval 整合）

建立初版 `SkillPackageManifest` / Registry、`PackageRouterInterface`、`LocalDecisionInterface`、`ExecutionPathRepository` 及 Package-scoped Experience Lookup。採固定 package classification 或 rule-based routing 起步，再沿用 pgvector/embedding 作語意 retrieval。驗證從完整成功 trace 萃取 validated execution path 的受控 PoC，檢查 task signature、schema、版本、權限、資料新鮮度與 fallback。多包任務僅做有限跨包協作，不實作自動組織重組。

### Phase 3（與既定 Decision/Skill/Token 研究整合）

新增 **Hierarchical Skill Packages × Decision Rationale × Validated Path Reuse** 正式比較：flat routing vs package routing vs local-history vs validated fast-path vs rationale-aware learning；另做無 rationale、無 local history、無 validator、無 lightweight fast-path、無 permission/version gate 的消融，依 Exact/Near/Generalized、skills/packages 規模與冷啟動/重用次數分層。衡量 Task Success、package/skill/path routing accuracy、latency（global/local/total）、tokens、Cost per Successful Task、hit/miss fallback、rationale overhead、regression、安全及 break-even。

### 後續（Organization Evolution，非 Phase 1–3 必需）

以 longitudinal telemetry 提出 Package split/merge、dynamic membership、跨 Package Skill reuse、adaptive Package organization 候選；所有變更需版本化、獨立驗證、權限審核與人工核准（適用時）。避免自動修改 production package 組織。


## Future Research — Agent Scaling Efficiency（延期；不影響當前 Phase 1）

已將 **Experiment F — Agent Scaling Efficiency & Aggregate Token Demand** 加入 [Future Vision](docs/AGENT_PLATFORM_FUTURE_VISION.md) 和 [Token／費用研究量測](docs/TOKEN_COST_RESEARCH.md)：

- **Phase 3：** 沿用既有每成功任務 Token／Cost baseline 與 Skill／execution path reuse 研究，先驗證單任務節省率和品質。
- **Phase 3 後期：** 使用既有 telemetry、離線 trace replay 與合成流量情境研究總 Token 消耗對任務量／使用者數／Agent 活躍度的敏感性。結果需標記 *simulated*，不能與真實 token usage 混淆。
- **更遠期：** 只有取得足夠硬體或雲端預算後，才進行多 Agent／多租戶大規模並行負載與容量驗證。
- **Edge AI 與雲端升級（Experiment F.1）：** 將邊緣本地推論、24/7 設備監控、異常升級及受控修復納入後期情境；分離 edge compute 與 cloud token，評估替代與新增需求，不納入目前實作。

**Status: Deferred / Design Only / Not Implemented / Not Evaluated.** 目前本機硬體不適合大型並行實測。不可藉此提前增加 Phase 1 / Phase 1.5 的 scope 或退出條件。

---

## Manager Agent Decision Layer — Planned

Manager / hierarchical routing 的後續實作正式加入 Decision Model abstraction，但不改變目前 Phase 1 / Phase 1.5 核心退出條件。

設計原則：

~~~text
Manager State
→ bounded candidate set
→ DecisionModelInterface
→ choice / score / confidence
→ high confidence + low risk: direct dispatch
→ low confidence / conflict / novelty / high risk: reasoning LLM / stronger model
~~~

第一個 open/self-host reference adapter 規劃使用 **Laya**，以 CPU self-host 為初始 deployment baseline。Laya 只是一個 adapter，不可成為 Manager domain logic 的硬相依。

預計介面：

~~~text
DecisionModelInterface
├─ LayaAdapter
├─ LLMDecisionAdapter
└─ FutureDecisionModelAdapter
~~~

後續 Manager development 必須保存 decision telemetry：candidate set、selected target、confidence/score、decision model/version、latency、fallback/override reason 與 final outcome，直接沿用目前 Phase 1 正在建立的 `routing_decisions` / trace correlation schema。

未來正式啟用前需比較 LLM-only、decision-model-only、decision→LLM fallback 與 decision→strong-model fallback，量測 routing accuracy、bad-routing rate、task success、calibration、latency、token/cost 與 fallback/escalation rate。

Decision Model 不得繞過 Policy Engine、permission/data governance、Secure Evolution Gate 或 mandatory Human escalation。

---

## 下一個里程碑：完成 Phase 1 Telemetry，再進入真實 Usage 與 Production Hardening

1. 建立 Execution Experience & Evolution Telemetry Foundation，開始累積成功與錯誤 routing / execution 資料。
2. 讓 LiteLLM／NVIDIA NIM／OpenRouter adapter 回傳 provider 原生 token usage 與可靠費用.
3. 建立 static-agent baseline runner 與 Exact／Near-Similar／Generalized 任務資料集。
4. 為生成名額加入 lease／逾時復原，驗證程序強制終止後能安全重試。
5. 加入認證、管理員授權、可信 reviewer 及 tenant/owner/scope 資料控制。
6. 將 restrictions 接到實際執行政策，加入請求大小、資源與執行配額。
7. 執行長時間負載、延遲、SQLite lock timeout 與故障復原量測。
8. 評估 PostgreSQL 與 Docker sandbox adapter；保留 Mock/SQLite 測試基線。

## 測試與執行

已建立 `.venv` 時，從專案根目錄執行：

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

若預設 pytest 暫存目錄受限，可指定一個全新、可寫的目錄：

```powershell
$testRunPath = Join-Path (Get-Location).Path ('.test-run-' + [guid]::NewGuid().ToString('N'))
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider --basetemp=$testRunPath
```

測試資料會存入指定目錄；確認執行結束後只清理該次產物，不將資料庫或暫存檔提交。
API、併發與成本研究測試分別位於 `tests/test_api.py`、`tests/test_concurrency.py`、
`tests/test_research_metrics.py`；
原有 schema、service、full-loop、failure/revision 測試仍保留。

## 後續修正候選

- 生成名額的租約／程序中止復原，避免永久停留在處理中。
- 認證、管理員授權、可信 reviewer、tenant/owner/scope 存取控制。
- 實際執行 restrictions 的政策，以及隔離與配額。
- Registry SQL 層篩選／分頁及長時間負載量測。
- 明確的 generation retry/backoff 上限與通知重送機制。

新版本遇到同 family 多個 open 能力的舊資料庫會拒絕啟動；需先備份並明確處理
重複資料。此安全檢查不可用自動刪除歷史紀錄的方式繞過。

## Architecture Baseline v1.8 — Code Evolution & Secure Evolution Gate

2026-10-01 已完成設計層補強，新增 `Capability-Evolving Agent Architecture — System Design v1.8.md`。此版本定義未來 Main Agent 已確認 Capability Gap / Agent Gap 後，如何真正執行程式生成與安全驗證。

此項目前為 **Design Defined / Not Implemented**，不得與目前 Phase 1 runtime 能力混淆。

核心設計要求：

1. `EvolutionPlanner` 先產生結構化 `BuildSpecification`，而不是直接要求 LLM 自由生成。
2. 以可替換 `CodeBuilderRuntime` 執行 coding loop；可接 Pi-like、Codex-like 或其他 coding-agent runtime，但核心不綁單一 provider/framework。
3. Builder 預設為 ephemeral，只能在 isolated Git/worktree + sandbox candidate workspace 內寫入。
4. Builder 輸出為版本化 Candidate Artifact / BuildResult，而不是文字式「完成」。
5. Main Agent 與 Audit Agent 對 Candidate 進行獨立 first-pass cross-validation。
6. Main Agent 檢查功能、需求、架構、整合與最小權限；Audit Agent檢查 privilege escalation、資料外洩、secret、tool/process/network、dependency、cross-branch 與 recursive delegation 風險。
7. 高風險 semantic review 可呼叫 strong frontier model；但必須與 deterministic test / SAST / dependency scan / secret scan / sandbox evidence 並行，不能由 LLM 取代。
8. Audit Agent 可產生 adversarial security tests，交給 sandbox / Testing runtime 執行。
9. Secure Evolution Gate 採 fail-closed：只有 `Main=PASS AND Audit=PASS` 才能自動繼續。
10. 任一 FAIL、ERROR、UNKNOWN、timeout 或 disagreement 必須 Block、建立 Validation Incident、通知 Human Administrator。
11. Human 可 Reject / Request Revision / Quarantine / 記錄 False Positive；不提供 unrestricted Force Activate。
12. 任何 revision 都建立新 artifact version 並重新跑完整 gate。
13. 未來 Sub-Agent construction 共用同一 pipeline，並額外驗證 `P_child ⊆ P_parent ⊆ P_root` 與 `G_child ⊆ G_parent ⊆ G_root`。

Phase 1.5 應先完成這套機制的必要基礎：real provider abstraction、runtime configuration、Docker sandbox、authn/authz、policy enforcement、trace / audit identity。完整 autonomous Code Builder 與 dynamic Sub-Agent generation 在上述基礎穩定後再進入實作。

---

## Current Architecture Reference — System Design v1.9

`Capability-Evolving Agent Architecture — System Design v1.9.md` is the **current design baseline** on `dev`. The v1.8 section above is retained as historical design context; Phase 1.5 implementations and new technology evaluations should follow v1.9 and preserve its governance invariants.

---

## Phase 1.5 — Real Infrastructure + Controlled Code Evolution

在上述 Phase 1 Telemetry 退出條件完成後，Phase 1.5 不只替換 mock infrastructure，也開始實作最新 System Design v1.9 延續的受控 Code Evolution 路徑。

### Phase 1.5-A — Runtime Configuration

- 統一 runtime configuration / environment profile。
- env.example 補齊 provider、model、database、sandbox、timeout、retry、budget 與 feature flag。
- dev / test / production-like configuration 分離。
- secret 不進 repository；由 runtime injection / secret provider 提供。

### Phase 1.5-B — Real LLM Provider

- LiteLLM adapter。
- NVIDIA NIM / OpenRouter。
- provider fallback / health check。
- provider-native token usage / cost / latency。
- 保留 MockLLMProvider 作 deterministic test baseline。
- 為未來 Builder、Main Reviewer、Audit Reviewer 預留獨立 model routing policy。

### Phase 1.5-C — PostgreSQL Repository

- PostgreSQL repository adapter。
- schema migration / transaction / concurrency validation。
- Registry filtering / pagination 下推 SQL。
- Validation Incident、Builder provenance、review evidence 等 v1.8 future records 預留 persistence contract。
- 保留 SQLite 作 local / unit-test baseline。

### Phase 1.5-D — Docker Sandbox

- SubprocessSandbox → DockerSandbox。
- CPU / memory / runtime limits。
- filesystem isolation。
- explicit network policy。
- controlled mounts。
- process cleanup / timeout / failure recovery。
- 為 Builder Agent 建立 disposable candidate workspace。

### Phase 1.5-E — Code Evolution Runtime / Skill Builder MVP

Phase 1.5 正式落實 System Design v1.9 的程式生成 execution layer。

第一個實作目標先限定為 **Skill / Capability generation**：

~~~text
Capability Gap Confirmed
        ↓
Build Specification
        ↓
CodeBuilderRuntime
        ↓
Ephemeral Builder Agent
        ↓
Isolated Git / Workspace
        ↓
Inspect → Plan → Code → Test → Debug → Revise
        ↓
Candidate Capability Artifact
~~~

必要工作：

- BuildSpecification domain contract。
- CodeBuilderRuntime interface。
- 至少一個 real coding-agent adapter；**Pi 1.x 維持首選評估方案，OpenCode 新增為並列比較的候選 adapter**，Codex-like / Native Builder 亦保留為替代方案；CEAA core 不綁單一 runtime。
- 透過 `AgentRuntimeInterface` / `CodeBuilderRuntime` 封裝 Pi，不讓 BuildSpecification、Evolution Planner 或 governance logic 依賴 Pi-specific session / provider schema。
- Pi 1.x 的 multi-provider / model switching 能力可用於 Builder 內部的角色化模型組合，例如 Planner、Coder、Debugger / Repair 使用不同 model/provider；模型選擇由 CEAA `ModelPolicy` 控制，而不是由 Pi 自行決定治理策略。
- Builder runtime 必須回傳 model/provider usage、model switch、latency、cost、tool execution 與 session provenance，供研究與稽核使用。
- Pi 版本需固定並建立 adapter compatibility test；升級 Pi 前先驗證 model switching、tool calling、session state、usage/cost 與 workspace 行為，避免 runtime package 變動破壞 evolution pipeline。
- temporary branch / worktree / candidate workspace。
- Builder iteration / time / token / cost / test-run budget。
- Builder 不可直接寫 production branch、activate registry 或取得 raw production credential。
- Builder 的 multi-model session 可以共享 construction context，但 **Main Reviewer 與 Audit Reviewer 必須使用獨立 session / context**，不得直接沿用 Builder conversation；兩者 first-pass 也彼此隔離。
- Main / Audit 可以使用 Pi runtime 作為模型執行層，但必須建立獨立 runtime session，並由 CEAA 決定 reviewer model/provider policy。
- BuildResult / Candidate Artifact 包含 code diff、tests、dependency change、build log、known limitations、model/provider provenance。
- 至少完成一個小型 Skill 的 end-to-end「讀 repo → 寫 code → 寫 tests → run → revise → candidate」驗證。

#### Phase 1.5-E.1 — Builder Runtime Candidate Evaluation: Pi vs OpenCode

**Status: Planned / Not Integrated / Not Evaluated.**

- `PiBuilderAdapter`：已規劃的精簡、多模型 coding-agent runtime reference candidate。
- `OpenCodeBuilderAdapter`：新候選，評估以 OpenCode SDK / HTTP server 驅動 Session、工具與 Sub-Agent / Agent 定義的可行性。
- 二者需透過同一個 `CodeBuilderRuntime` 契約產生 `BuildResult` / versioned Candidate Artifact；不可將框架私有 session 或 schema 滲入 CEAA domain。
- 在固定 task dataset、模型/provider、prompt-policy、budget、基準 revision、隔離 workspace 下公平比較，不預設功能較多的一方表現較好。
- 比較：setup/integration effort、API/SDK maturity、model routing/fallback、Skill / AgentArtifact generation success、acceptance-test pass rate、repair iterations、token/cost、latency、session/restart recovery、trace/evidence completeness、tool permission behavior。
- 測試 Docker sandbox、Git worktree boundary、network/credential restriction、timeout/cancel/cleanup；OpenCode 內建工具權限不得替代 CEAA Policy Engine。
- 不論 Builder 選 Pi 或 OpenCode，Main/Audit 都需不同的 independent first-pass session/context；Builder self-review 不計入 Secure Evolution Gate 的兩個 PASS。
- 契約驗證與安全/成本 benchmark 完成後才確定主要 runtime。若 OpenCode adapter 成熟度不足，保留替換與回退能力。

參考：https://github.com/anomalyco/opencode

---

### Phase 1.5-F — Secure Evolution Gate

新生成 Skill 不得因 Builder 自測成功而取得信任。

實作：

- Main Agent independent functional / architecture review。
- Audit Agent independent adversarial security review。
- first-pass review context isolation。
- strong frontier-model routing for high-risk semantic review。
- deterministic security evidence：regression / integration tests、static analysis、dependency scan、secret scan、sandbox execution、filesystem / network observation。
- Audit Agent adversarial test generation。
- CrossValidationResult。
- ValidationIncident。
- Notification Service 的 HumanReviewRequired / SecurityFinding / CrossValidationDisagreement。
- full revalidation after every revision。

**Future optional tooling — Strix (not a Phase 1.5 prerequisite):**

- Add `SecurityTestingInterface` / `StrixAdapter` as an optional authorized dynamic / agentic pentest backend when baseline deterministic checks and independent reviews are stable.
- For evaluation, provision a disposable Docker target, explicit target allowlist, restrictive outbound network policy, time/resource/LLM-spend budget, evidence collection and cleanup.
- Ingest reproducible findings / PoC evidence into Audit review, Validation Incident and trace; a clean scan never automatically grants PASS, and scanner failures cannot be converted to PASS.
- Compare true/false findings, known-defect detection, reproduction quality, duration, cost and operational overhead before adoption.
- Do not give Strix uncontrolled access to production, external assets or unapproved targets. Do not make Strix mandatory for every Skill.


強制 invariant：

~~~text
AUTO_CONTINUE
iff
Main Review = PASS
AND
Audit Review = PASS
~~~

以下任何情況都必須 Block 並通知 Human Administrator：

- Main FAIL
- Audit FAIL
- ERROR
- UNKNOWN
- timeout
- disagreement

Phase 1.5 不提供 unrestricted Force Activate。

### Phase 1.5-G — Auth / Policy / Recovery / Hardening

- authentication。
- administrator role / trusted reviewer。
- tenant / owner / scope access control。
- restrictions 接到真正 runtime policy。
- request / resource / execution quota。
- generation reservation lease / TTL / crash recovery。
- retry / backoff 上限。
- provider / database / sandbox failure recovery。
- long-running load / latency / lock / fault validation。
- real provider usage 寫入研究資料模型；缺失 token 一律保持 unavailable。

### Phase 1.5-H — Sub-Agent Construction Foundation

在 Skill Builder + Secure Evolution Gate 穩定後，Phase 1.5 可開始建立未來 Sub-Agent generation 的共同底座，但**不在本階段實作完整 Recursive Multi-Agent Organization runtime**。

預計：

- AgentBuildSpecification。
- AgentArtifact / Agent Manifest contract。
- capability / tool / model / memory / permission / data / delegation binding。
- 先以 existing validated Skills composition 為主。
- 若 Agent 建立過程發現缺少 Skill，回到 Skill Generation pipeline。
- Main/Audit 雙重 cross-validation。
- frontier-model semantic security review。
- hierarchy invariant checks：

~~~text
P_child ⊆ P_parent ⊆ P_root
G_child ⊆ G_parent ⊆ G_root
~~~

Phase 1.5 的 Sub-Agent 目標是證明「可生成、可驗證、可治理的 AgentArtifact」，不是完成整個 recursive organization orchestration。

### Phase 1.5-I — Autonomous Evolution & Cross-Validation Experiments

Phase 1.5 的驗證不只確認功能可執行，也要形成正式研究實驗，量化 Skill / Sub-Agent 自動生成能力與 Main/Audit cross-validation 的有效性。

#### Experiment Group A — Skill Auto-Generation

建立分級任務集，至少包含：

- Simple：單一函式 / isolated transformation。
- Medium：需要整合既有 CEAA interface / service。
- Complex：multi-file modification、dependency、integration tests。

每個案例從 Capability Gap 開始，不預先提供完成程式，觀察 Builder 是否能自主完成：

~~~text
Gap
→ Build Specification
→ Inspect Repository
→ Write Code
→ Write Tests
→ Execute
→ Debug / Revise
→ Candidate Skill
~~~

量測：

- generation success rate
- import / compilation success rate
- acceptance-test pass rate
- iterations to success
- revision count
- build latency
- input / output / total tokens
- provider cost
- human intervention rate
- unauthorized-action attempt count

#### Experiment Group B — Sub-Agent Auto-Generation

建立需要角色分工的受控任務，驗證 Main Agent 能否自主產生 AgentBuildSpecification，優先組合既有 Skills，並產生可執行 AgentArtifact。

量測：

- AgentArtifact generation success rate
- manifest completeness
- capability composition correctness
- tool / data / permission binding correctness
- controlled task success rate
- hierarchy-invariant pass rate
- unnecessary permission request rate
- generation / revision token cost
- latency
- human intervention rate

至少驗證：

~~~text
P_child ⊆ P_parent ⊆ P_root
G_child ⊆ G_parent ⊆ G_root
~~~

Phase 1.5 不要求完整 recursive organization benchmark，但必須證明至少一個受控 Sub-Agent 能由系統自動建立、驗證並執行。

#### Experiment Group C — Reviewer Ablation

比較四種驗證配置：

~~~text
A. Builder self-review only
B. Main Agent review only
C. Audit Agent review only
D. Main + Audit independent cross-validation
~~~

建立含已知 defect / vulnerability 的 Candidate Artifact benchmark，例如：

- functional bug
- boundary-condition bug
- excessive permission
- secret exposure
- unsafe subprocess / shell execution
- unexpected network access
- data exfiltration path
- dependency / supply-chain risk
- prompt / tool injection path
- cross-branch data access
- privilege escalation
- recursive delegation bypass

核心量測：

- overall detection rate
- functional finding recall
- security finding recall
- false-negative rate
- false-positive rate
- reviewer agreement / disagreement rate
- human escalation rate
- false escalation rate
- review token cost
- review latency

目標不是預設雙 reviewer 一定較好，而是實證 Main + Audit cross-validation 是否能在可接受成本下，降低單一 reviewer 的 blind spots。

#### Experiment Group C.1 — Builder Multi-Model Runtime

若 Pi 1.x adapter 通過基本 compatibility validation，追加 Builder runtime ablation，用來確認 multi-model composition 是否真的比 single-model Builder 有價值：

~~~text
A. Single model: Plan + Code + Debug
B. Planner Model A → Coder Model B
C. Planner Model A → Coder Model B → Debugger Model C
D. Dynamic fallback / model switch under budget
~~~

量測：

- build success rate
- first-pass test pass rate
- iterations / repair loops
- model switches
- total tokens / monetary cost
- build latency
- failure recovery rate
- unnecessary model-switch rate
- artifact defect rate entering Secure Evolution Gate

此實驗的目標不是預設模型越多越好，而是判斷角色化 multi-model Builder 是否在可接受成本下提高 construction reliability。

---

#### Experiment Group D — Model Configuration Comparison

比較 reviewer 模型配置，至少保留下列研究條件：

~~~text
Config 1:
Builder = Model A
Main = Model A
Audit = Model A

Config 2:
Builder = coding / medium model
Main = frontier model A
Audit = frontier model A

Config 3:
Builder = coding / medium model
Main = frontier model A
Audit = frontier model B
~~~

研究問題：

> 不同角色與不同 model family / provider 是否能降低 correlated blind spots，並提升功能與安全問題 detection？

量測 detection、false positive / negative、cost、latency 與 escalation burden。

#### Experiment Group E — Human Escalation Effectiveness

因 Secure Evolution Gate 採 fail-closed，Human Escalation 本身也必須量測，避免 Audit 過度敏感造成不可接受的人工作業量。

量測：

- escalation rate
- true-positive escalation rate
- false escalation rate
- human review burden
- revision-after-escalation rate
- quarantine / reject / false-positive decision distribution
- time to resolution

研究目標：

~~~text
High-risk issue detection ↑
while
Unnecessary human escalation ↓
~~~

#### Experimental Integrity

- 每個 Candidate 的已知 defect ground truth 必須在 reviewer 執行前固定。
- Main 與 Audit first-pass review 必須相互隔離。
- reviewer 無法完成時記錄 ERROR / UNKNOWN / timeout，不得當作 PASS。
- provider 未回報 token / cost 欄位時保存 unavailable，不估算。
- 所有 experiment 必須保存 model / provider / prompt-policy version、artifact version、trace_id、review evidence 與 human decision。
- Builder、Main、Audit 的模型配置必須可重現。

---

## Future Research — Goal-driven Autonomous Development & Multi-Audit Verification（2026-10-24）

**Status: Future Research / Design Backlog / Not Implemented / Not Evaluated.** 本方向研究 CEAA 在非人類工作時間，依預先授權的目標契約進行有界任務規劃、程式開發、測試、修復、審查與結果交付，並量化所需人類監督量能。**不新增 Phase 1 Telemetry 或 Phase 1.5 Main/Audit Gate 退出條件；也不是目前 Runtime 可用功能。**

### Goal Contract / Bounded Autonomous Development（planned）

人類先核准 versioned `DevelopmentGoalContract`，包含：

- 身分／版本：goal/task ID、repo/base commit、允許分支／路徑、owner、policy version、授權期限。
- Goal、Expected Outcomes、可客觀測量的 Acceptance Criteria、受保護測試／Outcome Oracle、Definition of Done。
- Tool/data permissions、sandbox、模型／Provider、token/cost/time/retry limits，以及禁止修改的 Secrets、Policy、Protected Tests。
- Stop / Escalation：scope 擴張、缺少權限、critical defect、審查矛盾、未知結果、預算耗盡、不可逆行為、無法恢復的執行狀態。
- Deliverable：isolated candidate branch／PR、驗證證據、結案報告；**不預設自動 Merge、Activate 或 Deploy**。

```text
Human-approved Goal Contract
 → Durable Queue / Checkpoint
 → CEAA Planning / Scoped Memory Retrieval
 → Development Agent / Isolated Workspace
 → Implementation + Independent Tests + Bounded Repair
 → Candidate PR (commit SHA bound)
 → Multi-Audit Verification + Governance Gate
    ├─ All mandatory checks PASS → Verified Candidate + Final Report
    ├─ Repairable FAIL → limited repair and complete applicable revalidation
    └─ UNKNOWN / Risk / Conflict / Budget Exhausted → Block + Human Escalation
```

### Multi-Audit Architecture（future extension to existing Main + Audit）

**現有第 8A 節的 Main functional / architecture review + Audit security review 必須保留為強制最低基線**。未來可加入 `AuditCoordinator`，依事先核准的風險政策**增加**專業化審查：Functional Auditor（Goal / independent acceptance）、Security Auditor（permissions / secrets / exploit checks）、Architecture Auditor（interfaces / schema / contract）、Regression Auditor（protected suite / CI / upgrade）。不是所有變更固定呼叫四個大型模型，可用 deterministic tools + risk-adaptive reviewers 降低費用。

- Auditor 的 first-pass context 與 Builder／其他 Reviewer 隔離；不能依 Developer 自評或多數決覆蓋必要檢查。
- 任一 mandatory finding = FAIL / ERROR / UNKNOWN / timeout / unresolved conflict，**不得自動 PASS**。Coordinator 無權取消既有必要 Main/Audit Review、降低權限政策或繞過 Human Escalation。
- Protected Acceptance / Regression / Security Tests 與 CI Gate 不由被審查的 Development Agent 控制；每次 Revision 需重做適用的完整驗證。
- 自主工作時僅在 Preapproved Scope 內操作；PR delivery 不等於自動合併、Capability Activation 或生產部署。`8A` 必要的 Human Approval 仍須滿足。

### Unified Verification Report（planned contract）

`AutonomousDevelopmentVerificationReport` 至少記錄 goal ID、task/trace IDs、PR、base/candidate commit SHA、模型／Reviewer／Oracle／Policy 版本、每一 Acceptance Criterion 的 expected-vs-observed 結果、獨立審查結論與 evidence refs、CI/Regression/Sandbox 結果、發現與嚴重度、未驗證風險、retries/tokens/cost/latency、人工介入及最終 gate status：`VERIFIED_CANDIDATE / BLOCKED / ESCALATE / INCOMPLETE`。**Report PASS 不等於已核准 Merge / Activation / Deployment**；報告與受測 Artifact 版本必須可核對，拒絕／失敗歷史保留供稽核。

### Research Protocol & Adoption Gates（deferred）

- **Prerequisites**：Phase 1 durable telemetry、Phase 1.5 trusted Builder / Secure Gate / Auth/Sandbox、後續 Decision/Memory PoC，以及具 checkpoint/resume、lease、idempotency 與資源配額的 Background Execution；依風險逐步導入而非一次建立全天候平台。
- **Baselines**：single Auditor、mandatory Main+Audit、specialized Multi-Audit、risk-adaptive Multi-Audit。省略強制審查的對照**僅能離線／合成測試**。
- **Metrics**：Verified Goal Completion Rate、Known-defect Detection / False-negative、Escaped Defect / Regression、Human Escalation、Review Queue Backlog、P95 Verification Latency、Human Oversight Minutes per Verified Goal、Verification Cost per Accepted PR、Task Success、Cost per Successful Task、unattended execution reliability。
- **Hypothesis**：在相同品質與安全條件下，Goal Contract + Multi-Audit + Result Report 是否能增加每單位人類監督時間的**可信交付量**。不預設 Reviewer 越多越好、24h 有效開發或指數加速成立。

完整長期規劃見 `docs/AGENT_PLATFORM_FUTURE_VISION.md`。此段是 Future Research Reservation，不改寫既有正式 Phase Exit Criteria。

---

## Future Console Deployment Candidate — Render

**Reserved for later platformization; not part of Phase 1.5 scope or exit criteria.**

- `CEAA Console` planned as independently maintained React/Vite front end consuming versioned CEAA REST / SSE interfaces.
- Render Static Site is a **candidate deployment provider** for Console, docs or demonstration landing pages; alternatives remain viable.
- Consider only after authentication / CORS / API versioning / approval / incident / audit / metrics contracts stabilize.
- A hosted static UI cannot replace the CEAA agent runtime, Pi Builder, Docker sandbox, Strix security environment, PostgreSQL or background workers.
- Before deployment evaluate bandwidth/build limits, API reachability, session/authentication model, preview branch strategy and vendor cost.

---

### Phase 1.5 Exit Direction

Phase 1.5 至少應能證明：

~~~text
Real Provider
+
Real Database
+
Real Sandbox
+
Controlled Code Builder
+
Skill Auto-Generation
+
Controlled Sub-Agent Auto-Generation
+
Main/Audit Secure Evolution Gate
+
Mandatory Human Escalation
+
Measured Cross-Validation Effectiveness
~~~

可以共同運作，並讓新 Skill 與至少一個受控 Sub-Agent 從 Gap 走到 Candidate、Security Review、Human Review / Approval 與 Registry / Controlled Execution，而沒有繞過治理邊界。

Phase 1.5 Exit Evidence 應至少包含：

- Skill generation benchmark results。
- Sub-Agent generation benchmark results。
- reviewer ablation（self / Main / Audit / Main+Audit）。
- known-defect security benchmark。
- model-configuration comparison。
- detection / FP / FN / agreement / escalation / cost / latency metrics。
- 至少一個 Human Escalation incident 的完整可追溯 evidence chain。

Phase 2 再加入 embedding/pgvector、語意檢索、相容性與排序；之後評估 tracing、實驗追蹤、Redis/RQ 背景 worker、更強隔離、管理介面及企業場景。
完整 Recursive Multi-Agent Organization、Sharing／Import／Export／Marketplace 仍屬後續階段。

核心依賴方向維持 **Agent → Service → Interface → Infrastructure Adapter**。
