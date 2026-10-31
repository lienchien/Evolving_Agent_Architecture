# Execution Experience／Evolution Telemetry Database

更新日期：2026-10-31

目前實作分支：`feature/provider-failure-stage`

## 目的與邊界

本階段先以 SQLite 建立 Phase 1 所需的 durable operational-history 資料層，同時讓
domain、service 與測試只依賴 backend-neutral `TelemetryRepository`。未來 PostgreSQL
以另一個 adapter 實作相同 contract，不要求 Agent、service 或 API 改寫 SQL。

目前已完成資料庫/repository foundation，以及 Phase 1 的 runtime wiring：MainAgent 會以同一組
`task_id` / `trace_id` 記錄 capability routing、evolution/execution observation、normalized
failure 與 final outcome。`TelemetryService` 隔離 instrumentation failure，避免遙測失敗改變
主要 task outcome，並透過 traces/detail/summary API 提供重啟後讀回、成功率、失敗率與 failure
recurrence。Runtime 現已支援 fail-closed bounded retry：只有明確冪等且屬暫時性失敗的 operation
可在能力設定與全域 hard cap 內重試；未知／非冪等、不可恢復、budget 耗盡或達上限時一律停止並
保存政策決定。當 retry 不可用或耗盡時，只有明確 `fallback_eligible`、同 tenant／owner／organization／
scope／trust、輸入相容且冪等的 active alternate target 才能依 `routing_priority` 選用；每個 target
單次任務最多執行一次。不合格 alternate 不會產生 fallback 事件。

## Domain 與 Repository Contract

`src/domain/telemetry.py` 定義：

- `ExecutionTrace`
- `RoutingDecision`
- `ExecutionObservation`
- `ExecutionFailure`
- `RecoveryAttempt`
- `FailureContext` / `RetryDecision` / `DecisionEvidence`
- `FailureAnalysis` / `RecoveryPlan` / `RecoveryGateResult` / `RecoveryOutcome`

`src/interfaces/telemetry_repository.py` 定義保存、完成、讀取與依 trace 查詢的抽象介面。
SQL、SQLite exception、JSON encoding、PRAGMA 與 migration 不可出現在 domain 或 service。

`src/interfaces/retry_policy.py` 與 `src/interfaces/recovery.py` 定義 bounded retry、failure analysis、
recovery planning/gate 與 outcome repository 的 backend-neutral contract。Phase 1 僅提供 contract
與 mock fail-closed tests；不建立自主診斷／修復 Agent，也不授予 recovery plan 執行權限。

`src/services/telemetry_service.py` 是 runtime instrumentation 與 operational-history read model
的 backend-neutral 邊界。寫入錯誤會記錄 log 並增加 process-local
`instrumentation_failure_count`；原始 task input、secret 與 exception message 不寫入 telemetry。

## Runtime API

- `GET /api/telemetry/traces`：以 `task_id` / `task_family` / `capability_id` / `target_id` /
  `failure_category` / `exception_type` / `outcome` / timezone-aware time window 篩選 trace，支援分頁。
- `GET /api/telemetry/traces/{trace_id}`：讀取 routing、observation、failure 與 recovery 關聯。
- `GET /api/telemetry/summary`：支援相同篩選，回傳 final-outcome denominator、success/failure
  rate、事件數、retry/fallback/recovery 數、normalized failure recurrence，以及可持久重建的
  `missing_event_count` / `missing_event_trace_count`。

`POST /api/tasks` 的 response 新增 `trace_id`，且既有 token/cost task／interaction metric 使用
相同 `task_id` / `trace_id`，可在不複製 payload 的前提下進行關聯。

## SQLite Schema v1

| 資料表 | 用途 |
|---|---|
| `telemetry_schema_migrations` | 記錄 adapter schema version，拒絕未知的較新版本 |
| `execution_traces` | task／trace correlation root 與 final outcome |
| `routing_decisions` | routing layer、candidate count、selected target、score/confidence 與 parent decision |
| `execution_observations` | execution／retry／fallback／policy observation 與 target outcome |
| `execution_failures` | normalized failure stage/category、exception type、recoverable 與 sanitized summary |
| `recovery_attempts` | failure 對 retry／fallback／human escalation 的關聯與結果 |

