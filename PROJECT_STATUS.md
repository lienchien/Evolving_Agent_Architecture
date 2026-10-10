# Capability-Evolving Agent — Project Status

更新日期：2026-10-01

開發分支：`dev`（Token／費用研究功能已合併）

## Current Stage

**Phase 1 — In Progress / Core Baseline Verified; Execution Experience & Evolution Telemetry Required**

Phase 1 原有的 Core Baseline 開發與驗證條件已完成，但在確認 Execution Experience & Evolution Telemetry 是未來 Experience Memory、system diagnosis、Capability / Agent / Organization Evolution 的必要歷史資料層後，**Phase 1 退出條件已重新開啟並擴充**。

目前狀態應解讀為：**Core Baseline Verified，但 Phase 1 尚未 Complete**。下一個工作不是 Phase 1.5，而是先完成 Phase 1 的 Execution Experience & Evolution Telemetry Foundation；完成後才進入 **Phase 1.5 — Real Infrastructure & Hardening**。

核心 mock 流程、FastAPI TestClient 整合、併發一致性與跨程序持久化已取得執行證據。
獨立 Uvicorn 已完成 loopback HTTP 全流程與停止／重啟持久化驗證；新增 Token／費用
量測基礎合併後，完整測試結果為 **28 passed, 1 warning in 7.12s**。
這不是 production-ready 或任意負載下的效能保證；安全與營運強化仍屬後續工作。

歷史過程見 [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md)；API 行為及升級條件見
[API_CONCURRENCY.md](docs/API_CONCURRENCY.md)。
Token／費用欄位與研究限制見 [TOKEN_COST_RESEARCH.md](docs/TOKEN_COST_RESEARCH.md)。

## Token／費用研究整合狀態

Token efficiency／cost amortization 的研究契約與實作已合併至 `dev`，並與
[TOKEN_COST_RESEARCH.md](docs/TOKEN_COST_RESEARCH.md)、System Design v1.8、Future Vision
及平台 roadmap 對齊。

目前 `dev` 已包含：

- task／LLM interaction 成本觀測模型；
- `llm_interactions` 與 `task_cost_metrics` SQLite persistence；
- `/api/research/tasks`、`/api/research/interactions`、`/api/research/summary`；
- unavailable token 不估算的研究完整性規則；
- baseline、saving rate 與 break-even reuse count 的基礎計算；
- `tests/test_research_metrics.py`。

目前完整 runtime 基準為 **28 passed, 1 warning**。真實 provider usage、static baseline runner、
Exact／Near-Similar／Generalized 長序列實驗仍屬下一階段研究工作，不能以目前 mock 測試結果
宣稱 CEAA 已證明節省 Token。

## 新增必要基礎：Execution Experience & Evolution Telemetry

Adaptive Agent Organization 已被列為長期主力研究方向，但**自動組織演化本身尚未進入目前實作範圍**。

本次概念修正：Telemetry 不應只被視為「錯誤紀錄」。完整 operational history 本身就是平台資產。大量重複 exception 即使尚未被 root-cause resolved，也可透過 frequency、clustering、trend、routing path、environment、retry outcome 與 failure-rate denominator 找出 systemic problems。

現階段新增的必要工作是先建立可持續累積的錯誤與 routing evidence。原因是未來要比較 Flat Routing、Skill Routing、Sub-Agent、Manager Hierarchy 與 Adaptive Organization，必須有長期且結構化的 baseline，而不能只依賴 application log 或最終 task success。

目前狀態：

- [x] task-level token / cost / latency measurement foundation
- [ ] routing decision persistence
- [ ] candidate-set / selected-target persistence
- [ ] normalized failure taxonomy
- [ ] retry / fallback linkage
- [ ] task / trace / routing correlation
- [ ] routing success / failure summary API
- [ ] restart-persistent routing / failure evidence
- [ ] durable raw operational history（success / failure / retry / fallback）
- [ ] repeated-exception aggregation / systemic-pattern analysis foundation
- [ ] longitudinal dataset for future Experience Memory、Evolution Signal 與 organization experiments

預定資料鏈：

