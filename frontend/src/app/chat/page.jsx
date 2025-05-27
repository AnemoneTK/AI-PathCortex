"use client";

import { useState, useEffect, useRef } from "react";
import { Send, User2, Loader2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
const MODES = [
  { name: "ทางการ", key: "formal", avatar: "/avatars/formal.png" },
  { name: "เพื่อน", key: "friendly", avatar: "/avatars/friend.png" },
  { name: "สนุก", key: "fun", avatar: "/avatars/fun.png" },
];

const SUGGESTIONS = [
  "อาชีพทางด้าน IT มีอะไรบ้าง?",
  "เงินเดือน Frontend Developer เท่าไหร่?",
  "วิธีเขียน Resume สำหรับ IT",
  "ทักษะที่จำเป็นสำหรับ UX/UI Designer",
];

export default function ModernChatPage() {
  const BASE_URL = process.env.NEXT_PUBLIC_API_BASE;
  const [mode, setMode] = useState(MODES[1]);
  const [inputValue, setInputValue] = useState("");
  const [aiResponse, setAiResponse] = useState("");
  const [userMessage, setUserMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showUserInfo, setShowUserInfo] = useState(false);
  const [userData, setUserData] = useState(null);
  const chatBodyRef = useRef();

  // โหลด user info
  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const response = await fetch(`${BASE_URL}/registration/user-info`);
        const text = await response.text();
        if (!response.ok || text.startsWith("<!DOCTYPE html>"))
          throw new Error();
        const data = JSON.parse(text);
        setUserData(data);
      } catch {
        setUserData(null);
      }
    };
    fetchUserData();
  }, [BASE_URL]);

  // Auto scroll chat body
  useEffect(() => {
    chatBodyRef.current?.scrollTo({
      top: chatBodyRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [aiResponse, userMessage]);

  // ส่งคำถาม
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;
    setUserMessage(inputValue);
    setAiResponse("");
    setIsLoading(true);

    try {
      const response = await fetch(`${BASE_URL}/chat/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          personality: mode.key,
          message: inputValue,
        }),
      });
      if (!response.ok) throw new Error();
      const data = await response.json();
      setAiResponse(data.message || "...");
    } catch {
      setAiResponse("ขออภัย เกิดข้อผิดพลาดกับระบบ กรุณาลองใหม่ภายหลัง");
    } finally {
      setIsLoading(false);
      setInputValue("");
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-blue-100">
      <div className="relative flex flex-col w-full max-w-xl h-[90vh] bg-white/95 rounded-3xl shadow-2xl border border-blue-100 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-4 md:px-6 py-3 border-b border-blue-100 bg-gradient-to-r from-blue-100 to-blue-300">
          <div className="flex gap-2">
            {MODES.map((m) => (
              <button
                key={m.key}
                onClick={() => !isLoading && setMode(m)}
                className={`px-3 md:px-4 py-1 rounded-full text-sm md:text-base font-semibold border-2 shadow transition
                  ${
                    mode.key === m.key
                      ? "bg-gradient-to-r from-blue-400 via-blue-500 to-blue-700 text-white border-blue-600 shadow-md scale-105"
                      : "bg-white text-blue-700 border-blue-200 hover:bg-blue-100 hover:text-blue-900"
                  }
                  ${isLoading ? "opacity-60 pointer-events-none" : ""}
                `}
                type="button"
                disabled={isLoading}
              >
                {m.name}
              </button>
            ))}
          </div>
          <button
            onClick={() => !isLoading && setShowUserInfo(true)}
            className="w-9 h-9 md:w-10 md:h-10 flex items-center justify-center rounded-full bg-white border-2 border-blue-300 shadow hover:bg-blue-50 transition"
            aria-label="ข้อมูลผู้ใช้"
            disabled={isLoading}
            tabIndex={isLoading ? -1 : 0}
          >
            <User2 className="text-blue-500" size={24} />
          </button>
        </div>

        {/* Avatar & Mode */}
        <div className="flex flex-col items-center py-4 border-b border-blue-50 bg-gradient-to-b from-white to-blue-50">
          <img
            src={mode.avatar}
            alt={mode.name}
            className="w-20 h-20 md:w-24 md:h-24 rounded-full border-4 border-blue-200 shadow-md bg-white object-cover mb-2"
          />
          <span className="font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-700 via-blue-600 to-blue-400 text-lg md:text-xl drop-shadow mb-1">
            โหมด: {mode.name}
          </span>
        </div>

        {/* Suggestions */}
        <div className="flex flex-wrap gap-2 px-4 md:px-6 py-3 bg-white border-b border-blue-50">
          {SUGGESTIONS.map((s, i) => (
            <button
              key={i}
              onClick={() => !isLoading && setInputValue(s)}
              className="w-full text-center md:w-auto md:text-left px-3 py-1 rounded-xl bg-gradient-to-r from-blue-200 via-blue-100 to-white text-blue-800 text-xs md:text-sm font-medium shadow border border-blue-100 hover:from-blue-300 hover:via-blue-200 hover:to-white transition"
              type="button"
              disabled={isLoading}
            >
              {s}
            </button>
          ))}
        </div>

        {/* Chat scrollable body */}
        <div
          ref={chatBodyRef}
          className="flex-1 px-3 md:px-5 py-3 md:py-4 space-y-4 overflow-y-auto bg-white/80"
          style={{ minHeight: 0 }}
        >
          {/* Bubble user */}
          {userMessage && (
            <div className="flex justify-end">
              <div className="max-w-[90%] md:max-w-[80%] px-4 py-2 rounded-2xl shadow bg-gradient-to-r from-blue-600 to-blue-400 text-white border border-blue-300 text-base ml-auto break-words whitespace-pre-wrap">
                {userMessage}
              </div>
            </div>
          )}
          {/* Bubble AI (Markdown + Prose) */}
          {(aiResponse || isLoading) && (
            <div className="flex justify-start">
              <div
                className="
  prose prose-blue max-w-full text-base
  prose-p:my-1 prose-p:leading-snug
  prose-li:my-0 prose-li:leading-tight
  px-4 py-2 rounded-2xl shadow
  bg-gradient-to-br from-blue-50 via-white to-blue-100
  border border-blue-200
"
              >
                {isLoading ? (
                  "กำลังพิมพ์..."
                ) : (
                  <ReactMarkdown>{aiResponse}</ReactMarkdown>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Input bar - always at bottom */}
        <form
          className="flex items-center gap-2 px-4 py-3 border-t border-blue-100 bg-white/95"
          onSubmit={handleSendMessage}
        >
          <input
            className="flex-1 px-4 py-3 rounded-full bg-gradient-to-r from-white via-blue-50 to-white border border-blue-200 text-blue-900 placeholder:text-blue-400 focus:ring-2 focus:ring-blue-300 shadow-md text-base"
            placeholder="พิมพ์คำถาม..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            disabled={isLoading}
            autoFocus
          />
          <button
            className="px-5 py-3 rounded-full bg-gradient-to-r from-blue-600 to-blue-400 text-white hover:from-blue-700 hover:to-blue-500 transition flex items-center gap-2 font-semibold text-base shadow disabled:opacity-50"
            type="submit"
            disabled={isLoading || !inputValue.trim()}
          >
            <Send size={22} /> ส่ง
          </button>
        </form>

        {/* Overlay loading - กันคลิกทุกจุด */}
        {isLoading && (
          <div className="absolute inset-0 bg-white/80 flex flex-col items-center justify-center z-50">
            <video
              src="/Loading.webm"
              autoPlay
              loop
              muted
              playsInline
              className="w-40 aspect-square object-contain"
            />
            <div className="text-blue-700 text-lg font-bold mt-3">
              Loading...
            </div>
          </div>
        )}

        {/* User info modal */}
        {showUserInfo && userData && (
          <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center">
            <div className="bg-white rounded-2xl shadow-2xl p-6 w-[90vw] max-w-md flex flex-col items-center relative animate-fade-in border border-blue-100">
              <button
                className="absolute top-2 right-3 text-gray-400 hover:text-red-500 text-2xl"
                onClick={() => setShowUserInfo(false)}
                aria-label="ปิด"
              >
                &times;
              </button>
              <User2 size={40} className="text-blue-500 mb-2" />
              <div className="text-lg font-bold text-blue-700 mb-2">
                ข้อมูลผู้ใช้
              </div>
              <div className="text-blue-800 text-center space-y-1">
                <div>
                  ชื่อ:{" "}
                  <span className="font-medium text-black">
                    {userData.name}
                  </span>
                </div>
                <div>
                  สถาบัน:{" "}
                  <span className="font-medium text-black">
                    {userData.institution}
                  </span>
                </div>
                <div>
                  ปีการศึกษา:{" "}
                  <span className="font-medium text-black">
                    {userData.year}
                  </span>
                </div>
                <div>
                  สถานะ:{" "}
                  <span className="font-medium text-black">
                    {userData.education_status}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
