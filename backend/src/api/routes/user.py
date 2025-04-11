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
from src.utils.storage import (
    create_user, get_user, update_user, delete_user, list_users, 
    save_resume, get_resume_path, update_user_to_combined_file, 
    remove_user_from_combined_file  
)
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
    
    # อัปเดตข้อมูลผู้ใช้ในไฟล์รวม
    update_user_to_combined_file(user)
    
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
    
    # อัปเดตข้อมูลผู้ใช้ในไฟล์รวม
    update_user_to_combined_file(user)
    
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
    
    # ลบข้อมูลผู้ใช้จากไฟล์รวม
    remove_user_from_combined_file(user_id)
    
    return {"message": f"ลบผู้ใช้ {user_id} เรียบร้อยแล้ว"}