~~~text
Task
→ Routing Decision(s)
→ Agent / Capability / Skill / Tool Selection
→ Execution
→ Failure / Retry / Fallback
→ Outcome
→ Token / Latency / Cost
~~~

未來 Manager / Sub-Agent 層加入後，沿用同一 decision model：

~~~text
Root → Manager → Agent → Sub-Agent → Skill → Tool
~~~

因此這項工作不是提前實作未來 hierarchy，而是建立**現在開始就不能缺少的 longitudinal operational history**。

未來同一批資料可走兩條路：

~~~text
Raw History
├─→ Individual Episode → Resolution → Validated Experience
└─→ Population Analysis → Repeated/Systemic Pattern → Evolution Signal
~~~

也就是失敗資料不需要先被整理成「好經驗」才值得保存。

---

## Manager Decision Layer — Future Design Update

Manager / hierarchical routing 的 future design 已加入 **Decision-first, Reasoning-on-demand**：高頻、有限候選的 routing / gating / scoring 優先交給 `DecisionModelInterface`，只有低 confidence、衝突、新穎或高風險情境才升級到 reasoning LLM / stronger model。

第一個 reference adapter 規劃為 **self-hosted Laya**，初始 deployment baseline 採 CPU-first；但 Laya 不屬於 platform hard dependency。

目前狀態：

- [ ] DecisionModelInterface
- [ ] LayaAdapter
- [ ] Manager bounded-candidate routing
- [ ] confidence-based LLM fallback
- [ ] routing calibration / accuracy benchmark
- [ ] decision-model telemetry integration

因此此功能目前是 **Design Planned / Not Implemented / Not Evaluated**，不能解讀為現有 Manager Agent 已使用 Laya。

---

## Design Baseline Update — System Design v1.8

2026-10-01 已新增 `Capability-Evolving Agent Architecture — System Design v1.8.md`，補齊 CEAA 先前較抽象的 `Generate Candidate` 階段。

新增設計包含：

- Evolution Planner / Build Specification；
- replaceable Code Evolution Runtime；
- ephemeral Builder Agent + isolated workspace；
- Candidate Artifact / BuildResult contract；
- Main Agent functional / architecture review；
- Audit Agent adversarial security review；
- strong frontier-model semantic verification；
- deterministic + semantic security evidence；
- adversarial security test generation；
- Secure Evolution Gate；
- mandatory Human Administrator escalation；
- Validation Incident / quarantine / full revalidation；
- future AgentArtifact / Sub-Agent construction path。

**狀態：Design Defined / Not Implemented.**

目前 `src/` 尚未提供 CodeBuilderRuntime、Builder Agent、SecureEvolutionGate、ValidationIncidentService 或 dynamic Sub-Agent generation。因此既有 28-test Core Baseline 不可被解讀為已驗證上述新機制。

此設計的安全 invariant 為：

```text
AUTO_CONTINUE
iff
Main Review = PASS
AND
Audit Review = PASS
```

任一 FAIL / ERROR / UNKNOWN / timeout / disagreement 均要求停止自動流程並通知 Human Administrator。

---

## 已實作與驗證

| 範圍 | 證據與目前行為 |
|---|---|
| 核心流程 | Task → Gap → Generate → Validate → Test → Pending Approval → Active → Reuse 測試通過 |
| 例外流程 | Functional failure → FAILED；要求修訂後可重新生成 |
| API | 可注入的 app factory、lifespan 初始化、HTTP 查詢／核准／重用及錯誤路徑測試 |
| Registry | status/task_family 篩選、offset/limit 分頁及 response model |
| Container | 首次併發請求共用實例；保留注入實例；未啟動 lifespan 不會在請求內建立實例 |
| 狀態更新 | revision 條件更新，舊資料寫入失敗回 409 |
| 決策交易 | 最終狀態、限制 metadata、ApprovalRecord 與 Audit 原子提交；失敗全部回滾 |
| 任務配對 | 同步處理自己的 gap，不再從共用 queue 取出其他請求的工作 |
| 去重 | 每個 task_family 最多一個處理中、待核准或 active 能力；資料庫唯一索引強制保護 |
| 共享資料 | Capability、版本化 TestReport、ApprovalRecord、Audit 共用 SQLite；跨 app、重啟與新程序查詢通過 |
| 相容性 | 舊 SQLite schema 升級；遇既有重複能力明確拒絕啟動、不刪除資料 |
| 獨立 Runtime | 真實 Uvicorn 程序完成建立、報告查詢、核准、重用；停止後以同一資料庫重啟仍可查詢與執行 |
| Token／費用量測 | task ID、LLM interaction、建立／重用、outcome、usage、費用與延遲持久化；提供明細及 summary API |
| 研究完整性 | provider 未回報 token 時保存 unavailable，不推估；資料完整且提供 baseline 時才計算 saving 與 break-even |

