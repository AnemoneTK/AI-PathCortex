"use client"

export default function FrequentlyAskedQuestions({ onQuestionClick }) {
  const questions = ["คุณช่วยอะไรฉันได้บ้าง?", "วิธีการใช้งานเว็บไซต์นี้", "ฉันจะติดต่อฝ่ายสนับสนุนได้อย่างไร?", "มีบริการอะไรบ้าง?"]

  return (
    <div className="bg-white rounded-lg shadow-sm border border-border p-4">
      <h3 className="text-sm font-medium mb-3 text-gray-700">คำถามที่พบบ่อย</h3>
      <div className="flex flex-wrap gap-2">
        {questions.map((question, index) => (
          <button
            key={index}
            onClick={() => onQuestionClick(question)}
            className="px-3 py-1.5 text-sm rounded-full bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors"
          >
            {question}
          </button>
        ))}
      </div>
    </div>
  )
}
