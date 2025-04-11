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
import time
from datetime import datetime
from pathlib import Path
import logging
import colorama
from colorama import Fore, Style, Back

# เริ่มต้นใช้งาน colorama
colorama.init(autoreset=True)

# เพิ่มโฟลเดอร์ปัจจุบันเข้าไปใน PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)
    
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

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

def display_progress_title(title, width=80):
    """แสดงหัวข้อขั้นตอนการทำงานแบบโดดเด่น"""
    print("\n")
    print(f"{Fore.CYAN}{Back.BLACK}{Style.BRIGHT}{' '*width}")
    padding = (width - len(title)) // 2
    print(f"{Fore.CYAN}{Back.BLACK}{Style.BRIGHT}{' '*padding}{title}{' '*(width - padding - len(title))}")
    print(f"{Fore.CYAN}{Back.BLACK}{Style.BRIGHT}{' '*width}")
    print()

def display_step_progress(step, message):
    """แสดงความคืบหน้าของขั้นตอนย่อย"""
    print(f"{Fore.GREEN}● {step}: {Fore.WHITE}{message}")

def display_substep_progress(message):
    """แสดงความคืบหน้าของขั้นตอนย่อยๆ"""
    print(f"{Fore.YELLOW}  └─ {message}")

def display_warning(message):
    """แสดงข้อความเตือน"""
    print(f"{Fore.YELLOW}⚠️  {message}")

def display_error(message):
    """แสดงข้อความผิดพลาด"""
    print(f"{Fore.RED}❌ {message}")

def display_success(message):
    """แสดงข้อความสำเร็จ"""
    print(f"{Fore.GREEN}✅ {message}")

def display_working(message):
    """แสดงข้อความกำลังทำงาน"""
    print(f"{Fore.CYAN}⏳ {message}")

def setup_directories(base_dir):
    """สร้างโฟลเดอร์ที่จำเป็นสำหรับการประมวลผลข้อมูล"""
    display_step_progress("Setup", "กำลังเตรียมโฟลเดอร์สำหรับเก็บข้อมูล")
    
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
        display_substep_progress(f"สร้างโฟลเดอร์ {dir_path}")
        logger.debug(f"สร้างโฟลเดอร์ {dir_path} (ถ้ายังไม่มี)")
        # เพิ่มการหน่วงเวลาเล็กน้อยเพื่อให้มองเห็นความคืบหน้า
        time.sleep(0.1)
    
    display_success("สร้างโฟลเดอร์ที่จำเป็นทั้งหมดเรียบร้อย")

