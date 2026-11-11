import { useMemo, useRef } from 'react'
import * as THREE from 'three'
import { Canvas, useFrame } from '@react-three/fiber'
import { Html, Line, OrbitControls } from '@react-three/drei'
import { Bloom, EffectComposer } from '@react-three/postprocessing'
import { AGENTS, LINKS } from './data'

function rng(seed) {
  let value = seed
  return () => {
    value = (1664525 * value + 1013904223) >>> 0
    return value / 4294967296
  }
}

function ParticleCloud() {
  const points = useRef()
  const positions = useMemo(() => {
    const random = rng(413)
    const clusters = [
      [-3.4, 1.65], [2.45, 1.65], [3.55, -1.10],
      [-3.25, -1.55], [0.60, -2.65], [-0.3, 2.75]
    ]
    const count = 4200
    const array = new Float32Array(count * 3)
    for (let i = 0; i < count; i++) {
      const [cx, cy] = clusters[Math.floor(random() * clusters.length)]
      const angle = random() * Math.PI * 2
      const radius = (random() ** 1.8) * 2.3
      array[3 * i] = cx + Math.cos(angle) * radius
      array[3 * i + 1] = cy + Math.sin(angle) * radius * 0.72
      array[3 * i + 2] = (random() - 0.5) * 2.6 - 0.8
    }
    return array
  }, [])
  useFrame((state, delta) => {
    if (points.current) points.current.rotation.z += delta * 0.002
  })
  return (
    <points ref={points}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial color="#719cd9" size={0.016} transparent opacity={0.68} sizeAttenuation depthWrite={false} />
    </points>
  )
}

function AgentNode({ agent, selected, onSelect }) {
  const core = useRef()
  const ring = useRef()
  useFrame(({ clock }) => {
    const t = clock.elapsedTime
    if (core.current) {
      const pulse = 1 + 0.10 * Math.sin(t * 2.3 + agent.position[0])
      core.current.scale.setScalar(pulse)
    }
    if (ring.current) ring.current.rotation.z = t * 0.22
  })
  return (
    <group position={agent.position}>
      <mesh
        ref={core}
        onClick={(e) => { e.stopPropagation(); onSelect(agent.id) }}
        onPointerOver={() => { document.body.style.cursor = 'pointer' }}
        onPointerOut={() => { document.body.style.cursor = '' }}
      >
        <sphereGeometry args={[agent.size, 20, 20]} />
        <meshBasicMaterial color={agent.color} toneMapped={false} />
      </mesh>
      <mesh>
        <sphereGeometry args={[agent.size * 2.2, 20, 20]} />
        <meshBasicMaterial color={agent.color} transparent opacity={selected ? 0.11 : 0.045} depthWrite={false} />
      </mesh>
      <mesh ref={ring} rotation={[0, 0, 0]}>
        <torusGeometry args={[agent.size * 2.25, 0.009, 6, 75]} />
        <meshBasicMaterial color={selected ? '#ffb48f' : '#6a88b4'} transparent opacity={0.7} />
      </mesh>
      <Html position={[0, agent.size + 0.38, 0]} center distanceFactor={11} style={{ pointerEvents: 'none' }}>
        <div className={'node-label ' + (selected ? 'node-label--selected' : '')}>
          <span className="node-label__name">{agent.name}</span>
          <span className="node-label__status">{agent.status} · {agent.tasks} tasks</span>
        </div>
      </Html>
    </group>
  )
}

function FlowParticle({ curve, index, speed }) {
  const particle = useRef()
  useFrame(({ clock }) => {
    if (!particle.current) return
    const t = (clock.elapsedTime * speed + index / 3) % 1
    particle.current.position.copy(curve.getPoint(t))
  })
  return (
    <mesh ref={particle}>
      <sphereGeometry args={[0.047, 8, 8]} />
      <meshBasicMaterial color="#ffd3bc" toneMapped={false} />
    </mesh>
  )
}

function AgentLink({ source, target, index }) {
  const curve = useMemo(() => {
    const a = new THREE.Vector3(...source.position)
    const b = new THREE.Vector3(...target.position)
    const middle = a.clone().add(b).multiplyScalar(0.5)
    middle.y += 0.72 + (index % 3) * 0.23
    middle.z += 0.70
    return new THREE.QuadraticBezierCurve3(a, middle, b)
  }, [source, target, index])
  const points = useMemo(() => curve.getPoints(70), [curve])
  return (
    <group>
      <Line points={points} color="#ff967f" lineWidth={1.25} transparent opacity={0.45} />
      <FlowParticle curve={curve} index={0} speed={0.16 + (index % 3) * 0.04} />
      <FlowParticle curve={curve} index={1} speed={0.16 + (index % 3) * 0.04} />
      <FlowParticle curve={curve} index={2} speed={0.16 + (index % 3) * 0.04} />
    </group>
  )
}

function Scene({ selectedId, onSelect, autoRotate }) {
  const byId = useMemo(() => Object.fromEntries(AGENTS.map((agent) => [agent.id, agent])), [])
  return (
    <Canvas dpr={[1, 1.7]} camera={{ position: [0, 0.8, 14], fov: 47 }} gl={{ antialias: true, powerPreference: 'high-performance' }}>
      <color attach="background" args={['#050a16']} />
      <fog attach="fog" args={['#050a16', 13, 26]} />
      <ParticleCloud />
      {LINKS.map(([a, b], index) => (
        <AgentLink key={`${a}-${b}`} source={byId[a]} target={byId[b]} index={index} />
      ))}
      {AGENTS.map((agent) => (
        <AgentNode key={agent.id} agent={agent} selected={selectedId === agent.id} onSelect={onSelect} />
      ))}
      <EffectComposer>
        <Bloom luminanceThreshold={0.48} luminanceSmoothing={0.35} intensity={1.1} mipmapBlur />
      </EffectComposer>
      <OrbitControls enablePan={false} enableZoom minDistance={9} maxDistance={19} maxPolarAngle={Math.PI * 0.72} minPolarAngle={Math.PI * 0.28} autoRotate={autoRotate} autoRotateSpeed={0.24} />
    </Canvas>
  )
}

export default Scene
