export const AGENTS = [
  { id: 'main', name: 'MAIN AGENT', detail: 'Orchestration & goal management', position: [-0.3, 0.05, 0.4], size: 0.30, status: 'running', color: '#fdf0e5', tasks: 12 },
  { id: 'decision', name: 'DECISION', detail: 'Policy, confidence & action selection', position: [2.45, 1.65, -0.6], size: 0.22, status: 'running', color: '#d8eaff', tasks: 7 },
  { id: 'memory', name: 'MEMORY ROUTER', detail: 'Retrieval & execution history', position: [3.55, -1.10, -0.6], size: 0.22, status: 'running', color: '#d8eaff', tasks: 5 },
  { id: 'skills', name: 'SKILL TREE', detail: 'Reusable capabilities', position: [-3.40, 1.65, -0.6], size: 0.25, status: 'running', color: '#b4d5ff', tasks: 9 },
  { id: 'evolution', name: 'EVOLUTION QUEUE', detail: 'Skill improvement candidates', position: [-3.25, -1.55, -0.5], size: 0.25, status: 'review', color: '#ffb6a1', tasks: 4 },
  { id: 'audit', name: 'AUDIT', detail: 'Testing, evidence & approval', position: [0.60, -2.65, -0.6], size: 0.23, status: 'review', color: '#ffb6a1', tasks: 3 },
  { id: 'tools', name: 'TOOLKIT', detail: 'Tools & environment interfaces', position: [-0.3, 2.75, -1.1], size: 0.19, status: 'idle', color: '#a7caff', tasks: 1 },
]

export const LINKS = [
  ['main', 'decision'], ['main', 'memory'], ['main', 'skills'],
  ['skills', 'evolution'], ['evolution', 'audit'], ['audit', 'main'],
  ['decision', 'tools'], ['decision', 'memory'],
]

export const INITIAL_EVENTS = [
  { type: 'EVOLVE', text: 'skill proposal queued for review', when: 'JUST NOW' },
  { type: 'AUDIT', text: 'regression suite passed · 14 checks', when: '00:14 AGO' },
  { type: 'ROUTE', text: 'Memory Router reused prior path', when: '00:28 AGO' },
  { type: 'TASK', text: 'Decision Agent delegated 3 subtasks', when: '00:46 AGO' },
]
