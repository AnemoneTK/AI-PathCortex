"use client"

import { useState, useRef, useEffect } from "react"
import { motion } from "framer-motion"
import ChatSidebar from "./ChatSidebar"
import MessageList from "./MessageList"
import ChatInput from "./ChatInput"
import ChatHeader from "./ChatHeader"

export default function ModernChatPage() {
  // States
  const [messages, setMessages] = useState([
    { 
      role: "assistant", 
      content: "สวัสดีค่ะ ฉันเป็น AI Buddy ที่จะช่วยให้คำแนะนำเกี่ยวกับอาชีพด้าน IT และคอมพิวเตอร์ คุณมีคำถามอะไรไหมคะ?" 
    }
  ])
  const [inputValue, setInputValue] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [chatStyle, setChatStyle] = useState("friendly")
  const messagesEndRef = useRef(null)
  const [showSidebar, setShowSidebar] = useState(true)

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  // Toggle sidebar on mobile
  const toggleSidebar = () => {
    setShowSidebar(!showSidebar)
  }

  // Handle sending message
  const handleSendMessage = async (e) => {
    e.preventDefault()
    if (inputValue.trim() === "") return

    // Add user message
    const userMessage = { role: "user", content: inputValue }
    setMessages((prev) => [...prev, userMessage])
    setInputValue("")
    setIsLoading(true)

    try {
      // Call API with selected style
      const response = await fetch("http://0.0.0.0:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          personality: chatStyle, 
          message: inputValue
        }),
      })

      if (!response.ok) {
        throw new Error(`API responded with status: ${response.status}`)
      }

      const data = await response.json()
      const aiResponse = { 
        role: "assistant", 
        content: data.message,
        sources: data.search_results
      }
      
      setMessages((prev) => [...prev, aiResponse])
    } catch (error) {
      console.error("Error calling chat API:", error)
      // Add error message
      const errorMessage = { 
        role: "assistant", 
        content: "ขออภัย เกิดข้อผิดพลาดในการเชื่อมต่อกับระบบ โปรดลองอีกครั้งในภายหลัง" 
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleStyleChange = (style) => {
    setChatStyle(style)
  }

  const handleQuestionClick = (question) => {
    setInputValue(question)
  }

  return (
    <div className="h-screen w-full bg-gray-50 flex">
      {/* Sidebar */}
      <ChatSidebar 
        chatStyle={chatStyle}
        onStyleChange={handleStyleChange}
        onQuestionClick={handleQuestionClick}
        showSidebar={showSidebar}
        toggleSidebar={toggleSidebar}
      />

      {/* Main Chat Area */}
      <div className="flex-1 overflow-hidden flex flex-col h-full pt-16 md:pt-0">
        <ChatHeader 
          chatStyle={chatStyle} 
          toggleSidebar={toggleSidebar} 
        />

        <MessageList 
          messages={messages} 
          isLoading={isLoading} 
          messagesEndRef={messagesEndRef} 
        />

        <ChatInput 
          value={inputValue}
          onChange={setInputValue}
          onSubmit={handleSendMessage}
          isLoading={isLoading}
        />
      </div>
    </div>
  )
}