目前 adapter 仍為 MockLLMProvider、SQLite、Python subprocess、Console Notification。
Queue 保留擴充介面，Phase 1 不透過它執行背景任務。

## Runtime 證據

- `.venv`：Python 3.14.3、pytest 9.1.1；相關 API 與 LangGraph 依賴可載入。
- 原始套件 6 項測試通過；API 開發後 9 項；container 修復後 12 項；併發修復後 25 項；
  Token／費用量測加入後 28 項。
- 24 個同類 HTTP 請求跨兩個 app：只生成一個能力；24 次核准只有一次成功，其餘回 409。
- 受控核准／拒絕交錯：只有一方成功，沒有被拒絕能力被舊資料覆蓋啟用的情形。
- 4 個獨立 Python 程序：只有一個取得生成名額；核准競爭只有一方成功。
- Report、ApprovalRecord、Audit 在另一 app、重啟及新程序均可讀取。
- 注入 audit 寫入失敗：能力狀態、限制及核准紀錄全部回滾。
- Windows 預設 pytest 暫存目錄曾遇到權限問題，改用唯一、可寫的測試目錄後通過。
- 一項既有 Starlette/AnyIO `BlockingPortal` 棄用警告；測試未因此失敗。
- 獨立 Uvicorn 驗證的 HTTP 請求均為 200；首次啟動與重啟皆完成 application startup，
  runtime log 未出現 traceback 或伺服器錯誤。
- Uvicorn 重啟後能力維持 `active`、報告 pass rate 100%／risk `low`、audit 維持 2 筆，
  相同任務再次執行得到 `word_count = 3`。
- 隔離 SQLite 最終核對：Capability 1、TestReport 1、ApprovalRecord 1、AuditEntry 2；
  JSON 與 Markdown 報告副本皆成功產生並可解析。
- Mock provider 的兩次建立 interaction 已記錄，但 token 保持 unavailable；新 app 使用同一
  SQLite 可讀回 task 與 interaction。具完整 usage 的測試 provider 驗證首次建立 100 tokens、
  第一次重用 0 LLM tokens、60 tokens/task baseline 下 1 次重用達 break-even。

測試範圍是 TestClient HTTP 整合、真實 SQLite 及 subprocess；不是外部網路壓力測試。
本輪 pytest、runtime log、SQLite 與報告產物在核對後已清理；本文件與
[DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md) 保存可版本控制的結果摘要，repository 內較早
提交的範例報告不作為本輪執行證據。

## 尚未完成與已接受限制

- [ ] Execution Experience & Evolution Telemetry：routing decision、candidate set、selected target、failure taxonomy、retry/fallback 與 outcome correlation。
- [ ] 長時間負載、吞吐量、延遲、鎖定逾時及故障復原驗證。
- [ ] 程序強制終止後的生成名額自動復原／租約。
- [ ] 認證、管理員角色與 tenant/owner/scope 資料控制。
- [ ] 執行 restrictions 的真正政策引擎，以及請求大小／資源配額。
- [ ] 將 registry 分頁下推資料庫；目前仍載入完整清單後切片。
- [ ] 真實 provider token／cost 回報、static baseline runner、reuse similarity 分類與正式長序列研究。
- [ ] 將大量研究 summary 下推 SQL／分析儲存；目前由 service 載入符合條件的紀錄後計算。

