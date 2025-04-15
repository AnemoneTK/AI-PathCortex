"use client"

import { Bot, Menu, Sun, Moon, User } from "lucide-react"
import { motion } from "framer-motion"

export default function ChatHeader({ 
  chatStyle, 
  toggleSidebar, 
  darkMode = false, 
  toggleDarkMode,
  toggleUserInfo
}) {
  const getPersonalityName = (style) => {
    switch(style) {
      case "formal": return "ทางการ"
      case "friendly": return "เพื่อน"
      case "fun": return "สนุก"
      default: return "เพื่อน"
    }
  }
  
  return (
    <motion.div 
      className={`px-4 py-3 border-b ${darkMode ? 'bg-gray-800 border-gray-700 text-white' : 'bg-white border-gray-200 text-gray-800'} shadow-sm flex items-center justify-between`}
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className="flex items-center gap-2">
        <Bot className={`${darkMode ? 'text-blue-400' : 'text-primary'} w-5 h-5`} />
        <div>
          <h1 className={`text-lg font-semibold ${darkMode ? 'text-white' : 'text-gray-800'}`}>แชทกับ AI Buddy</h1>
          <p className={`text-sm ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>กำลังใช้รูปแบบ: {getPersonalityName(chatStyle)}</p>
        </div>
      </div>
      
      <div className="flex items-center space-x-2">
        {/* ปุ่มดูข้อมูลผู้ใช้ */}
        <button 
          onClick={toggleUserInfo}
          className={`p-2 rounded-full ${darkMode ? 'text-gray-300 hover:bg-gray-700' : 'text-gray-600 hover:bg-gray-100'}`}
        >
          <User className="w-5 h-5" />
        </button>
        
        {/* ปุ่มสลับโหมดสี */}
        <button 
          onClick={toggleDarkMode}
          className={`p-2 rounded-full ${darkMode ? 'text-gray-300 hover:bg-gray-700' : 'text-gray-600 hover:bg-gray-100'}`}
        >
          {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </button>
        
        {/* ปุ่มแสดง/ซ่อน Sidebar บนมือถือ */}
        <button 
          className={`md:hidden p-2 rounded-full ${darkMode ? 'text-gray-300 hover:bg-gray-700' : 'text-gray-600 hover:bg-gray-100'}`}
          onClick={toggleSidebar}
        >
          <Menu className="w-5 h-5" />
        </button>
      </div>
    </motion.div>
  )
}