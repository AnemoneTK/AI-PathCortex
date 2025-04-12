"use client"

import { useState, useRef, useEffect } from "react"
import ChatHeader from "@/components/chat/ChatHeader"
import ChatMessages from "@/components/chat/ChatMessages"
import ChatInput from "@/components/chat/ChatInput"
import CharacterWithFollowingEyes from "@/components/CharacterWithFollowingEyes"
import FrequentQuestions from "@/components/chat/FrequentQuestions"

export default function ChatPage() {
  const [messages, setMessages] = useState([{ role: "assistant", content: "สวัสดีค่ะ มีอะไรให้ช่วยไหมคะ?" }])
  const [inputValue, setInputValue] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [chatStyle, setChatStyle] = useState("formal") // formal, friendly, fun
  const messagesEndRef = useRef(null)

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

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
          query: userMessage.content
        }),
      })
      console.log('response',response)

      if (!response.ok) {
        throw new Error(`API responded with status: ${response.status}`)
      }

      const data = await response.json()
      const aiResponse = { 
        role: "assistant", 
        content: data.answer,
        sources: data.sources // Save sources for potential display
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
    <div className="h-screen w-screen bg-contain flex flex-col justify-center items-center">
      <div className="container justify-center items-center px-4 py-6 flex-grow flex flex-col md:flex-row gap-6">
        {/* Left column - AI Character and Style Selection */}
        <div className="md:w-1/3 lg:w-1/4">
          <div className="sticky top-6">
            <CharacterWithFollowingEyes />
            <ChatHeader activeStyle={chatStyle} onStyleChange={handleStyleChange} />
            <FrequentQuestions onQuestionClick={handleQuestionClick} />
          </div>
        </div>

        {/* Right column - Chat Interface */}
        <div className="md:w-2/3 lg:w-3/4 flex flex-col h-[80vh]">
          <ChatMessages messages={messages} isLoading={isLoading} messagesEndRef={messagesEndRef} />
          <ChatInput value={inputValue} onChange={setInputValue} onSubmit={handleSendMessage} isLoading={isLoading} />
        </div>
      </div>
    </div>
  )
}