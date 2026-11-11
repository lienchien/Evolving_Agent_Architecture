import { useCallback, useEffect, useMemo, useReducer, useRef, useState } from 'react'
import Constellation, { KIND_COLOR } from './Constellation.jsx'
import { AGENTS, EDGES, createMockStream } from './data.js'

// 設定 VITE_EVENTS_WS（見 .env.example）就改用 WebSocket；留空則使用模擬資料。
const WS_URL = import.meta.env.VITE_EVENTS_WS || ''
// 模擬事件速率（筆/秒）。網址加 ?rate=200（或 #stress）可做壓力測試。
const MOCK_RATE = Math.min(1000, Math.max(0.2, Number(new URLSearchParams(window.location.search).get('rate')) || (window.location.hash === '#stress' ? 200 : 1.4)))
const ANIMATED = new Set(['task.delegated', 'task.completed', 'task.failed'])
const AGENT_BY_ID = Object.fromEntries(AGENTS.map((a) => [a.id, a]))
const nameOf = (id) => AGENT_BY_ID[id]?.name ?? id ?? '—'

const TYPE_LABEL = {
  'task.delegated': '分派',
  'task.completed': '完成',
  'task.failed': '失敗',
}

const FLUSH_MS = 250 // 事件先進 buffer，每 250ms 批次更新一次 React state
const MAX_FEED = 120

// rate：每秒一個 [秒, 筆數] 桶，只保留最近 60 秒，事件量再大也不會無限成長
const initial = { events: [], running: {}, stats: {}, totals: { tokens: 0, lat: 0, n: 0 }, rate: [] }

// 一次處理一整批事件（舊 → 新）。所有統計都從事件推導，WebSocket 與模擬資料共用。
function reducer(state, batch) {
  const running = { ...state.running }
  const stats = { ...state.stats }
  const touched = new Set()
  const get = (id) => {
    if (!touched.has(id)) {
      stats[id] = { sent: 0, received: 0, done: 0, failed: 0, tokens: 0, lat: 0, n: 0, last: null, ...stats[id] }
      touched.add(id)
    }
    return stats[id]
  }
  let { tokens, lat, n } = state.totals

  for (const ev of batch) {
    if (ev.state === 'running') running[ev.task_id] = { source: ev.source_agent, target: ev.target_agent }
    else if (ev.task_id) delete running[ev.task_id]

    const tk = ev.metadata?.tokens ?? 0
    const l = ev.metadata?.latency_ms
    tokens += tk
    if (l != null) {
      lat += l
      n++
    }
    if (ev.source_agent) {
      const s = get(ev.source_agent)
      s.sent++
      s.last = ev.ts
      if (ev.type === 'task.completed') s.done++
      if (ev.type === 'task.failed') s.failed++
      s.tokens += tk
      if (l != null) {
        s.lat += l
        s.n++
      }
    }
    if (ev.target_agent) {
      const s = get(ev.target_agent)
      s.received++
      s.last = ev.ts
    }
  }

  const sec = Math.floor(Date.now() / 1000)
  const rate = state.rate.filter(([t]) => sec - t < 60)
  const lastBucket = rate[rate.length - 1]
  if (lastBucket && lastBucket[0] === sec) rate[rate.length - 1] = [sec, lastBucket[1] + batch.length]
  else rate.push([sec, batch.length])

  const newest = batch.length > MAX_FEED ? batch.slice(-MAX_FEED) : batch
  return {
    events: [...newest].reverse().concat(state.events).slice(0, MAX_FEED),
    running,
    stats,
    totals: { tokens, lat, n },
    rate,
  }
}

const fmtK = (n) => (n >= 1e6 ? `${(n / 1e6).toFixed(2)}M` : n >= 1e3 ? `${(n / 1e3).toFixed(1)}k` : `${n}`)
const fmtTime = (ts) => new Date(ts).toLocaleTimeString('zh-TW', { hour12: false })

