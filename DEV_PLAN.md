# Capability-Evolving Agent — Phase 1 MVP (Agent + API 系統面)

## Context

專案目前只有兩份設計文件（System Design v1.6、Tech Stack v1），尚無任何程式碼，也不是 git repo。使用者希望先聚焦在 **Agent 與 API 系統面**的開發，暫緩 Sharing / Import / Export / Marketplace 等文件中標記為「Future Reserved」的部分。

使用者已確認兩個關鍵決策：
1. **起手方式**：先用最小可行版本（in-memory/SQLite + mock LLM）跑通一次完整循環，之後再逐步替換成真實 PostgreSQL / Docker sandbox / LiteLLM。
2. **LLM 憑證**：目前沒有 NVIDIA NIM / OpenRouter API Key，先用 Mock LLM Provider。

環境檢查發現：本機 `python` 只有 Windows Store 的 stub（非真實直譯器），`git` 存在，`docker` 未確認在 PATH 上。使用者明確要求**只做系統開發（寫程式碼/專案骨架），不要安裝任何額外程式**（包含 Python 本身）。因此本輪產出是**原始碼與專案結構**，執行環境安裝與 `pip install` 由使用者自行之後處理，我不會執行安裝動作。

目標：實作 System Design v1.6 §58 (Phase 1 — Core MVP) 所列核心循環，讓 Agent 能自主偵測能力缺口、產生候選能力、驗證、測試、產生報告、通知、經人工核准後啟用，並於後續任務重用 —— 全程用 mock/in-memory 元件證明流程可行，介面預留未來替換真實服務。

---

## 範圍邊界

**現在做（對應 §71「真的要做」清單）：**
Gap → Generate → Validate → Test → Report → Notify → Approve → Activate → Reuse

**現在不做（對應 §71「只需要預留」清單，本輪完全不 scaffold）：**
Export / Import / Publish / Discover / Sync / Marketplace / Collective Network、Tenant/Sharing 進階邏輯（schema 欄位保留但不做邏輯）、真實 PostgreSQL / Docker sandbox / LiteLLM / NVIDIA NIM / OpenRouter / pgvector / Phoenix / MLflow / Redis — 這些都用符合文件 §3.7~3.9（Model Independent / Infrastructure Independent / Implement Simple, Interface for Complex）的介面占位，之後可平滑替換。

---

## 專案結構

```
Evolving_Agent_Architecture/
├── requirements.txt
├── .env.example
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
│   │   ├── subprocess_sandbox.py     # 子行程沙箱（Docker 之前的替代品）
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

## 驗證方式

1. `tests/test_full_loop.py`：模擬「提交未知 task_family 任務 → 觸發 gap → evolution 產生候選 → validation/testing 通過 → pending_approval → 呼叫 approve → capability 變 active」，接著「提交同 task_family 第二個任務 → 直接 reuse，不再產生新 gap」，斷言全程狀態與輸出正確。
2. `tests/test_capability_schema.py`、`test_capability_service.py`：涵蓋 schema 預設值與狀態機合法/非法轉換。
3. 使用者之後自行安裝 Python + `pip install -r requirements.txt` 後，可用 `uvicorn src.main:app --reload` 啟動 API，並用 curl/Swagger UI（`/docs`）手動跑一次相同流程；也可直接 `pytest` 跑上述測試。**這一輪只交付程式碼與測試，不執行安裝或啟動任何服務。**

---

## 後續替換點（先留介面，不現在做）

- `MockLLMProvider` → `LiteLLMProvider`（接 NVIDIA NIM / OpenRouter，只需要 `.env` 塞 API Key，並在 `src/main.py` 的 `Container` 換掉一行）
- `SubprocessSandbox` → Docker-based sandbox（`interfaces/sandbox.py` 介面不變）
- `SqliteCapabilityRepository` → PostgreSQL repository（`interfaces/repository.py` 介面不變）
- `InMemoryEvolutionQueue` → Redis/RQ（`interfaces/queue.py` 介面不變）
- Gap Detection 關鍵字比對 → pgvector 語意搜尋（Phase 2）
