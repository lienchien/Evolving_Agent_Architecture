# Phase 1 本機啟動與測試指南

本指南適用於 Windows PowerShell，從專案根目錄啟動目前 `dev` 的 Phase 1 Runtime。現有服務使用 Mock LLM、SQLite、Python subprocess 與 Console Notification，供本機開發與功能驗證。

## 1. 檢查環境

先在 PowerShell 切換到專案根目錄，再確認虛擬環境與 Uvicorn 可用：

```powershell
cd '<專案根目錄>'
git branch --show-current
.venv\Scripts\python.exe --version
.venv\Scripts\python.exe -m uvicorn --version
```

目前整合基準分支為 `dev`。本機已驗證 Python 3.14.3、Uvicorn 0.53.0；Phase 1 合併後完整測試為 **59 passed、1 warning**。若 `.venv` 不存在，先建立虛擬環境並安裝 `requirements.txt`：

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

直接呼叫 `.venv\Scripts\python.exe`，不需要執行 `Activate.ps1` 或修改 PowerShell execution policy。

## 2. 使用獨立 SQLite 檔案啟動

在同一個 PowerShell 視窗設定本機測試資料庫，再啟動服務：

```powershell
$env:DATABASE_URL = '.\phase1-local-test.db'
.venv\Scripts\python.exe -m uvicorn src.main:app --host 127.0.0.1 --port 8000
```

看到 `Application startup complete` 後，開啟 <http://127.0.0.1:8000/docs>。程式會自動建立 SQLite 檔案、資料表及索引；不需要手動建表。`DATABASE_URL` 目前表示 **SQLite 檔案路徑**，不能填 PostgreSQL DSN。

測試資料會寫入 `phase1-local-test.db`。能力測試報告另會輸出到專案根目錄的 `capability_library/<capability_id>/test_report.json` 與 `test_report.md`。請先確認檔名未與要保留的資料重複，並避免把資料庫檔案或測試報告誤加入 Git。

## 3. 在 API 頁面完成一輪流程

在 `/docs` 依序操作：

1. 展開 `POST /api/tasks`，按 **Try it out**，送出：

   ```json
   {
     "task_family": "phase1_word_count_demo",
     "description": "count words",
     "input": {"text": "one two three"}
   }
   ```

   首次使用這個 task family 時，預期 HTTP 200、`status` 為 `capability_pending_approval`、`output` 為 `null`。記下回應中的 `capability_id`、`task_id` 和 `trace_id`。

2. 用 `GET /api/capabilities/{capability_id}/test-report` 檢查測試報告，再用 `GET /api/capabilities/{capability_id}` 確認狀態為 `pending_approval`。測試報告使用固定測例，不會隨後續任務的輸入而改變；實際字數請查看 `POST /api/tasks` 回應的 `output`。

3. 展開 `POST /api/approvals/{capability_id}/approve`，填入剛取得的 ID，request body 使用 `{}`。預期回應的 capability `status` 為 `active`。

4. 再次以相同 JSON 呼叫 `POST /api/tasks`。預期 `status` 為 `completed`，`output.word_count` 為 `3`，並回傳新的 `task_id` 與 `trace_id`。

5. 用第二次回應的 `trace_id` 查 `GET /api/telemetry/traces/{trace_id}`；可看到 routing decision 與成功的 execution observation。也可查 `GET /api/telemetry/summary?task_family=phase1_word_count_demo` 和 `GET /api/research/tasks?task_family=phase1_word_count_demo`。

若使用的資料庫中已有同名 active capability，第一步可能直接得到 `completed`；改用新的 `task_family` 或新的測試資料庫，即可測完整建立與核准流程。

## 4. 執行自動測試與重啟驗證

另開一個 PowerShell 視窗，從專案根目錄執行完整測試：

```powershell
.venv\Scripts\python.exe -m pytest -q --basetemp=.pytest-tmp-phase1-local -p no:cacheprovider
```

Windows 若對既有 pytest 暫存目錄回報 `Permission denied`，改用另一個尚不存在的 `--basetemp` 名稱重試。測試時使用的是隔離資料庫，不應把暫存目錄加入 Git。既有 Starlette／AnyIO `BlockingPortal` 棄用警告不代表測試失敗。

若要驗證 API 資料持久性，在伺服器視窗按 `Ctrl+C`，以相同的 `DATABASE_URL` 重啟，再查一次 capability、test report 與 telemetry。換成另一個資料庫檔案會得到另一組獨立資料。要停止服務，按 `Ctrl+C`；要取消這個 PowerShell 視窗的資料庫設定，可執行 `Remove-Item Env:DATABASE_URL`。

## 常見啟動問題

- 找不到 `.venv\Scripts\python.exe`：確認目前位置是專案根目錄；若虛擬環境尚未建立，依第 1 步建立並安裝依賴。
- 顯示 `Address already in use`：先停止占用 8000 埠的本機服務，或把啟動指令的 `--port 8000` 改為其他埠，並使用對應埠號開啟 `/docs`。
- SQLite 顯示 `unable to open database file`：確認 PowerShell 對目前目錄有寫入權限，並檢查 `DATABASE_URL` 指向的父目錄是否存在。
- 重新啟動後找不到先前的 capability：確認使用相同的 `DATABASE_URL`，且每次都從同一個專案根目錄啟動；相對路徑會依目前工作目錄解析。

## 注意事項

- 僅在本機 `127.0.0.1` 測試。目前 API 沒有正式認證、管理員授權或 tenant 資料隔離，請勿對外公開連接埠。
- Python subprocess executor 不具正式安全隔離；不要提供不可信的程式碼或敏感資料。核准請求中的 `reviewer` 由呼叫端填入，不能作為真實身分證明。
- Mock LLM 只產生固定範例，不會呼叫真實模型；token usage 可能是 `unavailable`。不要用此結果推論真實 LLM 成本或效能。
- `phase1-local-test.db` 與 `capability_library/` 下的測試報告是本機產物。測試完成後先確認不再需要，再自行清理指定檔案；不要批次刪除整個報告目錄或其他資料庫。
- PostgreSQL adapter、Docker sandbox、真實 LLM provider 與正式授權屬於 Phase 1.5，尚未接入此啟動流程。
