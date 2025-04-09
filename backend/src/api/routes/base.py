
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base routes for the Career AI Advisor API.

This module defines the base routes for the API.
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from src.utils.config import get_settings
from src.utils.logger import get_logger

# ตั้งค่า logger
logger = get_logger("api.routes.base")

# สร้าง router
router = APIRouter(tags=["General"])

@router.get("/")
async def root():
    """
    API Root - ทดสอบการเข้าถึง API
    
    Returns:
        Dict[str, Any]: ข้อความแสดงผล
    """
    return {"message": "Welcome to Career AI Advisor API", "status": "online"}

@router.get("/health")
async def health_check():
    """
    ตรวจสอบสถานะของ API
    
    Returns:
        Dict[str, Any]: สถานะของ API
    """
    try:
        # ตรวจสอบการเข้าถึงโฟลเดอร์ต่างๆ
        settings = get_settings()
        
        import os
        data_dir_exists = os.path.exists(settings["data_dir"])
        vector_db_exists = os.path.exists(settings["vector_db_dir"])
        users_dir_exists = os.path.exists(settings["users_dir"])
        
        return {
            "status": "healthy",
            "data_dir_exists": data_dir_exists,
            "vector_db_exists": vector_db_exists,
            "users_dir_exists": users_dir_exists,
            "api_version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการตรวจสอบสถานะของ API: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )

@router.get("/config")
async def get_public_config():
    """
    ดึงการตั้งค่าสาธารณะ
    
    Returns:
        Dict[str, Any]: การตั้งค่าสาธารณะ
    """
    # ดึงการตั้งค่าทั้งหมด
    settings = get_settings()
    
    # กรอง sensitive และส่งคืนเฉพาะการตั้งค่าสาธารณะ
    public_settings = {
        "api_version": "1.0.0",
        "embedding_model": settings["embedding_model"],
        "llm_model": settings["llm_model"],
        "api_host": settings["api_host"],
        "api_port": settings["api_port"],
    }
    
    return public_settings

@router.get("/personalities")
async def get_personalities():
    """
    ดึงรายการบุคลิกของ AI ที่รองรับ
    
    Returns:
        Dict[str, Any]: รายการบุคลิกของ AI
    """
    from src.utils.config import PersonalityType
    
    # สร้างข้อมูลอธิบายบุคลิก
    personality_descriptions = {
        PersonalityType.FORMAL: {
            "name": "ทางการ",
            "description": "ให้ข้อมูลและคำปรึกษาด้วยคำที่ดูจริงจังและเป็นทางการ ใช้ภาษาสุภาพ หลีกเลี่ยงคำแสลง"
        },
        PersonalityType.FRIENDLY: {
            "name": "เป็นกันเอง",
            "description": "ใช้คำฟิลเพื่อนคุยเล่นกัน มีการเล่นมุกเล็กน้อย แต่ยังคงให้ข้อมูลที่เป็นประโยชน์"
        },
        PersonalityType.FUN: {
            "name": "สนุกสนาน",
            "description": "เน้นสนุกเน้นตลกหรือตอบสั้นๆ แต่ยังถูกต้อง แทรกมุกตลกหรือวลีเด็ดๆ"
        }
    }
    
    # สร้างรายการบุคลิก
    personalities = []
    for personality_type in PersonalityType:
        personalities.append({
            "value": personality_type,
            "name": personality_descriptions[personality_type]["name"],
            "description": personality_descriptions[personality_type]["description"]
        })
    
    return {"personalities": personalities}