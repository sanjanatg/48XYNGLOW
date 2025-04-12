"use client"

import type { RefObject } from "react"
import { motion, AnimatePresence } from "motion/react"
import type { Message } from "./chat-interface"
import TypingIndicator from "./typing-indicator"

interface MessageListProps {
  messages: Message[]
  isTyping: boolean
  messagesEndRef: RefObject<HTMLDivElement>
}

export default function MessageList({ messages, isTyping, messagesEndRef }: MessageListProps) {
  return (
    <div className="flex h-[400px] flex-col overflow-y-auto p-4 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
      <AnimatePresence>
        {messages.map((message) => (
          <motion.div
            key={message.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className={`mb-4 flex ${message.sender === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-2 ${
                message.sender === "user"
                  ? "bg-blue-600/80 text-white shadow-[0_0_15px_rgba(59,130,246,0.3)]"
                  : "bg-purple-600/30 text-white shadow-[0_0_15px_rgba(147,51,234,0.2)]"
              }`}
            >
              <p className="text-sm">{message.content}</p>
              <p className="mt-1 text-right text-xs opacity-60">
                {new Date(message.timestamp).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </p>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>

      {isTyping && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-4 flex justify-start">
          <div className="rounded-2xl bg-purple-600/30 px-4 py-3 shadow-[0_0_15px_rgba(147,51,234,0.2)]">
            <TypingIndicator />
          </div>
        </motion.div>
      )}

      <div ref={messagesEndRef} />
    </div>
  )
}