重要索引涵蓋 task、task family、trace time、selected target、target/outcome、failure pattern
與 recovery attempt。Foreign key 使用 trace-aware composite constraints，避免 decision、
observation、failure 或 recovery 被錯接到另一條 trace。

SQLite adapter 啟用 foreign keys、15 秒 busy timeout 與 WAL。初始化採交易式、非破壞性
`CREATE TABLE/INDEX IF NOT EXISTS`；在既有 Capability database 加入 telemetry schema
不會刪除或改寫 Capability、Report、Approval、Audit 或 research metrics。

## PostgreSQL 替換邊界

後續 `PostgresTelemetryRepository` 應實作相同 contract，並遵守：

- ID 由應用程式產生，不依賴 SQLite rowid／autoincrement；
- timestamp 一律帶 timezone，PostgreSQL 使用 `TIMESTAMPTZ`；
- SQLite `TEXT` JSON 可映射為 PostgreSQL `JSONB`，轉換只存在 adapter；
- transaction、conflict 與 unknown-trace 行為須通過同一套 repository contract tests；
- backend selection 由 composition root／configuration 決定，不滲入 service；
- PostgreSQL migration 與 SQLite migration 分開管理，但維持相同資料語意。

目前 Container 可注入任意 `TelemetryRepository`；預設仍以相同 database path 建立
`SqliteTelemetryRepository`。PostgreSQL dependency、DSN 與 adapter 尚未加入。

## 驗證

`tests/test_telemetry_repository.py` 是可供未來 PostgreSQL adapter 重用的 contract suite，涵蓋：

- 完整 trace → routing → failed observation → failure → retry/recovery round trip；
- 關閉並重建 repository 後資料仍可讀取；
- task／task-family filter 與 trace 只能完成一次；
- duplicate ID 與跨 trace 關聯被拒絕；
- schema v1、必要 tables/indexes 與 WAL；
- timezone validation；
- 既有 Capability 資料在 migration 後保持不變；
- 較新未知 schema version 被舊程式拒絕。

2026-10-31 Phase 1 退出修訂後完整測試結果為 **59 passed, 1 warning in 14.69s**。除成功、partial、
validation failure、execution exception、重啟讀回、summary denominator/recurrence 與
instrumentation isolation 外，亦覆蓋 bounded retry、unsafe retry blocked、retry exhaustion、
time/cost budget exhaustion、RecoveryAttempt 重啟持久化、trace/cost correlation、完整查詢 filter
、受治理 fallback 的優先序／單次執行／父子 decision lineage／成功與失敗 outcome、跨 scope 拒絕
、16 個並行 task 的 identity isolation、故障注入 missing-event detection／重啟讀回與 optional contract
向後相容。警告仍為既有 Starlette／AnyIO
`BlockingPortal` alias 棄用。

## Missing-event detection 與並行退出證據

`TelemetryService.summarize()` 會從 durable trace 及子事件重建資料完整性訊號：已完成 trace 若沒有
任何 observation，計為一個 missing event；非失敗的已完成 trace 若沒有 routing decision，再計一個。
`missing_event_trace_count` 計算至少缺一項核心事件的 trace 數，`missing_event_count` 計算缺失的核心
事件類別總數。這兩項來自 SQLite durable history，因此 process 重啟後仍可重建；
`instrumentation_failure_count` 則維持 process-local 即時寫入失敗計數，兩者語意刻意分離。

此 detector 能辨識「已存在的 completed trace 缺少核心子事件」，不能從 telemetry 單一資料源推斷
從未成功寫入的 root trace，也不能猜測任意未定義的中間事件。Root trace 寫入失敗仍由即時
instrumentation counter／log 暴露，task cost metric 的 task／trace identity 可供後續跨資料集稽核；
Phase 1.5 應把 instrumentation health 接到正式監控與告警。

