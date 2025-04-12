import { motion } from "motion/react"

export default function TypingIndicator() {
  return (
    <div className="flex items-center space-x-2">
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          className="h-2 w-2 rounded-full bg-purple-400"
          animate={{
            y: ["0%", "-50%", "0%"],
          }}
          transition={{
            duration: 0.8,
            repeat: Number.POSITIVE_INFINITY,
            repeatType: "loop",
            delay: i * 0.2,
            ease: "easeInOut",
          }}
        />
      ))}
    </div>
  )
}

