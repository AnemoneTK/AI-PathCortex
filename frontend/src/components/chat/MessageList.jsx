"use client"

import { motion, AnimatePresence } from "framer-motion"
import { Bot } from "lucide-react"
import MessageBubble from "./MessageBubble"

export default function MessageList({ messages, isLoading, messagesEndRef, darkMode = false }) {
  return (
    <div className={`flex-1 overflow-y-auto ${darkMode ? 'bg-gray-900' : 'bg-gradient-to-br from-blue-50 to-indigo-50'} p-4`}>
      <div className="max-w-3xl mx-auto">
        <AnimatePresence initial={false}>
          {messages.map((message, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ 
                duration: 0.3,
                delay: message.role === "user" ? 0 : 0.2
              }}
            >
              <MessageBubble 
                message={message} 
                isLastMessage={index === messages.length - 1}
                darkMode={darkMode} 
              />
            </motion.div>
          ))}
        </AnimatePresence>

        {isLoading && (
          <motion.div 
            className="flex justify-start mb-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <div className="flex items-start">
              <div className={`w-8 h-8 rounded-full ${darkMode ? 'bg-blue-900' : 'bg-blue-100'} flex items-center justify-center mr-2 flex-shrink-0`}>
                <Bot className={`w-4 h-4 ${darkMode ? 'text-blue-400' : 'text-blue-600'}`} />
              </div>
              <div className={`${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} border p-4 rounded-2xl rounded-tl-none shadow-sm flex items-center space-x-2`}>
                <div className={`w-2 h-2 ${darkMode ? 'bg-blue-500' : 'bg-primary'} rounded-full animate-pulse`}></div>
                <div className={`w-2 h-2 ${darkMode ? 'bg-blue-500' : 'bg-primary'} rounded-full animate-pulse`} style={{ animationDelay: "0.2s" }}></div>
                <div className={`w-2 h-2 ${darkMode ? 'bg-blue-500' : 'bg-primary'} rounded-full animate-pulse`} style={{ animationDelay: "0.4s" }}></div>
              </div>
            </div>
          </motion.div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
    </div>
  )
}