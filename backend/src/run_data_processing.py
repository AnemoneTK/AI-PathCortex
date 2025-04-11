#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
สคริปต์รวมสำหรับประมวลผลข้อมูลอาชีพด้าน IT

สคริปต์นี้จะรวมขั้นตอนการประมวลผลข้อมูลทั้งหมด:
1. เก็บข้อมูลจากแหล่งต่างๆ
2. อ่านข้อมูลจากแหล่งข้อมูล
3. รวมข้อมูลและทำ normalize
4. เตรียมข้อมูลสำหรับสร้าง embeddings
5. สร้าง vectors สำหรับการค้นหา
"""

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
import logging
import colorama
from colorama import Fore, Style

# เริ่มต้นใช้งาน colorama
colorama.init(autoreset=True)

# เพิ่มโฟลเดอร์ปัจจุบันเข้าไปใน PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

# นำเข้าโมดูลสำหรับการประมวลผลข้อมูล
try:
    from src.utils.logger import get_logger, set_debug_mode
    from src.data_processing.job_normalizer import JobDataNormalizer
    from src.data_processing.prepare_embedding_data import prepare_jobs_data, prepare_advices_data
    # โมดูลสำหรับสร้าง vector database
    from src.utils.vector_creator import VectorCreator
    # โมดูลสำหรับเก็บข้อมูล
    from src.data_collection.jobsdb_scraper import JobDataProcessor as JobsDBScraper
    from src.data_collection.jobsdb_advice_scraper import SimpleArticleScraper
    from src.data_collection.salary_scraper import ISMTechSalaryScraper
    from src.data_collection.resp_scraper import JobResponsibilityScraper
except ImportError as e:
    print(f"{Fore.RED}Error importing modules: {e}")
    print(f"{Fore.YELLOW}Make sure you're running this script from the project root directory")
    sys.exit(1)

# ใช้ logger ที่ตั้งค่าแล้ว
logger = get_logger("run_data_processing")

def setup_directories(base_dir):
    """สร้างโฟลเดอร์ที่จำเป็นสำหรับการประมวลผลข้อมูล"""
    directories = [
        os.path.join(base_dir, "logs"),
        os.path.join(base_dir, "data", "raw"),
        os.path.join(base_dir, "data", "raw", "jobsdb"),
        os.path.join(base_dir, "data", "raw", "other_sources"),
        os.path.join(base_dir, "data", "processed"),
        os.path.join(base_dir, "data", "processed", "normalized_jobs"),
        os.path.join(base_dir, "data", "processed", "cleaned_jobs"),
        os.path.join(base_dir, "data", "processed", "career_advices"),
        os.path.join(base_dir, "data", "embedding"),
        os.path.join(base_dir, "data", "vector_db"),
        os.path.join(base_dir, "data", "vector_db", "job_knowledge"),
        os.path.join(base_dir, "data", "vector_db", "career_advice"),
        os.path.join(base_dir, "data", "vector_db", "combined_knowledge"),
        os.path.join(base_dir, "data", "users"),
        os.path.join(base_dir, "uploads")
    ]
    
    for dir_path in directories:
        os.makedirs(dir_path, exist_ok=True)
        logger.debug(f"สร้างโฟลเดอร์ {dir_path} (ถ้ายังไม่มี)")
    
    print(f"{Fore.GREEN}✓ สร้างโฟลเดอร์ที่จำเป็นทั้งหมดเรียบร้อย")

def run_data_collection(args):
    """เก็บข้อมูลจากแหล่งต่างๆ"""
    print(f"\n{Fore.CYAN}{'='*20} เริ่มการเก็บข้อมูลจากแหล่งต่างๆ {'='*20}")
    
    if args.skip_collection:
        print(f"{Fore.YELLOW}⚠️ ข้ามขั้นตอนการเก็บข้อมูลตามที่ระบุในพารามิเตอร์")
        return
    
    try:
        # 1. เก็บข้อมูลจาก JobsDB
        print(f"\n{Fore.CYAN}[1/4] กำลังเก็บข้อมูลอาชีพจาก JobsDB...")
        jobsdb_scraper = JobsDBScraper()
        jobsdb_result = jobsdb_scraper.process()
        
        # 2. เก็บข้อมูลบทความแนะนำอาชีพ
        print(f"\n{Fore.CYAN}[2/4] กำลังเก็บข้อมูลบทความแนะนำอาชีพ...")
        output_dir = os.path.join(args.processed_dir, "career_advices")
        article_scraper = SimpleArticleScraper(output_dir)
        article_scraper.scrape_to_txt()
        
        # 3. เก็บข้อมูลเงินเดือน
        print(f"\n{Fore.CYAN}[3/4] กำลังเก็บข้อมูลเงินเดือน...")
        salary_scraper = ISMTechSalaryScraper(
            output_folder=os.path.join(args.raw_dir, "other_sources")
        )
        salary_result = salary_scraper.scrape()
        
        # 4. เก็บข้อมูลความรับผิดชอบของตำแหน่งงาน
        print(f"\n{Fore.CYAN}[4/4] กำลังเก็บข้อมูลความรับผิดชอบของตำแหน่งงาน...")
        resp_scraper = JobResponsibilityScraper(
            output_folder=os.path.join(args.raw_dir, "other_sources")
        )
        resp_result = resp_scraper.scrape()
        
        print(f"{Fore.GREEN}✓ เก็บข้อมูลจากแหล่งต่างๆ เรียบร้อยแล้ว")
        
    except Exception as e:
        print(f"{Fore.RED}❌ เกิดข้อผิดพลาดในการเก็บข้อมูล: {str(e)}")
        logger.error(f"เกิดข้อผิดพลาดในการเก็บข้อมูล: {str(e)}")
        # ไม่ต้อง exit เพื่อให้ทำงานขั้นตอนถัดไปได้

def normalize_job_data(args):
    """รวมข้อมูลและทำ normalize"""
    print(f"\n{Fore.CYAN}{'='*20} เริ่มการ Normalize ข้อมูลอาชีพ {'='*20}")
    
    try:
        normalizer = JobDataNormalizer(
            jobs_data_path=os.path.join(args.raw_dir, "other_sources", "jobs_data.json"),
            job_responsibilities_path=os.path.join(args.raw_dir, "other_sources", "job_responsibilities.json"),
            it_salary_data_path=os.path.join(args.raw_dir, "other_sources", "it_salary_data.json"),
            output_dir=os.path.join(args.processed_dir, "normalized_jobs")
        )
        
        normalizer.process()
        print(f"{Fore.GREEN}✓ Normalize ข้อมูลอาชีพเรียบร้อยแล้ว")
        
    except Exception as e:
        print(f"{Fore.RED}❌ เกิดข้อผิดพลาดในการ Normalize ข้อมูลอาชีพ: {str(e)}")
        logger.error(f"เกิดข้อผิดพลาดในการ Normalize ข้อมูลอาชีพ: {str(e)}")
        # ไม่ต้อง exit เพื่อให้ทำงานขั้นตอนถัดไปได้

def prepare_embedding_data(args):
    """เตรียมข้อมูลสำหรับสร้าง embeddings"""
    print(f"\n{Fore.CYAN}{'='*20} เริ่มการเตรียมข้อมูลสำหรับ Embeddings {'='*20}")
    
    try:
        # เตรียมข้อมูลอาชีพ
        normalized_jobs_dir = os.path.join(args.processed_dir, "normalized_jobs")
        embedding_data_file = os.path.join(args.base_dir, "data", "embedding", "embedding_data.json")
        
        print(f"{Fore.CYAN}[1/2] กำลังเตรียมข้อมูลอาชีพสำหรับสร้าง embeddings...")
        job_success = prepare_jobs_data(normalized_jobs_dir, embedding_data_file)
        
        # เตรียมข้อมูลคำแนะนำ
        advice_file = os.path.join(args.processed_dir, "career_advices", "career_advices.json")
        advices_output_file = os.path.join(args.base_dir, "data", "embedding", "career_advices_embeddings.json")
        
        print(f"{Fore.CYAN}[2/2] กำลังเตรียมข้อมูลคำแนะนำอาชีพสำหรับสร้าง embeddings...")
        advice_success = prepare_advices_data(advice_file, advices_output_file)
        
        if job_success and advice_success:
            print(f"{Fore.GREEN}✓ เตรียมข้อมูลสำหรับสร้าง embeddings เรียบร้อยแล้ว")
        else:
            print(f"{Fore.YELLOW}⚠️ การเตรียมข้อมูลสำหรับสร้าง embeddings เสร็จสิ้นแต่มีบางส่วนไม่สำเร็จ")
        
    except Exception as e:
        print(f"{Fore.RED}❌ เกิดข้อผิดพลาดในการเตรียมข้อมูลสำหรับ embeddings: {str(e)}")
        logger.error(f"เกิดข้อผิดพลาดในการเตรียมข้อมูลสำหรับ embeddings: {str(e)}")
        # ไม่ต้อง exit เพื่อให้ทำงานขั้นตอนถัดไปได้

def create_vector_database(args):
    """สร้าง vector database"""
    print(f"\n{Fore.CYAN}{'='*20} เริ่มการสร้าง Vector Database {'='*20}")
    
    if args.skip_embeddings:
        print(f"{Fore.YELLOW}⚠️ ข้ามขั้นตอนการสร้าง vector database ตามที่ระบุในพารามิเตอร์")
        return
    
    try:
        # โหลดโมเดล embedding (ถ้ามี)
        model = None
        try:
            from sentence_transformers import SentenceTransformer
            print(f"{Fore.CYAN}🔄 กำลังโหลดโมเดล SentenceTransformer...")
            model = SentenceTransformer(args.model_name)
            print(f"{Fore.GREEN}✅ โหลดโมเดลสำเร็จ")
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ ไม่สามารถโหลดโมเดลได้: {str(e)}")
            print(f"{Fore.YELLOW}⚠️ จะใช้การจำลอง embedding แทน")
        
        # สร้าง VectorCreator
        vector_creator = VectorCreator(
            processed_data_dir=args.processed_dir,
            vector_db_dir=args.vector_db_dir,
            embedding_model=model,
            clear_vector_db=not args.no_clear
        )
        
        # สร้าง embeddings ทั้งหมด
        results = vector_creator.create_all_embeddings()
        
        # ประเมินผลการสร้าง embeddings
        all_success = (
            results["job_embeddings"]["success"] and 
            results["advice_embeddings"]["success"] and 
            results["combined_embeddings"]["success"]
        )
        
        if all_success:
            print(f"{Fore.GREEN}✓ สร้าง Vector Database เรียบร้อยแล้ว")
            print(f"{Fore.GREEN}  - ข้อมูลอาชีพ: {results['job_embeddings']['vectors_count']} vectors")
            print(f"{Fore.GREEN}  - ข้อมูลคำแนะนำอาชีพ: {results['advice_embeddings']['vectors_count']} vectors")
            print(f"{Fore.GREEN}  - ข้อมูลรวม: {results['combined_embeddings']['vectors_count']} vectors")
        else:
            print(f"{Fore.YELLOW}⚠️ สร้าง Vector Database เสร็จสิ้นแต่มีบางส่วนไม่สำเร็จ")
            if not results["job_embeddings"]["success"]:
                print(f"{Fore.RED}  - ข้อมูลอาชีพ: ไม่สำเร็จ - {results['job_embeddings'].get('error', 'ไม่ทราบสาเหตุ')}")
            else:
                print(f"{Fore.GREEN}  - ข้อมูลอาชีพ: {results['job_embeddings']['vectors_count']} vectors")
                
            if not results["advice_embeddings"]["success"]:
                print(f"{Fore.RED}  - ข้อมูลคำแนะนำอาชีพ: ไม่สำเร็จ - {results['advice_embeddings'].get('error', 'ไม่ทราบสาเหตุ')}")
            else:
                print(f"{Fore.GREEN}  - ข้อมูลคำแนะนำอาชีพ: {results['advice_embeddings']['vectors_count']} vectors")
                
            if not results["combined_embeddings"]["success"]:
                print(f"{Fore.RED}  - ข้อมูลรวม: ไม่สำเร็จ - {results['combined_embeddings'].get('error', 'ไม่ทราบสาเหตุ')}")
            else:
                print(f"{Fore.GREEN}  - ข้อมูลรวม: {results['combined_embeddings']['vectors_count']} vectors")
        
    except Exception as e:
        print(f"{Fore.RED}❌ เกิดข้อผิดพลาดในการสร้าง Vector Database: {str(e)}")
        logger.error(f"เกิดข้อผิดพลาดในการสร้าง Vector Database: {str(e)}")

def print_summary(args, start_time):
    """แสดงสรุปผลการทำงาน"""
    end_time = datetime.now()
    duration = end_time - start_time
    
    print(f"\n{Fore.CYAN}{'='*20} สรุปผลการทำงาน {'='*20}")
    print(f"{Fore.CYAN}เวลาเริ่มต้น: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{Fore.CYAN}เวลาสิ้นสุด: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{Fore.CYAN}ใช้เวลาทั้งหมด: {duration}")
    
    # ตรวจสอบไฟล์ที่สร้างขึ้น
    embedding_data_file = os.path.join(args.base_dir, "data", "embedding", "embedding_data.json")
    advices_embedding_file = os.path.join(args.base_dir, "data", "embedding", "career_advices_embeddings.json")
    job_index_file = os.path.join(args.vector_db_dir, "job_knowledge", "faiss_index.bin")
    job_metadata_file = os.path.join(args.vector_db_dir, "job_knowledge", "metadata.json")
    advice_index_file = os.path.join(args.vector_db_dir, "career_advice", "faiss_index.bin")
    
    files_to_check = {
        "ข้อมูล embeddings อาชีพ": embedding_data_file,
        "ข้อมูล embeddings คำแนะนำ": advices_embedding_file,
        "FAISS index อาชีพ": job_index_file,
        "Metadata อาชีพ": job_metadata_file,
        "FAISS index คำแนะนำ": advice_index_file
    }
    
    print(f"\n{Fore.CYAN}สถานะไฟล์:")
    for desc, file_path in files_to_check.items():
        if os.path.exists(file_path):
            size_kb = os.path.getsize(file_path) / 1024
            size_str = f"{size_kb:.2f} KB" if size_kb < 1024 else f"{size_kb/1024:.2f} MB"
            print(f"{Fore.GREEN}✓ {desc}: {file_path} ({size_str})")
        else:
            print(f"{Fore.RED}✗ {desc}: ไม่พบไฟล์ {file_path}")
    
    print(f"\n{Fore.GREEN}การประมวลผลข้อมูลเสร็จสิ้น!")
    print(f"{Fore.CYAN}{'='*50}")

def main():
    """ฟังก์ชันหลักสำหรับการประมวลผลข้อมูล"""
    # สร้างตัวแยกวิเคราะห์อาร์กิวเมนต์
    parser = argparse.ArgumentParser(description='เครื่องมือประมวลผลข้อมูลอาชีพด้าน IT')
    parser.add_argument('-b', '--base-dir', type=str, default=project_root,
                        help='โฟลเดอร์หลักของโปรเจค')
    parser.add_argument('-r', '--raw-dir', type=str, default=None,
                        help='โฟลเดอร์ข้อมูลดิบ')
    parser.add_argument('-p', '--processed-dir', type=str, default=None,
                        help='โฟลเดอร์ข้อมูลที่ประมวลผลแล้ว')
    parser.add_argument('-v', '--vector-db-dir', type=str, default=None,
                        help='โฟลเดอร์สำหรับฐานข้อมูลเวกเตอร์')
    parser.add_argument('-m', '--model-name', type=str, default='intfloat/e5-small-v2',
                        help='ชื่อโมเดล SentenceTransformer ที่ต้องการใช้')
    parser.add_argument('--skip-collection', action='store_true',
                        help='ข้ามขั้นตอนการเก็บข้อมูล')
    parser.add_argument('--skip-embeddings', action='store_true',
                        help='ข้ามขั้นตอนการสร้าง embeddings')
    parser.add_argument('--no-clear', action='store_true',
                        help='ไม่ต้องล้างโฟลเดอร์ output ก่อนการประมวลผล')
    parser.add_argument('--verbose', action='store_true',
                        help='แสดงรายละเอียดการทำงานโดยละเอียด')
    
    # แยกวิเคราะห์อาร์กิวเมนต์
    args = parser.parse_args()
    
    # ตั้งค่าโฟลเดอร์หากไม่ได้ระบุ
    if args.raw_dir is None:
        args.raw_dir = os.path.join(args.base_dir, "data", "raw")
    if args.processed_dir is None:
        args.processed_dir = os.path.join(args.base_dir, "data", "processed")
    if args.vector_db_dir is None:
        args.vector_db_dir = os.path.join(args.base_dir, "data", "vector_db")
    
    # ตั้งค่าระดับการบันทึกล็อก
    if args.verbose:
        set_debug_mode(True)
        logger.debug("เปิดใช้งานโหมด verbose")
    
    # บันทึกเวลาเริ่มต้น
    start_time = datetime.now()
    
    # พิมพ์ข้อความต้อนรับ
    print(f"\n{Fore.CYAN}{'='*50}")
    print(f"{Fore.CYAN}= เริ่มต้นการประมวลผลข้อมูลอาชีพด้าน IT")
    print(f"{Fore.CYAN}= เวลาเริ่มต้น: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{Fore.CYAN}{'='*50}\n")
    
    print(f"{Fore.CYAN}📂 โฟลเดอร์หลัก: {args.base_dir}")
    print(f"{Fore.CYAN}📂 โฟลเดอร์ข้อมูลดิบ: {args.raw_dir}")
    print(f"{Fore.CYAN}📂 โฟลเดอร์ข้อมูลที่ประมวลผลแล้ว: {args.processed_dir}")
    print(f"{Fore.CYAN}📂 โฟลเดอร์สำหรับฐานข้อมูลเวกเตอร์: {args.vector_db_dir}")
    print(f"{Fore.CYAN}🤖 โมเดล Embedding: {args.model_name}")
    
    # 1. สร้างโฟลเดอร์ที่จำเป็น
    setup_directories(args.base_dir)
    
    # 2. เก็บข้อมูลจากแหล่งต่างๆ
    run_data_collection(args)
    
    # 3. รวมข้อมูลและทำ normalize
    normalize_job_data(args)
    
    # 4. เตรียมข้อมูลสำหรับสร้าง embeddings
    prepare_embedding_data(args)
    
    # 5. สร้าง vector database
    create_vector_database(args)
    
    # แสดงสรุปผลการทำงาน
    print_summary(args, start_time)

if __name__ == "__main__":
    main()