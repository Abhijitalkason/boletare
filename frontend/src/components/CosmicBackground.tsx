import React, { useRef, useEffect, useCallback } from 'react'
import { useTheme } from '../context/ThemeContext'

// ═══════════════════════════════════════════════════════════════
// Cosmic Background — Rich space scene with planets, galaxy,
// dense starfield, comets, and nebula clouds
// ═══════════════════════════════════════════════════════════════

interface Star {
  x: number; y: number
  size: number; brightness: number
  twinkleSpeed: number; twinklePhase: number
  driftX: number; driftY: number
  color: [number, number, number]  // tint
  hasCross: boolean                // bright stars get cross sparkle
}

interface ShootingStar {
  x: number; y: number
  length: number; angle: number; speed: number
  opacity: number; life: number; maxLife: number
  width: number
}

interface Nebula {
  x: number; y: number; radius: number
  color: [number, number, number]
  driftX: number; driftY: number
  pulseSpeed: number; pulsePhase: number
  baseOpacity: number
}

interface Planet {
  x: number; y: number; radius: number
  orbitCenterX: number; orbitCenterY: number
  orbitRadiusX: number; orbitRadiusY: number
  orbitSpeed: number; orbitPhase: number
  colors: string[]       // gradient stops
  hasRings: boolean
  ringTilt: number       // ellipse tilt for rings
  hasBands: boolean      // Jupiter-like cloud bands
  glowColor: string
  glowRadius: number
}

interface GalaxyArm {
  cx: number; cy: number
  rotation: number
  armCount: number
  armSpread: number
  radius: number
  starCount: number
  driftAngle: number
  color: [number, number, number]
}

// ── Initialization ──────────────────────────────────────────

function createStars(w: number, h: number): Star[] {
  const stars: Star[] = []
  // Dense background stars (tiny, dim)
  for (let i = 0; i < 350; i++) {
    stars.push({
      x: Math.random() * w, y: Math.random() * h,
      size: Math.random() * 1.2 + 0.3,
      brightness: Math.random() * 0.4 + 0.2,
      twinkleSpeed: Math.random() * 0.002 + 0.0005,
      twinklePhase: Math.random() * Math.PI * 2,
      driftX: (Math.random() - 0.5) * 0.04,
      driftY: (Math.random() - 0.5) * 0.02,
      color: [220 + Math.random() * 35, 220 + Math.random() * 35, 230 + Math.random() * 25],
      hasCross: false,
    })
  }
  // Medium stars
  for (let i = 0; i < 80; i++) {
    const tint = Math.random()
    let color: [number, number, number]
    if (tint < 0.3) color = [255, 240, 200]        // warm gold
    else if (tint < 0.5) color = [200, 220, 255]    // cool blue
    else color = [255, 255, 255]                      // white
    stars.push({
      x: Math.random() * w, y: Math.random() * h,
      size: Math.random() * 1.5 + 1.2,
      brightness: Math.random() * 0.4 + 0.5,
      twinkleSpeed: Math.random() * 0.004 + 0.001,
      twinklePhase: Math.random() * Math.PI * 2,
      driftX: (Math.random() - 0.5) * 0.06,
      driftY: (Math.random() - 0.5) * 0.03,
      color,
      hasCross: false,
    })
  }
  // Bright prominent stars (with cross sparkle)
  for (let i = 0; i < 18; i++) {
    const tint = Math.random()
    let color: [number, number, number]
    if (tint < 0.35) color = [255, 248, 220]        // warm
    else if (tint < 0.6) color = [200, 220, 255]     // blue
    else color = [255, 255, 255]
    stars.push({
      x: Math.random() * w, y: Math.random() * h,
      size: Math.random() * 2 + 2,
      brightness: Math.random() * 0.3 + 0.7,
      twinkleSpeed: Math.random() * 0.005 + 0.002,
      twinklePhase: Math.random() * Math.PI * 2,
      driftX: (Math.random() - 0.5) * 0.03,
      driftY: (Math.random() - 0.5) * 0.015,
      color,
      hasCross: true,
    })
  }
  return stars
}

