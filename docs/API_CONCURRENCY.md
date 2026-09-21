# API 併發與持久化行為

## 狀態與決策

- Capability 的 `revision` 是儲存版本，每次成功更新加一。
- 更新以 SQLite `WHERE capability_id = ? AND revision = ?` 檢查舊版本；
  競爭失敗回 HTTP `409`，呼叫端應重新查詢能力狀態。
- 核准、拒絕、要求修訂只接受 `pending_approval`。
- 核准時會驗證 `pending_approval → approved → active`，一次提交最終狀態。
  限制 metadata、ApprovalRecord、Audit 也在同一交易內提交；失敗全部回滾。
- `reviewer` 仍由呼叫端提供；授權、tenant/owner 資料控制，以及 restrictions
  執行管制仍未實作，相關路由保留 `TODO(security)`。

## 任務與去重

- Phase 1 為同步演化，請求直接處理自己的 CapabilityGap，不經共享 queue。
  `/api/evolution/queue` 仍是預留介面，不代表有背景 worker 正在處理任務。
- 每個 `task_family` 最多有一個「處理中、待核准或已啟用」的能力。
  SQLite partial unique index 涵蓋 `draft / candidate / validating / testing /
  tested / pending_approval / approved / active`。
- 第一個請求以短交易預留 draft，交易結束後才執行生成與測試。
  後續同類請求回傳相同 capability ID 與當時狀態，例如 `capability_draft`
  或 `capability_pending_approval`，HTTP 狀態維持 `200`，`output` 為 `null`。
- 跟隨請求的 input 不會排入背景執行；能力核准後，需要重新提交任務才會執行。
- `failed / revision_requested / archived / deprecated / revoked` 不佔用該名額。
  新任務可建立新能力，舊能力仍保留。既有 active 需先 deprecated 或 revoked
  才能建立替代版本；目前透過 service 提供這些 lifecycle 操作。
- 可捕捉的演化例外會將處理中的能力設為 failed，讓後續請求可以重試。
  程序被強制終止時尚無租約或自動復原 worker；殘留的處理中能力需要先確認
  原工作已停止，再由管理流程處理。不可在仍執行時盲目釋放名額。

## 多實例與資料庫

- capabilities、版本化 test_reports、approval_records、audit_entries
  都儲存在同一 SQLite 檔案。多個 app／程序必須設定相同的絕對 database path。
- 報告 API 直接讀 SQLite；`capability_library/<id>/test_report.*` 是輸出副本，
  其他 worker 不需要相同的報告目錄。此次不會自動匯入既有報告副本；升級前
  已遺失的記憶體 audit／核准紀錄也無法自動還原。
- SQLite 連線完成後會明確關閉，寫入等待上限為 15 秒。這些變更保證已測試
  併發情境的一致性，不代表任意流量下的吞吐量或可用性保證。
- SQLite 檔案限同機可支援 SQLite 鎖定的檔案系統；跨主機部署不在本次範圍。

## 既有資料升級

啟動會以交易新增 `revision` 欄位、治理資料表與唯一索引。
若同 task family 已有多個處理中或 active 能力，啟動會明確失敗並保留原資料，
不會自行刪除或選擇勝出版本。需先備份，明確處理重複紀錄，再啟動升級。
所有 worker 應一起升級，避免舊版程式繞過新版 revision 檢查。

## Token／費用研究候選

`dev` 目前的持久化資料表仍只有本文件前述 Capability、Report、Approval 與 Audit。
Token／費用量測的 `llm_interactions`、`task_cost_metrics` 與 `/api/research/*` 已在
`feature/token-cost-research` 實作，但尚未合併。研究契約、unavailable 規則與驗證證據
見 [TOKEN_COST_RESEARCH.md](TOKEN_COST_RESEARCH.md)。

## 驗證

`tests/test_concurrency.py` 涵蓋：

- 受控的核准／拒絕競爭、舊版本更新拒絕。
- 不同任務並行時的 capability 配對。
- 24 請求跨兩個 app 的生成去重與核准競爭。
- 多個獨立 Python 程序的預留與核准競爭。
- 交易回滾、跨 app／程序與重啟後的報告及治理紀錄查詢。
- 舊 schema 升級及重複資料的非破壞性拒絕。
