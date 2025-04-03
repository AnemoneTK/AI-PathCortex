#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vector Database Creator for Career AI Advisor

เครื่องมือสำหรับสร้างฐานข้อมูล Vector จากข้อมูลอาชีพที่ประมวลผลแล้ว
โดยใช้ PostgreSQL + pgvector
"""

import os
import json
import logging
import argparse
import psycopg
import sys
import numpy as np
from tqdm import tqdm
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from sentence_transformers import SentenceTransformer

# ตั้งค่าสี Terminal
import colorama
colorama.init()

# สีสำหรับการแสดงผลในเทอร์มินัล
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# สร้างโฟลเดอร์สำหรับเก็บล็อก
log_dir = Path("src/logs")
log_dir.mkdir(parents=True, exist_ok=True)

# ตั้งค่าการบันทึกล็อก
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "vector_db_creator.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("vector_db_creator")

class VectorDBCreator:
    """
    คลาสสำหรับสร้างและจัดการฐานข้อมูล Vector
    """
    def __init__(self, 
                 input_file: str = "data/processed/cleaned_jobs.json",
                 db_name: str = "pctdb",
                 db_user: str = "PCT_admin",
                 db_password: str = "pct1234",
                 db_host: str = "localhost",
                 db_port: str = "5430",
                 embedding_model: str = "all-MiniLM-L6-v2",
                 embedding_dim: int = 384,
                 chunk_size: int = 512,
                 overlap_size: int = 50):
        """
        เริ่มต้นออบเจกต์ VectorDBCreator

        Args:
            input_file: ไฟล์ข้อมูลอาชีพที่ประมวลผลแล้ว
            db_name: ชื่อฐานข้อมูล PostgreSQL
            db_user: ชื่อผู้ใช้ฐานข้อมูล
            db_password: รหัสผ่านฐานข้อมูล
            db_host: โฮสต์ของฐานข้อมูล
            db_port: พอร์ตของฐานข้อมูล
            embedding_model: ชื่อโมเดล SentenceTransformer
            embedding_dim: มิติของ embedding vector
            chunk_size: ขนาดของชิ้นส่วนข้อความ (จำนวนตัวอักษร)
            overlap_size: ขนาดการซ้อนทับของชิ้นส่วนข้อความ
        """
        self.input_file = input_file
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self.db_port = db_port
        self.embedding_model_name = embedding_model
        self.embedding_dim = embedding_dim
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        
        # สร้าง connection string
        self.connection_string = (
            f"dbname={self.db_name} "
            f"user={self.db_user} "
            f"password={self.db_password} "
            f"host={self.db_host} "
            f"port={self.db_port}"
        )
        
        # โหลดโมเดล SentenceTransformer
        print(f"{Colors.CYAN}กำลังโหลดโมเดล {embedding_model}...{Colors.ENDC}")
        try:
            self.model = SentenceTransformer(f"sentence-transformers/{embedding_model}")
            print(f"{Colors.GREEN}โหลดโมเดลเรียบร้อย{Colors.ENDC}")
        except Exception as e:
            logger.error(f"ไม่สามารถโหลดโมเดล {embedding_model} ได้: {str(e)}")
            print(f"{Colors.FAIL}ไม่สามารถโหลดโมเดล {embedding_model} ได้: {str(e)}{Colors.ENDC}")
            raise e

    def get_connection(self):
        """สร้างการเชื่อมต่อกับฐานข้อมูล PostgreSQL"""
        try:
            conn = psycopg.connect(self.connection_string)
            return conn
        except Exception as e:
            logger.error(f"ไม่สามารถเชื่อมต่อกับฐานข้อมูลได้: {str(e)}")
            print(f"{Colors.FAIL}ไม่สามารถเชื่อมต่อกับฐานข้อมูลได้: {str(e)}{Colors.ENDC}")
            return None

    def create_database_schema(self):
        """
        สร้างโครงสร้างฐานข้อมูล (ตาราง และ indices)
        """
        print(f"{Colors.HEADER}===== สร้างโครงสร้างฐานข้อมูล ====={Colors.ENDC}")
        
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cursor:
                # เพิ่ม extensions ที่จำเป็น
                cursor.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
                cursor.execute('CREATE EXTENSION IF NOT EXISTS vector;')
                
                # สร้างตารางหลักสำหรับเก็บข้อมูลอาชีพ
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS jobs (
                        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                        job_key VARCHAR(100) NOT NULL UNIQUE,
                        job_title VARCHAR(255) NOT NULL,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # สร้างตารางสำหรับชื่อตำแหน่งงานที่หลากหลาย
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS job_titles (
                        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                        job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
                        title VARCHAR(255) NOT NULL
                    )
                ''')
                
                # สร้างตารางสำหรับเก็บความรับผิดชอบ
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS job_responsibilities (
                        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                        job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
                        responsibility TEXT NOT NULL
                    )
                ''')
                
                # สร้างตารางสำหรับเก็บทักษะ
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS job_skills (
                        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                        job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
                        skill TEXT NOT NULL
                    )
                ''')
                
                # สร้างตารางสำหรับเก็บข้อมูลเงินเดือน
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS job_salaries (
                        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                        job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
                        experience_range VARCHAR(50) NOT NULL,
                        salary_range VARCHAR(50) NOT NULL
                    )
                ''')
                
                # สร้างตารางสำหรับเก็บ chunks และ embeddings
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS job_vectors (
                        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                        job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
                        chunk_type VARCHAR(50) NOT NULL,
                        content TEXT NOT NULL,
                        embedding vector({self.embedding_dim}),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # สร้างดัชนีสำหรับการค้นหาด้วย cosine similarity
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS embedding_idx ON job_vectors 
                    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
                ''')
                
                # สร้างดัชนีสำหรับตาราง jobs
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_job_key ON jobs(job_key);')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_job_titles_job_id ON job_titles(job_id);')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_job_titles_title ON job_titles(title);')
                
                # Commit ข้อมูล
                conn.commit()
                
                logger.info("สร้างโครงสร้างฐานข้อมูลเสร็จสมบูรณ์")
                print(f"{Colors.GREEN}✅ สร้างโครงสร้างฐานข้อมูลเสร็จสมบูรณ์{Colors.ENDC}")
                return True
                
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"เกิดข้อผิดพลาดในการสร้างโครงสร้างฐานข้อมูล: {str(e)}")
            print(f"{Colors.FAIL}❌ เกิดข้อผิดพลาดในการสร้างโครงสร้างฐานข้อมูล: {str(e)}{Colors.ENDC}")
            return False
        finally:
            if conn:
                conn.close()

    def load_job_data(self) -> Dict[str, Any]:
        """
        โหลดข้อมูลอาชีพจากไฟล์ JSON
        
        Returns:
            Dict: ข้อมูลอาชีพทั้งหมด
        """
        try:
            print(f"{Colors.CYAN}กำลังโหลดข้อมูลจาก {self.input_file}...{Colors.ENDC}")
            with open(self.input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"โหลดข้อมูลอาชีพเสร็จสมบูรณ์ จำนวน {len(data)} อาชีพ")
            print(f"{Colors.GREEN}✅ โหลดข้อมูลอาชีพเสร็จสมบูรณ์ จำนวน {len(data)} อาชีพ{Colors.ENDC}")
            return data
        except Exception as e:
            logger.error(f"ไม่สามารถโหลดข้อมูลจาก {self.input_file} ได้: {str(e)}")
            print(f"{Colors.FAIL}❌ ไม่สามารถโหลดข้อมูลจาก {self.input_file} ได้: {str(e)}{Colors.ENDC}")
            return {}

    def create_text_chunks(self, text: str, job_key: str, chunk_type: str) -> List[Dict[str, Any]]:
        """
        แบ่งข้อความเป็นชิ้นส่วนเล็กๆ
        
        Args:
            text: ข้อความที่ต้องการแบ่ง
            job_key: คีย์อ้างอิงงาน
            chunk_type: ประเภทของชิ้นส่วน
            
        Returns:
            List[Dict]: รายการชิ้นส่วนพร้อมข้อมูลอ้างอิง
        """
        if not text or len(text) < 50:  # ข้ามข้อความสั้นๆ
            if text:
                return [{
                    "content": text,
                    "job_key": job_key,
                    "chunk_type": chunk_type
                }]
            return []
            
        chunks = []
        
        # แบ่งข้อความเป็นชิ้นส่วน
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            
            # หากไม่ใช่สิ้นสุดข้อความ ให้พยายามหาจุดสิ้นสุดประโยคหรือคำที่เหมาะสม
            if end < len(text):
                # หาจุดสิ้นสุดที่เป็นสิ้นสุดประโยค
                for punct in [". ", "! ", "? ", "\n"]:
                    last_punct = text.rfind(punct, start, end)
                    if last_punct != -1:
                        end = last_punct + 1
                        break
                
                # หากไม่พบจุดสิ้นสุดประโยค ให้หาช่องว่างล่าสุด
                if end == start + self.chunk_size:
                    last_space = text.rfind(" ", start, end)
                    if last_space != -1:
                        end = last_space + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append({
                    "content": chunk,
                    "job_key": job_key,
                    "chunk_type": chunk_type
                })
            
            # ถ้ามีการกำหนด overlap ให้ย้อนกลับไปเริ่มต้นที่ตำแหน่งใหม่
            start = end - self.overlap_size if self.overlap_size > 0 and end < len(text) else end
            
        return chunks

    def create_embeddings(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        สร้าง embeddings สำหรับชิ้นส่วนข้อความ
        
        Args:
            chunks: รายการชิ้นส่วนข้อความ
            
        Returns:
            List[Dict]: รายการชิ้นส่วนพร้อม embeddings
        """
        if not chunks:
            return []
            
        texts = [chunk["content"] for chunk in chunks]
        
        # สร้าง embeddings
        try:
            embeddings = self.model.encode(texts)
            
            # เพิ่ม embeddings เข้าไปในข้อมูล
            for i, chunk in enumerate(chunks):
                chunk["embedding"] = embeddings[i]
                
            return chunks
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการสร้าง embeddings: {str(e)}")
            print(f"{Colors.FAIL}❌ เกิดข้อผิดพลาดในการสร้าง embeddings: {str(e)}{Colors.ENDC}")
            return []

    def insert_job_data(self, job_data: Dict[str, Any]) -> Dict[str, str]:
        """
        เพิ่มข้อมูลอาชีพลงในฐานข้อมูล
        
        Args:
            job_data: ข้อมูลอาชีพทั้งหมด
            
        Returns:
            Dict[str, str]: พจนานุกรมแมประหว่าง job_key และ job_id
        """
        print(f"{Colors.HEADER}===== กำลังเพิ่มข้อมูลอาชีพลงฐานข้อมูล ====={Colors.ENDC}")
        
        conn = self.get_connection()
        if not conn:
            return {}
            
        job_ids = {}  # เก็บแมประหว่าง job_key และ UUID
        
        try:
            with conn.cursor() as cursor:
                for job_key, job in tqdm(job_data.items(), desc="เพิ่มข้อมูลอาชีพ"):
                    # เพิ่มข้อมูลหลักของงาน
                    cursor.execute('''
                        INSERT INTO jobs (job_key, job_title, description)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (job_key) DO UPDATE
                        SET job_title = EXCLUDED.job_title,
                            description = EXCLUDED.description
                        RETURNING id
                    ''', (job_key, job.get("titles", ["Unknown"])[0], job.get("description", "")))
                    
                    job_id = cursor.fetchone()[0]
                    job_ids[job_key] = job_id
                    
                    # เพิ่มชื่องานที่หลากหลาย
                    if "titles" in job:
                        for title in job["titles"]:
                            cursor.execute('''
                                INSERT INTO job_titles (job_id, title)
                                VALUES (%s, %s)
                                ON CONFLICT DO NOTHING
                            ''', (job_id, title))
                    
                    # เพิ่มความรับผิดชอบ
                    if "responsibilities" in job:
                        # ลบข้อมูลเดิม
                        cursor.execute("DELETE FROM job_responsibilities WHERE job_id = %s", (job_id,))
                        
                        for resp in job["responsibilities"]:
                            cursor.execute('''
                                INSERT INTO job_responsibilities (job_id, responsibility)
                                VALUES (%s, %s)
                            ''', (job_id, resp))
                    
                    # เพิ่มทักษะ
                    if "skills" in job:
                        # ลบข้อมูลเดิม
                        cursor.execute("DELETE FROM job_skills WHERE job_id = %s", (job_id,))
                        
                        for skill in job["skills"]:
                            cursor.execute('''
                                INSERT INTO job_skills (job_id, skill)
                                VALUES (%s, %s)
                            ''', (job_id, skill))
                    
                    # เพิ่มเงินเดือน
                    if "salary_info" in job:
                        # ลบข้อมูลเดิม
                        cursor.execute("DELETE FROM job_salaries WHERE job_id = %s", (job_id,))
                        
                        for salary_data in job["salary_info"]:
                            if isinstance(salary_data, dict) and "experience" in salary_data and "salary" in salary_data:
                                cursor.execute('''
                                    INSERT INTO job_salaries (job_id, experience_range, salary_range)
                                    VALUES (%s, %s, %s)
                                ''', (job_id, salary_data["experience"], salary_data["salary"]))
                    
                # Commit ข้อมูล
                conn.commit()
                
                logger.info(f"เพิ่มข้อมูลอาชีพเสร็จสมบูรณ์ จำนวน {len(job_ids)} อาชีพ")
                print(f"{Colors.GREEN}✅ เพิ่มข้อมูลอาชีพเสร็จสมบูรณ์ จำนวน {len(job_ids)} อาชีพ{Colors.ENDC}")
                return job_ids
                
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"เกิดข้อผิดพลาดในการเพิ่มข้อมูลอาชีพ: {str(e)}")
            print(f"{Colors.FAIL}❌ เกิดข้อผิดพลาดในการเพิ่มข้อมูลอาชีพ: {str(e)}{Colors.ENDC}")
            return {}
        finally:
            if conn:
                conn.close()

    def process_job_vectors(self, job_data: Dict[str, Any], job_ids: Dict[str, str]) -> bool:
        """
        ประมวลผลและเพิ่ม vectors ของงานลงในฐานข้อมูล
        
        Args:
            job_data: ข้อมูลอาชีพทั้งหมด
            job_ids: พจนานุกรมแมประหว่าง job_key และ job_id
            
        Returns:
            bool: True ถ้าสำเร็จ False ถ้าล้มเหลว
        """
        print(f"{Colors.HEADER}===== กำลังสร้างและบันทึก Vectors ====={Colors.ENDC}")
        
        if not job_ids:
            logger.error("ไม่มีข้อมูล job_ids สำหรับการสร้าง vectors")
            print(f"{Colors.FAIL}❌ ไม่มีข้อมูล job_ids สำหรับการสร้าง vectors{Colors.ENDC}")
            return False
            
        conn = self.get_connection()
        if not conn:
            return False
            
        try:
            # เตรียมชิ้นส่วนข้อความทั้งหมด
            all_chunks = []
            
            print(f"{Colors.CYAN}กำลังสร้างชิ้นส่วนข้อความ...{Colors.ENDC}")
            
            for job_key, job in tqdm(job_data.items(), desc="สร้างชิ้นส่วนข้อความ"):
                if job_key not in job_ids:
                    continue
                    
                # สร้างชิ้นส่วนจากคำอธิบาย
                if "description" in job and job["description"]:
                    chunks = self.create_text_chunks(job["description"], job_key, "description")
                    all_chunks.extend(chunks)
                
                # สร้างชิ้นส่วนจากความรับผิดชอบ
                if "responsibilities" in job and job["responsibilities"]:
                    for resp in job["responsibilities"]:
                        chunks = self.create_text_chunks(resp, job_key, "responsibility")
                        all_chunks.extend(chunks)
                
                # สร้างชิ้นส่วนจากทักษะ
                if "skills" in job and job["skills"]:
                    for skill in job["skills"]:
                        chunks = self.create_text_chunks(skill, job_key, "skill")
                        all_chunks.extend(chunks)
                
                # ถ้ามี cleaned_text ให้ใช้ด้วย
                if "cleaned_text" in job and job["cleaned_text"]:
                    chunks = self.create_text_chunks(job["cleaned_text"], job_key, "full_text")
                    all_chunks.extend(chunks)
            
            # สร้าง embeddings
            print(f"{Colors.CYAN}กำลังสร้าง embeddings สำหรับ {len(all_chunks)} ชิ้นส่วน...{Colors.ENDC}")
            
            # แบ่งชุดข้อมูลเป็นกลุ่มขนาด 100 ชิ้นเพื่อไม่ให้ใช้ RAM มากเกินไป
            batch_size = 100
            total_processed = 0
            
            for i in range(0, len(all_chunks), batch_size):
                batch_chunks = all_chunks[i:i+batch_size]
                embedded_chunks = self.create_embeddings(batch_chunks)
                
                # บันทึกลงฐานข้อมูล
                with conn.cursor() as cursor:
                    for chunk in embedded_chunks:
                        job_id = job_ids.get(chunk["job_key"])
                        if not job_id:
                            continue
                            
                        cursor.execute('''
                            INSERT INTO job_vectors (job_id, chunk_type, content, embedding)
                            VALUES (%s, %s, %s, %s)
                        ''', (
                            job_id,
                            chunk["chunk_type"],
                            chunk["content"],
                            chunk["embedding"].tolist()
                        ))
                    
                    # Commit ในแต่ละกลุ่ม
                    conn.commit()
                    
                total_processed += len(embedded_chunks)
                print(f"{Colors.CYAN}ประมวลผลและบันทึกแล้ว {total_processed}/{len(all_chunks)} ชิ้นส่วน{Colors.ENDC}")
            
            logger.info(f"สร้างและบันทึก vectors เสร็จสมบูรณ์ จำนวน {total_processed} รายการ")
            print(f"{Colors.GREEN}✅ สร้างและบันทึก vectors เสร็จสมบูรณ์ จำนวน {total_processed} รายการ{Colors.ENDC}")
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"เกิดข้อผิดพลาดในการสร้างและบันทึก vectors: {str(e)}")
            print(f"{Colors.FAIL}❌ เกิดข้อผิดพลาดในการสร้างและบันทึก vectors: {str(e)}{Colors.ENDC}")
            return False
        finally:
            if conn:
                conn.close()

    def verify_db(self) -> Dict[str, int]:
        """
        ตรวจสอบจำนวนข้อมูลในฐานข้อมูล
        
        Returns:
            Dict[str, int]: จำนวนข้อมูลในแต่ละตาราง
        """
        print(f"{Colors.HEADER}===== ตรวจสอบข้อมูลในฐานข้อมูล ====={Colors.ENDC}")
        
        conn = self.get_connection()
        if not conn:
            return {}
            
        result = {}
        
        try:
            with conn.cursor() as cursor:
                tables = [
                    "jobs", 
                    "job_titles", 
                    "job_responsibilities", 
                    "job_skills", 
                    "job_salaries", 
                    "job_vectors"
                ]
                
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    result[table] = count
                    print(f"{Colors.CYAN}ตาราง {table}: {count} รายการ{Colors.ENDC}")
            
            return result
            
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการตรวจสอบข้อมูล: {str(e)}")
            print(f"{Colors.FAIL}❌ เกิดข้อผิดพลาดในการตรวจสอบข้อมูล: {str(e)}{Colors.ENDC}")
            return {}
        finally:
            if conn:
                conn.close()

    def process(self) -> bool:
        """
        ประมวลผลทั้งหมด
        
        Returns:
            bool: True ถ้าสำเร็จ False ถ้าล้มเหลว
        """
        # เริ่มเวลา
        start_time = datetime.now()
        
        print(f"{Colors.BOLD}{Colors.HEADER}===== เริ่มสร้างฐานข้อมูล Vector ====={Colors.ENDC}")
        print(f"{Colors.CYAN}เริ่มเวลา: {start_time.strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")
        
        # 1. สร้างโครงสร้างฐานข้อมูล
        if not self.create_database_schema():
            return False
        
        # 2. โหลดข้อมูลอาชีพ
        job_data = self.load_job_data()
        if not job_data:
            return False
        
        # 3. เพิ่มข้อมูลอาชีพลงฐานข้อมูล
        job_ids = self.insert_job_data(job_data)
        if not job_ids:
            return False
        
        # 4. สร้างและบันทึก vectors
        if not self.process_job_vectors(job_data, job_ids):
            return False
        
        # 5. ตรวจสอบข้อมูลในฐานข้อมูล
        self.verify_db()
        
        # คำนวณเวลาที่ใช้
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info(f"สร้างฐานข้อมูล Vector เสร็จสมบูรณ์ ใช้เวลา {duration}")
        print(f"{Colors.GREEN}✅ สร้างฐานข้อมูล Vector เสร็จสมบูรณ์!{Colors.ENDC}")
        print(f"{Colors.CYAN}⏱️ ใช้เวลาทั้งสิ้น: {duration}{Colors.ENDC}")
        
        return True

