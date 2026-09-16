# Capability-Evolving Agent — Phase 1 MVP (Agent + API 系統面)

## 狀態：骨架已實作完成，尚未執行/驗證

以下所有程式碼（`src/`、`tests/`）已依本計畫寫入專案目錄。因為本機沒有可用的 Python 直譯器，且使用者要求不安裝任何額外程式，**目前尚未實際跑過 `pytest` 或啟動過 API**，邏輯正確性僅靠設計時的手動推導確認，尚待使用者在自己的環境安裝依賴後驗證。

`.env.example` 因權限設定的 deny rule 被擋下，改以 **`env.example`**（無開頭句點）建立在專案根目錄；使用時請自行複製為 `.env`。

## Context

專案目前已完成 **Phase 1 MVP 的程式骨架與測試案例**，包含 Main Agent、Evolution Agent、Capability lifecycle、Validation / Testing、Approval、Notification、Audit、FastAPI routes 與端對端測試。現階段仍聚焦在 **Agent 與 API 系統面**，尚未進入真實基礎設施整合與正式執行驗證。

目前核心流程已依 System Design v1.6 建立：

`Gap → Generate → Validate → Test → Report → Notify → Approve → Activate → Reuse`

Sharing / Import / Export / Marketplace / Collective Capability Network 等設計仍維持 **Future Reserved**，本階段不實作完整邏輯，只保留必要 schema 與介面擴充點。

使用者已確認兩個關鍵決策：
1. **起手方式**：先用最小可行版本（in-memory/SQLite + mock LLM）跑通一次完整循環，之後再逐步替換成真實 PostgreSQL / Docker sandbox / LiteLLM。
2. **LLM 憑證**：目前沒有 NVIDIA NIM / OpenRouter API Key，先用 Mock LLM Provider。

目前 repo 已存在完整原始碼與測試，但尚未在實際 Python 執行環境跑過 `pytest` 或啟動 API。因此本階段的剩餘工作重點，是先完成 **Phase 1 骨架驗證**，再進入 **Phase 1.5 Real Infrastructure Integration**。

目標：實作並驗證 System Design v1.6 §58 (Phase 1 — Core MVP) 所列核心循環，讓 Agent 能自主偵測能力缺口、產生候選能力、驗證、測試、產生報告、通知、經人工核准後啟用，並於後續任務重用 —— 目前先使用 mock/in-memory 元件證明流程，介面預留未來替換真實服務。

---

## 範圍邊界

**現在做（對應 §71「真的要做」清單）：**
Gap → Generate → Validate → Test → Report → Notify → Approve → Activate → Reuse

**現在不做（對應 §71「只需要預留」清單，本輪完全不 scaffold）：**
Export / Import / Publish / Discover / Sync / Marketplace / Collective Network、Tenant/Sharing 進階邏輯（schema 欄位保留但不做邏輯）、真實 PostgreSQL / Docker sandbox / LiteLLM / NVIDIA NIM / OpenRouter / pgvector / Phoenix / MLflow / Redis — 這些都用符合文件 §3.7~3.9（Model Independent / Infrastructure Independent / Implement Simple, Interface for Complex）的介面占位，之後可平滑替換。

---

## 專案結構