export default function App() {
  const [state, dispatch] = useReducer(reducer, initial)
  const [selected, setSelected] = useState(null)
  const [autoRotate, setAutoRotate] = useState(true)
  const [paused, setPaused] = useState(false)
  const [conn, setConn] = useState(WS_URL ? 'connecting' : 'mock')
  const [, setClock] = useState(0)
  const [perf, setPerf] = useState(null)
  const scene = useRef()
  const bufferRef = useRef([])
  const pausedRef = useRef(paused)
  pausedRef.current = paused
  const streamRef = useRef(null)
  if (!streamRef.current) streamRef.current = createMockStream()
  const quality = useMemo(() => (window.innerWidth < 700 ? 0.45 : 1), [])

  const handleEvent = useCallback((ev) => {
    if (!ev?.type) return
    bufferRef.current.push(ev)
    // Agent 真的執行一次事件，前端才觸發一次動畫
    if (ANIMATED.has(ev.type) && ev.source_agent && ev.target_agent) {
      scene.current?.fire(ev.source_agent, ev.target_agent, ev.type)
    }
  }, [])

  // 批次把 buffer 寫進 state：事件量再大，React 每秒最多 render 4 次
  useEffect(() => {
    const id = setInterval(() => {
      if (!bufferRef.current.length) return
      const batch = bufferRef.current
      bufferRef.current = []
      dispatch(batch)
    }, FLUSH_MS)
    return () => clearInterval(id)
  }, [])

  // 正式資料：WebSocket（斷線 3 秒後重連）
  useEffect(() => {
    if (!WS_URL) return
    let ws
    let retry
    let closed = false
    const open = () => {
      setConn('connecting')
      ws = new WebSocket(WS_URL)
      ws.onopen = () => setConn('live')
      ws.onmessage = (e) => {
        if (pausedRef.current) return
        try {
          handleEvent(JSON.parse(e.data))
        } catch (err) {
          console.warn('無法解析事件', err)
        }
      }
      ws.onclose = () => {
        if (closed) return
        setConn('offline')
        retry = setTimeout(open, 3000)
      }
    }
    open()
    return () => {
      closed = true
      clearTimeout(retry)
      ws?.close()
    }
  }, [handleEvent])

  // 模擬資料
  useEffect(() => {
    if (WS_URL || paused) return
    // 每 100ms 依 MOCK_RATE 產生對應數量的事件（小數部分累積到下一輪）
    let carry = 0
    const id = setInterval(() => {
      carry += MOCK_RATE / 10
      while (carry >= 1) {
        handleEvent(streamRef.current())
        carry--
      }
    }, 100)
    return () => clearInterval(id)
  }, [paused, handleEvent])

  // 讓「事件 / 分鐘」在沒有新事件時也會往下掉
  useEffect(() => {
    const id = setInterval(() => setClock((c) => c + 1), 5000)
    return () => clearInterval(id)
  }, [])

  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && setSelected(null)
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  const busy = useMemo(() => {
    const m = {}
    for (const r of Object.values(state.running)) m[r.target] = (m[r.target] || 0) + 1
    return m
  }, [state.running])

  const now = Date.now()
  const activeCount = AGENTS.filter((a) => busy[a.id] || (state.stats[a.id]?.last && now - Date.parse(state.stats[a.id].last) < 15000)).length
  const runningCount = Object.keys(state.running).length
  const nowSec = Math.floor(now / 1000)
  const perMin = state.rate.reduce((sum, [t, c]) => (nowSec - t < 60 ? sum + c : sum), 0)
  const avgLat = state.totals.n ? Math.round(state.totals.lat / state.totals.n) : 0

  const connLabel = { mock: '模擬資料', connecting: '連線中', live: '即時連線', offline: '已斷線，重試中' }[conn]

  return (
    <div className="app">
      <header className="top">
        <div className="brand">
          <h1>CEAA · Agent Constellation</h1>
          <p>
            <span className={`conn conn-${conn}`} aria-hidden="true" />
            {connLabel}
            {paused && ' · 已暫停'}
          </p>
        </div>
        <dl className="kpis">
          <div>
            <dt>活躍 Agent</dt>
            <dd>
              {activeCount}
              <small>/{AGENTS.length}</small>
            </dd>
          </div>
          <div>
            <dt>進行中任務</dt>
            <dd>{runningCount}</dd>
          </div>
          <div>
            <dt>事件 / 分鐘</dt>
            <dd>{perMin}</dd>
          </div>
          <div>
            <dt>平均延遲</dt>
            <dd>
              {avgLat}
              <small> ms</small>
            </dd>
          </div>
          <div>
            <dt>Tokens</dt>
            <dd>{fmtK(state.totals.tokens)}</dd>
          </div>
        </dl>
        <div className="controls">
          <button type="button" aria-pressed={autoRotate} onClick={() => setAutoRotate((v) => !v)}>
            自動旋轉
          </button>
          <button type="button" aria-pressed={paused} onClick={() => setPaused((v) => !v)}>
            {paused ? '繼續事件' : '暫停事件'}
          </button>
          <button type="button" onClick={() => scene.current?.resetView()}>
            重設視角
          </button>
        </div>
      </header>

      <main className="main">
        <section className="stage" aria-label="Agent 星圖">
          <Constellation
            ref={scene}
            agents={AGENTS}
            edges={EDGES}
            selected={selected}
            onSelect={setSelected}
            busy={busy}
            autoRotate={autoRotate}
            quality={quality}
            onPerf={setPerf}
          />
          <div className="legend">
            {Object.entries(TYPE_LABEL).map(([k, v]) => (
              <span key={k}>
                <i style={{ background: KIND_COLOR[k] }} />
                {v}
              </span>
            ))}
            {perf && (
              <span className="perf">
                畫質 {perf.dpr}x{perf.bloom ? '' : ' · 光暈關閉'}
              </span>
            )}
            <span className="hint">拖曳旋轉 · 滾輪縮放 · 點選節點看詳情</span>
          </div>
        </section>

        <aside className="side">
          <AgentPanel
            agent={selected ? AGENT_BY_ID[selected] : null}
            stats={state.stats}
            busy={busy}
            events={state.events}
            onSelect={setSelected}
          />
        </aside>
      </main>

      <section className="feed" aria-label="事件流">
        <div className="feed-head">
          <h2>事件流</h2>
          <span>最近 {state.events.length} 筆</span>
        </div>
        <div className="feed-scroll">
          <table>
            <thead>
              <tr>
                <th>時間</th>
                <th>類型</th>
                <th>路徑</th>
                <th>任務</th>
                <th>狀態</th>
                <th className="num">Tokens</th>
                <th className="num">延遲</th>
              </tr>
            </thead>
            <tbody>
              {state.events.slice(0, 60).map((e) => (
                <tr
                  key={e.event_id}
                  className={selected && (e.source_agent === selected || e.target_agent === selected) ? 'hl' : ''}
                >
                  <td>{fmtTime(e.ts)}</td>
                  <td>
                    <span className="tag" style={{ '--c': KIND_COLOR[e.type] ?? '#8a96ad' }}>
                      {TYPE_LABEL[e.type] ?? e.type}
                    </span>
                  </td>
                  <td>
                    <button type="button" className="link" onClick={() => setSelected(e.source_agent)}>
                      {nameOf(e.source_agent)}
                    </button>
                    <span className="arrow">→</span>
                    <button type="button" className="link" onClick={() => setSelected(e.target_agent)}>
                      {nameOf(e.target_agent)}
                    </button>
                  </td>
                  <td className="muted">{e.task_id}</td>
                  <td className={`state state-${e.state}`}>{e.state}</td>
                  <td className="num">{e.metadata?.tokens ?? '—'}</td>
                  <td className="num">{e.metadata?.latency_ms != null ? `${e.metadata.latency_ms} ms` : '—'}</td>
                </tr>
              ))}
              {!state.events.length && (
                <tr>
                  <td colSpan={7} className="muted empty">
                    {WS_URL ? '等待後端推送事件…' : '模擬事件即將開始…'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}

function AgentPanel({ agent, stats, busy, events, onSelect }) {
  if (!agent) {
    return (
      <div className="panel">
        <h2>Agents</h2>
        <p className="muted">點選場景中的節點，或從下方選擇。</p>
        <ul className="agent-list">
          {AGENTS.map((a) => (
            <li key={a.id}>
              <button type="button" onClick={() => onSelect(a.id)}>
                <i style={{ background: a.color }} />
                <span>{a.name}</span>
                <em>{busy[a.id] ? `${busy[a.id]} 執行中` : '待命'}</em>
              </button>
            </li>
          ))}
        </ul>
      </div>
    )
  }

  const s = stats[agent.id] ?? {}
  const inbound = EDGES.filter(([, t]) => t === agent.id).map(([x]) => x)
  const outbound = EDGES.filter(([x]) => x === agent.id).map(([, t]) => t)
  const recent = events.filter((e) => e.source_agent === agent.id || e.target_agent === agent.id).slice(0, 8)
  const finished = (s.done ?? 0) + (s.failed ?? 0)

  return (
    <div className="panel">
      <div className="panel-head">
        <h2>
          <i style={{ background: agent.color }} />
          {agent.name}
        </h2>
        <button type="button" className="close" onClick={() => onSelect(null)} aria-label="關閉詳情">
          ✕
        </button>
      </div>
      <p className="muted">{agent.role}</p>
      <p className={`status ${busy[agent.id] ? 'is-busy' : ''}`}>{busy[agent.id] ? `${busy[agent.id]} 個任務執行中` : '待命中'}</p>

      <dl className="stats">
        <div>
          <dt>收到任務</dt>
          <dd>{s.received ?? 0}</dd>
        </div>
        <div>
          <dt>送出事件</dt>
          <dd>{s.sent ?? 0}</dd>
        </div>
        <div>
          <dt>完成</dt>
          <dd>{s.done ?? 0}</dd>
        </div>
        <div>
          <dt>失敗</dt>
          <dd className={s.failed ? 'bad' : ''}>{s.failed ?? 0}</dd>
        </div>
        <div>
          <dt>成功率</dt>
          <dd>{finished ? `${Math.round(((s.done ?? 0) / finished) * 100)}%` : '—'}</dd>
        </div>
        <div>
          <dt>平均延遲</dt>
          <dd>{s.n ? `${Math.round(s.lat / s.n)} ms` : '—'}</dd>
        </div>
        <div>
          <dt>Tokens</dt>
          <dd>{fmtK(s.tokens ?? 0)}</dd>
        </div>
        <div>
          <dt>最後活動</dt>
          <dd>{s.last ? fmtTime(s.last) : '—'}</dd>
        </div>
      </dl>

      <h3>連線</h3>
      <div className="links">
        <div>
          <span className="muted">接收自</span>
          {inbound.length ? inbound.map((id) => <Chip key={id} id={id} onSelect={onSelect} />) : <span className="muted">—</span>}
        </div>
        <div>
          <span className="muted">分派給</span>
          {outbound.length ? outbound.map((id) => <Chip key={id} id={id} onSelect={onSelect} />) : <span className="muted">—</span>}
        </div>
      </div>

      <h3>最近事件</h3>
      <ul className="mini-feed">
        {recent.map((e) => (
          <li key={e.event_id}>
            <span className="tag" style={{ '--c': KIND_COLOR[e.type] ?? '#8a96ad' }}>
              {TYPE_LABEL[e.type] ?? e.type}
            </span>
            <span>
              {nameOf(e.source_agent)} → {nameOf(e.target_agent)}
            </span>
            <span className="muted">{fmtTime(e.ts)}</span>
          </li>
        ))}
        {!recent.length && <li className="muted">尚無事件</li>}
      </ul>
    </div>
  )
}

function Chip({ id, onSelect }) {
  return (
    <button type="button" className="chip" onClick={() => onSelect(id)}>
      <i style={{ background: AGENT_BY_ID[id]?.color }} />
      {nameOf(id)}
    </button>
  )
}
