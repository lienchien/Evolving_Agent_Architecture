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


---

## 2026-10-20 — AMD Ross：MCP × RAG × Expert-authored Skills 的 Agent 工程架構

- **文章／產品**：AMD Brings the Power of Agentic AI to Embedded Design and Development Cycle；AMD Ross Agentic AI Assistant。
- **官方來源**：https://newsroom.amd.com/news/amd-ross-agentic-ai-embedded-design-development/
- **官方產品文件**：https://www.amd.com/zh-tw/products/software/ross-agentic-ai.html
- **官方開發文件**：https://docs.amd.com/r/en-US/ug1400-vitis-embedded/Enabling-the-MCP-and-Skills-in-Agent-Mode
- **官方參考實作與範例**：https://github.com/xilinx/ross-ai-assistant
- **發表日期**：2026-09-30（AMD Newsroom）；**研究收錄日期**：2026-10-20。
- **作者／發布單位**：AMD Newsroom / Advanced Micro Devices（官方產品公告，未以個人論文作者署名）。
- **研究優先級**：**High**（Skill Architecture / Skill Registry / Capability Evolution / Skill Optimization / Edge AI Tool Integration）。
- **證據層級**：AMD 官方產品與開發文件；不是 CEAA 或第三方獨立量化比較。

### 核心貢獻（可核實的官方資訊）

AMD Ross 將四個元件組合為嵌入式開發 Agent 工具鏈：**MCP servers**（連接 Vivado、Vitis 等工具）、**AMD Knowledge Base**（文件 RAG，部分環境可本機使用）、**expert-authored Agent Skills**（可分享的結構化工程工作流程）、**ready-to-run design examples**（可執行參考設計）。AMD 官方說明 Skill 以可重用的 Markdown 程序捕捉領域專家實務，並支援從設計、除錯到優化的工具操作。Vitis 文件要求執行 shell / 修改檔案前審查權限與預計操作。

### 與 CEAA 的直接關聯（研究推論，非 AMD 官方主張）

1. **Static Expert Skill vs Evolving Skill**：Ross 的人工撰寫 Skill 適合作為 CEAA 自主生成、修訂、驗證與重用 Skill 的外部設計基準。
2. **Skill Tree × RAG**：比較文件檢索與可執行程序記憶的分工；檢查按需載入 Skill 是否減少 context 與錯誤工具選擇。
3. **Manager / Tool Selection**：比較固定工作流程與 Experience-aware Routing、Difficulty-aware Skill Tiering；不要將模型、工具與領域知識效應混為一談。
4. **Governance**：Skill 前置條件、工具版本、使用者授權與操作審核應與實際工具執行隔離。
5. **Skill Complexity Compression**：假設高能力、昂貴的探索工作流程可經優化後由較低成本執行策略重用；尚無 Ross 對此的直接證據。

### 建議 Baseline / Experiment / Ablation

- **B0**：同一模型 + 一般文件 RAG + 原始工具呼叫（無 Skill）。
- **B1**：B0 + 專家預先編寫的靜態 Skill（Ross-style；使用公開範例或在相同模擬任務自行實作）。
- **B2**：B1 + 明確的 Tool/MCP Schema、前置檢查與版本化 Skill。
- **CEAA**：B2 + 自主候選 Skill Generation / Optimization + Experience-aware Routing + independent validation + governance。
- **Ablation**：移除 Skill、RAG、preflight、Experience Memory、cost-aware routing、Skill versioning 或 independent validator。
- **指標**：Task Success、final-artifact correctness、invalid tool call rate、token、latency、Cost per Successful Task、Skill creation/maintenance cost、Capability Retention、Regression Rate、break-even reuse count。
- **控制條件**：相同模型、任務集、工具版本與執行預算；先以可重現 mock FPGA/CLI 任務避免專屬硬體干擾，再評估真實嵌入式工作流程。

### 證據與限制

AMD 公告是產品能力描述，**不等於已獨立證實 Skill 自主演化、Token 節省或跨領域泛化**。Ross 專注 AMD 嵌入式工具，CEAA 的通用 Skill 架構需跨領域驗證；若使用專屬工具，需確認硬體、授權與環境限制。所有效能改善應以 CEAA 自己的 holdout benchmark 證明。

---

## 2026-10-20 — OpenClaw Gateway：Role / Scope / Device Identity 與 Tool Permission 治理

