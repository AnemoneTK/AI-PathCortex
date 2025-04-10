import { User, Bot } from "lucide-react"
import React from "react"

export default function ChatMessages({ messages, isLoading, messagesEndRef }) {
  return (
    <div className="flex-1 overflow-y-auto bg-white rounded-t-xl border border-border shadow-sm p-4 mb-2">
      <div className="space-y-4">
        {messages.map((message, index) => (
          <ChatMessage key={index} message={message} />
        ))}

        {isLoading && (
          <div className="flex items-center space-x-2 animate-pulse">
            <div className="w-2 h-2 bg-primary rounded-full"></div>
            <div className="w-2 h-2 bg-primary rounded-full animation-delay-200"></div>
            <div className="w-2 h-2 bg-primary rounded-full animation-delay-400"></div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>
    </div>
  )
}

function ChatMessage({ message }) {
  const isUser = message.role === "user"

  // ฟังก์ชันสำหรับการแปลงข้อความให้มีการจัดรูปแบบที่ดีขึ้น
  const formatMessageContent = (content) => {
    if (!content) return "";
    
    // แยกเนื้อหาตามบรรทัด
    const lines = content.split('\n');
    
    // ตรวจหาและปรับแต่งส่วนต่างๆ ของข้อความ
    let formattedContent = [];
    let inList = false;
    
    for (let i = 0; i < lines.length; i++) {
      let line = lines[i];
      
      // จัดการกับหัวข้อใหญ่
      if (line.match(/^ตำแหน่ง|^ความรับผิดชอบ|^ทักษะ|^ช่วงเงินเดือน/i)) {
        formattedContent.push(
          <h3 key={i} className="font-bold text-md mt-3 mb-1">{line}</h3>
        );
      }
      // จัดการกับหัวข้อย่อยที่มีเครื่องหมาย :
      else if (line.includes(':') && !line.trim().startsWith('*')) {
        const [title, ...rest] = line.split(':');
        formattedContent.push(
          <div key={i} className="mb-2">
            <span className="font-bold">{title}:</span>
            <span>{rest.join(':')}</span>
          </div>
        );
      }
      // จัดการกับรายการที่ขึ้นต้นด้วย *
      else if (line.trim().startsWith('*')) {
        if (!inList) {
          inList = true;
          formattedContent.push(<ul key={`list-${i}`} className="list-disc pl-5 my-2 space-y-1"></ul>);
        }
        
        const listItem = line.trim().substring(1).trim();
        const lastList = formattedContent[formattedContent.length - 1];
        
        // เพิ่มรายการเข้าไปใน ul ที่มีอยู่แล้ว
        const updatedList = React.cloneElement(
          lastList,
          { ...lastList.props },
          [...(lastList.props.children || []), <li key={`item-${i}`}>{listItem}</li>]
        );
        
        formattedContent[formattedContent.length - 1] = updatedList;
      }
      // ข้อความปกติ
      else {
        inList = false;
        if (line.trim() !== "") {
          formattedContent.push(<p key={i} className="mb-2">{line}</p>);
        } else {
          formattedContent.push(<div key={i} className="my-1"></div>);
        }
      }
    }
    
    return <>{formattedContent}</>;
  };

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`flex max-w-[80%] ${isUser ? "flex-row-reverse" : "flex-row"}`}>
        <div className={`flex-shrink-0 flex items-start mt-1 ${isUser ? "ml-2" : "mr-2"}`}>
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center ${
              isUser ? "bg-blue-100" : "bg-gray-100"
            }`}
          >
            {isUser ? <User className="w-4 h-4 text-blue-600" /> : <Bot className="w-4 h-4 text-gray-600" />}
          </div>
        </div>

        <div className="flex flex-col">
          <div
            className={`p-3 rounded-lg ${
              isUser ? "bg-primary text-white rounded-tr-none" : "bg-gray-100 text-gray-800 rounded-tl-none"
            }`}
          >
            {isUser ? message.content : formatMessageContent(message.content)}
          </div>
          
          {/* Sources section */}
          {!isUser && message.sources && message.sources.length > 0 && (
            <div className="mt-2 text-xs text-gray-500 px-1">
              <details className="cursor-pointer">
                <summary className="font-medium">แหล่งข้อมูล ({message.sources.length})</summary>
                <ul className="mt-1 space-y-1 pl-2">
                  {message.sources.map((source, idx) => (
                    <li key={idx} className="flex items-start gap-1">
                      <span className="font-medium">{source.job_title || source.type}:</span> 
                      <span>{source.content.substring(0, 60)}...</span>
                    </li>
                  ))}
                </ul>
              </details>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}