# backend/src/utils/vector_search.py
import os
import json
import numpy as np
import faiss
import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import sys
from colorama import init, Fore, Style
from difflib import get_close_matches

# เริ่มต้นใช้งาน colorama
init(autoreset=True)

# เพิ่มโฟลเดอร์ปัจจุบันเข้าไปใน PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

try:
    from src.utils.logger import get_logger
    # ใช้ logger ที่ตั้งค่าแล้ว
    logger = get_logger("vector_search")
except ImportError:
    import logging
    # ตั้งค่า logger ใหม่
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("vector_search")

class VectorSearch:
    def __init__(self, vector_db_dir: str, embedding_model=None):
        """
        เริ่มต้นการใช้งาน VectorSearch
        
        Args:
            vector_db_dir: โฟลเดอร์ของฐานข้อมูล vector
            embedding_model: โมเดลสำหรับสร้าง embeddings (ถ้าไม่ระบุจะใช้การจำลอง vector)
        """
        # ไฟล์สำหรับคำศัพท์ที่ใช้บ่อยในอาชีพไอที
        self.tech_keywords = set([
            "programmer", "developer", "software", "web", "frontend", "backend", 
            "fullstack", "full stack", "data scientist", "data analyst", "devops", 
            "database", "engineer", "ux", "ui", "python", "java", "javascript", 
            "react", "angular", "node", "typescript", "c#", "c++", "php", "ruby", 
            "software engineer", "project manager", "scrum master", "product owner",
            "mobile", "android", "ios", "cloud", "aws", "azure", "network",
            "security", "system", "administrator", "qa", "testing"
        ])
        
        # คำที่เกี่ยวข้องกับการสืบค้นข้อมูลอาชีพ
        self.job_query_keywords = set([
            "เงินเดือน", "หน้าที่", "ทักษะ", "สกิล", "ความรับผิดชอบ", "การศึกษา", 
            "คุณสมบัติ", "ประสบการณ์", "ข้อดี", "ข้อเสีย", "สายงาน", "สายอาชีพ",
            "salary", "responsibility", "skill", "education", "qualification", 
            "experience", "pros", "cons", "career path"
        ])
        
        # คำที่เกี่ยวข้องกับ resume และการสมัครงาน
        self.resume_keywords = set([
            "resume", "เรซูเม่", "เรซูเม", "cv", "ประวัติ", "สมัครงาน", "สัมภาษณ์",
            "interview", "application", "portfolio", "พอร์ตโฟลิโอ", "job hunt",
            "career", "อาชีพ", "การเขียน", "writing", "template", "แม่แบบ", "ตัวอย่าง"
        ])
        
        # คำที่เกี่ยวกับผู้ใช้หรือการค้นหาผู้ใช้
        self.user_keywords = set([
            "user", "ผู้ใช้", "profile", "โปรไฟล์", "นักศึกษา", "student", 
            "จบใหม่", "freshly graduated", "ประวัติส่วนตัว", "ข้อมูลส่วนตัว"
        ])
        
        # คำที่อาจสะกดผิด และคำที่ถูกต้อง
        self.common_misspellings = {
            "badkend": "backend",
            "frentend": "frontend",
            "frontned": "frontend",
            "recat": "react",
            "javascrip": "javascript",
            "javascrpit": "javascript",
            "เดเวลอปเปอ": "developer",
            "เดเวลอปเป้อ": "developer",
            "เดเวลอปเปอร์": "developer",
            "โปรเเกรมเมอ": "programmer",
            "โปรแกรมเมอ": "programmer",
            "เรซูเม": "resume",
            "เรซูเม่": "resume",
            "เรซูม่": "resume",
            "เร้ซูเม่": "resume"
        }
        
        try:
            from sentence_transformers import SentenceTransformer
            
            # ถ้าไม่มี embedding_model ให้โหลดโมเดลเริ่มต้น
            if embedding_model is None:
                default_model = 'intfloat/e5-small-v2'
                embedding_model = SentenceTransformer(default_model)
                print(f"{Fore.CYAN}📚 โหลดโมเดล embedding เริ่มต้น: {default_model}{Style.RESET_ALL}")
        except ImportError:
            print(f"{Fore.YELLOW}⚠️ ไม่สามารถโหลด SentenceTransformer ได้ จะใช้การจำลอง vector{Style.RESET_ALL}")
            embedding_model = None

        self.embedding_model = embedding_model

        print(f"{Fore.CYAN}⚙️ กำลังเริ่มต้น VectorSearch...{Style.RESET_ALL}")
        self.vector_db_dir = vector_db_dir
        self.embedding_model = embedding_model
        
        # โฟลเดอร์สำหรับแต่ละประเภทข้อมูล
        self.job_knowledge_dir = os.path.join(vector_db_dir, "job_knowledge")
        self.career_advice_dir = os.path.join(vector_db_dir, "career_advice")
        self.combined_knowledge_dir = os.path.join(vector_db_dir, "combined_knowledge")
        
        # ไฟล์ FAISS index และ metadata
        self.job_index_file = os.path.join(self.job_knowledge_dir, "faiss_index.bin")
        self.job_metadata_file = os.path.join(self.job_knowledge_dir, "metadata.json")
        
        self.advice_index_file = os.path.join(self.career_advice_dir, "faiss_index.bin")
        self.advice_metadata_file = os.path.join(self.career_advice_dir, "metadata.json")
        
        self.combined_index_file = os.path.join(self.combined_knowledge_dir, "faiss_index.bin")
        self.combined_metadata_file = os.path.join(self.combined_knowledge_dir, "metadata.json")
        
        print(f"{Fore.CYAN}📂 โฟลเดอร์ฐานข้อมูล vector: {vector_db_dir}")
        print(f"{Fore.CYAN}📄 ไฟล์ job index: {self.job_index_file}")
        print(f"{Fore.CYAN}📄 ไฟล์ job metadata: {self.job_metadata_file}")
        print(f"{Fore.CYAN}📄 ไฟล์ advice index: {self.advice_index_file}")
        print(f"{Fore.CYAN}📄 ไฟล์ advice metadata: {self.advice_metadata_file}")
        print(f"{Fore.CYAN}📄 ไฟล์ combined index: {self.combined_index_file}")
        print(f"{Fore.CYAN}📄 ไฟล์ combined metadata: {self.combined_metadata_file}{Style.RESET_ALL}")
        
        # โหลด metadata
        self.job_metadata = self._load_metadata(self.job_metadata_file)
        self.advice_metadata = self._load_metadata(self.advice_metadata_file)
        self.combined_metadata = self._load_metadata(self.combined_metadata_file)
        
        # ดึงข้อมูลที่จัดเก็บไว้
        self.processed_data_dir = os.path.join(project_root, "data", "processed")
        try:
            # ลองใช้ค่าจาก config ถ้ามี
            from src.utils.config import NORMALIZED_JOBS_DIR
            self.normalized_jobs_dir = NORMALIZED_JOBS_DIR
        except (ImportError, AttributeError):
            # ถ้าไม่มีให้ใช้ค่าเริ่มต้น
            self.normalized_jobs_dir = os.path.join(self.processed_data_dir, "normalized_jobs")
        
        # สร้าง mapping ของ job_id -> job_data
        self.jobs_data = self._load_jobs_data()
        
        # ถ้าไม่มีข้อมูลเลย ให้โหลดจาก embedding_data.json แทน
        if len(self.job_metadata) == 0 and len(self.advice_metadata) == 0 and len(self.combined_metadata) == 0:
            print(f"{Fore.YELLOW}⚠️ ไม่พบข้อมูล metadata จะลองโหลดจาก embedding_data.json แทน{Style.RESET_ALL}")
            self._load_fallback_metadata()
        
        if len(self.job_metadata) > 0 and len(self.advice_metadata) > 0:
            print(f"{Fore.GREEN}✅ VectorSearch เริ่มต้นสำเร็จ: {len(self.job_metadata)} job metadata, {len(self.advice_metadata)} advice metadata{Style.RESET_ALL}")
            if len(self.combined_metadata) > 0:
                print(f"{Fore.GREEN}✅ พบฐานข้อมูลรวม: {len(self.combined_metadata)} combined metadata{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}⚠️ VectorSearch เริ่มต้นสำเร็จ แต่อาจไม่มีข้อมูล: {len(self.job_metadata)} job metadata, {len(self.advice_metadata)} advice metadata{Style.RESET_ALL}")
        
        logger.info(f"VectorSearch เริ่มต้นสำเร็จ: {len(self.job_metadata)} job metadata, {len(self.advice_metadata)} advice metadata, {len(self.combined_metadata)} combined metadata")
    
    def _load_fallback_metadata(self):
        """โหลดข้อมูล metadata จากไฟล์ fallback (embedding_data.json)"""
        try:
            # ลองหาไฟล์ embedding_data.json ในโฟลเดอร์ data/embedding
            embedding_data_path = os.path.join(project_root, "data", "embedding", "embedding_data.json")
            advice_data_path = os.path.join(project_root, "data", "embedding", "career_advices_embeddings.json")
            
            # โหลดข้อมูลอาชีพ
            if os.path.exists(embedding_data_path):
                print(f"{Fore.CYAN}📄 พบไฟล์ fallback สำหรับข้อมูลอาชีพ: {embedding_data_path}{Style.RESET_ALL}")
                with open(embedding_data_path, 'r', encoding='utf-8') as f:
                    fallback_data = json.load(f)
                    self.job_metadata = fallback_data
                    
                    # เพิ่มข้อมูลอาชีพเข้าไปใน jobs_data
                    for job in fallback_data:
                        job_id = job.get("id")
                        if job_id:
                            self.jobs_data[job_id] = job.get("metadata", {})
                
                print(f"{Fore.GREEN}✅ โหลดข้อมูลอาชีพจาก fallback สำเร็จ: {len(self.job_metadata)} รายการ{Style.RESET_ALL}")
            
            # โหลดข้อมูลคำแนะนำ
            if os.path.exists(advice_data_path):
                print(f"{Fore.CYAN}📄 พบไฟล์ fallback สำหรับข้อมูลคำแนะนำ: {advice_data_path}{Style.RESET_ALL}")
                with open(advice_data_path, 'r', encoding='utf-8') as f:
                    self.advice_metadata = json.load(f)
                
                print(f"{Fore.GREEN}✅ โหลดข้อมูลคำแนะนำจาก fallback สำเร็จ: {len(self.advice_metadata)} รายการ{Style.RESET_ALL}")
            
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการโหลดข้อมูล fallback: {str(e)}")
            print(f"{Fore.RED}❌ เกิดข้อผิดพลาดในการโหลดข้อมูล fallback: {str(e)}{Style.RESET_ALL}")
    
    def _load_metadata(self, metadata_file: str) -> List[Dict[str, Any]]:
        """โหลดข้อมูล metadata จากไฟล์"""
        try:
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # ตรวจสอบโครงสร้างข้อมูล
                    if isinstance(data, dict) and "job_data" in data:
                        # กรณีโครงสร้างแบบของ JobDataNormalizer
                        return data.get("job_data", [])
                    elif isinstance(data, dict) and "advice_data" in data:
                        # กรณีโครงสร้างแบบของ JobDataNormalizer สำหรับคำแนะนำ
                        return data.get("advice_data", [])
                    else:
                        # กรณีเป็น list
                        return data
            else:
                logger.warning(f"ไม่พบไฟล์ metadata: {metadata_file}")
                print(f"{Fore.YELLOW}⚠️ ไม่พบไฟล์ metadata: {metadata_file}{Style.RESET_ALL}")
                return []
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการโหลด metadata: {str(e)}")
            print(f"{Fore.RED}❌ เกิดข้อผิดพลาดในการโหลด metadata: {str(e)}{Style.RESET_ALL}")
            return []
    
    def _load_jobs_data(self) -> Dict[str, Any]:
        """โหลดข้อมูลอาชีพทั้งหมด"""
        jobs_data = {}
        
        try:
            if os.path.exists(self.normalized_jobs_dir):
                for filename in os.listdir(self.normalized_jobs_dir):
                    if filename.endswith('.json'):
                        file_path = os.path.join(self.normalized_jobs_dir, filename)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                job_data = json.load(f)
                                job_id = job_data.get('id')
                                if job_id:
                                    jobs_data[job_id] = job_data
                        except Exception as e:
                            logger.error(f"เกิดข้อผิดพลาดในการอ่านไฟล์ {file_path}: {str(e)}")
                            print(f"{Fore.RED}❌ เกิดข้อผิดพลาดในการอ่านไฟล์ {file_path}: {str(e)}{Style.RESET_ALL}")
            
            print(f"{Fore.GREEN}✅ โหลดข้อมูลอาชีพสำเร็จ: {len(jobs_data)} รายการ{Style.RESET_ALL}")
            logger.info(f"โหลดข้อมูลอาชีพสำเร็จ: {len(jobs_data)} รายการ")
            return jobs_data
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการโหลดข้อมูลอาชีพ: {str(e)}")
            print(f"{Fore.RED}❌ เกิดข้อผิดพลาดในการโหลดข้อมูลอาชีพ: {str(e)}{Style.RESET_ALL}")
            return {}
    
    def _normalize_query(self, query: str) -> Tuple[str, List[str]]:
        """
        ทำความสะอาดคำค้นหาและแยกคำสำคัญ
        
        Args:
            query: คำค้นหา
            
        Returns:
            Tuple[str, List[str]]: คำค้นหาที่ปรับปรุงแล้ว และรายการคำสำคัญ
        """
        # แก้ไขคำที่สะกดผิด
        words = query.lower().split()
        corrected_words = []
        
        for word in words:
            # ตรวจสอบคำที่สะกดผิดที่พบบ่อย
            if word in self.common_misspellings:
                corrected_words.append(self.common_misspellings[word])
            else:
                corrected_words.append(word)
        
        corrected_query = " ".join(corrected_words)
        
        # แยกคำสำคัญจากคำค้นหา
        keywords = []
        
        # ค้นหาคำเกี่ยวกับอาชีพ
        for tech_term in self.tech_keywords:
            if tech_term.lower() in corrected_query.lower():
                keywords.append(tech_term)
        
        # ค้นหาคำเกี่ยวกับการสืบค้นข้อมูล
        for query_term in self.job_query_keywords:
            if query_term.lower() in corrected_query.lower():
                keywords.append(query_term)
        
        # ถ้าไม่พบคำสำคัญ ให้ใช้คำค้นหาที่ปรับปรุงแล้วเป็นคำสำคัญ
        if not keywords:
            # ตัดคำถามออก
            query_without_question = re.sub(r'(ยังไง|อย่างไร|มั้ย|ไหม|เท่าไร|เท่าไหร่|\?)+\s*$', '', corrected_query)
            keywords = query_without_question.split()
        
        return corrected_query, keywords
    
    def get_job_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        """ดึงข้อมูลอาชีพตาม ID"""
        # ถ้าไม่มีข้อมูลในฐานข้อมูลหลัก ให้ลองหาในข้อมูล fallback
        job_data = self.jobs_data.get(job_id)
        if not job_data:
            # ค้นหาจาก job_metadata ด้วย
            for job in self.job_metadata:
                if job.get("id") == job_id:
                    return job.get("metadata", {})
        return job_data
    
    def _create_mock_embedding(self, text: str, dimension: int = 384) -> np.ndarray:
        """
        สร้าง embedding จำลองในกรณีที่ไม่มี model
        """
        # ใช้ hash ของข้อความเพื่อให้ได้ค่าเดิมเมื่อให้ข้อความเดียวกัน
        text_hash = hash(text) % 2**32
        np.random.seed(text_hash)
        vector = np.random.random(dimension).astype(np.float32)
        # Normalize vector
        vector = vector / np.linalg.norm(vector)
        return vector
    
    def _fallback_search(self, query: str, keywords: List[str], limit: int) -> List[Dict[str, Any]]:
        """
        ค้นหาแบบ fallback ในกรณีที่ไม่มี FAISS index
        
        Args:
            query: คำค้นหาที่ปรับปรุงแล้ว
            keywords: คำสำคัญที่สกัดได้จากคำค้นหา
            limit: จำนวนผลลัพธ์ที่ต้องการ
            
        Returns:
            List[Dict[str, Any]]: รายการอาชีพที่เกี่ยวข้อง
        """
        results = []
        
        for job in self.job_metadata:
            score = 0
            job_id = job.get("id", "")
            
            # ตรวจสอบว่ามีคำสำคัญในชื่อตำแหน่งหรือไม่
            if job_id:
                for keyword in keywords:
                    if keyword.lower() in job_id.lower():
                        score += 5
            
            # ตรวจสอบว่ามีคำสำคัญในเนื้อหาหรือไม่
            job_text = job.get("text", "")
            if job_text:
                for keyword in keywords:
                    if keyword.lower() in job_text.lower():
                        score += 1
            
            # ตรวจสอบว่ามีคำสำคัญในชื่ออาชีพหรือไม่
            job_titles = job.get("metadata", {}).get("titles", [])
            if job_titles:
                for title in job_titles:
                    for keyword in keywords:
                        if keyword.lower() in title.lower():
                            score += 3
            
            # ตรวจสอบว่ามีคำสำคัญในทักษะหรือไม่
            job_skills = job.get("metadata", {}).get("skills", [])
            if job_skills:
                for skill in job_skills:
                    for keyword in keywords:
                        if keyword.lower() in skill.lower():
                            score += 2
            
            # เพิ่มผลลัพธ์ที่มีคะแนนมากกว่า 0
            if score > 0:
                job_result = {
                    "id": job_id,
                    "title": job_titles[0] if job_titles else job_id,
                    "description": job_text,
                    "responsibilities": job.get("metadata", {}).get("responsibilities", []),
                    "skills": job_skills,
                    "salary_ranges": job.get("metadata", {}).get("salary_ranges", []),
                    "education_requirements": job.get("metadata", {}).get("education_requirements", []),
                    "similarity_score": float(score / 10)  # แปลงคะแนนเป็น similarity score
                }
                results.append(job_result)
        
        # เรียงลำดับผลลัพธ์ตามคะแนน (มากไปน้อย)
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        # จำกัดจำนวนผลลัพธ์
        return results[:limit]
    
    def _fallback_search_advices(self, query: str, keywords: List[str], limit: int) -> List[Dict[str, Any]]:
        """
        ค้นหาแบบ fallback สำหรับคำแนะนำอาชีพในกรณีที่ไม่มี FAISS index
        """
        results = []
        
        for advice in self.advice_metadata:
            score = 0
            advice_id = advice.get("id", "")
            
            # ตรวจสอบว่ามีคำสำคัญในชื่อหรือไม่
            if advice_id:
                for keyword in keywords:
                    if keyword.lower() in advice_id.lower():
                        score += 5
            
            # ตรวจสอบว่ามีคำสำคัญในเนื้อหาหรือไม่
            advice_text = advice.get("text", "")
            if advice_text:
                for keyword in keywords:
                    if keyword.lower() in advice_text.lower():
                        score += 1
            
            # ตรวจสอบว่ามีคำสำคัญในชื่อบทความหรือไม่
            advice_title = advice.get("title", "")
            if advice_title:
                for keyword in keywords:
                    if keyword.lower() in advice_title.lower():
                        score += 3
            
            # ตรวจสอบว่ามีคำสำคัญในแท็กหรือไม่
            advice_tags = advice.get("tags", [])
            if advice_tags:
                for tag in advice_tags:
                    for keyword in keywords:
                        if keyword.lower() in tag.lower():
                            score += 2
            
            # เพิ่มผลลัพธ์ที่มีคะแนนมากกว่า 0
            if score > 0:
                advice_result = {
                    "id": advice_id,
                    "title": advice_title,
                    "text_preview": advice_text,
                    "tags": advice_tags,
                    "source": advice.get("source", ""),
                    "url": advice.get("url", ""),
                    "similarity_score": float(score / 10)  # แปลงคะแนนเป็น similarity score
                }
                results.append(advice_result)
        
        # เรียงลำดับผลลัพธ์ตามคะแนน (มากไปน้อย)
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        # จำกัดจำนวนผลลัพธ์
        return results[:limit]
    
    def search_jobs(self, query: str, limit: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        ค้นหาอาชีพที่เกี่ยวข้องกับคำค้นหา
        
        Args:
            query: คำค้นหา
            limit: จำนวนผลลัพธ์ที่ต้องการ
            filters: ตัวกรองผลลัพธ์ (เช่น {"skill": "python", "experience": "1-3"})
            
        Returns:
            รายการอาชีพที่เกี่ยวข้อง
        """
        print(f"{Fore.CYAN}🔍 กำลังค้นหาอาชีพที่เกี่ยวข้องกับ: \"{query}\"{Style.RESET_ALL}")
        logger.info(f"กำลังค้นหาอาชีพที่เกี่ยวข้องกับ: {query}")
        
        # ปรับปรุงคำค้นหาและแยกคำสำคัญ
        corrected_query, keywords = self._normalize_query(query)
        
        if corrected_query != query:
            print(f"{Fore.YELLOW}ℹ️ คำค้นหาที่ปรับปรุง: \"{corrected_query}\"{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}ℹ️ คำสำคัญที่พบ: {', '.join(keywords)}{Style.RESET_ALL}")
            logger.info(f"คำค้นหาที่ปรับปรุง: \"{corrected_query}\", คำสำคัญที่พบ: {', '.join(keywords)}")
        
        # ตรวจสอบว่า index มีอยู่จริง
        if not os.path.exists(self.job_index_file) or not os.path.exists(self.job_metadata_file):
            warning_msg = "ไม่พบไฟล์ FAISS index หรือ metadata สำหรับข้อมูลอาชีพ จะใช้การค้นหาแบบ fallback แทน"
            logger.warning(warning_msg)
            print(f"{Fore.YELLOW}⚠️ {warning_msg}{Style.RESET_ALL}")
            
            # ถ้าไม่มี FAISS index ให้ใช้การค้นหาแบบ fallback แทน
            return self._fallback_search(corrected_query, keywords, limit)
        
        try:
            print(f"{Fore.CYAN}⏳ กำลังโหลด FAISS index...{Style.RESET_ALL}")
            # โหลด FAISS index
            index = faiss.read_index(self.job_index_file)
            
            print(f"{Fore.CYAN}⏳ กำลังสร้าง embedding สำหรับคำค้นหา...{Style.RESET_ALL}")
            # สร้าง embedding สำหรับคำค้นหา
            try:
                if self.embedding_model is None:
                    # จำลองการสร้าง embedding
                    print(f"{Fore.YELLOW}ℹ️ ไม่พบโมเดล embedding จะใช้การจำลอง vector แทน{Style.RESET_ALL}")
                    logger.warning("ไม่พบโมเดล embedding จะใช้การจำลอง vector แทน")
                    
                    # สร้าง embedding จากคำสำคัญแทนที่จะใช้คำค้นหาเต็ม
                    query_embedding = self._create_mock_embedding(" ".join(keywords), dimension=index.d)
                else:
                    # ใช้โมเดลที่กำหนด
                    query_embedding = self.embedding_model.encode([corrected_query])[0]
                    # Normalize vector
                    query_embedding = query_embedding / np.linalg.norm(query_embedding)
                
                print(f"{Fore.CYAN}🔎 กำลังค้นหาใน vector database...{Style.RESET_ALL}")
                # ค้นหาใน FAISS index
                query_embedding = np.array([query_embedding]).astype(np.float32)
                distances, indices = index.search(query_embedding, limit * 3)  # ค้นหาจำนวนมากกว่า limit เผื่อกรณีมีการกรอง
                
                # แปลงผลลัพธ์
                results = []
                for i, idx in enumerate(indices[0]):
                    if idx < 0 or idx >= len(self.job_metadata):
                        continue  # ข้ามดัชนีที่ไม่ถูกต้อง
                        
                    job_id = self.job_metadata[idx]["id"]
                    job_data = self.get_job_by_id(job_id)
                    
                    if job_data:
                        # ตรวจสอบ filters ถ้ามีการระบุ
                        if filters and not self._match_filters(job_data, filters):
                            continue
                        
                        # ดึงข้อมูลอาชีพ
                        job_title = "Unknown"
                        if "titles" in job_data and job_data["titles"]:
                            job_title = job_data["titles"][0]
                        elif "title" in job_data:
                            job_title = job_data["title"]
                        
                        # สร้างข้อมูลผลลัพธ์
                        job_result = {
                            "id": job_id,
                            "title": job_title,
                            "description": job_data.get("description", ""),
                            "responsibilities": job_data.get("responsibilities", []),
                            "skills": job_data.get("skills", []),
                            "salary_ranges": job_data.get("salary_ranges", []),
                            "education_requirements": job_data.get("education_requirements", []),
                            "similarity_score": float(1 / (1 + distances[0][i]))  # แปลง distance เป็น similarity score
                        }
                        results.append(job_result)
                        
                        # หยุดหากมีผลลัพธ์ครบจำนวนที่ต้องการแล้ว
                        if len(results) >= limit:
                            break
                
                # ถ้าไม่พบผลลัพธ์ หรือพบน้อยกว่าที่ต้องการ ให้ใช้การค้นหาแบบ fallback เสริม
                if len(results) < limit:
                    fallback_results = self._fallback_search(corrected_query, keywords, limit - len(results))
                    
                    # เพิ่มผลลัพธ์จาก fallback ที่ไม่ซ้ำ
                    existing_ids = {result["id"] for result in results}
                    for result in fallback_results:
                        if result["id"] not in existing_ids:
                            results.append(result)
                            if len(results) >= limit:
                                break
                
                print(f"{Fore.GREEN}✅ ค้นหาสำเร็จ พบ {len(results)} ผลลัพธ์{Style.RESET_ALL}")
                logger.info(f"ค้นหาสำเร็จ พบ {len(results)} ผลลัพธ์")
                
                # เรียงลำดับผลลัพธ์ตาม similarity_score
                results.sort(key=lambda x: x["similarity_score"], reverse=True)
                
                # แสดงผลลัพธ์
                if results:
                    print(f"\n{Fore.CYAN}🔍 ผลลัพธ์การค้นหา:{Style.RESET_ALL}")
                    for i, result in enumerate(results):
                        print(f"{i+1}. {Fore.GREEN}{result['title']}{Style.RESET_ALL} " + 
                            f"(คะแนนความเหมือน: {Fore.YELLOW}{result['similarity_score']:.2f}{Style.RESET_ALL})")
                else:
                    print(f"{Fore.YELLOW}⚠️ ไม่พบผลลัพธ์สำหรับคำค้นหานี้{Style.RESET_ALL}")
                
                return results
                
            except Exception as e:
                error_msg = f"เกิดข้อผิดพลาดในการค้นหา: {str(e)}"
                logger.error(error_msg)
                print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}")
                
                # ใช้การค้นหาแบบ fallback แทน
                print(f"{Fore.YELLOW}ℹ️ ใช้การค้นหาแบบ fallback แทน{Style.RESET_ALL}")
                return self._fallback_search(corrected_query, keywords, limit)
                
        except Exception as e:
            error_msg = f"เกิดข้อผิดพลาดในการค้นหา: {str(e)}"
            logger.error(error_msg)
            print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}")
            
            # ใช้การค้นหาแบบ fallback แทน
            print(f"{Fore.YELLOW}ℹ️ ใช้การค้นหาแบบ fallback แทน{Style.RESET_ALL}")
            return self._fallback_search(corrected_query, keywords, limit)
    
    def _match_filters(self, job_data: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """ตรวจสอบว่าข้อมูลอาชีพตรงกับตัวกรองหรือไม่"""
        for key, value in filters.items():
            # กรณีกรองตามทักษะ
            if key == "skill" and "skills" in job_data:
                if not any(value.lower() in skill.lower() for skill in job_data["skills"]):
                    return False
            
            # กรณีกรองตามประสบการณ์
            elif key == "experience" and "salary_ranges" in job_data:
                if not any(value == salary_range.get("experience") for salary_range in job_data["salary_ranges"]):
                    return False
            
            # กรณีกรองตามการศึกษา
            elif key == "education" and "education_requirements" in job_data:
                if not any(value.lower() in edu.lower() for edu in job_data["education_requirements"]):
                    return False
            
            # กรณีกรองตามชื่อตำแหน่ง
            elif key == "title" and "titles" in job_data:
                if not any(value.lower() in title.lower() for title in job_data["titles"]):
                    return False
        
        return True
    
    def search_career_advices(self, query: str, limit: int = 5, filter_tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        ค้นหาคำแนะนำอาชีพที่เกี่ยวข้องกับคำค้นหา
        
        Args:
            query: คำค้นหา
            limit: จำนวนผลลัพธ์ที่ต้องการ
            filter_tags: กรองเฉพาะคำแนะนำที่มีแท็กที่ระบุ
            
        Returns:
            รายการคำแนะนำอาชีพที่เกี่ยวข้อง
        """
        print(f"{Fore.CYAN}🔍 กำลังค้นหาคำแนะนำอาชีพที่เกี่ยวข้องกับ: \"{query}\"{Style.RESET_ALL}")
        logger.info(f"กำลังค้นหาคำแนะนำอาชีพที่เกี่ยวข้องกับ: {query}")
        
        # ปรับปรุงคำค้นหาและแยกคำสำคัญ
        corrected_query, keywords = self._normalize_query(query)
        
        if corrected_query != query:
            print(f"{Fore.YELLOW}ℹ️ คำค้นหาที่ปรับปรุง: \"{corrected_query}\"{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}ℹ️ คำสำคัญที่พบ: {', '.join(keywords)}{Style.RESET_ALL}")
            logger.info(f"คำค้นหาที่ปรับปรุง: \"{corrected_query}\", คำสำคัญที่พบ: {', '.join(keywords)}")
        
        # ตรวจสอบว่ามีการกรองด้วยแท็กหรือไม่
        if filter_tags:
            print(f"{Fore.CYAN}🔖 กรองผลลัพธ์ด้วยแท็ก: {', '.join(filter_tags)}{Style.RESET_ALL}")
            logger.info(f"กรองผลลัพธ์ด้วยแท็ก: {filter_tags}")
        
        # ตรวจสอบว่า index มีอยู่จริง
        if not os.path.exists(self.advice_index_file) or not os.path.exists(self.advice_metadata_file):
            warning_msg = "ไม่พบไฟล์ FAISS index หรือ metadata สำหรับข้อมูลคำแนะนำอาชีพ จะใช้การค้นหาแบบ fallback แทน"
            logger.warning(warning_msg)
            print(f"{Fore.YELLOW}⚠️ {warning_msg}{Style.RESET_ALL}")
            
            # ถ้าไม่มี FAISS index ให้ใช้การค้นหาแบบ fallback แทน
            return self._fallback_search_advices(corrected_query, keywords, limit)
        
        try:
            print(f"{Fore.CYAN}⏳ กำลังโหลด FAISS index...{Style.RESET_ALL}")
            # โหลด FAISS index
            index = faiss.read_index(self.advice_index_file)
            
            print(f"{Fore.CYAN}⏳ กำลังสร้าง embedding สำหรับคำค้นหา...{Style.RESET_ALL}")
            # สร้าง embedding สำหรับคำค้นหา
            try:
                if self.embedding_model is None:
                    # จำลองการสร้าง embedding
                    print(f"{Fore.YELLOW}ℹ️ ไม่พบโมเดล embedding จะใช้การจำลอง vector แทน{Style.RESET_ALL}")
                    logger.warning("ไม่พบโมเดล embedding จะใช้การจำลอง vector แทน")
                    
                    # สร้าง embedding จากคำสำคัญแทนที่จะใช้คำค้นหาเต็ม
                    query_embedding = self._create_mock_embedding(" ".join(keywords), dimension=index.d)
                else:
                    # ใช้โมเดลที่กำหนด
                    query_embedding = self.embedding_model.encode([corrected_query])[0]
                    # Normalize vector
                    query_embedding = query_embedding / np.linalg.norm(query_embedding)
                
                print(f"{Fore.CYAN}🔎 กำลังค้นหาใน vector database...{Style.RESET_ALL}")
                # ค้นหาใน FAISS index
                query_embedding = np.array([query_embedding]).astype(np.float32)
                # เพิ่มจำนวนผลลัพธ์ที่ต้องการเพื่อให้มีโอกาสได้ผลลัพธ์หลังจากการกรอง
                additional_results = 20 if filter_tags else 0
                distances, indices = index.search(query_embedding, limit + additional_results)
                
                # แปลงผลลัพธ์
                results = []
                filtered_count = 0
                
                for i, idx in enumerate(indices[0]):
                    if idx < 0 or idx >= len(self.advice_metadata):
                        continue  # ข้ามดัชนีที่ไม่ถูกต้อง
                        
                    item = self.advice_metadata[idx]
                    
                    # กรองตาม tags ถ้ามีการระบุ
                    if filter_tags:
                        item_tags = item.get("tags", [])
                        if not any(tag in filter_tags for tag in item_tags):
                            filtered_count += 1
                            continue
                    
                    # สร้างข้อมูลผลลัพธ์
                    advice_result = {
                        "id": item.get("id", "unknown"),
                        "title": item.get("title", ""),
                        "text_preview": item.get("text", ""),
                        "tags": item.get("tags", []),
                        "source": item.get("source", ""),
                        "url": item.get("url", ""),
                        "similarity_score": float(1 / (1 + distances[0][i]))  # แปลง distance เป็น similarity score
                    }
                    results.append(advice_result)
                    
                    # หลังจากกรอง ถ้าได้ผลลัพธ์ครบแล้วให้หยุด
                    if len(results) >= limit:
                        break
                
                # ถ้าไม่พบผลลัพธ์ หรือพบน้อยกว่าที่ต้องการ ให้ใช้การค้นหาแบบ fallback เสริม
                if len(results) < limit:
                    fallback_results = self._fallback_search_advices(corrected_query, keywords, limit - len(results))
                    
                    # เพิ่มผลลัพธ์จาก fallback ที่ไม่ซ้ำ
                    existing_ids = {result["id"] for result in results}
                    for result in fallback_results:
                        if result["id"] not in existing_ids:
                            results.append(result)
                            if len(results) >= limit:
                                break
                
                if filter_tags and filtered_count > 0:
                    print(f"{Fore.YELLOW}ℹ️ คัดกรองออก {filtered_count} รายการที่ไม่ตรงกับแท็กที่กำหนด{Style.RESET_ALL}")
                    logger.info(f"คัดกรองออก {filtered_count} รายการที่ไม่ตรงกับแท็กที่กำหนด")
                
                print(f"{Fore.GREEN}✅ ค้นหาสำเร็จ พบ {len(results)} คำแนะนำที่เกี่ยวข้อง{Style.RESET_ALL}")
                logger.info(f"ค้นหาสำเร็จ พบ {len(results)} คำแนะนำที่เกี่ยวข้อง")
                
                # เรียงลำดับผลลัพธ์ตาม similarity_score
                results.sort(key=lambda x: x["similarity_score"], reverse=True)
                
                # แสดงผลลัพธ์
                if results:
                    print(f"\n{Fore.CYAN}🔍 ผลลัพธ์การค้นหา:{Style.RESET_ALL}")
                    for i, result in enumerate(results):
                        tags_str = f", แท็ก: {', '.join(result['tags'])}" if result['tags'] else ""
                        print(f"{i+1}. {Fore.GREEN}{result['title']}{Style.RESET_ALL} " + 
                            f"(คะแนนความเหมือน: {Fore.YELLOW}{result['similarity_score']:.2f}{Style.RESET_ALL}{tags_str})")
                else:
                    print(f"{Fore.YELLOW}⚠️ ไม่พบผลลัพธ์สำหรับคำค้นหานี้{Style.RESET_ALL}")
                
                return results
                
            except Exception as e:
                error_msg = f"เกิดข้อผิดพลาดในการค้นหา: {str(e)}"
                logger.error(error_msg)
                print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}")
                
                # ใช้การค้นหาแบบ fallback แทน
                print(f"{Fore.YELLOW}ℹ️ ใช้การค้นหาแบบ fallback แทน{Style.RESET_ALL}")
                return self._fallback_search_advices(corrected_query, keywords, limit)
            
        except Exception as e:
            error_msg = f"เกิดข้อผิดพลาดในการค้นหา: {str(e)}"
            logger.error(error_msg)
            print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}")
            
            # ใช้การค้นหาแบบ fallback แทน
            print(f"{Fore.YELLOW}ℹ️ ใช้การค้นหาแบบ fallback แทน{Style.RESET_ALL}")
            return self._fallback_search_advices(corrected_query, keywords, limit)
    
    def get_advice_document(self, advice_id: str) -> Optional[Dict[str, Any]]:
        """ดึงข้อมูลเอกสารคำแนะนำอาชีพตาม ID"""
        for item in self.advice_metadata:
            if item.get("id") == advice_id:
                return item
        return None
    
    def search_relevant_advices(self, query: str, limit: int = 5, filter_tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        ค้นหาคำแนะนำอาชีพที่เกี่ยวข้องกับคำค้นหา
        
        Args:
            query: คำค้นหา
            limit: จำนวนผลลัพธ์ที่ต้องการ
            filter_tags: กรองเฉพาะคำแนะนำที่มีแท็กที่ระบุ
            
        Returns:
            รายการคำแนะนำอาชีพที่เกี่ยวข้อง
        """
        print(f"{Fore.CYAN}🔍 กำลังค้นหาคำแนะนำอาชีพที่เกี่ยวข้องกับ: \"{query}\"{Style.RESET_ALL}")
        logger.info(f"กำลังค้นหาคำแนะนำอาชีพที่เกี่ยวข้องกับ: {query}")
        
        # ปรับปรุงคำค้นหาและแยกคำสำคัญ
        corrected_query, keywords = self._normalize_query(query)
        
        if corrected_query != query:
            print(f"{Fore.YELLOW}ℹ️ คำค้นหาที่ปรับปรุง: \"{corrected_query}\"{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}ℹ️ คำสำคัญที่พบ: {', '.join(keywords)}{Style.RESET_ALL}")
            logger.info(f"คำค้นหาที่ปรับปรุง: \"{corrected_query}\", คำสำคัญที่พบ: {', '.join(keywords)}")
        
        # ตรวจสอบว่ามีการกรองด้วยแท็กหรือไม่
        if filter_tags:
            print(f"{Fore.CYAN}🔖 กรองผลลัพธ์ด้วยแท็ก: {', '.join(filter_tags)}{Style.RESET_ALL}")
            logger.info(f"กรองผลลัพธ์ด้วยแท็ก: {filter_tags}")
        
        # ตรวจสอบว่า index มีอยู่จริง
        if not os.path.exists(self.advice_index_file) or not os.path.exists(self.advice_metadata_file):
            warning_msg = "ไม่พบไฟล์ FAISS index หรือ metadata สำหรับข้อมูลคำแนะนำอาชีพ จะใช้การค้นหาแบบ fallback แทน"
            logger.warning(warning_msg)
            print(f"{Fore.YELLOW}⚠️ {warning_msg}{Style.RESET_ALL}")
            
            # ถ้าไม่มี FAISS index ให้ใช้การค้นหาแบบ fallback แทน
            return self._fallback_search_advices(corrected_query, keywords, limit)
        
        try:
            print(f"{Fore.CYAN}⏳ กำลังโหลด FAISS index...{Style.RESET_ALL}")
            # โหลด FAISS index
            index = faiss.read_index(str(self.advice_index_file))
            
            print(f"{Fore.CYAN}⏳ กำลังสร้าง embedding สำหรับคำค้นหา...{Style.RESET_ALL}")
            # สร้าง embedding สำหรับคำค้นหา
            try:
                if self.embedding_model is None:
                    # จำลองการสร้าง embedding
                    print(f"{Fore.YELLOW}ℹ️ ไม่พบโมเดล embedding จะใช้การจำลอง vector แทน{Style.RESET_ALL}")
                    logger.warning("ไม่พบโมเดล embedding จะใช้การจำลอง vector แทน")
                    
                    # สร้าง embedding จากคำสำคัญแทนที่จะใช้คำค้นหาเต็ม
                    query_embedding = self._create_mock_embedding(" ".join(keywords), dimension=index.d)
                else:
                    # ใช้โมเดลที่กำหนด
                    query_embedding = self.embedding_model.encode([corrected_query])[0]
                    # Normalize vector
                    query_embedding = query_embedding / np.linalg.norm(query_embedding)
                
                print(f"{Fore.CYAN}🔎 กำลังค้นหาใน vector database...{Style.RESET_ALL}")
                # ค้นหาใน FAISS index
                query_embedding = np.array([query_embedding]).astype(np.float32)
                # เพิ่มจำนวนผลลัพธ์ที่ต้องการเพื่อให้มีโอกาสได้ผลลัพธ์หลังจากการกรอง
                additional_results = 20 if filter_tags else 0
                distances, indices = index.search(query_embedding, limit + additional_results)
                
                # แปลงผลลัพธ์
                results = []
                filtered_count = 0
                
                for i, idx in enumerate(indices[0]):
                    if idx < 0 or idx >= len(self.advice_metadata):
                        continue  # ข้ามดัชนีที่ไม่ถูกต้อง
                        
                    item = self.advice_metadata[idx]
                    
                    # กรองตาม tags ถ้ามีการระบุ
                    if filter_tags:
                        item_tags = item.get("tags", [])
                        if not any(tag in filter_tags for tag in item_tags):
                            filtered_count += 1
                            continue
                    
                    # สร้างข้อมูลผลลัพธ์
                    advice_result = {
                        "id": item.get("id", "unknown"),
                        "title": item.get("title", ""),
                        "text_preview": item.get("text", ""),
                        "tags": item.get("tags", []),
                        "source": item.get("source", ""),
                        "url": item.get("url", ""),
                        "similarity_score": float(1 / (1 + distances[0][i]))  # แปลง distance เป็น similarity score
                    }
                    results.append(advice_result)
                    
                    # หลังจากกรอง ถ้าได้ผลลัพธ์ครบแล้วให้หยุด
                    if len(results) >= limit:
                        break
                
                # ถ้าไม่พบผลลัพธ์ หรือพบน้อยกว่าที่ต้องการ ให้ใช้การค้นหาแบบ fallback เสริม
                if len(results) < limit:
                    fallback_results = self._fallback_search_advices(corrected_query, keywords, limit - len(results))
                    
                    # เพิ่มผลลัพธ์จาก fallback ที่ไม่ซ้ำ
                    existing_ids = {result["id"] for result in results}
                    for result in fallback_results:
                        if result["id"] not in existing_ids:
                            results.append(result)
                            if len(results) >= limit:
                                break
                
                if filter_tags and filtered_count > 0:
                    print(f"{Fore.YELLOW}ℹ️ คัดกรองออก {filtered_count} รายการที่ไม่ตรงกับแท็กที่กำหนด{Style.RESET_ALL}")
                    logger.info(f"คัดกรองออก {filtered_count} รายการที่ไม่ตรงกับแท็กที่กำหนด")
                
                print(f"{Fore.GREEN}✅ ค้นหาสำเร็จ พบ {len(results)} คำแนะนำที่เกี่ยวข้อง{Style.RESET_ALL}")
                logger.info(f"ค้นหาสำเร็จ พบ {len(results)} คำแนะนำที่เกี่ยวข้อง")
                
                # เรียงลำดับผลลัพธ์ตาม similarity_score
                results.sort(key=lambda x: x["similarity_score"], reverse=True)
                
                # แสดงผลลัพธ์
                if results:
                    print(f"\n{Fore.CYAN}🔍 ผลลัพธ์การค้นหา:{Style.RESET_ALL}")
                    for i, result in enumerate(results):
                        tags_str = f", แท็ก: {', '.join(result['tags'])}" if result['tags'] else ""
                        print(f"{i+1}. {Fore.GREEN}{result['title']}{Style.RESET_ALL} " + 
                            f"(คะแนนความเหมือน: {Fore.YELLOW}{result['similarity_score']:.2f}{Style.RESET_ALL}{tags_str})")
                else:
                    print(f"{Fore.YELLOW}⚠️ ไม่พบผลลัพธ์สำหรับคำค้นหานี้{Style.RESET_ALL}")
                
                return results
                
            except Exception as e:
                error_msg = f"เกิดข้อผิดพลาดในการค้นหา: {str(e)}"
                logger.error(error_msg)
                print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}")
                
                # ใช้การค้นหาแบบ fallback แทน
                print(f"{Fore.YELLOW}ℹ️ ใช้การค้นหาแบบ fallback แทน{Style.RESET_ALL}")
                return self._fallback_search_advices(corrected_query, keywords, limit)
            
        except Exception as e:
            error_msg = f"เกิดข้อผิดพลาดในการค้นหา: {str(e)}"
            logger.error(error_msg)
            print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}")
            
            # ใช้การค้นหาแบบ fallback แทน
            print(f"{Fore.YELLOW}ℹ️ ใช้การค้นหาแบบ fallback แทน{Style.RESET_ALL}")
            return self._fallback_search_advices(corrected_query, keywords, limit)
    
    def search_combined(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        ค้นหาข้อมูลแบบรวมทั้งอาชีพ คำแนะนำ และข้อมูลผู้ใช้
        
        Args:
            query: คำค้นหา
            limit: จำนวนผลลัพธ์ที่ต้องการ
                
        Returns:
            รายการผลลัพธ์การค้นหาที่เกี่ยวข้อง
        """
        print(f"{Fore.CYAN}🔍 กำลังค้นหาข้อมูลแบบรวมสำหรับ: \"{query}\"{Style.RESET_ALL}")
        logger.info(f"กำลังค้นหาข้อมูลแบบรวมสำหรับ: {query}")
        
        # ปรับปรุงคำค้นหาและแยกคำสำคัญ
        corrected_query, keywords = self._normalize_query(query)
        
        # ระบุประเภทคำถาม (ปรับการลำดับความสำคัญของประเภทข้อมูล)
        query_type = self._identify_query_type(query, keywords)
        
        if corrected_query != query:
            print(f"{Fore.YELLOW}ℹ️ คำค้นหาที่ปรับปรุง: \"{corrected_query}\"{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}ℹ️ คำสำคัญที่พบ: {', '.join(keywords)}{Style.RESET_ALL}")
            logger.info(f"คำค้นหาที่ปรับปรุง: \"{corrected_query}\", คำสำคัญที่พบ: {', '.join(keywords)}")
        
        print(f"{Fore.CYAN}🔍 ประเภทคำถาม: {query_type}{Style.RESET_ALL}")
        
        # ตรวจสอบว่า index แบบรวมมีอยู่จริง
        if not os.path.exists(self.combined_index_file) or not os.path.exists(self.combined_metadata_file):
            warning_msg = "ไม่พบไฟล์ FAISS index หรือ metadata สำหรับข้อมูลแบบรวม จะใช้การค้นหาแยกประเภทแทน"
            logger.warning(warning_msg)
            print(f"{Fore.YELLOW}⚠️ {warning_msg}{Style.RESET_ALL}")
            
            # ถ้าเป็นคำถามเกี่ยวกับผู้ใช้
            if query_type == "user":
                # ค้นหาผู้ใช้เป็นหลัก
                users = self._fallback_search_users(corrected_query, keywords, limit)
                return users
            
            # ถ้าเป็นคำถามเกี่ยวกับ resume หรือการสมัครงาน
            elif query_type == "resume":
                # ค้นหาคำแนะนำเป็นหลัก
                advices = self.search_career_advices(query, limit)
                return advices
            
            # ถ้าเป็นคำถามเกี่ยวกับอาชีพ
            else:
                # ค้นหาอาชีพเป็นหลัก
                jobs = self.search_jobs(query, limit)
                return jobs
        
        try:
            print(f"{Fore.CYAN}⏳ กำลังโหลด FAISS index...{Style.RESET_ALL}")
            # โหลด FAISS index แบบรวม
            index = faiss.read_index(self.combined_index_file)
            
            print(f"{Fore.CYAN}⏳ กำลังสร้าง embedding สำหรับคำค้นหา...{Style.RESET_ALL}")
            
            # สร้าง embedding สำหรับคำค้นหา
            try:
                if self.embedding_model is None:
                    # จำลองการสร้าง embedding
                    print(f"{Fore.YELLOW}ℹ️ ไม่พบโมเดล embedding จะใช้การจำลอง vector แทน{Style.RESET_ALL}")
                    logger.warning("ไม่พบโมเดล embedding จะใช้การจำลอง vector แทน")
                    
                    # สร้าง embedding จากคำสำคัญแทนที่จะใช้คำค้นหาเต็ม
                    query_embedding = self._create_mock_embedding(" ".join(keywords), dimension=index.d)
                else:
                    # ใช้โมเดลที่กำหนด
                    query_embedding = self.embedding_model.encode([corrected_query])[0]
                    # Normalize vector
                    query_embedding = query_embedding / np.linalg.norm(query_embedding)
                
                print(f"{Fore.CYAN}🔎 กำลังค้นหาใน vector database...{Style.RESET_ALL}")
                
                # ค้นหาใน FAISS index
                query_embedding = np.array([query_embedding]).astype(np.float32)
                distances, indices = index.search(query_embedding, limit * 2)  # ค้นหาจำนวนมากกว่า limit เพื่อกรองตามประเภท
                
                # แปลงผลลัพธ์
                results = []
                
                # ปรับการจัดอันดับผลลัพธ์ตามประเภทคำถาม
                type_weights = {
                    "job": 1.0 if query_type == "job" else 0.6,
                    "advice": 1.0 if query_type == "resume" else 0.7,
                    "user": 1.0 if query_type == "user" else 0.5
                }
                
                # โหลด metadata จาก combined_metadata
                item_types = self.combined_metadata.get("item_types", [])
                item_data = self.combined_metadata.get("item_data", [])
                
                processed_results = []
                
                for i, idx in enumerate(indices[0]):
                    if idx < 0 or idx >= len(item_data):
                        continue  # ข้ามดัชนีที่ไม่ถูกต้อง
                    
                    item_type = item_types[idx] if idx < len(item_types) else "unknown"
                    item = item_data[idx]
                    
                    # คำนวณคะแนนความเกี่ยวข้องโดยใช้น้ำหนักตามประเภท
                    similarity_score = 1.0 / (1.0 + distances[0][i])
                    weighted_score = similarity_score * type_weights.get(item_type, 0.5)
                    
                    # สร้างข้อมูลผลลัพธ์
                    result = {
                        "id": item.get("id", ""),
                        "type": item_type,
                        "title": item.get("title", ""),
                        "similarity_score": float(similarity_score),
                        "weighted_score": float(weighted_score),
                        "content": {}
                    }
                    
                    # เพิ่มข้อมูลตามประเภท
                    if item_type == "job":
                        result["content"] = {
                            "description": item.get("description", ""),
                            "responsibilities": item.get("responsibilities", []),
                            "skills": item.get("skills", []),
                            "salary_ranges": item.get("salary_ranges", [])
                        }
                    elif item_type == "advice":
                        result["content"] = {
                            "text_preview": item.get("text_preview", ""),
                            "tags": item.get("tags", []),
                            "source": item.get("source", ""),
                            "url": item.get("url", "")
                        }
                    elif item_type == "user":
                        result["content"] = {
                            "name": item.get("name", ""),
                            "institution": item.get("institution", ""),
                            "education_status": item.get("education_status", ""),
                            "skills": item.get("skills", [])
                        }
                    
                    processed_results.append(result)
                
                # เรียงลำดับผลลัพธ์ตาม weighted_score
                processed_results.sort(key=lambda x: x["weighted_score"], reverse=True)
                
                # จำกัดจำนวนผลลัพธ์
                results = processed_results[:limit]
                
                print(f"{Fore.GREEN}✅ ค้นหาสำเร็จ พบ {len(results)} ผลลัพธ์{Style.RESET_ALL}")
                logger.info(f"ค้นหาสำเร็จ พบ {len(results)} ผลลัพธ์")
                
                # แสดงผลลัพธ์
                if results:
                    print(f"\n{Fore.CYAN}🔍 ผลลัพธ์การค้นหา:{Style.RESET_ALL}")
                    for i, result in enumerate(results):
                        item_type = result["type"]
                        item_type_str = {
                            "job": "อาชีพ",
                            "advice": "คำแนะนำ",
                            "user": "ผู้ใช้"
                        }.get(item_type, item_type)
                        
                        print(f"{i+1}. {Fore.GREEN}{result['title']}{Style.RESET_ALL} " + 
                            f"({item_type_str}, คะแนน: {Fore.YELLOW}{result['weighted_score']:.2f}{Style.RESET_ALL})")
                else:
                    print(f"{Fore.YELLOW}⚠️ ไม่พบผลลัพธ์สำหรับคำค้นหานี้{Style.RESET_ALL}")
                
                return results
                    
            except Exception as e:
                error_msg = f"เกิดข้อผิดพลาดในการค้นหา: {str(e)}"
                logger.error(error_msg)
                print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}")
                
                # ทำ fallback ตามประเภทคำถาม
                if query_type == "resume":
                    return self.search_career_advices(query, limit)
                elif query_type == "user":
                    return self._fallback_search_users(corrected_query, keywords, limit)
                else:
                    return self.search_jobs(query, limit)
        
        except Exception as e:
            error_msg = f"เกิดข้อผิดพลาดในการค้นหาแบบรวม: {str(e)}"
            logger.error(error_msg)
            print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}")
            
            # ทำ fallback ตามประเภทคำถาม
            if query_type == "resume":
                return self.search_career_advices(query, limit)
            elif query_type == "user":
                return self._fallback_search_users(corrected_query, keywords, limit)
            else:
                return self.search_jobs(query, limit)
                    
    def _identify_query_type(self, query: str, keywords: List[str]) -> str:
        """
        ระบุประเภทของคำถามว่าเกี่ยวข้องกับอาชีพ คำแนะนำ หรือผู้ใช้
        
        Args:
            query: คำค้นหา
            keywords: คำสำคัญที่สกัดได้จากคำค้นหา
            
        Returns:
            str: ประเภทของคำถาม ("job", "resume", "user")
        """
        # นับจำนวนคำที่เกี่ยวข้องกับแต่ละประเภท
        job_count = sum(1 for kw in keywords if kw.lower() in self.tech_keywords or kw.lower() in self.job_query_keywords)
        resume_count = sum(1 for kw in keywords if kw.lower() in self.resume_keywords)
        user_count = sum(1 for kw in keywords if kw.lower() in self.user_keywords)
        
        # คำถามเกี่ยวกับผู้ใช้มีคำสำคัญเฉพาะ
        if user_count > 0 and (user_count >= job_count and user_count >= resume_count):
            return "user"
        
        # ตรวจสอบคำที่เกี่ยวข้องกับ resume
        if resume_count > 0 and (resume_count >= job_count):
            # คำถามเกี่ยวกับ resume และการสมัครงาน
            return "resume"
        
        # คำถามเกี่ยวข้องกับอาชีพ (เป็นกรณีพื้นฐาน)
        return "job"

    def _fallback_search_users(self, query: str, keywords: List[str], limit: int = 5) -> List[Dict[str, Any]]:
        """
        ค้นหาผู้ใช้แบบ fallback ในกรณีที่ไม่มี FAISS index
        
        Args:
            query: คำค้นหาที่ปรับปรุงแล้ว
            keywords: คำสำคัญที่สกัดได้จากคำค้นหา
            limit: จำนวนผลลัพธ์ที่ต้องการ
            
        Returns:
            List[Dict[str, Any]]: รายการผู้ใช้ที่เกี่ยวข้อง
        """
        results = []
        
        try:
            # โหลดข้อมูลผู้ใช้
            from src.utils.config import USERS_DIR
            users_file = os.path.join(USERS_DIR, "users.json")
            
            if not os.path.exists(users_file):
                logger.warning(f"ไม่พบไฟล์ข้อมูลผู้ใช้: {users_file}")
                return []
            
            with open(users_file, 'r', encoding='utf-8') as f:
                users_data = json.load(f)
            
            for user in users_data:
                score = 0
                user_id = user.get("id", "")
                
                # ตรวจสอบชื่อ
                if "name" in user and any(kw.lower() in user["name"].lower() for kw in keywords):
                    score += 5
                
                # ตรวจสอบสถาบันการศึกษา
                if "institution" in user and any(kw.lower() in user["institution"].lower() for kw in keywords):
                    score += 3
                
                # ตรวจสอบทักษะ
                if "skills" in user:
                    for skill in user["skills"]:
                        skill_name = skill.get("name", "")
                        if any(kw.lower() in skill_name.lower() for kw in keywords):
                            score += 2
                
                # ตรวจสอบภาษาโปรแกรม
                if "programming_languages" in user:
                    for lang in user["programming_languages"]:
                        if any(kw.lower() in lang.lower() for kw in keywords):
                            score += 2
                
                # เพิ่มผลลัพธ์ที่มีคะแนนมากกว่า 0
                if score > 0:
                    user_result = {
                        "id": f"user_{user_id}",
                        "type": "user",
                        "title": user.get("name", f"ผู้ใช้ {user_id}"),
                        "similarity_score": float(score / 10),
                        "weighted_score": float(score / 10),
                        "content": {
                            "name": user.get("name", ""),
                            "institution": user.get("institution", ""),
                            "education_status": user.get("education_status", ""),
                            "skills": [skill.get("name") for skill in user.get("skills", [])]
                        }
                    }
                    results.append(user_result)
            
            # เรียงลำดับผลลัพธ์ตามคะแนน (มากไปน้อย)
            results.sort(key=lambda x: x["weighted_score"], reverse=True)
            
            # จำกัดจำนวนผลลัพธ์
            return results[:limit]
            
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการค้นหาข้อมูลผู้ใช้: {str(e)}")
            return []
    
    