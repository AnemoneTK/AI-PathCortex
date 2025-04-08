# backend/src/utils/vector_search.py
import os
import json
import numpy as np
import faiss
from typing import List, Dict, Any, Optional
from pathlib import Path
import sys
from colorama import init, Fore, Style

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
        # คงเดิม แต่อาจเพิ่มการ import SentenceTransformer
        try:
            from sentence_transformers import SentenceTransformer
            
            # ถ้าไม่มี embedding_model ให้โหลดโมเดลเริ่มต้น
            if embedding_model is None:
                default_model = 'intfloat/multilingual-e5-large'
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
        
        # ไฟล์ FAISS index และ metadata
        self.job_index_file = os.path.join(self.job_knowledge_dir, "faiss_index.bin")
        self.job_metadata_file = os.path.join(self.job_knowledge_dir, "metadata.json")
        
        self.advice_index_file = os.path.join(self.career_advice_dir, "faiss_index.bin")
        self.advice_metadata_file = os.path.join(self.career_advice_dir, "metadata.json")
        
        print(f"{Fore.CYAN}📂 โฟลเดอร์ฐานข้อมูล vector: {vector_db_dir}")
        print(f"{Fore.CYAN}📄 ไฟล์ job index: {self.job_index_file}")
        print(f"{Fore.CYAN}📄 ไฟล์ job metadata: {self.job_metadata_file}")
        print(f"{Fore.CYAN}📄 ไฟล์ advice index: {self.advice_index_file}")
        print(f"{Fore.CYAN}📄 ไฟล์ advice metadata: {self.advice_metadata_file}{Style.RESET_ALL}")
        
        # โหลด metadata
        self.job_metadata = self._load_metadata(self.job_metadata_file)
        self.advice_metadata = self._load_metadata(self.advice_metadata_file)
        
        # ดึงข้อมูลที่จัดเก็บไว้
        self.processed_data_dir = os.path.join(project_root, "data", "processed")
        self.normalized_jobs_dir = os.path.join(self.processed_data_dir, "normalized_jobs")
        
        # สร้าง mapping ของ job_id -> job_data
        self.jobs_data = self._load_jobs_data()
        
        if len(self.job_metadata) > 0 and len(self.advice_metadata) > 0:
            print(f"{Fore.GREEN}✅ VectorSearch เริ่มต้นสำเร็จ: {len(self.job_metadata)} job metadata, {len(self.advice_metadata)} advice metadata{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}⚠️ VectorSearch เริ่มต้นสำเร็จ แต่อาจไม่มีข้อมูล: {len(self.job_metadata)} job metadata, {len(self.advice_metadata)} advice metadata{Style.RESET_ALL}")
        
        logger.info(f"VectorSearch เริ่มต้นสำเร็จ: {len(self.job_metadata)} job metadata, {len(self.advice_metadata)} advice metadata")
    
    def _load_metadata(self, metadata_file: str) -> List[Dict[str, Any]]:
        """โหลดข้อมูล metadata จากไฟล์"""
        try:
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
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
    
    def get_job_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        """ดึงข้อมูลอาชีพตาม ID"""
        return self.jobs_data.get(job_id)
    
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
        
        # ตรวจสอบว่า index มีอยู่จริง
        if not os.path.exists(self.job_index_file) or not os.path.exists(self.job_metadata_file):
            error_msg = "ไม่พบไฟล์ FAISS index หรือ metadata สำหรับข้อมูลอาชีพ"
            logger.error(error_msg)
            print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}")
            return []
        
        try:
            print(f"{Fore.CYAN}⏳ กำลังโหลด FAISS index...{Style.RESET_ALL}")
            # โหลด FAISS index
            index = faiss.read_index(self.job_index_file)
            
            print(f"{Fore.CYAN}⏳ กำลังสร้าง embedding สำหรับคำค้นหา...{Style.RESET_ALL}")
            # สร้าง embedding สำหรับคำค้นหา
            if self.embedding_model is None:
                # จำลองการสร้าง embedding
                print(f"{Fore.YELLOW}ℹ️ ไม่พบโมเดล embedding จะใช้การจำลอง vector แทน{Style.RESET_ALL}")
                logger.warning("ไม่พบโมเดล embedding จะใช้การจำลอง vector แทน")
                query_embedding = np.random.random(1536).astype(np.float32)
                # Normalize vector
                query_embedding = query_embedding / np.linalg.norm(query_embedding)
            else:
                # ใช้โมเดลที่กำหนด
                query_embedding = self.embedding_model.encode([query])[0]
            
            print(f"{Fore.CYAN}🔎 กำลังค้นหาใน vector database...{Style.RESET_ALL}")
            # ค้นหาใน FAISS index
            query_embedding = np.array([query_embedding]).astype(np.float32)
            distances, indices = index.search(query_embedding, limit * 3)  # ค้นหาจำนวนมากกว่า limit เผื่อกรณีมีการกรอง
            
            # แปลงผลลัพธ์
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.job_metadata) and idx >= 0:  # ป้องกันการเข้าถึงข้อมูลเกินขอบเขต
                    job_id = self.job_metadata[idx]["id"]
                    job_data = self.get_job_by_id(job_id)
                    
                    if job_data:
                        # ตรวจสอบ filters ถ้ามีการระบุ
                        if filters and not self._match_filters(job_data, filters):
                            continue
                        
                        # สร้างข้อมูลผลลัพธ์
                        job_result = {
                            "id": job_id,
                            "title": job_data.get("titles", ["Unknown"])[0] if job_data.get("titles") else "Unknown",
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
            
            print(f"{Fore.GREEN}✅ ค้นหาสำเร็จ พบ {len(results)} ผลลัพธ์{Style.RESET_ALL}")
            logger.info(f"ค้นหาสำเร็จ พบ {len(results)} ผลลัพธ์")
            
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
            return []
    
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
        
        # ตรวจสอบว่ามีการกรองด้วยแท็กหรือไม่
        if filter_tags:
            print(f"{Fore.CYAN}🔖 กรองผลลัพธ์ด้วยแท็ก: {', '.join(filter_tags)}{Style.RESET_ALL}")
            logger.info(f"กรองผลลัพธ์ด้วยแท็ก: {filter_tags}")
        
        # ตรวจสอบว่า index มีอยู่จริง
        if not os.path.exists(self.advice_index_file) or not os.path.exists(self.advice_metadata_file):
            error_msg = "ไม่พบไฟล์ FAISS index หรือ metadata สำหรับข้อมูลคำแนะนำอาชีพ"
            logger.error(error_msg)
            print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}")
            return []
        
        try:
            print(f"{Fore.CYAN}⏳ กำลังโหลด FAISS index...{Style.RESET_ALL}")
            # โหลด FAISS index
            index = faiss.read_index(self.advice_index_file)
            
            print(f"{Fore.CYAN}⏳ กำลังสร้าง embedding สำหรับคำค้นหา...{Style.RESET_ALL}")
            # สร้าง embedding สำหรับคำค้นหา
            if self.embedding_model is None:
                # จำลองการสร้าง embedding
                print(f"{Fore.YELLOW}ℹ️ ไม่พบโมเดล embedding จะใช้การจำลอง vector แทน{Style.RESET_ALL}")
                logger.warning("ไม่พบโมเดล embedding จะใช้การจำลอง vector แทน")
                query_embedding = np.random.random(1536).astype(np.float32)
                # Normalize vector
                query_embedding = query_embedding / np.linalg.norm(query_embedding)
            else:
                # ใช้โมเดลที่กำหนด
                query_embedding = self.embedding_model.encode([query])[0]
            
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
                if idx < len(self.advice_metadata) and idx >= 0:  # ป้องกันการเข้าถึงข้อมูลเกินขอบเขต
                    item = self.advice_metadata[idx]
                    
                    # กรองตาม tags ถ้ามีการระบุ
                    if filter_tags and not any(tag in filter_tags for tag in item.get("tags", [])):
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
            
            if filter_tags and filtered_count > 0:
                print(f"{Fore.YELLOW}ℹ️ คัดกรองออก {filtered_count} รายการที่ไม่ตรงกับแท็กที่กำหนด{Style.RESET_ALL}")
                logger.info(f"คัดกรองออก {filtered_count} รายการที่ไม่ตรงกับแท็กที่กำหนด")
            
            print(f"{Fore.GREEN}✅ ค้นหาสำเร็จ พบ {len(results)} คำแนะนำที่เกี่ยวข้อง{Style.RESET_ALL}")
            logger.info(f"ค้นหาสำเร็จ พบ {len(results)} คำแนะนำที่เกี่ยวข้อง")
            
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
            return []
    
    def get_advice_document(self, advice_id: str) -> Optional[Dict[str, Any]]:
        """ดึงข้อมูลเอกสารคำแนะนำอาชีพตาม ID"""
        for item in self.advice_metadata:
            if item.get("id") == advice_id:
                return item
        return None