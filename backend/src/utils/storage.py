#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Storage utilities for Career AI Advisor.

This module provides functions for file storage and retrieval.
"""

import os
import json
import shutil
import uuid
from typing import Dict, List, Any, Optional, Union, BinaryIO
from datetime import datetime
from pathlib import Path

from src.utils.config import USERS_DIR, UPLOADS_DIR, EducationStatus
from src.utils.logger import get_logger
from src.api.models import User, UserCreate, UserUpdate, ChatHistory, ChatMessage

# ตั้งค่า logger
logger = get_logger("storage")

# ไฟล์สำหรับเก็บข้อมูลผู้ใช้คนเดียว
USER_FILE = os.path.join(USERS_DIR, "user.json")
# โฟลเดอร์สำหรับเก็บ Resume
RESUME_DIR = os.path.join(USERS_DIR, "resume")
# โฟลเดอร์สำหรับเก็บประวัติการสนทนา
CHATS_DIR = os.path.join(USERS_DIR, "chats")

# สร้างโฟลเดอร์ที่จำเป็น
os.makedirs(USERS_DIR, exist_ok=True)
os.makedirs(RESUME_DIR, exist_ok=True)
os.makedirs(CHATS_DIR, exist_ok=True)

def app_user_exists() -> bool:
    """
    ตรวจสอบว่ามีไฟล์ข้อมูลผู้ใช้หรือไม่
    
    Returns:
        bool: True ถ้ามีไฟล์ข้อมูลผู้ใช้, False ถ้าไม่มี
    """
    return os.path.exists(USER_FILE)

def get_app_user() -> Optional[User]:
    """
    ดึงข้อมูลผู้ใช้จากไฟล์ user.json
    
    Returns:
        Optional[User]: ข้อมูลผู้ใช้ หรือ None ถ้าไม่พบ
    """
    try:
        # ตรวจสอบว่าไฟล์มีอยู่หรือไม่
        if not os.path.exists(USER_FILE):
            logger.info("ไม่พบไฟล์ข้อมูลผู้ใช้")
            return None
        
        # อ่านข้อมูลจากไฟล์
        with open(USER_FILE, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
        
        # แปลงเป็น User object
        user = User.parse_obj(user_data)
        
        logger.info(f"ดึงข้อมูลผู้ใช้สำเร็จ: {user.name}")
        return user
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการดึงข้อมูลผู้ใช้: {str(e)}")
        return None

def save_app_user(user: User) -> bool:
    """
    บันทึกข้อมูลผู้ใช้ลงไฟล์ user.json
    
    Args:
        user: ข้อมูลผู้ใช้ที่ต้องการบันทึก
        
    Returns:
        bool: สถานะความสำเร็จ
    """
    try:
        # แปลงเป็น dict แล้วบันทึก
        user_dict = user.dict()
        with open(USER_FILE, 'w', encoding='utf-8') as f:
            json.dump(user_dict, f, ensure_ascii=False, indent=2)
        
        logger.info(f"บันทึกข้อมูลผู้ใช้ {user.name} สำเร็จ")
        return True
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการบันทึกข้อมูลผู้ใช้: {str(e)}")
        return False

def update_app_user(user_data: UserUpdate) -> Optional[User]:
    """
    อัปเดตข้อมูลผู้ใช้
    
    Args:
        user_data: ข้อมูลผู้ใช้ที่ต้องการอัปเดต
        
    Returns:
        Optional[User]: ข้อมูลผู้ใช้ที่อัปเดตแล้ว หรือ None ถ้าไม่สำเร็จ
    """
    try:
        # ดึงข้อมูลผู้ใช้เดิม
        user = get_app_user()
        if not user:
            # ถ้าไม่มีข้อมูลผู้ใช้เดิม ให้สร้างใหม่
            user = User(
                id="app_user",
                name="App User",
                institution="",
                education_status=EducationStatus.STUDENT,
                year=1,
                skills=[],
                programming_languages=[],
                tools=[],
                projects=[],
                work_experiences=[],
                resume_path=None,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
        
        # แปลงเป็น dict เพื่อการอัปเดต
        user_dict = user.dict()
        
        # อัปเดตข้อมูล
        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:  # อัปเดตเฉพาะฟิลด์ที่มีค่า
                user_dict[field] = value
        
        # อัปเดตเวลา
        user_dict["updated_at"] = datetime.now().isoformat()
        
        # สร้าง User object ใหม่
        updated_user = User.parse_obj(user_dict)
        
        # บันทึกข้อมูลผู้ใช้
        if not save_app_user(updated_user):
            logger.error(f"ไม่สามารถบันทึกข้อมูลผู้ใช้")
            return None
        
        logger.info(f"อัปเดตผู้ใช้สำเร็จ")
        return updated_user
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการอัปเดตผู้ใช้: {str(e)}")
        return None

def create_app_user(user_data: UserCreate) -> Optional[User]:
    """
    สร้างข้อมูลผู้ใช้ใหม่
    
    Args:
        user_data: ข้อมูลผู้ใช้
        
    Returns:
        Optional[User]: ข้อมูลผู้ใช้ที่สร้างแล้ว หรือ None ถ้าไม่สำเร็จ
    """
    try:
        # สร้างเวลาปัจจุบัน
        now = datetime.now().isoformat()
        
        # สร้าง User object
        user = User(
            id="app_user",  # ใช้ ID คงที่
            name=user_data.name,
            institution=user_data.institution,
            education_status=user_data.education_status,
            year=user_data.year,
            skills=user_data.skills,
            programming_languages=user_data.programming_languages,
            tools=user_data.tools,
            projects=user_data.projects,
            work_experiences=user_data.work_experiences,
            resume_path=None,
            created_at=now,
            updated_at=now
        )
        
        # บันทึกข้อมูลผู้ใช้
        if not save_app_user(user):
            logger.error(f"ไม่สามารถบันทึกข้อมูลผู้ใช้")
            return None
        
        logger.info(f"สร้างผู้ใช้สำเร็จ: {user.name}")
        return user
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการสร้างผู้ใช้: {str(e)}")
        return None

def save_app_resume(content, filename: str) -> Optional[str]:
    """
    บันทึกไฟล์ Resume สำหรับผู้ใช้แอพ
    
    Args:
        content: เนื้อหาของไฟล์ (bytes)
        filename: ชื่อไฟล์
        
    Returns:
        Optional[str]: พาธของไฟล์ Resume หรือ None ถ้าไม่สำเร็จ
    """
    try:
        # สร้างชื่อไฟล์
        _, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        new_filename = f"resume_{timestamp}{ext}"
        
        # สร้างพาธไฟล์
        file_path = os.path.join(RESUME_DIR, new_filename)
        
        # บันทึกไฟล์
        with open(file_path, 'wb') as f:
            # ตรวจสอบว่าข้อมูลเป็น bytes หรือ BinaryIO
            if hasattr(content, 'read'):
                # กรณีเป็น BinaryIO (file-like object)
                shutil.copyfileobj(content, f)
            else:
                # กรณีเป็น bytes
                f.write(content)
        
        # อัปเดตข้อมูลผู้ใช้
        user = get_app_user()
        if user:
            user_dict = user.dict()
            user_dict["resume_path"] = file_path
            user_dict["updated_at"] = datetime.now().isoformat()
            
            updated_user = User.parse_obj(user_dict)
            save_app_user(updated_user)
        
        logger.info(f"บันทึกไฟล์ Resume {file_path} สำเร็จ")
        return file_path
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการบันทึกไฟล์ Resume: {str(e)}")
        return None

def get_app_resume_path() -> Optional[str]:
    """
    ดึงพาธของไฟล์ Resume
    
    Returns:
        Optional[str]: พาธของไฟล์ Resume หรือ None ถ้าไม่พบ
    """
    try:
        # ดึงข้อมูลผู้ใช้
        user = get_app_user()
        if not user:
            logger.warning("ไม่พบข้อมูลผู้ใช้")
            return None
        
        # ตรวจสอบว่ามีไฟล์ Resume หรือไม่
        if not user.resume_path:
            logger.warning("ผู้ใช้ไม่มีไฟล์ Resume")
            return None
        
        # ตรวจสอบว่าไฟล์มีอยู่จริงหรือไม่
        if not os.path.exists(user.resume_path):
            logger.warning(f"ไม่พบไฟล์ Resume {user.resume_path}")
            return None
        
        logger.info(f"ดึงพาธของไฟล์ Resume {user.resume_path} สำเร็จ")
        return user.resume_path
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการดึงพาธของไฟล์ Resume: {str(e)}")
        return None

def save_chat_history(chat_history: ChatHistory) -> bool:
    """
    บันทึกประวัติการสนทนา
    
    Args:
        chat_history: ประวัติการสนทนา
        
    Returns:
        bool: สถานะความสำเร็จ
    """
    try:
        # กำหนดชื่อไฟล์
        chat_file = os.path.join(CHATS_DIR, f"{chat_history.id}.json")
        
        # แปลงเป็น dict แล้วบันทึก
        chat_dict = chat_history.dict()
        with open(chat_file, 'w', encoding='utf-8') as f:
            json.dump(chat_dict, f, ensure_ascii=False, indent=2)
        
        logger.info(f"บันทึกประวัติการสนทนา {chat_history.id} สำเร็จ")
        return True
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการบันทึกประวัติการสนทนา: {str(e)}")
        return False

def get_chat_history(limit: int = 10) -> List[ChatHistory]:
    """
    ดึงประวัติการสนทนา
    
    Args:
        limit: จำนวนประวัติการสนทนาที่ต้องการ
        
    Returns:
        List[ChatHistory]: ประวัติการสนทนา
    """
    try:
        chat_histories = []
        
        # ตรวจสอบว่ามีโฟลเดอร์ประวัติการสนทนาหรือไม่
        if not os.path.exists(CHATS_DIR):
            logger.warning("ไม่พบโฟลเดอร์ประวัติการสนทนา")
            return []
        
        # อ่านไฟล์ทั้งหมดในโฟลเดอร์
        for filename in os.listdir(CHATS_DIR):
            if filename.endswith('.json'):
                chat_file = os.path.join(CHATS_DIR, filename)
                with open(chat_file, 'r', encoding='utf-8') as f:
                    chat_data = json.load(f)
                    chat_history = ChatHistory.parse_obj(chat_data)
                    chat_histories.append(chat_history)
        
        # เรียงตามเวลา (ล่าสุดก่อน)
        chat_histories.sort(key=lambda x: x.timestamp, reverse=True)
        
        # จำกัดจำนวน
        chat_histories = chat_histories[:limit]
        
        logger.info(f"ดึงประวัติการสนทนา {len(chat_histories)} รายการ สำเร็จ")
        return chat_histories
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการดึงประวัติการสนทนา: {str(e)}")
        return []

def create_chat_message(query: str, response: str) -> ChatHistory:
    """
    สร้างประวัติการสนทนาใหม่
    
    Args:
        query: คำถาม
        response: คำตอบ
        
    Returns:
        ChatHistory: ประวัติการสนทนาที่สร้างแล้ว
    """
    chat_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    
    chat_history = ChatHistory(
        id=chat_id,
        user_id="app_user",  # ใช้ ID คงที่
        timestamp=timestamp,
        messages=[
            ChatMessage(role="user", content=query),
            ChatMessage(role="assistant", content=response)
        ]
    )
    
    return chat_history

# สำหรับ backward compatibility อาจจะยังคงฟังก์ชันเดิมไว้
def get_user(user_id: str) -> Optional[User]:
    """
    ดึงข้อมูลผู้ใช้
    
    Args:
        user_id: รหัสผู้ใช้
        
    Returns:
        Optional[User]: ข้อมูลผู้ใช้ หรือ None ถ้าไม่พบ
    """
    if user_id == "app_user":
        return get_app_user()
    return None