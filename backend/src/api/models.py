# src/api/models.py

from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from uuid import uuid4

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
    """ทักษะของผู้ใช้"""
    name: str = Field(..., description="ชื่อทักษะ")
    proficiency: int = Field(1, ge=1, le=5, description="ระดับความชำนาญ (1-5)")

class UserProject(BaseModel):
    """โปรเจกต์ของผู้ใช้"""
    name: str = Field(..., description="ชื่อโปรเจกต์")
    description: Optional[str] = Field(None, description="คำอธิบายโปรเจกต์")
    technologies: List[str] = Field([], description="เทคโนโลยีที่ใช้")
    role: Optional[str] = Field(None, description="บทบาทในโปรเจกต์")
    url: Optional[str] = Field(None, description="URL ของโปรเจกต์ (ถ้ามี)")

class UserWorkExperience(BaseModel):
    """ประสบการณ์ทำงานของผู้ใช้"""
    title: str = Field(..., description="ตำแหน่งงาน")
    company: str = Field(..., description="ชื่อบริษัท")
    start_date: str = Field(..., description="วันที่เริ่มงาน (YYYY-MM)")
    end_date: Optional[str] = Field(None, description="วันที่สิ้นสุดการทำงาน (YYYY-MM หรือ 'Present')")
    description: Optional[str] = Field(None, description="รายละเอียดงาน")

class UserCreate(BaseModel):
    """ข้อมูลสำหรับสร้างผู้ใช้ใหม่"""
    name: str = Field(..., description="ชื่อผู้ใช้")
    institution: Optional[str] = Field(None, description="สถาบันการศึกษา")
    education_status: Optional[EducationStatus] = Field(EducationStatus.STUDENT, description="สถานะการศึกษา")
    year: Optional[int] = Field(None, description="ชั้นปีที่กำลังศึกษา (ถ้ามี)")
    skills: List[UserSkill] = Field([], description="ทักษะที่มี")
    programming_languages: List[UserSkill] = Field([], description="ภาษาโปรแกรมที่ใช้ได้")
    tools: List[UserSkill] = Field([], description="เครื่องมือที่ใช้ได้") 
    projects: List[UserProject] = Field([], description="โปรเจกต์ที่เคยทำ")
    work_experiences: List[UserWorkExperience] = Field([], description="ประสบการณ์ทำงาน")

class UserUpdate(BaseModel):
    """ข้อมูลสำหรับอัปเดตผู้ใช้"""
    name: Optional[str] = Field(None, description="ชื่อผู้ใช้")
    institution: Optional[str] = Field(None, description="สถาบันการศึกษา")
    education_status: Optional[EducationStatus] = Field(None, description="สถานะการศึกษา")
    year: Optional[int] = Field(None, description="ชั้นปีที่กำลังศึกษา")
    skills: Optional[List[UserSkill]] = Field(None, description="ทักษะที่มี")
    programming_languages: Optional[List[UserSkill]] = Field(None, description="ภาษาโปรแกรมที่ใช้ได้")
    tools: Optional[List[UserSkill]] = Field(None, description="เครื่องมือที่ใช้ได้")
    projects: Optional[List[UserProject]] = Field(None, description="โปรเจกต์ที่เคยทำ")
    work_experiences: Optional[List[UserWorkExperience]] = Field(None, description="ประสบการณ์ทำงาน")

class User(BaseModel):
    """ข้อมูลผู้ใช้"""
    id: str = Field(..., description="รหัสผู้ใช้")
    name: str = Field(..., description="ชื่อผู้ใช้")
    institution: Optional[str] = Field(None, description="สถาบันการศึกษา")
    education_status: Optional[EducationStatus] = Field(EducationStatus.STUDENT, description="สถานะการศึกษา")
    year: Optional[int] = Field(None, description="ชั้นปีที่กำลังศึกษา")
    skills: List[UserSkill] = Field([], description="ทักษะที่มี")
    programming_languages: List[UserSkill] = Field([], description="ภาษาโปรแกรมที่ใช้ได้")
    tools: List[UserSkill] = Field([], description="เครื่องมือที่ใช้ได้")
    projects: List[UserProject] = Field([], description="โปรเจกต์ที่เคยทำ")
    work_experiences: List[UserWorkExperience] = Field([], description="ประสบการณ์ทำงาน")
    resume_path: Optional[str] = Field(None, description="พาธของไฟล์ Resume")
    created_at: str = Field(..., description="วันที่สร้าง")
    updated_at: str = Field(..., description="วันที่อัปเดตล่าสุด")

    # เปลี่ยนจาก @validator เป็น @field_validator และเพิ่ม @classmethod
    @field_validator('created_at', 'updated_at', mode='before')
    @classmethod
    def default_datetime(cls, v):
        return v or datetime.now().isoformat()