```text
Evolving_Agent_Architecture/
├── DEV_PLAN.md                      # 本文件
├── PROJECT_STATUS.md                # 開發階段與完成度追蹤
├── requirements.txt
├── env.example                      # 複製為 .env 後填入金鑰
├── .gitignore
├── pytest.ini
├── src/
│   ├── main.py                      # FastAPI app entrypoint + 手動 DI container
│   ├── config.py                    # Settings（mock/真實服務切換用的預留點）
│   ├── domain/
│   │   ├── capability.py            # Capability schema (§10) + lifecycle enum (§13)
│   │   ├── gap.py                   # CapabilityGap (§6)
│   │   ├── report.py                # TestReport (§20)
│   │   ├── approval.py              # ApprovalRecord (§22/24)
│   │   └── events.py                # Event 定義 (§25 核心事件子集)
│   ├── interfaces/
│   │   ├── llm.py                   # LLMProvider ABC
│   │   ├── queue.py                 # QueueInterface ABC
│   │   ├── sandbox.py               # SandboxInterface ABC
│   │   ├── notification.py          # NotificationProvider ABC
│   │   └── repository.py            # CapabilityRepository ABC
│   ├── infrastructure/
│   │   ├── mock_llm.py              # MockLLMProvider（樣板式生成）
│   │   ├── memory_queue.py          # In-memory EvolutionQueue
│   │   ├── sqlite_repository.py     # SQLite 版 CapabilityRepository
│   │   ├── subprocess_sandbox.py    # 子行程沙箱（Docker 之前的替代品）
│   │   └── console_notification.py  # Console 版 NotificationProvider
│   ├── services/
│   │   ├── capability_service.py    # Registry CRUD + lifecycle 狀態機
│   │   ├── gap_detection_service.py
│   │   ├── evolution_service.py
│   │   ├── validation_service.py
│   │   ├── testing_service.py
│   │   ├── policy_service.py        # can_generate/validate/execute/activate stub
│   │   ├── approval_service.py
│   │   ├── notification_service.py
│   │   ├── execution_service.py     # CapabilityExecutor
│   │   ├── report_store.py
│   │   └── audit_service.py         # append-only audit log
│   ├── agents/
│   │   ├── main_agent.py            # LangGraph: Task → Search → Execute | Gap
│   │   └── evolution_agent.py       # LangGraph: Gap → Generate → Validate → Test → Report
│   └── api/
│       └── routes/
│           ├── tasks.py             # POST /api/tasks
│           ├── capabilities.py      # GET /api/capabilities[/{id}][/test-report]
│           ├── evolution.py         # GET /api/evolution/queue
│           ├── approvals.py         # POST /api/approvals/{capability_id}/...
│           └── audit.py             # GET /api/audit
└── tests/
    ├── test_capability_schema.py
    ├── test_capability_service.py
    └── test_full_loop.py            # 端對端：新任務→gap→evolution→approve→reuse
```

---

## 核心元件設計

### Capability Schema (`domain/capability.py`)
依 §10 定義 Pydantic model，欄位含 `capability_id / capability_version / name / description / task_family / inputs / outputs / preconditions / dependencies / implementation / validation_requirements / safety_requirements / trust_level / status / sharing_policy(預設 private_only) / tenant_id/owner_id/organization_id/scope(預留，先用 default 值) / created_at/updated_at`。狀態機依 §13：`draft → candidate → validating → testing → tested → pending_approval → approved → active → deprecated/revoked/archived`。

### Main Agent (`agents/main_agent.py`)
用 LangGraph 定義簡單狀態圖：`receive_task → search_capability → (found: execute_capability | not_found: create_gap + enqueue)`。對應 §5 職責邊界（不能直接修改/啟用/上傳 Capability）。

### Gap Detection (`services/gap_detection_service.py`)
MVP 用 `task_family` 關鍵字比對 registry（§59 向量檢索留待 Phase 2 用 pgvector，這裡先用簡單字串比對），找不到就建立 `CapabilityGap` 並丟進 in-memory queue。

### Evolution Service + Mock LLM
`MockLLMProvider` 不是真的呼叫外部 API，而是依 task 描述關鍵字比對內建樣板（csv 欄位統計、文字字數統計）產生 `implementation.py` 程式碼字串與基礎測試案例，證明 Generate→Validate→Test 全流程可跑，之後替換 LiteLLM+NVIDIA NIM 時只需換掉這個 Provider。