- **文章／主題**：OpenClaw Gateway Protocol、Handshake and Roles、Operator Scopes、Node Pairing。
- **官方原文**：https://docs.openclaw.ai/gateway/protocol
- **官方 Handshake**：https://docs.openclaw.ai/gateway/protocol/handshake
- **官方 Operator Scopes**：https://docs.openclaw.ai/gateway/operator-scopes
- **官方 Node Pairing**：https://docs.openclaw.ai/gateway/pairing
- **作者／發布單位**：OpenClaw 專案維護團隊（官方持續更新文件，未列單一作者）。
- **發表日期**：官方動態文件未提供可核實的單一首次發布日期；**查核／研究收錄日期**：2026-10-20。
- **研究優先級**：**High**（Agent Governance / Tool Permission / Manager & Sub-Agent Authority / Secure Recovery）。
- **證據層級**：官方協定與操作文件，屬設計與行為規格；尚非 CEAA 安全有效性的實驗證據。

### 核心貢獻（官方規格）

Gateway 使用 WebSocket 控制平面，客戶端連線時宣告角色、scopes、capabilities 與 device identity；握手包含 challenge 與裝置驗證。Gateway 對 operator / node 權限、RPC method scopes、節點允許的 commands / permissions、配對審批進行伺服器端檢查；具更高風險的操作需要更高權限與審核。官方明確指出 operator scopes **不是不可信多租戶間的強隔離**；若要強隔離，需分開 Gateway / OS user / host。

### 與 CEAA 的直接關聯（研究推論）

1. **Agent Identity ≠ User Identity ≠ Tool Authority**：Manager、Sub-Agent、Skill 與 Tool 的操作權限必須在每次執行檢查，不可僅信任 Agent 的工具宣告。
2. **Hierarchical Delegation**：維持 `P_child ⊆ P_parent ⊆ P_root` 的權限不擴張原則；動態 Sub-Agent、Tool Discovery 與 Skill Registry 更新不得繞過審批。
3. **Failure-driven Self-Recovery**：診斷 Agent 可讀取最小必要的 sanitised trace；Repair Agent 不可因修復任務而自動取得高權限。未知或拒絕授權的恢復候選必須 fail closed。
4. **Governance Observability**：保存 identity、scope、approval、tool invocation、failure category 與 recovery outcome 的可追溯事件。
5. **Protocol Boundary**：研究集中控制平面是否降低權限分散造成的治理缺口；但不可假定單一 Gateway 就能解決租戶隔離。

### 建議 Baseline / Experiment / Ablation

- **B0**：工具權限僅以 Agent prompt / tool description 約束（不應在真實環境部署）。
- **B1**：固定 per-tool allowlist + deterministic authorization。
- **B2**：B1 + role/scope/device identity + approval-time permission check（OpenClaw-style）。
- **CEAA**：B2 + hierarchical delegation + risk-aware routing + Secure Evolution Gate + Recovery-specific permissions。
- **Security fault injection**：未授權工具呼叫、權限升級、跨使用者工作階段、被竄改 tool descriptor、過期憑證、配對擴權、修復 Agent 越權、審核 timeout 與 ambiguous approval。
- **Ablation**：移除 device binding、scope check、approval-time check、parent-child permission invariant、audit trace、recovery gate。
- **指標**：Unauthorized Action Rate、Privilege Escalation Detection、Policy Violation Recall/False Positive、Human Escalation、Task Success、P95 Latency、Token/Cost Overhead、Cost per Successful Task、Recovery Regression Rate。
- **控制條件**：僅在隔離沙盒與授權測試帳戶執行；固定角色、工具、任務與攻擊案例，保留獨立 holdout。

### 證據與限制

官方文件提供可核對的權限設計，**不代表 OpenClaw 或 CEAA 已在攻擊測試中達成特定安全指標**。協定會演進，需在重現時鎖定 commit / version。官方明確限制 operator scopes 不是強多租戶隔離，CEAA 仍須實作獨立的 tenant/owner/scope 資料治理與 Sandbox。上述 Baseline 和 CEAA 對照均為待實驗驗證的研究規劃；**本次僅新增研究筆記，不修改正式 v1.9 架構或程式碼**。


---

## 2026-10-21 — Context Rot：長上下文可靠性與 CEAA 按需記憶路由

