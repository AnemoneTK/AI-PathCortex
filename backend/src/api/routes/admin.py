#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Admin routes for the Career AI Advisor API.

This module defines the routes for administration tasks.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body
from pydantic import BaseModel

from src.utils.fine_tune import FineTuneHelper
from src.utils.logger import get_logger
from src.utils.config import API_KEY

# ตั้งค่า logger
logger = get_logger("api.routes.admin")

# สร้าง router
router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    responses={404: {"description": "Not found"}},
)

# โมเดลข้อมูลสำหรับการทำ fine-tuning
class FineTuneRequest(BaseModel):
    """
    คำขอสำหรับการสร้างชุดข้อมูล fine-tuning
    """
    num_examples: int = 100
    use_existing_file: Optional[str] = None

class FineTuneResponse(BaseModel):
    """
    ผลลัพธ์จากการสร้างชุดข้อมูล fine-tuning
    """
    success: bool
    message: str
    file_path: Optional[str] = None
    examples_count: Optional[int] = None
    error: Optional[str] = None

class StartFineTuneRequest(BaseModel):
    """
    คำขอสำหรับการเริ่ม fine-tuning
    """
    data_file: str
    base_model: Optional[str] = None
    n_epochs: Optional[int] = 3

class StartFineTuneResponse(BaseModel):
    """
    ผลลัพธ์จากการเริ่ม fine-tuning
    """
    success: bool
    message: str
    job_id: Optional[str] = None
    status: Optional[str] = None
    error: Optional[str] = None

# ฟังก์ชันสำหรับตรวจสอบ admin API key
async def verify_admin_api_key(api_key: str = Depends(lambda: API_KEY)):
    """
    ตรวจสอบ admin API key
    
    Args:
        api_key: API key จาก header
        
    Returns:
        bool: True ถ้า API key ถูกต้อง
    """
    # ตรวจสอบว่ามีการตั้งค่า API_KEY หรือไม่
    if not API_KEY:
        logger.warning("ไม่ได้กำหนด API_KEY ในการตั้งค่า")
        raise HTTPException(
            status_code=401,
            detail="ไม่ได้กำหนด API key สำหรับเข้าถึงฟังก์ชัน admin",
        )
    
    return True

@router.post("/fine-tune/prepare", response_model=FineTuneResponse)
async def prepare_fine_tune_data(
    request: FineTuneRequest,
    _: bool = Depends(verify_admin_api_key)
):
    """
    สร้างชุดข้อมูลสำหรับการทำ fine-tuning
    
    Args:
        request: คำขอสำหรับการสร้างชุดข้อมูล fine-tuning
        
    Returns:
        FineTuneResponse: ผลลัพธ์จากการสร้างชุดข้อมูล fine-tuning
    """
    try:
        # สร้าง FineTuneHelper
        helper = FineTuneHelper()
        
        # ถ้ามีการระบุไฟล์ที่มีอยู่แล้ว
        if request.use_existing_file:
            logger.info(f"ใช้ไฟล์ที่มีอยู่แล้ว: {request.use_existing_file}")
            
            # ตรวจสอบว่าไฟล์มีอยู่จริงหรือไม่
            import os
            if not os.path.exists(request.use_existing_file):
                return FineTuneResponse(
                    success=False,
                    message="ไม่พบไฟล์ที่ระบุ",
                    error=f"ไม่พบไฟล์: {request.use_existing_file}"
                )
            
            # นับจำนวนตัวอย่างในไฟล์
            with open(request.use_existing_file, 'r', encoding='utf-8') as f:
                examples_count = sum(1 for _ in f)
            
            return FineTuneResponse(
                success=True,
                message="ใช้ไฟล์ที่มีอยู่แล้ว",
                file_path=request.use_existing_file,
                examples_count=examples_count
            )
        
        # สร้างชุดข้อมูลใหม่
        file_path = helper.prepare_fine_tune_data(num_examples=request.num_examples)
        
        # นับจำนวนตัวอย่างในไฟล์
        with open(file_path, 'r', encoding='utf-8') as f:
            examples_count = sum(1 for _ in f)
        
        return FineTuneResponse(
            success=True,
            message="สร้างชุดข้อมูล fine-tuning สำเร็จ",
            file_path=file_path,
            examples_count=examples_count
        )
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการสร้างชุดข้อมูล fine-tuning: {str(e)}")
        return FineTuneResponse(
            success=False,
            message="เกิดข้อผิดพลาดในการสร้างชุดข้อมูล fine-tuning",
            error=str(e)
        )

@router.post("/fine-tune/start", response_model=StartFineTuneResponse)
async def start_fine_tuning(
    request: StartFineTuneRequest,
    _: bool = Depends(verify_admin_api_key)
):
    """
    เริ่มกระบวนการ fine-tuning
    
    Args:
        request: คำขอสำหรับการเริ่ม fine-tuning
        
    Returns:
        StartFineTuneResponse: ผลลัพธ์จากการเริ่ม fine-tuning
    """
    try:
        # สร้าง FineTuneHelper
        helper = FineTuneHelper()
        
        # เริ่ม fine-tuning
        result = await helper.start_fine_tuning(request.data_file)
        
        if result["success"]:
            # ดึงข้อมูลสถานะงาน
            job_data = result.get("data", {})
            job_id = job_data.get("id", "")
            status = job_data.get("status", "created")
            
            return StartFineTuneResponse(
                success=True,
                message="เริ่มกระบวนการ fine-tuning สำเร็จ",
                job_id=job_id,
                status=status
            )
        else:
            return StartFineTuneResponse(
                success=False,
                message="เกิดข้อผิดพลาดในการเริ่ม fine-tuning",
                error=result.get("error", "ไม่ทราบสาเหตุ")
            )
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการเริ่ม fine-tuning: {str(e)}")
        return StartFineTuneResponse(
            success=False,
            message="เกิดข้อผิดพลาดในการเริ่ม fine-tuning",
            error=str(e)
        )

@router.get("/model/status")
async def get_model_status(
    _: bool = Depends(verify_admin_api_key)
):
    """
    ดึงสถานะของโมเดล
    
    Returns:
        Dict[str, Any]: สถานะของโมเดล
    """
    from src.utils.config import LLM_MODEL, FINE_TUNED_MODEL, USE_FINE_TUNED
    
    return {
        "base_model": LLM_MODEL,
        "fine_tuned_model": FINE_TUNED_MODEL or "ไม่ได้กำหนด",
        "use_fine_tuned": USE_FINE_TUNED,
        "status": "active" if FINE_TUNED_MODEL and USE_FINE_TUNED else "inactive"
    }