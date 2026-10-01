# Capability-Evolving Agent — Phase 1 Development Plan

更新日期：2026-10-01

## 目前基準

**Phase 1 — In Progress：Core Baseline 已驗證；Execution Experience & Evolution Telemetry Foundation 納入 Phase 1 必做項目。**

目前分支為 `dev`；既有 Core Baseline 與 Token／費用研究功能已完成驗證，但 **Phase 1 尚未退出**。Phase 1 現在必須補齊 Execution Experience & Evolution Telemetry Foundation。既有量測包含 task／LLM interaction
成本觀測、SQLite 持久化與研究 API。最近完整測試為 **28 passed, 1 warning in 7.12s**。
實作仍採 Mock LLM、SQLite、Python subprocess 與 Console Notification。
本輪實際過程見 [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md)，完成度見
[PROJECT_STATUS.md](PROJECT_STATUS.md)。

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

上述行為與資料庫升級細節以 [API_CONCURRENCY.md](docs/API_CONCURRENCY.md) 為準。
授權與資料控制本輪不啟用；既有安全註記需保留。

## 已整合基礎：Token／費用研究量測

研究契約與實作均已納入 `dev`，詳見 [TOKEN_COST_RESEARCH.md](docs/TOKEN_COST_RESEARCH.md)。目前 Core Baseline 為 **28 passed, 1 warning**；此量測基礎保留為 Phase 1 已驗證能力，下一個必做項目是 Execution Experience & Evolution Telemetry Foundation。

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
- [ ] Durable execution observation schema，可保存 success / failure / retry / fallback。
- [ ] Task / trace / routing decision correlation。
- [ ] Candidate set、selected target、routing depth / parent decision（適用時）持久化。
- [ ] Normalized failure stage / category，同時保留可分析的 raw exception metadata。
- [ ] Retry / fallback 與原始 failure 關聯。
- [ ] Success denominator 與 failure recurrence / failure-rate 聚合。
- [ ] 可依 task family / capability / target / exception type / time window 查詢 operational history。
- [ ] Restart 後 telemetry 仍可讀回。
- [ ] 成功、失敗、retry、缺失 metrics、持久化與 correlation 測試。
- [ ] Telemetry 與既有 `llm_interactions` / `task_cost_metrics` 使用一致 task / trace identity。

完成後 Phase 1 才可重新標記為 **Complete**，並進入 Phase 1.5 的 real infrastructure / hardening。

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

## Phase 1.5 — Real Infrastructure + Controlled Code Evolution

在上述 Phase 1 Telemetry 退出條件完成後，Phase 1.5 不只替換 mock infrastructure，也開始實作 System Design v1.8 定義的第一條受控 Code Evolution 路徑。

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

Phase 1.5 正式加入 v1.8 的程式生成 execution layer。

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
- 至少一個 real coding-agent adapter；可評估 Pi-like / Codex-like runtime，但 CEAA core 不綁單一實作。
- temporary branch / worktree / candidate workspace。
- Builder iteration / time / token / cost / test-run budget。
- Builder 不可直接寫 production branch、activate registry 或取得 raw production credential。
- BuildResult / Candidate Artifact 包含 code diff、tests、dependency change、build log、known limitations、model/provider provenance。
- 至少完成一個小型 Skill 的 end-to-end「讀 repo → 寫 code → 寫 tests → run → revise → candidate」驗證。

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
