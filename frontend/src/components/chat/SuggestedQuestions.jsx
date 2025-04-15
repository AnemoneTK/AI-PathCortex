"use client"

import { BriefcaseBusiness, FileText, Code, Lightbulb } from "lucide-react"
import { motion } from "framer-motion"

export default function SuggestedQuestions({ onQuestionClick, darkMode = false }) {
  const questions = [
    { text: "อาชีพทางด้าน IT มีอะไรบ้าง?", icon: <BriefcaseBusiness size={14} /> },
    { text: "เงินเดือน Frontend Developer เท่าไหร่?", icon: <Lightbulb size={14} /> },
    { text: "วิธีเขียน Resume สำหรับ IT", icon: <FileText size={14} /> },
    { text: "ทักษะที่จำเป็นสำหรับ UX/UI Designer", icon: <Code size={14} /> },
  ]

  return (
    <div className="space-y-2">
      <h3 className={`text-sm font-medium ${darkMode ? 'text-gray-300' : 'text-gray-700'} mb-2`}>คำถามแนะนำ</h3>
      <div className="grid grid-cols-1 gap-2">
        {questions.map((question, index) => (
          <motion.button
            key={index}
            onClick={() => onQuestionClick(question.text)}
            className={`px-3 py-2 text-sm text-left rounded-lg ${
              darkMode 
                ? 'bg-gray-700 border-gray-600 text-gray-200 hover:bg-gray-600' 
                : 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50'
            } transition-colors flex items-center gap-2 shadow-sm`}
            whileHover={{ y: -2, boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)" }}
          >
            <span className={`flex-shrink-0 ${darkMode ? 'text-blue-400' : 'text-blue-600'}`}>
              {question.icon}
            </span>
            <span>{question.text}</span>
          </motion.button>
        ))}
      </div>
    </div>
  )
}