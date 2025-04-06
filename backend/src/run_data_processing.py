#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
สคริปต์รวมสำหรับประมวลผลข้อมูลอาชีพด้าน IT

สคริปต์นี้จะรวมขั้นตอนการประมวลผลข้อมูลทั้งหมด:
1. อ่านข้อมูลจากหลายแหล่ง
2. รวมข้อมูลและทำ normalize
3. สร้าง vectors สำหรับการค้นหา
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# เพิ่มโฟลเดอร์ปัจจุบันเข้าไปใน PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# นำเข้าโมดูลสำหรับการประมวลผลข้อมูล
from data_processing.data_processor import DataProcessor
from data_processing.vector_creator import VectorCreator
from utils.logger import get_logger

# ใช้ logger ที่ตั้งค่าแล้ว
logger = get_logger("run_data_processing")

def setup_directories():
    """สร้างโฟลเดอร์ที่จำเป็นสำหรับการประมวลผลข้อมูล"""
    directories = [
        "backend/logs",
        "backend/data/raw",
        "backend/data/raw/jobsdb",
        "backend/data/raw/other_sources",
        "backend/data/processed",
        "backend/data/vector_db",
        "backend/data/vector_db/job_knowledge"
    ]
    
    for dir_path in directories:
        os.makedirs(dir_path, exist_ok=True)
        logger.debug(f"สร้างโฟลเดอร์ {dir_path} (ถ้ายังไม่มี)")

def main():
    """ฟังก์ชันหลักสำหรับการประมวลผลข้อมูล"""
    # สร้างตัวแยกวิเคราะห์อาร์กิวเมนต์
    parser = argparse.ArgumentParser(description='เครื่องมือประมวลผลข้อมูลอาชีพด้าน IT')
    parser.add_argument('-r', '--raw-dir', type=str, default="backend/data/raw",
                        help='โฟลเดอร์ข้อมูลดิบ')
    parser.add_argument('-p', '--processed-dir', type=str, default="backend/data/processed",
                        help='โฟลเดอร์ข้อมูลที่ประมวลผลแล้ว')
    parser.add_argument('-v', '--vector-dir', type=str, default="backend/data/vector_db",
                        help='โฟลเดอร์สำหรับฐานข้อมูลเวกเตอร์')
    parser.add_argument('--skip-embeddings', action='store_true',
                        help='ข้ามขั้นตอนการสร้าง embeddings')
    parser.add_argument('--no-clear', action='store_true',
                        help='ไม่ต้องล้างโฟลเดอร์ output ก่อนการประมวลผล')
    parser.add_argument('--verbose', action='store_true',
                        help='แสดงรายละเอียดการทำงานโดยละเอียด')
    
    # แยกวิเคราะห์อาร์กิวเมนต์
    args = parser.parse_args()
    
    # ตั้งค่าระดับการบันทึกล็อก
    from utils.logger import set_debug_mode
    if args.verbose:
        set_debug_mode(True)
        logger.debug("เปิดใช้งานโหมด verbose")
    
    # สร้างโฟลเดอร์ที่จำเป็น
    setup_directories()
    
    # เริ่มการประมวลผลข้อมูล
    logger.info("=== เริ่มการประมวลผลข้อมูลอาชีพด้าน IT ===")
    
    # 1. ประมวลผลข้อมูลจากหลายแหล่ง
    processor = DataProcessor(args.raw_dir, args.processed_dir, clear_output=not args.no_clear)
    result = processor.process_all_data()
    
    logger.info(f"ประมวลผลและรวมข้อมูลอาชีพสำเร็จ {result['job_count']} อาชีพ")
    
    # 2. สร้าง vectors สำหรับการค้นหา (ถ้าไม่ข้ามขั้นตอนนี้)
    if not args.skip_embeddings:
        logger.info("กำลังสร้าง vectors สำหรับการค้นหา...")
        
        # ในตัวอย่างนี้เราไม่ได้กำหนดโมเดล embedding จึงใช้การจำลองข้อมูล
        vector_creator = VectorCreator(args.processed_dir, args.vector_dir, clear_vector_db=not args.no_clear)
        embedding_result = vector_creator.create_embeddings()
        
        if embedding_result["success"]:
            logger.info(f"สร้าง vectors สำเร็จ {embedding_result['vectors_count']} vectors")
        else:
            logger.error(f"เกิดข้อผิดพลาดในการสร้าง vectors: {embedding_result.get('error', 'ไม่ทราบสาเหตุ')}")
    else:
        logger.info("ข้ามขั้นตอนการสร้าง vectors")
    
    logger.info("=== สิ้นสุดการประมวลผลข้อมูลอาชีพด้าน IT ===")
    
    # แสดงสรุปผลการทำงาน
    print("\n=== สรุปผลการประมวลผลข้อมูล ===")
    print(f"จำนวนอาชีพที่ประมวลผล: {result['job_count']}")
    print(f"ไฟล์ข้อมูลที่รวมแล้ว: {os.path.join(args.processed_dir, 'merged_jobs.json')}")
    print(f"ไฟล์ข้อมูลสำหรับ embeddings: {os.path.join(args.processed_dir, 'embedding_data.json')}")
    
    if not args.skip_embeddings:
        print(f"ไฟล์ FAISS index: {os.path.join(args.vector_dir, 'job_knowledge', 'faiss_index.bin')}")
        print(f"ไฟล์ metadata: {os.path.join(args.vector_dir, 'job_knowledge', 'metadata.json')}")

if __name__ == "__main__":
    main()