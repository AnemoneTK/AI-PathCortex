#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chat routes for the Career AI Advisor API.

This module defines the routes for chat interactions.
"""

import os
import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Path, BackgroundTasks

from src.api.models import ChatRequest, ChatResponse, ChatHistory, ChatHistoryResponse
from src.utils.config import PersonalityType
from src.utils.logger import get_logger
from src.utils.storage import get_user, save_chat_history, get_chat_history
from src.utils.llm import chat_with_job_context
from src.utils.vector_search import VectorSearch

# ตั้งค่า logger
logger = get_logger("api.routes.chat")

# สร้าง router
router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
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

@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    vector_search: VectorSearch = Depends(get_vector_search),
):
    """
    สนทนากับ AI
    
    Args:
        request: คำขอสนทนา
        background_tasks: งานที่ทำในพื้นหลัง
        vector_search: instance ของ VectorSearch
        
    Returns:
        ChatResponse: คำตอบจาก AI
    """
    try:
        # ดึงข้อมูลผู้ใช้ (ถ้ามี)
        user_context = None
        if request.user_id:
            from src.utils.storage import get_user
            user = get_user(request.user_id)
            if user:
                user_context = user.dict()
        
        # ค้นหาข้อมูลอาชีพที่เกี่ยวข้อง
        job_results = vector_search.search_jobs(request.query, limit=3)
        
        # ค้นหาคำแนะนำที่เกี่ยวข้อง
        advice_results = vector_search.search_career_advices(request.query, limit=2)
        
        # สร้างคำตอบจาก LLM
        answer = await chat_with_job_context(
            query=request.query,
            job_contexts=job_results,
            user_context=user_context,
            advice_contexts=advice_results,
            personality=request.personality
        )
        
        # สร้างแหล่งข้อมูล
        sources = []
        for job in job_results:
            sources.append({
                "content": job["description"][:150] + "..." if len(job["description"]) > 150 else job["description"],
                "job_title": job["title"],
                "type": "job",
                "similarity": job["similarity_score"]
            })
        
        for advice in advice_results:
            sources.append({
                "content": advice["title"],
                "job_title": "",
                "type": "advice",
                "similarity": advice["similarity_score"]
            })
        
        # บันทึกประวัติการสนทนา (ในพื้นหลัง)
        chat_history = ChatHistory(
            id=str(uuid.uuid4()),
            user_id=request.user_id,
            query=request.query,
            answer=answer,
            personality=request.personality,
            sources=sources,
            timestamp=None  # ใช้ค่าเริ่มต้น
        )
        background_tasks.add_task(save_chat_history, chat_history)
        
        return ChatResponse(answer=answer, sources=sources)
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการสนทนา: {str(e)}")
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการสนทนา: {str(e)}")

@router.get("/history", response_model=ChatHistoryResponse)
async def get_chat_history_api(
    user_id: Optional[str] = Query(None, description="รหัสผู้ใช้"),
    limit: int = Query(10, description="จำนวนประวัติการสนทนาที่ต้องการ", ge=1, le=100)
):
    """
    ดึงประวัติการสนทนา
    
    Args:
        user_id: รหัสผู้ใช้ (ถ้ามี)
        limit: จำนวนประวัติการสนทนาที่ต้องการ
        
    Returns:
        ChatHistoryResponse: ประวัติการสนทนา
    """
    try:
        # ตรวจสอบว่าผู้ใช้มีอยู่จริง (ถ้าระบุ user_id)
        if user_id:
            from src.utils.storage import get_user
            user = get_user(user_id)
            if not user:
                raise HTTPException(status_code=404, detail=f"ไม่พบผู้ใช้ {user_id}")
        
        # ดึงประวัติการสนทนา
        history = get_chat_history(user_id, limit)
        
        return ChatHistoryResponse(
            user_id=user_id,
            history=history,
            count=len(history)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการดึงประวัติการสนทนา: {str(e)}")
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการดึงประวัติการสนทนา: {str(e)}")

@router.post("/personality", response_model=ChatResponse)
async def chat_with_personality(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    personality: PersonalityType = Query(PersonalityType.FRIENDLY, description="รูปแบบบุคลิกของ AI"),
    vector_search: VectorSearch = Depends(get_vector_search),
):
    """
    สนทนากับ AI โดยระบุบุคลิก
    
    Args:
        request: คำขอสนทนา
        background_tasks: งานที่ทำในพื้นหลัง
        personality: รูปแบบบุคลิกของ AI
        vector_search: instance ของ VectorSearch
        
    Returns:
        ChatResponse: คำตอบจาก AI
    """
    # กำหนดบุคลิก
    request.personality = personality
    
    # เรียกใช้ API chat ปกติ
    return await chat(request, background_tasks, vector_search)