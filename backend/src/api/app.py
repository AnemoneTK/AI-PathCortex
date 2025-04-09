#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main application for the Career AI Advisor API.

This module defines the FastAPI application and routes.
"""

import os
import sys
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi

# เพิ่มพาธของโปรเจค
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.append(project_root)

from src.utils.config import API_HOST, API_PORT, API_DEBUG
from src.utils.logger import get_logger
from src.api.dependencies import verify_api_key
from src.api.routes import base, user, jobs, chat

# ตั้งค่า logger
logger = get_logger("api.app")

# สร้าง FastAPI app
app = FastAPI(
    title="Career AI Advisor API",
    description="API สำหรับระบบให้คำปรึกษาด้านอาชีพด้วย AI",
    version="1.0.0",
    dependencies=[Depends(verify_api_key)],
)

# เพิ่ม CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # สำหรับการพัฒนา (ควรระบุ domain ที่แน่นอนในการใช้งานจริง)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# เพิ่ม routes
app.include_router(base.router)
app.include_router(user.router)
app.include_router(jobs.router)
app.include_router(chat.router)

# จัดการข้อผิดพลาด
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"เกิดข้อผิดพลาดที่ไม่ได้จัดการ: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"เกิดข้อผิดพลาดที่ไม่ได้จัดการ: {str(exc)}"}
    )

# กำหนด OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Career AI Advisor API",
        version="1.0.0",
        description="API สำหรับระบบให้คำปรึกษาด้านอาชีพด้วย AI",
        routes=app.routes,
    )
    
    # เพิ่ม API key security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "APIKeyHeader": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key"
        }
    }
    
    # เพิ่ม security requirement ให้กับทุก endpoint
    openapi_schema["security"] = [{"APIKeyHeader": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Event: เมื่อเริ่มต้น app
@app.on_event("startup")
async def startup_event():
    """ทำงานเมื่อเริ่มต้น API"""
    try:
        logger.info("กำลังเริ่มต้น Career AI Advisor API...")
        
        # ตรวจสอบโฟลเดอร์ที่จำเป็น
        from src.utils.config import DATA_DIR, VECTOR_DB_DIR, USERS_DIR, UPLOADS_DIR, LOGS_DIR
        for dir_path in [DATA_DIR, VECTOR_DB_DIR, USERS_DIR, UPLOADS_DIR, LOGS_DIR]:
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"ตรวจสอบโฟลเดอร์ {dir_path} เรียบร้อย")
        
        # ตรวจสอบ VectorSearch
        from src.utils.vector_search import VectorSearch
        vector_search = VectorSearch(VECTOR_DB_DIR)
        logger.info("ตรวจสอบ VectorSearch เรียบร้อย")
        
        logger.info("เริ่มต้น Career AI Advisor API สำเร็จ")
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการเริ่มต้น API: {str(e)}")

# Event: เมื่อปิด app
@app.on_event("shutdown")
async def shutdown_event():
    """ทำงานเมื่อปิด API"""
    logger.info("กำลังปิด Career AI Advisor API...")

# รัน API ถ้าเรียกใช้โดยตรง
if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"กำลังเริ่มต้น API ที่ {API_HOST}:{API_PORT}")
    uvicorn.run(
        "src.api.app:app",
        host=API_HOST,
        port=API_PORT,
        reload=API_DEBUG
    )