import { forwardRef, memo, useEffect, useImperativeHandle, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Html, Line, OrbitControls, PerformanceMonitor } from '@react-three/drei'
import { Bloom, EffectComposer } from '@react-three/postprocessing'
import * as THREE from 'three'

export const KIND_COLOR = {
  'task.delegated': '#9cc2ff',
  'task.completed': '#7fe0d2',
  'task.failed': '#ff6b5a',
}

const MAX_PULSES = 48 // 同時在路徑上移動的光點上限
const TRAIL = 7 // 每個光點的拖尾長度（instance 數）
const MERGE_WINDOW = 0.18 // 同一路徑、同方向、同類型的事件，若前一顆光點才走不到 18%，就合併成一顆
const LABEL_LIMIT = 16 // Agent 數量超過此值時，只顯示選取／相鄰／滑過節點的標籤

const gauss = () => {
  let u = 0
  let v = 0
  while (!u) u = Math.random()
  while (!v) v = Math.random()
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v)
}

/* ---------------- 曲線 ---------------- */

function buildCurves(agents, edges) {
  const pos = Object.fromEntries(agents.map((a) => [a.id, new THREE.Vector3(...a.pos)]))
  const up = new THREE.Vector3(0, 1, 0)
  const map = new Map()
  for (const [s, t] of edges) {
    const a = pos[s]
    const b = pos[t]
    if (!a || !b) continue
    const dir = b.clone().sub(a)
    const len = dir.length()
    const side = new THREE.Vector3().crossVectors(dir, up)
    if (side.lengthSq() < 1e-4) side.set(1, 0, 0)
    side.normalize()
    const mid = a.clone().add(b).multiplyScalar(0.5).addScaledVector(side, len * 0.18).addScaledVector(up, len * 0.12)
    const curve = new THREE.QuadraticBezierCurve3(a, mid, b)
    map.set(`${s}->${t}`, { s, t, curve, points: curve.getPoints(48) })
  }
  return map
}

/* ---------------- 粒子群（單一 BufferGeometry + shader） ---------------- */

const VERT = /* glsl */ `
  uniform float uTime;
  uniform float uPixel;
  uniform float uSel;
  uniform float uSize;
  attribute vec3 aCenter;
  attribute vec3 aColor;
  attribute float aSize;
  attribute float aPhase;
  attribute float aAgent;
  varying vec3 vColor;
  varying float vAlpha;
  void main() {
    vec3 off = position - aCenter;
    float ang = uTime * (0.03 + 0.05 * fract(aPhase * 3.17));
    float c = cos(ang);
    float s = sin(ang);
    off.xz = mat2(c, -s, s, c) * off.xz;
    vec4 mv = modelViewMatrix * vec4(aCenter + off, 1.0);
    gl_Position = projectionMatrix * mv;
    gl_PointSize = aSize * uSize * uPixel * (38.0 / -mv.z);
    float tw = 0.5 + 0.5 * sin(uTime * (0.8 + aPhase * 0.25) + aPhase * 20.0);
    float sel = 1.0;
    if (uSel > -0.5) sel = abs(aAgent - uSel) < 0.5 ? 1.7 : 0.3;
    vAlpha = (0.3 + 0.7 * tw) * sel;
    vColor = aColor;
  }
`

const FRAG = /* glsl */ `
  varying vec3 vColor;
  varying float vAlpha;
  void main() {
    float d = length(gl_PointCoord - 0.5);
    if (d > 0.5) discard;
    float a = smoothstep(0.5, 0.0, d);
    gl_FragColor = vec4(vColor, a * vAlpha);
  }
`

