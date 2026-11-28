# Phase 1.5-A Runtime Configuration

此階段只建立設定解析、驗證與既有 Phase 1 adapter 的接線，不代表真實 Provider、PostgreSQL、Docker Sandbox 或 Code Builder 已可使用。

## 設定來源與環境

設定由 `Settings.from_environment()` 在 `Container` 建立時讀取 process environment，不在 module import 時快取；`.env.example` 只是範本，程式不會自動讀取 `.env`。請由啟動程序注入環境變數，密鑰不可寫入 Git。

| 變數 | 預設 | 目前作用 |
| --- | --- | --- |
| `APP_PROFILE` | `development` | `development`、`test` 可執行現有 local runtime；`production-like` 在安全基礎完成前拒絕啟動 |
| `LLM_PROVIDER` | `mock` | API 目前僅使用 `mock`；`litellm` 和 `ollama` 僅可作獨立 adapter 驗證 |
| `LLM_MODEL` | 空 | 獨立 adapter 所用模型；現有 Mock API 不可設定 |
| `LLM_REQUEST_TIMEOUT_SECONDS` | `30` | 獨立 LiteLLM adapter 的單次請求逾時，須為正數 |
| `LLM_MAX_OUTPUT_TOKENS` | `2048` | 獨立 LiteLLM adapter 的輸出上限，範圍 1–8192 |
| `OLLAMA_CONTEXT_TOKENS` | `4096` | Ollama context，範圍 512–32768，須大於輸出上限；不建議直接使用上限 |
| `LLM_REASONING_EFFORT` | 空 | 獨立 OpenRouter adapter 的推理強度；可選 `none`、`minimal`、`low`、`medium`、`high`、`xhigh`、`max`，空值沿用供應商預設 |
| `LLM_RESPONSE_FORMAT` | 空 | 獨立 OpenRouter adapter 可設 `json_object` 要求 JSON 語法；空值沿用供應商預設，schema 仍由本機嚴格驗證 |
| `DATABASE_URL` | `capability_library.db` | 目前僅 SQLite 檔案路徑；PostgreSQL 至 Phase 1.5-C，DSN 不會被當成檔名使用 |
| `REPORT_DIRECTORY` | `capability_library` | 能力測試報告輸出目錄 |
| `SANDBOX_BACKEND` | `subprocess` | 目前僅 subprocess；`docker` 保留至 Phase 1.5-D，選用時拒絕啟動 |
| `SANDBOX_TIMEOUT_SECONDS` | `5` | 套用至 subprocess 執行逾時，須為正數 |
| `RETRY_HARD_MAX` | `3` | 現有 retry policy 的 hard cap，可設為 0–3 |
| `RETRY_BACKOFF_MS` | `0` | 現有 retry policy 的基礎 backoff，可設為 0–60000 |
| `BUILDER_MAX_TOKENS` / `BUILDER_MAX_COST_USD` | `0` | Phase 1.5-E 保留欄位；非零值目前拒絕啟動，不假裝已執行預算控制 |
| `ENABLE_CODE_BUILDER` | `false` | Phase 1.5-E 保留開關；設為 true 目前拒絕啟動 |

`test` profile 必須明確指定 `DATABASE_URL` 和 `REPORT_DIRECTORY`，避免測試誤用開發資料。程式也會拒絕無效數值、未知 backend 與不支援的 DSN。

## 本機範例（PowerShell）

```powershell
$env:APP_PROFILE = 'development'
$env:DATABASE_URL = '.\phase15-local.db'
$env:REPORT_DIRECTORY = '.\capability_library'
.venv\Scripts\python.exe -m uvicorn src.main:app --host 127.0.0.1 --port 8000
```

目前 API 仍無正式認證／授權，subprocess 也沒有真正的安全隔離。僅供 loopback 本機開發；不要將此設定當作 production-ready 部署。真實 Provider 憑證應由啟動環境或 secret provider 注入；B 階段的獨立 adapter 已實作，但仍拒絕接入主 API。

Phase 1.5-B 的離線設定檢查與額外操作見 [真實 LLM 前置準備](PHASE15_REAL_PROVIDER_PREPARATION.md)；此檢查不會啟用 adapter 或送出請求。
