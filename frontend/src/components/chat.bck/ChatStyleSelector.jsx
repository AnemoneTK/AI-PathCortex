"use client"

export default function ChatStyleSelector({ selectedStyle, onStyleChange }) {
  const styles = [
    { id: "formal", label: "ทางการ" },
    { id: "friendly", label: "เพื่อน" },
    { id: "fun", label: "สนุก" },
  ]

  return (
    <div className="bg-white rounded-lg shadow-sm border border-border p-4 mb-6">
      <h3 className="text-sm font-medium mb-3 text-gray-700">รูปแบบการสนทนา</h3>
      <div className="flex flex-wrap gap-2">
        {styles.map((style) => (
          <button
            key={style.id}
            onClick={() => onStyleChange(style.id)}
            className={`px-3 py-1.5 text-sm rounded-full transition-colors ${
              selectedStyle === style.id ? "bg-primary text-white" : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            {style.label}
          </button>
        ))}
      </div>
    </div>
  )
}
