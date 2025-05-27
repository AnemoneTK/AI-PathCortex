"use client";
import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { GraduationCap, Smile, PartyPopper } from "lucide-react";

const Personalities = () => {
  const [activePersonality, setActivePersonality] = useState(0);

  const personalities = [
    {
      id: 0,
      name: "ทางการ",
      en: "Formal",
      icon: <GraduationCap className="h-12 w-12" />,
      description:
        "ตอบแบบเป็นทางการ สุภาพ จริงจัง สไตล์ครู ให้ข้อมูลชัดเจนและถูกต้องทุกประการ เหมาะสำหรับคนที่อยากได้ความรู้จริงจัง",
      features: [
        "อธิบายละเอียดและถูกหลัก",
        "สุภาพ เป็นทางการ",
        "เน้นข้อเท็จจริง",
        "ใช้ถ้อยคำชัดเจน",
      ],
      image: "/F1.png", // เปลี่ยนเป็น URL รูปตัวละครแบบในภาพที่ส่งมา
    },
    {
      id: 1,
      name: "เพื่อน",
      en: "Friendly",
      icon: <Smile className="h-12 w-12 " />,
      description:
        "พูดคุยเหมือนเพื่อน มีมุก ช่วยคิดและให้กำลังใจ พร้อมแนะนำและให้ความรู้ในแบบกันเอง เหมาะกับคนที่อยากคุยสบายๆ",
      features: [
        "พูดคุยกันเอง สบาย ๆ",
        "มีอารมณ์ขัน เล่นมุกได้",
        "ให้คำแนะนำตรงใจ",
        "ปลอบใจหรือชวนคุยแก้เครียด",
      ],
      image: "/F2.png",
    },
    {
      id: 2,
      name: "เน้นสนุก",
      en: "Fun",
      icon: <PartyPopper className="h-12 w-12 " />,
      description:
        "ตัดตกมาเน้นความสนุก ตอบแบบแปลกใหม่ มีสีสัน ชวนหัวเราะ และช่วยให้ไอเดียไหลลื่น เหมาะกับคนที่อยากสนุกกับ AI",
      features: [
        "สนุกสนาน เฮฮา",
        "ชวนคิดนอกกรอบ",
        "ภาษาสีสันไม่ซ้ำใคร",
        "เหมาะกับการหาแรงบันดาลใจ",
      ],
      image: "/F3.png",
    },
  ];

  const active = personalities[activePersonality];

  return (
    <section id="personalities" className="py-16 md:py-20">
      <div className="container mx-auto px-4">
        <div className="text-center mb-10 md:mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4 text-theme-blue">
            1 ระบบ 3 บุคลิก <br className="md:hidden" />
            <span className="text-lg block mt-2 font-medium text-blue-600">
              เลือกได้ตามอารมณ์
            </span>
          </h2>
          <p className="text-base md:text-lg text-gray-600 max-w-2xl mx-auto">
            คุณสามารถเลือกโหมดให้ AI Buddy ตอบตามสไตล์ที่ต้องการ ไม่ว่าจะจริงจัง
            เป็นกันเอง หรือสายฮา!
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8 items-center">
          <div className="lg:col-span-2">
            <Card className="overflow-hidden border-none shadow-xl">
              <CardContent className="p-0">
                <div className="bg-gradient-to-br from-theme-blue to-theme-light-blue p-1">
                  <div className="bg-gradient-to-b rounded-lg overflow-hidden">
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
                  variant={
                    activePersonality === personality.id ? "default" : "outline"
                  }
                  className={`px-6 py-8 flex items-center space-x-2 ${
                    activePersonality === personality.id
                      ? "bg-theme-blue text-white"
                      : "border-theme-blue text-theme-blue"
                  }`}
                  onClick={() => setActivePersonality(personality.id)}
                >
                  <span>{personality.icon}</span>
                  <span className="text-lg font-medium">
                    {personality.name}
                  </span>
                  <span className="hidden md:inline-block text-sm text-gray-400 ml-2">
                    {personality.en}
                  </span>
                </Button>
              ))}
            </div>

            <div className="glass-card p-8">
              <h3 className="text-2xl font-bold mb-4 text-theme-blue flex items-center gap-2">
                {active.icon}
                <span>{active.name}</span>
                <span className="text-base text-gray-500 ml-2">
                  {active.en}
                </span>
              </h3>
              <p className="text-gray-700 mb-6">{active.description}</p>

              <ul className="grid grid-cols-1 md:grid-cols-2 gap-4 list-disc pl-5 text-gray-800">
                {active.features.map((feature, idx) => (
                  <li key={idx}>{feature}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Personalities;
