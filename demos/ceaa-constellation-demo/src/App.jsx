import { useEffect, useMemo, useState } from 'react'
import Scene from './Constellation'
import { AGENTS, INITIAL_EVENTS } from './data'
import './style.css'

const EVENT_CYCLE = [
  { type: 'ROUTE', text: 'historical plan retrieved from memory' },
  { type: 'TASK', text: 'specialized agent accepted new task' },
  { type: 'AUDIT', text: 'skill validation report generated' },
  { type: 'EVOLVE', text: 'capability candidate added to queue' },
]

function Metric({ label, value, sub, highlight }) {
  return (
    <div className="metric">
      <div className="metric__label">{label}</div>
      <div className={'metric__value ' + (highlight ? 'metric__value--warm' : '')}>{value}</div>
      <div className="metric__sub">{sub}</div>
    </div>
  )
}

function SmallBars() {
  return (
    <div className="bars" aria-hidden="true">
      {Array.from({ length: 29 }, (_, i) => {
        const height = 15 + Math.abs(Math.sin(i * 0.7) * 30 + Math.cos(i * 0.3) * 21)
        return <span key={i} style={{ height: `${height}px`, opacity: 0.35 + 0.65 * (i / 29) }} />
      })}
    </div>
  )
}

export default function App() {
  const [selectedId, setSelectedId] = useState('main')
  const [autoRotate, setAutoRotate] = useState(false)
  const [events, setEvents] = useState(INITIAL_EVENTS)
  const [ticks, setTicks] = useState(0)
  const selected = useMemo(() => AGENTS.find((item) => item.id === selectedId), [selectedId])

  // This is DEMO traffic. Replace with actual WebSocket events when connecting CEAA.
  useEffect(() => {
    const timer = window.setInterval(() => {
      setTicks((n) => n + 1)
      setEvents((items) => [{ ...EVENT_CYCLE[Math.floor(Math.random() * EVENT_CYCLE.length)], when: 'JUST NOW' }, ...items].slice(0, 5))
    }, 4200)
    return () => window.clearInterval(timer)
  }, [])

  return (
    <div className="app">
      <div className="backdrop-grid" />
      <div className="visual"><Scene selectedId={selectedId} onSelect={setSelectedId} autoRotate={autoRotate} /></div>
      <header className="header">
        <div className="brand"><span className="brand__icon">✦</span> CEAA <span className="brand__slash">/</span> LIVE OPERATIONS</div>
        <span className="demo-tag"><i /> DEMO DATA</span>
        <div className="header__right">CAPABILITY-EVOLVING AGENT ARCHITECTURE <span>v1.9</span></div>
      </header>
      <section className="metrics" aria-label="Summary indicators">
        <Metric label="AGENTS LIVE" value="07" sub="operational graph" />
        <Metric label="TASKS ACTIVE" value={String(24 + (ticks % 5)).padStart(2, '0')} sub="across all agents" />
        <Metric label="SKILLS AVAILABLE" value="062" sub="reusable capabilities" />
        <Metric label="EVOLUTION QUEUE" value="04" sub="awaiting validation" highlight />
      </section>
      <div className="scene-title">AGENT CONSTELLATION <span>·</span> LIVE TASK FLOWS</div>
      <aside className="float-actions">
        <button onClick={() => setAutoRotate((value) => !value)} title="Toggle automatic rotation">{autoRotate ? '■' : '↻'} <span>{autoRotate ? 'STOP' : 'ROTATE'}</span></button>
        <button onClick={() => setSelectedId('main')} title="Select main agent">◎ <span>MAIN</span></button>
      </aside>
      <div className="dashboard">
        <div className="section-head"><span>01 / TELEMETRY & EVENTS</span><span>SIMULATED STREAM · REFRESHING</span></div>
        <div className="dashboard-grid">
          <section className="panel events-panel">
            <h2>SESSION LOG <small>RECENT EVENTS</small></h2>
            <ul className="events">
              {events.map((event, index) => (
                <li key={`${ticks}-${index}`}><b className={`event-${event.type.toLowerCase()}`}>{event.type}</b><span>{event.text}</span><small>{event.when}</small></li>
              ))}
            </ul>
          </section>
          <section className="panel details-panel">
            <h2>SELECTED NODE <small>CLICK ANY GLOWING NODE</small></h2>
            <div className="selected-name"><span className="selected-dot" />{selected.name}</div>
            <div className="selected-description">{selected.detail}</div>
            <div className="detail-pair"><span>Current state</span><b>{selected.status.toUpperCase()}</b></div>
            <div className="detail-pair"><span>Tracked tasks</span><b>{String(selected.tasks).padStart(2, '0')}</b></div>
          </section>
          <section className="panel throughput-panel">
            <h2>THROUGHPUT <small>VISUAL DEMO</small></h2>
            <div className="graph-meta"><span>DELEGATIONS</span><strong>↑ 14.8%</strong></div>
            <SmallBars />
            <div className="graph-footer"><span>00:00</span><span>AGENT ACTIVITY</span><span>LIVE</span></div>
          </section>
        </div>
        <footer className="footer">
          <span>◉ 7 AGENTS CONNECTED</span><span>8 PATHWAYS</span><span>NO BACKEND CONNECTED</span><span>WEBGL SCENE / REACT HUD</span>
        </footer>
      </div>
    </div>
  )
}
