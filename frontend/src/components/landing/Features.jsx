import React from 'react';
import { Brain, Code, Book, Globe, Clock, Shield } from 'lucide-react';

const Features = () => {
  const features = [
    {
      icon: <Brain className="h-10 w-10 text-theme-blue" />,
      title: "การเรียนรู้ที่ปรับเปลี่ยนได้",
      description: "AI Buddy ปรับเปลี่ยนวิธีการสอนตามระดับความรู้และรูปแบบการเรียนรู้ของคุณ"
    },
    {
      icon: <Code className="h-10 w-10 text-theme-blue" />,
      title: "ความช่วยเหลือด้านการเขียนโค้ด",
      description: "รับคำแนะนำเกี่ยวกับการเขียนโค้ด การแก้ไขบั๊ก และแนวทางการเขียนโปรแกรมที่ดี"
    },
    {
      icon: <Book className="h-10 w-10 text-theme-blue" />,
      title: "แหล่งข้อมูลการเรียนรู้",
      description: "เข้าถึงบทความ เอกสาร และแหล่งข้อมูลที่เกี่ยวข้องกับหัวข้อที่คุณสนใจ"
    },
    {
      icon: <Globe className="h-10 w-10 text-theme-blue" />,
      title: "ข้อมูลที่ทันสมัย",
      description: "ข้อมูลและคำแนะนำที่เป็นปัจจุบันตามเทรนด์ล่าสุดในวงการไอที"
    },
    {
      icon: <Clock className="h-10 w-10 text-theme-blue" />,
      title: "พร้อมใช้งาน 24/7",
      description: "สามารถถามคำถามและรับคำแนะนำได้ตลอด 24 ชั่วโมง ทุกวัน"
    },
    {
      icon: <Shield className="h-10 w-10 text-theme-blue" />,
      title: "ความปลอดภัยและความเป็นส่วนตัว",
      description: "ระบบความปลอดภัยที่แข็งแกร่งเพื่อปกป้องข้อมูลและความเป็นส่วนตัวของคุณ"
    }
  ];

  return (
    <section id="features" className="py-20 bg-theme-light-gray">
      <div className="container mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4 text-theme-blue">คุณสมบัติหลัก</h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            AI Buddy มาพร้อมกับฟีเจอร์ที่หลากหลายเพื่อช่วยให้การเรียนรู้ด้าน Computer Science เป็นเรื่องง่าย
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <div 
              key={index} 
              className="feature-card"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <div className="mb-4">{feature.icon}</div>
              <h3 className="text-xl font-semibold mb-3 text-theme-blue">{feature.title}</h3>
              <p className="text-gray-600">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Features;
