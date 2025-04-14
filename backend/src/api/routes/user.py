#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
User routes for the Career AI Advisor API.

This module defines the routes for user management.
"""

import os
import json
import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Path, File, UploadFile, Form, BackgroundTasks
from fastapi.responses import FileResponse

# เพิ่มการนำเข้า EducationStatus จาก config
from src.utils.config import EducationStatus
from src.api.models import User, UserCreate, UserUpdate, UserSummary, ResumeUploadResponse, UserSkill, UserProject, UserWorkExperience
from src.utils.storage import (
    create_app_user, get_app_user, update_app_user, save_app_user, app_user_exists,
    save_app_resume, get_app_resume_path
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

@router.get("/", response_model=User)
async def get_user_info():
    """
    ดึงข้อมูลผู้ใช้
    
    Returns:
        User: ข้อมูลผู้ใช้
    """
    user = get_app_user()
    if not user:
        raise HTTPException(status_code=404, detail="ไม่พบข้อมูลผู้ใช้")
    return user

@router.post("/", response_model=User)
async def create_new_user(
    name: str = Form(...),
    institution: Optional[str] = Form(None),
    education_status: str = Form("student"),  # รับเป็น string แทน Enum
    year: int = Form(1),
    skills: str = Form("[]"),  # JSON string
    programming_languages: str = Form("[]"),  # เปลี่ยนเป็น JSON string
    tools: str = Form("[]"),  # เปลี่ยนเป็น JSON string
    projects: str = Form("[]"),  # JSON string
    work_experiences: str = Form("[]"),  # JSON string
    resume: Optional[UploadFile] = File(None)
):
    """
    สร้างผู้ใช้ใหม่
    
    Args:
        name: ชื่อผู้ใช้
        institution: สถาบันการศึกษา
        education_status: สถานะการศึกษา
        year: ชั้นปี
        skills: ทักษะในรูปแบบ JSON string
        programming_languages: ภาษาโปรแกรมในรูปแบบ JSON string
        tools: เครื่องมือในรูปแบบ JSON string
        projects: โปรเจกต์ในรูปแบบ JSON string
        work_experiences: ประสบการณ์ทำงานในรูปแบบ JSON string
        resume: ไฟล์ resume
        
    Returns:
        User: ข้อมูลผู้ใช้ที่สร้างแล้ว
    """
    try:
        # แปลง education_status เป็น Enum
        edu_status = EducationStatus.STUDENT
        if education_status == "graduate":
            edu_status = EducationStatus.GRADUATE
        elif education_status == "working":
            edu_status = EducationStatus.WORKING
        
        # แปลง JSON strings
        skills_data = json.loads(skills)
        programming_languages_data = json.loads(programming_languages)
        tools_data = json.loads(tools)
        projects_data = json.loads(projects)
        work_experiences_data = json.loads(work_experiences)
        
        # แปลงทักษะให้เป็นรูปแบบที่ถูกต้อง
        skills_objects = []
        for skill in skills_data:
            if isinstance(skill, dict):
                skills_objects.append(UserSkill(**skill))
            elif isinstance(skill, str):
                skills_objects.append(UserSkill(name=skill, proficiency=4))
        
        # แปลงภาษาโปรแกรมให้เป็นรูปแบบที่ถูกต้อง
        programming_languages_objects = []
        for lang in programming_languages_data:
            if isinstance(lang, dict):
                programming_languages_objects.append(UserSkill(**lang))
            elif isinstance(lang, str):
                programming_languages_objects.append(UserSkill(name=lang, proficiency=4))
        
        # แปลงเครื่องมือให้เป็นรูปแบบที่ถูกต้อง
        tools_objects = []
        for tool in tools_data:
            if isinstance(tool, dict):
                tools_objects.append(UserSkill(**tool))
            elif isinstance(tool, str):
                tools_objects.append(UserSkill(name=tool, proficiency=4))
        
        # แปลงโปรเจกต์ให้เป็นรูปแบบที่ถูกต้อง
        projects_objects = []
        for project in projects_data:
            if isinstance(project, dict):
                projects_objects.append(UserProject(**project))
        
        # แปลงประสบการณ์ทำงานให้เป็นรูปแบบที่ถูกต้อง
        work_experiences_objects = []
        for work in work_experiences_data:
            if isinstance(work, dict):
                work_experiences_objects.append(UserWorkExperience(**work))
        
        # สร้าง UserCreate object
        user_data = UserCreate(
            name=name,
            institution=institution,
            education_status=edu_status,
            year=year,
            skills=skills_objects,
            programming_languages=programming_languages_objects,
            tools=tools_objects,
            projects=projects_objects,
            work_experiences=work_experiences_objects
        )
        
        # ตรวจสอบว่ามีข้อมูลผู้ใช้อยู่แล้วหรือไม่
        if app_user_exists():
            # อัปเดตข้อมูลผู้ใช้เดิม
            user = get_app_user()
            user.name = user_data.name
            user.institution = user_data.institution
            user.education_status = user_data.education_status
            user.year = user_data.year
            user.skills = user_data.skills
            user.programming_languages = user_data.programming_languages
            user.tools = user_data.tools
            user.projects = user_data.projects
            user.work_experiences = user_data.work_experiences
            user.updated_at = datetime.now().isoformat()
            if not save_app_user(user):
                raise HTTPException(status_code=500, detail="ไม่สามารถอัปเดตข้อมูลผู้ใช้ได้")
        else:
            # สร้างผู้ใช้ใหม่
            user = create_app_user(user_data)
            if not user:
                raise HTTPException(status_code=500, detail="ไม่สามารถสร้างผู้ใช้ได้")
        
        # บันทึก resume ถ้ามี
        if resume:
            content = await resume.read()
            resume_path = save_app_resume(content, resume.filename)
            if resume_path:
                logger.info(f"บันทึกไฟล์ Resume ที่ {resume_path}")
                # อัปเดต resume_path ในข้อมูลผู้ใช้
                user.resume_path = resume_path
                save_app_user(user)
        
        return user
        
    except json.JSONDecodeError as e:
        logger.error(f"ข้อมูล JSON ไม่ถูกต้อง: {str(e)}")
        raise HTTPException(status_code=400, detail=f"ข้อมูล JSON ไม่ถูกต้อง: {str(e)}")
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการสร้างผู้ใช้: {str(e)}")
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการสร้างผู้ใช้: {str(e)}")

@router.get("/default", response_model=User)
async def get_default_user():
    """
    ดึงข้อมูลผู้ใช้
    
    Returns:
        User: ข้อมูลผู้ใช้
    """
    user = get_app_user()
    if not user:
        raise HTTPException(status_code=404, detail="ไม่พบข้อมูลผู้ใช้")
    return user

@router.patch("/", response_model=User)
async def update_user_info(user_data: UserUpdate):
    """
    อัปเดตข้อมูลผู้ใช้
    
    Args:
        user_data: ข้อมูลผู้ใช้ที่ต้องการอัปเดต
        
    Returns:
        User: ข้อมูลผู้ใช้ที่อัปเดตแล้ว
    """
    user = update_app_user(user_data)
    if not user:
        raise HTTPException(status_code=404, detail="ไม่พบข้อมูลผู้ใช้หรือไม่สามารถอัปเดตได้")
    return user

@router.delete("/")
async def delete_user_info():
    """
    ลบข้อมูลผู้ใช้
    
    Returns:
        Dict[str, Any]: ผลลัพธ์การลบผู้ใช้
    """
    # ตรวจสอบก่อนว่ามีผู้ใช้หรือไม่
    user = get_app_user()
    if not user:
        raise HTTPException(status_code=404, detail="ไม่พบข้อมูลผู้ใช้")
    
    # ลบข้อมูลผู้ใช้
    from src.utils.storage import delete_app_user
    success = delete_app_user()
    
    if not success:
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการลบข้อมูลผู้ใช้")
    
    return {"message": "ลบข้อมูลผู้ใช้เรียบร้อยแล้ว"}

@router.get("/user-status")
async def check_user_status():
    """
    ตรวจสอบสถานะว่ามีข้อมูลผู้ใช้แล้วหรือไม่
    
    Returns:
        Dict[str, bool]: สถานะผู้ใช้
    """
    user_exists = app_user_exists()
    return {"user_exists": user_exists}