依開發階段決策，授權與資料控制維持現狀，已在路由加上 `TODO(security)`。
`reviewer` 仍是呼叫端提供的值；subprocess 不具安全隔離，LLM 仍為固定模板。
所有 worker 必須同時升級並使用相同 SQLite 路徑；跨主機部署未納入本次驗證。

## Phase 1 更新後退出條件

既有完成項目：

- [x] pytest 實際執行並通過既有 Core Baseline。
- [x] mock 核心循環、功能失敗與修訂路徑。
- [x] HTTP 整合的核准、啟用、重用與報告查詢。
- [x] 併發去重、決策交易、跨實例持久化。
- [x] 獨立伺服器與重啟持久化。
- [x] Token／費用 task／interaction measurement foundation。

新增 Phase 1 必做項目：

- [ ] Durable raw execution observations：success / failure / retry / fallback。
- [ ] Task / trace / routing correlation。
- [ ] Candidate set / selected target / routing decision persistence。
- [ ] Failure stage / normalized category / raw exception metadata。
- [ ] Retry / fallback linkage and recovery outcome。
- [ ] Success denominator、failure rate、exception recurrence aggregation。
- [ ] Operational-history query / summary capability。
- [ ] Restart-persistent telemetry evidence。
- [ ] Telemetry 與 token / cost metrics 的一致 identity linkage。
- [ ] 對 success、failure、retry、missing metrics、persistence 的自動測試。

因此 **Phase 1 = In Progress**。既有 28-test 結果代表 Core Baseline Verified，不再代表整個 Phase 1 Complete。

---

## Phase 1.5 Planned Scope Clarification

System Design v1.8 定義的 Code Evolution Runtime 與 Secure Evolution Gate 已正式納入 **Phase 1.5 預計開發項目**。

Phase 1.5 的 construction scope 採漸進策略：

~~~text
First:
Skill / Capability Builder MVP
        ↓
Main + Audit Secure Evolution Gate
        ↓
Mandatory Human Escalation / Approval

Then:
AgentArtifact Construction Foundation
~~~

完整 recursive child-Agent organization / multi-Agent orchestration 仍維持後續階段，避免 Phase 1.5 同時引入過多 coordination complexity。

目前狀態仍為 **Planned / Not Implemented**。

---

## Phase 1.5 Builder Runtime Candidates — Pi 1.x / OpenCode

Phase 1.5 的 Code Evolution Runtime 目前規劃以 **Pi 1.x 為優先評估方案**，新增 **OpenCode** 為 Builder Runtime 比較候選，用於 `CodeBuilderRuntime` / `AgentRuntimeInterface`。兩者均須提供與 CEAA 治理層解耦的 coding-agent execution adapter；最後選型需由相同 task / model / budget 條件的整合與驗證實驗決定。

規劃中的責任分工：

~~~text
CEAA
= BuildSpecification / ModelPolicy / Budget / Permission / Governance / Validation

Pi 1.x
= Builder Session / Tool Loop / Provider-Model Execution / Model Switching
~~~

Builder 內部可規劃 Planner / Coder / Debugger 使用不同模型，但模型選擇、fallback 與成本上限仍由 CEAA policy 控制。

Secure Evolution Gate 邊界不變：

- Builder session 可在 construction steps 之間共享 context。
- Main Reviewer 使用獨立 session / context。
- Audit Reviewer 使用另一個獨立 session / context。
- Main/Audit first-pass 不讀取彼此 reviewer context。
- Reviewer 不直接沿用 Builder conversation。

另新增 Pi adapter compatibility requirement：固定具體 1.x 版本，升級前測試 model switching、tool calling、session state、usage/cost 與 isolated workspace 行為。

目前狀態：**Planned / Not Implemented / Not Evaluated**。現有 `src/` 尚未包含 Pi adapter 或 multi-model Builder runtime。

---

### OpenCode candidate evaluation

- [ ] OpenCode SDK / HTTP server adapter proof of concept
- [ ] Skill / controlled AgentArtifact construction using uniform BuildSpecification
- [ ] Pi vs OpenCode generation success / test pass / repair iterations / cost / latency comparison
- [ ] Docker workspace / tool / network restrictions and independent reviewer-context verification
- [ ] Session failure / cancellation / restart and trace/provenance contract test

