# CEAA · Agent Constellation (demo)

以 React + React Three Fiber + Three.js 建立的動態 Agent 監控介面，包含：

- 3D 粒子群、發光 Agent 節點、弧線和沿路徑移動的光點
- 可拖曳/縮放場景、節點點選、旋轉控制
- 上方 KPI、底部事件流和 Agent 詳情面板
- 完全本地執行，使用**模擬資料**；沒有連接 CEAA 真實後端

## 需求

- Node.js 20.19+ 或 22.12+（Vite 需求依你安裝版本而定）
- 可使用 WebGL 的瀏覽器

## 啟動

```bash
npm install
npm run dev
```

在終端機顯示的本機網址開啟網頁，通常是 `http://localhost:5173`。

## 專案結構

- `src/data.js`：模擬 Agent 與有向流動路徑的資料
- `src/Constellation.jsx`：Three.js 粒子、節點、曲線與動畫
- `src/App.jsx`：React Dashboard、選擇節點與模擬事件
- `src/style.css`：深色科技風介面

## 接入現有 CEAA 平台

目前 `src/App.jsx` 的 `setInterval` 用來模擬事件。正式接入時，改為 WebSocket：

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

將執行事件與畫面粒子路徑分離：**Agent 真正執行一次事件，前端才觸發一次動畫**，避免持續動畫被誤認為實際業務流量。建議從 PostgreSQL/事件匯流層訂閱事件，經 FastAPI WebSocket 推送到前端；不要把 Three.js 每一幀直接連接至資料庫。

## 效能

- 一般粒子用 `BufferGeometry` / `Points` 批次呈現，不要為數千粒子建立數千個 React Mesh。
- `useFrame` 內更新 Three.js object ref，不要每秒呼叫 React `setState` 60 次。
- Agent 數量增加時使用 instancing、篩選、分群與 LOD，並降低手機版粒子數。
- 真正的 GPU 渲染需要支援 WebGL 的顯示裝置；不要求 NVIDIA 顯卡。

## 參考

- https://r3f.docs.pmnd.rs/
- https://drei.docs.pmnd.rs/
- https://react-postprocessing.docs.pmnd.rs/effects/bloom
- https://fastapi.tiangolo.com/advanced/websockets/
