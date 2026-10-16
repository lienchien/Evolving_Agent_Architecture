# CEAA Research Watch

本檔案收錄與 Capability-Evolving Agent Architecture（CEAA）直接相關、值得追蹤的論文及技術文章。此處為研究筆記與待驗證假設，不代表已納入正式系統設計。

## 2026-10-15 — Langfuse vs. LangSmith：AI Observability 如何選擇與整合

- **原始文章**：[Langfuse vs. LangSmith：AI Observability 如何選擇與整合](https://ithelp.ithome.com.tw/articles/10421215)
- **來源**：iT 邦幫忙；由當日 Gmail 科技摘要收錄。
- **研究優先級**：High（直接支援 CEAA v1.9 的執行追蹤與 Skill Complexity Compression 實驗）。
- **查核狀態**：初步研究筆記；目前依據郵件提供的文章標題與摘要，尚未逐篇核實全文與作者實測結果，以下比較項目均屬 CEAA 擬評估方向，不視為原文結論。

### 核心研究價值

AI Agent Observability 的價值不僅是記錄 LLM 呼叫，還在於串接任務、決策、Skill 版本、工具呼叫、執行結果與成本，形成可分析的完整 execution trace。Langfuse 與 LangSmith 可列為 CEAA 可觀測性工具選型的候選方案；需以官方文件與實測確認各項功能、部署條件與成本。

### 與 CEAA 架構的關聯

- **Execution Telemetry**：以一致的 trace / span 追蹤 Manager/Router、Skill、Tool、Model 與 Validator 的執行路徑。
- **Skill Registry / Versioning**：每次執行綁定 Skill ID、版本、能力等級與執行成本等級，避免跨版本統計混淆。
- **Decision Evolution**：保存路由決策依據、候選方案、升級與 fallback 次數，分析 cost-aware routing 是否有效。
- **Performance Evolution**：追蹤 Skill 優化前後的成功率、延遲、token／運算資源、重試次數與成本。
- **Skill Complexity Compression**：驗證高複雜度 Skill 在特定任務域經過迭代後，是否能降低成本且維持能力與安全門檻。

### 建議資料模型與衡量指標

建議最小 trace 欄位：`task_id`、`trace_id`、`skill_id`、`skill_version`、`capability_level`、`execution_cost_tier`、`router_policy_version`、`model_id`、`tool_calls`、`token_usage`、`latency_ms`、`retry_count`、`resource_usage`、`validation_result`、`task_success`、`estimated_cost`。記錄敏感資料時應去識別化、設定權限及保留期限。

主要 KPI：**Cost per Successful Task**、Success Rate、P50/P95 Latency、Retry Rate、Capability Retention Rate、Skill Compression Ratio；另計入可觀測性與優化自身的額外成本。

### 建議實驗與消融

1. **工具選型 PoC**：在相同 Agent 工作負載下比較 Langfuse、LangSmith 與輕量自建 OpenTelemetry/DB 方案，評估 trace 完整性、整合工時、資料可攜性、部署與維運成本。
2. **Routing 實驗**：比較固定模型／固定 Skill、Difficulty-aware Routing、Experience-aware Routing；以相同成功判準測量成本、品質與延遲。
3. **Skill Compression 縱向實驗**：在固定任務集上追蹤 L3 Skill 的多個優化版本，檢查成本下降是否維持能力與安全驗證結果。
4. **消融實驗**：移除 version-aware tracing、failure taxonomy、tool-level metrics、resource-level metrics，觀察對優化決策與實驗可重現性的影響。
5. **Telemetry Overhead**：量測開啟／關閉完整追蹤對延遲、儲存與執行成本的影響。

### 限制與待驗證問題

- **HTTP 成功不等於任務成功**：必須另外建立 schema、語意正確性與目標達成驗證。
- 各工具的功能、費用、資料留存及自架能力可能變動，需閱讀官方文件並實測，不能由文章標題推定。
- 避免將 prompt、API token、個資與企業機密直接寫入 trace。
- 若僅依成功執行的樣本優化，可能產生選擇偏誤；失敗與中止的 trace 同樣重要。

### 建議下一步

在 CEAA 的 Phase 3 實驗設計中加入 **Observability Instrumentation PoC**，先制定工具無關的 Trace Schema 與 Evaluation Contract，再決定採用哪個觀測平台。**本筆記不修改正式 v1.9 架構文件。**


---

## 2026-10-16 — Google ADK：Gemini 4 Argon 自主優化大型 Agent Framework

- **原文**：[Optimizing a 200,000-line Python codebase overnight with Gemini 4 Argon](https://developers.googleblog.com/en/optimizing-a-200000-line-python-codebase-overnight-with-gemini-4-argon/)
- **作者**：George Weale、Bo Yang、Andrew Biernat（Google Cloud）；**原文發表**：2026-10-13；**收錄**：2026-10-16。
- **來源等級**：Google 官方工程案例，包含內部測試與公開程式庫修改；並非獨立第三方重現。
- **研究優先級**：Critical — 直接對應 CEAA Performance Evolution / Skill Optimization / Architecture-Stable Continuous Evolution。

### 核心貢獻與已報告的結果

Google 讓 Gemini 4 Argon 在約 205,000 行、近 800 個來源檔案的 Python ADK 程式庫執行效能改善。第一輪未提供自訂 repository 指南，約執行兩小時；第二輪提供 `.agents/skills` 維護規範與跨 context compaction 保持目標的 `/goal` 模式，約自主執行 11 小時。第二輪執行 16,892 項開源單元測試並產出供人工審查的 PR，沒有自行合併。

- 共提出六項優化，**兩項**通過維護者審查並正式採用：先過濾 session history 再複製，以及延遲載入重量級 Python 模組。
- 官方報告：特定長 session 的 **in-memory session preparation framework overhead 約降低 40%**；`import google.adk` 冷啟動匯入約快 **21%**。
- 獨立 holdout benchmark 中，158-turn 工作流程的整體執行時間由 **65.6 秒降至 56.1 秒**；但**新 process 到第一個 model request 的時間幾乎不變**（3.07 秒至 3.09 秒）。
- 四項未採用的提案分別涉及 stale cache 風險、依賴 OpenTelemetry 私有屬性、無實際端到端改善，以及僅對合成測試有益的複雜索引。
- 改善主要適用於 `InMemorySessionService`；不能推廣至外部資料庫、Redis、Firestore 等不同 session backend。

### 與 CEAA 的關聯及可借鑑設計

1. **Skill Optimization Agent**：自主 profiler/benchmark → 提出候選優化 → regression/holdout evaluation → independent approval → versioned rollout。候選方案不得直接部署。
2. **Skill Tree × RAG**：採用小型 `SKILL.md` 索引與按需載入 `references/`，避免每次將所有規範塞入 context；比較與 CEAA Skill Registry 的整合。
3. **Experience Memory**：除了採用成功的優化，也儲存被拒絕方案的 failure taxonomy（stale state、private API、synthetic-only gain、compatibility regression），減少重複探索。
4. **Manager / Router**：以任務複雜度決定是否啟動長時程 Optimization Agent；對低頻任務需計入探索與審核的攤提成本。
5. **Governance**：限制 agent 僅能建立 candidate branch/PR；CI、holdout、權限檢查與人工核准維持獨立。

### 建議 Baseline、實驗與消融

- **Baseline A**：人工指定 bottleneck + 固定工具與模型。
- **Baseline B**：同一模型自主優化，但無 Skill/維護規範與 Experience Memory。
- **Baseline C**：加入 repository Skill 指南與 goal persistence，但不啟用 CEAA 自適應決策。
- **CEAA**：Skill 指南 + Experience Memory + Difficulty-aware Routing + Optimization Agent + Secure Evolution Gate。
- **Ablation**：分別移除 Skill 指南、Experience Memory、獨立 holdout benchmark、治理審核與成本感知路由。
- **Metrics**：task success、實際 end-to-end latency、framework overhead、regression rate、proposal acceptance rate、review effort、optimization total cost、cost per successful task、break-even reuse count、capability retention；不同 backend 分層報告。

### 證據限制與後續工作

這是 Google 在 ADK 的特定工作負載實測，**不代表 CEAA 已驗證 Skill Complexity Compression**。框架 overhead 的 40% 改善也不等於整個 Agent 任務成本降低 40%。建議先重現具代表性的 session 與 tool-heavy benchmark，採固定 holdout 工作負載與統計重複測試，再將「高能力 Skill 是否可維持能力並降低執行成本」列為獨立假設檢驗。

## 2026-10-16 — Gemini 4 Argon：長時程 Agent 模型能力與 CEAA 路由比較

- **官方文件**：[What's new in Gemini 4 Argon](https://ai.google.dev/gemini-api/docs/latest-model?hl=en)
- **相關官方研究案例**：[Google ADK 自主優化](https://developers.googleblog.com/en/optimizing-a-200000-line-python-codebase-overnight-with-gemini-4-argon/)
- **收錄日期**：2026-10-16；**研究優先級**：High。
- **查核狀態**：官方產品文件已核對；價格與功能可能隨時調整。

### 核心能力與研究意義

官方文件列出模型 ID `gemini-4-argon`、統一的約 1M-token context / thinking / output 預算、長輸出及可調 thinking levels（low / medium / high）。這提供長時程、複雜多步驟工程任務的候選高能力模型，但模型能力本身不等同於可控的 Agent 執行框架。

### 與 CEAA 的關聯

- **Difficulty-aware Routing**：Argon 可列為高難度任務候選模型；與低成本模型、cascade 與 critique 工作流程比較。
- **Skill Complexity Compression**：將高成本模型建立的 Skill 與後續低成本模型重用 Skill 的效果分開評估，區分 **Capability Level** 與 **Execution Cost Tier**。
- **Cost Governance**：完整計入 thinking/output tokens、工具呼叫、長時間執行、失敗重試、驗證及審核成本。
- **Security**：長時間自主執行仍應維持 sandbox、權限邊界、審核與可回滾機制。

### 建議實驗

比較 (1) 直接高能力模型、(2) 低成本模型、(3) cascade/escalation、(4) CEAA experience-aware Skill routing。固定任務集與成功標準，記錄 Success Rate、Cost per Successful Task、P95 latency、retry/escalation rate 與 Capability Retention Rate。另比較同一模型不同 thinking levels 的品質／成本曲線。

### 限制

官方公布的模型價格為限時促銷，不能用單一固定價格推估長期成本；不同任務域也不保證長 context 或長執行必然帶來較高成功率。實驗需記錄測試日期、模型版本、計費與評估環境。**本條目僅供研究規劃，不修改 CEAA 正式 v1.9 設計。**
