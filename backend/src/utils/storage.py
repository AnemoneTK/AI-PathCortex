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

from src.utils.config import USERS_DIR, UPLOADS_DIR
from src.utils.logger import get_logger
from src.api.models import User, UserCreate, UserUpdate, ChatHistory

# ตั้งค่า logger
logger = get_logger("storage")

def save_user(user: User) -> bool:
    """
    บันทึกข้อมูลผู้ใช้ลงไฟล์
    
    Args:
        user: ข้อมูลผู้ใช้ที่ต้องการบันทึก
        
    Returns:
        bool: สถานะความสำเร็จ
    """
    try:
        # สร้างพาธไฟล์
        user_file = os.path.join(USERS_DIR, f"{user.id}.json")
        
        # บันทึกข้อมูลลงไฟล์
        with open(user_file, 'w', encoding='utf-8') as f:
            f.write(user.json(ensure_ascii=False, indent=2))
        
        logger.info(f"บันทึกข้อมูลผู้ใช้ {user.id} สำเร็จ")
        return True
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการบันทึกข้อมูลผู้ใช้ {user.id}: {str(e)}")
        return False

def get_user(user_id: str) -> Optional[User]:
    """
    ดึงข้อมูลผู้ใช้จากไฟล์
    
    Args:
        user_id: รหัสผู้ใช้
        
    Returns:
        Optional[User]: ข้อมูลผู้ใช้ หรือ None ถ้าไม่พบ
    """
    try:
        # สร้างพาธไฟล์
        user_file = os.path.join(USERS_DIR, f"{user_id}.json")
        
        # ตรวจสอบว่าไฟล์มีอยู่หรือไม่
        if not os.path.exists(user_file):
            logger.warning(f"ไม่พบไฟล์ข้อมูลผู้ใช้ {user_id}")
            return None
        
        # อ่านข้อมูลจากไฟล์
        with open(user_file, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
        
        # แปลงเป็น User object
        user = User.parse_obj(user_data)
        
        logger.info(f"ดึงข้อมูลผู้ใช้ {user_id} สำเร็จ")
        return user
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการดึงข้อมูลผู้ใช้ {user_id}: {str(e)}")
        return None

def create_user(user_data: UserCreate) -> Optional[User]:
    """
    สร้างผู้ใช้ใหม่
    
    Args:
        user_data: ข้อมูลผู้ใช้
        
    Returns:
        Optional[User]: ข้อมูลผู้ใช้ที่สร้างแล้ว หรือ None ถ้าไม่สำเร็จ
    """
    try:
        # สร้างรหัสผู้ใช้
        user_id = str(uuid.uuid4())
        
        # สร้างเวลาปัจจุบัน
        now = datetime.now().isoformat()
        
        # สร้าง User object
        user = User(
            id=user_id,
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
        if not save_user(user):
            logger.error(f"ไม่สามารถบันทึกข้อมูลผู้ใช้ {user_id}")
            return None
        
        # สร้างโฟลเดอร์สำหรับเก็บไฟล์ของผู้ใช้
        user_upload_dir = os.path.join(UPLOADS_DIR, user_id)
        os.makedirs(user_upload_dir, exist_ok=True)
        
        logger.info(f"สร้างผู้ใช้ {user_id} สำเร็จ")
        return user
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการสร้างผู้ใช้: {str(e)}")
        return None

def update_user(user_id: str, user_data: UserUpdate) -> Optional[User]:
    """
    อัปเดตข้อมูลผู้ใช้
    
    Args:
        user_id: รหัสผู้ใช้
        user_data: ข้อมูลผู้ใช้ที่ต้องการอัปเดต
        
    Returns:
        Optional[User]: ข้อมูลผู้ใช้ที่อัปเดตแล้ว หรือ None ถ้าไม่สำเร็จ
    """
    try:
        # ดึงข้อมูลผู้ใช้เดิม
        user = get_user(user_id)
        if not user:
            logger.warning(f"ไม่พบผู้ใช้ {user_id}")
            return None
        
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
        if not save_user(updated_user):
            logger.error(f"ไม่สามารถบันทึกข้อมูลผู้ใช้ {user_id}")
            return None
        
        logger.info(f"อัปเดตผู้ใช้ {user_id} สำเร็จ")
        return updated_user
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการอัปเดตผู้ใช้ {user_id}: {str(e)}")
        return None

def delete_user(user_id: str) -> bool:
    """
    ลบผู้ใช้
    
    Args:
        user_id: รหัสผู้ใช้
        
    Returns:
        bool: สถานะความสำเร็จ
    """
    try:
        # ดึงข้อมูลผู้ใช้
        user = get_user(user_id)
        if not user:
            logger.warning(f"ไม่พบผู้ใช้ {user_id}")
            return False
        
        # ลบไฟล์ Resume (ถ้ามี)
        if user.resume_path and os.path.exists(user.resume_path):
            os.remove(user.resume_path)
            logger.info(f"ลบไฟล์ Resume ของผู้ใช้ {user_id} แล้ว")
        
        # ลบไฟล์ข้อมูลผู้ใช้
        user_file = os.path.join(USERS_DIR, f"{user_id}.json")
        if os.path.exists(user_file):
            os.remove(user_file)
            logger.info(f"ลบไฟล์ข้อมูลผู้ใช้ {user_id} แล้ว")
        else:
            logger.warning(f"ไม่พบไฟล์ข้อมูลผู้ใช้ {user_id}")
            return False
        
        # ลบโฟลเดอร์ของผู้ใช้
        user_upload_dir = os.path.join(UPLOADS_DIR, user_id)
        if os.path.exists(user_upload_dir):
            shutil.rmtree(user_upload_dir)
            logger.info(f"ลบโฟลเดอร์ของผู้ใช้ {user_id} แล้ว")
        
        logger.info(f"ลบผู้ใช้ {user_id} สำเร็จ")
        return True
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการลบผู้ใช้ {user_id}: {str(e)}")
        return False

def list_users() -> List[Dict[str, Any]]:
    """
    ดึงรายชื่อผู้ใช้ทั้งหมด
    
    Returns:
        List[Dict[str, Any]]: รายชื่อผู้ใช้
    """
    try:
        users = []
        
        # อ่านไฟล์ทั้งหมดในโฟลเดอร์ USERS_DIR
        for filename in os.listdir(USERS_DIR):
            if filename.endswith('.json'):
                user_id = filename[:-5]  # ตัด .json ออก
                user = get_user(user_id)
                if user:
                    users.append({
                        "id": user.id,
                        "name": user.name,
                        "institution": user.institution,
                        "education_status": user.education_status
                    })
        
        logger.info(f"ดึงรายชื่อผู้ใช้ทั้งหมด {len(users)} รายการ สำเร็จ")
        return users
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการดึงรายชื่อผู้ใช้: {str(e)}")
        return []

def save_resume(user_id: str, file_content, filename: str) -> Optional[str]:
    """
    บันทึกไฟล์ Resume
    
    Args:
        user_id: รหัสผู้ใช้
        file_content: เนื้อหาของไฟล์ (bytes)
        filename: ชื่อไฟล์
        
    Returns:
        Optional[str]: พาธของไฟล์ Resume หรือ None ถ้าไม่สำเร็จ
    """
    try:
        # ดึงข้อมูลผู้ใช้
        user = get_user(user_id)
        if not user:
            logger.warning(f"ไม่พบผู้ใช้ {user_id}")
            return None
        
        # สร้างชื่อไฟล์
        _, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        new_filename = f"resume_{timestamp}{ext}"
        
        # สร้างโฟลเดอร์ถ้ายังไม่มี
        user_upload_dir = os.path.join(UPLOADS_DIR, user_id)
        os.makedirs(user_upload_dir, exist_ok=True)
        
        # สร้างพาธไฟล์
        file_path = os.path.join(user_upload_dir, new_filename)
        
        # บันทึกไฟล์
        with open(file_path, 'wb') as f:
            # ตรวจสอบว่าข้อมูลเป็น bytes หรือ BinaryIO
            if hasattr(file_content, 'read'):
                # กรณีเป็น BinaryIO (file-like object)
                shutil.copyfileobj(file_content, f)
            else:
                # กรณีเป็น bytes
                f.write(file_content)
        
        # อัปเดตข้อมูลผู้ใช้
        user_dict = user.dict()
        user_dict["resume_path"] = file_path
        user_dict["updated_at"] = datetime.now().isoformat()
        
        # สร้าง User object ใหม่
        updated_user = User.parse_obj(user_dict)
        
        # บันทึกข้อมูลผู้ใช้
        if not save_user(updated_user):
            logger.error(f"ไม่สามารถบันทึกข้อมูลผู้ใช้ {user_id}")
            return None
        
        logger.info(f"บันทึกไฟล์ Resume {file_path} สำเร็จ")
        return file_path
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการบันทึกไฟล์ Resume: {str(e)}")
        return None
    
def get_resume_path(user_id: str) -> Optional[str]:
    """
    ดึงพาธของไฟล์ Resume
    
    Args:
        user_id: รหัสผู้ใช้
        
    Returns:
        Optional[str]: พาธของไฟล์ Resume หรือ None ถ้าไม่พบ
    """
    try:
        # ดึงข้อมูลผู้ใช้
        user = get_user(user_id)
        if not user:
            logger.warning(f"ไม่พบผู้ใช้ {user_id}")
            return None
        
        # ตรวจสอบว่ามีไฟล์ Resume หรือไม่
        if not user.resume_path:
            logger.warning(f"ผู้ใช้ {user_id} ไม่มีไฟล์ Resume")
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
        chat_file = None
        if chat_history.user_id:
            # ถ้ามี user_id ให้บันทึกในโฟลเดอร์ของผู้ใช้
            user_dir = os.path.join(UPLOADS_DIR, chat_history.user_id, "chats")
            os.makedirs(user_dir, exist_ok=True)
            chat_file = os.path.join(user_dir, f"{chat_history.id}.json")
        else:
            # ถ้าไม่มี user_id ให้บันทึกในโฟลเดอร์ chats
            chat_dir = os.path.join(UPLOADS_DIR, "chats")
            os.makedirs(chat_dir, exist_ok=True)
            chat_file = os.path.join(chat_dir, f"{chat_history.id}.json")
        
        # บันทึกข้อมูลลงไฟล์
        with open(chat_file, 'w', encoding='utf-8') as f:
            f.write(chat_history.json(ensure_ascii=False, indent=2))
        
        logger.info(f"บันทึกประวัติการสนทนา {chat_history.id} สำเร็จ")
        return True
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการบันทึกประวัติการสนทนา: {str(e)}")
        return False

def get_chat_history(user_id: Optional[str] = None, limit: int = 10) -> List[ChatHistory]:
    """
    ดึงประวัติการสนทนา
    
    Args:
        user_id: รหัสผู้ใช้ (ถ้ามี)
        limit: จำนวนประวัติการสนทนาที่ต้องการ
        
    Returns:
        List[ChatHistory]: ประวัติการสนทนา
    """
    try:
        chat_histories = []
        
        if user_id:
            # ถ้ามี user_id ให้ดึงประวัติการสนทนาของผู้ใช้
            chat_dir = os.path.join(UPLOADS_DIR, user_id, "chats")
            if not os.path.exists(chat_dir):
                logger.warning(f"ไม่พบโฟลเดอร์ประวัติการสนทนาของผู้ใช้ {user_id}")
                return []
            
            # อ่านไฟล์ทั้งหมดในโฟลเดอร์
            for filename in os.listdir(chat_dir):
                if filename.endswith('.json'):
                    chat_file = os.path.join(chat_dir, filename)
                    with open(chat_file, 'r', encoding='utf-8') as f:
                        chat_data = json.load(f)
                        chat_history = ChatHistory.parse_obj(chat_data)
                        chat_histories.append(chat_history)
        else:
            # ถ้าไม่มี user_id ให้ดึงประวัติการสนทนาทั้งหมด
            chat_dir = os.path.join(UPLOADS_DIR, "chats")
            if not os.path.exists(chat_dir):
                logger.warning("ไม่พบโฟลเดอร์ประวัติการสนทนา")
                return []
            
            # อ่านไฟล์ทั้งหมดในโฟลเดอร์
            for filename in os.listdir(chat_dir):
                if filename.endswith('.json'):
                    chat_file = os.path.join(chat_dir, filename)
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

# Testing
if __name__ == "__main__":
    from src.api.models import UserCreate, UserSkill, UserProject, UserWorkExperience
    from src.utils.config import EducationStatus
    
    # ทดสอบสร้างผู้ใช้
    user_data = UserCreate(
        name="John Doe",
        institution="มหาวิทยาลัยเกษตรศาสตร์",
        education_status=EducationStatus.STUDENT,
        year=3,
        skills=[
            UserSkill(name="Python", proficiency=4),
            UserSkill(name="JavaScript", proficiency=3),
        ],
        programming_languages=["Python", "JavaScript", "HTML", "CSS"],
        tools=["VS Code", "Git", "GitHub"],
        projects=[
            UserProject(
                name="Career AI Advisor",
                description="ระบบให้คำปรึกษาด้านอาชีพด้วย AI",
                technologies=["Python", "FastAPI", "React"],
                role="Backend Developer"
            ),
        ],
        work_experiences=[
            UserWorkExperience(
                title="Software Developer Intern",
                company="Example Co., Ltd.",
                start_date="2022-06",
                end_date="2022-08",
                description="พัฒนาเว็บแอปพลิเคชัน"
            ),
        ]
    )
    
    user = create_user(user_data)
    if user:
        print(f"สร้างผู้ใช้ {user.id} สำเร็จ")
        
        # ทดสอบอัปเดตผู้ใช้
        user_update = UserUpdate(
            name="John Smith",
            programming_languages=["Python", "JavaScript", "TypeScript", "HTML", "CSS"],
        )
        updated_user = update_user(user.id, user_update)
        if updated_user:
            print(f"อัปเดตผู้ใช้ {updated_user.id} สำเร็จ")
            print(f"ชื่อใหม่: {updated_user.name}")
            print(f"ภาษาโปรแกรม: {updated_user.programming_languages}")
        
        # ทดสอบลบผู้ใช้
        if delete_user(user.id):
            print(f"ลบผู้ใช้ {user.id} สำเร็จ")
    else:
        print("สร้างผู้ใช้ไม่สำเร็จ")


def get_all_users() -> List[Dict[str, Any]]:
    """
    ดึงข้อมูลผู้ใช้ทั้งหมดจากไฟล์ users.json
    
    Returns:
        List[Dict[str, Any]]: รายการข้อมูลผู้ใช้ทั้งหมด
    """
    users_file = os.path.join(USERS_DIR, "users.json")
    
    # ตรวจสอบว่าไฟล์มีอยู่หรือไม่
    if not os.path.exists(users_file):
        # สร้างไฟล์เปล่า
        with open(users_file, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        logger.info(f"สร้างไฟล์ข้อมูลผู้ใช้ใหม่: {users_file}")
        return []
    
    try:
        # อ่านข้อมูลจากไฟล์
        with open(users_file, 'r', encoding='utf-8') as f:
            users_data = json.load(f)
        
        logger.info(f"โหลดข้อมูลผู้ใช้สำเร็จ: {len(users_data)} รายการ")
        return users_data
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการโหลดข้อมูลผู้ใช้: {str(e)}")
        return []

def save_all_users(users_data: List[Dict[str, Any]]) -> bool:
    """
    บันทึกข้อมูลผู้ใช้ทั้งหมดลงไฟล์ users.json
    
    Args:
        users_data: รายการข้อมูลผู้ใช้ทั้งหมด
        
    Returns:
        bool: สถานะความสำเร็จ
    """
    users_file = os.path.join(USERS_DIR, "users.json")
    
    try:
        # บันทึกข้อมูลลงไฟล์
        with open(users_file, 'w', encoding='utf-8') as f:
            json.dump(users_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"บันทึกข้อมูลผู้ใช้สำเร็จ: {len(users_data)} รายการ")
        return True
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการบันทึกข้อมูลผู้ใช้: {str(e)}")
        return False

def update_user_to_combined_file(user: User) -> bool:
    """
    อัปเดตข้อมูลผู้ใช้ในไฟล์ข้อมูลรวม
    
    Args:
        user: ข้อมูลผู้ใช้ที่ต้องการอัปเดต
        
    Returns:
        bool: สถานะความสำเร็จ
    """
    try:
        # โหลดข้อมูลผู้ใช้ทั้งหมด
        users_data = get_all_users()
        
        # ตรวจสอบว่ามีผู้ใช้อยู่แล้วหรือไม่
        user_dict = user.dict()
        user_id = user_dict.get("id")
        
        existing_index = None
        for i, existing_user in enumerate(users_data):
            if existing_user.get("id") == user_id:
                existing_index = i
                break
        
        # อัปเดตหรือเพิ่มข้อมูลผู้ใช้
        if existing_index is not None:
            users_data[existing_index] = user_dict
            logger.info(f"อัปเดตข้อมูลผู้ใช้ {user_id} ในไฟล์รวม")
        else:
            users_data.append(user_dict)
            logger.info(f"เพิ่มข้อมูลผู้ใช้ {user_id} ในไฟล์รวม")
        
        # บันทึกข้อมูลผู้ใช้ทั้งหมด
        if save_all_users(users_data):
            # อัปเดต vector database หลังจากบันทึกข้อมูลผู้ใช้
            # ตรวจสอบว่า VectorCreator พร้อมใช้งานหรือไม่
            try:
                from src.utils.vector_creator import VectorCreator
                from src.utils.config import PROCESSED_DATA_DIR, VECTOR_DB_DIR
                
                # สร้าง VectorCreator
                creator = VectorCreator(
                    processed_data_dir=PROCESSED_DATA_DIR,
                    vector_db_dir=VECTOR_DB_DIR,
                    clear_vector_db=False  # ไม่ล้างฐานข้อมูลเดิม
                )
                
                # สร้าง embeddings แบบรวมข้อมูล
                result = creator.create_combined_embeddings()
                
                if result["success"]:
                    logger.info(f"อัปเดต vector database สำเร็จ: {result['vectors_count']} vectors")
                else:
                    logger.warning(f"อัปเดต vector database ไม่สำเร็จ: {result.get('error', 'ไม่ทราบสาเหตุ')}")
            except Exception as e:
                logger.error(f"เกิดข้อผิดพลาดในการอัปเดต vector database: {str(e)}")
            
            return True
        
        return False
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการอัปเดตข้อมูลผู้ใช้ในไฟล์รวม: {str(e)}")
        return False

def remove_user_from_combined_file(user_id: str) -> bool:
    """
    ลบข้อมูลผู้ใช้จากไฟล์ข้อมูลรวม
    
    Args:
        user_id: รหัสผู้ใช้ที่ต้องการลบ
        
    Returns:
        bool: สถานะความสำเร็จ
    """
    try:
        # โหลดข้อมูลผู้ใช้ทั้งหมด
        users_data = get_all_users()
        
        # หาและลบผู้ใช้
        original_length = len(users_data)
        users_data = [user for user in users_data if user.get("id") != user_id]
        
        if len(users_data) < original_length:
            # บันทึกข้อมูลผู้ใช้ทั้งหมด
            if save_all_users(users_data):
                logger.info(f"ลบข้อมูลผู้ใช้ {user_id} จากไฟล์รวมสำเร็จ")
                
                # อัปเดต vector database หลังจากลบข้อมูลผู้ใช้
                try:
                    from src.utils.vector_creator import VectorCreator
                    from src.utils.config import PROCESSED_DATA_DIR, VECTOR_DB_DIR
                    
                    # สร้าง VectorCreator
                    creator = VectorCreator(
                        processed_data_dir=PROCESSED_DATA_DIR,
                        vector_db_dir=VECTOR_DB_DIR,
                        clear_vector_db=False  # ไม่ล้างฐานข้อมูลเดิม
                    )
                    
                    # สร้าง embeddings แบบรวมข้อมูล
                    result = creator.create_combined_embeddings()
                    
                    if result["success"]:
                        logger.info(f"อัปเดต vector database สำเร็จ: {result['vectors_count']} vectors")
                    else:
                        logger.warning(f"อัปเดต vector database ไม่สำเร็จ: {result.get('error', 'ไม่ทราบสาเหตุ')}")
                except Exception as e:
                    logger.error(f"เกิดข้อผิดพลาดในการอัปเดต vector database: {str(e)}")
                
                return True
            else:
                logger.error(f"ไม่สามารถบันทึกข้อมูลผู้ใช้หลังจากลบ {user_id}")
                return False
        else:
            logger.warning(f"ไม่พบข้อมูลผู้ใช้ {user_id} ในไฟล์รวม")
            return False
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการลบข้อมูลผู้ใช้จากไฟล์รวม: {str(e)}")
        return False