def run_data_collection(args):
    """เก็บข้อมูลจากแหล่งต่างๆ"""
    display_progress_title("STEP 1: เก็บข้อมูลจากแหล่งต่างๆ")
    
    if args.skip_collection:
        display_warning("ข้ามขั้นตอนการเก็บข้อมูลตามที่ระบุในพารามิเตอร์")
        return
    
    try:
        # 1. เก็บข้อมูลจาก JobsDB
        display_step_progress("1.1", "กำลังเก็บข้อมูลอาชีพจาก JobsDB")
        display_working("เริ่มดึงข้อมูลจาก JobsDB...")
        jobsdb_scraper = JobsDBScraper()
        jobsdb_result = jobsdb_scraper.process()
        display_success("เก็บข้อมูลจาก JobsDB เสร็จสิ้น")
        
        # แสดงรายละเอียดผลลัพธ์
        if hasattr(jobsdb_result, 'get') and jobsdb_result.get('success', 0) > 0:
            display_substep_progress(f"ดึงข้อมูลสำเร็จ {jobsdb_result.get('success', 0)} รายการ")
        
        # 2. เก็บข้อมูลบทความแนะนำอาชีพ
        display_step_progress("1.2", "กำลังเก็บข้อมูลบทความแนะนำอาชีพ")
        display_working("เริ่มดึงข้อมูลบทความแนะนำอาชีพ...")
        output_dir = os.path.join(args.processed_dir, "career_advices")
        article_scraper = SimpleArticleScraper(output_dir)
        article_scraper.scrape()
        display_success("เก็บข้อมูลบทความแนะนำอาชีพเสร็จสิ้น")
        
        # 3. เก็บข้อมูลเงินเดือน
        display_step_progress("1.3", "กำลังเก็บข้อมูลเงินเดือน")
        display_working("เริ่มดึงข้อมูลเงินเดือนจาก ISM Technology...")
        salary_scraper = ISMTechSalaryScraper(
            output_folder=os.path.join(args.raw_dir, "other_sources")
        )
        salary_result = salary_scraper.scrape()
        if salary_result and salary_result.get("success", False):
            display_success(f"เก็บข้อมูลเงินเดือนสำเร็จ: {salary_result.get('jobs_count', 0)} ตำแหน่ง")
        else:
            display_warning("เก็บข้อมูลเงินเดือนสำเร็จบางส่วนหรือไม่สำเร็จ")
        
        # 4. เก็บข้อมูลความรับผิดชอบของตำแหน่งงาน
        display_step_progress("1.4", "กำลังเก็บข้อมูลความรับผิดชอบของตำแหน่งงาน")
        display_working("เริ่มดึงข้อมูลความรับผิดชอบของตำแหน่งงานจาก Talance...")
        resp_scraper = JobResponsibilityScraper(
            output_folder=os.path.join(args.raw_dir, "other_sources")
        )
        resp_result = resp_scraper.scrape()
        if resp_result and resp_result.get("success", False):
            display_success(f"เก็บข้อมูลความรับผิดชอบสำเร็จ: {resp_result.get('jobs_count', 0)} ตำแหน่ง")
        else:
            display_warning("เก็บข้อมูลความรับผิดชอบสำเร็จบางส่วนหรือไม่สำเร็จ")
        
        display_success("การเก็บข้อมูลจากแหล่งต่างๆ เสร็จสิ้นแล้ว")
        
    except Exception as e:
        display_error(f"เกิดข้อผิดพลาดในการเก็บข้อมูล: {str(e)}")
        logger.error(f"เกิดข้อผิดพลาดในการเก็บข้อมูล: {str(e)}")
        # ไม่ต้อง exit เพื่อให้ทำงานขั้นตอนถัดไปได้

def normalize_job_data(args):
    """รวมข้อมูลและทำ normalize"""
    display_progress_title("STEP 2: Normalize ข้อมูลอาชีพ")
    
    try:
        display_step_progress("2.1", "กำลังสร้างตัวปรับแต่งข้อมูล (Normalizer)")
        display_working("กำลังเตรียมการ normalize ข้อมูลอาชีพ...")
        
        # แสดงพาธของไฟล์ข้อมูลที่จะใช้
        jobs_data_path = os.path.join(args.raw_dir, "other_sources", "jobs_data.json")
        job_responsibilities_path = os.path.join(args.raw_dir, "other_sources", "job_responsibilities.json")
        it_salary_data_path = os.path.join(args.raw_dir, "other_sources", "it_salary_data.json")
        output_dir = os.path.join(args.processed_dir, "normalized_jobs")
        
        display_substep_progress(f"ไฟล์ข้อมูลอาชีพ: {jobs_data_path}")
        display_substep_progress(f"ไฟล์ข้อมูลความรับผิดชอบ: {job_responsibilities_path}")
        display_substep_progress(f"ไฟล์ข้อมูลเงินเดือน: {it_salary_data_path}")
        display_substep_progress(f"ไดเรกทอรีเอาต์พุต: {output_dir}")
        
        # ตรวจสอบว่าไฟล์มีอยู่จริงหรือไม่
        files_exist = all([
            os.path.exists(jobs_data_path),
            os.path.exists(job_responsibilities_path),
            os.path.exists(it_salary_data_path)
        ])
        
        if not files_exist:
            display_warning("บางไฟล์ข้อมูลไม่มีอยู่ การ normalize อาจไม่สมบูรณ์")
        
        normalizer = JobDataNormalizer(
            jobs_data_path=jobs_data_path,
            job_responsibilities_path=job_responsibilities_path,
            it_salary_data_path=it_salary_data_path,
            output_dir=output_dir
        )
        
        display_step_progress("2.2", "กำลังโหลดข้อมูลจากไฟล์")
        display_working("โหลดข้อมูลจากไฟล์ต่างๆ...")
        normalizer.load_data()
        
        display_step_progress("2.3", "กำลัง Normalize และบันทึกข้อมูล")
        display_working("กำลังประมวลผลและรวมข้อมูลจากแหล่งต่างๆ...")
        normalizer.normalize_and_save_jobs()
        
        # ตรวจสอบไฟล์ที่สร้างขึ้น
        if os.path.exists(output_dir):
            normalized_files = os.listdir(output_dir)
            display_success(f"Normalize ข้อมูลอาชีพเสร็จสิ้น: สร้างไฟล์ข้อมูล {len(normalized_files)} ไฟล์")
            
            # แสดงตัวอย่างไฟล์ที่สร้างขึ้น (สูงสุด 5 ไฟล์)
            sample_files = normalized_files[:5]
            for file in sample_files:
                display_substep_progress(f"ไฟล์: {file}")
            
            if len(normalized_files) > 5:
                display_substep_progress(f"และอีก {len(normalized_files) - 5} ไฟล์...")
        else:
            display_warning("ไม่พบไดเรกทอรีเอาต์พุต การ normalize อาจไม่สำเร็จ")
        
    except Exception as e:
        display_error(f"เกิดข้อผิดพลาดในการ Normalize ข้อมูลอาชีพ: {str(e)}")
        logger.error(f"เกิดข้อผิดพลาดในการ Normalize ข้อมูลอาชีพ: {str(e)}")
        # ไม่ต้อง exit เพื่อให้ทำงานขั้นตอนถัดไปได้