function createNebulae(w: number, h: number): Nebula[] {
  return [
    // Large blue cosmic dust cloud (top area)
    { x: w * 0.65, y: h * 0.2, radius: Math.max(w, h) * 0.35, color: [40, 80, 160], driftX: 0.015, driftY: 0.008, pulseSpeed: 0.0005, pulsePhase: 0, baseOpacity: 0.07 },
    // Purple nebula (center-left)
    { x: w * 0.2, y: h * 0.5, radius: Math.max(w, h) * 0.28, color: [100, 60, 180], driftX: -0.01, driftY: 0.012, pulseSpeed: 0.0008, pulsePhase: Math.PI * 0.5, baseOpacity: 0.05 },
    // Deep blue cloud (bottom)
    { x: w * 0.5, y: h * 0.85, radius: Math.max(w, h) * 0.3, color: [30, 60, 120], driftX: 0.008, driftY: -0.01, pulseSpeed: 0.0004, pulsePhase: Math.PI, baseOpacity: 0.06 },
    // Warm accent (small, near planet area)
    { x: w * 0.8, y: h * 0.6, radius: Math.max(w, h) * 0.15, color: [120, 80, 40], driftX: -0.005, driftY: 0.005, pulseSpeed: 0.001, pulsePhase: Math.PI * 1.5, baseOpacity: 0.03 },
    // Milky band (horizontal haze)
    { x: w * 0.5, y: h * 0.45, radius: Math.max(w, h) * 0.5, color: [60, 70, 120], driftX: 0.005, driftY: 0, pulseSpeed: 0.0003, pulsePhase: 0.5, baseOpacity: 0.03 },
  ]
}

function createPlanets(w: number, h: number): Planet[] {
  const scale = Math.min(w, h)
  return [
    // Saturn (large, with rings, upper-left area)
    {
      x: 0, y: 0,
      radius: scale * 0.07,
      orbitCenterX: w * 0.18, orbitCenterY: h * 0.28,
      orbitRadiusX: w * 0.02, orbitRadiusY: h * 0.015,
      orbitSpeed: 0.00008, orbitPhase: 0,
      colors: ['#d4a96a', '#c49a5c', '#b08840', '#9a7535', '#c4a060'],
      hasRings: true, ringTilt: 0.3,
      hasBands: false,
      glowColor: 'rgba(200, 170, 100, 0.12)', glowRadius: scale * 0.14,
    },
    // Jupiter (large, with bands, lower-center)
    {
      x: 0, y: 0,
      radius: scale * 0.06,
      orbitCenterX: w * 0.45, orbitCenterY: h * 0.72,
      orbitRadiusX: w * 0.015, orbitRadiusY: h * 0.01,
      orbitSpeed: 0.00006, orbitPhase: Math.PI * 0.7,
      colors: ['#d4a070', '#c89060', '#b07840', '#c49a60', '#d4a878'],
      hasRings: false, ringTilt: 0,
      hasBands: true,
      glowColor: 'rgba(180, 140, 80, 0.1)', glowRadius: scale * 0.12,
    },
    // Rocky moon (small, lower-right)
    {
      x: 0, y: 0,
      radius: scale * 0.025,
      orbitCenterX: w * 0.78, orbitCenterY: h * 0.65,
      orbitRadiusX: w * 0.01, orbitRadiusY: h * 0.008,
      orbitSpeed: 0.00015, orbitPhase: Math.PI * 1.3,
      colors: ['#a0a8b8', '#889098', '#788088', '#909aa8'],
      hasRings: false, ringTilt: 0,
      hasBands: false,
      glowColor: 'rgba(150, 160, 180, 0.08)', glowRadius: scale * 0.05,
    },
    // Small distant planet (upper-right)
    {
      x: 0, y: 0,
      radius: scale * 0.015,
      orbitCenterX: w * 0.82, orbitCenterY: h * 0.22,
      orbitRadiusX: w * 0.005, orbitRadiusY: h * 0.004,
      orbitSpeed: 0.0002, orbitPhase: Math.PI * 0.4,
      colors: ['#8090a0', '#708090', '#607080'],
      hasRings: false, ringTilt: 0,
      hasBands: false,
      glowColor: 'rgba(120, 140, 160, 0.06)', glowRadius: scale * 0.03,
    },
  ]
}

function createGalaxy(w: number, h: number): GalaxyArm {
  return {
    cx: w * 0.72, cy: h * 0.18,
    rotation: 0,
    armCount: 2,
    armSpread: 0.6,
    radius: Math.min(w, h) * 0.15,
    starCount: 200,
    driftAngle: 0,
    color: [180, 200, 255],
  }
}

// ── Drawing helpers ─────────────────────────────────────────

