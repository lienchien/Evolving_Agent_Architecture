# Capability-Evolving Agent — Project Status

更新日期：2026-09-20

開發分支：`feature/token-cost-research`（基於 `dev` 的 `6f2fd1d`）

功能提交：`ca08851`（`feat: add token cost research instrumentation`）；尚未合併至 `dev`。

## Current Stage

**Phase 1 — Verified Core plus Token/Cost Research Instrumentation**

核心 mock 流程、FastAPI TestClient 整合、併發一致性與跨程序持久化已取得執行證據。
獨立 Uvicorn 已完成 loopback HTTP 全流程與停止／重啟持久化驗證；新增 Token／費用
量測基礎後，完整測試結果為 **28 passed, 1 warning in 6.42s**。
這不是 production-ready 或任意負載下的效能保證；安全與營運強化仍屬後續工作。

歷史過程見 [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md)；API 行為及升級條件見
[API_CONCURRENCY.md](docs/API_CONCURRENCY.md)。
Token／費用欄位與研究限制見 [TOKEN_COST_RESEARCH.md](docs/TOKEN_COST_RESEARCH.md)。

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

## Phase 1 退出條件

- [x] pytest 實際執行並通過。
- [x] mock 核心循環、功能失敗與修訂路徑通過。
- [x] HTTP 整合的核准、啟用、重用與報告查詢通過。
- [x] 併發去重、決策交易、跨實例持久化通過。
- [x] 獨立伺服器啟動、外部 HTTP 操作、報告／log 核對及重啟持久化通過。
- [x] Token／費用研究的 task／interaction 持久化、API、unavailable 規則與衍生計算基礎通過。

Phase 1 的驗證退出條件已完成；下一步進入 production hardening 與 Phase 1.5 adapter
工作，詳見 [DEV_PLAN.md](DEV_PLAN.md)。

## 後續階段

| 階段 | 規劃與狀態 |
|---|---|
| Phase 1.5 | 尚未開始：LiteLLM、NVIDIA NIM/OpenRouter、PostgreSQL adapter/migration、Docker sandbox、更多邊界與安全測試 |
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
