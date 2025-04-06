#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Career AI Advisor - API Service (ใช้ FAISS โดยตรง)

บริการ API สำหรับระบบ Career AI Advisor ที่ใช้ FastAPI และ FAISS โดยตรง
สำหรับให้บริการแนะนำอาชีพด้าน IT และตอบคำถามเกี่ยวกับอาชีพต่างๆ
"""

import os
import json
import logging
import faiss
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

# ปรับพาธให้สัมพัทธ์กับไฟล์ปัจจุบัน
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", os.path.join(BASE_DIR, "data/vector_db/job_knowledge/faiss_index.bin"))
METADATA_PATH = os.getenv("METADATA_PATH", os.path.join(BASE_DIR, "data/vector_db/job_knowledge/job_metadata.json"))

# ตั้งค่าโมเดล Embedding
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")

# AI Model Configuration
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1:latest")
LLM_API_BASE = os.getenv("LLM_API_BASE", "http://localhost:11434")

# API Key (ถ้ามี)
API_KEY = os.getenv("API_KEY", "")

# Global variables สำหรับ FAISS และ metadata
faiss_index = None
job_metadata = None

# โหลดโมเดล SentenceTransformer
try:
    embedder = SentenceTransformer(EMBEDDING_MODEL)
    logger.info(f"โหลดโมเดล {EMBEDDING_MODEL} เรียบร้อย")
except Exception as e:
    logger.error(f"ไม่สามารถโหลดโมเดล {EMBEDDING_MODEL} ได้: {str(e)}")
    raise e

# โมเดล Pydantic
class QueryRequest(BaseModel):
    """คำขอสำหรับการค้นหาข้อมูล"""
    query: str = Field(..., description="คำค้นหาหรือคำถาม")
    limit: int = Field(5, description="จำนวนผลลัพธ์ที่ต้องการ")
    
class QueryResult(BaseModel):
    """ผลลัพธ์จากการค้นหา"""
    content: str = Field(..., description="เนื้อหาที่ค้นพบ")
    job_title: str = Field(..., description="ชื่อตำแหน่งงาน")
    type: str = Field(..., description="ประเภทของข้อมูล (description, responsibilities, skills)")
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
    titles: List[str] = Field(..., description="ชื่อตำแหน่งงาน")
    description: str = Field(..., description="คำอธิบายอาชีพ")
    skills: List[str] = Field([], description="ทักษะที่ต้องการ")
    responsibilities: List[str] = Field([], description="ความรับผิดชอบ")
    salary_ranges: List[Dict[str, Any]] = Field([], description="ข้อมูลเงินเดือน")
    
class JobSummary(BaseModel):
    """ข้อมูลสรุปอาชีพ"""
    id: str = Field(..., description="รหัสอาชีพ")
    title: str = Field(..., description="ชื่อตำแหน่งงาน")

# ฟังก์ชันสำหรับโหลด FAISS index และ metadata
def load_faiss_and_metadata():
    """
    โหลด FAISS index และ metadata
    
    Returns:
        tuple: (faiss_index, metadata)
    """
    global faiss_index, job_metadata
    
    # ตรวจสอบการมีอยู่ของไฟล์
    if not os.path.exists(FAISS_INDEX_PATH):
        logger.error(f"ไม่พบไฟล์ FAISS index ที่: {FAISS_INDEX_PATH}")
        raise FileNotFoundError(f"ไม่พบไฟล์ FAISS index ที่: {FAISS_INDEX_PATH}")
        
    if not os.path.exists(METADATA_PATH):
        logger.error(f"ไม่พบไฟล์ metadata ที่: {METADATA_PATH}")
        raise FileNotFoundError(f"ไม่พบไฟล์ metadata ที่: {METADATA_PATH}")
    
    # ... (โค้ดที่เหลือเหมือนเดิม)
    
    try:
        # โหลด FAISS index ถ้ายังไม่ได้โหลด
        if faiss_index is None:
            faiss_index = faiss.read_index(FAISS_INDEX_PATH)
            logger.info(f"โหลด FAISS index สำเร็จ: {faiss_index.ntotal} vectors, dimension {faiss_index.d}")
        
        # โหลด metadata ถ้ายังไม่ได้โหลด
        if job_metadata is None:
            with open(METADATA_PATH, 'r', encoding='utf-8') as f:
                job_metadata = json.load(f)
            logger.info(f"โหลด metadata สำเร็จ: {len(job_metadata['job_ids'])} อาชีพ")
        
        return faiss_index, job_metadata
    
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการโหลดข้อมูล: {str(e)}")
        raise e

# ฟังก์ชันสำหรับค้นหาข้อมูลโดยใช้ FAISS
def search_with_faiss(query: str, limit: int = 5):
    """
    ค้นหาข้อมูลโดยใช้ FAISS
    
    Args:
        query: คำค้นหา
        limit: จำนวนผลลัพธ์ที่ต้องการ
        
    Returns:
        list: ผลการค้นหา
    """
    index, metadata = load_faiss_and_metadata()
    
    # สร้าง embedding สำหรับคำค้นหา
    query_vector = embedder.encode([query])
    
    # ค้นหาใน FAISS
    distances, indices = index.search(query_vector, limit)
    
    # แปลงผลลัพธ์
    results = []
    for i, idx in enumerate(indices[0]):
        if idx == -1:  # ถ้า FAISS ไม่พบผลลัพธ์
            continue
            
        # ดึงข้อมูลจาก metadata
        job_id = metadata["job_ids"][idx]
        job_data = None
        
        # หาข้อมูลอาชีพจาก job_id
        for job in metadata["job_data"]:
            if job["id"] == job_id:
                job_data = job
                break
        
        if job_data is None:
            continue
        
        # ประมวลผลประเภทของข้อมูล (description, responsibilities, skills, etc.)
        content_type = "description"  # ค่าเริ่มต้น
        content = job_data["description"]
        
        # สร้างข้อมูลสำหรับผลลัพธ์
        job_title = job_data["titles"][0] if job_data["titles"] else job_id
        
        # คำนวณคะแนนความคล้ายคลึง (1 - ระยะทาง)
        similarity = 1.0 - float(distances[0][i])
        
        results.append({
            "content": content,
            "job_title": job_title,
            "type": content_type,
            "similarity": similarity
        })
    
    return results

# Event: เมื่อเริ่ม app
@app.on_event("startup")
async def startup_event():
    """ทำงานเมื่อเริ่มต้น API"""
    try:
        # โหลด FAISS และ metadata เพื่อตรวจสอบว่าทำงานได้
        load_faiss_and_metadata()
        logger.info("เริ่มต้น API สำเร็จ")
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการเริ่มต้น API: {str(e)}")

# API Routes
@app.get("/", tags=["General"])
async def root():
    """API Root - ทดสอบการเข้าถึง API"""
    return {"message": "Career AI Advisor API"}

@app.post("/query", response_model=List[QueryResult], tags=["Search"])
async def search_query(request: QueryRequest):
    """
    ค้นหาข้อมูลด้วย semantic search โดยใช้ FAISS
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="คำค้นหาต้องไม่เป็นค่าว่าง")
    
    try:
        # ค้นหาข้อมูลด้วย FAISS
        results = search_with_faiss(request.query, request.limit)
        
        # แปลงผลลัพธ์เป็น QueryResult
        formatted_results = []
        for result in results:
            formatted_results.append(QueryResult(
                content=result["content"],
                job_title=result["job_title"],
                type=result["type"],
                similarity=result["similarity"]
            ))
        
        return formatted_results
    
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการค้นหา: {str(e)}")
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการค้นหา: {str(e)}")

