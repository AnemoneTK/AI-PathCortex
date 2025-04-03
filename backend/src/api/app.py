#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Career AI Advisor - API Service

บริการ API สำหรับระบบ Career AI Advisor ที่ใช้ FastAPI และฐานข้อมูล PostgreSQL + pgvector
สำหรับให้บริการแนะนำอาชีพด้าน IT และตอบคำถามเกี่ยวกับอาชีพต่างๆ
"""

import os
import json
import logging
import psycopg
import uvicorn
import asyncio
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# โหลดค่าจากไฟล์ .env (ถ้ามี)
load_dotenv()

# ตั้งค่าการบันทึกล็อก
log_dir = Path("logs")
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "api.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("career_api")

# ตั้งค่า FastAPI
app = FastAPI(
    title="Career AI Advisor API",
    description="API สำหรับระบบให้คำปรึกษาด้านอาชีพด้วย AI",
    version="1.0.0"
)

# เพิ่ม CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # สำหรับการพัฒนา (ควรระบุ domain ที่แน่นอนในการใช้งานจริง)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ตั้งค่าการเชื่อมต่อฐานข้อมูล
DB_NAME = os.getenv("DB_NAME", "pctdb")
DB_USER = os.getenv("DB_USER", "PCT_admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "pct1234")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5430")

# ตั้งค่าโมเดล Embedding
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
# AI Model Configuration
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1:latest")
LLM_API_BASE = os.getenv("LLM_API_BASE", "http://localhost:11434")

# API Key (ถ้ามี)
API_KEY = os.getenv("API_KEY", "")

# โหลดโมเดล SentenceTransformer
try:
    embedder = SentenceTransformer(f"sentence-transformers/{EMBEDDING_MODEL}")
    logger.info(f"โหลดโมเดล {EMBEDDING_MODEL} เรียบร้อย")
except Exception as e:
    logger.error(f"ไม่สามารถโหลดโมเดล {EMBEDDING_MODEL} ได้: {str(e)}")
    raise e

# ฟังก์ชันสำหรับเชื่อมต่อฐานข้อมูล
def get_db_connection():
    """
    สร้างการเชื่อมต่อกับฐานข้อมูล PostgreSQL
    
    Returns:
        psycopg.Connection: การเชื่อมต่อกับฐานข้อมูล
    """
    try:
        conn = psycopg.connect(
            f"dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD} host={DB_HOST} port={DB_PORT}"
        )
        return conn
    except Exception as e:
        logger.error(f"ไม่สามารถเชื่อมต่อกับฐานข้อมูลได้: {str(e)}")
        return None

# โมเดล Pydantic
class QueryRequest(BaseModel):
    """คำขอสำหรับการค้นหาข้อมูล"""
    query: str = Field(..., description="คำค้นหาหรือคำถาม")
    limit: int = Field(5, description="จำนวนผลลัพธ์ที่ต้องการ")
    
class QueryResult(BaseModel):
    """ผลลัพธ์จากการค้นหา"""
    content: str = Field(..., description="เนื้อหาที่ค้นพบ")
    job_title: str = Field(..., description="ชื่อตำแหน่งงาน")
    chunk_type: str = Field(..., description="ประเภทของข้อมูล")
    similarity: float = Field(..., description="คะแนนความใกล้เคียง")
    
class ChatRequest(BaseModel):
    """คำขอสำหรับการสนทนา"""
    query: str = Field(..., description="คำถามจากผู้ใช้")
    
class ChatResponse(BaseModel):
    """การตอบกลับการสนทนา"""
    answer: str = Field(..., description="คำตอบจากระบบ")
    sources: List[Dict[str, Any]] = Field([], description="แหล่งข้อมูลที่ใช้")

class JobFilter(BaseModel):
    """ตัวกรองสำหรับการค้นหางาน"""
    skill: Optional[str] = Field(None, description="ทักษะที่ต้องการ")
    experience_range: Optional[str] = Field(None, description="ช่วงประสบการณ์")
    title: Optional[str] = Field(None, description="ชื่อตำแหน่งงาน")
    
class JobResponse(BaseModel):
    """ข้อมูลอาชีพ"""
    id: str = Field(..., description="รหัสอาชีพ")
    job_key: str = Field(..., description="คีย์อาชีพ")
    job_title: str = Field(..., description="ชื่อตำแหน่งงาน")
    description: str = Field(..., description="คำอธิบายอาชีพ")
    skills: List[str] = Field([], description="ทักษะที่ต้องการ")
    responsibilities: List[str] = Field([], description="ความรับผิดชอบ")
    salary_info: List[Dict[str, str]] = Field([], description="ข้อมูลเงินเดือน")
    
class JobSummary(BaseModel):
    """ข้อมูลสรุปอาชีพ"""
    job_key: str = Field(..., description="คีย์อาชีพ")
    job_title: str = Field(..., description="ชื่อตำแหน่งงาน")

# API Routes
@app.get("/", tags=["General"])
async def root():
    """API Root - ทดสอบการเข้าถึง API"""
    return {"message": "Career AI Advisor API"}

@app.post("/query", response_model=List[QueryResult], tags=["Search"])
async def search_query(request: QueryRequest):
    """
    ค้นหาข้อมูลด้วย semantic search
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="คำค้นหาต้องไม่เป็นค่าว่าง")
    
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="ไม่สามารถเชื่อมต่อฐานข้อมูลได้")
    
    try:
        # สร้าง embedding สำหรับคำค้นหา
        query_embedding = embedder.encode(request.query).tolist()
        
        cursor = conn.cursor()
        # ใช้ฟังก์ชัน cosine_distance สำหรับการค้นหา (คะแนนยิ่งน้อยยิ่งดี)
        cursor.execute('''
            SELECT jv.content, j.job_title, jv.chunk_type, 
                   (1 - (jv.embedding <=> %s::vector)) AS similarity
            FROM job_vectors jv
            JOIN jobs j ON jv.job_id = j.id
            ORDER BY similarity DESC
            LIMIT %s
        ''', (query_embedding, request.limit))
        
        results = cursor.fetchall()
        
        # จัดรูปแบบผลลัพธ์
        formatted_results = []
        for content, job_title, chunk_type, similarity in results:
            formatted_results.append(QueryResult(
                content=content,
                job_title=job_title,
                chunk_type=chunk_type,
                similarity=float(similarity)
            ))
        
        return formatted_results
    
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการค้นหา: {str(e)}")
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการค้นหา: {str(e)}")
    
    finally:
        conn.close()

