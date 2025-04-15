import "../globals.css"

export const metadata = {
  title: "AI Chat Assistant",
  description: "Chat with our AI assistant",
}

export default function ChatLayout({ children }) {
  return <div className="chat-container h-full">{children}</div>
}
