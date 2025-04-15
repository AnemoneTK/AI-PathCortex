"use client"

import { motion, AnimatePresence } from "framer-motion"
import { Settings, MoreHorizontal, Sun, Moon, User, LogOut } from "lucide-react"
import CharacterWithFollowingEyes from "@/components/CharacterWithFollowingEyes"
import PersonalitySelector from "./PersonalitySelector"
import SuggestedQuestions from "./SuggestedQuestions"

export default function ChatSidebar({ 
  chatStyle, 
  onStyleChange, 
  onQuestionClick, 
  showSidebar, 
  toggleSidebar,
  darkMode,
  toggleDarkMode,
  toggleUserInfo,
  userData
}) {
  return (
    <>
      {/* Sidebar Toggle Button (Mobile Only) */}
      <button 
        className="fixed top-4 left-4 z-50 md:hidden bg-white dark:bg-gray-800 p-2 rounded-full shadow-md"
        onClick={toggleSidebar}
      >
        <MoreHorizontal className="w-5 h-5 text-gray-700 dark:text-gray-300" />
      </button>

      {/* Sidebar */}
      <div 
        className={`w-80 lg:w-96 h-full ${darkMode ? 'bg-gray-800 text-white' : 'bg-white'} border-r ${darkMode ? 'border-gray-700' : 'border-gray-200'} p-6 flex flex-col fixed md:relative z-40 transition-all duration-300 ${
          showSidebar ? "left-0" : "-left-full"
        } md:left-0`}
      >
        <div className="mb-6">
          <div className="w-full aspect-square max-w-[160px] mx-auto mb-4 relative">
            {/* ฉากหลังสีอ่อนด้านหลังตัวละคร */}
            <div className={`absolute inset-0 rounded-full bg-gradient-to-br ${darkMode ? 'from-blue-900 to-indigo-900' : 'from-blue-100 to-indigo-100'}`}></div>
            <CharacterWithFollowingEyes />
          </div>

          <div>
            <h2 className={`text-lg font-semibold ${darkMode ? 'text-white' : 'text-gray-800'} text-center mb-1`}>AI Buddy</h2>
            <p className={`text-sm ${darkMode ? 'text-gray-300' : 'text-gray-500'} text-center mb-4`}>ที่ปรึกษาด้านอาชีพ IT ของคุณ</p>
          </div>

          <div>
            <h3 className={`text-sm font-medium ${darkMode ? 'text-gray-300' : 'text-gray-700'} mb-2`}>รูปแบบการสนทนา</h3>
            <PersonalitySelector 
              selectedStyle={chatStyle} 
              onStyleChange={onStyleChange}
              darkMode={darkMode}
            />
          </div>
        </div>

        <div className="flex-1 overflow-auto">
          <SuggestedQuestions onQuestionClick={onQuestionClick} darkMode={darkMode} />
        </div>

        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex flex-col gap-3">
            {/* ปุ่มดูข้อมูลผู้ใช้ */}
            <button 
              onClick={toggleUserInfo}
              className={`flex items-center gap-2 text-sm ${darkMode ? 'text-gray-300 hover:text-white' : 'text-gray-600 hover:text-gray-900'} transition-colors px-2 py-1.5 rounded-lg hover:bg-opacity-10 hover:bg-gray-500`}
            >
              <User size={16} />
              <span>ข้อมูลผู้ใช้</span>
              {userData && <span className={`ml-auto text-xs px-1.5 py-0.5 rounded-full ${darkMode ? 'bg-blue-700' : 'bg-blue-100'}`}>{userData.name}</span>}
            </button>

            {/* ปุ่มสลับโหมดสี */}
            <button 
              onClick={toggleDarkMode}
              className={`flex items-center gap-2 text-sm ${darkMode ? 'text-gray-300 hover:text-white' : 'text-gray-600 hover:text-gray-900'} transition-colors px-2 py-1.5 rounded-lg hover:bg-opacity-10 hover:bg-gray-500`}
            >
              {darkMode ? <Sun size={16} /> : <Moon size={16} />}
              <span>{darkMode ? 'โหมดสว่าง' : 'โหมดมืด'}</span>
            </button>

            {/* ปุ่มตั้งค่า */}
            <button 
              className={`flex items-center gap-2 text-sm ${darkMode ? 'text-gray-300 hover:text-white' : 'text-gray-600 hover:text-gray-900'} transition-colors px-2 py-1.5 rounded-lg hover:bg-opacity-10 hover:bg-gray-500`}
            >
              <Settings size={16} />
              <span>ตั้งค่า</span>
            </button>
          </div>
        </div>
      </div>
    </>
  )
}