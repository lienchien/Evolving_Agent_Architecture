# Capability-Evolving Agent — Phase 1 Development Plan

更新日期：2026-09-20

## 目前基準

**Phase 1 — 驗證退出條件完成；進入 production hardening / Phase 1.5 準備。**

目前 `dev` 與 `origin/dev` 同步於 `773df54`，已完成 API feature、四項併發修復、
完整 pytest 及獨立 Uvicorn/HTTP 重啟驗證。最近完整測試為
**25 passed, 1 warning in 6.82s**。實作仍採 Mock LLM、SQLite、Python subprocess
與 Console Notification。
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

上述行為與資料庫升級細節以 [API_CONCURRENCY.md](docs/API_CONCURRENCY.md) 為準。
授權與資料控制本輪不啟用；既有安全註記需保留。

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

## 下一個里程碑：Production Hardening 與 Phase 1.5 Adapter

1. 為生成名額加入 lease／逾時復原，驗證程序強制終止後能安全重試。
2. 加入認證、管理員授權、可信 reviewer 及 tenant/owner/scope 資料控制。
3. 將 restrictions 接到實際執行政策，加入請求大小、資源與執行配額。
4. 執行長時間負載、延遲、SQLite lock timeout 與故障復原量測。
5. 依序評估 LiteLLM、PostgreSQL 與 Docker sandbox adapter；保留 Mock/SQLite 測試基線。

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
API、併發測試分別位於 `tests/test_api.py`、`tests/test_concurrency.py`；
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

在 Phase 1 驗證收尾後依序評估：

1. LiteLLM adapter、NVIDIA NIM/OpenRouter、provider fallback/health check；保留 Mock 測試。
2. PostgreSQL repository、migration 與 runtime configuration。
3. Docker sandbox、資源限制、檔案隔離、network policy 與 cleanup。
4. 更多 boundary/failure/regression/generalization/safety 測試及 performance metrics。

Phase 2 再加入 embedding/pgvector、語意檢索、相容性與排序；之後評估 tracing、
實驗追蹤、Redis/RQ 背景 worker、更強隔離、管理介面及企業場景。
Sharing／Import／Export／Marketplace 仍是 Future Reserved。

核心依賴方向維持 **Agent → Service → Interface → Infrastructure Adapter**。
