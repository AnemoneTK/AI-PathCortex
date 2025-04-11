#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chat routes for the Career AI Advisor API.

This module defines the routes for interacting with the AI.
"""

import os
import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body, BackgroundTasks
from pydantic import BaseModel

from src.utils.llm import chat_with_job_context, chat_with_combined_context
from src.utils.vector_search import VectorSearch
from src.utils.config import PersonalityType, VECTOR_DB_DIR
from src.utils.storage import get_user, save_chat_history
from src.api.models import ChatHistory, ChatMessage
from src.utils.logger import get_logger

# ตั้งค่า logger
logger = get_logger("api.routes.chat")

# สร้าง router
router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
    responses={404: {"description": "Not found"}},
)

# สร้าง VectorSearch
try:
    vector_search = VectorSearch(vector_db_dir=VECTOR_DB_DIR)
except Exception as e:
    logger.error(f"ไม่สามารถสร้าง VectorSearch ได้: {str(e)}")
    vector_search = None

# คลาสสำหรับรับข้อมูลคำถาม
class ChatRequest(BaseModel):
    query: str
    user_id: Optional[str] = None
    personality: Optional[PersonalityType] = PersonalityType.FRIENDLY
    use_combined_search: bool = True
    use_fine_tuned: bool = False

# คลาสสำหรับส่งคำตอบ
class ChatResponse(BaseModel):
    response: str
    search_results: List[Dict[str, Any]]
    personality: PersonalityType
    user_context: Optional[Dict[str, Any]] = None

@router.post("/", response_model=ChatResponse)
async def ask_question(
    request: ChatRequest,
    background_tasks: BackgroundTasks
):
    """
    ถามคำถามและรับคำตอบจาก AI
    
    Args:
        request: ข้อมูลคำถาม
        
    Returns:
        ChatResponse: คำตอบจาก AI
    """
    try:
        # ตรวจสอบ VectorSearch
        if vector_search is None:
            raise HTTPException(status_code=500, detail="ระบบค้นหาข้อมูลไม่พร้อมใช้งาน")
        
        # ตรวจสอบว่ามีคำถามหรือไม่
        if not request.query:
            raise HTTPException(status_code=400, detail="กรุณาระบุคำถาม")
        
        # ดึงข้อมูลผู้ใช้ (ถ้ามี)
        user_context = None
        if request.user_id:
            user = get_user(request.user_id)
            if user:
                user_context = user.dict()
        
        # ค้นหาข้อมูลที่เกี่ยวข้อง
        search_results = []
        
        if request.use_combined_search:
            # ใช้การค้นหาแบบรวม
            search_results = vector_search.search_combined(request.query, limit=5)
        else:
            # ใช้การค้นหาแบบแยกประเภท
            job_results = vector_search.search_jobs(request.query, limit=3)
            advice_results = vector_search.search_career_advices(request.query, limit=3)
            
            # รวมผลลัพธ์
            search_results = job_results + advice_results
        
        # สร้างคำตอบ
        if request.use_combined_search:
            response_text = await chat_with_combined_context(
                request.query,
                search_results,
                user_context,
                request.personality,
                request.use_fine_tuned
            )
        else:
            response_text = await chat_with_job_context(
                request.query,
                job_results,
                user_context,
                advice_results,
                request.personality,
                request.use_fine_tuned
            )
        
        # บันทึกประวัติการสนทนา
        chat_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        chat_history = ChatHistory(
            id=chat_id,
            user_id=request.user_id,
            timestamp=timestamp,
            messages=[
                ChatMessage(role="user", content=request.query),
                ChatMessage(role="assistant", content=response_text)
            ]
        )
        
        # บันทึกประวัติในพื้นหลัง
        background_tasks.add_task(save_chat_history, chat_history)
        
        # สร้าง response
        return ChatResponse(
            response=response_text,
            search_results=search_results,
            personality=request.personality,
            user_context=user_context
        )
        
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการสร้างคำตอบ: {str(e)}")
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการสร้างคำตอบ: {str(e)}")

@router.get("/personalities", response_model=List[str])
async def get_personalities():
    """
    ดึงรายการบุคลิกที่สามารถใช้ได้
    
    Returns:
        List[str]: รายการบุคลิก
    """
    return [p.value for p in PersonalityType]

@router.get("/history/{user_id}", response_model=List[ChatHistory])
async def get_user_chat_history(user_id: str = Path(..., description="รหัสผู้ใช้")):
    """
    ดึงประวัติการสนทนาของผู้ใช้
    
    Args:
        user_id: รหัสผู้ใช้
        
    Returns:
        List[ChatHistory]: รายการประวัติการสนทนา
    """
    from src.utils.storage import get_chat_history
    
    # ตรวจสอบว่ามีผู้ใช้หรือไม่
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"ไม่พบผู้ใช้ {user_id}")
    
    # ดึงประวัติการสนทนา
    history = get_chat_history(user_id)
    return history