const Particles = memo(function Particles({ agents, quality, selIndex }) {
  const geometry = useMemo(() => {
    const per = Math.round(1500 * quality)
    const dust = Math.round(2600 * quality)
    const counts = agents.map((a) => Math.round(per * (a.size ?? 0.8)))
    const total = counts.reduce((n, c) => n + c, 0) + dust

    const position = new Float32Array(total * 3)
    const center = new Float32Array(total * 3)
    const color = new Float32Array(total * 3)
    const size = new Float32Array(total)
    const phase = new Float32Array(total)
    const agentIdx = new Float32Array(total)

    const white = new THREE.Color('#e3ecff')
    const c = new THREE.Color()
    const off = new THREE.Vector3()
    let i = 0

    const put = (px, py, pz, cx, cy, cz, col, sz, ai) => {
      position.set([px, py, pz], i * 3)
      center.set([cx, cy, cz], i * 3)
      color.set([col.r, col.g, col.b], i * 3)
      size[i] = sz
      phase[i] = Math.random() * 10
      agentIdx[i] = ai
      i++
    }

    agents.forEach((a, ai) => {
      const base = new THREE.Color(a.color)
      const filaments = Array.from({ length: 5 }, () => new THREE.Vector3(gauss(), gauss() * 0.6, gauss()).normalize())
      for (let k = 0; k < counts[ai]; k++) {
        if (Math.random() < 0.55) {
          off.set(gauss() * 0.85, gauss() * 0.6, gauss() * 0.85)
        } else {
          const d = filaments[k % filaments.length]
          const t = Math.pow(Math.random(), 1.5) * 4.4
          const j = 0.12 * (1 + t)
          off.copy(d).multiplyScalar(t).add(new THREE.Vector3(gauss() * j, gauss() * j, gauss() * j))
        }
        c.copy(base).lerp(white, Math.random() * 0.7).multiplyScalar(1 / (1 + off.length() * 0.35))
        const sz = Math.random() < 0.04 ? 2.6 : 0.6 + Math.random() * 1.1
        put(a.pos[0] + off.x, a.pos[1] + off.y, a.pos[2] + off.z, a.pos[0], a.pos[1], a.pos[2], c, sz, ai)
      }
    })

    const dustColor = new THREE.Color('#6f8fc9')
    for (let k = 0; k < dust; k++) {
      const r = 6 + Math.pow(Math.random(), 0.7) * 20
      const th = Math.random() * Math.PI * 2
      const y = gauss() * 3
      c.copy(dustColor).multiplyScalar(0.25 + Math.random() * 0.35)
      put(Math.cos(th) * r, y, Math.sin(th) * r, 0, 0, 0, c, 0.5 + Math.random() * 0.8, -1)
    }

    const g = new THREE.BufferGeometry()
    g.setAttribute('position', new THREE.BufferAttribute(position, 3))
    g.setAttribute('aCenter', new THREE.BufferAttribute(center, 3))
    g.setAttribute('aColor', new THREE.BufferAttribute(color, 3))
    g.setAttribute('aSize', new THREE.BufferAttribute(size, 1))
    g.setAttribute('aPhase', new THREE.BufferAttribute(phase, 1))
    g.setAttribute('aAgent', new THREE.BufferAttribute(agentIdx, 1))
    return g
  }, [agents, quality])

  useEffect(() => () => geometry.dispose(), [geometry])

  const uniforms = useMemo(
    () => ({ uTime: { value: 0 }, uPixel: { value: 1 }, uSel: { value: -1 }, uSize: { value: quality < 1 ? 0.8 : 1 } }),
    [quality],
  )

  // 只改 uniform，不觸發 React re-render
  useFrame((state) => {
    uniforms.uTime.value = state.clock.elapsedTime
    uniforms.uPixel.value = state.gl.getPixelRatio()
    uniforms.uSel.value = selIndex
  })

  return (
    <points geometry={geometry} frustumCulled={false}>
      <shaderMaterial
        uniforms={uniforms}
        vertexShader={VERT}
        fragmentShader={FRAG}
        transparent
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </points>
  )
})

/* ---------------- Agent 節點 ---------------- */

function makeHaloTexture() {
  const s = 128
  const cv = document.createElement('canvas')
  cv.width = cv.height = s
  const ctx = cv.getContext('2d')
  const g = ctx.createRadialGradient(s / 2, s / 2, 0, s / 2, s / 2, s / 2)
  g.addColorStop(0, 'rgba(255,255,255,1)')
  g.addColorStop(0.25, 'rgba(255,255,255,0.35)')
  g.addColorStop(1, 'rgba(255,255,255,0)')
  ctx.fillStyle = g
  ctx.fillRect(0, 0, s, s)
  const tex = new THREE.CanvasTexture(cv)
  tex.colorSpace = THREE.SRGBColorSpace
  return tex
}

