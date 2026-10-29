# Execution Experience／Evolution Telemetry Database

更新日期：2026-10-26

目前實作分支：`feature/telemetry-runtime-wiring`

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
保存政策決定。現階段沒有第二個合格 target，因此不製造虛假的 fallback 成功事件。

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
  rate、事件數、retry/fallback/recovery 數與 normalized failure recurrence。

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

2026-10-26 P1 修訂完整測試結果為 **52 passed, 1 warning in 11.85s**。除成功、partial、
validation failure、execution exception、重啟讀回、summary denominator/recurrence 與
instrumentation isolation 外，亦覆蓋 bounded retry、unsafe retry blocked、retry exhaustion、
time/cost budget exhaustion、RecoveryAttempt 重啟持久化、trace/cost correlation、完整查詢 filter
與 optional contract 向後相容。警告仍為既有 Starlette／AnyIO
`BlockingPortal` alias 棄用。

## Planned extension — Package / Path / Decision Rationale evidence（2026-10-20）

**Optional contract 已實作，SQLite v1 六表不變。** 新欄位存在 versioned JSON data envelope；既有 row 以 default/null 向後相容讀回，因此不需要為 optional 欄位進行破壞性 migration。

目標：同一份 append-only raw operational history 支援 Global Package Decision → Local Skill Decision → ordered/branched Execution Path → Result Validation → curated reusable path。Package 僅需邏輯隔離；不建立每個 Package 一套獨立 DB。若沒有 package，package ID 保持 null。

**已加入 optional 欄位／事件**：`package_id`, `package_version`, `path_id`, `path_version`, `step_id`, `parent_step_id`, `sequence/branch`, `candidate_ids`, `selected_target_version`, `DecisionEvidence`（`rationale_summary`, `selection_criteria`, `evidence_refs`, `expected_outcome`, `observed_outcome`）與 `policy/model_version`。`decision_scope`、`validation_status`、`cache_hit` 仍待實際使用案例再加入。父子決策、失敗／重試與 trace ID 必須能關聯，缺失值用 null，不推估信心與成本。

**Rationale 邊界**：儲存可檢查的簡短決策摘要和候選取捨，不儲存 LLM private chain-of-thought、secret、完整敏感 payload；與事後 observed outcome 分離。不要讓遙測寫入失敗改變主要 task outcome，但需可觀測 instrumentation failure。

**階段**：Phase 1 僅確立 optional schema contract、必要 lineage、測試及現有 telemetry wiring；Phase 2 建立 curated Validated Execution Path Registry / package-local read models；Phase 3 驗證決策理由與快取的增益、成本及安全回歸。curated paths 與 raw traces 保持不同生命週期與驗證流程。


## 下一步

1. 將 provider／LLM generation failure 從通用 runtime/execution 對應至 provider stage/category，
   並補上對應查詢與測試。
2. 為未來多候選 capability/tool 定義 eligibility 與安全 alternate-target fallback；在此之前不建立
   不存在的 fallback runtime 事件。
3. 完成 Phase 1 正式 checklist 驗收，包含並行 task telemetry correlation 與 missing-event 行為。
4. 視查詢量決定是否將 service-side filter／summary 下推為 repository aggregate contract。
5. Phase 1.5 再加入 PostgreSQL adapter，執行同一套 contract tests 與 migration 驗證。
