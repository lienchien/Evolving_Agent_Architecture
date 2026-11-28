# Phase 1.5-B 真實 LLM 前置準備

本頁記錄雲端 LiteLLM 驗證；本地優先路徑與跨大小實驗見 [Ollama 本地推理](PHASE15_LOCAL_INFERENCE.md)。

目前已提供**離線設定檢查及獨立 LiteLLM adapter**；本機 `.venv` 已安裝 LiteLLM 1.109.0。使用者已在自己的 PowerShell 環境完成 OpenRouter 免費模型的獨立連線與 adapter smoke test，沒有將 key 寫入專案，也沒有執行模型產生的程式碼。主程式仍會拒絕 `LLM_PROVIDER=litellm`，且明確拒絕注入 `LiteLLMProvider`，直到隔離與治理邊界完成。

## 需要額外設定什麼

1. 選定第一個供應商：OpenRouter 或 NVIDIA NIM，並確認帳戶可使用的模型。LiteLLM 的模型名稱須分別以 `openrouter/` 或 `nvidia_nim/` 開頭；不要把範例中的 `<provider>/<model>` 原樣當成模型名稱。
2. 取得該供應商的 API key，**只在執行環境或 secret provider 注入**。OpenRouter 使用 `OPENROUTER_API_KEY`；透過 LiteLLM 呼叫 NVIDIA NIM 使用 `NVIDIA_NIM_API_KEY`。這兩種 key 不要混用，也不要寫入 `.env.example`、文件、Git 或測試輸出。
3. 確認供應商帳戶的模型權限、預算／費用上限及可連線的 HTTPS 網路。Adapter 的可選依賴列於 `requirements-llm.txt`，單次逾時與輸出上限由 `LLM_REQUEST_TIMEOUT_SECONDS`、`LLM_MAX_OUTPUT_TOKENS` 設定；SDK 內部 retry 已關閉。應用層成本硬上限、健康檢查、provider fallback 與實際帳單核對**尚未實作或驗證**，不能只依賴設定值控制花費。
   OpenRouter 的獨立 adapter 可選 `LLM_REASONING_EFFORT=none` 與 `LLM_RESPONSE_FORMAT=json_object`；空值保持供應商預設。JSON 模式只改善語法，不保證符合本機 schema，adapter 仍會拒絕不完整或不符格式的輸出。NVIDIA NIM 的這兩個參數尚未驗證，設定時會拒絕建立 adapter。
4. 開發測試需使用獨立 SQLite 路徑與報告目錄。現有 API 沒有正式認證，subprocess 也沒有安全隔離；不要將服務對外公開或把真實模型輸出的程式碼交給現有 subprocess 執行。Docker Sandbox 與授權政策接入前，不做真實生成的端到端驗證。

