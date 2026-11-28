# Phase 1.5-B：Ollama 本地推理與模型大小對照

本地推理是 Phase 1.5-B 的優先開發路徑，使用已量化的模型權重，不訓練或微調。Mock 仍是可重現的單元測試基線；OpenRouter／NVIDIA NIM 保留為操作者明確選擇的雲端路徑，不是本地請求的自動 fallback。

## 獨立 adapter

- `OllamaProvider` 和雲端 adapter 共用 `LLMProvider` 契約、提示及 Pydantic 驗證。Ollama 原生 `/api/chat` 另收到 JSON Schema；回應截斷、模型不符或不符合 schema 一律拒絕。
- 僅連 `127.0.0.1:11434`，不走代理、不跟隨重導向、不要求金鑰、不下載模型。推理前檢查已安裝的明確 `name:tag`，拒絕雲端標籤與遠端 metadata。Ollama daemon 應由操作者管理，勿對外開放；需要獨立的 daemon 離線政策時，可依 [Ollama 本機模式](https://docs.ollama.com/faq) 設為 `OLLAMA_NO_CLOUD=1` 並重啟。專案不代改 daemon 設定。
- 可設逾時、context 與輸出上限；同一 Python 程序一次只允許一個推理請求，不等待或重試。這不是跨程序或伺服器層限流。模型查詢可驗證服務及安裝狀態，不等同完整運行健康監控。
- 只記錄 Ollama 回報的 prompt／output tokens；兩者皆有才加總。沒有 USD 帳單欄位，不填零或推估電力成本。主 API 仍拒絕透過設定或依賴注入接入真實 adapter，SQLite／PostgreSQL 及 Docker／授權的路線維持不變。

## 本機重跑

先確定 Ollama 已啟動且兩個模型都在 `ollama list`。如需下載，模型名稱為 `qwen2.5-coder:3b-instruct-q4_K_M` 與 `qwen2.5-coder:7b-instruct-q4_K_M`（約 1.93／4.68 GB）。下列指令從專案根目錄執行；預設跑兩個模型各一輪，可用 `--repeats 3` 重複或 `--models` 選擇至少兩個已安裝標籤。

```powershell
.\.venv\Scripts\python.exe -B -m src.ollama_model_benchmark
```

只輸出逐模型 JSON 摘要（每筆含格式、契約、預期值正確數、token、延遲、冷暖標記和裝置分配）；不輸出原始提示或生成程式碼，不建立資料庫或寫入能力目錄。非預期格式也會被記錄，而不是自動重試。若需測試設定解析，可在隔離的 PowerShell 視窗設定：

```powershell
$env:LLM_PROVIDER = 'ollama'
$env:LLM_MODEL = 'qwen2.5-coder:3b-instruct-q4_K_M'
$env:LLM_REQUEST_TIMEOUT_SECONDS = '90'
$env:LLM_MAX_OUTPUT_TOKENS = '512'
$env:OLLAMA_CONTEXT_TOKENS = '4096'
Remove-Item Env:LLM_REASONING_EFFORT, Env:LLM_RESPONSE_FORMAT -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe -B -m src.provider_preflight
```

Preflight 不連網、也不呼叫 Ollama。獨立程式可用 `OllamaProvider.from_settings(Settings.from_environment())` 與 `model_info()` 做本機 readiness。不要用這組環境變數啟動主 API。

## 2026-11-28 初測

同一台 Windows 主機（i5-14600K、80 GiB RAM、Radeon RX 6650 XT 8 GB），Ollama `0.40.19`；兩個模型都採 Q4_K_M、4K context、512 輸出 tokens 上限、temperature 0、seed 42、依序單請求。同組任務分別是空白分隔字數、Python Unicode code-point 字元數。每項任務各呼叫一次能力生成與一次邊界測例生成。邊界輸入使用固定、人工撰寫的實作文字；期待值與可信的 Python 參考函數比對。**不執行任何模型生成的程式碼。**

| 模型 | 格式／契約通過 | 測例期待值正確 | 模型未載入首筆 | 已載入後其餘三筆 | 總 token | Ollama 回報 GPU 負載 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 3.1B | 4/4 | 6/6 | 6.71 s | 0.94–1.40 s | 928 | 2.16 GB（載入量 100%） |
| 7.6B | 4/4 | 6/6 | 54.88 s | 19.72–40.96 s | 998 | 4.76 GB（載入量 100%） |

模型 digest：3B `f72c60cabf6237b07f6e632b2c48d533cef25eda2efbd34bed21c5e9c01e6225`；7B `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`。延遲為 adapter 的 wall time；「暖」只表示模型已載入，並非固定 GPU 時脈或排除其他系統負載。初期與測試套件有時序重疊，且每個任務只跑一輪，不能把延遲差距歸因於參數量，也不能宣稱兩模型一般能力相同。暫以 3B 做短任務開發回歸，7B 保留品質對照；正式比較應採固定題庫、交錯順序、多次重跑、控制其他負載，並另在治理完成後驗證生成程式碼。
