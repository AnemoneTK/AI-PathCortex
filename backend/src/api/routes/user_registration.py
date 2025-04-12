#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ไฟล์สำหรับจัดการการลงทะเบียนผู้ใช้
"""

import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, File, UploadFile, Form, Depends
from fastapi.responses import JSONResponse

# เพิ่มการนำเข้าที่จำเป็น
from src.api.models import UserCreate, User, UserSkill, UserProject, UserWorkExperience
from src.utils.config import EducationStatus, USERS_DIR, UPLOADS_DIR
from src.utils.storage import create_user, save_resume, update_user_to_combined_file
from src.utils.logger import get_logger

# ตั้งค่า logger
logger = get_logger("api.routes.user_registration")

# สร้าง router
router = APIRouter(
    prefix="/registration",
    tags=["Registration"],
    responses={404: {"description": "Not found"}},
)

@router.post("/")
async def register_user(
    user_data: str = Form(...),
    resume: Optional[UploadFile] = File(None)
):
    """
    ลงทะเบียนผู้ใช้ใหม่พร้อมรับไฟล์ resume (ถ้ามี)
    
    Args:
        user_data: ข้อมูลผู้ใช้ในรูปแบบ JSON string
        resume: ไฟล์ resume (ไม่บังคับ)
        
    Returns:
        User: ข้อมูลผู้ใช้ที่สร้างแล้ว
    """
    try:
        # แปลง JSON string เป็น dictionary
        user_dict = json.loads(user_data)
        
        # แปลงข้อมูลให้เข้ากับโมเดล UserCreate
        education_status = EducationStatus.STUDENT
        if user_dict.get('education_status') == 'graduate':
            education_status = EducationStatus.GRADUATE
        elif user_dict.get('education_status') == 'working':
            education_status = EducationStatus.WORKING
        
        # แปลงทักษะให้เป็นรูปแบบที่ถูกต้อง
        skills = []
        for skill in user_dict.get('skills', []):
            skills.append(UserSkill(**skill if isinstance(skill, dict) else {"name": skill, "proficiency": 4}))
        
        # แปลงโปรเจกต์ให้เป็นรูปแบบที่ถูกต้อง
        projects = []
        for project in user_dict.get('projects', []):
            projects.append(UserProject(**project))
        
        # แปลงประสบการณ์ทำงานให้เป็นรูปแบบที่ถูกต้อง
        work_experiences = []
        for work in user_dict.get('work_experiences', []):
            work_experiences.append(UserWorkExperience(**work))
        
        # สร้าง UserCreate object
        user_create = UserCreate(
            name=user_dict.get('name', ''),
            institution=user_dict.get('institution', ''),
            education_status=education_status,
            year=user_dict.get('year', 1),
            skills=skills,
            programming_languages=user_dict.get('programming_languages', []),
            tools=user_dict.get('tools', []),
            projects=projects,
            work_experiences=work_experiences
        )
        
        # สร้างผู้ใช้
        user = create_user(user_create)
        if not user:
            raise HTTPException(status_code=500, detail="ไม่สามารถสร้างผู้ใช้ได้")
        
        # บันทึก resume ถ้ามี
        if resume:
            content = await resume.read()
            resume_path = save_resume(user.id, content, resume.filename)
            if resume_path:
                logger.info(f"บันทึกไฟล์ Resume สำหรับผู้ใช้ {user.id} ที่ {resume_path}")
                
                # อัปเดตข้อมูลผู้ใช้ใน combined file
                update_user_to_combined_file(user)
        
        return user
        
    except json.JSONDecodeError as e:
        logger.error(f"ไม่สามารถแปลงข้อมูลเป็น JSON ได้: {str(e)}")
        raise HTTPException(status_code=400, detail=f"ข้อมูลไม่ถูกต้อง: {str(e)}")
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการลงทะเบียน: {str(e)}")
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการลงทะเบียน: {str(e)}")