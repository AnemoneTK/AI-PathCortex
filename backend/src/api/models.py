#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pydantic models for the Career AI Advisor API.

This module defines the data models used in the API.
"""

from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel, Field, constr, validator
from datetime import datetime, date
import uuid

from src.utils.config import PersonalityType, EducationStatus

#############################
# ข้อมูลพื้นฐาน
#############################

class QueryRequest(BaseModel):
    """คำขอสำหรับการค้นหาข้อมูล"""
    query: str = Field(..., description="คำค้นหาหรือคำถาม")
    limit: int = Field(5, description="จำนวนผลลัพธ์ที่ต้องการ", ge=1, le=50)

class QueryResult(BaseModel):
    """ผลลัพธ์จากการค้นหา"""
    content: str = Field(..., description="เนื้อหาที่ค้นพบ")
    job_title: str = Field(..., description="ชื่อตำแหน่งงาน")
    type: str = Field(..., description="ประเภทของข้อมูล (description, responsibilities, skills)")
    similarity: float = Field(..., description="คะแนนความใกล้เคียง")

class ChatRequest(BaseModel):
    """คำขอสำหรับการสนทนา"""
    query: str = Field(..., description="คำถามจากผู้ใช้")
    user_id: Optional[str] = Field(None, description="รหัสผู้ใช้ (ถ้ามี)")
    personality: PersonalityType = Field(PersonalityType.FRIENDLY, description="รูปแบบบุคลิกของ AI ที่ต้องการ")

class ChatResponse(BaseModel):
    """การตอบกลับการสนทนา"""
    answer: str = Field(..., description="คำตอบจากระบบ")
    sources: List[Dict[str, Any]] = Field([], description="แหล่งข้อมูลที่ใช้")

#############################
# ข้อมูลอาชีพ
#############################

class JobFilter(BaseModel):
    """ตัวกรองสำหรับการค้นหางาน"""
    skill: Optional[str] = Field(None, description="ทักษะที่ต้องการ")
    experience_range: Optional[str] = Field(None, description="ช่วงประสบการณ์")
    title: Optional[str] = Field(None, description="ชื่อตำแหน่งงาน")

class SalaryRange(BaseModel):
    """ข้อมูลช่วงเงินเดือน"""
    experience: str = Field(..., description="ประสบการณ์ (เช่น '0-2', '3-5')")
    salary: str = Field(..., description="ช่วงเงินเดือน (เช่น '30,000 - 50,000')")
    titles: Optional[List[str]] = Field(None, description="ตำแหน่งงานที่เกี่ยวข้อง (ถ้ามี)")

class JobResponse(BaseModel):
    """ข้อมูลอาชีพ"""
    id: str = Field(..., description="รหัสอาชีพ")
    titles: List[str] = Field(..., description="ชื่อตำแหน่งงาน")
    description: str = Field(..., description="คำอธิบายอาชีพ")
    skills: List[str] = Field([], description="ทักษะที่ต้องการ")
    responsibilities: List[str] = Field([], description="ความรับผิดชอบ")
    salary_ranges: List[SalaryRange] = Field([], description="ข้อมูลเงินเดือน")
    education_requirements: List[str] = Field([], description="ข้อกำหนดด้านการศึกษา")

class JobSummary(BaseModel):
    """ข้อมูลสรุปอาชีพ"""
    id: str = Field(..., description="รหัสอาชีพ")
    title: str = Field(..., description="ชื่อตำแหน่งงาน")

#############################
# ข้อมูลผู้ใช้
#############################

class UserSkill(BaseModel):
    """ข้อมูลทักษะของผู้ใช้"""
    name: str = Field(..., description="ชื่อทักษะ")
    proficiency: int = Field(1, ge=1, le=5, description="ระดับความชำนาญ (1-5)")

class UserProject(BaseModel):
    """ข้อมูลโปรเจกต์ของผู้ใช้"""
    name: str = Field(..., description="ชื่อโปรเจกต์")
    description: str = Field(..., description="คำอธิบายโปรเจกต์")
    technologies: List[str] = Field([], description="เทคโนโลยีที่ใช้")
    role: Optional[str] = Field(None, description="บทบาทในโปรเจกต์")
    url: Optional[str] = Field(None, description="URL ของโปรเจกต์ (ถ้ามี)")

class UserWorkExperience(BaseModel):
    """ข้อมูลประสบการณ์ทำงานของผู้ใช้"""
    title: str = Field(..., description="ตำแหน่งงาน")
    company: str = Field(..., description="ชื่อบริษัท")
    start_date: str = Field(..., description="วันที่เริ่มงาน (YYYY-MM)")
    end_date: Optional[str] = Field(None, description="วันที่สิ้นสุดการทำงาน (YYYY-MM หรือ 'Present')")
    description: Optional[str] = Field(None, description="รายละเอียดงาน")

class UserCreate(BaseModel):
    """ข้อมูลสำหรับสร้างผู้ใช้ใหม่"""
    name: str = Field(..., description="ชื่อผู้ใช้")
    institution: Optional[str] = Field(None, description="สถาบันการศึกษา")
    education_status: EducationStatus = Field(EducationStatus.STUDENT, description="สถานะการศึกษา")
    year: Optional[int] = Field(None, description="ชั้นปีที่กำลังศึกษา (ถ้ามี)")
    skills: List[UserSkill] = Field([], description="ทักษะที่มี")
    programming_languages: List[str] = Field([], description="ภาษาโปรแกรมที่ใช้ได้")
    tools: List[str] = Field([], description="เครื่องมือที่ใช้ได้")
    projects: List[UserProject] = Field([], description="โปรเจกต์ที่เคยทำ")
    work_experiences: List[UserWorkExperience] = Field([], description="ประสบการณ์ทำงาน")

class UserUpdate(BaseModel):
    """ข้อมูลสำหรับอัปเดตผู้ใช้"""
    name: Optional[str] = Field(None, description="ชื่อผู้ใช้")
    institution: Optional[str] = Field(None, description="สถาบันการศึกษา")
    education_status: Optional[EducationStatus] = Field(None, description="สถานะการศึกษา")
    year: Optional[int] = Field(None, description="ชั้นปีที่กำลังศึกษา")
    skills: Optional[List[UserSkill]] = Field(None, description="ทักษะที่มี")
    programming_languages: Optional[List[str]] = Field(None, description="ภาษาโปรแกรมที่ใช้ได้")
    tools: Optional[List[str]] = Field(None, description="เครื่องมือที่ใช้ได้")
    projects: Optional[List[UserProject]] = Field(None, description="โปรเจกต์ที่เคยทำ")
    work_experiences: Optional[List[UserWorkExperience]] = Field(None, description="ประสบการณ์ทำงาน")

class User(BaseModel):
    """ข้อมูลผู้ใช้"""
    id: str = Field(..., description="รหัสผู้ใช้")
    name: str = Field(..., description="ชื่อผู้ใช้")
    institution: Optional[str] = Field(None, description="สถาบันการศึกษา")
    education_status: EducationStatus = Field(EducationStatus.STUDENT, description="สถานะการศึกษา")
    year: Optional[int] = Field(None, description="ชั้นปีที่กำลังศึกษา")
    skills: List[UserSkill] = Field([], description="ทักษะที่มี")
    programming_languages: List[str] = Field([], description="ภาษาโปรแกรมที่ใช้ได้")
    tools: List[str] = Field([], description="เครื่องมือที่ใช้ได้")
    projects: List[UserProject] = Field([], description="โปรเจกต์ที่เคยทำ")
    work_experiences: List[UserWorkExperience] = Field([], description="ประสบการณ์ทำงาน")
    resume_path: Optional[str] = Field(None, description="พาธของไฟล์ Resume")
    created_at: str = Field(..., description="วันที่สร้าง")
    updated_at: str = Field(..., description="วันที่อัปเดตล่าสุด")

    @validator('created_at', 'updated_at', pre=True, always=True)
    def default_datetime(cls, v):
        return v or datetime.now().isoformat()

class UserSummary(BaseModel):
    """ข้อมูลสรุปผู้ใช้"""
    id: str = Field(..., description="รหัสผู้ใช้") 
    name: str = Field(..., description="ชื่อผู้ใช้")
    institution: Optional[str] = Field(None, description="สถาบันการศึกษา")
    education_status: EducationStatus = Field(..., description="สถานะการศึกษา")

class ResumeUploadResponse(BaseModel):
    """ผลลัพธ์การอัปโหลดไฟล์ Resume"""
    success: bool = Field(..., description="สถานะความสำเร็จ")
    file_name: str = Field(..., description="ชื่อไฟล์")
    content_type: str = Field(..., description="ประเภทของไฟล์")
    message: str = Field(..., description="ข้อความแสดงผล")

#############################
# ข้อมูลการวิเคราะห์ Resume
#############################

class ResumeAnalysisRequest(BaseModel):
    """คำขอวิเคราะห์ Resume"""
    user_id: str = Field(..., description="รหัสผู้ใช้")

class ResumeAnalysisResponse(BaseModel):
    """ผลลัพธ์การวิเคราะห์ Resume"""
    success: bool = Field(..., description="สถานะความสำเร็จ")
    user_id: str = Field(..., description="รหัสผู้ใช้")
    analysis: str = Field(..., description="ผลการวิเคราะห์")
    suggested_jobs: List[JobSummary] = Field([], description="อาชีพที่แนะนำ")
    suggested_skills: List[str] = Field([], description="ทักษะที่แนะนำให้พัฒนา")
    message: str = Field(..., description="ข้อความแสดงผล")

#############################
# ข้อมูลประวัติการสนทนา
#############################

class ChatHistory(BaseModel):
    """ประวัติการสนทนา"""
    id: str = Field(..., description="รหัสการสนทนา")
    user_id: Optional[str] = Field(None, description="รหัสผู้ใช้ (ถ้ามี)")
    query: str = Field(..., description="คำถามจากผู้ใช้")
    answer: str = Field(..., description="คำตอบจากระบบ")
    personality: PersonalityType = Field(PersonalityType.FRIENDLY, description="รูปแบบบุคลิกที่ใช้")
    sources: List[Dict[str, Any]] = Field([], description="แหล่งข้อมูลที่ใช้")
    timestamp: str = Field(..., description="เวลาที่สนทนา")

    @validator('id', pre=True, always=True)
    def default_id(cls, v):
        return v or str(uuid.uuid4())

    @validator('timestamp', pre=True, always=True)
    def default_timestamp(cls, v):
        return v or datetime.now().isoformat()

class ChatHistoryResponse(BaseModel):
    """ผลลัพธ์การดึงประวัติการสนทนา"""
    user_id: Optional[str] = Field(None, description="รหัสผู้ใช้ (ถ้ามี)")
    history: List[ChatHistory] = Field([], description="ประวัติการสนทนา")
    count: int = Field(..., description="จำนวนประวัติการสนทนา")