const AgentNode = memo(function AgentNode({ agent, selected, dim, busy, flashRef, onSelect, haloTex, labelMode }) {
  const core = useRef()
  const halo = useRef()
  const ring1 = useRef()
  const ring2 = useRef()
  const [hover, setHover] = useState(false)
  const r = 0.32 * (agent.size ?? 0.8)
  const coreColor = useMemo(() => new THREE.Color(agent.color).multiplyScalar(2.4), [agent.color])

  useEffect(() => {
    document.body.style.cursor = hover ? 'pointer' : ''
    return () => {
      document.body.style.cursor = ''
    }
  }, [hover])

  useFrame((_, dt) => {
    const f = flashRef.current[agent.id] || 0
    flashRef.current[agent.id] = Math.max(0, f - dt * 1.5)
    core.current.scale.setScalar(1 + f * 0.5 + (hover || selected ? 0.18 : 0))
    halo.current.scale.setScalar(r * 9 * (1 + f * 0.9))
    halo.current.material.opacity = (dim ? 0.06 : 0.65) + f * 0.35
    ring1.current.rotation.z += dt * 0.4
    ring2.current.rotation.z -= dt * 0.25
  })

  return (
    <group position={agent.pos}>
      <mesh ref={core}>
        <sphereGeometry args={[r, 32, 32]} />
        <meshBasicMaterial color={coreColor} toneMapped={false} transparent opacity={dim ? 0.35 : 1} />
      </mesh>
      {/* 透明的較大球體，放大點選範圍 */}
      <mesh
        onClick={(e) => {
          e.stopPropagation()
          onSelect(agent.id)
        }}
        onPointerOver={(e) => {
          e.stopPropagation()
          setHover(true)
        }}
        onPointerOut={() => setHover(false)}
      >
        <sphereGeometry args={[r * 2.6, 16, 16]} />
        <meshBasicMaterial transparent opacity={0} depthWrite={false} />
      </mesh>
      <sprite ref={halo}>
        <spriteMaterial map={haloTex} color={agent.color} blending={THREE.AdditiveBlending} depthWrite={false} transparent />
      </sprite>
      <group rotation={[1.2, 0.3, 0]}>
        <mesh ref={ring1}>
          <torusGeometry args={[r * 2, 0.012, 6, 96]} />
          <meshBasicMaterial color={agent.color} transparent opacity={selected ? 0.95 : dim ? 0.1 : 0.35} toneMapped={false} />
        </mesh>
      </group>
      <group rotation={[-0.4, 1.1, 0.3]}>
        <mesh ref={ring2}>
          <torusGeometry args={[r * 2.7, 0.008, 6, 96]} />
          <meshBasicMaterial color={agent.color} transparent opacity={selected ? 0.7 : dim ? 0.08 : 0.22} toneMapped={false} />
        </mesh>
      </group>
      {(labelMode === 'all' || selected || hover || labelMode === agent.id) && (
        <Html position={[0, r * 3.4, 0]} center zIndexRange={[20, 0]} style={{ pointerEvents: 'none' }}>
          <div className={`node-label${selected ? ' is-sel' : ''}${dim ? ' is-dim' : ''}`}>
            <b>{agent.name}</b>
            <span>{busy ? `${busy} 執行中` : '待命'}</span>
          </div>
        </Html>
      )}
    </group>
  )
})

/* ---------------- 路徑 ---------------- */

const Edges = memo(function Edges({ curves, selected }) {
  return [...curves.entries()].map(([key, e]) => {
    const on = selected && (e.s === selected || e.t === selected)
    return (
      <Line
        key={key}
        points={e.points}
        color={on ? '#cfe0ff' : '#4a6aa3'}
        lineWidth={on ? 1.4 : 1}
        transparent
        opacity={selected ? (on ? 0.75 : 0.08) : 0.28}
        toneMapped={false}
      />
    )
  })
})

/* ---------------- 事件光點（InstancedMesh 物件池） ---------------- */

