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

# โหลดค่าจากไฟล์ .env (ค้นหาจากหลายตำแหน่ง)
# ลำดับการค้นหา: /app/.env (Docker), .env (โฟลเดอร์ปัจจุบัน), parent dirs
dotenv_paths = [
    "/app/.env",  # Docker container root path
    ".env",
    "../.env",
    "../../.env",
]

for dotenv_path in dotenv_paths:
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
        print(f"Loaded .env from {os.path.abspath(dotenv_path)}")
        break

# กำหนด BASE_DIR จาก environment variable (สำหรับ Docker) หรือคำนวณจาก path ปัจจุบัน
APP_PATH = os.environ.get("APP_PATH", None)

if APP_PATH:
    # Docker mode: ใช้ APP_PATH จาก environment variable
    BASE_DIR = APP_PATH
    print(f"Using BASE_DIR from APP_PATH: {BASE_DIR}")
else:
    # Local mode: คำนวณจาก path ของไฟล์ปัจจุบัน
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # "src/utils/config.py" -> "src/utils" -> "src" -> "backend"
    backend_dir = os.path.dirname(os.path.dirname(current_dir))
    
    # BASE_DIR = โฟลเดอร์ "AI-PathCortex"
    BASE_DIR = os.path.dirname(backend_dir)
    print(f"Calculated BASE_DIR: {BASE_DIR}")

# สร้างพาธที่จำเป็น
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGS_DIR = os.path.join(BACKEND_DIR, "logs")
UPLOADS_DIR = os.path.join(BACKEND_DIR, "uploads")

# โฟลเดอร์ข้อมูล
EMBEDDING_DIR = os.path.join(DATA_DIR, "embedding")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
VECTOR_DB_DIR = os.path.join(DATA_DIR, "vector_db")
FINE_TUNE_DIR = os.path.join(DATA_DIR, "fine_tune")

# โฟลเดอร์ย่อยของ PROCESSED_DATA_DIR
CLEANED_JOBS_DIR = os.path.join(PROCESSED_DATA_DIR, "cleaned_jobs")
NORMALIZED_JOBS_DIR = os.path.join(PROCESSED_DATA_DIR, "normalized_jobs")
CAREER_ADVICES_DIR = os.path.join(PROCESSED_DATA_DIR, "career_advices")

# โฟลเดอร์ย่อยของ VECTOR_DB_DIR
JOB_VECTOR_DIR = os.path.join(VECTOR_DB_DIR, "job_knowledge")
ADVICE_VECTOR_DIR = os.path.join(VECTOR_DB_DIR, "career_advice")

# โฟลเดอร์ผู้ใช้
USERS_DIR = os.path.join(DATA_DIR, "users")

JOB_VECTOR_DIR = os.path.join(VECTOR_DB_DIR, "job_knowledge")
ADVICE_VECTOR_DIR = os.path.join(VECTOR_DB_DIR, "career_advice")
COMBINED_VECTOR_DIR = os.path.join(VECTOR_DB_DIR, "combined_knowledge")

# สร้างโฟลเดอร์ที่จำเป็นทั้งหมด
dirs_to_create = [
    DATA_DIR, LOGS_DIR, UPLOADS_DIR, EMBEDDING_DIR, PROCESSED_DATA_DIR, 
    RAW_DATA_DIR, VECTOR_DB_DIR, FINE_TUNE_DIR, CLEANED_JOBS_DIR, 
    NORMALIZED_JOBS_DIR, CAREER_ADVICES_DIR, JOB_VECTOR_DIR, 
    ADVICE_VECTOR_DIR, COMBINED_VECTOR_DIR, USERS_DIR 
]

for dir_path in dirs_to_create:
    os.makedirs(dir_path, exist_ok=True)
    print(f"Ensured directory exists: {dir_path}")

# ตั้งค่า API
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_DEBUG = os.getenv("API_DEBUG", "False").lower() in ("true", "1", "t")
API_KEY = os.getenv("API_KEY", "")

# ตั้งค่า Embedding Model
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/e5-small-v2")

# ตั้งค่า LLM
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1:latest")
LLM_API_BASE = os.getenv("LLM_API_BASE", "http://host.docker.internal:11434")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")

# ตั้งค่า Fine-tuned Model
FINE_TUNED_MODEL = os.getenv("FINE_TUNED_MODEL", "llama3.1-8b-instruct-fine-tuned")
USE_FINE_TUNED = os.getenv("USE_FINE_TUNED", "False").lower() in ("true", "1", "t")

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
        "backend_dir": BACKEND_DIR,
        "data_dir": DATA_DIR,
        "embedding_dir": EMBEDDING_DIR,
        "processed_data_dir": PROCESSED_DATA_DIR,
        "raw_data_dir": RAW_DATA_DIR,
        "cleaned_jobs_dir": CLEANED_JOBS_DIR,
        "normalized_jobs_dir": NORMALIZED_JOBS_DIR,
        "career_advices_dir": CAREER_ADVICES_DIR,
        "vector_db_dir": VECTOR_DB_DIR,
        "job_vector_dir": JOB_VECTOR_DIR,
        "advice_vector_dir": ADVICE_VECTOR_DIR,
        "combined_vector_dir": COMBINED_VECTOR_DIR,
        "users_dir": USERS_DIR,
        "uploads_dir": UPLOADS_DIR,
        "logs_dir": LOGS_DIR,
        "fine_tune_dir": FINE_TUNE_DIR,
        "api_host": API_HOST,
        "api_port": API_PORT,
        "api_debug": API_DEBUG,
        "api_key": API_KEY,
        "embedding_model": EMBEDDING_MODEL,
        "llm_model": LLM_MODEL,
        "llm_api_base": LLM_API_BASE,
        "llm_api_key": LLM_API_KEY,
        "fine_tuned_model": FINE_TUNED_MODEL,
        "use_fine_tuned": USE_FINE_TUNED,
    }