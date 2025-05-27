import "../globals.css";

export const metadata = {
  title: "AI Chat Assistant",
  description: "Chat with our AI assistant",
};

export default function ChatLayout({ children }) {
  return (
    <div className="min-h-screen  w-full bg-gradient-to-b from-[hsl(var(--theme-light-blue))] via-white to-[hsl(var(--theme-light-gray))] flex items-center justify-center">
      <div className="w-full  px-2 md:px-6">{children}</div>
    </div>
  );
}
