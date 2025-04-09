#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration utilities for Career AI Advisor.

This module provides centralized configuration management for the application.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from enum import Enum

# โหลดค่าจากไฟล์ .env (ถ้ามี)
load_dotenv()

# Root directory of the project (3 levels up from this file)
current_dir = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))

# สร้างพาธที่จำเป็น
DATA_DIR = os.path.join(BASE_DIR, "data")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR,"backend", "processed")
CLEANED_JOBS_DIR = os.path.join(PROCESSED_DATA_DIR, "cleaned_jobs")
CAREER_ADVICES_DIR = os.path.join(PROCESSED_DATA_DIR, "career_advices")
VECTOR_DB_DIR = os.path.join(BASE_DIR,"backend","data", "vector_db")
JOB_VECTOR_DIR = os.path.join(VECTOR_DB_DIR, "job_knowledge")
ADVICE_VECTOR_DIR = os.path.join(VECTOR_DB_DIR, "career_advice")
USERS_DIR = os.path.join(DATA_DIR, "users")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# สร้างโฟลเดอร์ที่จำเป็น
for dir_path in [DATA_DIR, PROCESSED_DATA_DIR, CLEANED_JOBS_DIR, CAREER_ADVICES_DIR, 
                VECTOR_DB_DIR, JOB_VECTOR_DIR, ADVICE_VECTOR_DIR, USERS_DIR, 
                UPLOADS_DIR, LOGS_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# ตั้งค่า API
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_DEBUG = os.getenv("API_DEBUG", "False").lower() in ("true", "1", "t")
API_KEY = os.getenv("API_KEY", "")

# ตั้งค่า Embedding Model
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/e5-small-v2")
# EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-large")

# ตั้งค่า LLM
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1:latest")
LLM_API_BASE = os.getenv("LLM_API_BASE", "http://localhost:11434")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")

class PersonalityType(str, Enum):
    """ประเภทบุคลิกของ AI"""
    FORMAL = "formal"  # ทางการ
    FRIENDLY = "friendly"  # เพื่อน
    FUN = "fun"  # สนุก

class EducationStatus(str, Enum):
    """สถานะการศึกษา"""
    STUDENT = "student"  # นักศึกษา
    GRADUATE = "graduate"  # จบการศึกษา
    WORKING = "working"  # ทำงานแล้ว
    OTHER = "other"  # อื่นๆ

def get_settings() -> Dict[str, Any]:
    """
    รวบรวมการตั้งค่าทั้งหมดเป็น dictionary
    
    Returns:
        Dict[str, Any]: การตั้งค่าทั้งหมด
    """
    return {
        "base_dir": BASE_DIR,
        "data_dir": DATA_DIR,
        "processed_data_dir": PROCESSED_DATA_DIR,
        "cleaned_jobs_dir": CLEANED_JOBS_DIR,
        "career_advices_dir": CAREER_ADVICES_DIR,
        "vector_db_dir": VECTOR_DB_DIR,
        "job_vector_dir": JOB_VECTOR_DIR,
        "advice_vector_dir": ADVICE_VECTOR_DIR,
        "users_dir": USERS_DIR,
        "uploads_dir": UPLOADS_DIR,
        "logs_dir": LOGS_DIR,
        "api_host": API_HOST,
        "api_port": API_PORT,
        "api_debug": API_DEBUG,
        "api_key": API_KEY,
        "embedding_model": EMBEDDING_MODEL,
        "llm_model": LLM_MODEL,
        "llm_api_base": LLM_API_BASE,
        "llm_api_key": LLM_API_KEY,
    }