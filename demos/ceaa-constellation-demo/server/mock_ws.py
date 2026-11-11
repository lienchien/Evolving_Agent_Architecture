"""本機測試用的 FastAPI WebSocket 模擬事件來源。

    pip install fastapi uvicorn
    cd server && uvicorn mock_ws:app --port 8000

接著在專案根目錄建立 .env.local：
    VITE_EVENTS_WS=ws://localhost:8000/ws/events
再重新執行 npm run dev。正式環境請改成從 PostgreSQL / 事件匯流層訂閱真實事件。
"""
import asyncio
import itertools
import json
import random
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()
TZ = timezone(timedelta(hours=8))
EDGES = [
    ("main", "planner"), ("main", "decision"), ("planner", "retrieval"),
    ("planner", "executor"), ("retrieval", "decision"), ("decision", "executor"),
    ("executor", "verifier"), ("verifier", "main"), ("verifier", "reporter"),
    ("decision", "reporter"), ("monitor", "main"), ("monitor", "executor"),
]


@app.websocket("/ws/events")
async def events(ws: WebSocket):
    await ws.accept()
    seq = itertools.count(1000)
    task = itertools.count(70)
    running = []
    try:
        while True:
            if running and (random.random() < 0.45 or len(running) > 9):
                task_id, src, tgt = running.pop(random.randrange(len(running)))
                failed = random.random() < 0.09
                ev_type, state, src, tgt = (
                    ("task.failed", "failed", tgt, src) if failed else ("task.completed", "done", tgt, src)
                )
            else:
                src, tgt = random.choice(EDGES)
                task_id = f"task-{next(task)}"
                running.append((task_id, src, tgt))
                ev_type, state = "task.delegated", "running"
            await ws.send_text(json.dumps({
                "event_id": f"evt-{next(seq)}",
                "ts": datetime.now(TZ).isoformat(timespec="seconds"),
                "type": ev_type,
                "source_agent": src,
                "target_agent": tgt,
                "task_id": task_id,
                "state": state,
                "metadata": {"tokens": random.randint(220, 4200), "latency_ms": random.randint(40, 1400)},
            }))
            await asyncio.sleep(random.uniform(0.4, 1.1))
    except WebSocketDisconnect:
        pass
