import "../globals.css"

export const metadata = {
  title: "AI Chat Assistant",
  description: "Chat with our AI assistant",
}

export default function RootLayout({ children }) {
  return (
    <html lang="th">
      <body className="h-screen w-screen bg-background flex  justify-center items-center">{children}</body>
    </html>
  )
}
