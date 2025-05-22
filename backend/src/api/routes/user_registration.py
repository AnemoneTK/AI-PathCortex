#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ไฟล์สำหรับจัดการการลงทะเบียนผู้ใช้
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, File, UploadFile, Form, Depends
from fastapi.responses import JSONResponse

# เพิ่มการนำเข้าที่จำเป็น
from src.api.models import UserCreate, User, UserSkill, UserProject, UserWorkExperience
from src.utils.config import EducationStatus, USERS_DIR
from src.utils.storage import create_app_user, save_app_user, save_app_resume, app_user_exists, get_app_user
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
    ลงทะเบียนผู้ใช้สำหรับระบบ
    
    Args:
        user_data: ข้อมูลผู้ใช้ในรูปแบบ JSON string
        resume: ไฟล์ resume (ไม่บังคับ)
        
    Returns:
        User: ข้อมูลผู้ใช้ที่สร้างแล้ว
    """
    try:
        # แปลง JSON string เป็น dictionary
        user_dict = json.loads(user_data)
        
        logger.info(f"Received user data: {json.dumps(user_dict, ensure_ascii=False)[:200]}...")
        
        # แปลงข้อมูลให้เข้ากับโมเดล UserCreate
        education_status = EducationStatus.STUDENT
        if user_dict.get('education_status') == 'graduate':
            education_status = EducationStatus.GRADUATE
        elif user_dict.get('education_status') == 'working':
            education_status = EducationStatus.WORKING
        
        # แปลงทักษะให้เป็นรูปแบบที่ถูกต้อง
        skills = []
        for skill in user_dict.get('skills', []):
            if isinstance(skill, dict):
                # กรณีส่งมาเป็น object ที่มี name และ proficiency
                skill_obj = {"name": skill.get("name", ""), "proficiency": skill.get("proficiency", 4)}
                skills.append(UserSkill(**skill_obj))
            elif isinstance(skill, str):
                # กรณีส่งมาเป็น string
                skills.append(UserSkill(name=skill, proficiency=4))
            else:
                # กรณีอื่นๆ
                logger.warning(f"พบรูปแบบทักษะที่ไม่รองรับ: {skill}")
        
        # แปลงภาษาโปรแกรมให้เป็นรูปแบบที่ถูกต้อง
        programming_languages = []
        for lang in user_dict.get('programming_languages', []):
            if isinstance(lang, dict):
                # กรณีส่งมาเป็น object ที่มี name และ proficiency
                lang_obj = {"name": lang.get("name", ""), "proficiency": lang.get("proficiency", 4)}
                programming_languages.append(UserSkill(**lang_obj))
            elif isinstance(lang, str):
                # กรณีส่งมาเป็น string
                programming_languages.append(UserSkill(name=lang, proficiency=4))
            else:
                # กรณีอื่นๆ
                logger.warning(f"พบรูปแบบภาษาโปรแกรมที่ไม่รองรับ: {lang}")
        
        # แปลงเครื่องมือให้เป็นรูปแบบที่ถูกต้อง
        tools = []
        for tool in user_dict.get('tools', []):
            if isinstance(tool, dict):
                # กรณีส่งมาเป็น object ที่มี name และ proficiency
                tool_obj = {"name": tool.get("name", ""), "proficiency": tool.get("proficiency", 4)}
                tools.append(UserSkill(**tool_obj))
            elif isinstance(tool, str):
                # กรณีส่งมาเป็น string
                tools.append(UserSkill(name=tool, proficiency=4))
            else:
                # กรณีอื่นๆ
                logger.warning(f"พบรูปแบบเครื่องมือที่ไม่รองรับ: {tool}")
        
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
            programming_languages=programming_languages,
            tools=tools,
            projects=projects,
            work_experiences=work_experiences
        )
        
        # สร้างผู้ใช้ใหม่หรืออัปเดตผู้ใช้ที่มีอยู่แล้ว
        if app_user_exists():
            # ถ้ามีผู้ใช้อยู่แล้ว ให้อัปเดตข้อมูล
            user = get_app_user()
            
            # อัปเดตข้อมูล
            user.name = user_create.name
            user.institution = user_create.institution
            user.education_status = user_create.education_status
            user.year = user_create.year
            user.skills = user_create.skills
            user.programming_languages = user_create.programming_languages
            user.tools = user_create.tools
            user.projects = user_create.projects
            user.work_experiences = user_create.work_experiences
            user.updated_at = datetime.now().isoformat()
            
            # บันทึกข้อมูลผู้ใช้
            if not save_app_user(user):
                raise HTTPException(status_code=500, detail="ไม่สามารถอัปเดตข้อมูลผู้ใช้ได้")
            
            logger.info(f"อัปเดตข้อมูลผู้ใช้ {user.name} เรียบร้อยแล้ว")
        else:
            # ถ้ายังไม่มีผู้ใช้ ให้สร้างใหม่
            user = create_app_user(user_create)
            if not user:
                raise HTTPException(status_code=500, detail="ไม่สามารถสร้างผู้ใช้ได้")
            
            logger.info(f"สร้างผู้ใช้ใหม่ {user.name} เรียบร้อยแล้ว")
        
        # บันทึก resume ถ้ามี
        if resume:
            content = await resume.read()
            resume_path = save_app_resume(content, resume.filename)
            if resume_path:
                logger.info(f"บันทึกไฟล์ Resume ที่ {resume_path}")
                
                # อัปเดต resume_path ในข้อมูลผู้ใช้
                user.resume_path = resume_path
                save_app_user(user)
                
                logger.info("อัปเดต resume_path ในข้อมูลผู้ใช้เรียบร้อยแล้ว")
        
        return user
        
    except json.JSONDecodeError as e:
        logger.error(f"ไม่สามารถแปลงข้อมูลเป็น JSON ได้: {str(e)}")
        raise HTTPException(status_code=400, detail=f"ข้อมูลไม่ถูกต้อง: {str(e)}")
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการลงทะเบียน: {str(e)}")
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการลงทะเบียน: {str(e)}")

@router.get("/user-status")
async def check_user_status():
    """
    ตรวจสอบสถานะว่ามีข้อมูลผู้ใช้แล้วหรือไม่
    
    Returns:
        Dict[str, bool]: สถานะผู้ใช้
    """
    user_exists = app_user_exists()
    return {"user_exists": user_exists}

@router.get("/user-info")
async def get_user_info():
    """
    ดึงข้อมูลผู้ใช้ที่ลงทะเบียนไว้
    
    Returns:
        User หรือ {"user_exists": False}: ข้อมูลผู้ใช้หรือสถานะว่าไม่มีผู้ใช้
    """
    user = get_app_user()
    if user:
        return user.dict()  
    return {"user_exists": False}