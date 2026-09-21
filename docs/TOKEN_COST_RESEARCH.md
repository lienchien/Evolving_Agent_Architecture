# Token／費用研究量測

實作狀態：已合併至 `dev`；原始功能提交為 `ca08851`。

## 研究目的

本功能將 System Design v1.7 的 H-cost 假說提前納入 Phase 1 的執行基礎：

> Capability 第一次建立可能較昂貴，但若後續能以較少推理重用，累積成本與平均
> task 成本可能低於每次都由 static agent 重新解題。

Phase 1 的責任是可靠記錄資料並提供可重現計算；Phase 3 才使用真實 provider、
多種模型、Exact／Near-Similar／Generalized 任務序列進行正式對照實驗。

## 記錄模型

每次 `POST /api/tasks` 產生一個 `TASK-*` ID，回應會包含 `task_id`。系統保存：

- task family、capability ID／version；
- 是否由該 task 建立 capability、是否實際重用 capability；
- outcome status 與 task success；
- input／output／reasoning／total tokens；
- LLM call count、總延遲、capability execution time、retry count；
- provider monetary cost（僅在 provider 提供可靠資料時）；
- generation、testing 等 phase 的 token breakdown。

每次 LLM interaction 另存一筆資料，包括 phase、provider、model、usage source、
latency、success 與 error。這使 task 彙總可以追溯到原始 provider response。

目前同步流程的首次建立會呼叫 MockLLMProvider 兩次：generation 與 testing；重用
已啟用能力時不呼叫 LLM。首次請求只建立待核准能力、沒有完成原始 task，因此
`task_success=false`；核准後再次提交並取得 `completed` 才計為成功重用。

## 不估算缺失 token

`TokenUsage.source` 有三種值：

- `provider_reported`：數值由 provider response 提供；
- `unavailable`：provider 沒有回報，欄位保持 `null`；
- `not_applicable`：該 interaction 不使用 token。

MockLLMProvider 是本機固定模板，沒有真實 tokenizer 或模型計費。它會記錄
provider/model、兩次 call 與可靠的費用 `0.0`，但 token 欄位保持 `null`。
禁止用字元數、單字數或本地估算值冒充 provider token，reasoning token 亦同。

只要任一 LLM interaction 的 total token 不可取得，該 task 與涵蓋它的 summary 就不
產生 cumulative token、saving 或 break-even 數字。API 會以 `token_data_complete=false`
及 note 說明原因，避免不完整資料形成錯誤研究結論。

## API

```text
GET /api/research/tasks
GET /api/research/tasks?task_family=<family>&capability_id=<id>&offset=0&limit=100
GET /api/research/interactions
GET /api/research/interactions?task_id=<task-id>&offset=0&limit=100
GET /api/research/summary
GET /api/research/summary?task_family=<family>&baseline_tokens_per_task=<tokens>
```

`baseline_tokens_per_task` 必須是明確量測或研究設定，不由 CEAA 自動猜測。資料完整時，
summary 計算；break-even 必須同時指定單一 `task_family`，避免混合不同能力的重用序列：

```text
Average Tokens per Task = cumulative CEAA tokens / task count
Token Saving = cumulative baseline tokens - cumulative CEAA tokens
Token Saving Rate = 1 - (cumulative CEAA tokens / cumulative baseline tokens)
Break-even Reuse Count = cumulative CEAA tokens 首次低於 cumulative baseline 時，
                         已發生的 capability reuse 次數
```

summary 也回傳 task success rate、平均建立／重用 token、平均 task latency 與平均
capability execution time，避免只看 token 降低而忽略成功率或延遲代價。

## 儲存與重啟

SQLite 新增非破壞性的 `llm_interactions` 與 `task_cost_metrics` 資料表及查詢索引。
資料使用與 Capability／Report／Approval／Audit 相同的 database path，因此 app 重啟、
另一 app 實例或另一程序可讀取相同研究紀錄。升級不修改既有資料表內容。

## 目前驗證

`tests/test_research_metrics.py` 的三項測試驗證：

- Mock usage 保持 unavailable，沒有產生虛構 token 或 break-even；
- interaction、task metric 與 `task_id` 對應正確；
- 研究資料可由使用相同 SQLite 的新 app 實例讀回；
- provider 回報完整 usage 時，建立成本、零 LLM 的重用成本、phase breakdown、
  average tokens、saving rate、provider cost 與 break-even reuse count 計算正確。
- generation 失敗時仍保存失敗 interaction、error、建立嘗試與未知 token，不計為成功。

最近完整套件結果為 **28 passed, 1 warning in 7.12s**；警告仍是既有
Starlette／AnyIO `BlockingPortal` alias 棄用。

## 限制與後續

- 尚未接上 LiteLLM、NVIDIA NIM 或 OpenRouter，沒有真實 token/cost 資料。
- 尚未實作 static-agent baseline runner；目前 baseline 必須由研究者明確提供。
- 尚未分類 Exact／Near-Similar／Generalized reuse，也沒有 adaptation/revision cost。
- summary 目前在 service 層讀取符合條件的紀錄後計算；大量資料時需下推 SQL／分析庫。
- metric API 尚無認證與 tenant scope，已保留 `TODO(security)`，不得直接公開部署。
- task metric 與 LLM interaction 尚未包在同一個端到端交易；程序強制終止可能留下
  interaction 而沒有最終 task metric。這類不完整觀測應保留供故障分析，不可偽裝成功。

Phase 1.5 應讓真實 provider adapter 回傳原生 usage 與可靠價格；Phase 3 再執行完整
baseline／模型組合／相似度／長序列研究，檢驗節省是否以成功率或維護成本為代價。