const Pulses = forwardRef(function Pulses({ curves, flashRef, glow }, ref) {
  const mesh = useRef()
  // 有 Bloom 時顏色要 >1 才會發光；沒有 Bloom 時 >1 會被截成白色，所以維持原色
  const glowRef = useRef(glow)
  glowRef.current = glow
  const pool = useMemo(
    () =>
      Array.from({ length: MAX_PULSES }, () => ({
        active: false,
        visible: false, // 上一幀是否有畫出來；用來在消失時只清一次
        dirtyColor: false,
        key: '',
        count: 1, // 合併的事件數
        t: 0,
        speed: 0.5,
        curve: null,
        reverse: false,
        target: null,
        color: new THREE.Color(),
      })),
    [],
  )
  const tmp = useMemo(() => ({ obj: new THREE.Object3D(), v: new THREE.Vector3() }), [])
  const colors = useMemo(() => new Float32Array(MAX_PULSES * TRAIL * 3), [])

  // 一開始把全部 instance 縮成 0，之後只更新有在動的光點
  useLayoutEffect(() => {
    const m = mesh.current
    tmp.obj.scale.setScalar(0)
    tmp.obj.updateMatrix()
    for (let i = 0; i < MAX_PULSES * TRAIL; i++) m.setMatrixAt(i, tmp.obj.matrix)
    m.instanceMatrix.needsUpdate = true
  }, [tmp])

  useImperativeHandle(
    ref,
    () => ({
      // 一筆事件 = 一次動畫；短時間內同路徑同類型的事件合併成一顆更亮更大的光點。
      fire(source, target, type) {
        let edgeKey = `${source}->${target}`
        let edge = curves.get(edgeKey)
        let reverse = false
        if (!edge) {
          edgeKey = `${target}->${source}`
          edge = curves.get(edgeKey)
          reverse = true
        }
        if (!edge) return false
        const key = `${edgeKey}|${reverse ? 'r' : 'f'}|${type}`
        flashRef.current[source] = Math.max(flashRef.current[source] || 0, 0.6)

        const merge = pool.find((x) => x.active && x.key === key && x.t < MERGE_WINDOW)
        const base = KIND_COLOR[type] ?? '#ffffff'
        if (merge) {
          merge.count++
          merge.color.set(base).multiplyScalar(glowRef.current ? 1.8 + Math.min(merge.count - 1, 4) * 0.35 : 1)
          merge.dirtyColor = true
          return true
        }
        const p = pool.find((x) => !x.active) ?? pool.reduce((a, b) => (a.t > b.t ? a : b))
        p.active = true
        p.key = key
        p.count = 1
        p.t = 0
        p.speed = 0.45 + Math.random() * 0.25
        p.curve = edge.curve
        p.reverse = reverse
        p.target = target
        p.color.set(base).multiplyScalar(glowRef.current ? 1.8 : 1)
        p.dirtyColor = true
        return true
      },
    }),
    [curves, pool, flashRef],
  )

  useFrame((_, dt) => {
    const m = mesh.current
    if (!m) return
    const { obj, v } = tmp
    let matrixChanged = false
    let colorChanged = false
    for (let pi = 0; pi < pool.length; pi++) {
      const p = pool[pi]
      if (!p.active && !p.visible) continue // 閒置光點完全跳過
      if (p.active) {
        p.t += dt * p.speed
        if (p.t >= 1) {
          p.active = false
          flashRef.current[p.target] = 1
        }
      }
      const base = pi * TRAIL
      if (p.dirtyColor) {
        for (let k = 0; k < TRAIL; k++) m.setColorAt(base + k, p.color)
        p.dirtyColor = false
        colorChanged = true
      }
      const grow = 1 + Math.min(Math.log2(p.count), 3) * 0.22
      for (let k = 0; k < TRAIL; k++) {
        const tt = p.t - k * 0.022
        if (!p.active || tt < 0) {
          obj.scale.setScalar(0)
        } else {
          p.curve.getPoint(p.reverse ? 1 - tt : tt, v)
          obj.position.copy(v)
          obj.scale.setScalar((1 - k / TRAIL) * grow)
        }
        obj.updateMatrix()
        m.setMatrixAt(base + k, obj.matrix)
      }
      p.visible = p.active
      matrixChanged = true
    }
    if (matrixChanged) m.instanceMatrix.needsUpdate = true
    if (colorChanged && m.instanceColor) m.instanceColor.needsUpdate = true
  })

  return (
    <instancedMesh ref={mesh} args={[undefined, undefined, MAX_PULSES * TRAIL]} frustumCulled={false}>
      <sphereGeometry args={[0.085, 10, 10]} />
      <meshBasicMaterial toneMapped={false} />
      <instancedBufferAttribute attach="instanceColor" args={[colors, 3]} />
    </instancedMesh>
  )
})

