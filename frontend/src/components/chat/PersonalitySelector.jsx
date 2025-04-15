"use client"

import { User, Bot, Smile } from "lucide-react"
import { motion } from "framer-motion"

export default function PersonalitySelector({ selectedStyle, onStyleChange, darkMode = false }) {
  const styles = [
    { id: "formal", label: "ทางการ", icon: <User size={16} /> },
    { id: "friendly", label: "เพื่อน", icon: <Smile size={16} /> },
    { id: "fun", label: "สนุก", icon: <Bot size={16} /> },
  ]

  return (
    <div className="flex items-center gap-2 mb-4">
      {styles.map((style) => (
        <motion.button
          key={style.id}
          onClick={() => onStyleChange(style.id)}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm transition-all ${
            selectedStyle === style.id 
              ? `bg-primary text-white font-medium shadow-md` 
              : `${darkMode ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`
          }`}
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
        >
          {style.icon}
          <span>{style.label}</span>
        </motion.button>
      ))}
    </div>
  )
}