#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Job routes for the Career AI Advisor API.

This module defines the routes for job information.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Path

from src.api.models import JobSummary, JobResponse, JobFilter
from src.utils.logger import get_logger
from src.utils.vector_search import VectorSearch

# ตั้งค่า logger
logger = get_logger("api.routes.jobs")

# สร้าง router
router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
    responses={404: {"description": "Not found"}},
)

# ฟังก์ชันสำหรับดึง VectorSearch instance
def get_vector_search():
    """
    ดึง VectorSearch instance
    
    Returns:
        VectorSearch: instance ของ VectorSearch
    """
    # นำเข้า vector_db_dir จาก config
    from src.utils.config import VECTOR_DB_DIR
    
    # สร้าง VectorSearch instance
    return VectorSearch(VECTOR_DB_DIR)

@router.get("/", response_model=List[JobSummary])
async def list_jobs(
    title: Optional[str] = Query(None, description="กรองตามชื่อตำแหน่ง"),
    skill: Optional[str] = Query(None, description="กรองตามทักษะ"),
    limit: int = Query(20, description="จำนวนผลลัพธ์สูงสุด", ge=1, le=100),
    vector_search: VectorSearch = Depends(get_vector_search),
):
    """
    ดึงรายการอาชีพตามเงื่อนไข
    
    Args:
        title: กรองตามชื่อตำแหน่ง
        skill: กรองตามทักษะ
        limit: จำนวนผลลัพธ์สูงสุด
        vector_search: instance ของ VectorSearch
        
    Returns:
        List[JobSummary]: รายการอาชีพ
    """
    try:
        # สร้างตัวกรอง
        filters = {}
        if title:
            filters["title"] = title
        if skill:
            filters["skill"] = skill
        
        # ใช้ VectorSearch
        # ถ้าไม่มีคำค้นหา ให้ใช้คำทั่วไป
        search_query = title or skill or "software development"
        results = vector_search.search_jobs(search_query, limit=limit, filters=filters)
        
        # แปลงเป็น JobSummary
        job_summaries = [
            JobSummary(id=result["id"], title=result["title"]) 
            for result in results
        ]
        
        return job_summaries
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการดึงรายการอาชีพ: {str(e)}")
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการดึงรายการอาชีพ: {str(e)}")

@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str = Path(..., description="รหัสอาชีพ"),
    vector_search: VectorSearch = Depends(get_vector_search),
):
    """
    ดึงข้อมูลอาชีพ
    
    Args:
        job_id: รหัสอาชีพ
        vector_search: instance ของ VectorSearch
        
    Returns:
        JobResponse: ข้อมูลอาชีพ
    """
    try:
        # ดึงข้อมูลอาชีพ
        job_data = vector_search.get_job_by_id(job_id)
        
        if not job_data:
            raise HTTPException(status_code=404, detail=f"ไม่พบอาชีพ {job_id}")
        
        # แปลงเป็น JobResponse
        job_response = JobResponse(
            id=job_data["id"],
            titles=job_data["titles"],
            description=job_data["description"],
            skills=job_data.get("skills", []),
            responsibilities=job_data.get("responsibilities", []),
            salary_ranges=job_data.get("salary_ranges", []),
            education_requirements=job_data.get("education_requirements", [])
        )
        
        return job_response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการดึงข้อมูลอาชีพ: {str(e)}")
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการดึงข้อมูลอาชีพ: {str(e)}")

@router.post("/search", response_model=List[JobSummary])
async def search_jobs(
    job_filter: JobFilter,
    limit: int = Query(20, description="จำนวนผลลัพธ์สูงสุด", ge=1, le=100),
    vector_search: VectorSearch = Depends(get_vector_search),
):
    """
    ค้นหาอาชีพตามตัวกรอง
    
    Args:
        job_filter: ตัวกรองสำหรับการค้นหางาน
        limit: จำนวนผลลัพธ์สูงสุด
        vector_search: instance ของ VectorSearch
        
    Returns:
        List[JobSummary]: รายการอาชีพ
    """
    try:
        # สร้างตัวกรอง
        filters = {}
        if job_filter.title:
            filters["title"] = job_filter.title
        if job_filter.skill:
            filters["skill"] = job_filter.skill
        if job_filter.experience_range:
            filters["experience"] = job_filter.experience_range
        
        # ใช้ VectorSearch
        # ถ้าไม่มีคำค้นหา ให้ใช้คำทั่วไป
        search_query = job_filter.title or job_filter.skill or "software development"
        results = vector_search.search_jobs(search_query, limit=limit, filters=filters)
        
        # แปลงเป็น JobSummary
        job_summaries = [
            JobSummary(id=result["id"], title=result["title"]) 
            for result in results
        ]
        
        return job_summaries
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการค้นหาอาชีพ: {str(e)}")
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการค้นหาอาชีพ: {str(e)}")

@router.get("/recommend/for-user", response_model=List[JobSummary])
async def recommend_jobs_for_user(
    limit: int = Query(5, description="จำนวนอาชีพที่แนะนำ", ge=1, le=20),
    vector_search: VectorSearch = Depends(get_vector_search),
):
    """
    แนะนำอาชีพสำหรับผู้ใช้
    
    Args:
        user_id: รหัสผู้ใช้
        limit: จำนวนอาชีพที่แนะนำ
        vector_search: instance ของ VectorSearch
        
    Returns:
        List[JobSummary]: รายการอาชีพที่แนะนำ
    """
    try:
        # ดึงข้อมูลผู้ใช้
        from src.utils.storage import get_app_user
        user = get_app_user()
        if not user:
            raise HTTPException(status_code=404, detail=f"ไม่พบข้อมูลผู้ใช้")
        
        # สร้างคำค้นหาจากข้อมูลผู้ใช้
        search_terms = []
        
        # เพิ่มภาษาโปรแกรม
        if user.programming_languages:
            search_terms.extend(user.programming_languages[:3])  # ใช้แค่ 3 ภาษาแรก
        
        # เพิ่มทักษะที่มีระดับสูง
        high_skills = [skill.name for skill in user.skills if skill.proficiency >= 4]
        if high_skills:
            search_terms.extend(high_skills[:3])  # ใช้แค่ 3 ทักษะแรก
        
        # ถ้าไม่มีคำค้นหา ให้ใช้คำทั่วไป
        if not search_terms:
            search_terms = ["software development"]
        
        # สร้างคำค้นหา
        search_query = " ".join(search_terms)
        
        # ค้นหาอาชีพ
        results = vector_search.search_jobs(search_query, limit=limit)
        
        # แปลงเป็น JobSummary
        job_summaries = [
            JobSummary(id=result["id"], title=result["title"]) 
            for result in results
        ]
        
        return job_summaries
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการแนะนำอาชีพสำหรับผู้ใช้: {str(e)}")
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการแนะนำอาชีพสำหรับผู้ใช้: {str(e)}")