/* ---------------- 主場景 ---------------- */

const Constellation = forwardRef(function Constellation(
  { agents, edges, selected, onSelect, busy, autoRotate, quality = 1, onPerf },
  ref,
) {
  // 自適應畫質：掉幀時先降 DPR，到 1 之後關閉 Bloom；回穩時反向恢復
  const maxDpr = Math.min(window.devicePixelRatio || 1, quality < 1 ? 1.5 : 2)
  const [dpr, setDpr] = useState(maxDpr)
  const [bloom, setBloom] = useState(true)
  const perf = useRef({ dpr: maxDpr, bloom: true })
  const decline = () => {
    if (perf.current.dpr > 1) perf.current.dpr = Math.max(1, perf.current.dpr - 0.25)
    else perf.current.bloom = false
    setDpr(perf.current.dpr)
    setBloom(perf.current.bloom)
  }
  const incline = () => {
    if (!perf.current.bloom) perf.current.bloom = true
    else perf.current.dpr = Math.min(maxDpr, perf.current.dpr + 0.25)
    setDpr(perf.current.dpr)
    setBloom(perf.current.bloom)
  }
  const fallback = () => {
    perf.current = { dpr: 1, bloom: false }
    setDpr(1)
    setBloom(false)
  }
  useEffect(() => {
    onPerf?.({ dpr, bloom })
  }, [dpr, bloom, onPerf])

  const curves = useMemo(() => buildCurves(agents, edges), [agents, edges])
  const flashRef = useRef({})
  const pulses = useRef()
  const controls = useRef()
  const haloTex = useMemo(() => makeHaloTexture(), [])

  useImperativeHandle(
    ref,
    () => ({
      fire: (s, t, type) => pulses.current?.fire(s, t, type) ?? false,
      resetView: () => controls.current?.reset(),
    }),
    [],
  )

  const selIndex = selected ? agents.findIndex((a) => a.id === selected) : -1
  const neighbors = useMemo(() => {
    if (!selected) return null
    const set = new Set([selected])
    for (const [s, t] of edges) {
      if (s === selected) set.add(t)
      if (t === selected) set.add(s)
    }
    return set
  }, [selected, edges])

  return (
    <Canvas
      dpr={dpr}
      camera={{ position: [0, 5, 24], fov: 48, near: 0.1, far: 200 }}
      gl={{ antialias: false, powerPreference: 'high-performance' }}
      onPointerMissed={() => onSelect(null)}
    >
      <color attach="background" args={['#03050b']} />
      <PerformanceMonitor onIncline={incline} onDecline={decline} onFallback={fallback} flipflops={4} />
      <Particles agents={agents} quality={quality} selIndex={selIndex} />
      <Edges curves={curves} selected={selected} />
      {agents.map((a) => (
        <AgentNode
          key={a.id}
          agent={a}
          selected={selected === a.id}
          dim={!!neighbors && !neighbors.has(a.id)}
          busy={busy[a.id] || 0}
          flashRef={flashRef}
          onSelect={onSelect}
          haloTex={haloTex}
          labelMode={agents.length <= LABEL_LIMIT || (neighbors && neighbors.has(a.id)) ? 'all' : 'auto'}
        />
      ))}
      <Pulses ref={pulses} curves={curves} flashRef={flashRef} glow={bloom} />
      <OrbitControls
        ref={controls}
        makeDefault
        enableDamping
        dampingFactor={0.08}
        autoRotate={autoRotate}
        autoRotateSpeed={0.35}
        minDistance={6}
        maxDistance={48}
      />
      {bloom && (
        <EffectComposer multisampling={0}>
          <Bloom
            mipmapBlur
            levels={quality < 1 ? 5 : 8}
            intensity={1.1}
            luminanceThreshold={0.3}
            luminanceSmoothing={0.25}
            radius={0.75}
          />
        </EffectComposer>
      )}
    </Canvas>
  )
})

export default Constellation
