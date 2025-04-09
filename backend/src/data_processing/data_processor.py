import os
import json
import glob
import re
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any

class JobDataProcessor:
    """
    คลาสสำหรับประมวลผลข้อมูลอาชีพทั้งโฟลเดอร์: ทำความสะอาดและสร้าง vector embeddings
    """
    def __init__(self, model_name="intfloat/e5-small-v2"):
        """
        เริ่มต้นคลาสด้วย model สำหรับสร้าง embeddings (ใช้ multilingual model สำหรับภาษาไทย)
        """
        self.model = SentenceTransformer(model_name)
        self.processed_jobs = []
        self.job_ids_to_index = {}  # map ระหว่าง job_id กับ index ใน vector db
    
    def clean_text(self, text: str) -> str:
        """
        ทำความสะอาดข้อความ
        """
        if not text:
            return ""
            
        # แก้ไขคำเฉพาะและรูปแบบที่ไม่ถูกต้อง
        text = text.replace('a ', '')
        text = text.replace('ซฮฟต์แวร์', 'ซอฟต์แวร์')
        text = text.replace('หน้าที่', '')
        # กำจัดช่องว่างซ้ำซ้อน
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def should_skip_responsibility(self, resp: str) -> bool:
        """
        ตรวจสอบว่าควรข้ามความรับผิดชอบนี้หรือไม่ (กรณีที่เป็นคำถามหรือไม่เกี่ยวข้อง)
        """
        skip_patterns = [
            'วิธีการเป็น', 'เป็นอย่างไร', 'ล่าสุด', 
            'ทักษะและประสบการณ์ที่ดีที่สุดสำหรับ',
            '?', 'คุณสมบัติ'
        ]
        return any(pattern in resp.lower() for pattern in skip_patterns)
    
    def clean_job_data(self, job_data: Dict) -> Dict:
        """
        ทำความสะอาดข้อมูลงาน (1 อาชีพ)
        """
        # สร้าง deep copy เพื่อไม่ให้กระทบข้อมูลต้นฉบับ
        cleaned_job = job_data.copy()
        
        # ทำความสะอาด description
        if 'description' in cleaned_job:
            cleaned_job['description'] = self.clean_text(cleaned_job['description'])
        
        # ทำความสะอาด responsibilities
        if 'responsibilities' in cleaned_job and isinstance(cleaned_job['responsibilities'], list):
            filtered_responsibilities = []
            for resp in cleaned_job['responsibilities']:
                # ข้ามรายการที่เป็นคำถามหรือไม่เกี่ยวข้อง
                if self.should_skip_responsibility(resp):
                    continue
                
                # ทำความสะอาด
                cleaned_resp = self.clean_text(resp)
                if cleaned_resp and len(cleaned_resp) > 5:  # ข้ามข้อความสั้นเกินไป
                    filtered_responsibilities.append(cleaned_resp)
            
            cleaned_job['responsibilities'] = filtered_responsibilities
        
        # ทำความสะอาด skills
        if 'skills' in cleaned_job and isinstance(cleaned_job['skills'], list):
            cleaned_skills = []
            for skill in cleaned_job['skills']:
                # ทำความสะอาด skill
                cleaned_skill = self.clean_text(skill)
                if cleaned_skill and len(cleaned_skill) > 1:  # ข้ามทักษะที่สั้นเกินไป เช่น "c"
                    # ตรวจสอบว่ามีอยู่แล้วหรือไม่ (case-insensitive)
                    if not any(s.lower() == cleaned_skill.lower() for s in cleaned_skills):
                        cleaned_skills.append(cleaned_skill)
            
            cleaned_job['skills'] = cleaned_skills
            
        return cleaned_job
    
    def process_single_file(self, file_path: str) -> List[Dict]:
        """
        ประมวลผลไฟล์เดียว: อ่านและทำความสะอาดข้อมูล
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                job_data = json.load(f)
            
            # ตรวจสอบว่าเป็น dict หรือ list
            if isinstance(job_data, dict):
                # กรณีมีข้อมูลอาชีพเดียว
                return [self.clean_job_data(job_data)]
            elif isinstance(job_data, list):
                # กรณีมีหลายอาชีพในไฟล์เดียว
                return [self.clean_job_data(job) for job in job_data]
            else:
                print(f"รูปแบบไฟล์ไม่รองรับ: {file_path}")
                return []
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการประมวลผลไฟล์ {file_path}: {e}")
            return []
    
    def prepare_text_for_embedding(self, job: Dict) -> str:
        """
        เตรียมข้อความจากข้อมูลอาชีพเพื่อสร้าง embedding
        """
        text_parts = []
        
        # เพิ่มชื่อตำแหน่งงาน
        if "id" in job:
            text_parts.append(f"รหัสงาน: {job['id']}")
            
        # เพิ่มชื่ออาชีพทั้งหมด
        if "titles" in job and isinstance(job["titles"], list):
            text_parts.append(f"ตำแหน่งงาน: {', '.join(job['titles'])}")
        
        # เพิ่มคำอธิบาย
        if "description" in job and job["description"]:
            text_parts.append(f"คำอธิบาย: {job['description']}")
        
        # เพิ่มความรับผิดชอบ
        if "responsibilities" in job and isinstance(job["responsibilities"], list) and job["responsibilities"]:
            resp_text = " ".join(job["responsibilities"])
            text_parts.append(f"ความรับผิดชอบ: {resp_text}")
        
        # เพิ่มทักษะ
        if "skills" in job and isinstance(job["skills"], list) and job["skills"]:
            skills_text = ", ".join(job["skills"])
            text_parts.append(f"ทักษะ: {skills_text}")
        
        # เพิ่มระดับเงินเดือนและประสบการณ์
        if "salary_ranges" in job and isinstance(job["salary_ranges"], list):
            salary_info = []
            for salary_range in job["salary_ranges"]:
                if "experience" in salary_range and "salary" in salary_range:
                    salary_info.append(f"ประสบการณ์ {salary_range['experience']} ปี: เงินเดือน {salary_range['salary']} บาท")
            
            if salary_info:
                text_parts.append(f"ข้อมูลเงินเดือน: {' '.join(salary_info)}")
        
        # รวมทุกส่วนเข้าด้วยกัน
        return " ".join(text_parts)
    
    def process_directory(self, input_dir: str, output_dir: str) -> None:
        """
        ประมวลผลไฟล์ทั้งหมดในไดเรกทอรี
        """
        # ตรวจสอบและสร้างไดเรกทอรีเอาต์พุตถ้ายังไม่มี
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # รวบรวมไฟล์ทั้งหมด
        json_files = glob.glob(os.path.join(input_dir, "*.json"))
        print(f"พบไฟล์ JSON จำนวน {len(json_files)} ไฟล์")
        
        # ประมวลผลทุกไฟล์
        all_cleaned_jobs = []
        for file_path in json_files:
            file_name = os.path.basename(file_path)
            print(f"กำลังประมวลผลไฟล์: {file_name}")
            
            # ประมวลผลไฟล์
            cleaned_jobs = self.process_single_file(file_path)
            all_cleaned_jobs.extend(cleaned_jobs)
            
            # บันทึกไฟล์ที่ทำความสะอาดแล้ว
            output_path = os.path.join(output_dir, file_name)
            with open(output_path, 'w', encoding='utf-8') as f:
                if len(cleaned_jobs) == 1:
                    # กรณีมีอาชีพเดียว
                    json.dump(cleaned_jobs[0], f, ensure_ascii=False, indent=2)
                else:
                    # กรณีมีหลายอาชีพ
                    json.dump(cleaned_jobs, f, ensure_ascii=False, indent=2)
        
        print(f"ทำความสะอาดข้อมูลเสร็จสิ้น: {len(all_cleaned_jobs)} อาชีพ")
        self.processed_jobs = all_cleaned_jobs
    
    def create_vector_database(self, output_index_path: str, output_metadata_path: str) -> None:
        """
        สร้าง vector database จากข้อมูลที่ทำความสะอาดแล้ว
        """
        if not self.processed_jobs:
            print("ไม่มีข้อมูลที่ทำความสะอาดแล้ว โปรดเรียก process_directory() ก่อน")
            return
        
        print(f"กำลังสร้าง embeddings สำหรับ {len(self.processed_jobs)} อาชีพ...")
        
        # เตรียมข้อความสำหรับสร้าง embeddings
        texts = []
        job_ids = []
        
        for job in self.processed_jobs:
            if "id" not in job:
                continue
                
            job_text = self.prepare_text_for_embedding(job)
            texts.append(job_text)
            job_ids.append(job["id"])
        
        # สร้าง embeddings
        print("กำลังสร้าง embeddings...")
        embeddings = self.model.encode(texts, show_progress_bar=True)
        
        # สร้าง FAISS index
        print("กำลังสร้าง FAISS index...")
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)
        
        # สร้าง map ระหว่าง job_id กับ index
        for i, job_id in enumerate(job_ids):
            self.job_ids_to_index[job_id] = i
        
        # บันทึก index
        print(f"กำลังบันทึก FAISS index ไปที่ {output_index_path}...")
        os.makedirs(os.path.dirname(output_index_path), exist_ok=True)
        faiss.write_index(index, output_index_path)
        
        # บันทึก metadata
        print(f"กำลังบันทึก metadata ไปที่ {output_metadata_path}...")
        metadata = {
            "job_ids": job_ids,
            "job_ids_to_index": self.job_ids_to_index,
            "job_data": self.processed_jobs
        }
        
        with open(output_metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        print("เสร็จสิ้นการสร้าง vector database!")
    
    def run_full_process(self, input_dir: str, cleaned_output_dir: str, 
                         vector_index_path: str, vector_metadata_path: str) -> None:
        """
        รันกระบวนการทั้งหมด: ทำความสะอาดและสร้าง vector database
        """
        # 1. ทำความสะอาดข้อมูล
        self.process_directory(input_dir, cleaned_output_dir)
        
        # 2. สร้าง vector database
        self.create_vector_database(vector_index_path, vector_metadata_path)


# ตัวอย่างการใช้งาน:
if __name__ == "__main__":
    processor = JobDataProcessor()
    
    # กำหนดพาธ
    input_dir = "data/processed/normalized_jobs"
    cleaned_output_dir = "data/processed/cleaned_jobs"
    vector_index_path = "data/vector_db/job_knowledge/faiss_index.bin"
    vector_metadata_path = "data/vector_db/job_knowledge/job_metadata.json"
    
    # รันกระบวนการทั้งหมด
    processor.run_full_process(
        input_dir=input_dir,
        cleaned_output_dir=cleaned_output_dir,
        vector_index_path=vector_index_path,
        vector_metadata_path=vector_metadata_path
    )