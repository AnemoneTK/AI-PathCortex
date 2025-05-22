// frontend/src/components/chat/UserProfileModal.jsx
"use client"

import { useState, useEffect } from 'react'
import { X, User } from 'lucide-react'

export default function UserProfileModal({ isOpen, onClose }) {
const BASE_URL = process.env.NEXT_PUBLIC_API_BASE;

  const [userData, setUserData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (isOpen) {
      fetchUserData()
    }
  }, [isOpen])

  const fetchUserData = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${BASE_URL}/registration/user-info`)
          const text = await response.text();
console.log("📦 Raw response:", text);

      
      if (!response.ok) {
        throw new Error(`API responded with status: ${response.status}`)
      }
      
      const data = await response.json()
      setUserData(data)
    } catch (error) {
      console.error('Error fetching user data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-lg w-full max-w-md max-h-[80vh] overflow-y-auto">
        <div className="sticky top-0 bg-white p-4 border-b flex justify-between items-center">
          <h2 className="text-xl font-bold">ข้อมูลผู้ใช้</h2>
          <button 
            onClick={onClose}
            className="p-1 rounded-full hover:bg-gray-100 transition-colors"
          >
            <X />
          </button>
        </div>
        
        <div className="p-4">
          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary mx-auto"></div>
              <p className="mt-4 text-gray-600">กำลังโหลดข้อมูล...</p>
            </div>
          ) : userData ? (
            <div className="space-y-6">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
                  <User className="h-8 w-8 text-blue-600" />
                </div>
                <div>
                  <h3 className="text-xl font-bold">{userData.name}</h3>
                  <p className="text-gray-600">
                    {userData.institution && `${userData.institution} • `}
                    {userData.education_status === 'student' ? `นักศึกษาชั้นปีที่ ${userData.year}` : 
                     userData.education_status === 'graduate' ? 'จบการศึกษา' : 'ทำงานแล้ว'}
                  </p>
                </div>
              </div>
              
              {userData.skills && userData.skills.length > 0 && (
                <div>
                  <h4 className="font-bold text-gray-700 mb-2">ทักษะ</h4>
                  <div className="flex flex-wrap gap-2">
                    {userData.skills.map((skill, index) => (
                      <span 
                        key={index} 
                        className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                      >
                        {skill.name} ({skill.proficiency}/5)
                      </span>
                    ))}
                  </div>
                </div>
              )}
              
              {userData.programming_languages && userData.programming_languages.length > 0 && (
                <div>
                  <h4 className="font-bold text-gray-700 mb-2">ภาษาโปรแกรม</h4>
                  <div className="flex flex-wrap gap-2">
                    {userData.programming_languages.map((lang, index) => (
                      <span 
                        key={index} 
                        className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm"
                      >
                        {lang.name} ({lang.proficiency}/5)
                      </span>
                    ))}
                  </div>
                </div>
              )}
              
              {userData.tools && userData.tools.length > 0 && (
                <div>
                  <h4 className="font-bold text-gray-700 mb-2">เครื่องมือ</h4>
                  <div className="flex flex-wrap gap-2">
                    {userData.tools.map((tool, index) => (
                      <span 
                        key={index} 
                        className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm"
                      >
                        {tool.name} ({tool.proficiency}/5)
                      </span>
                    ))}
                  </div>
                </div>
              )}
              
              {userData.projects && userData.projects.length > 0 && (
                <div>
                  <h4 className="font-bold text-gray-700 mb-2">โปรเจกต์</h4>
                  <div className="space-y-3">
                    {userData.projects.map((project, index) => (
                      <div key={index} className="border border-gray-200 rounded-lg p-3">
                        <h5 className="font-medium">{project.name}</h5>
                        {project.role && <p className="text-sm text-blue-600">{project.role}</p>}
                        {project.description && <p className="text-sm text-gray-600 mt-1">{project.description}</p>}
                        {project.technologies && project.technologies.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {project.technologies.map((tech, i) => (
                              <span key={i} className="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded-full">
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
            </div>
          ) : (
            <div className="text-center py-8 text-gray-600">
              ไม่พบข้อมูลผู้ใช้
            </div>
          )}
        </div>
      </div>
    </div>
  )
}