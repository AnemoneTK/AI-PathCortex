import React from 'react';
import { Button } from "@/components/ui/button";
import { Bot, Brain, Book } from "lucide-react";

const Hero = () => {
  return (
    <section id="home" className="pt-28 pb-16 md:py-32 bg-hero-pattern">
      <div className="container mx-auto px-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
          <div className="animate-fade-in">
            <h1 className="text-3xl md:text-5xl font-bold mb-4 text-theme-blue">
              AI Buddy สำหรับนักศึกษา<br />
              <span className="text-gradient">วิทยาการคอมพิวเตอร์</span>
            </h1>
            <p className="text-lg text-gray-600 mb-8">
              ผู้ช่วยอัจฉริยะที่จะช่วยพัฒนาทักษะและให้คำปรึกษาในด้าน Computer Science
              พร้อมด้วย 3 บุคลิกภาพเฉพาะตัว ที่สามารถเลือกให้เหมาะกับรูปแบบการเรียนรู้ของคุณ
            </p>
            <div className="flex flex-wrap gap-4">
              <Button className="bg-theme-blue hover:bg-blue-800 text-white">เริ่มต้นใช้งานฟรี</Button>
              <Button variant="outline" className="border-theme-blue text-theme-blue hover:bg-theme-blue/10">ดูเพิ่มเติม</Button>
            </div>
            
            <div className="flex items-center space-x-8 mt-8">
              <div className="flex items-center space-x-2">
                <div className="bg-blue-100 p-2 rounded-full">
                  <Brain className="h-5 w-5 text-theme-blue" />
                </div>
                <span className="text-gray-600">RAG + LLM</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="bg-blue-100 p-2 rounded-full">
                  <Bot className="h-5 w-5 text-theme-blue" />
                </div>
                <span className="text-gray-600">3 บุคลิกภาพ</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="bg-blue-100 p-2 rounded-full">
                  <Book className="h-5 w-5 text-theme-blue" />
                </div>
                <span className="text-gray-600">ความรู้ที่เป็นปัจจุบัน</span>
              </div>
            </div>
          </div>
          
          <div className="animate-fade-in" style={{ animationDelay: '0.3s' }}>
            <div className="relative">
              <div className="absolute -top-16 -left-16 w-32 h-32 bg-theme-light-blue/20 rounded-full filter blur-xl"></div>
              <div className="absolute -bottom-16 -right-16 w-32 h-32 bg-theme-blue/20 rounded-full filter blur-xl"></div>
              <div className="glass-card p-8 relative z-10 animate-float">
                <img src="https://cdn.gpteng.co/lab/wU4Nqp8uSS.png" alt="AI Buddy" className="w-full h-auto rounded-lg" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Hero;
