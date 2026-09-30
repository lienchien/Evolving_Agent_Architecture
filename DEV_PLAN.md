# Capability-Evolving Agent — Phase 1 Development Plan

更新日期：2026-09-30

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

## 候選增量：Token／費用研究量測

研究契約已納入 Phase 1 文件，詳見
[TOKEN_COST_RESEARCH.md](docs/TOKEN_COST_RESEARCH.md)。候選實作位於
`feature/token-cost-research` 的 `ca08851`，文件紀錄為 `d3270fc`，尚未合併 `dev`。

在決定合併程式前應重新檢查：

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

## Phase 1.5 與後續

在上述 Phase 1 Telemetry 退出條件完成後，再依序評估：

1. LiteLLM adapter、NVIDIA NIM/OpenRouter、provider fallback/health check；保留 Mock 測試。
2. PostgreSQL repository、migration 與 runtime configuration。
3. Docker sandbox、資源限制、檔案隔離、network policy 與 cleanup。
4. 更多 boundary/failure/regression/generalization/safety 測試及 performance metrics。
5. 將真實 provider usage 寫入 Phase 1 已建立的研究資料模型，禁止估算缺失 token。

Phase 2 再加入 embedding/pgvector、語意檢索、相容性與排序；之後評估 tracing、
實驗追蹤、Redis/RQ 背景 worker、更強隔離、管理介面及企業場景。
Sharing／Import／Export／Marketplace 仍是 Future Reserved。

核心依賴方向維持 **Agent → Service → Interface → Infrastructure Adapter**。
