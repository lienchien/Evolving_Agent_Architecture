# Capability-Evolving Agent — Project Status

更新日期：2026-09-18

開發分支：`codex/feature-api-integration`

## Current Stage

**Phase 1 — Automated Core/API/Concurrency Validation Passed; Standalone Server Validation Pending**

核心 mock 流程、FastAPI TestClient 整合、併發一致性與跨程序持久化已取得執行證據。
最近完整測試結果為 **25 passed, 1 warning in 6.84s**。
這不是 production-ready 或任意負載下的效能保證；Phase 1 尚待獨立 Uvicorn/HTTP 驗證收尾。

歷史過程見 [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md)；API 行為及升級條件見
[API_CONCURRENCY.md](docs/API_CONCURRENCY.md)。

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

目前 adapter 仍為 MockLLMProvider、SQLite、Python subprocess、Console Notification。
Queue 保留擴充介面，Phase 1 不透過它執行背景任務。

## Runtime 證據

- `.venv`：Python 3.14.3、pytest 9.1.1；相關 API 與 LangGraph 依賴可載入。
- 原始套件 6 項測試通過；API 開發後 9 項；container 修復後 12 項；本輪併發修復後 25 項。
- 24 個同類 HTTP 請求跨兩個 app：只生成一個能力；24 次核准只有一次成功，其餘回 409。
- 受控核准／拒絕交錯：只有一方成功，沒有被拒絕能力被舊資料覆蓋啟用的情形。
- 4 個獨立 Python 程序：只有一個取得生成名額；核准競爭只有一方成功。
- Report、ApprovalRecord、Audit 在另一 app、重啟及新程序均可讀取。
- 注入 audit 寫入失敗：能力狀態、限制及核准紀錄全部回滾。
- Windows 預設 pytest 暫存目錄曾遇到權限問題，改用唯一、可寫的測試目錄後通過。
- 一項既有 Starlette/AnyIO `BlockingPortal` 棄用警告；測試未因此失敗。

測試範圍是 TestClient HTTP 整合、真實 SQLite 及 subprocess；不是外部網路壓力測試。
本輪測試產物已清理，repository 內較早提交的範例報告不作為本輪執行證據。

## 尚未完成與已接受限制

- [ ] 獨立啟動 Uvicorn，從外部 HTTP client 完整操作並保存 runtime log。
- [ ] 手動核對 Console Notification、報告輸出與 API 結果。
- [ ] 長時間負載、吞吐量、延遲、鎖定逾時及故障復原驗證。
- [ ] 程序強制終止後的生成名額自動復原／租約。
- [ ] 認證、管理員角色與 tenant/owner/scope 資料控制。
- [ ] 執行 restrictions 的真正政策引擎，以及請求大小／資源配額。
- [ ] 將 registry 分頁下推資料庫；目前仍載入完整清單後切片。

依開發階段決策，授權與資料控制維持現狀，已在路由加上 `TODO(security)`。
`reviewer` 仍是呼叫端提供的值；subprocess 不具安全隔離，LLM 仍為固定模板。
所有 worker 必須同時升級並使用相同 SQLite 路徑；跨主機部署未納入本次驗證。

## Phase 1 退出條件

- [x] pytest 實際執行並通過。
- [x] mock 核心循環、功能失敗與修訂路徑通過。
- [x] HTTP 整合的核准、啟用、重用與報告查詢通過。
- [x] 併發去重、決策交易、跨實例持久化通過。
- [ ] 獨立伺服器啟動與手動 API 驗證，保存相關證據。

因此目前不標記 `Phase 1 Complete`。下一步見 [DEV_PLAN.md](DEV_PLAN.md)。

## 後續階段

| 階段 | 規劃與狀態 |
|---|---|
| Phase 1.5 | 尚未開始：LiteLLM、NVIDIA NIM/OpenRouter、PostgreSQL adapter/migration、Docker sandbox、更多邊界與安全測試 |
| Phase 2 | 規劃：pgvector、embedding、語意檢索、相容性篩選與排序；目前僅完成 task_family 精確去重 |
| Phase 3 | 規劃：tracing、Phoenix/DeepEval/MLflow、成本／延遲／重用與回歸指標 |
| Phase 4 | 規劃：Redis/RQ、Evolution/Testing/Notification workers |
| Phase 5 | 未來：gVisor/Firecracker/Kata 等更強隔離 |
| Phase 6 | 未來：管理與研究 dashboard |
| Phase 7 | 預留：本機 LLM |
| Phase 8 | 未來：企業場景研究驗證 |
| Phase 9 | 未來：資安領域驗證 |
| Phase 10 | 預留：能力 import/export/publish/discover/sync |
| Phase 11 | 長期：Marketplace／Collective Capability Network |
