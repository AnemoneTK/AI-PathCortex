# backend/src/services/advisor_service.py
import os
import sys
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

# เพิ่มโฟลเดอร์ปัจจุบันเข้าไปใน PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

from src.utils.vector_search import VectorSearch
from src.utils.logger import get_logger

# ใช้ logger ที่ตั้งค่าแล้ว
logger = get_logger("advisor_service")

class CareerAdvisorService:
    def __init__(self, vector_search: Optional[VectorSearch] = None):
        """
        เริ่มต้นการใช้งาน CareerAdvisorService
        
        Args:
            vector_search: instance ของ VectorSearch (ถ้าไม่ระบุจะสร้างใหม่)
        """
        if vector_search:
            self.vector_search = vector_search
        else:
            # สร้าง vector_search ใหม่
            project_root = Path(parent_dir)
            vector_db_dir = project_root / "data" / "vector_db"
            self.vector_search = VectorSearch(str(vector_db_dir))
        
        logger.info("CareerAdvisorService เริ่มต้นสำเร็จ")
    
    def get_advice(self, 
                  query: str, 
                  current_role: Optional[str] = None,
                  desired_role: Optional[str] = None,
                  experience_years: Optional[float] = None,
                  education: Optional[str] = None,
                  skills: Optional[List[str]] = None,
                  chat_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        ให้คำแนะนำเกี่ยวกับอาชีพตามคำถามที่ได้รับ
        
        Args:
            query: คำถามหรือประเด็นที่ต้องการคำแนะนำ
            current_role: ตำแหน่งงานปัจจุบัน (ถ้ามี)
            desired_role: ตำแหน่งงานที่ต้องการ (ถ้ามี)
            experience_years: จำนวนปีประสบการณ์ (ถ้ามี)
            education: ระดับการศึกษา (ถ้ามี)
            skills: ทักษะที่มี (ถ้ามี)
            chat_history: ประวัติการสนทนาก่อนหน้า (ถ้ามี)
            
        Returns:
            คำแนะนำและข้อมูลที่เกี่ยวข้อง
        """
        logger.info(f"ได้รับคำถาม: {query}")
        
        # ค้นหาคำแนะนำที่เกี่ยวข้อง
        relevant_advices = self.vector_search.search_career_advices(query, limit=3)
        
        # ค้นหาอาชีพที่เกี่ยวข้อง
        relevant_jobs = []
        if desired_role:
            relevant_jobs = self.vector_search.search_jobs(desired_role, limit=3)
        
        # สร้าง prompt สำหรับ LLM
        prompt = self._create_llm_prompt(
            query=query,
            current_role=current_role,
            desired_role=desired_role,
            experience_years=experience_years,
            education=education,
            skills=skills,
            relevant_advices=relevant_advices,
            relevant_jobs=relevant_jobs,
            chat_history=chat_history
        )
        
        # ในตัวอย่างนี้ เราจะจำลองการเรียกใช้ LLM
        # ในการใช้งานจริง คุณจะต้องส่ง prompt ไปยัง LLM API (เช่น OpenAI)
        response = self._simulate_llm_response(prompt)
        
        # จัดเตรียมผลลัพธ์
        result = {
            "response": response,
            "suggested_jobs": relevant_jobs[:3] if relevant_jobs else None,
            "learning_resources": self._get_learning_resources(desired_role) if desired_role else None,
            "salary_insights": self._get_salary_insights(desired_role) if desired_role else None
        }
        
        logger.info(f"ส่งคำแนะนำสำเร็จ")
        return result
    
    def _create_llm_prompt(self,
                          query: str,
                          current_role: Optional[str],
                          desired_role: Optional[str],
                          experience_years: Optional[float],
                          education: Optional[str],
                          skills: Optional[List[str]],
                          relevant_advices: List[Dict[str, Any]],
                          relevant_jobs: List[Dict[str, Any]],
                          chat_history: Optional[List[Dict[str, str]]]) -> str:
        """สร้าง prompt สำหรับส่งไปยัง LLM"""
        prompt = f"คำถาม: {query}\n\n"
        
        # เพิ่มข้อมูลผู้ใช้
        prompt += "ข้อมูลผู้ใช้:\n"
        if current_role:
            prompt += f"- ตำแหน่งงานปัจจุบัน: {current_role}\n"
        if desired_role:
            prompt += f"- ตำแหน่งงานที่ต้องการ: {desired_role}\n"
        if experience_years:
            prompt += f"- ประสบการณ์: {experience_years} ปี\n"
        if education:
            prompt += f"- การศึกษา: {education}\n"
        if skills:
            prompt += f"- ทักษะ: {', '.join(skills)}\n"
        prompt += "\n"
        
        # เพิ่มข้อมูลคำแนะนำที่เกี่ยวข้อง
        if relevant_advices:
            prompt += "คำแนะนำที่เกี่ยวข้อง:\n"
            for i, advice in enumerate(relevant_advices):
                prompt += f"คำแนะนำ {i+1}: {advice['title']}\n"
                prompt += f"{advice['text_preview'][:500]}...\n\n"
        
        # เพิ่มข้อมูลอาชีพที่เกี่ยวข้อง
        if relevant_jobs:
            prompt += "อาชีพที่เกี่ยวข้อง:\n"
            for i, job in enumerate(relevant_jobs):
                prompt += f"อาชีพ {i+1}: {job['title']}\n"
                if 'description' in job and job['description']:
                    prompt += f"คำอธิบาย: {job['description'][:300]}...\n"
                if 'skills' in job and job['skills']:
                    prompt += f"ทักษะที่ต้องการ: {', '.join(job['skills'][:5])}\n"
                if 'salary_ranges' in job and job['salary_ranges']:
                    salary_range = job['salary_ranges'][0]
                    prompt += f"เงินเดือน (ประสบการณ์ {salary_range.get('experience', 'N/A')}): {salary_range.get('salary', 'N/A')}\n"
                prompt += "\n"
        
        # เพิ่มประวัติการสนทนา
        if chat_history:
            prompt += "ประวัติการสนทนา:\n"
            for msg in chat_history[-3:]:  # เอาเฉพาะ 3 ข้อความล่าสุด
                role = "ผู้ใช้" if msg.get("role") == "user" else "แชทบอท"
                prompt += f"{role}: {msg.get('content', '')}\n"
            prompt += "\n"
        
        # คำแนะนำในการตอบ
        prompt += """
โปรดให้คำแนะนำที่เป็นประโยชน์และตรงประเด็นกับคำถามของผู้ใช้ โดยอ้างอิงจากข้อมูลที่ให้มา

คำตอบควรมีลักษณะดังนี้:
1. ตอบคำถามโดยตรงอย่างชัดเจน
2. ให้คำแนะนำที่ปฏิบัติได้จริง
3. อ้างอิงข้อมูลที่เกี่ยวข้องจากคำแนะนำและข้อมูลอาชีพที่ให้มา
4. ใช้ภาษาที่เป็นมิตร เข้าใจง่าย และให้กำลังใจ
5. หากมีข้อมูลไม่เพียงพอ ให้แนะนำว่าผู้ใช้ควรหาข้อมูลเพิ่มเติมในเรื่องใดบ้าง

คำตอบ:
"""
        return prompt
    
    def _simulate_llm_response(self, prompt: str) -> str:
        """จำลองการตอบกลับจาก LLM (ในการใช้งานจริงจะส่งไปยัง LLM API)"""
        # ในที่นี้เป็นเพียงตัวอย่าง ในการใช้งานจริงคุณจะต้องเรียกใช้ LLM API
        logger.info("กำลังจำลองการตอบกลับจาก LLM...")
        
        # ตัวอย่างการตอบกลับ
        response = """
สวัสดีครับ ผมยินดีให้คำแนะนำเกี่ยวกับการพัฒนาอาชีพของคุณ

จากคำถามของคุณและข้อมูลที่คุณให้มา ผมขอแนะนำดังนี้:

1. การพัฒนาทักษะที่จำเป็น
   - ควรเน้นพัฒนาทักษะทางเทคนิคที่เกี่ยวข้องกับตำแหน่งที่คุณสนใจ
   - เรียนรู้เทคโนโลยีใหม่ๆ อยู่เสมอเพื่อไม่ให้ตกเทรนด์

2. การเตรียมตัวสมัครงาน
   - เขียน Resume ที่โดดเด่น ไม่ลอกแบบคนอื่น
   - นำเสนอจุดเด่นและประสบการณ์ที่สอดคล้องกับตำแหน่งที่สมัคร

3. การพัฒนาตนเองอย่างต่อเนื่อง
   - เรียนรู้ภาษาต่างประเทศเพิ่มเติม
   - เข้าร่วมคอร์สเรียนออนไลน์หรือเวิร์คช็อปที่เกี่ยวข้อง

ผมหวังว่าคำแนะนำนี้จะเป็นประโยชน์กับคุณ หากมีคำถามเพิ่มเติม ไม่ว่าจะเป็นเรื่องการสัมภาษณ์งาน หรือการพัฒนาทักษะเฉพาะทาง ผมยินดีให้คำแนะนำเพิ่มเติมครับ
"""
        return response
    
    def _get_learning_resources(self, role: str) -> List[Dict[str, str]]:
        """รวบรวมแหล่งเรียนรู้ที่เกี่ยวข้องกับอาชีพ"""
        # ในที่นี้เป็นเพียงตัวอย่าง ในการใช้งานจริงอาจดึงจากฐานข้อมูล
        return [
            {
                "title": f"คอร์สเรียนออนไลน์เกี่ยวกับ {role}",
                "url": "https://www.example.com/courses"
            },
            {
                "title": "แหล่งเรียนรู้ฟรีสำหรับนักพัฒนา",
                "url": "https://www.example.com/free-resources"
            },
            {
                "title": "หนังสือแนะนำสำหรับผู้เริ่มต้น",
                "url": "https://www.example.com/books"
            }
        ]
    
    def _get_salary_insights(self, role: str) -> Dict[str, Any]:
        """รวบรวมข้อมูลเงินเดือนสำหรับอาชีพที่เกี่ยวข้อง"""
        # ในที่นี้เป็นเพียงตัวอย่าง ในการใช้งานจริงอาจดึงจากฐานข้อมูล
        return {
            "role": role,
            "ranges": [
                {"experience": "0-1 ปี", "range": "20,000 - 30,000 บาท"},
                {"experience": "1-3 ปี", "range": "30,000 - 50,000 บาท"},
                {"experience": "3-5 ปี", "range": "50,000 - 80,000 บาท"},
                {"experience": "5+ ปี", "range": "80,000 - 150,000 บาท"}
            ],
            "factors": [
                "ประสบการณ์",
                "ทักษะเฉพาะทาง",
                "ภาษาต่างประเทศ",
                "ขนาดบริษัท",
                "ที่ตั้งของบริษัท"
            ]
        }