官方設定參考：[LiteLLM OpenRouter](https://docs.litellm.ai/docs/providers/openrouter)、[LiteLLM NVIDIA NIM](https://docs.litellm.ai/docs/providers/nvidia_nim)。NVIDIA 自行部署的 NIM 與雲端 API Catalog 可能需要不同的端點及認證流程；先以選定的部署型態確認，不預設兩者相同。

## 離線檢查（不發送請求）

在獨立的 PowerShell 視窗、專案根目錄執行；以下以 OpenRouter 為例，模型名稱請換成帳戶可使用者：

```powershell
$env:LLM_PROVIDER = 'litellm'
$env:LLM_MODEL = 'openrouter/<provider>/<model>'
# 對已驗證的 OpenRouter 免費模型可另設下列兩項；主 API 仍禁止真實 Provider。
$env:LLM_REASONING_EFFORT = 'none'
$env:LLM_RESPONSE_FORMAT = 'json_object'
# 若已取得 key，請在目前 shell 設定 OPENROUTER_API_KEY；不要寫入檔案。
.venv\Scripts\python.exe -m src.provider_preflight
```

若選 NVIDIA NIM，改用 `nvidia_nim/<provider>/<model>` 與 `NVIDIA_NIM_API_KEY`。檢查結果只列出所需環境變數名稱、模型前綴與缺少的項目，不印出 key。缺少設定時結束碼為 1；設定齊全時為 0，但這**不代表**帳戶、模型、費用或網路已驗證，也不代表主程式已啟用真實 Provider。

完成檢查後，如需啟動現有 Phase 1 本機服務，請另開未設定真實 Provider 的 shell，或將 `LLM_PROVIDER` 恢復為 `mock` 並清空 `LLM_MODEL`。

## Adapter 目前的驗證邊界

`src/infrastructure/litellm_provider.py` 實作現有 `LLMProvider` 契約：將能力與邊界測例要求送至 LiteLLM `completion()`，只接受完整且符合 schema 的 JSON 回應，並將回應中的 token usage 映射至 `TokenUsage`。只有明確出現在 response `usage.cost` 的數值才會填入 `provider_cost_usd`；不使用 LiteLLM `completion_cost()` 估算值冒充供應商帳單。錯誤訊息經過淨化，不記錄原始 provider exception 或 key。生成 prompt 不包含 `task_input` 的值，但仍包含任務描述；真實外送前須完成資料治理。

## OpenRouter 獨立實測紀錄（使用者回報，2026-11-15）

- `openrouter/free` 基本連線成功，路由至 `inclusionai/ling-3.2-flash:free`；金鑰驗證端點回應 200。金鑰值未提供給專案或紀錄文件。
- `generate_capability()` 以該免費模型產生 `word_count_smoke`，adapter 解析通過；回報 input 130、output 396、reasoning 270、total 526 tokens，response `usage.cost=0.0`。
- `generate_boundary_tests()` 在供應商預設推理下曾回 `finish_reason=length`、空正文；關閉推理後正文完整，但 prompt-only JSON 不符本機 schema。再以 `reasoning_effort=none` 與 `response_format=json_object` 獨立呼叫後，15 個測例通過 adapter 格式驗證；回報 input 122、output 490、reasoning 0、total 612 tokens，response `usage.cost=0.0`。
- 測例尚未執行，語意正確性及生成程式碼安全性未驗證；`0.0` 是該次回應提供的費用欄位，不等同正式帳單核對。上述選項已做成可選設定，不會自動啟用主 API。

若要在**已有 OpenRouter key 的同一 PowerShell 視窗**驗證新設定接線，可做一次獨立 boundary 呼叫；這會使用免費模型的請求額度，不會建立資料庫、保存能力或執行示例程式碼。請先確認 [模型頁](https://openrouter.ai/inclusionai/ling-3.2-flash%3Afree) 仍標示免費：

```powershell
$env:LLM_PROVIDER = 'litellm'
$env:LLM_MODEL = 'openrouter/inclusionai/ling-3.2-flash:free'
$env:LLM_REASONING_EFFORT = 'none'
$env:LLM_RESPONSE_FORMAT = 'json_object'
@'
from src.config import Settings
from src.domain.capability import Capability, Implementation
from src.infrastructure.litellm_provider import LiteLLMProvider

adapter = LiteLLMProvider.from_settings(Settings.from_environment())
capability = Capability(
    name="word_count_smoke", task_family="word_count_smoke",
    inputs=["text"], outputs=["word_count"],
    implementation=Implementation(code="def run(input: dict) -> dict:\n    return {'word_count': len(input['text'].split())}"),
)
result = adapter.generate_boundary_tests(capability)
print("boundary_cases:", len(result.value))
print("usage:", result.usage.model_dump(mode="json", exclude_none=True))
'@ | .venv\Scripts\python.exe -
```

此驗證只檢查格式和供應商 usage；測例內容及程式碼不應因通過 schema 就被視為可信。失敗時 adapter 會淨化錯誤訊息，不要開啟包含金鑰或完整提示的 debug log。

Adapter 的單元測試使用注入的假 `completion()`；本機 `.venv` 亦曾以 LiteLLM 1.109.0 的 SDK `mock_response` 驗證物件解析，`pip check` 無相依衝突。使用者回報的獨立實測提供 OpenRouter 模型及 usage 的相容性證據，但尚未驗證新設定接線後的真實呼叫、模型 JSON 的跨請求穩定性、正式帳單或端到端安全性。`requirements-llm.txt` 是可選依賴清單；即使設定和憑證檢查通過，主 API 仍不可使用 adapter。後續需完成 Docker Sandbox、認證／政策與受控測試方案，再決定是否開放端到端執行。

LiteLLM 匯入時曾嘗試下載模型價格表；在受限網路下改用套件內建副本。若做**純離線 SDK 測試**，可在匯入前設定 `LITELLM_OFFLINE_MODE=true` 避免此類目錄更新。此設定不會阻止對已配置模型端點的請求，不能取代 API key、網路隔離或費用控管；見 [LiteLLM 官方離線模式說明](https://docs.litellm.ai/docs/proxy/outbound_requests)。