@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    สนทนาและตอบคำถามเกี่ยวกับอาชีพ
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="คำถามต้องไม่เป็นค่าว่าง")
    
    try:
        # ค้นหาข้อมูลที่เกี่ยวข้องจากฐานข้อมูล
        conn = get_db_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="ไม่สามารถเชื่อมต่อฐานข้อมูลได้")
        
        try:
            # สร้าง embedding สำหรับคำค้นหา
            query_embedding = embedder.encode(request.query).tolist()
            
            cursor = conn.cursor()
            # ใช้ฟังก์ชัน cosine_distance สำหรับการค้นหา
            # หมายเหตุ: ไม่สามารถใช้ similarity ในส่วน WHERE ได้โดยตรง
            # เพราะเป็น alias ที่คำนวณใน SELECT
            cursor.execute('''
                SELECT jv.content, j.job_title, jv.chunk_type, 
                       (1 - (jv.embedding <=> %s::vector)) AS similarity
                FROM job_vectors jv
                JOIN jobs j ON jv.job_id = j.id
                ORDER BY similarity DESC
                LIMIT 5
            ''', (query_embedding,))
            
            results = cursor.fetchall()
            
            # จัดรูปแบบผลลัพธ์เพื่อใช้ในการสร้างคำตอบ
            sources = []
            context_parts = []
            
            for content, job_title, chunk_type, similarity in results:
                # กรองเฉพาะผลลัพธ์ที่มีความเกี่ยวข้องเพียงพอ
                if similarity < 0.2:
                    continue
                    
                sources.append({
                    "content": content[:150] + "..." if len(content) > 150 else content,
                    "job_title": job_title,
                    "chunk_type": chunk_type,
                    "similarity": float(similarity)
                })
                
                context_parts.append(f"ตำแหน่ง: {job_title} ({chunk_type})\n{content}")
            
            # เตรียม context สำหรับ LLM
            context = "\n\n".join(context_parts) if context_parts else "ไม่พบข้อมูลที่เกี่ยวข้อง"
            
        finally:
            conn.close()
        
        # สร้าง prompt สำหรับ LLM
        prompt = f"""
        คุณเป็นที่ปรึกษาด้านอาชีพ IT ที่ให้คำแนะนำแก่นักศึกษาวิทยาการคอมพิวเตอร์และผู้สนใจงานด้าน IT
        ตอบคำถามเกี่ยวกับอาชีพและตำแหน่ง เพื่อช่วยพัฒนาทักษะ หรือเตรียมตัวเข้าทำงาน เป็นภาษาไทย
        ใช้ข้อมูลต่อไปนี้เป็นหลักในการตอบ และอ้างอิงชื่อตำแหน่งงานเพื่อให้คำตอบน่าเชื่อถือ

        กฎสำหรับการตอบ:
        1. ถ้าผู้ใช้พิมพ์ชื่ออาชีพผิด ไม่ต้องบอกว่าผิด ให้เติมคำว่า "หรือ" ตามด้วยชื่อที่ถูกต้อง
        2. เมื่อกล่าวถึงเงินเดือน ให้เสริมว่า "เงินเดือนอาจแตกต่างกันตามโครงสร้างบริษัท ขนาดบริษัท และภูมิภาค"
        3. ถ้าผู้ใช้ไม่รู้ว่าตัวเองถนัดอะไร ให้ถามว่า "ช่วยบอกสกิล ภาษาโปรแกรม หรือเครื่องมือที่เคยใช้ 
           โปรเจกต์ที่เคยทำ หรือประเมินทักษะของตัวเองแต่ละด้านจาก 1-5 คะแนนได้ไหม"
        4. ตอบให้กระชับ มีหัวข้อ หรือรายการข้อสั้นๆ เพื่อให้อ่านง่าย
        5. ถ้าไม่มีข้อมูลเพียงพอในการตอบคำถาม ให้ตอบว่า "ขออภัย ฉันไม่มีข้อมูลเพียงพอในการตอบคำถามนี้"
        
        ข้อมูล:
        {context}

        คำถาม: {request.query}
        คำตอบ:
        """
        
        # ใช้ LLM API เพื่อสร้างคำตอบ
        answer = await generate_from_llm(prompt)
        
        return ChatResponse(answer=answer, sources=sources)
    
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการสนทนา: {str(e)}")
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการสนทนา: {str(e)}")