def prepare_embedding_data(args):
    """เตรียมข้อมูลสำหรับสร้าง embeddings"""
    display_progress_title("STEP 3: เตรียมข้อมูลสำหรับ Embeddings")
    
    try:
        # เตรียมข้อมูลอาชีพ
        normalized_jobs_dir = os.path.join(args.processed_dir, "normalized_jobs")
        embedding_data_file = os.path.join(args.base_dir, "data", "embedding", "embedding_data.json")
        
        display_step_progress("3.1", "กำลังเตรียมข้อมูลอาชีพสำหรับสร้าง embeddings")
        display_working(f"กำลังอ่านข้อมูลอาชีพจาก {normalized_jobs_dir}...")
        
        # ตรวจสอบไฟล์ข้อมูลอาชีพ
        if os.path.exists(normalized_jobs_dir):
            job_files = [f for f in os.listdir(normalized_jobs_dir) if f.endswith('.json')]
            display_substep_progress(f"พบไฟล์อาชีพทั้งหมด {len(job_files)} ไฟล์")
            
            # แสดงตัวอย่างไฟล์ที่พบ (สูงสุด 3 ไฟล์)
            if job_files:
                display_substep_progress("ตัวอย่างไฟล์:")
                for file in job_files[:3]:
                    display_substep_progress(f"- {file}")
                if len(job_files) > 3:
                    display_substep_progress(f"- และอีก {len(job_files) - 3} ไฟล์...")
        else:
            display_warning(f"ไม่พบไดเรกทอรี {normalized_jobs_dir}")
            display_substep_progress("ข้ามขั้นตอนการเตรียมข้อมูลอาชีพ")
            job_success = False
        
        # เริ่มการเตรียมข้อมูลอาชีพ
        display_working("กำลังแปลงข้อมูลอาชีพเป็นรูปแบบสำหรับ embedding...")
        job_success = prepare_jobs_data(normalized_jobs_dir, embedding_data_file)
        
        if job_success:
            display_success(f"เตรียมข้อมูลอาชีพสำเร็จ บันทึกไปที่ {embedding_data_file}")
            
            # แสดงรายละเอียดเพิ่มเติมของไฟล์ที่สร้าง
            if os.path.exists(embedding_data_file):
                file_size = os.path.getsize(embedding_data_file) / 1024  # KB
                if file_size > 1024:
                    file_size = file_size / 1024  # MB
                    display_substep_progress(f"ขนาดไฟล์: {file_size:.2f} MB")
                else:
                    display_substep_progress(f"ขนาดไฟล์: {file_size:.2f} KB")
                
                # ลองอ่านข้อมูลเพื่อตรวจสอบจำนวนรายการ
                try:
                    with open(embedding_data_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        display_substep_progress(f"จำนวนข้อมูลที่เตรียมไว้: {len(data)} รายการ")
                except Exception as e:
                    display_warning(f"ไม่สามารถอ่านข้อมูลจากไฟล์ได้: {str(e)}")
        else:
            display_error("การเตรียมข้อมูลอาชีพไม่สำเร็จ")
        
        # เตรียมข้อมูลคำแนะนำ
        advice_file = os.path.join(args.processed_dir, "career_advices", "career_advices.json")
        advices_output_file = os.path.join(args.base_dir, "data", "embedding", "career_advices_embeddings.json")
        
        display_step_progress("3.2", "กำลังเตรียมข้อมูลคำแนะนำอาชีพสำหรับสร้าง embeddings")
        display_working(f"กำลังอ่านข้อมูลคำแนะนำจาก {advice_file}...")
        
        # ตรวจสอบไฟล์ข้อมูลคำแนะนำ
        if os.path.exists(advice_file):
            display_substep_progress(f"พบไฟล์ข้อมูลคำแนะนำ: {advice_file}")
            
            # ลองอ่านข้อมูลเพื่อตรวจสอบจำนวนรายการ
            try:
                with open(advice_file, 'r', encoding='utf-8') as f:
                    advice_data = json.load(f)
                    if isinstance(advice_data, dict) and "career_advices" in advice_data:
                        display_substep_progress(f"จำนวนคำแนะนำ: {len(advice_data['career_advices'])} รายการ")
                    elif isinstance(advice_data, list):
                        display_substep_progress(f"จำนวนคำแนะนำ: {len(advice_data)} รายการ")
                    else:
                        display_warning("รูปแบบข้อมูลคำแนะนำไม่ถูกต้อง")
            except Exception as e:
                display_warning(f"ไม่สามารถอ่านข้อมูลจากไฟล์ได้: {str(e)}")
        else:
            display_warning(f"ไม่พบไฟล์ {advice_file}")
            display_substep_progress("ข้ามขั้นตอนการเตรียมข้อมูลคำแนะนำ")
            advice_success = False
        
        # เริ่มการเตรียมข้อมูลคำแนะนำ
        display_working("กำลังแปลงข้อมูลคำแนะนำเป็นรูปแบบสำหรับ embedding...")
        advice_success = prepare_advices_data(advice_file, advices_output_file)
        
        if advice_success:
            display_success(f"เตรียมข้อมูลคำแนะนำสำเร็จ บันทึกไปที่ {advices_output_file}")
            
            # แสดงรายละเอียดเพิ่มเติมของไฟล์ที่สร้าง
            if os.path.exists(advices_output_file):
                file_size = os.path.getsize(advices_output_file) / 1024  # KB
                if file_size > 1024:
                    file_size = file_size / 1024  # MB
                    display_substep_progress(f"ขนาดไฟล์: {file_size:.2f} MB")
                else:
                    display_substep_progress(f"ขนาดไฟล์: {file_size:.2f} KB")
                
                # ลองอ่านข้อมูลเพื่อตรวจสอบจำนวนรายการ
                try:
                    with open(advices_output_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        display_substep_progress(f"จำนวนข้อมูลที่เตรียมไว้: {len(data)} รายการ")
                except Exception as e:
                    display_warning(f"ไม่สามารถอ่านข้อมูลจากไฟล์ได้: {str(e)}")
        else:
            display_error("การเตรียมข้อมูลคำแนะนำไม่สำเร็จ")
        
        # สรุปผลการเตรียมข้อมูล
        if job_success and advice_success:
            display_success("เตรียมข้อมูลสำหรับสร้าง embeddings เสร็จสิ้นทั้งหมด")
        else:
            display_warning("การเตรียมข้อมูลสำหรับสร้าง embeddings เสร็จสิ้นแต่มีบางส่วนไม่สำเร็จ")
        
    except Exception as e:
        display_error(f"เกิดข้อผิดพลาดในการเตรียมข้อมูลสำหรับ embeddings: {str(e)}")
        logger.error(f"เกิดข้อผิดพลาดในการเตรียมข้อมูลสำหรับ embeddings: {str(e)}")
        # ไม่ต้อง exit เพื่อให้ทำงานขั้นตอนถัดไปได้

def create_vector_database(args):
    """สร้าง vector database"""
    display_progress_title("STEP 4: สร้าง Vector Database")
    
    if args.skip_embeddings:
        display_warning("ข้ามขั้นตอนการสร้าง vector database ตามที่ระบุในพารามิเตอร์")
        return
    
    try:
        # โหลดโมเดล embedding (ถ้ามี)
        display_step_progress("4.1", "กำลังโหลดโมเดล Embedding")
        model = None
        try:
            from sentence_transformers import SentenceTransformer
            display_working(f"กำลังโหลดโมเดล SentenceTransformer: {args.model_name}")
            model = SentenceTransformer(args.model_name)
            display_success(f"โหลดโมเดล {args.model_name} สำเร็จ")
        except Exception as e:
            display_warning(f"ไม่สามารถโหลดโมเดลได้: {str(e)}")
            display_substep_progress("จะใช้การจำลอง embedding แทน (ผลลัพธ์อาจไม่แม่นยำ)")
        
        # แสดงข้อมูลเกี่ยวกับการสร้าง Vector Database
        display_step_progress("4.2", "กำลังเตรียมสร้าง Vector Database")
        display_working("กำลังเตรียมการสร้าง Vector Database...")
        display_substep_progress(f"โฟลเดอร์ข้อมูลที่ประมวลผลแล้ว: {args.processed_dir}")
        display_substep_progress(f"โฟลเดอร์สำหรับเก็บฐานข้อมูล vector: {args.vector_db_dir}")
        if model:
            display_substep_progress(f"โมเดล Embedding: {args.model_name}")
        else:
            display_substep_progress("โมเดล Embedding: จำลอง vector (mock embedding)")
        
        if not args.no_clear:
            display_substep_progress("จะล้างฐานข้อมูล vector เดิมก่อนสร้างใหม่")
        else:
            display_substep_progress("จะไม่ล้างฐานข้อมูล vector เดิม (เพิ่มเติมข้อมูลเข้าไป)")
        
        # สร้าง VectorCreator
        display_step_progress("4.3", "กำลังสร้าง VectorCreator")
        vector_creator = VectorCreator(
            processed_data_dir=args.processed_dir,
            vector_db_dir=args.vector_db_dir,
            embedding_model=model,
            clear_vector_db=not args.no_clear
        )
        
        # สร้าง embeddings ทั้งหมด
        display_step_progress("4.4", "กำลังสร้าง Embeddings ทั้งหมด")
        display_working("กำลังสร้าง embeddings สำหรับข้อมูลอาชีพและคำแนะนำ...")
        results = vector_creator.create_all_embeddings()
        
        # วิเคราะห์ผลลัพธ์การสร้าง embeddings
        job_success = results["job_embeddings"]["success"]
        advice_success = results["advice_embeddings"]["success"]
        combined_success = results["combined_embeddings"]["success"] if "combined_embeddings" in results else False
        
        # แสดงผลการสร้าง embeddings สำหรับข้อมูลอาชีพ
        if job_success:
            display_success(f"สร้าง embeddings สำหรับข้อมูลอาชีพสำเร็จ: {results['job_embeddings']['vectors_count']} vectors")
        else:
            display_error(f"สร้าง embeddings สำหรับข้อมูลอาชีพไม่สำเร็จ: {results['job_embeddings'].get('error', 'ไม่ทราบสาเหตุ')}")
        
        # แสดงผลการสร้าง embeddings สำหรับข้อมูลคำแนะนำ
        if advice_success:
            display_success(f"สร้าง embeddings สำหรับข้อมูลคำแนะนำสำเร็จ: {results['advice_embeddings']['vectors_count']} vectors")
        else:
            display_error(f"สร้าง embeddings สำหรับข้อมูลคำแนะนำไม่สำเร็จ: {results['advice_embeddings'].get('error', 'ไม่ทราบสาเหตุ')}")
        
        # แสดงผลการสร้าง embeddings แบบรวม (ถ้ามี)
        if "combined_embeddings" in results:
            if combined_success:
                display_success(f"สร้าง embeddings แบบรวมสำเร็จ: {results['combined_embeddings']['vectors_count']} vectors")
            else:
                display_error(f"สร้าง embeddings แบบรวมไม่สำเร็จ: {results['combined_embeddings'].get('error', 'ไม่ทราบสาเหตุ')}")
        
        # ทดสอบการค้นหา
        if job_success:
            display_step_progress("4.5", "กำลังทดสอบการค้นหาอาชีพ")
            test_queries = [
                "นักพัฒนาซอฟต์แวร์", 
                "data scientist", 
                "fullstack developer", 
                "อาชีพเกี่ยวกับ AI"
            ]
            
            for query in test_queries:
                display_working(f"ทดสอบค้นหา: \"{query}\"")
                results = vector_creator.search_similar_jobs(query, k=2)
                
                # แสดงบรรทัดว่าง
                print("")
        
        if advice_success:
            display_step_progress("4.6", "กำลังทดสอบการค้นหาคำแนะนำอาชีพ")
            test_queries = [
                "วิธีการทำ resume ให้โดดเด่น", 
                "การเตรียมตัวสัมภาษณ์", 
                "เทคนิคการเขียน portfolio"
            ]
            
            for query in test_queries:
                display_working(f"ทดสอบค้นหา: \"{query}\"")
                results = vector_creator.search_relevant_advices(query, k=2)
                
                # แสดงบรรทัดว่าง
                print("")
        
        # สรุปผลการสร้าง Vector Database
        display_step_progress("4.7", "สรุปผลการสร้าง Vector Database")
        
        if job_success and advice_success:
            if combined_success:
                display_success("สร้าง Vector Database สำเร็จทั้งหมด (อาชีพ, คำแนะนำ และฐานข้อมูลรวม)")
            else:
                display_success("สร้าง Vector Database สำเร็จส่วนหลัก (อาชีพและคำแนะนำ) แต่ฐานข้อมูลรวมไม่สำเร็จ")
        elif job_success or advice_success:
            display_warning("สร้าง Vector Database สำเร็จบางส่วน")
        else:
            display_error("สร้าง Vector Database ไม่สำเร็จทั้งหมด")
            
        # ตรวจสอบไฟล์ที่สร้างขึ้น
        job_index_file = os.path.join(args.vector_db_dir, "job_knowledge", "faiss_index.bin")
        job_metadata_file = os.path.join(args.vector_db_dir, "job_knowledge", "metadata.json")
        advice_index_file = os.path.join(args.vector_db_dir, "career_advice", "faiss_index.bin")
        advice_metadata_file = os.path.join(args.vector_db_dir, "career_advice", "metadata.json")
        
        display_substep_progress("ไฟล์ที่สร้างขึ้น:")
        if os.path.exists(job_index_file):
            size_mb = os.path.getsize(job_index_file) / (1024 * 1024)
            display_substep_progress(f"- FAISS index อาชีพ: {job_index_file} ({size_mb:.2f} MB)")
        
        if os.path.exists(job_metadata_file):
            size_kb = os.path.getsize(job_metadata_file) / 1024
            display_substep_progress(f"- Metadata อาชีพ: {job_metadata_file} ({size_kb:.2f} KB)")
        
        if os.path.exists(advice_index_file):
            size_mb = os.path.getsize(advice_index_file) / (1024 * 1024)
            display_substep_progress(f"- FAISS index คำแนะนำ: {advice_index_file} ({size_mb:.2f} MB)")
        
        if os.path.exists(advice_metadata_file):
            size_kb = os.path.getsize(advice_metadata_file) / 1024
            display_substep_progress(f"- Metadata คำแนะนำ: {advice_metadata_file} ({size_kb:.2f} KB)")

    except Exception as e:
        display_error(f"เกิดข้อผิดพลาดในการสร้าง Vector Database: {str(e)}")
        logger.error(f"เกิดข้อผิดพลาดในการสร้าง Vector Database: {str(e)}")


def print_summary(args, start_time):
    """แสดงสรุปผลการทำงาน"""
    end_time = datetime.now()
    duration = end_time - start_time
    
    display_progress_title("STEP 5: สรุปผลการทำงาน")
    
    # แสดงข้อมูลเวลา
    display_step_progress("5.1", "ข้อมูลเวลาในการทำงาน")
    display_substep_progress(f"เวลาเริ่มต้น: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    display_substep_progress(f"เวลาสิ้นสุด: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # คำนวณเวลาที่ใช้ในรูปแบบที่อ่านง่าย
    hours, remainder = divmod(duration.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours > 0:
        time_str = f"{int(hours)} ชั่วโมง {int(minutes)} นาที {int(seconds)} วินาที"
    else:
        time_str = f"{int(minutes)} นาที {int(seconds)} วินาที"
    display_substep_progress(f"ใช้เวลาทั้งหมด: {time_str}")
    
    # ตรวจสอบไฟล์ที่สร้างขึ้น
    display_step_progress("5.2", "สถานะไฟล์ที่สร้างขึ้น")
    
    embedding_data_file = os.path.join(args.base_dir, "data", "embedding", "embedding_data.json")
    advices_embedding_file = os.path.join(args.base_dir, "data", "embedding", "career_advices_embeddings.json")
    job_index_file = os.path.join(args.vector_db_dir, "job_knowledge", "faiss_index.bin")
    job_metadata_file = os.path.join(args.vector_db_dir, "job_knowledge", "metadata.json")
    advice_index_file = os.path.join(args.vector_db_dir, "career_advice", "faiss_index.bin")
    advice_metadata_file = os.path.join(args.vector_db_dir, "career_advice", "metadata.json")
    combined_index_file = os.path.join(args.vector_db_dir, "combined_knowledge", "faiss_index.bin")
    
    files_to_check = {
        "ข้อมูล embeddings อาชีพ": embedding_data_file,
        "ข้อมูล embeddings คำแนะนำ": advices_embedding_file,
        "FAISS index อาชีพ": job_index_file,
        "Metadata อาชีพ": job_metadata_file,
        "FAISS index คำแนะนำ": advice_index_file,
        "Metadata คำแนะนำ": advice_metadata_file,
        "FAISS index รวม": combined_index_file
    }
    
    files_exist_count = 0
    for desc, file_path in files_to_check.items():
        if os.path.exists(file_path):
            size_kb = os.path.getsize(file_path) / 1024
            if size_kb > 1024:
                size_str = f"{size_kb/1024:.2f} MB"
            else:
                size_str = f"{size_kb:.2f} KB"
            display_success(f"{desc}: {os.path.basename(file_path)} ({size_str})")
            files_exist_count += 1
        else:
            display_warning(f"{desc}: ไม่พบไฟล์")
    
    # สรุปผล
    display_step_progress("5.3", "สรุปผลการดำเนินการ")
    if files_exist_count >= 4:
        display_success("การประมวลผลข้อมูลเสร็จสิ้น! ระบบพร้อมใช้งาน")
    else:
        display_warning("การประมวลผลข้อมูลเสร็จสิ้นบางส่วน ระบบอาจทำงานได้ไม่สมบูรณ์")
    
    print(f"\n{Fore.GREEN}{Style.BRIGHT}การประมวลผลข้อมูลเสร็จสิ้น!{Style.RESET_ALL}")
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
                        help='ไม่ต้องล้างฐานข้อมูล vector เดิมก่อนการประมวลผล')
    parser.add_argument('--verbose', action='store_true',
                        help='แสดงรายละเอียดการทำงานโดยละเอียด')
    parser.add_argument('--step', type=int, choices=[1, 2, 3, 4],
                        help='เริ่มทำงานจากขั้นตอนที่ระบุ (1: เก็บข้อมูล, 2: Normalize, 3: เตรียม embeddings, 4: สร้าง vector)')
    
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
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*80}")
    print(f"{Fore.CYAN}{Style.BRIGHT}{' '*20}ระบบประมวลผลข้อมูลอาชีพด้าน IT{' '*20}")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'='*80}\n")
    
    # แสดงข้อมูลการทำงาน
    print(f"{Fore.CYAN}{Style.BRIGHT}ข้อมูลการทำงาน:")
    print(f"{Fore.CYAN}📂 โฟลเดอร์หลัก: {args.base_dir}")
    print(f"{Fore.CYAN}📂 โฟลเดอร์ข้อมูลดิบ: {args.raw_dir}")
    print(f"{Fore.CYAN}📂 โฟลเดอร์ข้อมูลที่ประมวลผลแล้ว: {args.processed_dir}")
    print(f"{Fore.CYAN}📂 โฟลเดอร์สำหรับฐานข้อมูลเวกเตอร์: {args.vector_db_dir}")
    print(f"{Fore.CYAN}🤖 โมเดล Embedding: {args.model_name}")
    
    if args.skip_collection:
        print(f"{Fore.YELLOW}⚠️ ข้ามขั้นตอนการเก็บข้อมูล (--skip-collection)")
    
    if args.skip_embeddings:
        print(f"{Fore.YELLOW}⚠️ ข้ามขั้นตอนการสร้าง embeddings (--skip-embeddings)")
    
    if args.no_clear:
        print(f"{Fore.YELLOW}⚠️ ไม่ล้างฐานข้อมูล vector เดิม (--no-clear)")
    
    if args.step:
        print(f"{Fore.YELLOW}⚠️ เริ่มทำงานจากขั้นตอนที่ {args.step} (--step {args.step})")
    
    print("\n")
    
    # 1. สร้างโฟลเดอร์ที่จำเป็น
    setup_directories(args.base_dir)
    
    # กำหนดขั้นตอนเริ่มต้น
    start_step = args.step if args.step else 1
    
    # 2. เก็บข้อมูลจากแหล่งต่างๆ
    if start_step <= 1:
        run_data_collection(args)
    else:
        display_warning(f"ข้ามขั้นตอนที่ 1: เก็บข้อมูลจากแหล่งต่างๆ (เริ่มจากขั้นตอนที่ {start_step})")
    
    # 3. รวมข้อมูลและทำ normalize
    if start_step <= 2:
        normalize_job_data(args)
    else:
        display_warning(f"ข้ามขั้นตอนที่ 2: Normalize ข้อมูลอาชีพ (เริ่มจากขั้นตอนที่ {start_step})")
    
    # 4. เตรียมข้อมูลสำหรับสร้าง embeddings
    if start_step <= 3:
        prepare_embedding_data(args)
    else:
        display_warning(f"ข้ามขั้นตอนที่ 3: เตรียมข้อมูลสำหรับ Embeddings (เริ่มจากขั้นตอนที่ {start_step})")
    
    # 5. สร้าง vector database
    if start_step <= 4:
        create_vector_database(args)
    else:
        display_warning(f"ข้ามขั้นตอนที่ 4: สร้าง Vector Database (เริ่มจากขั้นตอนที่ {start_step})")
    
    # แสดงสรุปผลการทำงาน
    print_summary(args, start_time)

if __name__ == "__main__":
    """ฟังก์ชันหลักสำหรับการประมวลผลข้อมูล"""
    # เพิ่มส่วนนี้ก่อน parser
    app_dir = os.environ.get('APP_PATH', '/app')
    base_dir = os.path.join(app_dir,'app', 'data')
    raw_dir = os.path.join(base_dir, 'raw')
    processed_dir = os.path.join(base_dir, 'processed')
    vector_db_dir = os.path.join(base_dir, 'vector_db')
    embedding_dir = os.path.join(base_dir, 'embedding')

    # สร้างตัวแยกวิเคราะห์อาร์กิวเมนต์
    parser = argparse.ArgumentParser(description='เครื่องมือประมวลผลข้อมูลอาชีพด้าน IT')
    parser.add_argument('-b', '--base-dir', type=str, default=base_dir,
                        help='โฟลเดอร์หลักของโปรเจค')
    parser.add_argument('-r', '--raw-dir', type=str, default=raw_dir,
                        help='โฟลเดอร์ข้อมูลดิบ')
    parser.add_argument('-p', '--processed-dir', type=str, default=processed_dir,
                        help='โฟลเดอร์ข้อมูลที่ประมวลผลแล้ว')
    parser.add_argument('-v', '--vector-db-dir', type=str, default=vector_db_dir,
                        help='โฟลเดอร์สำหรับฐานข้อมูลเวกเตอร์')
    
    main()