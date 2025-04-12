"use client"

import { useEffect, useRef } from "react"
import { motion } from "motion/react"
import { cn } from "@/lib/utils"

interface BeamsBackgroundProps {
  className?: string
  intensity?: "subtle" | "medium" | "strong"
}

interface Beam {
  x: number
  y: number
  width: number
  length: number
  angle: number
  speed: number
  opacity: number
  hue: number
  pulse: number
  pulseSpeed: number
}

function createBeam(width: number, height: number): Beam {
  // Modified to create more visible beams with a brighter color palette
  const angle = -35 + Math.random() * 10
  return {
    x: Math.random() * width * 1.5 - width * 0.25,
    y: Math.random() * height * 1.5 - height * 0.25,
    width: 40 + Math.random() * 80, // Wider beams
    length: height * 2.5,
    angle: angle,
    speed: 0.4 + Math.random() * 0.8, // Slightly faster movement
    opacity: 0.15 + Math.random() * 0.15, // Higher opacity for visibility
    hue: 220 + Math.random() * 60, // Blue to purple range
    pulse: Math.random() * Math.PI * 2,
    pulseSpeed: 0.01 + Math.random() * 0.02,
  }
}

export default function BeamsBackground({ className, intensity = "subtle" }: BeamsBackgroundProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const beamsRef = useRef<Beam[]>([])
  const animationFrameRef = useRef<number>(0)
  const MINIMUM_BEAMS = 20 // More beams for visibility

  const opacityMap = {
    subtle: 0.6,
    medium: 0.8,
    strong: 1,
  }

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext("2d")
    if (!ctx) return

    const updateCanvasSize = () => {
      const dpr = window.devicePixelRatio || 1
      canvas.width = window.innerWidth * dpr
      canvas.height = window.innerHeight * dpr
      canvas.style.width = `${window.innerWidth}px`
      canvas.style.height = `${window.innerHeight}px`
      ctx.scale(dpr, dpr)

      const totalBeams = MINIMUM_BEAMS
      beamsRef.current = Array.from({ length: totalBeams }, () => createBeam(canvas.width, canvas.height))
    }

    updateCanvasSize()
    window.addEventListener("resize", updateCanvasSize)

    function resetBeam(beam: Beam, index: number, totalBeams: number) {
      if (!canvas) return beam

      const column = index % 3
      const spacing = canvas.width / 3

      beam.y = canvas.height + 100
      beam.x = column * spacing + spacing / 2 + (Math.random() - 0.5) * spacing * 0.5
      beam.width = 50 + Math.random() * 50
      beam.speed = 0.3 + Math.random() * 0.3
      beam.hue = 220 + (index * 60) / totalBeams // Blue to purple range
      beam.opacity = 0.05 + Math.random() * 0.08
      return beam
    }

    function drawBeam(ctx: CanvasRenderingContext2D, beam: Beam) {
      ctx.save()
      ctx.translate(beam.x, beam.y)
      ctx.rotate((beam.angle * Math.PI) / 180)

      // Calculate pulsing opacity
      const pulsingOpacity = beam.opacity * (0.8 + Math.sin(beam.pulse) * 0.2) * opacityMap[intensity]

      const gradient = ctx.createLinearGradient(0, 0, 0, beam.length)

      // Enhanced gradient with multiple color stops - brighter, more visible colors
      gradient.addColorStop(0, `hsla(${beam.hue}, 85%, 60%, 0)`)
      gradient.addColorStop(0.1, `hsla(${beam.hue}, 85%, 60%, ${pulsingOpacity * 0.5})`)
      gradient.addColorStop(0.4, `hsla(${beam.hue}, 85%, 60%, ${pulsingOpacity})`)
      gradient.addColorStop(0.6, `hsla(${beam.hue}, 85%, 60%, ${pulsingOpacity})`)
      gradient.addColorStop(0.9, `hsla(${beam.hue}, 85%, 60%, ${pulsingOpacity * 0.5})`)
      gradient.addColorStop(1, `hsla(${beam.hue}, 85%, 60%, 0)`)

      ctx.fillStyle = gradient
      ctx.fillRect(-beam.width / 2, 0, beam.width, beam.length)
      ctx.restore()
    }

    function animate() {
      if (!canvas || !ctx) return

      ctx.clearRect(0, 0, canvas.width, canvas.height)
      ctx.filter = "blur(35px)" // Less blur for more defined beams

      const totalBeams = beamsRef.current.length
      beamsRef.current.forEach((beam, index) => {
        beam.y -= beam.speed
        beam.pulse += beam.pulseSpeed

        // Reset beam when it goes off screen
        if (beam.y + beam.length < -100) {
          resetBeam(beam, index, totalBeams)
        }

        drawBeam(ctx, beam)
      })

      animationFrameRef.current = requestAnimationFrame(animate)
    }

    animate()

    return () => {
      window.removeEventListener("resize", updateCanvasSize)
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
    }
  }, [intensity])

  return (
    <div className={cn("absolute inset-0 overflow-hidden bg-black", className)}>
      <canvas ref={canvasRef} className="absolute inset-0" style={{ filter: "blur(20px)" }} />

      <motion.div
        className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/40 to-black/60"
        animate={{
          opacity: [0.5, 0.6, 0.5],
        }}
        transition={{
          duration: 8,
          ease: "easeInOut",
          repeat: Number.POSITIVE_INFINITY,
        }}
        style={{
          backdropFilter: "blur(30px)",
        }}
      />

      {/* Digital grid overlay */}
      <div
        className="absolute inset-0 opacity-10"
        style={{
          backgroundImage: `
            linear-gradient(rgba(66, 71, 112, 0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(66, 71, 112, 0.1) 1px, transparent 1px)
          `,
          backgroundSize: "40px 40px",
        }}
      />
    </div>
  )
}

