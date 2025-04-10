"use client"

import { Send } from "lucide-react"

export default function ChatInput({ value, onChange, onSubmit, isLoading }) {
  return (
    <form onSubmit={onSubmit} className="flex items-center gap-2">
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="พิมพ์ข้อความของคุณที่นี่..."
        className="flex-1 p-3 rounded-lg border border-border focus:outline-none focus:ring-2 focus:ring-primary"
        disabled={isLoading}
      />
      <button
        type="submit"
        className="p-3 bg-primary text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50"
        disabled={value.trim() === "" || isLoading}
      >
        <Send className="w-5 h-5" />
      </button>
    </form>
  )
}
