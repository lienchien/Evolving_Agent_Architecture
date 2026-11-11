// 模擬資料：Agent、有向流動路徑，以及符合 README 事件 schema 的模擬事件流。
// 正式接入時，只需保留 AGENTS / EDGES（或改由後端提供），事件改從 WebSocket 進來。

export const AGENTS = [
  { id: 'main', name: 'Main', role: '協調者：接收需求、分派任務、彙整結果', pos: [0, 0, 0], color: '#ffd27a', size: 1.15 },
  { id: 'planner', name: 'Planner', role: '把需求拆成步驟並排序', pos: [-6.5, 2.6, -2], color: '#9cc2ff', size: 0.9 },
  { id: 'decision', name: 'Decision', role: '比較選項、依規則做決策', pos: [6, 3.2, -1.5], color: '#9cc2ff', size: 0.95 },
  { id: 'retrieval', name: 'Retrieval', role: '查詢資料庫、文件與歷史紀錄', pos: [-7.5, -3.2, 2.5], color: '#7fe0d2', size: 0.85 },
  { id: 'executor', name: 'Executor', role: '呼叫工具、執行實際動作', pos: [6.8, -2.8, 2.8], color: '#7fe0d2', size: 0.9 },
  { id: 'verifier', name: 'Verifier', role: '檢查輸出是否符合規則與資料', pos: [1.2, -6, -3], color: '#c7a6ff', size: 0.8 },
  { id: 'monitor', name: 'Monitor', role: '監看系統狀態並觸發告警', pos: [-2.2, 6, 3.2], color: '#c7a6ff', size: 0.75 },
  { id: 'reporter', name: 'Reporter', role: '產生報告與通知', pos: [10, 0.8, -5.5], color: '#9cc2ff', size: 0.75 },
]

// [source, target]：任務分派方向。完成／失敗事件會沿同一條路徑反向回傳。
export const EDGES = [
  ['main', 'planner'],
  ['main', 'decision'],
  ['planner', 'retrieval'],
  ['planner', 'executor'],
  ['retrieval', 'decision'],
  ['decision', 'executor'],
  ['executor', 'verifier'],
  ['verifier', 'main'],
  ['verifier', 'reporter'],
  ['decision', 'reporter'],
  ['monitor', 'main'],
  ['monitor', 'executor'],
]

const rand = (a, b) => a + Math.random() * (b - a)

// 回傳一個 next() 函式，每次呼叫產生一筆事件。
// 會記住進行中的任務，讓 completed / failed 對應到先前真的被分派過的 task。
export function createMockStream() {
  const running = []
  let seq = 1000
  let task = 70

  const make = (type, source, target, taskId, state) => ({
    event_id: `evt-${++seq}`,
    ts: new Date().toISOString(),
    type,
    source_agent: source,
    target_agent: target,
    task_id: taskId,
    state,
    metadata: {
      tokens: Math.round(rand(220, 4200)),
      latency_ms: Math.round(type === 'task.delegated' ? rand(40, 260) : rand(180, 1400)),
    },
  })

  return function next() {
    if (running.length && (Math.random() < 0.45 || running.length > 9)) {
      const job = running.splice(Math.floor(Math.random() * running.length), 1)[0]
      const failed = Math.random() < 0.09
      return make(failed ? 'task.failed' : 'task.completed', job.target, job.source, job.taskId, failed ? 'failed' : 'done')
    }
    const [source, target] = EDGES[Math.floor(Math.random() * EDGES.length)]
    const taskId = `task-${++task}`
    running.push({ taskId, source, target })
    return make('task.delegated', source, target, taskId, 'running')
  }
}
