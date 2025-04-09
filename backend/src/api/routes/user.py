#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
User routes for the Career AI Advisor API.

This module defines the routes for user management.
"""

import os
import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Path, File, UploadFile, Form, BackgroundTasks
from fastapi.responses import FileResponse

from src.api.models import User, UserCreate, UserUpdate, UserSummary, ResumeUploadResponse
from src.utils.storage import create_user, get_user, update_user, delete_user, list_users, save_resume, get_resume_path
from src.utils.logger import get_logger

# ตั้งค่า logger
logger = get_logger("api.routes.users")

# สร้าง router
router = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[UserSummary])
async def get_users():
    """
    ดึงรายชื่อผู้ใช้ทั้งหมด
    
    Returns:
        List[UserSummary]: รายชื่อผู้ใช้
    """
    users = list_users()
    return [UserSummary.parse_obj(user) for user in users]

@router.post("/", response_model=User)
async def create_new_user(user_data: UserCreate):
    """
    สร้างผู้ใช้ใหม่
    
    Args:
        user_data: ข้อมูลผู้ใช้
        
    Returns:
        User: ข้อมูลผู้ใช้ที่สร้างแล้ว
    """
    user = create_user(user_data)
    if not user:
        raise HTTPException(status_code=500, detail="ไม่สามารถสร้างผู้ใช้ได้")
    return user

@router.get("/{user_id}", response_model=User)
async def get_user_info(user_id: str = Path(..., description="รหัสผู้ใช้")):
    """
    ดึงข้อมูลผู้ใช้
    
    Args:
        user_id: รหัสผู้ใช้
        
    Returns:
        User: ข้อมูลผู้ใช้
    """
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"ไม่พบผู้ใช้ {user_id}")
    return user

@router.patch("/{user_id}", response_model=User)
async def update_user_info(
    user_data: UserUpdate,
    user_id: str = Path(..., description="รหัสผู้ใช้")
):
    """
    อัปเดตข้อมูลผู้ใช้
    
    Args:
        user_data: ข้อมูลผู้ใช้ที่ต้องการอัปเดต
        user_id: รหัสผู้ใช้
        
    Returns:
        User: ข้อมูลผู้ใช้ที่อัปเดตแล้ว
    """
    user = update_user(user_id, user_data)
    if not user:
        raise HTTPException(status_code=404, detail=f"ไม่พบผู้ใช้ {user_id}")
    return user

@router.delete("/{user_id}")
async def delete_user_info(user_id: str = Path(..., description="รหัสผู้ใช้")):
    """
    ลบผู้ใช้
    
    Args:
        user_id: รหัสผู้ใช้
        
    Returns:
        Dict[str, Any]: ผลลัพธ์การลบผู้ใช้
    """
    if not delete_user(user_id):
        raise HTTPException(status_code=404, detail=f"ไม่พบผู้ใช้ {user_id}")
    return {"message": f"ลบผู้ใช้ {user_id} เรียบร้อยแล้ว"}

@router.post("/{user_id}/resume", response_model=ResumeUploadResponse)
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Path(..., description="รหัสผู้ใช้")
):
    """
    อัปโหลดไฟล์ Resume
    
    Args:
        file: ไฟล์ Resume
        user_id: รหัสผู้ใช้
        background_tasks: งานที่ทำในพื้นหลัง
        
    Returns:
        ResumeUploadResponse: ผลลัพธ์การอัปโหลดไฟล์ Resume
    """
    # ตรวจสอบว่าผู้ใช้มีอยู่จริง
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"ไม่พบผู้ใช้ {user_id}")
    
    # ตรวจสอบประเภทไฟล์
    allowed_types = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="รองรับเฉพาะไฟล์ PDF และ Word เท่านั้น")
    
    # บันทึกไฟล์
    file_path = save_resume(user_id, file.file, file.filename)
    if not file_path:
        raise HTTPException(status_code=500, detail="ไม่สามารถบันทึกไฟล์ได้")
    
    # สร้างผลลัพธ์
    return ResumeUploadResponse(
        success=True,
        file_name=os.path.basename(file_path),
        content_type=file.content_type,
        message="อัปโหลดไฟล์ Resume สำเร็จ"
    )

@router.get("/{user_id}/resume")
async def download_resume(user_id: str = Path(..., description="รหัสผู้ใช้")):
    """
    ดาวน์โหลดไฟล์ Resume
    
    Args:
        user_id: รหัสผู้ใช้
        
    Returns:
        FileResponse: ไฟล์ Resume
    """
    # ดึงพาธของไฟล์ Resume
    resume_path = get_resume_path(user_id)
    if not resume_path:
        raise HTTPException(status_code=404, detail="ไม่พบไฟล์ Resume สำหรับผู้ใช้นี้")
    
    # สร้าง FileResponse
    return FileResponse(
        path=resume_path,
        filename=os.path.basename(resume_path),
        media_type="application/octet-stream"
    )