正式並行測試以同一 SQLite/WAL、共享 Container 和 8 個 worker 同時執行 16 個已啟用 capability
任務，確認 task ID、trace ID、routing decision、execution observation 與 cost metric 一對一關聯、
沒有跨 trace 污染，且重啟讀回的 summary 完全一致。

## Alternate-target fallback invariant

Capability registry 將 active target 分為一個 primary 與零個以上明確 alternate。SQLite 以
`uq_capabilities_primary_active_family` 保護每個 task family 只有一個 primary active；生成／審核中的
reservation 則由 `uq_capabilities_reserved_family` 獨立保護。舊版涵蓋 `active` 的唯一索引會在啟動時
由非破壞性 migration 替換；若既有資料含多個 primary active，啟動會明確失敗，不會自行選擇或刪除資料。
初始 task routing 與 generation reservation 只認 primary；fallback-only active 不會被當作一般 target，
也不會阻擋建立新的 primary reservation。

Fallback routing 會保存新的 child `RoutingDecision`，以 `parent_decision_id` 連回失敗 target 的 decision，
並記錄完整候選、selected target/version、policy version、fallback reason、可稽核 evidence 與限制。
對應 observation 使用 `kind=fallback`，`RecoveryAttempt(strategy=fallback)` 連回觸發它的原始 failure；
成功或再次失敗都會持久化。Task API 與 cost metric 另回報 `fallback_count`，因此 fallback 成本不會被隱藏。

## Planned extension — Package / Path / Decision Rationale evidence（2026-10-20）

**Optional contract 已實作，SQLite v1 六表不變。** 新欄位存在 versioned JSON data envelope；既有 row 以 default/null 向後相容讀回，因此不需要為 optional 欄位進行破壞性 migration。

目標：同一份 append-only raw operational history 支援 Global Package Decision → Local Skill Decision → ordered/branched Execution Path → Result Validation → curated reusable path。Package 僅需邏輯隔離；不建立每個 Package 一套獨立 DB。若沒有 package，package ID 保持 null。

**已加入 optional 欄位／事件**：`package_id`, `package_version`, `path_id`, `path_version`, `step_id`, `parent_step_id`, `sequence/branch`, `candidate_ids`, `selected_target_version`, `DecisionEvidence`（`rationale_summary`, `selection_criteria`, `evidence_refs`, `expected_outcome`, `observed_outcome`）與 `policy/model_version`。`decision_scope`、`validation_status`、`cache_hit` 仍待實際使用案例再加入。父子決策、失敗／重試與 trace ID 必須能關聯，缺失值用 null，不推估信心與成本。

**Rationale 邊界**：儲存可檢查的簡短決策摘要和候選取捨，不儲存 LLM private chain-of-thought、secret、完整敏感 payload；與事後 observed outcome 分離。不要讓遙測寫入失敗改變主要 task outcome，但需可觀測 instrumentation failure。

**階段**：Phase 1 僅確立 optional schema contract、必要 lineage、測試及現有 telemetry wiring；Phase 2 建立 curated Validated Execution Path Registry / package-local read models；Phase 3 驗證決策理由與快取的增益、成本及安全回歸。curated paths 與 raw traces 保持不同生命週期與驗證流程。


## 下一步

Provider／LLM capability generation 與 boundary-test generation failure 已從通用
runtime/execution 改為 `stage=provider`，並保存固定 error code、去敏摘要、原始 exception type
及 provider operation metadata。

Phase 1 正式 checklist（包含並行 task telemetry correlation 與 missing-event 行為）已在目前 feature
分支完成。後續工作：

1. 整合此 feature 分支至 `dev`。
2. 視查詢量決定是否將 service-side filter／summary 下推為 repository aggregate contract。
3. Phase 1.5 加入 PostgreSQL adapter，執行同一套 contract tests 與 migration 驗證，並將
   instrumentation health 接入正式監控／告警。
