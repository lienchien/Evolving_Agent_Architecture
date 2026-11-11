# CEAA · Agent Constellation (demo)

以 React + React Three Fiber + Three.js 建立的動態 Agent 監控介面，包含：

- 3D 粒子群、發光 Agent 節點、弧線和沿路徑移動的光點
- 可拖曳/縮放場景、節點點選、旋轉控制
- 上方 KPI、底部事件流和 Agent 詳情面板
- 完全本地執行，預設使用**模擬資料**；沒有連接 CEAA 真實後端

## 需求

- Node.js 18+（本專案固定使用 Vite 5.4；若升級到 Vite 7，需 Node.js 20.19+ 或 22.12+）
- 可使用 WebGL 的瀏覽器

## 啟動

```bash
npm install
npm run dev
```

在終端機顯示的本機網址開啟網頁，通常是 `http://localhost:5173`。

## 專案結構

- `src/data.js`：模擬 Agent 與有向流動路徑的資料，以及模擬事件流
- `src/Constellation.jsx`：Three.js 粒子、節點、曲線與動畫
- `src/App.jsx`：React Dashboard、選擇節點、事件處理（模擬 / WebSocket）
- `src/style.css`：深色科技風介面
- `server/mock_ws.py`：本機測試用的 FastAPI WebSocket 事件來源

## 接入現有 CEAA 平台

`src/App.jsx` 已內建兩種事件來源，共用同一個 `handleEvent`：

- 未設定 `VITE_EVENTS_WS`：用 `setInterval` 產生模擬事件
- 設定 `VITE_EVENTS_WS`：改用 WebSocket（斷線 3 秒自動重連）

本機試接 WebSocket：

```bash
pip install fastapi uvicorn
cd server && uvicorn mock_ws:app --port 8000
# 另一個終端機，在專案根目錄：
cp .env.example .env.local
npm run dev
```

核心寫法：

```jsx
useEffect(() => {
  const ws = new WebSocket('ws://localhost:8000/ws/events')
  ws.onmessage = (event) => {
    const payload = JSON.parse(event.data)
    // 依 payload.type 更新 events / agents / edges / metrics
  }
  return () => ws.close()
}, [])
```

建議事件 schema：

```json
{
  "event_id": "evt-123",
  "ts": "2026-11-11T13:06:00+08:00",
  "type": "task.delegated",
  "source_agent": "main",
  "target_agent": "decision",
  "task_id": "task-73",
  "state": "running",
  "metadata": { "tokens": 1840, "latency_ms": 230 }
}
```

目前會觸發光點動畫的 `type`：`task.delegated`（藍）、`task.completed`（青）、`task.failed`（紅）。
`source_agent` / `target_agent` 必須對應 `src/data.js` 中 `AGENTS` 的 `id`，且兩者之間要有 `EDGES` 路徑（正反方向皆可）。

將執行事件與畫面粒子路徑分離：**Agent 真正執行一次事件，前端才觸發一次動畫**，避免持續動畫被誤認為實際業務流量。建議從 PostgreSQL/事件匯流層訂閱事件，經 FastAPI WebSocket 推送到前端；不要把 Three.js 每一幀直接連接至資料庫。

## 效能

- 一般粒子用 `BufferGeometry` / `Points` 批次呈現，不要為數千粒子建立數千個 React Mesh。
- `useFrame` 內更新 Three.js object ref，不要每秒呼叫 React `setState` 60 次。
- **事件批次更新**：事件先進 buffer，每 250ms 以一批寫入 reducer。不論後端每秒推幾筆，React 每秒最多 render 4 次；「事件／分鐘」用每秒一桶計數，記憶體不會隨事件量成長。
- **光點合併**：光點動畫仍然即時觸發，但同一路徑、同方向、同類型的事件，若前一顆光點才走不到 18%，就合併成一顆較大、較亮的光點，不會塞爆 48 顆的物件池。
- **閒置零成本**：`InstancedMesh` 只更新正在移動的光點，顏色只在發射或合併時寫入一次；沒有光點時每幀幾乎不做事。
- **自適應畫質**：drei `PerformanceMonitor` 偵測掉幀時，先把 DPR 每次降 0.25（最低 1），再關閉 Bloom；回穩後依相反順序恢復。目前狀態顯示在場景左下角。手機版 DPR 上限 1.5、Bloom mip 層數 5、粒子數 45%、粒子尺寸 80%。
- **標籤**：Agent 數量超過 16 個時，只顯示選取、相鄰與滑鼠滑過節點的 HTML 標籤，避免大量 DOM 每幀更新。節點、路徑、粒子元件都以 `memo` 包住，批次更新時不會重建。
- 真正的 GPU 渲染需要支援 WebGL 的顯示裝置；不要求 NVIDIA 顯卡。

### 壓力測試

模擬模式下在網址加上 `?rate=200`（每秒 200 筆，上限 1000）或 `#stress`（每秒 200 筆）：

```
http://localhost:5173/?rate=300
```

## 參考

- https://r3f.docs.pmnd.rs/
- https://drei.docs.pmnd.rs/
- https://react-postprocessing.docs.pmnd.rs/effects/bloom
- https://fastapi.tiangolo.com/advanced/websockets/
