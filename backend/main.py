#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main application entry point for the Career AI Advisor.

This module starts the FastAPI application.
"""

import os
import sys
sys.path.append('/opt/anaconda3/lib/python3.12/site-packages')
import uvicorn
import argparse
from pathlib import Path

# เพิ่มพาธของโปรเจค
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# นำเข้าการตั้งค่า
from src.utils.config import API_HOST, API_PORT, API_DEBUG

def main():
    """
    ฟังก์ชันหลักสำหรับเริ่มต้นแอปพลิเคชัน
    """
    # สร้าง ArgumentParser
    parser = argparse.ArgumentParser(description='Career AI Advisor API')
    parser.add_argument('--host', type=str, default=API_HOST, help='Host to listen on')
    parser.add_argument('--port', type=int, default=API_PORT, help='Port to listen on')
    parser.add_argument('--debug', action='store_true', default=API_DEBUG, help='Enable debug mode')
    
    # แยกวิเคราะห์อาร์กิวเมนต์
    args = parser.parse_args()
    
    # พิมพ์ข้อความต้อนรับ
    print("=" * 50)
    print("   Career AI Advisor API - เริ่มต้น   ")
    print("=" * 50)
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"Debug mode: {'เปิดใช้งาน' if args.debug else 'ปิดใช้งาน'}")
    print("=" * 50)
    
    # เริ่มต้น API
    uvicorn.run(
        "src.api.app:app",
        host=args.host,
        port=args.port,
        reload=args.debug
    )

if __name__ == "__main__":
    main()