class UserSummary(BaseModel):
    """ข้อมูลสรุปผู้ใช้"""
    id: str = Field(..., description="รหัสผู้ใช้") 
    name: str = Field(..., description="ชื่อผู้ใช้")
    institution: Optional[str] = Field(None, description="สถาบันการศึกษา")
    education_status: Optional[EducationStatus] = Field(None, description="สถานะการศึกษา")

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
# ข้อมูลการค้นหา
#############################

class SearchResult(BaseModel):
    """ผลลัพธ์การค้นหา"""
    id: str = Field(..., description="รหัสผลลัพธ์")
    title: str = Field(..., description="ชื่อผลลัพธ์")
    similarity_score: float = Field(..., description="คะแนนความเหมือน")
    type: str = Field(..., description="ประเภทของผลลัพธ์ (job, advice, user)")
    content: Dict[str, Any] = Field({}, description="เนื้อหาของผลลัพธ์")

class JobSearchResult(BaseModel):
    """ผลลัพธ์การค้นหาอาชีพ"""
    id: str = Field(..., description="รหัสอาชีพ")
    title: str = Field(..., description="ชื่อตำแหน่งงาน")
    description: str = Field(..., description="คำอธิบายอาชีพ")
    responsibilities: List[str] = Field([], description="ความรับผิดชอบ")
    skills: List[str] = Field([], description="ทักษะที่ต้องการ")
    salary_ranges: List[Dict[str, Any]] = Field([], description="ข้อมูลเงินเดือน")
    education_requirements: List[str] = Field([], description="ข้อกำหนดด้านการศึกษา")
    similarity_score: float = Field(..., description="คะแนนความเหมือน")

class AdviceSearchResult(BaseModel):
    """ผลลัพธ์การค้นหาคำแนะนำอาชีพ"""
    id: str = Field(..., description="รหัสคำแนะนำ")
    title: str = Field(..., description="หัวข้อคำแนะนำ")
    text_preview: str = Field(..., description="ตัวอย่างเนื้อหา")
    tags: List[str] = Field([], description="แท็ก")
    source: str = Field("", description="แหล่งที่มา")
    url: str = Field("", description="URL")
    similarity_score: float = Field(..., description="คะแนนความเหมือน")

class JobSearchQuery(BaseModel):
    """คำค้นหาอาชีพ"""
    query: str = Field(..., description="คำค้นหา")
    filters: Optional[Dict[str, Any]] = Field(None, description="ตัวกรอง")
    limit: int = Field(5, description="จำนวนผลลัพธ์")

class AdviceSearchQuery(BaseModel):
    """คำค้นหาคำแนะนำอาชีพ"""
    query: str = Field(..., description="คำค้นหา")
    filter_tags: Optional[List[str]] = Field(None, description="กรองตามแท็ก")
    limit: int = Field(5, description="จำนวนผลลัพธ์")

class CombinedSearchQuery(BaseModel):
    """คำค้นหาแบบรวม"""
    query: str = Field(..., description="คำค้นหา")
    limit: int = Field(5, description="จำนวนผลลัพธ์")

#############################
# ข้อมูลการสนทนา
#############################

class ChatMessage(BaseModel):
    """ข้อความการสนทนา"""
    role: str = Field(..., description="บทบาท (user, assistant)")
    content: str = Field(..., description="เนื้อหาข้อความ")
    timestamp: Optional[str] = Field(None, description="เวลาที่ส่งข้อความ")
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now().isoformat()
        super().__init__(**data)

class ChatRequest(BaseModel):
    """คำขอการสนทนา"""
    message: str = Field(..., description="ข้อความ")
    personality: PersonalityType = Field(PersonalityType.FRIENDLY, description="บุคลิกของ AI")
    use_combined_search: bool = Field(True, description="ใช้การค้นหาแบบรวมหรือไม่")
    use_fine_tuned: bool = Field(False, description="ใช้โมเดล fine-tuned หรือไม่")

class ChatHistory(BaseModel):
    """ประวัติการสนทนา"""
    id: str = Field(default_factory=lambda: str(uuid4()), description="รหัสการสนทนา")
    user_id: Optional[str] = Field(None, description="รหัสผู้ใช้ (ถ้ามี)")
    messages: List[ChatMessage] = Field([], description="ข้อความในการสนทนา")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="เวลาที่สนทนา")

class ChatResponse(BaseModel):
    """การตอบกลับการสนทนา"""
    chat_id: str = Field(..., description="รหัสการสนทนา")
    message: str = Field(..., description="ข้อความตอบกลับ")
    search_results: List[Union[Dict[str, Any], JobSearchResult, AdviceSearchResult]] = Field([], description="ผลลัพธ์การค้นหาที่เกี่ยวข้อง")