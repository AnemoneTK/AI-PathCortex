"use client"

import { Send } from "lucide-react"
import { motion } from "framer-motion"

export default function ChatInput({ value, onChange, onSubmit, isLoading, darkMode = false }) {
  return (
    <div className={`${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} border-t p-4 shadow-md`}>
      <div className="mx-auto">
        <form onSubmit={onSubmit} className="relative">
          <input
            type="text"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder="พิมพ์ข้อความของคุณที่นี่..."
            className={`w-full px-4 py-3 pr-12 rounded-2xl ${
              darkMode 
                ? 'bg-gray-700 border-gray-600 text-white placeholder:text-gray-400 focus:ring-blue-500' 
                : 'bg-white border-gray-200 text-gray-800 focus:ring-primary'
            } border focus:outline-none focus:ring-2 focus:border-transparent shadow-sm`}
            disabled={isLoading}
          />
          <motion.button
            type="submit"
            className={`absolute right-2 top-1/2 -translate-y-1/2 p-2 ${
              value.trim() === "" || isLoading 
                ? "bg-gray-300 text-gray-500 dark:bg-gray-600 dark:text-gray-400" 
                : "bg-primary text-white hover:bg-blue-600"
            } rounded-full transition-colors disabled:opacity-50`}
            disabled={value.trim() === "" || isLoading}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Send className="w-4 h-4" />
          </motion.button>
        </form>
      </div>
    </div>
  )
}