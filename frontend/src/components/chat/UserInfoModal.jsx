"use client"

import { X, User, Briefcase, Book, Code, WrenchIcon, FileText } from "lucide-react"
import { motion } from "framer-motion"

export default function UserInfoModal({ userData, onClose, darkMode = false }) {
  if (!userData) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <motion.div 
        className={`${darkMode ? 'bg-gray-800 text-white' : 'bg-white text-gray-800'} rounded-xl shadow-xl w-full max-w-md max-h-[90vh] overflow-auto`}
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.2 }}
      >
        {/* Header */}
        <div className={`p-4 border-b ${darkMode ? 'border-gray-700' : 'border-gray-200'} flex justify-between items-center sticky top-0 ${darkMode ? 'bg-gray-800' : 'bg-white'} z-10`}>
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <User className={`${darkMode ? 'text-blue-400' : 'text-blue-600'}`} />
            ข้อมูลผู้ใช้
          </h2>
          <button 
            onClick={onClose}
            className={`p-1 rounded-full ${darkMode ? 'hover:bg-gray-700 text-gray-300' : 'hover:bg-gray-100 text-gray-600'}`}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4">
          {/* ข้อมูลส่วนตัว */}
          <div className="mb-6">
            <div className={`h-20 w-20 rounded-full ${darkMode ? 'bg-blue-900' : 'bg-blue-100'} mx-auto flex items-center justify-center mb-4`}>
              <User className={`h-10 w-10 ${darkMode ? 'text-blue-400' : 'text-blue-600'}`} />
            </div>
            <h3 className="text-xl font-bold text-center">{userData.name}</h3>
            <p className={`text-center ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
              {userData.institution || "ไม่ระบุสถาบัน"} • 
              {userData.education_status === 'student' 
                ? ` นักศึกษาชั้นปีที่ ${userData.year}` 
                : userData.education_status === 'graduate' 
                  ? ' จบการศึกษา' 
                  : ' ทำงานแล้ว'}
            </p>
          </div>

          {/* ทักษะ */}
          <div className={`mb-4 p-4 rounded-lg ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
            <h4 className="font-semibold flex items-center gap-1 mb-2">
              <Briefcase className={`h-4 w-4 ${darkMode ? 'text-blue-400' : 'text-blue-600'}`} />
              ทักษะ
            </h4>
            <div className="flex flex-wrap gap-2">
              {userData.skills && userData.skills.length > 0 ? (
                userData.skills.map((skill, index) => (
                  <span 
                    key={index} 
                    className={`px-2 py-1 text-xs rounded-full ${
                      darkMode 
                        ? 'bg-blue-900 text-blue-200' 
                        : 'bg-blue-100 text-blue-800'
                    }`}
                  >
                    {typeof skill === 'object' 
                      ? `${skill.name} (${skill.proficiency})` 
                      : skill}
                  </span>
                ))
              ) : (
                <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>ไม่มีข้อมูลทักษะ</p>
              )}
            </div>
          </div>

          {/* ภาษาโปรแกรม */}
          <div className={`mb-4 p-4 rounded-lg ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
            <h4 className="font-semibold flex items-center gap-1 mb-2">
              <Code className={`h-4 w-4 ${darkMode ? 'text-blue-400' : 'text-blue-600'}`} />
              ภาษาโปรแกรม
            </h4>
            <div className="flex flex-wrap gap-2">
              {userData.programming_languages && userData.programming_languages.length > 0 ? (
                userData.programming_languages.map((lang, index) => (
                  <span 
                    key={index} 
                    className={`px-2 py-1 text-xs rounded-full ${
                      darkMode 
                        ? 'bg-green-900 text-green-200' 
                        : 'bg-green-100 text-green-800'
                    }`}
                  >
                    {typeof lang === 'object' 
                      ? `${lang.name} (${lang.proficiency})` 
                      : lang}
                  </span>
                ))
              ) : (
                <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>ไม่มีข้อมูลภาษาโปรแกรม</p>
              )}
            </div>
          </div>

          {/* เครื่องมือ */}
          <div className={`mb-4 p-4 rounded-lg ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
            <h4 className="font-semibold flex items-center gap-1 mb-2">
              <WrenchIcon className={`h-4 w-4 ${darkMode ? 'text-blue-400' : 'text-blue-600'}`} />
              เครื่องมือ
            </h4>
            <div className="flex flex-wrap gap-2">
              {userData.tools && userData.tools.length > 0 ? (
                userData.tools.map((tool, index) => (
                  <span 
                    key={index} 
                    className={`px-2 py-1 text-xs rounded-full ${
                      darkMode 
                        ? 'bg-purple-900 text-purple-200' 
                        : 'bg-purple-100 text-purple-800'
                    }`}
                  >
                    {typeof tool === 'object' 
                      ? `${tool.name} (${tool.proficiency})` 
                      : tool}
                  </span>
                ))
              ) : (
                <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>ไม่มีข้อมูลเครื่องมือ</p>
              )}
            </div>
          </div>

          {/* โปรเจกต์ */}
          {userData.projects && userData.projects.length > 0 && (
            <div className={`mb-4 p-4 rounded-lg ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
              <h4 className="font-semibold flex items-center gap-1 mb-2">
                <Book className={`h-4 w-4 ${darkMode ? 'text-blue-400' : 'text-blue-600'}`} />
                โปรเจกต์
              </h4>
              <div className="space-y-3">
                {userData.projects.map((project, index) => (
                  <div 
                    key={index} 
                    className={`p-3 rounded-lg ${darkMode ? 'bg-gray-800 border-gray-600' : 'bg-white border-gray-200'} border`}
                  >
                    <h5 className="font-medium">{project.name}</h5>
                    {project.description && (
                      <p className={`text-sm mt-1 ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                        {project.description}
                      </p>
                    )}
                    {project.technologies && project.technologies.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {project.technologies.map((tech, techIndex) => (
                          <span 
                            key={techIndex} 
                            className={`text-xs px-1.5 py-0.5 rounded ${
                              darkMode 
                                ? 'bg-gray-700 text-gray-300' 
                                : 'bg-gray-100 text-gray-800'
                            }`}
                          >
                            {tech}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Resume (ถ้ามี) */}
          {userData.resume_path && (
            <div className={`mb-4 p-4 rounded-lg ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
              <h4 className="font-semibold flex items-center gap-1 mb-2">
                <FileText className={`h-4 w-4 ${darkMode ? 'text-blue-400' : 'text-blue-600'}`} />
                Resume
              </h4>
              <p className={`text-sm ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                มีไฟล์ Resume อัปโหลด
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className={`p-4 border-t ${darkMode ? 'border-gray-700' : 'border-gray-200'} sticky bottom-0 ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
          <button 
            onClick={onClose}
            className={`w-full py-2 px-4 rounded-lg ${
              darkMode 
                ? 'bg-gray-700 text-white hover:bg-gray-600' 
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            } transition-colors`}
          >
            ปิด
          </button>
        </div>
      </motion.div>
    </div>
  )
}