@app.get("/jobs", response_model=List[JobSummary], tags=["Jobs"])
async def list_jobs(
    title: Optional[str] = Query(None, description="กรองตามชื่อตำแหน่ง"),
    skill: Optional[str] = Query(None, description="กรองตามทักษะ"),
    limit: int = Query(20, description="จำนวนผลลัพธ์สูงสุด")
):
    """
    ดึงรายการอาชีพตามเงื่อนไข
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="ไม่สามารถเชื่อมต่อฐานข้อมูลได้")
    
    try:
        cursor = conn.cursor()
        
        # สร้างคำสั่ง SQL พื้นฐาน
        sql = "SELECT j.id, j.job_key, j.job_title FROM jobs j"
        params = []
        
        # เพิ่มเงื่อนไขการกรอง
        where_clauses = []
        
        if title:
            where_clauses.append("j.job_title ILIKE %s")
            params.append(f"%{title}%")
        
        if skill:
            sql += " JOIN job_skills js ON j.id = js.job_id"
            where_clauses.append("js.skill ILIKE %s")
            params.append(f"%{skill}%")
        
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
        
        sql += " ORDER BY j.job_title LIMIT %s"
        params.append(limit)
        
        cursor.execute(sql, params)
        results = cursor.fetchall()
        
        # จัดรูปแบบผลลัพธ์
        jobs = []
        for id, job_key, job_title in results:
            jobs.append(JobSummary(job_key=job_key, job_title=job_title))
        
        return jobs
    
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการดึงรายการอาชีพ: {str(e)}")
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการดึงรายการอาชีพ: {str(e)}")
    
    finally:
        conn.close()

@app.get("/jobs/{job_key}", response_model=JobResponse, tags=["Jobs"])
async def get_job(job_key: str):
    """
    ดึงข้อมูลอาชีพตาม job_key
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="ไม่สามารถเชื่อมต่อฐานข้อมูลได้")
    
    try:
        cursor = conn.cursor()
        
        # ดึงข้อมูลหลักของอาชีพ
        cursor.execute('''
            SELECT id, job_key, job_title, description
            FROM jobs
            WHERE job_key = %s
        ''', (job_key,))
        
        job_data = cursor.fetchone()
        
        if not job_data:
            raise HTTPException(status_code=404, detail=f"ไม่พบข้อมูลอาชีพสำหรับ key: {job_key}")
        
        job_id, job_key, job_title, description = job_data
        
        # ดึงข้อมูลทักษะ
        cursor.execute('''
            SELECT skill FROM job_skills
            WHERE job_id = %s
        ''', (job_id,))
        
        skills = [row[0] for row in cursor.fetchall()]
        
        # ดึงข้อมูลความรับผิดชอบ
        cursor.execute('''
            SELECT responsibility FROM job_responsibilities
            WHERE job_id = %s
        ''', (job_id,))
        
        responsibilities = [row[0] for row in cursor.fetchall()]
        
        # ดึงข้อมูลเงินเดือน
        cursor.execute('''
            SELECT experience_range, salary_range FROM job_salaries
            WHERE job_id = %s
        ''', (job_id,))
        
        salary_info = [
            {"experience": row[0], "salary": row[1]}
            for row in cursor.fetchall()
        ]
        
        # สร้างและส่งคืนข้อมูลอาชีพ
        job = JobResponse(
            id=str(job_id),
            job_key=job_key,
            job_title=job_title,
            description=description,
            skills=skills,
            responsibilities=responsibilities,
            salary_info=salary_info
        )
        
        return job
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการดึงข้อมูลอาชีพ: {str(e)}")
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการดึงข้อมูลอาชีพ: {str(e)}")
    
    finally:
        conn.close()

# ฟังก์ชันสร้างคำตอบจาก LLM
async def generate_from_llm(prompt: str) -> str:
    """
    สร้างคำตอบจาก LLM โดยใช้ API
    
    Args:
        prompt: Prompt สำหรับ LLM
        
    Returns:
        str: คำตอบจาก LLM
    """
    try:
        import httpx
        
        # ใช้ httpx เพื่อเรียก Ollama API หรือ API อื่นๆ
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{LLM_API_BASE}/api/generate",
                json={
                    "model": LLM_MODEL,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60.0  # กำหนด timeout เพื่อป้องกันการค้างเมื่อ API ไม่ตอบสนอง
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "ไม่สามารถสร้างคำตอบได้")
            else:
                logger.error(f"LLM API ตอบกลับด้วย status code: {response.status_code}, {response.text}")
                return "ขณะนี้ระบบไม่สามารถสร้างคำตอบได้ กรุณาลองใหม่ในภายหลัง"
                
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการสร้างคำตอบจาก LLM: {str(e)}")
        return f"ขณะนี้ระบบไม่สามารถสร้างคำตอบได้: {str(e)}"

# รัน API Server
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)