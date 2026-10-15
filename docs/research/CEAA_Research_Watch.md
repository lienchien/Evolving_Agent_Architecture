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
