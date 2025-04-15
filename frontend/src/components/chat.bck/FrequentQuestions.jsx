"use client"

export default function FrequentQuestions({ onQuestionClick }) {
  const questions = ["คุณช่วยอะไรฉันได้บ้าง?", "วิธีการใช้งานเว็บไซต์นี้", "ฉันจะติดต่อฝ่ายสนับสนุนได้อย่างไร?", "มีบริการอะไรบ้าง?"]

  return (
    <div className="bg-white rounded-xl shadow-sm border border-border p-4">
      <h3 className="text-sm font-medium mb-3 text-gray-700">คำถามที่พบบ่อย</h3>
      <div className="flex flex-col gap-2">
        {questions.map((question, index) => (
          <button
            key={index}
            onClick={() => onQuestionClick(question)}
            className="px-3 py-2 text-sm text-left rounded-lg bg-gray-50 text-gray-700 hover:bg-gray-100 transition-colors"
          >
            {question}
          </button>
        ))}
      </div>
    </div>
  )
}
