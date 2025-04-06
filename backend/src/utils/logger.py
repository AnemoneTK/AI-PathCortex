import os
import logging
from pathlib import Path
from datetime import datetime
import sys

# สร้างโฟลเดอร์สำหรับบันทึก logs
LOGS_DIR = Path('logs')
LOGS_DIR.mkdir(parents=True, exist_ok=True)

def setup_logger(name: str, log_level: int = logging.INFO) -> logging.Logger:
    # สร้าง logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # ตรวจสอบว่า logger มี handlers อยู่แล้วหรือไม่ เพื่อป้องกันการซ้ำซ้อน
    if logger.handlers:
        return logger
    
    # สร้างชื่อไฟล์ log โดยใช้วันที่และชื่อโมดูล
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = LOGS_DIR / f"{today}_{name}.log"
    
    # สร้าง formatter สำหรับกำหนดรูปแบบข้อความ log
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # สร้าง handler สำหรับบันทึก log ลงไฟล์
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    
    # สร้าง handler สำหรับแสดง log บน console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # เพิ่ม handlers เข้าไปใน logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_logger(name: str, log_level: int = logging.INFO) -> logging.Logger:
    return setup_logger(name, log_level)

def set_debug_mode(debug: bool = True) -> None:
    level = logging.DEBUG if debug else logging.INFO
    
    # ตั้งค่า root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # ตั้งค่า handlers ทั้งหมดของ root logger
    for handler in root_logger.handlers:
        handler.setLevel(level)
        
    # บันทึกสถานะการเปิด/ปิด DEBUG mode
    status = "เปิดใช้งาน" if debug else "ปิดใช้งาน"
    root_logger.info(f"{status} DEBUG mode")