**Status: Candidate / Not Integrated / Not Evaluated.**

---

## Phase 1.5 Experimental Validation Scope

Phase 1.5 已正式加入研究實驗，不只驗證 infrastructure 與 feature completion。

預計實驗分為：

1. **Skill Auto-Generation**：Simple / Medium / Complex 任務，量測 generation success、test pass、iteration、token/cost、latency、human intervention。
2. **Sub-Agent Auto-Generation**：量測 AgentArtifact 完整性、Skill composition、permission/data/tool binding、controlled task success 與 hierarchy invariant。
3. **Reviewer Ablation**：Builder self-review、Main only、Audit only、Main+Audit cross-validation。
4. **Known-Defect Security Benchmark**：功能錯誤、過度權限、secret exposure、unsafe process/network、data exfiltration、dependency risk、prompt/tool injection、cross-branch access、privilege escalation、recursive delegation bypass。
5. **Model Configuration Comparison**：同模型 reviewer、frontier same-family reviewer、cross-model / cross-provider reviewer。
6. **Human Escalation Evaluation**：escalation rate、false escalation、human burden、resolution outcome。

核心研究指標包括 detection rate、functional/security recall、false-positive rate、false-negative rate、reviewer agreement、human escalation rate、token/cost、latency。

目前狀態仍為 **Planned / Not Implemented / Not Evaluated**。

---

## Optional Future Technology Candidates

| Candidate | Intended role | Timing / dependency | Status |
|---|---|---|---|
| **OpenCode** | Optional SDK / HTTP-based CodeBuilderRuntime adapter; compare with Pi 1.x on controlled Skill / AgentArtifact generation | Phase 1.5-E evaluation only; Pi remains first evaluation candidate | Candidate / Not Integrated / Not Evaluated |
| **Strix** | Optional agentic/dynamic security testing adapter for Secure Evolution Gate, under Audit review | Evaluate after Docker sandbox, deterministic checks, evidence schema and reviewer independence are working; authorized disposable targets only | Candidate / Not Integrated / Not Evaluated |
| **Render** | Optional static hosting for independently maintained React/Vite CEAA Console / public demo | Plan only after stable versioned API, auth, approval/incident/audit contracts; outside Phase 1.5 | Candidate / Not Selected / Not Deployed |

Neither changes mandatory Phase 1.5 exit criteria. Strix does not replace Main/Audit, and Render does not host the core autonomous Builder/Sandbox by default.

---

## 後續階段

| 階段 | 規劃與狀態 |
|---|---|
| Phase 1 | 進行中：Core Baseline 已驗證；目前必做 Execution Experience & Evolution Telemetry Foundation，完成後才正式退出 Phase 1 |
| Phase 1.5 | 尚未開始：Real Infrastructure + Controlled Code Evolution + Experimental Validation。除 LiteLLM/NIM/OpenRouter、PostgreSQL、Docker、auth/policy/recovery 外，實作 Skill/Sub-Agent autonomous construction、Main/Audit Secure Evolution Gate、frontier semantic review、Validation Incident、mandatory Human Escalation，並執行 reviewer ablation、known-defect security benchmark、model configuration 與 escalation-burden 實驗；不包含完整 recursive organization runtime |
| Phase 2 | 規劃：pgvector、embedding、語意檢索、相容性篩選與排序；目前僅完成 task_family 精確去重 |
| Phase 3 | 規劃：在 Phase 1 量測基礎上，以 tracing、Phoenix/DeepEval/MLflow 執行跨模型 baseline、token amortization、相似度、重用與回歸實驗 |
| Phase 4 | 規劃：Redis/RQ、Evolution/Testing/Notification workers |
| Phase 5 | 未來：gVisor/Firecracker/Kata 等更強隔離 |
| Phase 6 | 未來：管理與研究 dashboard |
| Phase 7 | 預留：本機 LLM |
| Phase 8 | 未來：企業場景研究驗證 |
| Phase 9 | 未來：資安領域驗證 |
| Phase 10 | 預留：能力 import/export/publish/discover/sync |
| Phase 11 | 長期：Marketplace／Collective Capability Network |
