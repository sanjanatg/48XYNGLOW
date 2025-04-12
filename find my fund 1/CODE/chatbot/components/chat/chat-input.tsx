"use client"

import { useState, type FormEvent, type KeyboardEvent } from "react"
import { Send } from "lucide-react"
import { motion } from "motion/react"

interface ChatInputProps {
  onSendMessage: (message: string) => void
}

export default function ChatInput({ onSendMessage }: ChatInputProps) {
  const [message, setMessage] = useState("")

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (message.trim()) {
      onSendMessage(message)
      setMessage("")
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="flex items-end gap-2">
        <div className="relative flex-1">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about funds or investments..."
            className="w-full resize-none rounded-lg bg-white/5 px-4 py-2 text-white placeholder-white/40 outline-none ring-1 ring-white/10 transition-all focus:ring-2 focus:ring-purple-500/50 min-h-[40px] max-h-[120px]"
            rows={1}
          />
        </div>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          type="submit"
          className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-[0_0_15px_rgba(147,51,234,0.5)] transition-all hover:shadow-[0_0_20px_rgba(147,51,234,0.7)]"
          disabled={!message.trim()}
        >
          <Send size={18} />
        </motion.button>
      </div>
    </form>
  )
}

