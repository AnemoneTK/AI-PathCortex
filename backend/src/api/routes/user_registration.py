#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ไฟล์สำหรับจัดการการลงทะเบียนผู้ใช้ - ใช้สำหรับเพิ่มเข้าไปในโค้ดที่มีอยู่
"""

import os
import sys
import uuid
import json
import shutil
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, File, UploadFile, Form, Depends
from fastapi.responses import JSONResponse

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))  
sys.path.append(project_root)

from src.api.models import UserCreate, User, UserSkill, UserProject, UserWorkExperience
from src.utils.config import EducationStatus
from src.utils.storage import create_user, save_resume
from src.utils.logger import get_logger

# ตั้งค่า logger
logger = get_logger("api.routes.user_registration")

# ถ้าต้องการใช้ router ที่มีอยู่แล้ว
# router = existing_router

# กรณีต้องการสร้าง router ใหม่
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
        if user_dict.get('education', {}).get('status') == 'graduate':
            education_status = EducationStatus.GRADUATE
        elif user_dict.get('education', {}).get('status') == 'working':
            education_status = EducationStatus.WORKING
        
        # แปลงทักษะให้เป็นรูปแบบที่ถูกต้อง
        skills = []
        for skill_name in user_dict.get('skills', []):
            skills.append(UserSkill(name=skill_name, proficiency=4))  # ค่าเริ่มต้น proficiency = 4
        
        # แปลงโปรเจกต์ให้เป็นรูปแบบที่ถูกต้อง
        projects = []
        for project_data in user_dict.get('projects', []):
            project = UserProject(
                name=project_data.get('name', ''),
                description=project_data.get('description', ''),
                technologies=project_data.get('technologies', []),
                role=project_data.get('role', '')
            )
            projects.append(project)
        
        # สร้าง UserCreate object
        user_create = UserCreate(
            name=user_dict.get('name', ''),
            institution=user_dict.get('education', {}).get('institution', ''),
            education_status=education_status,
            year=user_dict.get('education', {}).get('year', 1),
            skills=skills,
            programming_languages=user_dict.get('programmingLanguages', []),
            tools=user_dict.get('tools', []),
            projects=projects,
            work_experiences=[]  # ยังไม่มีข้อมูลประสบการณ์ทำงานในฟอร์มลงทะเบียน
        )
        
        # สร้างผู้ใช้
        user = create_user(user_create)
        if not user:
            raise HTTPException(status_code=500, detail="ไม่สามารถสร้างผู้ใช้ได้")
        
        # บันทึก resume ถ้ามี
        if resume:
            resume_path = await save_resume(user.id, resume.file, resume.filename)
            if resume_path:
                logger.info(f"บันทึกไฟล์ Resume สำหรับผู้ใช้ {user.id} ที่ {resume_path}")
        
        return user
        
    except json.JSONDecodeError:
        logger.error("ไม่สามารถแปลงข้อมูลผู้ใช้เป็น JSON ได้")
        raise HTTPException(status_code=400, detail="ข้อมูลผู้ใช้ไม่ถูกต้อง")
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการลงทะเบียน: {str(e)}")
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการลงทะเบียน: {str(e)}")


# เพิ่ม API Route สำหรับการบันทึกข้อมูลเป็นไฟล์ JSON ในโฟลเดอร์โดยตรง
# กรณีใช้สำหรับการทดสอบหรือยังไม่ได้เชื่อมต่อกับระบบฐานข้อมูล
@router.post("/simple")
async def register_user_simple(
    user_data: str = Form(...),
    resume: Optional[UploadFile] = File(None)
):
    """
    ลงทะเบียนผู้ใช้ใหม่แบบง่าย เก็บข้อมูลเป็นไฟล์ JSON
    
    Args:
        user_data: ข้อมูลผู้ใช้ในรูปแบบ JSON string
        resume: ไฟล์ resume (ไม่บังคับ)
        
    Returns:
        Dict: ข้อมูลผู้ใช้ที่สร้างแล้วพร้อม ID
    """
    try:
        # แปลง JSON string เป็น dictionary
        user_dict = json.loads(user_data)
        
        # สร้าง ID สำหรับผู้ใช้
        user_id = str(uuid.uuid4())
        user_dict['id'] = user_id
        
        # กำหนดวันที่สร้างและอัปเดต
        from datetime import datetime
        current_time = datetime.now().isoformat()
        user_dict['created_at'] = current_time
        user_dict['updated_at'] = current_time
        
        # กำหนดโฟลเดอร์สำหรับเก็บข้อมูลผู้ใช้
        # จะต้องปรับตามโครงสร้างโฟลเดอร์ของโปรเจกต์
        data_dir = os.path.join(project_root,"app", "data")
        users_dir = os.path.join(data_dir, "users")
        uploads_dir = os.path.join(data_dir, "uploads")
        
        # สร้างโฟลเดอร์ถ้ายังไม่มี
        os.makedirs(users_dir, exist_ok=True)
        os.makedirs(uploads_dir, exist_ok=True)
        
        # สร้างโฟลเดอร์สำหรับผู้ใช้นี้
        user_upload_dir = os.path.join(uploads_dir, user_id)
        os.makedirs(user_upload_dir, exist_ok=True)
        
        # บันทึกข้อมูลผู้ใช้เป็นไฟล์ JSON
        user_file = os.path.join(users_dir, f"{user_id}.json")
        with open(user_file, 'w', encoding='utf-8') as f:
            json.dump(user_dict, f, ensure_ascii=False, indent=2)
        
        # บันทึก resume ถ้ามี
        resume_path = None
        if resume:
            # กำหนดชื่อไฟล์
            filename = resume.filename
            _, ext = os.path.splitext(filename)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            new_filename = f"resume_{timestamp}{ext}"
            
            # กำหนดพาธของไฟล์
            resume_path = os.path.join(user_upload_dir, new_filename)
            
            # บันทึกไฟล์
            with open(resume_path, 'wb') as f:
                content = await resume.read()
                f.write(content)
            
            # อัปเดตข้อมูลผู้ใช้ให้มี resume_path
            user_dict['resume_path'] = resume_path
            with open(user_file, 'w', encoding='utf-8') as f:
                json.dump(user_dict, f, ensure_ascii=False, indent=2)
                
            logger.info(f"บันทึกไฟล์ Resume สำหรับผู้ใช้ {user_id} ที่ {resume_path}")
        
        # ตรวจสอบว่าต้องเพิ่มข้อมูลผู้ใช้เข้าไปในไฟล์รวมหรือไม่
        all_users_file = os.path.join(users_dir, "users.json")
        all_users = []
        
        # อ่านข้อมูลที่มีอยู่ (ถ้ามี)
        if os.path.exists(all_users_file):
            try:
                with open(all_users_file, 'r', encoding='utf-8') as f:
                    all_users = json.load(f)
            except:
                all_users = []
        
        # เพิ่มผู้ใช้ใหม่เข้าไป
        all_users.append(user_dict)
        
        # บันทึกกลับไป
        with open(all_users_file, 'w', encoding='utf-8') as f:
            json.dump(all_users, f, ensure_ascii=False, indent=2)
        
        logger.info(f"บันทึกข้อมูลผู้ใช้ {user_id} สำเร็จ")
        
        return {
            "success": True,
            "user_id": user_id,
            "message": "ลงทะเบียนสำเร็จ",
            "user_data": user_dict
        }
        
    except json.JSONDecodeError:
        logger.error("ไม่สามารถแปลงข้อมูลผู้ใช้เป็น JSON ได้")
        raise HTTPException(status_code=400, detail="ข้อมูลผู้ใช้ไม่ถูกต้อง")
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการลงทะเบียน: {str(e)}")
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการลงทะเบียน: {str(e)}")