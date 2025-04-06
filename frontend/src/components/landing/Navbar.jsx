import React from 'react';
import { Button } from "@/components/ui/button";
import { Brain } from "lucide-react";

const Navbar = () => {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md shadow-sm">
      <div className="container mx-auto px-4 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Brain className="h-8 w-8 text-theme-blue" />
          <span className="text-xl font-bold text-theme-blue">AI Buddy</span>
        </div>
        
        <nav className="hidden md:flex items-center space-x-8">
          <a href="#home" className="text-gray-600 hover:text-theme-blue transition-colors">หน้าหลัก</a>
          <a href="#features" className="text-gray-600 hover:text-theme-blue transition-colors">คุณสมบัติ</a>
          <a href="#personalities" className="text-gray-600 hover:text-theme-blue transition-colors">บุคลิกภาพ AI</a>
          <a href="#technology" className="text-gray-600 hover:text-theme-blue transition-colors">เทคโนโลยี</a>
          <a href="#contact" className="text-gray-600 hover:text-theme-blue transition-colors">ติดต่อ</a>
        </nav>
        
        <div className="hidden md:block">
          <Button className="bg-theme-blue hover:bg-blue-800 text-white">เริ่มต้นใช้งาน</Button>
        </div>
        
        <button className="md:hidden text-gray-700">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
      </div>
    </header>
  );
};

export default Navbar;