function drawCrossStar(ctx: CanvasRenderingContext2D, x: number, y: number, size: number, alpha: number, color: [number, number, number]) {
  const [r, g, b] = color
  // Core bright dot
  ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${alpha})`
  ctx.beginPath()
  ctx.arc(x, y, size * 0.6, 0, Math.PI * 2)
  ctx.fill()

  // Cross spikes (4-pointed star)
  const spikeLen = size * 4
  const spikeWidth = size * 0.3
  ctx.strokeStyle = `rgba(${r}, ${g}, ${b}, ${alpha * 0.6})`
  ctx.lineWidth = spikeWidth
  ctx.beginPath()
  ctx.moveTo(x - spikeLen, y); ctx.lineTo(x + spikeLen, y)
  ctx.moveTo(x, y - spikeLen); ctx.lineTo(x, y + spikeLen)
  ctx.stroke()

  // Smaller diagonal spikes
  const dLen = spikeLen * 0.5
  ctx.strokeStyle = `rgba(${r}, ${g}, ${b}, ${alpha * 0.3})`
  ctx.lineWidth = spikeWidth * 0.6
  ctx.beginPath()
  ctx.moveTo(x - dLen, y - dLen); ctx.lineTo(x + dLen, y + dLen)
  ctx.moveTo(x + dLen, y - dLen); ctx.lineTo(x - dLen, y + dLen)
  ctx.stroke()

  // Soft glow
  const glow = ctx.createRadialGradient(x, y, 0, x, y, size * 5)
  glow.addColorStop(0, `rgba(${r}, ${g}, ${b}, ${alpha * 0.2})`)
  glow.addColorStop(1, `rgba(${r}, ${g}, ${b}, 0)`)
  ctx.fillStyle = glow
  ctx.fillRect(x - size * 5, y - size * 5, size * 10, size * 10)
}

function drawPlanet(ctx: CanvasRenderingContext2D, p: Planet, t: number) {
  // Update orbital position
  p.x = p.orbitCenterX + Math.cos(t * p.orbitSpeed + p.orbitPhase) * p.orbitRadiusX
  p.y = p.orbitCenterY + Math.sin(t * p.orbitSpeed + p.orbitPhase) * p.orbitRadiusY

  ctx.save()

  // Outer glow
  const glow = ctx.createRadialGradient(p.x, p.y, p.radius * 0.5, p.x, p.y, p.glowRadius)
  glow.addColorStop(0, p.glowColor)
  glow.addColorStop(1, 'rgba(0, 0, 0, 0)')
  ctx.fillStyle = glow
  ctx.fillRect(p.x - p.glowRadius, p.y - p.glowRadius, p.glowRadius * 2, p.glowRadius * 2)

  // Planet body (sphere gradient)
  const bodyGrad = ctx.createRadialGradient(
    p.x - p.radius * 0.3, p.y - p.radius * 0.3, p.radius * 0.1,
    p.x, p.y, p.radius
  )
  bodyGrad.addColorStop(0, p.colors[0])
  bodyGrad.addColorStop(0.4, p.colors[1] || p.colors[0])
  bodyGrad.addColorStop(0.7, p.colors[2] || p.colors[0])
  bodyGrad.addColorStop(1, p.colors[p.colors.length - 1])

  ctx.fillStyle = bodyGrad
  ctx.beginPath()
  ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2)
  ctx.fill()

  // Cloud bands (Jupiter style)
  if (p.hasBands) {
    ctx.save()
    ctx.beginPath()
    ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2)
    ctx.clip()
    const bandColors = ['rgba(180,130,60,0.3)', 'rgba(160,110,50,0.2)', 'rgba(200,160,80,0.25)', 'rgba(140,100,50,0.2)']
    for (let i = 0; i < 6; i++) {
      const by = p.y - p.radius + (p.radius * 2 * (i + 0.5)) / 6
      const bandH = p.radius * 0.18
      ctx.fillStyle = bandColors[i % bandColors.length]
      ctx.fillRect(p.x - p.radius, by - bandH / 2, p.radius * 2, bandH)
    }
    // Great red spot
    const spotX = p.x + p.radius * 0.2 + Math.sin(t * 0.0003) * p.radius * 0.1
    const spotY = p.y + p.radius * 0.15
    const spotGrad = ctx.createRadialGradient(spotX, spotY, 0, spotX, spotY, p.radius * 0.12)
    spotGrad.addColorStop(0, 'rgba(180, 100, 40, 0.5)')
    spotGrad.addColorStop(1, 'rgba(180, 100, 40, 0)')
    ctx.fillStyle = spotGrad
    ctx.beginPath()
    ctx.ellipse(spotX, spotY, p.radius * 0.12, p.radius * 0.08, 0, 0, Math.PI * 2)
    ctx.fill()
    ctx.restore()
  }

  // Shadow (dark edge on right/bottom for 3D effect)
  const shadowGrad = ctx.createRadialGradient(
    p.x + p.radius * 0.2, p.y + p.radius * 0.2, p.radius * 0.3,
    p.x, p.y, p.radius
  )
  shadowGrad.addColorStop(0, 'rgba(0, 0, 0, 0)')
  shadowGrad.addColorStop(0.6, 'rgba(0, 0, 0, 0.1)')
  shadowGrad.addColorStop(1, 'rgba(0, 0, 0, 0.5)')
  ctx.fillStyle = shadowGrad
  ctx.beginPath()
  ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2)
  ctx.fill()

  // Rings (Saturn)
  if (p.hasRings) {
    ctx.save()
    // Ring behind planet (lower half)
    const ringInner = p.radius * 1.3
    const ringOuter = p.radius * 2.0
    const ringYScale = p.ringTilt

    // Back ring
    ctx.globalAlpha = 0.4
    ctx.strokeStyle = '#c8a870'
    ctx.lineWidth = p.radius * 0.12
    ctx.beginPath()
    ctx.ellipse(p.x, p.y, ringOuter, ringOuter * ringYScale, -0.15, Math.PI * 0.05, Math.PI * 0.95)
    ctx.stroke()

    ctx.strokeStyle = '#b89860'
    ctx.lineWidth = p.radius * 0.08
    ctx.beginPath()
    ctx.ellipse(p.x, p.y, ringInner, ringInner * ringYScale, -0.15, Math.PI * 0.05, Math.PI * 0.95)
    ctx.stroke()

    // Redraw planet body over back ring portion
    ctx.globalAlpha = 1
    ctx.fillStyle = bodyGrad
    ctx.beginPath()
    ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2)
    ctx.fill()
    ctx.fillStyle = shadowGrad
    ctx.beginPath()
    ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2)
    ctx.fill()

    // Front ring
    ctx.globalAlpha = 0.6
    ctx.strokeStyle = '#d4b880'
    ctx.lineWidth = p.radius * 0.14
    ctx.beginPath()
    ctx.ellipse(p.x, p.y, ringOuter, ringOuter * ringYScale, -0.15, Math.PI * 1.05, Math.PI * 1.95)
    ctx.stroke()

    ctx.strokeStyle = '#c4a870'
    ctx.lineWidth = p.radius * 0.09
    ctx.beginPath()
    ctx.ellipse(p.x, p.y, ringInner, ringInner * ringYScale, -0.15, Math.PI * 1.05, Math.PI * 1.95)
    ctx.stroke()

    // Thin gap ring
    ctx.globalAlpha = 0.3
    ctx.strokeStyle = '#b09050'
    ctx.lineWidth = p.radius * 0.04
    ctx.beginPath()
    ctx.ellipse(p.x, p.y, (ringInner + ringOuter) / 2, ((ringInner + ringOuter) / 2) * ringYScale, -0.15, Math.PI * 1.05, Math.PI * 1.95)
    ctx.stroke()

    ctx.restore()
  }

  // Specular highlight (bright spot top-left)
  const specGrad = ctx.createRadialGradient(
    p.x - p.radius * 0.35, p.y - p.radius * 0.35, 0,
    p.x - p.radius * 0.35, p.y - p.radius * 0.35, p.radius * 0.5
  )
  specGrad.addColorStop(0, 'rgba(255, 255, 255, 0.25)')
  specGrad.addColorStop(1, 'rgba(255, 255, 255, 0)')
  ctx.fillStyle = specGrad
  ctx.beginPath()
  ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2)
  ctx.fill()

  ctx.restore()
}

function drawGalaxy(ctx: CanvasRenderingContext2D, g: GalaxyArm, t: number) {
  g.driftAngle = t * 0.00005
  const cos = Math.cos(g.driftAngle)
  const sin = Math.sin(g.driftAngle)

  // Bright core glow
  const coreGlow = ctx.createRadialGradient(g.cx, g.cy, 0, g.cx, g.cy, g.radius * 0.3)
  coreGlow.addColorStop(0, `rgba(${g.color[0]}, ${g.color[1]}, ${g.color[2]}, 0.2)`)
  coreGlow.addColorStop(0.5, `rgba(${g.color[0]}, ${g.color[1]}, ${g.color[2]}, 0.06)`)
  coreGlow.addColorStop(1, 'rgba(0,0,0,0)')
  ctx.fillStyle = coreGlow
  ctx.fillRect(g.cx - g.radius * 0.3, g.cy - g.radius * 0.3, g.radius * 0.6, g.radius * 0.6)

  // Spiral arm stars
  for (let i = 0; i < g.starCount; i++) {
    const armIndex = i % g.armCount
    const frac = i / g.starCount
    const dist = frac * g.radius
    const baseAngle = (armIndex / g.armCount) * Math.PI * 2
    const spiralAngle = baseAngle + frac * Math.PI * 3 + g.driftAngle
    const scatter = (Math.random() - 0.5) * g.armSpread * (0.3 + frac * 0.7)

    const sx = dist * Math.cos(spiralAngle + scatter)
    const sy = dist * Math.sin(spiralAngle + scatter) * 0.45  // tilt

    // Rotate
    const rx = sx * cos - sy * sin + g.cx
    const ry = sx * sin + sy * cos + g.cy

    const brightness = (1 - frac) * 0.6 + 0.1
    const size = (1 - frac) * 1.2 + 0.3
    const alpha = brightness * (0.6 + 0.4 * Math.sin(t * 0.001 + i))

    ctx.fillStyle = `rgba(${g.color[0]}, ${g.color[1]}, ${g.color[2]}, ${alpha})`
    ctx.beginPath()
    ctx.arc(rx, ry, size, 0, Math.PI * 2)
    ctx.fill()
  }
}

// ═══════════════════════════════════════════════════════════════
// Main Component
// ═══════════════════════════════════════════════════════════════

export default function CosmicBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const animRef = useRef<number>(0)
  const starsRef = useRef<Star[]>([])
  const nebulaeRef = useRef<Nebula[]>([])
  const shootingRef = useRef<ShootingStar[]>([])
  const planetsRef = useRef<Planet[]>([])
  const galaxyRef = useRef<GalaxyArm | null>(null)
  const timeRef = useRef(0)
  const { isDark } = useTheme()

  const reducedMotion = typeof window !== 'undefined'
    && window.matchMedia('(prefers-reduced-motion: reduce)').matches

  const initCanvas = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const dpr = window.devicePixelRatio || 1
    const w = window.innerWidth
    const h = window.innerHeight
    canvas.width = w * dpr
    canvas.height = h * dpr
    canvas.style.width = `${w}px`
    canvas.style.height = `${h}px`
    const ctx = canvas.getContext('2d')
    if (ctx) ctx.scale(dpr, dpr)
    starsRef.current = createStars(w, h)
    nebulaeRef.current = createNebulae(w, h)
    planetsRef.current = createPlanets(w, h)
    galaxyRef.current = createGalaxy(w, h)
    shootingRef.current = []
  }, [])

  useEffect(() => {
    initCanvas()
    const onResize = () => initCanvas()
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [initCanvas])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    if (reducedMotion) {
      const w = window.innerWidth
      const h = window.innerHeight
      ctx.clearRect(0, 0, w, h)
      ctx.globalAlpha = isDark ? 0.8 : 0.08
      starsRef.current.forEach((s) => {
        ctx.fillStyle = `rgba(${s.color[0]}, ${s.color[1]}, ${s.color[2]}, ${s.brightness})`
        ctx.beginPath()
        ctx.arc(s.x, s.y, s.size, 0, Math.PI * 2)
        ctx.fill()
      })
      return
    }

    const animate = () => {
      const w = window.innerWidth
      const h = window.innerHeight
      const opacity = isDark ? 0.85 : 0.08
      timeRef.current++
      const t = timeRef.current

      ctx.clearRect(0, 0, w, h)
      ctx.globalAlpha = opacity

      // ── Nebulae ──
      nebulaeRef.current.forEach((n) => {
        n.x += n.driftX
        n.y += n.driftY
        if (n.x < -n.radius) n.x = w + n.radius
        if (n.x > w + n.radius) n.x = -n.radius
        if (n.y < -n.radius) n.y = h + n.radius
        if (n.y > h + n.radius) n.y = -n.radius

        const pulse = 0.7 + 0.3 * Math.sin(t * n.pulseSpeed + n.pulsePhase)
        const nebulaOpacity = (isDark ? n.baseOpacity : n.baseOpacity * 0.3) * pulse
        const grad = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, n.radius)
        grad.addColorStop(0, `rgba(${n.color[0]}, ${n.color[1]}, ${n.color[2]}, ${nebulaOpacity})`)
        grad.addColorStop(0.4, `rgba(${n.color[0]}, ${n.color[1]}, ${n.color[2]}, ${nebulaOpacity * 0.5})`)
        grad.addColorStop(1, 'rgba(0, 0, 0, 0)')
        ctx.fillStyle = grad
        ctx.fillRect(n.x - n.radius, n.y - n.radius, n.radius * 2, n.radius * 2)
      })

      // ── Galaxy ──
      if (galaxyRef.current) {
        drawGalaxy(ctx, galaxyRef.current, t)
      }

      // ── Stars ──
      starsRef.current.forEach((s) => {
        s.x += s.driftX
        s.y += s.driftY
        if (s.x < 0) s.x += w
        if (s.x > w) s.x -= w
        if (s.y < 0) s.y += h
        if (s.y > h) s.y -= h

        const twinkle = 0.4 + 0.6 * Math.sin(t * s.twinkleSpeed + s.twinklePhase)
        const alpha = s.brightness * twinkle

        if (s.hasCross) {
          drawCrossStar(ctx, s.x, s.y, s.size, alpha, s.color)
        } else {
          const [r, g, b] = s.color
          ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${alpha})`
          ctx.beginPath()
          ctx.arc(s.x, s.y, s.size, 0, Math.PI * 2)
          ctx.fill()

          // Soft glow for medium+ stars
          if (s.size > 1.2) {
            ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${alpha * 0.12})`
            ctx.beginPath()
            ctx.arc(s.x, s.y, s.size * 3, 0, Math.PI * 2)
            ctx.fill()
          }
        }
      })

      // ── Planets ──
      planetsRef.current.forEach((p) => drawPlanet(ctx, p, t))

      // ── Shooting Stars / Comets ──
      if (Math.random() < 0.004) {
        const startX = Math.random() * w * 0.8 + w * 0.1
        const startY = Math.random() * h * 0.4
        const isBig = Math.random() < 0.2  // 20% chance of a bright comet
        shootingRef.current.push({
          x: startX, y: startY,
          length: isBig ? 120 + Math.random() * 100 : 50 + Math.random() * 70,
          angle: Math.PI * 0.15 + Math.random() * 0.35,
          speed: isBig ? 3 + Math.random() * 2 : 5 + Math.random() * 5,
          opacity: 1,
          life: 0,
          maxLife: isBig ? 80 + Math.random() * 40 : 35 + Math.random() * 25,
          width: isBig ? 2.5 : 1.2,
        })
      }

      shootingRef.current = shootingRef.current.filter((ss) => {
        ss.life++
        ss.x += Math.cos(ss.angle) * ss.speed
        ss.y += Math.sin(ss.angle) * ss.speed
        ss.opacity = 1 - (ss.life / ss.maxLife) ** 0.7

        if (ss.opacity <= 0) return false

        const tailX = ss.x - Math.cos(ss.angle) * ss.length
        const tailY = ss.y - Math.sin(ss.angle) * ss.length

        const grad = ctx.createLinearGradient(tailX, tailY, ss.x, ss.y)
        grad.addColorStop(0, 'rgba(255, 255, 255, 0)')
        grad.addColorStop(0.5, `rgba(180, 200, 255, ${ss.opacity * 0.2})`)
        grad.addColorStop(0.85, `rgba(220, 235, 255, ${ss.opacity * 0.6})`)
        grad.addColorStop(1, `rgba(255, 255, 255, ${ss.opacity})`)

        ctx.strokeStyle = grad
        ctx.lineWidth = ss.width
        ctx.lineCap = 'round'
        ctx.beginPath()
        ctx.moveTo(tailX, tailY)
        ctx.lineTo(ss.x, ss.y)
        ctx.stroke()

        // Bright glowing head
        const headGlow = ctx.createRadialGradient(ss.x, ss.y, 0, ss.x, ss.y, ss.width * 4)
        headGlow.addColorStop(0, `rgba(255, 255, 255, ${ss.opacity})`)
        headGlow.addColorStop(1, 'rgba(255, 255, 255, 0)')
        ctx.fillStyle = headGlow
        ctx.beginPath()
        ctx.arc(ss.x, ss.y, ss.width * 4, 0, Math.PI * 2)
        ctx.fill()

        return true
      })

      animRef.current = requestAnimationFrame(animate)
    }

    animRef.current = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(animRef.current)
  }, [isDark, reducedMotion])

  return (
    <canvas
      ref={canvasRef}
      className="cosmic-bg"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        zIndex: 0,
        pointerEvents: 'none',
      }}
    />
  )
}
