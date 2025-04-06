import React from 'react';
import { Database, Bot, Cpu, BarChart } from 'lucide-react';

const Technology = () => {
  return (
    <section id="technology" className="py-20 bg-theme-blue text-white">
      <div className="container mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">เทคโนโลยีของเรา</h2>
          <p className="text-lg opacity-80 max-w-2xl mx-auto">
            AI Buddy ใช้เทคโนโลยีล่าสุดในการให้คำแนะนำและความช่วยเหลือที่ชาญฉลาด
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-16 items-center">
          <div>
            <div className="backdrop-blur-md bg-white/10 p-6 md:p-10 rounded-2xl border border-white/20">
              <div className="grid gap-8">
                <div className="flex items-start space-x-4">
                  <div className="bg-white/20 p-3 rounded-lg">
                    <Database className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold mb-2">Retrieval-Augmented Generation (RAG)</h3>
                    <p className="opacity-80">
                      เทคโนโลยีที่ช่วยให้ AI สามารถค้นหาและดึงข้อมูลจากฐานความรู้ที่กว้างขวางเพื่อให้คำตอบที่ถูกต้องและเป็นปัจจุบัน
                    </p>
                  </div>
                </div>
                
                <div className="flex items-start space-x-4">
                  <div className="bg-white/20 p-3 rounded-lg">
                    <Bot className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold mb-2">Large Language Models (LLM)</h3>
                    <p className="opacity-80">
                      โมเดลภาษาขั้นสูงที่ช่วยให้ AI เข้าใจคำถาม ให้คำตอบที่สอดคล้อง และมีความเป็นธรรมชาติในการสนทนา
                    </p>
                  </div>
                </div>
                
                <div className="flex items-start space-x-4">
                  <div className="bg-white/20 p-3 rounded-lg">
                    <Cpu className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold mb-2">การประมวลผลที่รวดเร็ว</h3>
                    <p className="opacity-80">
                      ระบบประมวลผลประสิทธิภาพสูงที่ช่วยให้ AI ตอบสนองได้อย่างรวดเร็วแม้กับคำถามที่ซับซ้อน
                    </p>
                  </div>
                </div>
                
                <div className="flex items-start space-x-4">
                  <div className="bg-white/20 p-3 rounded-lg">
                    <BarChart className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold mb-2">การวิเคราะห์การเรียนรู้</h3>
                    <p className="opacity-80">
                      ระบบวิเคราะห์ที่ติดตามความก้าวหน้าของคุณและปรับเนื้อหาให้เหมาะสมกับระดับความรู้ของคุณ
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-r from-theme-blue/50 to-theme-light-blue/50 rounded-2xl filter blur-3xl opacity-30"></div>
            <img 
              src="https://cdn.gpteng.co/lab/1UPcifudF9.jpg" 
              alt="AI Technology" 
              className="relative z-10 rounded-2xl shadow-2xl w-full h-auto" 
            />
          </div>
        </div>
      </div>
    </section>
  );
};

export default Technology;
