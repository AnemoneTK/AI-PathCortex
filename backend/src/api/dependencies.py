#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dependencies for the Career AI Advisor API.

This module defines the dependencies used in the API.
"""

from typing import Optional
from fastapi import Header, HTTPException, Depends
from fastapi.security import APIKeyHeader

from src.utils.config import API_KEY
from src.utils.logger import get_logger
from src.utils.vector_search import VectorSearch

# ตั้งค่า logger
logger = get_logger("api.dependencies")

# สร้าง API key security scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Depends(api_key_header)):
    """
    ตรวจสอบ API key
    
    Args:
        api_key: API key จาก header
        
    Returns:
        bool: True ถ้า API key ถูกต้อง
    """
    # ถ้าไม่ได้กำหนด API_KEY ไว้ในการตั้งค่า ไม่ต้องตรวจสอบ
    if not API_KEY:
        return True
    
    if api_key != API_KEY:
        logger.warning(f"มีการพยายามเข้าถึง API ด้วย API key ที่ไม่ถูกต้อง")
        raise HTTPException(
            status_code=401,
            detail="API key ไม่ถูกต้อง",
            headers={"WWW-Authenticate": "API key header"},
        )
    
    return True

def get_vector_search_dependency():
    """
    ฟังก์ชันสำหรับสร้าง VectorSearch dependency
    
    Returns:
        VectorSearch: instance ของ VectorSearch
    """
    # นำเข้า vector_db_dir จาก config
    from src.utils.config import VECTOR_DB_DIR
    
    # สร้าง VectorSearch instance
    try:
        vector_search = VectorSearch(VECTOR_DB_DIR)
        return vector_search
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการสร้าง VectorSearch: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"เกิดข้อผิดพลาดในการสร้าง VectorSearch: {str(e)}",
        )

async def get_user_from_header(x_user_id: Optional[str] = Header(None)):
    """
    ดึงข้อมูลผู้ใช้จาก header
    
    Args:
        x_user_id: รหัสผู้ใช้จาก header
        
    Returns:
        Optional[Dict[str, Any]]: ข้อมูลผู้ใช้ หรือ None ถ้าไม่พบ
    """
    if not x_user_id:
        return None
    
    # ดึงข้อมูลผู้ใช้
    from src.utils.storage import get_user
    user = get_user(x_user_id)
    
    return user

async def common_parameters(
    personality: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    x_chat_id: Optional[str] = Header(None),
):
    """
    พารามิเตอร์ที่ใช้ร่วมกันสำหรับหลาย API endpoints
    
    Args:
        personality: รูปแบบบุคลิกของ AI จาก header
        x_user_id: รหัสผู้ใช้จาก header
        x_chat_id: รหัสการสนทนาจาก header
        
    Returns:
        Dict[str, Any]: พารามิเตอร์ที่ใช้ร่วมกัน
    """
    # แปลงบุคลิกเป็น PersonalityType enum
    if personality:
        from src.utils.config import PersonalityType
        try:
            personality = PersonalityType(personality)
        except ValueError:
            personality = PersonalityType.FRIENDLY
    else:
        from src.utils.config import PersonalityType
        personality = PersonalityType.FRIENDLY
    
    return {
        "personality": personality,
        "user_id": x_user_id,
        "chat_id": x_chat_id,
    }