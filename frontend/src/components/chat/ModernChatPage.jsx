"use client"

import { useState, useRef, useEffect } from "react"
import { motion } from "framer-motion"
import ChatSidebar from "./ChatSidebar"
import MessageList from "./MessageList"
import ChatInput from "./ChatInput"
import ChatHeader from "./ChatHeader"
import UserInfoModal from "./UserInfoModal"

export default function ModernChatPage() {
const BASE_URL = process.env.NEXT_PUBLIC_API_BASE;

  // States
  const [messages, setMessages] = useState([
    { 
      role: "assistant", 
      content: "สวัสดี ฉันเป็น AI Buddy ที่จะช่วยให้คำแนะนำเกี่ยวกับอาชีพด้าน IT และคอมพิวเตอร์ คุณมีคำถามอะไรไหม?" 
    }
  ])
  const [inputValue, setInputValue] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [chatStyle, setChatStyle] = useState("friendly")
  const messagesEndRef = useRef(null)
  const [showSidebar, setShowSidebar] = useState(true)
  const [darkMode, setDarkMode] = useState(false)
  const [showUserInfo, setShowUserInfo] = useState(false)
  const [userData, setUserData] = useState(null)

  // ตรวจสอบและโหลดข้อมูลผู้ใช้
  useEffect(() => {
   const fetchUserData = async () => {
  try {
    const response = await fetch(`${BASE_URL}/registration/user-info`);
    
    const text = await response.text(); 
    console.log("Raw response:", text);

    if (!response.ok || text.startsWith("<!DOCTYPE html>")) {
      throw new Error("ได้ HTML แทน JSON");
    }

    const data = JSON.parse(text); // แปลง text เป็น JSON ทีหลัง
    setUserData(data);

  } catch (error) {
    console.error("Failed to fetch user info:", error);
  }
};

    
    fetchUserData();
  }, []);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  // Toggle sidebar on mobile
  const toggleSidebar = () => {
    setShowSidebar(!showSidebar)
  }

  // Toggle dark mode
  const toggleDarkMode = () => {
    setDarkMode(!darkMode)
  }

  // Toggle user info modal
  const toggleUserInfo = () => {
    setShowUserInfo(!showUserInfo)
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
      console.log('inputValue',inputValue)
      console.log('BASE_URL',BASE_URL)

      const response = await fetch(`${BASE_URL}/chat/`, {
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
    <div className={`h-screen w-full flex flex-row ${darkMode ? 'dark bg-gray-900' : 'bg-gradient-to-br from-blue-50 to-indigo-50'} transition-colors duration-200`}>
      {/* Sidebar */}
      <ChatSidebar 
        chatStyle={chatStyle}
        onStyleChange={handleStyleChange}
        onQuestionClick={handleQuestionClick}
        showSidebar={showSidebar}
        toggleSidebar={toggleSidebar}
        darkMode={darkMode}
        toggleDarkMode={toggleDarkMode}
        toggleUserInfo={toggleUserInfo}
        userData={userData}
      />

      {/* Main Chat Area */}
      <div className=" overflow-hidden flex flex-col h-full w-full pt-16 md:pt-0 ml-0 ">
        <ChatHeader 
          chatStyle={chatStyle} 
          toggleSidebar={toggleSidebar}
          darkMode={darkMode}
          toggleDarkMode={toggleDarkMode}
          toggleUserInfo={toggleUserInfo}
        />

        <MessageList 
          messages={messages} 
          isLoading={isLoading} 
          messagesEndRef={messagesEndRef}
          darkMode={darkMode}
        />

        <ChatInput 
          value={inputValue}
          onChange={setInputValue}
          onSubmit={handleSendMessage}
          isLoading={isLoading}
          darkMode={darkMode}
        />
      </div>

      {/* User Info Modal */}
      {showUserInfo && userData && (
        <UserInfoModal 
          userData={userData} 
          onClose={toggleUserInfo}
          darkMode={darkMode}
        />
      )}
    </div>
  )
}