- **原文**：[Context Rot: How Increasing Input Tokens Impacts LLM Performance](https://www.trychroma.com/research/context-rot)
- **作者**：Kelly Hong、Anton Troynikov、Jeff Huber（Chroma）。
- **原文發表**：2025-07-14；**研究收錄**：2026-10-21。
- **可重現程式碼**：https://github.com/chroma-core/context-rot
- **研究優先級**：**High**（Context Engineering、Package-local Experience Memory、Experience-aware Routing、Skill Complexity Compression）。
- **證據層級**：Chroma 原始技術報告與公開實驗程式碼；非 CEAA 實驗結果。

### 核心貢獻（原文研究事實與作者主張）

Chroma 評估 18 個 LLM，涵蓋 GPT-4.1、Claude 4、Gemini 2.5、Qwen3 等，使用擴展 Needle-in-a-Haystack（語意匹配與干擾內容）、LongMemEval 與 Repeated Words 等控制實驗。作者觀察到：隨輸入 token 增加，模型表現可能下降且非均勻變化；即使相關資訊仍在上下文內，也不保證可靠使用。研究強調上下文的選取、呈現方式與干擾資訊的重要性，不能只以 context-window 最大長度或簡單詞彙匹配 NIAH 成績推定實務可靠性。這是受控任務上的觀察，並非證明所有模型在所有任務上皆單調下降。

### 與 CEAA 的關聯（以下為待驗證研究推論，非原文結論）

1. **Skill Tree × RAG / Context Budget**：Manager 只讀 Skill metadata；選定 Package 後按需讀取 Skill contract、必要參考資料及歷史經驗，避免全量注入。
2. **Package-local Experience Memory**：以任務類型、Skill 版本、成功判準及 failure taxonomy 檢索局部經驗；同時設計跨 Package 搜尋與 fallback，防止局部記憶遺漏關鍵證據。
3. **Experience-aware Routing**：比較檢索到的 execution path 是否有助於路由正確率與端到端任務成功，而非只計算節省的 token。
4. **Skill Complexity Compression**：將 context 壓縮和能力維持分開驗證；較短 prompt 不必然有較高準確率，也可能因資訊遺失而降低成功率。
5. **Governance / Observability**：記錄 context selection policy、retrieved memory IDs、token budget、decision trace、驗證結果、重試與總成本；避免在 trace 中儲存敏感原文與 token。

### 建議 Baseline / Experiment / Ablation

- **B0 Full Context**：相同模型、任務與工具下，注入全部相關 Skill 文件與歷史經驗（受模型 context limit 約束）。
- **B1 Top-K RAG**：全域語意檢索 Top-K；固定 token budget。
- **B2 Package-local Retrieval**：先選 Package，再在局部 Skill / Experience Memory 中檢索。
- **B3 Experience-aware Retrieval**：B2 + 成功／失敗路徑、版本與驗證結果排序；必要時 fallback 全域檢索。
- **B4 Execution Path Fast Path**：B3 + 只在任務匹配與風險門檻通過時重用已驗證路徑，否則重新規劃。
- **Ablation**：移除 Package 分流、Experience Memory、failure-aware ranking、global fallback、context budget、fast-path validator；另外在固定有效資訊下逐步增加無關與語意相近干擾內容。
- **KPI**：Task Success、evidence retrieval recall、route accuracy、hallucination / wrong-tool rate、context tokens、P50/P95 latency、retry rate、Cost per Successful Task、Capability Retention Rate、regression rate；將索引、檢索、路由、驗證及失敗重試成本計入總成本。
- **實驗控制**：固定模型版本、工具與任務集；控制 context token budget、資訊位置、干擾密度及檢索品質；採多次重複、分層難度與獨立 holdout。檢查縮短 context 是否只是刪掉困難證據，以及 Package routing error 是否抵銷收益。

### 證據與限制

原文是受控長上下文測試，**未直接評估 CEAA、Skill Package、Experience-aware Routing 或 Cost per Successful Task**。不同模型、任務、語意干擾與上下文位置的效應可能不同；按需檢索可能造成資訊遺失或額外延遲。CEAA 需透過獨立端到端任務與成本量測驗證，不能把 Context Rot 直接當成架構優越性的證據。

### 建議下一步

優先設計 **Context Budget × Memory Scope × Routing Policy** 的 factorial experiment，先驗證 B0–B2 的成功率／成本曲線，再加入 B3–B4 與安全回退。**僅為研究筆記，不修改正式 v1.9 架構文件或實作。**


### CEAA 獨立實驗章節：Direct LLM Tool Planning vs Experience-aware Hierarchical Decision

- **提出日期**：2026-10-21；**狀態**：研究設計／尚未執行；**優先級**：High。
- **研究問題**：相同使用者問題、模型與工具條件下，讓單一 LLM 自主讀取工具清單、選擇工具並規劃流程，或先由 CEAA 決策層根據歷史執行經驗選擇 Package、執行計畫與工具，何者具較高的端到端回覆可靠性？效率與成本是否有取捨？
- **研究假設 H1**：Experience-aware Hierarchical Decision 對重複或相似任務可能提高 end-to-end Task Success / Answer Groundedness，並減少錯誤工具呼叫與不必要 Context。
- **研究假設 H2（Decision Stability）**：在同題多次重跑或同類任務反覆執行時，CEAA 的 validated path reuse 可能降低不必要的規劃與工具選擇變異；但穩定不代表正確，必須與任務成功率及適應新情境的能力共同驗證。
- **競爭假設 H0／風險**：額外決策層可能誤路由、受過時經驗影響、增加延遲；對新穎或跨領域任務可能不優於直接 LLM。兩者須實測，不預設 CEAA 勝出。

#### 比較組別（固定同一基礎 LLM、可用工具集合、工具版本、任務與權限）

| Group | 設計 | 用途 |
| --- | --- | --- |
| A Direct LLM Agent | 直接給使用者問題與全部可用工具 metadata，由 LLM 自主選工具、規劃、必要時重試；不提供歷史路由經驗 | 使用者提出的直接決策 baseline |
| B Direct LLM + Retrieved Experience | 同 A，但可檢索與 C 相同的歷史紀錄及品質標籤 | 拆出「有經驗」本身的效果，避免 C 因獨享資訊取得不公平優勢 |
| C Hierarchical Decision (no memory) | Manager/Package Decision 分流、選擇工具及執行計畫，但不使用歷史經驗 | 拆出分層與縮小工具／Context 空間的效果 |
| D CEAA Experience-aware Decision | C + 基於過往已驗證執行路線與失敗經驗排序，按需載入 Skill／工具、風險檢查及失敗 fallback | 主要實驗組 |

#### 執行流程

1. 建立任務基準：至少涵蓋單工具、複數工具、有相依順序、工具功能重疊、跨 Package、需要澄清、未知工具／未見任務、過時歷史經驗及工具失敗等類型；分層報告，不用單一總分掩蓋失敗。
2. 各組接受**相同使用者輸入**、後端資料快照與可用能力；區分「可發現工具集合」與「實際放入 prompt 的工具描述」，記錄兩者差異。使用相同驗證器、安全規則、最大呼叫次數與任務 deadline。
3. 設定相同模型版本與推理參數；每題多個隨機種子／重複執行，隨機化測試順序，排除外部 API 狀態波動；訓練／記憶庫與保留測試集切分，避免答案或路線洩漏。
4. 記錄路由候選、路由原因摘要、選定 execution plan、Skill/tool ID 與版本、檢索記憶來源、上下文 token、每次工具輸入與輸出（敏感資訊去識別化）、最終答案及獨立評估結果。
5. **雙層檢驗**：工具使用是否正確、任務產物／答案是否正確且有證據；HTTP 200／工具呼叫成功不得直接算 Task Success。
6. C/D 若無合適 Package、信心不足、記憶失效或驗證失敗，允許明確定義的 global search / replan fallback；fallback 次數及成本必須列入。
7. 先在可重播 mock tools 與固定資料集測試，再做受控真實工具任務；任何具副作用操作一律於沙盒或經授權環境，全部組別維持相同政策閘門。

#### 主要衡量指標與統計

- **Primary：End-to-end Task Success Rate**（獨立 ground truth／artifact verifier；必要時盲評）、**Answer Reliability**（正確、完整、引用證據一致；同時記錄不確定時適當拒答）。
- **Secondary：Tool Selection Accuracy**、Invalid/Wrong Tool Call Rate、Plan Validity、Tool Call Count、Retry/Fallback Rate、Missing Evidence Rate、Hallucination Rate、Context Tokens、P50/P95 End-to-end Latency。
- **Efficiency：Cost per Successful Task = 全部執行／規劃／檢索／驗證／重試成本總和 ÷ 成功任務數**；另列記憶建置、維護與 amortized cost，零成功組須標示未定義，不可宣稱為零。
- **分析方法**：依任務類型分層，對同題配對成功／失敗做差異比較與信賴區間（例如配對 bootstrap；二元成功可用 McNemar test），並報告延遲與成本分布。預先規定最小有意義改善門檻，不僅比較平均數。

#### 決策穩定性（Decision Stability / Execution Consistency）

此維度作為**正式評估項目**，用以量化相同條件下決策重現程度，而不是要求回答文字完全一致。每一個 benchmark task 在**固定使用者輸入、模型與版本、工具清單／版本、資料快照、權限與記憶快照**下，每組重跑建議至少 20–30 次（依試點變異與功效分析調整），並記錄 seed（若 API 支援）、prompt 與檢索版本、plan、tool call trace、結果正確性。另在相似但輸入條件改變的任務上測試**適應性**，不可把應有的策略改變計成失穩。

- **Plan Consistency**：將執行計畫標準化為目的／相依步驟／必要檢查的等效類別，測量同題重跑落在相同或功能等效計畫的比例。
- **Tool Selection Consistency**：比較工具選擇集合與必要呼叫順序的一致程度（考慮可交換步驟及功能等效工具）；同時回報正確工具選擇率。
- **Execution Path Entropy**：將完成的執行路線按功能等效規則分群，計算 `H(P) = -Σ p_i log₂(p_i)`；越低表示路線越集中，**不代表越正確**。可輔以最常見路線占比及不同類別數量。
- **Answer Consistency**：針對相同證據快照，比較可驗證事實、數值、結論及必要引用的一致率，避免以純文字相似度代理正確性。
- **Consistency × Correctness**：額外呈現「穩定且正確」、「穩定但錯誤」、「不穩定但正確」與「不穩定且錯誤」；各組分別報告 Task Success Rate、錯誤路徑重複率與信賴區間。
- **Adaptation / Stale-memory Robustness**：當工具 schema、任務約束或來源資料改變時，量測系統是否適當改選路線及觸發 fallback；避免經驗重用造成穩定的系統性錯誤。
- **Learning Curve**：對 cold-start、5／20／50 筆合格歷史案例（依可用資料調整）的 memory snapshot，追蹤各穩定性指標、成功率、平均工具呼叫量及 Cost per Successful Task，禁止把同題 holdout 答案回灌記憶庫。

**主張成立條件**：只有在正確率／可靠性不下降且決策變異減少、總成本可接受時，才視為有益的穩定性提升；優先報告「正確路徑的一致性」，而非盲目追求最低 entropy。

#### 關鍵消融與因果歸因

- D 移除 Experience Memory；D 移除 Package Decision；D 移除 validated path reuse；D 移除 failure-aware ranking；D 移除 fallback；比較歷史資訊過時／錯誤時的耐受性。
- **Context-matched comparison**：A/B/C/D 限定相近 token budget；另做 context-size sweep 與相同資訊量條件，分辨收益是來自少讀資訊、改變路由流程還是歷史經驗品質。
- **Cold-start vs Warm-start**：新任務無歷史、相似舊任務有歷史；另比較跨領域／跨 Package 轉移。記憶庫不得包含 holdout 標準答案或測試執行軌跡。
- **Stability ablation**：比較 D 關閉 validated path reuse、固定／擾動 experience retrieval 順序、注入過時經驗、移除決策層；觀察一致性提升是否只是凍結同一條錯誤路徑。
- **複雜度 × 工具數量**：測試工具由少到多、描述相似性升高時的失敗率，評估「縮小決策空間」是否確實改善工具挑選。

#### 成功判準與研究限制

若 D 相較 A 在 holdout 上有可重現、具實務意義的任務成功率／答案可靠性改善，且對 B、C 仍有增量貢獻，才能支持「歷史經驗導向的分層決策」具有獨立價值。若只在 D 對 A 勝出而不勝 B 或 C，應分別歸因為資訊取得或分層優勢；若複雜度較高任務表現反轉，採用按任務難度動態選擇路由策略的後續假設。Context Rot 只提供研究動機，**不是 CEAA 分層架構有效性的既有實驗證據**。

**治理邊界**：本章是研究方案，尚無數據或結論；不得自動修改正式 CEAA v1.9 架構文件、程式與部署設定。正式採納須由使用者審核。


---

## 2026-10-22 — NVIDIA OpenShell / Sentry：獨立於 Agent 的執行期治理與硬體隔離

- **官方公告**：[NVIDIA Launches OpenShell Reference Architecture for Safe AI Agents](https://nvidianews.nvidia.com/news/openshell-reference-architecture)
- **技術原文**：[Inside NVIDIA Sentry: Secure AI Agents at Runtime](https://developer.nvidia.com/blog/inside-nvidia-sentry-secure-ai-agents-at-runtime/)
- **技術文章作者**：Ofir Arkin、Ariel Kit、Itay Ozery（NVIDIA）；**原文日期**：2026-10-21；**研究收錄日期**：2026-10-22。
- **來源／證據層級**：NVIDIA 官方公告與設計解說；為供應商架構及能力宣稱，非獨立安全測試或 CEAA 效能實驗。
- **研究優先級**：**High**（Governance、Policy Enforcement、Independent Validation、Execution Observability、Manager/Tool Authority）。

### 核心貢獻：來源事實與供應商主張

NVIDIA 公布 OpenShell 企業 Agent 參考架構，結合開源 OpenShell 隔離執行環境、Vera CPU 執行 Agent harness、Vera Rubin 推論資源及 BlueField-4 DPU 上的 Sentry 安全框架。Sentry 將部分觀測與政策執行放在 Agent／Host 以外的隔離信任域，形成 defense in depth。NVIDIA 的技術文件將以下列為設計元件：

1. **DOCA Flow + DOCA Tower**：L4/L7 流量管制、Proxy、MCP/A2A/API 連線檢查。
2. **OPA / Rego**：以身分、操作、資源與執行期證據判定是否授權；與 OpenShell policy 結合。
3. **DOCA Argus**：從隔離層觀測進程、容器、執行狀態及記憶體等 runtime context。
4. **Workload Identity 與安全 Telemetry**：整合 SPIFFE/SPIRE，產生 tamper-evident / attested activity record，供稽核與事件鑑識。
5. **Inline / Out-of-band Classification**：分析工具請求／回覆與 Agent 行為；可能阻擋禁止的操作及敏感資料外洩。

NVIDIA 宣稱可進行毫秒級硬體隔離，以及低延遲本地政策判定；這些是**供應商宣稱而非已獨立量測的通用效能保證**。完整 Sentry 方案預計 2027 年初推出；**已公開的 OpenShell 軟體 ≠ 現在即可取得完整 BlueField-4 Sentry 硬體方案**。

### 與 CEAA 的直接關聯（研究推論，非 NVIDIA 結論）

- **Manager/Decision Agent 與權限分離**：Decision Agent 僅提出 Plan / Tool Request；獨立 Policy Enforcement Point 依 Skill ID、Agent identity、tool scope、資料分類與操作風險判定是否允許執行。不可讓 Manager 自行核准自己的高風險動作。
- **Skill Governance / Versioning**：將 Skill version、允許工具、前置條件、批准狀態與風險等級綁定 Policy Decision；重用歷史 execution path 也必須重新檢查當下授權與環境完整性。
- **Execution Telemetry**：建立跨 Manager → Package → Skill → Tool → Validator 的 trace 與獨立 audit event，追蹤政策阻擋、風險警示、fallback 與結果。
- **Reliability ≠ Security**：同一 Agent 即使正確完成任務仍可能越權。CEAA 的 Task Success、Decision Stability 與 Policy Compliance 必須分開量測。
- **部署選項**：先以一般 CPU／容器上的 policy sidecar、OPA、network proxy、OpenTelemetry 與 sandbox 建立硬體無關的 PoC；未來再比較 DPU out-of-band enforcement，避免將 CEAA 與專有硬體綁死。

### 可借鑑的方法與最小設計

定義 `DecisionProposal(task_id, agent_id, skill_id, skill_version, tool_id, action, resource, risk_tier, context_hash)`；每項執行前由獨立 Policy Enforcement Point 確認「身分／資源／動作／權限／版本／風險」並留下 `PolicyDecision(allow|deny|require_approval, policy_version, reason_code, trace_id)`。禁止 Agent 直接改寫政策及稽核紀錄；對 secrets、個資、模型輸入輸出及 trace 採最小化存取與遮罩。實際 API/Tool 權限仍須由可信任執行層強制落實，不能只用 Prompt 或日誌取代。

### 建議 Baseline / Experiment / Ablation

- **B0**：Direct LLM tool planning + 沙盒內統一基礎權限規則；不加入額外語意 policy layer。
- **B1**：CEAA Manager/Package routing + 相同基礎權限規則（隔離路由設計的效果）。
- **B2**：B1 + 獨立 software policy gateway / OPA + versioned Skill permissions + audit trace。
- **B3**：B2 + runtime context-aware policy、異常偵測、授權重驗與可測試的 fail-closed quarantine（軟體 PoC）。
- **Optional B4**：若未來可取得獨立硬體觀測方案，再比較 host-independent enforcement；不作為初版 CEAA 驗證前提。
- **Ablation**：分別移除獨立 policy enforcement、per-tool scopes、版本驗證、runtime context、監測／告警、不可竄改稽核、approval gate；在一致任務集上衡量對安全與任務可靠性的影響。
- **Fault-injection**：未授權 MCP tool call、越權子 Agent、竄改工具描述、prompt injection、過期憑證、錯誤版本 Skill、重播過時的 validated path、資料外洩嘗試、審核逾時與 sandbox escape 模擬；僅限隔離測試環境。
- **Evaluation**：Policy Violation Rate、Unauthorized Action Block Rate、False Allow / False Block、Containment Latency、Trace Completeness、Task Success Rate、Correct Decision Consistency、P95 Latency、Governance Overhead、Cost per Successful Task。區分「違規企圖數」與「真正成功違規數」。
- **研究控制**：保持任務、模型、工具、權限意圖、政策與資料快照一致；使用 holdout 攻擊與正常業務案例，避免僅因封鎖所有工具而虛增安全分數；紀錄人工作業成本與服務中斷影響。

### 證據、限制與建議優先序

本文是 NVIDIA 產品架構與技術解說，**不是完整安全評估報告**。毫秒級阻擋、監測準確度、誤判率與總成本尚需獨立驗證；部分能力依賴 BlueField-4 和 NVIDIA 軟體堆疊，可能有相容性、供應與採購限制。CEAA 首先驗證**獨立授權檢查與可稽核執行**的軟體方案，再決定是否研究硬體隔離；評估必須同時觀察安全性、任務成功率、決策穩定性及效能成本。

**僅新增研究筆記與候選實驗，不修改正式 v1.9 架構文件或實作程式；後續架構變更須使用者核准。**


---

## 2026-10-24 — Meta Muse Wonder：Active Memory × Active Focus 與長任務 Agent

- **原文**：[Muse Wonder: A Frontier Model For Personal & Professional AI Agents](https://research.meta.ai/blog/muse-wonder)
- **相關原始技術**：[Introducing Muse Code and Muse Spark 1.2](https://research.meta.ai/blog/introducing-muse-code-and-muse-spark-1-2)；[Introducing Muse Spark 1.3](https://research.meta.ai/blog/introducing-muse-spark-1-3)
- **作者／發布單位**：Meta AI Research / Meta Superintelligence Labs（官方頁面未列可確認的個人作者）。
- **原文日期**：2026-10-12；**研究收錄日期**：2026-10-24；**來源**：2026-10-23 DeepLearning.AI《The Batch》電子報提及 Muse Wonder / Muse Spark Open，進一步查核官方原文。
- **優先級**：**High**（Experience Memory、Context Engineering、Long-horizon Agent、Decision Stability、Tool/Model Selection、Cost per Successful Task）。
- **證據層級**：模型發布方的技術介紹及內部評估；不是 CEAA 的獨立實驗證據。

### 核心貢獻（官方描述）

Meta 將 **Active Memory** 描述為跨對話保存重要背景並在當前任務主動檢索相關資訊的能力；將 **Active Focus** 描述為長時間維持目標、遭遇阻礙時嘗試替代路徑、整合新資訊、必要時澄清與重要操作前確認。官方提到以 **FocusBench** 與 **SWE-Marathon** 等測試持續工作能力。Muse Wonder 透過 Meta Model API 與 Muse Code 提供；Muse Wonder Full 以 Muse Code 訂閱提供。Meta 另主張模型在記憶、Agent 與 Coding benchmark 上具競爭力，但成績及泛化能力須獨立複驗。

### 與 CEAA 的關聯（研究推論，非原文已證實結論）

1. **Active Memory ↔ Package-local Experience Memory**：記憶不應等於全部歷史上下文；CEAA 可以比較 task-scoped retrieval、全域 RAG 與完整歷史注入，控制 memory freshness、evidence recall 及錯誤檢索。
2. **Active Focus ↔ Manager / Decision Agent**：將 goal persistence、計畫更新、遇錯重試、風險授權與必要時澄清分為可觀測狀態，而非僅以「模型願意持續推理」判定成功。
3. **Decision Stability**：對同類任務多次執行，衡量正確 plan/tool/path 一致性；「穩定但錯誤」與「合理調整策略」需分開統計。
4. **Tool/Model Selection**：比較 Direct LLM（使用長上下文與模型內建持續推理）與 CEAA 外部 Experience-aware Hierarchical Decision；不能因 Meta 模型較強就推論外部決策層不需要。
5. **Cost/Context Budget**：將記憶檢索、推理努力、驗證、重試、fallback 及維護成本納入 Cost per Successful Task，並檢查 context rot。

### 建議 Baseline / Experiment / Ablation

- **B0**：Direct LLM + full history / full tool metadata（相同模型、任務與權限）。
- **B1**：Direct LLM + task-scoped RAG memory；允許內部自主規劃與重試。
- **B2**：CEAA Manager/Package routing，無 Experience Memory。
- **B3**：CEAA Experience-aware routing + validated execution path + fallback。
- **B4（可選）**：以 Muse Wonder 作為額外模型軸，重跑 B0–B3；與架構軸分開，避免模型能力混淆。
- **Ablation**：移除 Memory retrieval、路徑重用、goal-state checkpoint、fallback、驗證器、重要操作前授權；擾動歷史資訊位置／相似干擾／過時案例。
- **KPI**：Verified Task Success、Answer Groundedness、Correct Decision Consistency、Plan/Tool Consistency、Execution Path Entropy、Memory Retrieval Recall、Goal Completion、Wrong Tool Rate、P95 Latency、Cost per Successful Task、Stale-memory Failure Rate。
- **控制**：相同輸入／工具／資料與記憶快照，20–30 次重複（依功效分析調整）；分 cold-start/warm-start、已見／未見任務與高風險操作；所有組別使用相同安全 gate，記錄失敗與成功案例。

### 證據與限制

官方公開內容未證明 Active Memory／Focus 能獨立提高 CEAA 的穩定性，也未提供足夠資訊將性能提升歸因於記憶策略、模型規模或訓練。產品能力、基準測試與企業工作負載之間存在落差。**本條僅是研究筆記及候選對照設計，不修改 CEAA v1.9 正式架構或程式碼。**


---

## 2026-10-24 — TurboVLA：以輕量感知—動作路徑取代每步 LLM 推論的 Edge AI 對照

- **原始論文**：[TurboVLA: Real-Time Vision-Language-Action Model at 32 Hz on an RTX 4090 with <1 GB VRAM](https://arxiv.org/abs/2607.27205)
- **作者**：Hengyi Xie、Chenfei Yao、Xianjin Wu、Xuanyang Xi、Yiping Tang、Di Xu、Yingying Zhu、Dingkang Liang、Xiang Bai、Han Ding。
- **原文首次提交**：2026-07-29（arXiv:2607.27205，後續版本可能更新）；**研究收錄日期**：2026-10-24；**來源**：2026-10-23 DeepLearning.AI《The Batch》電子報報導，另查核原始論文。
- **程式碼**：https://github.com/H-EmbodVis/TurboVLA
- **優先級**：**High（Edge AI / Model & Workflow Selection / Skill Complexity Compression 的方法參考）**；**證據層級**：公開預印本、作者自述基準與開源程式碼，尚非 CEAA 驗證結果。

### 核心貢獻（論文作者主張）

常見 VLA 使用 `Vision → LLM → Action`，每次機器人控制都依賴大模型推論，增加延遲與記憶體成本。TurboVLA 改為 `Vision + Language → Action`：獨立的視覺與語言編碼器、輕量跨模態交互及小型動作解碼器。論文在 LIBERO 模擬任務報告約 **97.6–97.7%** 平均成功率、**0.2B** 參數、**31.2 ms** 推論延遲及 RTX 4090 上約 **0.9 GB** 推論 VRAM（不同版本數值略有差異）。此為特定任務及硬體上的作者結果，**不是所有機器人任務都不需要 LLM**。

### 與 CEAA 的關聯（跨領域研究推論，非論文原結論）

1. **High-level Decision vs Low-level Execution**：讓 Manager/Decision Agent 負責新任務規劃、選擇 Skill 與異常升級；已驗證、重複且低風險的子任務交由專用模型／決定性程序執行，而非每步重新呼叫通用 LLM。
2. **Skill Complexity Compression**：可借鏡「高能力規劃 → 輕量可重用執行器」的拆分方式，但 TurboVLA 本身**不是** CEAA Skill 降級或 Agent routing 的實驗。
3. **Edge/Cloud Escalation**：在 edge 端以輕量策略執行可驗證的已知工作；遇到低信心、未見狀況或風險事件才上送雲端 Manager，保留安全停機及人工接管。
4. **Reliability-first**：必須同時驗證任務成功、適應性、安全性與延遲，避免僅因節省算力就部署失效的輕量模型。

### 建議 Baseline / Experiment / Ablation

- **B0**：每個控制步驟皆由大型 VLA／LLM 決定（在可重現模擬器內）。
- **B1**：固定輕量 VLA／專用 Skill executor；不啟用雲端升級。
- **B2**：CEAA Manager 選擇專用 executor；已知任務走快路徑，未知／失敗任務升級 LLM 重新規劃。
- **B3**：B2 + Experience-aware routing、失敗記錄、驗證過的回退策略及安全 gate。
- **Ablation**：移除任務分類、經驗路由、升級閾值、獨立驗證器、錯誤回退與安全停止；改變感知噪聲、任務分布、設備能力與網路中斷條件。
- **KPI**：Task Success、Safety Violation、Correct Route Consistency、OOD Recovery、Edge VRAM、CPU/GPU Utilization、Power、P95 End-to-end Latency、Cloud Escalation Rate、Cost per Successful Task。
- **控制**：先採用作者公開程式碼及固定版本 LIBERO 模擬環境，分清模擬結果與真實機器部署；在固定任務、工具與感測條件下重複試驗。若無實體機器人，僅研究模擬／方法，不推論真實世界可靠性。

### 證據與限制

TurboVLA 的成果限於論文指定模擬與少量真機任務，且模型對複雜開放式規劃的適用性未獲全面證明。其設計與 CEAA 的架構類比需要新的對照實驗，不能把 TurboVLA 數據當成 CEAA 的性能證據。**本次只收錄研究筆記，不修改 v1.9 正式架構或實作。**
