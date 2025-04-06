"use client";

import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { GraduationCap, Lightbulb, Rocket } from "lucide-react";

const Personalities = () => {
  const [activePersonality, setActivePersonality] = useState(0);
  
  const personalities = [
    {
      id: 0,
      name: "ครูพี่โค้ช",
      icon: <GraduationCap className="h-12 w-12 text-theme-blue" />,
      description: "บุคลิกภาพแบบครูผู้สอน ที่จะอธิบายอย่างละเอียดและเข้าใจง่าย เหมาะสำหรับผู้เริ่มต้นที่ต้องการคำอธิบายที่ชัดเจน",
      features: ["อธิบายแบบขั้นตอน", "ให้ตัวอย่างที่เข้าใจง่าย", "มีความอดทนสูง", "เน้นหลักการพื้นฐาน"],
      image: "https://cdn.gpteng.co/lab/A1rxQL9zkI.png"
    },
    {
      id: 1,
      name: "ผู้เชี่ยวชาญเทค",
      icon: <Lightbulb className="h-12 w-12 text-theme-blue" />,
      description: "มืออาชีพที่มีความเชี่ยวชาญเฉพาะด้าน ให้คำแนะนำเชิงลึกและเทคนิคขั้นสูง เหมาะสำหรับผู้ที่มีพื้นฐานระดับกลางถึงสูง",
      features: ["คำแนะนำเชิงลึก", "เทคนิคขั้นสูง", "แนวทางปฏิบัติที่ดีที่สุด", "เน้นการแก้ปัญหาที่ซับซ้อน"],
      image: "https://cdn.gpteng.co/lab/nmpWMCMoD1.png"
    },
    {
      id: 2,
      name: "เพื่อนนักพัฒนา",
      icon: <Rocket className="h-12 w-12 text-theme-blue" />,
      description: "เป็นกันเองเหมือนเพื่อนร่วมงาน เน้นการแก้ปัญหาร่วมกันและให้กำลังใจ เหมาะสำหรับการทำงานโปรเจกต์และการเรียนรู้แบบกลุ่ม",
      features: ["สไตล์การสื่อสารเป็นกันเอง", "ให้กำลังใจและแรงบันดาลใจ", "แนะนำทรัพยากรที่มีประโยชน์", "ช่วยระดมความคิด"],
      image: "https://cdn.gpteng.co/lab/rlvn1xOuTf.png"
    }
  ];
  
  const active = personalities[activePersonality];
  
  return (
    <section id="personalities" className="py-20">
      <div className="container mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4 text-theme-blue">เลือกบุคลิกภาพ AI ที่เหมาะกับคุณ</h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            AI Buddy มีบุคลิกภาพให้เลือก 3 แบบ ตามสไตล์การเรียนรู้และความต้องการของคุณ
          </p>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8 items-center">
          <div className="lg:col-span-2">
            <Card className="overflow-hidden border-none shadow-xl">
              <CardContent className="p-0">
                <div className="bg-gradient-to-br from-theme-blue to-theme-light-blue p-1">
                  <div className="bg-white rounded-lg overflow-hidden">
                    <img 
                      src={active.image} 
                      alt={active.name} 
                      className="w-full h-auto object-cover" 
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
          
          <div className="lg:col-span-3 space-y-8">
            <div className="flex flex-wrap gap-3 justify-center lg:justify-start">
              {personalities.map((personality) => (
                <Button 
                  key={personality.id}
                  variant={activePersonality === personality.id ? "default" : "outline"}
                  className={`px-6 py-8 flex items-center space-x-2 ${
                    activePersonality === personality.id 
                      ? "bg-theme-blue text-white" 
                      : "border-theme-blue text-theme-blue"
                  }`}
                  onClick={() => setActivePersonality(personality.id)}
                >
                  <span>{personality.icon}</span>
                  <span className="text-lg font-medium">{personality.name}</span>
                </Button>
              ))}
            </div>
            
            <div className="glass-card p-8">
              <h3 className="text-2xl font-bold mb-4 text-theme-blue flex items-center gap-2">
                {active.icon}
                <span>{active.name}</span>
              </h3>
              <p className="text-gray-600 mb-6">{active.description}</p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {active.features.map((feature, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <div className="w-2 h-2 rounded-full bg-theme-blue"></div>
                    <span>{feature}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Personalities;