### Validation / Testing (`subprocess_sandbox.py`)
`SandboxInterface.run_test_cases/execute` 用 Python subprocess（非 Docker）執行產生的程式碼、餵測試輸入、比對輸出，介面與未來 Docker/gVisor 替換相容。ValidationService 跑 functional 案例；TestingService（獨立 agent，對應 §17）再跑額外的 boundary 案例，產生 `test_report.json` + `test_report.md`（§20）存到 `capability_library/CAP-xxxx/`。

### Registry / Approval / Notification
`CapabilityService` 管狀態轉換與版本；`ApprovalService` 提供 `approve/reject/request_revision/approve_with_restrictions`（§24），且會先問過 `PolicyService.can_activate()`（§53）才真正 Activate；`NotificationService` 用 console provider 印出「有能力待審核」訊息（§23）。

### API (FastAPI, `src/api/routes/*`)
對應 §27 Service Layer 列出的路徑草案：`/api/tasks`、`/api/capabilities`、`/api/evolution`、`/api/approvals`、`/api/audit`。

### Audit Trail
`audit_service.py` 用 in-memory append-only list 記錄 §26 列出的動作（request_approval/approve/reject/request_revision），提供 `GET /api/audit` 查詢。

---

## 驗證方式（尚未執行，待使用者環境備妥後跑一次）

1. `tests/test_capability_schema.py`、`test_capability_service.py`：涵蓋 schema 預設值與狀態機合法/非法轉換。
2. `tests/test_full_loop.py`：模擬「提交未知 task_family 任務 → 觸發 gap → evolution 產生候選 → validation/testing 通過 → pending_approval → 呼叫 approve → capability 變 active」，接著「提交同 task_family 第二個任務 → 直接 reuse，不再產生新 gap」，斷言全程狀態與輸出正確。
3. 使用者自行安裝 Python 3.10+ 後：
   ```text
   pip install -r requirements.txt
   pytest
   uvicorn src.main:app --reload
   ```
   之後可用 curl 或 Swagger UI (`/docs`) 手動跑一次相同流程。

### 首次執行時建議留意的風險點

- **LangGraph API 版本**：`agents/main_agent.py`、`agents/evolution_agent.py` 用了 `StateGraph.add_conditional_edges` 標準寫法，若 `requirements.txt` 裝到的版本 API 有差異，可能需要微調。
- **Windows subprocess sandbox**：`infrastructure/subprocess_sandbox.py` 用 `sys.executable` 開子行程執行生成的程式碼，在 Windows 上路徑/編碼理論上沒問題，但這是唯一沒有實際跑過的執行路徑，值得先手動測一次。
- **SQLite 檔案位置**：預設會在執行時的當前目錄產生 `capability_library.db`（與 `capability_library/` 產物資料夾同名但不同東西，注意不要搞混）。

---

## 下一階段：Phase 1.5 — Real Infrastructure Integration

Phase 1 骨架完成並通過基本測試後，下一步將逐步把 mock / local substitute 換成真實基礎設施：

1. `MockLLMProvider` → LiteLLM Provider
2. 接入 NVIDIA NIM / OpenRouter
3. `SqliteCapabilityRepository` → PostgreSQL
4. `SubprocessSandbox` → Docker Sandbox
5. 增加更完整的 autonomous test / generalization cases

Phase 2 再導入 pgvector、semantic capability retrieval 與更完整的 evaluation / observability。

---

## 後續替換點

- `MockLLMProvider` → `LiteLLMProvider`（接 NVIDIA NIM / OpenRouter，只需要 `.env` 塞 API Key，並在 `src/main.py` 的 `Container` 換掉 adapter）
- `SubprocessSandbox` → Docker-based sandbox（`interfaces/sandbox.py` 介面不變）
- `SqliteCapabilityRepository` → PostgreSQL repository（`interfaces/repository.py` 介面不變）
- `InMemoryEvolutionQueue` → Redis/RQ（`interfaces/queue.py` 介面不變）
- Gap Detection 關鍵字比對 → pgvector 語意搜尋（Phase 2）
