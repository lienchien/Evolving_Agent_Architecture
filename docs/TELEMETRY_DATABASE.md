# Execution Experience／Evolution Telemetry Database

更新日期：2026-10-18

實作分支：`feature/execution-telemetry-database`

## 目的與邊界

本階段先以 SQLite 建立 Phase 1 所需的 durable operational-history 資料層，同時讓
domain、service 與測試只依賴 backend-neutral `TelemetryRepository`。未來 PostgreSQL
以另一個 adapter 實作相同 contract，不要求 Agent、service 或 API 改寫 SQL。

目前完成的是**資料庫與 repository foundation**，尚未把 MainAgent、EvolutionAgent、
Capability execution 或 API runtime 的事件自動寫入這些表，也尚未提供 telemetry summary API。

## Domain 與 Repository Contract

`src/domain/telemetry.py` 定義：

- `ExecutionTrace`
- `RoutingDecision`
- `ExecutionObservation`
- `ExecutionFailure`
- `RecoveryAttempt`

`src/interfaces/telemetry_repository.py` 定義保存、完成、讀取與依 trace 查詢的抽象介面。
SQL、SQLite exception、JSON encoding、PRAGMA 與 migration 不可出現在 domain 或 service。

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

2026-10-18 feature 完整測試結果為 **35 passed, 1 warning in 8.93s**；合併至 `dev`
後再次執行為 **35 passed, 1 warning in 12.04s**。警告仍為既有 Starlette／AnyIO
`BlockingPortal` alias 棄用。

## 下一步

1. 建立 telemetry service／transaction boundary。
2. 為 task 建立一致的 task ID 與 trace ID，並與既有 token/cost metrics 關聯。
3. 在 routing、execution、failure、retry 與 fallback 路徑寫入 observations。
4. 加入 operational-history query／summary API 與 failure recurrence 聚合。
5. 驗證 instrumentation failure 不改變主要 task outcome。
6. Phase 1.5 再加入 PostgreSQL adapter，執行同一套 contract tests 與 migration 驗證。
