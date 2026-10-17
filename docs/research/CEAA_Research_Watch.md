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


---

## 2026-10-17 — NeMo Gym × Siemens EDA：以可驗證產物驅動 Skill 與 MCP Tool 最佳化

- **原文**：[Optimizing Agent Reliability and Tool Calling Efficiency for Chip Design Using NVIDIA NeMo Gym](https://developer.nvidia.com/blog/optimizing-agent-reliability-and-tool-calling-efficiency-for-chip-design-using-nvidia-nemo-gym/)
- **作者**：Joshua Mabry、Chris Wing、Niranjan Sitapure、Kenton DeLathouwer、Ming Ming Zhang。
- **發表日期**：2026-10-14；**郵件發現／收錄日期**：2026-10-17（NVIDIA Developer Newsletter）。
- **研究優先級**：**Critical**（CEAA v1.9 Performance Evolution、Skill Optimization、Tool Interface Optimization 的直接實驗對照）。
- **證據層級**：NVIDIA／Siemens 官方工程案例，已核對全文；非獨立重現的通用結果。

### 核心貢獻與原文證據

Siemens Fuse EDA AI Agent 以 NVIDIA NeMo Gym 對晶片 standard-cell characterization 流程建立受控評估環境，產出可由 domain-specific verifier 檢查的 Liberty (.lib) 檔案。以固定 Claude Opus 4.8 與 Claude Code harness，約 25 次 rollout（每次約 1.5–2 小時）迭代調整 Skill 及 MCP 工具描述；每次實驗限縮為 2 個 cells × 36 PVT corners，原始資料集為 229 cells × 36 corners。

原文報告的**開發 benchmark**平均 composite verification score 約 **55% → 95%**；agent turns **155 → 53（約 -66%）**；平均 output tokens **81K → 29K（約 -64%）**。這是同一任務環境中的 harness／Skill 優化結果，**不是更換基礎模型、不是整體金額成本下降 64%、也不是 CEAA 實驗結果**。

驗證器的五個面向：Coverage、Validity、Relative Validation、Accuracy、Integrity。其 reward 使用多個必要條件的乘積 gate：若覆蓋、有效性、相對驗證或完整性任一失敗，總分歸零；通過後才依 tolerance 內數值比例計分。能抓出「工具呼叫成功但最終產物錯誤」、重用既有數值或輸出不完整等問題。

### 與 CEAA 的關聯／可借鑑設計

1. **Performance Evolution Loop**：版本化任務與 verifier → 收集完整 execution trajectory → failure taxonomy → 修訂 Skill/MCP JSON schema/工具敘述 → 受控重測。
2. **Skill Complexity Compression**：將能力保留率與效率分開衡量；此案例可作為「固定高能力模型、優化 Skill/harness」的 baseline，而非已證明 L3 降至 L1 成本。
3. **Manager/Router**：刪除重複、語意重疊的工具路徑，並強化明確 JSON schema；測試減少 action space 是否改善工具選擇。
4. **Governance & Evaluation**：最終產物 verifier 獨立於執行 Agent，必要時搭配人工審核與 rollback；避免優化者修改評分器來獲得虛假進步。
5. **Experience Memory**：記錄失敗軌跡、錯誤根因、修訂版本與後續回歸結果。

### 建議 Baseline / Experiment / Ablation

- **B0**：固定模型 + 原始 Skill/MCP tools。
- **B1**：固定模型 + 人工改善 Skill 描述與工具 JSON schema（重現 Siemens 路徑）。
- **B2**：固定模型 + CEAA Experience-aware Skill Optimization Agent 產生候選改善 + 獨立驗證。
- **B3**：B2 + difficulty-aware routing / cost-aware tool selection。
- **Ablation**：移除 domain verifier、failure taxonomy、tool-schema refinement、Skill versioning、holdout gate。
- **KPI**：final-artifact correctness、hard-gate pass rate、Success Rate、Cost per Successful Task、turns、output tokens、P95 latency、regression rate、Skill Compression Ratio、Capability Retention Rate、break-even reuse count。
- **研究控制**：固定模型、溫度、任務分割、工具版本；使用開發／保留測試集並多次重複；記錄優化探索與審核成本。

### 限制

成果侷限於 EDA 的可驗證工程任務、特定 simulator／PDK／harness。不能將 composite score 直接當成通用任務成功率；亦不可把 output token 減少直接視為總費用同比下降。非可驗證的管理／策略任務需要額外 human rubric 或偏好評估。

## 2026-10-17 — KDD Cup Data Agents：小模型 × 受限 Harness × Trace 驅動改善

- **原文**：[Building Reliable Data Analytics Agents: Lessons from the KDD Cup](https://developer.nvidia.com/blog/building-reliable-data-analytics-agents-lessons-from-the-kdd-cup/)
- **作者**：Eduardo Rocha de Andrade、Jiwei Liu、Maximilian Jeblick、Raja Biswas、Isabel Hulseman。
- **發表日期**：2026-10-08；**郵件發現／收錄日期**：2026-10-17（NVIDIA Developer Newsletter）。
- **研究優先級**：**Critical**（CEAA 小型本地模型、Agent Harness、Tool Governance、Decision Evolution 的可重現比較）。
- **證據層級**：NVIDIA KGMON 團隊 KDD Cup 2026 第二名工程經驗，官方文章已核對；非 CEAA 實測。

### 核心貢獻與原文證據

競賽使用**固定小模型**，團隊以 Harness 限縮動作空間而非升級模型：將 CSV/JSON 統一轉為 SQLite 查詢面；先行 schema scouting；提供 `schema()`、`sql(query)`、`write_answer(df)`、`prose_helper()` 四類窄介面；使用 persistent Python state、單一路徑輸出、工具格式修復、文件限量檢索與專用低推理成本 extraction call。保留每次 prompt、tool call、SQL、錯誤與答案 trace，供 inspector agent 歸類失敗。

團隊指出：重試／多次抽樣可以提升穩定性但會增加成本；自動改善可能導致 benchmark overfitting、矛盾 prompt 或 brittle postprocessing；因此必須有 holdout 與人工核准。

### 與 CEAA 的關聯／可借鑑設計

1. **Skill × Tool Contract**：以單一受治理的資料存取介面替代多個重疊工具；Skill 可包含 schema 與使用限制。
2. **Decision Evolution**：先評估簡化工具空間能否降低路由錯誤，再加入更複雜的 Manager Agent，避免把模型能力不足誤判成需要更多 Agent。
3. **Cost-aware Routing**：將低成本 `prose_helper` 抽取任務與主推理任務拆開，必要時才重試或 ensembling。
4. **Experience Memory**：Inspector Agent 從 trace 產生可重用的錯誤分類與改善候選，但不得直接修改正式 harness。
5. **Governance**：限制全文讀取、單一答案輸出、holdout、prompt audit 與人工升級門檻。

### 建議 Baseline / Experiment / Ablation

- **B0**：單一小型本地 LLM + 通用 Python/SQL/文件工具。
- **B1**：同模型 + 統一 SQL surface + schema preflight + 窄工具介面。
- **B2**：B1 + persistent state + selective prose helper。
- **CEAA**：B2 + Inspector Agent + Experience Memory + cost-aware routing + reviewed Skill evolution。
- **Ablation**：去除 schema scouting、統一 SQL、persistent state、trace-based failure analysis、selective retry、approval gate。
- **KPI**：value-level answer accuracy、join/row-grain error rate、invalid tool calls、tokens、latency、Cost per Successful Task、retry count、holdout generalization gap。

### 限制

KDD 競賽固定模型、無網路、單一評分規則，不能推定相同方法適用所有企業 Agent。若資料含敏感資訊，應限制 SQLite／trace 留存與讀取權限；重試與 inspector 自身成本必須計入。本文提出的 CEAA 實驗均為待驗證設計。

## 2026-10-17 — NVIDIA DOCA Agent Skills：領域知識契約、能力檢查與安全前置條件

- **原文**：[Build Applications on NVIDIA BlueField Faster with NVIDIA DOCA Agent Skills](https://developer.nvidia.com/blog/build-applications-on-nvidia-bluefield-faster-with-nvidia-doca-agent-skills/)
- **作者**：Claudia Martinez、Matan Raz、Tamir Tevet。
- **發表日期**：2026-10-01；**郵件發現／收錄日期**：2026-10-17（NVIDIA Developer Newsletter）。
- **研究優先級**：**High**（CEAA Skill Registry、Skill Quality Evaluation、Secure Evolution Gate）。
- **證據層級**：NVIDIA 官方產品案例與內部 65 prompts 測試，已核對原文；非獨立 benchmark。

### 核心貢獻與原文證據

DOCA Agent Skills 以 `SKILL.md` 提供已核實 API signatures、硬體能力要求、建置約束、故障模式與 preflight／rollback 規範。官方 65-prompt checklist 評估報告：無 Skill 滿足 **19%** 檢查項目，有 Skill **100%**；在 RDMA side-by-side demo 中，with-skill agent 使用 **189 vs 695** 行手寫程式碼（-73%），**20 vs 37** 個硬體命令（-46%）。這是官方特定評估，**不能直接等同於整體成功率或所有工作負載改善幅度**。

### 與 CEAA 的關聯／可借鑑設計

- **Skill Contract**：Capability Prerequisites、Supported Versions、Tool Schema、Preflight Checks、Known Failure Modes、Rollback Plan 與 Approval Requirement 應成為 Skill Metadata。
- **Skill Tiering**：能力等級不等於執行成本；在低風險 API 查詢與高風險 firmware 變更間，採不同 Skill／審核層級。
- **Governance**：具硬體副作用的工具必須執行能力檢查、維護窗口與 rollback；Agent 不得自行繞過安全閘門。
- **Performance Evolution**：將領域知識契約與一般文件摘要分開評估，檢查是否真的降低 hallucinated API、錯誤路由與重試成本。

### 建議 Baseline / Experiment / Ablation

- **B0**：通用 Agent + 普通文件檢索。
- **B1**：B0 + 結構化 Skill（API schema／版本／preflight）。
- **CEAA**：B1 + risk-aware routing + Skill versioning + Secure Evolution Gate。
- **Ablation**：移除 API signatures、capability checks、rollback metadata、approval gate。
- **KPI**：API hallucination rate、preflight compliance、tool success、artifact correctness、retries、Cost per Successful Task、policy violations。

### 限制

DOCA 範例受 BlueField 硬體與專屬 API 場景限制；65-prompt checklist 與單次示範不足以證明廣泛可遷移性。需要跨領域、跨模型及保留測試集重現，並將維護 Skill 的成本納入比較。**本筆記不修改 CEAA 正式 v1.9 架構。**