@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    สนทนาและตอบคำถามเกี่ยวกับอาชีพ
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="คำถามต้องไม่เป็นค่าว่าง")
    
    try:
        # ค้นหาข้อมูลที่เกี่ยวข้องด้วย FAISS
        search_results = search_with_faiss(request.query, limit=5)
        
        # เตรียมข้อมูลแหล่งข้อมูลและบริบท
        sources = []
        context_parts = []
        
        for result in search_results:
            # กรองเฉพาะผลลัพธ์ที่มีความเกี่ยวข้องเพียงพอ
            if result["similarity"] < 0.15:
                continue
                
            sources.append({
                "content": result["content"][:150] + "..." if len(result["content"]) > 150 else result["content"],
                "job_title": result["job_title"],
                "type": result["type"],
                "similarity": result["similarity"]
            })
            
            context_parts.append(f"ตำแหน่ง: {result['job_title']} ({result['type']})\n{result['content']}")
        
        # เตรียม context สำหรับ LLM
        context = "\n\n".join(context_parts) if context_parts else "ไม่พบข้อมูลที่เกี่ยวข้อง"
        
        # สร้าง prompt สำหรับ LLM
        prompt = f"""
        คุณเป็นที่ปรึกษาด้านอาชีพให้คำแนะนำแก่นักศึกษาวิทยาการคอมพิวเตอร์และผู้สนใจงานด้าน IT
        ตอบคำถามเกี่ยวกับอาชีพและตำแหน่ง เพื่อช่วยพัฒนาทักษะ หรือเตรียมตัวเข้าทำงาน เป็นภาษาไทย
        ใช้ข้อมูลต่อไปนี้เป็นหลักในการตอบ และอ้างอิงชื่อตำแหน่งงานเพื่อให้คำตอบน่าเชื่อถือ

        และตอบแบบฟิลเพื่อนคุยกันปกติ ไม่ต้องทางการมาก เป็นกันเอง มีการยิงมุกบ้าง

        กฎสำหรับการตอบ:
        1. ถ้าผู้ใช้พิมพ์ชื่ออาชีพผิด ไม่ต้องบอกว่าผิด ให้เติมคำว่า "หรือ" ตามด้วยชื่อที่ถูกต้อง
        2. กรณีที่มีการถามถึงเงินเดือน ให้เสริมว่า "เงินเดือนอาจแตกต่างกันตามโครงสร้างบริษัท ขนาดบริษัท และภูมิภาค"
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
    try:
        # โหลด metadata
        _, metadata = load_faiss_and_metadata()
        jobs = metadata["job_data"]
        
        # กรองตามเงื่อนไข
        filtered_jobs = []
        
        for job in jobs:
            # กรองตามชื่อ
            if title and not any(title.lower() in t.lower() for t in job["titles"]):
                continue
                
            # กรองตามทักษะ
            if skill and not any(skill.lower() in s.lower() for s in job.get("skills", [])):
                continue
                
            # เพิ่มลงในผลลัพธ์
            filtered_jobs.append(job)
            
            # จำกัดจำนวนผลลัพธ์
            if len(filtered_jobs) >= limit:
                break
        
        # แปลงเป็น JobSummary
        result = []
        for job in filtered_jobs:
            result.append(JobSummary(
                id=job["id"],
                title=job["titles"][0] if job["titles"] else job["id"]
            ))
        
        return result
    
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการดึงรายการอาชีพ: {str(e)}")
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการดึงรายการอาชีพ: {str(e)}")

@app.get("/jobs/{job_id}", response_model=JobResponse, tags=["Jobs"])
async def get_job(job_id: str):
    """
    ดึงข้อมูลอาชีพตาม job_id
    """
    try:
        # โหลด metadata
        _, metadata = load_faiss_and_metadata()
        
        # ค้นหาอาชีพจาก job_id
        job_data = None
        for job in metadata["job_data"]:
            if job["id"] == job_id:
                job_data = job
                break
                
        if job_data is None:
            raise HTTPException(status_code=404, detail=f"ไม่พบข้อมูลอาชีพสำหรับ ID: {job_id}")
        
        # สร้างและส่งคืนข้อมูลอาชีพ
        return JobResponse(
            id=job_data["id"],
            titles=job_data["titles"],
            description=job_data["description"],
            skills=job_data.get("skills", []),
            responsibilities=job_data.get("responsibilities", []),
            salary_ranges=job_data.get("salary_ranges", [])
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการดึงข้อมูลอาชีพ: {str(e)}")
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการดึงข้อมูลอาชีพ: {str(e)}")

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
# รัน API Server
if __name__ == "__main__":
    # พิมพ์พาธของไฟล์เพื่อตรวจสอบ
    print(f"Current working directory: {os.getcwd()}")
    print(f"FAISS index path: {os.path.abspath(FAISS_INDEX_PATH)}")
    print(f"Metadata path: {os.path.abspath(METADATA_PATH)}")
    
    # ตรวจสอบการมีอยู่ของไฟล์
    faiss_exists = os.path.exists(FAISS_INDEX_PATH)
    metadata_exists = os.path.exists(METADATA_PATH)
    
    print(f"FAISS index exists: {faiss_exists}")
    print(f"Metadata exists: {metadata_exists}")
    
    # รัน uvicorn โดยใช้ตัวแปร app โดยตรง
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)