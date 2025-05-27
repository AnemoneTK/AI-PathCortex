import React from "react";
import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";
import Link from "next/link";

const CTA = () => {
  return (
    <section className="py-16">
      <div className="container mx-auto px-4">
        <div className="bg-gradient-to-r from-theme-blue to-theme-light-blue rounded-2xl p-1">
          <div className="bg-white rounded-xl p-8 md:p-12">
            <div className="max-w-3xl mx-auto text-center">
              <h2 className="text-3xl md:text-4xl font-bold mb-6 text-theme-blue">
                พร้อมที่จะเริ่มการเรียนรู้กับ AI Buddy PathCorTex แล้วหรือยัง?
              </h2>
              <p className="text-lg text-gray-600 mb-8">
                เริ่มต้นใช้งาน AI Buddy และพัฒนาทักษะด้าน Computer Science
                ของคุณได้อย่างรวดเร็วและมีประสิทธิภาพ
              </p>
              <Link href="/registration">
                <Button className="bg-theme-blue hover:bg-blue-800 text-white px-8 py-6 rounded-xl text-lg">
                  <span>เริ่มต้นใช้งาน</span>
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default CTA;