def main():
    """
    ฟังก์ชันหลักสำหรับการรันสคริปต์
    """
    parser = argparse.ArgumentParser(description='สร้างฐานข้อมูล Vector สำหรับระบบ Career AI Advisor')
    
    parser.add_argument('--input', type=str, default="data/processed/cleaned_jobs.json",
                    help='ไฟล์ข้อมูลอาชีพที่ประมวลผลแล้ว')
    parser.add_argument('--db-name', type=str, default="pctdb",
                        help='ชื่อฐานข้อมูล PostgreSQL')
    parser.add_argument('--db-user', type=str, default="PCT_admin",
                        help='ชื่อผู้ใช้ฐานข้อมูล')
    parser.add_argument('--db-password', type=str, default="pct1234",
                        help='รหัสผ่านฐานข้อมูล')
    parser.add_argument('--db-host', type=str, default="localhost",
                        help='โฮสต์ของฐานข้อมูล')
    parser.add_argument('--db-port', type=str, default="5430",  
                        help='พอร์ตของฐานข้อมูล')
    parser.add_argument('--embedding-model', type=str, default="all-MiniLM-L6-v2",
                        help='ชื่อโมเดล SentenceTransformer')
    parser.add_argument('--embedding-dim', type=int, default=384,
                        help='มิติของ embedding vector')
    parser.add_argument('--chunk-size', type=int, default=512,
                        help='ขนาดของชิ้นส่วนข้อความ (จำนวนตัวอักษร)')
    parser.add_argument('--overlap-size', type=int, default=50,
                        help='ขนาดการซ้อนทับของชิ้นส่วนข้อความ')
    
    args = parser.parse_args()
    
    try:
        # สร้างออบเจกต์ VectorDBCreator
        creator = VectorDBCreator(
            input_file=args.input,
            db_name=args.db_name,
            db_user=args.db_user,
            db_password=args.db_password,
            db_host=args.db_host,
            db_port=args.db_port,
            embedding_model=args.embedding_model,
            embedding_dim=args.embedding_dim,
            chunk_size=args.chunk_size,
            overlap_size=args.overlap_size
        )
        
        # ประมวลผล
        success = creator.process()
        
        if success:
            sys.exit(0)
        else:
            print(f"{Colors.FAIL}❌ การสร้างฐานข้อมูล Vector ล้มเหลว{Colors.ENDC}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาด: {str(e)}")
        print(f"{Colors.FAIL}❌ เกิดข้อผิดพลาด: {str(e)}{Colors.ENDC}")
        sys.exit(1)

if __name__ == "__main__":
    main()