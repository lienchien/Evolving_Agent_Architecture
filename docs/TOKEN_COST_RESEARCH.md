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

## Future Experiment F — Agent Scaling Efficiency / Aggregate Token Demand（延期）

**狀態：僅規劃，尚未實作或驗證。** 對應 [Future Vision](AGENT_PLATFORM_FUTURE_VISION.md) 的 Experiment F。此研究不得新增 Phase 1／1.5 退出門檻，也不要求現有單機執行大規模並行 Agent 壓力測試。

- **L1 單任務（Phase 3 既有研究）**：固定相同任務、品質與成功定義，比較 static-agent 和 CEAA 的 provider-reported token、Cost per Successful Task、延遲與重試。
- **L2 總量情境（後期離線研究）**：用匿名化歷史 trace replay 與合成工作負載，改變使用者數、每日任務數、Agent 活躍度、任務難度分布及路徑重用率，推演總 Tokens／日與成本；標記為**模擬值**，不可冒充真實使用量。
- **L3 真實規模（硬體／雲端資源充足後）**：擴充負載測試至實際並行請求、多 Agent 與多租戶，衡量 throughput、p95 latency、排隊深度、資源利用率、成功率、可靠性、Tokens／日與總成本。

簡化關係式：`Aggregate Tokens = Σ(所有實際 LLM interactions 的已量測 Tokens；含失敗、重試與 fallback)`；假設相同任務組成、品質與失敗／重試率，單任務節省率為 `s`，總工作量成長倍率為 `g`，則總 Token 倍率近似 `g × (1 − s)`。這是條件式情境模型，無法單憑效率提升推論真實市場採用率或 GPU 採購量。

資料完整性沿用本文件現有規範：不得推估缺失的 provider usage；模型差異、cached/input/output/reasoning tokens、任務成功率及成本須分層比較。L2 合成用量應保存在獨立 scenario/replay dataset，與實際 telemetry 分離。

**執行門檻：** Phase 3 真實 baseline／完整 usage 與驗證過的成功品質先成立；L3 另須可重現的負載架構、資源監測、預算與足夠硬體或雲端配額。現階段不購置額外 GPU，也不啟動大規模實驗。


### Experiment F.1 — Edge AI 與雲端升級情境（延期）

納入 24 小時設備監控、自主異常診斷與自動修復流程。區分「邊緣本地推論」（CPU／GPU／NPU）與「升級到雲端的推論」，避免將所有 Edge 事件都視為資料中心 LLM Token 消耗。

情境變數：裝置數量、每台每日事件量、本地解決率、雲端升級率、升級任務的真實 provider token usage、邊緣運算量／能耗（有實測才列值）、重試與驗證成本、端到端成功率。比較 Edge offloading 對雲端需求的替代效應與設備普及增加整體任務量的誘發效應。

L2 僅使用清楚標示的數值情境與 replay 模擬；L3 真實多設備並行、資源與能耗測試，待設備與預算充足後進行。不能將 Token 數量直接換算為 GPU 需求，也不能在沒有量測前推論長期為指數成長。此項不影響 Phase 1／1.5 退出條件。
