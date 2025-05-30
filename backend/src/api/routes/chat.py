#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chat routes for the Career AI Advisor API.

This module defines the routes for interacting with the AI.
"""

import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime 
from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body, BackgroundTasks
from pydantic import BaseModel

# นำเข้าฟังก์ชันและโมดูลที่จำเป็น
from src.utils.llm import safe_chat_with_context  # import จากไฟล์ llm.py ใหม่
from src.utils.vector_search import VectorSearch
from src.utils.config import PersonalityType, VECTOR_DB_DIR
from src.utils.storage import get_app_user, create_chat_message, save_chat_history
from src.api.models import ChatHistory, ChatMessage, ChatResponse, ChatRequest
from src.utils.logger import get_logger

# ตั้งค่า logger
logger = get_logger("api.routes.chat")

# สร้าง router - ใช้ prefix แบบเดิมคือ /chat/
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
        if not request.message:
            raise HTTPException(status_code=400, detail="กรุณาระบุคำถาม")
        
        # ดึงข้อมูลผู้ใช้เดียวในระบบ
        user_context = None
        user = get_app_user()
        if user:
            user_context = user.dict()
        
        # ค้นหาข้อมูลที่เกี่ยวข้อง
        search_results = []
        
        # Set default values for optional attributes
        use_combined_search = getattr(request, 'use_combined_search', True)
        use_fine_tuned = getattr(request, 'use_fine_tuned', False)
        
        if use_combined_search and vector_search is not None:
            # ใช้การค้นหาแบบรวม
            search_results = vector_search.search_combined(request.message, limit=5)
        else:
            # ใช้การค้นหาแบบแยกประเภท
            job_results = vector_search.search_jobs(request.message, limit=3)
            advice_results = vector_search.search_career_advices(request.message, limit=3)
            
            # เพิ่มคีย์ type ถ้าไม่มีในผลลัพธ์
            for job in job_results:
                if "type" not in job:
                    job["type"] = "job"
            
            for advice in advice_results:
                if "type" not in advice:
                    advice["type"] = "advice"
            
            # รวมผลลัพธ์
            search_results = job_results + advice_results
        
        # ใช้ฟังก์ชัน safe_chat_with_context ใหม่
        response_text = await safe_chat_with_context(
            query=request.message,
            search_results=search_results,
            user_context=user_context,
            personality=request.personality,
            use_fine_tuned=use_fine_tuned
        )
        
        # สร้างและบันทึกประวัติการสนทนา
        chat_history = create_chat_message(request.message, response_text)
        
        # บันทึกประวัติในพื้นหลัง
        background_tasks.add_task(save_chat_history, chat_history)
        
        # สร้าง response
        return ChatResponse(
            chat_id=chat_history.id,
            message=response_text,
            search_results=search_results
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

@router.get("/history", response_model=List[ChatHistory])
async def get_user_chat_history(
    limit: int = Query(10, description="จำนวนประวัติการสนทนาที่ต้องการ", ge=1, le=100)
):
    """
    ดึงประวัติการสนทนาของผู้ใช้
    
    Args:
        limit: จำนวนประวัติการสนทนาที่ต้องการ
        
    Returns:
        List[ChatHistory]: รายการประวัติการสนทนา
    """
    from src.utils.storage import get_chat_history
    
    # ดึงประวัติการสนทนา
    history = get_chat_history(limit=limit)
    return history

@router.post("/query", response_model=ChatResponse)
async def query_chat(request: ChatRequest):
    """
    ส่งคำถามไปยัง LLM และรับคำตอบกลับมา
    
    Args:
        request: คำถามและบุคลิกของ AI
        
    Returns:
        ChatResponse: คำตอบจาก LLM
    """
    try:
        # ดึงข้อมูลผู้ใช้
        user_context = None
        user = get_app_user()
        if user:
            user_context = user.dict()
        
        # ตรวจสอบ VectorSearch
        if vector_search is None:
            raise HTTPException(status_code=500, detail="ระบบค้นหาข้อมูลไม่พร้อมใช้งาน")
        
        # ใช้การค้นหาแบบรวม
        search_results = vector_search.search_combined(request.message, limit=5)
        
        # ใช้ฟังก์ชันใหม่
        response = await safe_chat_with_context(
            query=request.message,
            search_results=search_results,
            user_context=user_context,
            personality=request.personality
        )
        
        # สร้างประวัติการสนทนา
        chat_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        chat_history = ChatHistory(
            id=chat_id,
            user_id="app_user",
            timestamp=timestamp,
            messages=[
                ChatMessage(role="user", content=request.message),
                ChatMessage(role="assistant", content=response)
            ]
        )
        
        # บันทึกประวัติการสนทนา (ข้ามหากเกิดข้อผิดพลาด)
        try:
            save_chat_history(chat_history)
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการบันทึกประวัติการสนทนา: {str(e)}")
        
        return ChatResponse(
            chat_id=chat_id,
            message=response,
            search_results=search_results
        )
    
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการส่งคำถามไปยัง LLM: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"เกิดข้อผิดพลาดในการส่งคำถามไปยัง LLM: {str(e)}"
        )