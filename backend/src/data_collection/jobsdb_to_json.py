#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
โปรแกรมแปลงข้อมูลข้อความเป็น JSON สำหรับข้อมูลอาชีพ (แก้ไขข้อมูลซ้ำซ้อน)

โปรแกรมนี้จะแปลงไฟล์ข้อความที่ดึงมาจาก JobsDB เป็นไฟล์ JSON ที่มีโครงสร้างเหมาะสม
สำหรับนำไปใช้ในระบบให้คำปรึกษาอาชีพ โดยแก้ไขปัญหาข้อมูลซ้ำซ้อนระหว่าง responsibilities และ career_path
"""
# backend/src/data_collection/jobsdb_to_json.py

import os
import sys
import json
import re
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from tqdm import tqdm
import colorama

# เริ่มต้นใช้งาน colorama
colorama.init()

# สีสำหรับการแสดงผลในเทอร์มินัล
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# สร้างโฟลเดอร์สำหรับเก็บล็อก
log_dir = Path("src/logs")
log_dir.mkdir(parents=True, exist_ok=True)

# ตั้งค่าการบันทึกล็อก
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "text_to_json_converter.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("text_to_json_converter")

class TextToJsonConverterFixed:
    """
    คลาสสำหรับแปลงข้อมูลข้อความเป็น JSON ที่แก้ไขปัญหาข้อมูลซ้ำซ้อน
    """
    def __init__(self, input_folder: str = "data/raw/jobsdb", 
                 output_folder: str = "data/json", 
                 output_filename: str = "jobs_data.json"):
        """
        เริ่มต้นการทำงานของ converter
        
        Args:
            input_folder: โฟลเดอร์ที่เก็บไฟล์ข้อความ
            output_folder: โฟลเดอร์สำหรับบันทึกไฟล์ JSON
            output_filename: ชื่อไฟล์ JSON ที่จะบันทึก
        """
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.output_filename = output_filename
        self.output_path = os.path.join(output_folder, output_filename)
        
        # สร้างโฟลเดอร์ output ถ้ายังไม่มี
        Path(self.output_folder).mkdir(parents=True, exist_ok=True)
        
        # ข้อมูลที่แปลงแล้ว
        self.job_data = {}
        
        # รายการข้อความที่ไม่ใช่ความรับผิดชอบหรือเส้นทางอาชีพ
        self.non_responsibility_patterns = [
            r"^การเป็น.*เป็นอย่างไร",
            r"^วิธีการเป็น",
            r"^งาน.*ล่าสุด",
            r"^ทักษะและประสบการณ์ที่ดีที่สุดสำหรับ",
            r"^\d+\.",
            r"^เรียน",
            r"^สมัครงาน",
            r"^ระหว่างทำงาน",
            r"^เส้นทางสายอาชีพ"
        ]
        
        # รูปแบบของหัวข้อที่จะค้นหาในข้อความ
        self.section_patterns = {
            "description": [
                r"^Description:(.+?)(?=\n\nResponsibilities:|\n\nRequired Skills:|\n\nEducation:|\n\nCareer Path:|\Z)",
                r"^คำอธิบาย:(.+?)(?=\n\nความรับผิดชอบ:|\n\nทักษะที่ต้องการ:|\n\nการศึกษา:|\n\nเส้นทางอาชีพ:|\Z)",
                r"การเป็น(.+?)(?=\n\n[•\-]|\Z)"
            ],
            "responsibilities": [
                r"^Responsibilities:(.+?)(?=\n\nRequired Skills:|\n\nEducation:|\n\nCareer Path:|\Z)",
                r"^ความรับผิดชอบ:(.+?)(?=\n\nทักษะที่ต้องการ:|\n\nการศึกษา:|\n\nเส้นทางอาชีพ:|\Z)"
            ],
            "education": [
                r"^Education:(.+?)(?=\n\nCareer Path:|\Z)",
                r"^การศึกษา:(.+?)(?=\n\nเส้นทางอาชีพ:|\Z)",
                r"จบการศึกษา(.+?)(?=\n\n|.เรียนเพิ่มเติม|\Z)"
            ],
            "career_path": [
                r"^Career Path:(.+?)(?=\Z)",
                r"^เส้นทางอาชีพ:(.+?)(?=\Z)",
                r"เส้นทางสายอาชีพ(.+?)(?=\Z)"
            ]
        }
    
    def backup_existing_file(self) -> None:
        """สำรองไฟล์ที่มีอยู่แล้วก่อนเขียนทับ"""
        if os.path.exists(self.output_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{os.path.splitext(self.output_path)[0]}_{timestamp}.json"
            
            try:
                import shutil
                shutil.copy2(self.output_path, backup_file)
                logger.info(f"สำรองไฟล์เดิมไว้ที่: {backup_file}")
                print(f"{Colors.CYAN}📋 สำรองไฟล์เดิมไว้ที่: {backup_file}{Colors.ENDC}")
            except Exception as e:
                logger.error(f"ไม่สามารถสำรองไฟล์เดิมได้: {str(e)}")
                print(f"{Colors.FAIL}❌ ไม่สามารถสำรองไฟล์เดิมได้: {str(e)}{Colors.ENDC}")
    
    def clean_text(self, text: str) -> str:
        """
        ทำความสะอาดข้อความ
        
        Args:
            text: ข้อความที่ต้องการทำความสะอาด
            
        Returns:
            ข้อความที่ทำความสะอาดแล้ว
        """
        # ลบช่องว่างที่ไม่จำเป็น
        text = text.strip()
        
        # ลบเลขที่ขึ้นต้น
        text = re.sub(r"^\d+\.?\s*", "", text)
        
        # ลบจุดนำหน้า
        text = re.sub(r"^[•\-]\s*", "", text)
        
        # แทนที่การขึ้นบรรทัดซ้ำด้วยการขึ้นบรรทัดเดียว
        text = re.sub(r"\n+", "\n", text)
        
        # แก้ไขข้อความ "การเป็นa..." เป็น "การเป็น..."
        text = re.sub(r"การเป็นa\s+", "การเป็น", text)
        
        return text.strip()
    
    def is_responsibility_item(self, text: str) -> bool:
        """
        ตรวจสอบว่าข้อความเป็นความรับผิดชอบหรือไม่
        
        Args:
            text: ข้อความที่ต้องการตรวจสอบ
            
        Returns:
            True ถ้าเป็นความรับผิดชอบ, False ถ้าไม่ใช่
        """
        # ตรวจสอบว่าไม่ตรงกับรูปแบบที่ไม่ใช่ความรับผิดชอบ
        for pattern in self.non_responsibility_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return False
        
        # ตรวจสอบว่ามีคำที่เกี่ยวกับความรับผิดชอบหรือไม่
        responsibility_keywords = [
            "ออกแบบ", "พัฒนา", "สร้าง", "ดูแล", "ปรับปรุง", "ตรวจสอบ", "วางแผน", 
            "ทำงาน", "ประสานงาน", "ทดสอบ", "ติดตั้ง", "รับฟัง", "บริหาร", "แก้ไข",
            "วิเคราะห์", "ร่าง", "จัดการ", "เขียน", "กำหนด", "รายงาน", "นำเสนอ"
        ]
        
        for keyword in responsibility_keywords:
            if keyword in text.lower():
                return True
        
        return False
    
    def is_career_path_item(self, text: str) -> bool:
        """
        ตรวจสอบว่าข้อความเป็นเส้นทางอาชีพหรือไม่
        
        Args:
            text: ข้อความที่ต้องการตรวจสอบ
            
        Returns:
            True ถ้าเป็นเส้นทางอาชีพ, False ถ้าไม่ใช่
        """
        # ตรวจสอบว่าตรงกับรูปแบบเส้นทางอาชีพ
        career_path_patterns = [
            r"^\d+\.",
            r"^เรียน",
            r"^สมัครงาน",
            r"^ระหว่างทำงาน",
            r"^เส้นทางสาย",
            r"^จบการศึกษา"
        ]
        
        for pattern in career_path_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def extract_section(self, content: str, patterns: List[str]) -> str:
        """
        สกัดส่วนข้อมูลจากข้อความตามรูปแบบที่กำหนด
        
        Args:
            content: ข้อความที่ต้องการสกัด
            patterns: รายการรูปแบบที่ใช้ในการสกัด
            
        Returns:
            ข้อความที่สกัดได้
        """
        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                return self.clean_text(match.group(1))
        
        return ""
    
    def extract_list_items(self, text: str) -> List[str]:
        """
        สกัดรายการจากข้อความ
        
        Args:
            text: ข้อความที่ต้องการสกัดรายการ
            
        Returns:
            รายการที่สกัดได้
        """
        # ถ้าเป็นข้อความว่าง ให้คืนรายการว่าง
        if not text:
            return []
        
        # ตรวจสอบว่ามีเครื่องหมาย , หรือ ; หรือไม่
        if "," in text or ";" in text:
            # แยกตามเครื่องหมาย , หรือ ;
            if ";" in text:
                items = text.split(";")
            else:
                items = text.split(",")
            
            # ทำความสะอาดแต่ละรายการ
            return [self.clean_text(item) for item in items if self.clean_text(item)]
        
        # หากไม่มีเครื่องหมาย , หรือ ; ให้ตรวจสอบว่ามีบรรทัดใหม่หรือไม่
        elif "\n" in text:
            # แยกตามบรรทัดใหม่
            items = text.split("\n")
            
            # ทำความสะอาดแต่ละรายการ
            return [self.clean_text(item) for item in items if self.clean_text(item)]
        
        # หากไม่มีทั้งเครื่องหมาย , หรือ ; และบรรทัดใหม่ ให้คืนข้อความเดิมเป็นรายการเดียว
        else:
            return [self.clean_text(text)] if self.clean_text(text) else []
    
    def extract_bullet_points(self, text: str) -> List[str]:
        """
        สกัดรายการที่มีจุดนำหน้าจากข้อความ
        
        Args:
            text: ข้อความที่ต้องการสกัดรายการ
            
        Returns:
            รายการที่สกัดได้
        """
        # ถ้าเป็นข้อความว่าง ให้คืนรายการว่าง
        if not text:
            return []
        
        # แยกตามบรรทัดใหม่
        lines = text.split("\n")
        
        # กรองเฉพาะบรรทัดที่มีจุดนำหน้า
        bullet_points = []
        
        for line in lines:
            # แยกตามจุดหรือเครื่องหมาย - นำหน้า
            if line.strip().startswith("•") or line.strip().startswith("-"):
                bullet_points.append(self.clean_text(line))
            # แยกตามตัวเลขนำหน้า
            elif re.match(r"^\d+\.", line.strip()):
                bullet_points.append(self.clean_text(line))
        
        return bullet_points if bullet_points else self.extract_list_items(text)
    
    def fix_duplicate_data(self, responsibilities: List[str], career_path: List[str]) -> tuple:
        """
        แก้ไขข้อมูลซ้ำซ้อนระหว่างความรับผิดชอบและเส้นทางอาชีพ
        
        Args:
            responsibilities: รายการความรับผิดชอบ
            career_path: รายการเส้นทางอาชีพ
            
        Returns:
            (รายการความรับผิดชอบที่แก้ไขแล้ว, รายการเส้นทางอาชีพที่แก้ไขแล้ว)
        """
        if not responsibilities and not career_path:
            return [], []
        
        # สร้างรายการข้อมูลใหม่
        fixed_responsibilities = []
        fixed_career_path = []
        
        # ทำให้เป็นเซตเพื่อเปรียบเทียบข้อมูลซ้ำซ้อน
        resp_set = set()
        
        # ตรวจสอบความรับผิดชอบทั้งหมด
        for resp in responsibilities:
            clean_resp = self.clean_text(resp)
            
            # ข้ามข้อความที่ว่าง
            if not clean_resp:
                continue
                
            # ตรวจสอบว่าเป็นรายการความรับผิดชอบหรือไม่
            if self.is_responsibility_item(clean_resp):
                # ตรวจสอบว่าซ้ำกันหรือไม่
                if clean_resp not in resp_set:
                    resp_set.add(clean_resp)
                    fixed_responsibilities.append(clean_resp)
        
        # ตรวจสอบเส้นทางอาชีพทั้งหมด
        for path in career_path:
            clean_path = self.clean_text(path)
            
            # ข้ามข้อความที่ว่าง
            if not clean_path:
                continue
            
            # ถ้าเป็นเส้นทางอาชีพและไม่ซ้ำกับความรับผิดชอบ
            if self.is_career_path_item(clean_path) and clean_path not in resp_set:
                fixed_career_path.append(clean_path)
            # ถ้าเป็นความรับผิดชอบและไม่ซ้ำกับรายการก่อนหน้า
            elif self.is_responsibility_item(clean_path) and clean_path not in resp_set:
                resp_set.add(clean_path)
                fixed_responsibilities.append(clean_path)
        
        return fixed_responsibilities, fixed_career_path
    
    def normalize_job_title(self, job_title: str) -> str:
        """
        ปรับชื่อตำแหน่งงานให้เป็นมาตรฐาน
        
        Args:
            job_title: ชื่อตำแหน่งงานที่ต้องการปรับ
            
        Returns:
            ชื่อตำแหน่งงานที่เป็นมาตรฐาน
        """
        # แยกคำด้วยขีด - และเปลี่ยนเป็นช่องว่าง
        job_title = job_title.replace("-", " ")
        
        # แปลงเป็นตัวพิมพ์ใหญ่เฉพาะตัวแรกของแต่ละคำ (Title Case)
        title_case = " ".join(word.capitalize() for word in job_title.split())
        
        # กรณีพิเศษสำหรับคำบางคำ
        special_cases = {
            "Ui": "UI",
            "Ux": "UX",
            "Api": "API",
            "Qa": "QA",
            "Cto": "CTO",
            "Cio": "CIO",
            "Ios": "iOS",
            "Devops": "DevOps",
            "Fullstack": "Full Stack",
            "Frontend": "Frontend",
            "Backend": "Backend",
            "It": "IT"
        }
        
        # แทนที่คำพิเศษ
        for old, new in special_cases.items():
            # ตรวจสอบว่าเป็นคำเดี่ยวหรือไม่
            title_case = re.sub(r'\b' + old + r'\b', new, title_case)
        
        return title_case
    
    def process_txt_file(self, filepath: str) -> Dict[str, Any]:
        """
        แปลงไฟล์ข้อความเป็นข้อมูล JSON
        
        Args:
            filepath: เส้นทางไฟล์ข้อความ
            
        Returns:
            ข้อมูล JSON ที่แปลงแล้ว
        """
        try:
            # อ่านเนื้อหาไฟล์
            with open(filepath, "r", encoding="utf-8") as file:
                content = file.read().strip()
            
            # ดึงชื่อตำแหน่งงานจากชื่อไฟล์
            filename = os.path.basename(filepath)
            job_title = self.normalize_job_title(filename.replace(".txt", ""))
            
            # สกัดข้อมูลแต่ละส่วน
            description = self.extract_section(content, self.section_patterns["description"])
            
            # ถ้าไม่พบ description ให้ใช้ย่อหน้าแรก
            if not description and content:
                paragraphs = content.split("\n\n")
                if paragraphs:
                    description = self.clean_text(paragraphs[0])
            
            # สกัดข้อมูลส่วนอื่นๆ
            responsibilities_text = self.extract_section(content, self.section_patterns["responsibilities"])
            education_text = self.extract_section(content, self.section_patterns["education"])
            career_path_text = self.extract_section(content, self.section_patterns["career_path"])
            
            # แปลงข้อความเป็นรายการ
            responsibilities_raw = self.extract_bullet_points(responsibilities_text)
            education = self.extract_list_items(education_text)
            career_path_raw = self.extract_bullet_points(career_path_text)
            
            # ถ้าไม่พบในรูปแบบที่กำหนด ให้ตรวจสอบจุดนำหน้าที่พบในไฟล์
            if not responsibilities_raw:
                # ค้นหารายการที่ขึ้นต้นด้วย • หรือ -
                bullet_points = re.findall(r"(?:^|\n)[•\-]\s*(.+?)(?=\n[•\-]|\n\n|\Z)", content, re.DOTALL)
                responsibilities_raw = [self.clean_text(point) for point in bullet_points if self.clean_text(point)]
            
            # ถ้าไม่พบการศึกษา ให้ค้นหาประโยคที่เกี่ยวกับการศึกษา
            if not education:
                education_sentences = re.findall(r"จบการศึกษา[^.]*?(?:ปริญญา|วิทยาศาสตร์|วิศวกรรม|เทคโนโลยี)[^.]*?\.", content)
                education = [self.clean_text(sentence) for sentence in education_sentences if self.clean_text(sentence)]
            
            # แก้ไขข้อมูลซ้ำซ้อนระหว่างความรับผิดชอบและเส้นทางอาชีพ
            responsibilities, career_path = self.fix_duplicate_data(responsibilities_raw, career_path_raw)
            
            # จัดเตรียมข้อมูล JSON
            job_data = {
                "title": job_title,
                "description": description,
                "responsibilities": responsibilities,
                "education": education,
                "career_path": career_path,
                "source_file": filename
            }
            
            return job_data
            
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการแปลงไฟล์ {filepath}: {str(e)}")
            return {
                "title": os.path.basename(filepath).replace(".txt", ""),
                "description": "",
                "responsibilities": [],
                "education": [],
                "career_path": [],
                "source_file": os.path.basename(filepath),
                "error": str(e)
            }
    
    def process_all_files(self) -> Dict[str, Dict[str, Any]]:
        """
        แปลงไฟล์ข้อความทั้งหมดเป็นข้อมูล JSON
        
        Returns:
            ข้อมูล JSON ที่แปลงแล้ว
        """
        try:
            # ตรวจสอบว่ามีโฟลเดอร์ข้อมูลหรือไม่
            if not os.path.exists(self.input_folder):
                logger.error(f"ไม่พบโฟลเดอร์ข้อมูล {self.input_folder}")
                print(f"{Colors.FAIL}❌ ไม่พบโฟลเดอร์ข้อมูล {self.input_folder}{Colors.ENDC}")
                return {}
            
            # ค้นหาไฟล์ข้อความทั้งหมด
            txt_files = [f for f in os.listdir(self.input_folder) if f.endswith(".txt")]
            
            if not txt_files:
                logger.error(f"ไม่พบไฟล์ข้อความใน {self.input_folder}")
                print(f"{Colors.FAIL}❌ ไม่พบไฟล์ข้อความใน {self.input_folder}{Colors.ENDC}")
                return {}
            
            logger.info(f"พบไฟล์ข้อความทั้งหมด {len(txt_files)} ไฟล์")
            print(f"{Colors.CYAN}🔍 พบไฟล์ข้อความทั้งหมด {len(txt_files)} ไฟล์{Colors.ENDC}")
            
            # แปลงไฟล์ข้อความทั้งหมด
            job_data = {}
            
            for filename in tqdm(txt_files, desc="📝 แปลงข้อมูลอาชีพ", unit="file"):
                filepath = os.path.join(self.input_folder, filename)
                job_info = self.process_txt_file(filepath)
                
                if job_info and job_info.get("title"):
                    job_data[job_info["title"]] = job_info
            
            logger.info(f"แปลงข้อมูลสำเร็จ {len(job_data)} ตำแหน่ง")
            print(f"{Colors.GREEN}✅ แปลงข้อมูลสำเร็จ {len(job_data)} ตำแหน่ง{Colors.ENDC}")
            
            self.job_data = job_data
            return job_data
            
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการแปลงข้อมูล: {str(e)}")
            print(f"{Colors.FAIL}❌ เกิดข้อผิดพลาดในการแปลงข้อมูล: {str(e)}{Colors.ENDC}")
            return {}
    
    def save_to_json(self) -> bool:
        """
        บันทึกข้อมูลลงในไฟล์ JSON
        
        Returns:
            True ถ้าบันทึกสำเร็จ, False ถ้าไม่สำเร็จ
        """
        if not self.job_data:
            logger.error("ไม่มีข้อมูลที่จะบันทึก")
            print(f"{Colors.FAIL}❌ ไม่มีข้อมูลที่จะบันทึก{Colors.ENDC}")
            return False
        
        try:
            logger.info(f"กำลังบันทึกข้อมูลลงในไฟล์ {self.output_path}")
            print(f"{Colors.CYAN}📝 กำลังบันทึกข้อมูลลงในไฟล์ {self.output_path}{Colors.ENDC}")
            
            # สร้างโฟลเดอร์หากยังไม่มี
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
            
            with open(self.output_path, "w", encoding="utf-8") as file:
                json.dump(self.job_data, file, indent=4, ensure_ascii=False)
            
            logger.info("บันทึกข้อมูลลงในไฟล์ JSON สำเร็จ")
            print(f"{Colors.GREEN}✅ บันทึกข้อมูลลงในไฟล์ JSON สำเร็จ{Colors.ENDC}")
            return True
            
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการบันทึกข้อมูลลงในไฟล์ JSON: {str(e)}")
            print(f"{Colors.FAIL}❌ เกิดข้อผิดพลาดในการบันทึกข้อมูลลงในไฟล์ JSON: {str(e)}{Colors.ENDC}")
            return False
    
    def create_summary_file(self) -> bool:
        """
        สร้างไฟล์สรุปข้อมูลอาชีพ
        
        Returns:
            True ถ้าสร้างสำเร็จ, False ถ้าไม่สำเร็จ
        """
        if not self.job_data:
            logger.error("ไม่มีข้อมูลที่จะสรุป")
            print(f"{Colors.FAIL}❌ ไม่มีข้อมูลที่จะสรุป{Colors.ENDC}")
            return False
        
        try:
            summary_path = os.path.join(self.output_folder, "jobs_data_summary.md")
            logger.info(f"กำลังสร้างไฟล์สรุป {summary_path}")
            print(f"{Colors.CYAN}📊 กำลังสร้างไฟล์สรุป {summary_path}{Colors.ENDC}")
            
            # สร้างโฟลเดอร์หากยังไม่มี
            os.makedirs(os.path.dirname(summary_path), exist_ok=True)
            
            with open(summary_path, "w", encoding="utf-8") as file:
                file.write("# สรุปข้อมูลอาชีพด้าน IT\n\n")
                file.write(f"วันที่แปลงข้อมูล: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                file.write(f"จำนวนอาชีพทั้งหมด: {len(self.job_data)}\n\n")
                
                for job_title, job_info in sorted(self.job_data.items()):
                    file.write(f"## {job_title}\n\n")
                    
                    if job_info["description"]:
                        file.write(f"{job_info['description']}\n\n")
                    
                    if job_info["responsibilities"]:
                        file.write("### ความรับผิดชอบ\n\n")
                        for resp in job_info["responsibilities"]:
                            file.write(f"- {resp}\n")
                        file.write("\n")
                    
                    if job_info["education"]:
                        file.write("### การศึกษา\n\n")
                        for edu in job_info["education"]:
                            file.write(f"- {edu}\n")
                        file.write("\n")
                    
                    if job_info["career_path"]:
                        file.write("### เส้นทางอาชีพ\n\n")
                        for path in job_info["career_path"]:
                            file.write(f"- {path}\n")
                        file.write("\n")
                    
                    file.write("---\n\n")
            
            logger.info("สร้างไฟล์สรุปสำเร็จ")
            print(f"{Colors.GREEN}✅ สร้างไฟล์สรุปสำเร็จ{Colors.ENDC}")
            return True
            
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการสร้างไฟล์สรุป: {str(e)}")
            print(f"{Colors.FAIL}❌ เกิดข้อผิดพลาดในการสร้างไฟล์สรุป: {str(e)}{Colors.ENDC}")
            return False
    
    def convert(self) -> Dict[str, Any]:
        """
        แปลงข้อมูลทั้งหมด
        
        Returns:
            ผลลัพธ์การแปลงข้อมูล
        """
        print(f"\n{Colors.BOLD}{Colors.HEADER}===== Text to JSON Converter ====={Colors.ENDC}\n")
        
        # สำรองไฟล์เดิม
        self.backup_existing_file()
        
        # แปลงข้อมูลทั้งหมด
        job_data = self.process_all_files()
        if not job_data:
            return {
                "success": False,
                "error": "ไม่สามารถแปลงข้อมูลได้",
                "jobs_count": 0
            }
        
        # บันทึกข้อมูลลงในไฟล์ JSON
        json_result = self.save_to_json()
        
        # สร้างไฟล์สรุป
        summary_result = self.create_summary_file()
        
        return {
            "success": json_result and summary_result,
            "jobs_count": len(job_data),
            "json_file": self.output_path,
            "summary_file": os.path.join(self.output_folder, "jobs_data_summary.md"),
            "json_saved": json_result,
            "summary_saved": summary_result
        }


def main():
    """
    ฟังก์ชันหลักสำหรับการแปลงข้อมูล
    """
    # สร้างตัวแยกวิเคราะห์อาร์กิวเมนต์
    parser = argparse.ArgumentParser(description='เครื่องมือแปลงข้อมูลข้อความเป็น JSON สำหรับข้อมูลอาชีพ')
    parser.add_argument('-i', '--input', type=str, default="data/raw/jobsdb",
                        help='โฟลเดอร์ที่เก็บไฟล์ข้อความ')
    parser.add_argument('-o', '--output', type=str, default="data/json",
                        help='โฟลเดอร์สำหรับบันทึกไฟล์ JSON')
    parser.add_argument('-f', '--filename', type=str, default="jobs_data.json",
                        help='ชื่อไฟล์ JSON ที่จะบันทึก')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='แสดงรายละเอียดการทำงานโดยละเอียด')
    
    # แยกวิเคราะห์อาร์กิวเมนต์
    args = parser.parse_args()
    
    # ตั้งค่าระดับการบันทึกล็อก
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)
    
    # สร้างและรันตัวแปลงข้อมูล
    converter = TextToJsonConverterFixed(args.input, args.output, args.filename)
    result = converter.convert()
    
    # สรุปผลการทำงาน
    print(f"\n{Colors.BOLD}{Colors.HEADER}===== สรุปผลการแปลงข้อมูล ====={Colors.ENDC}")
    print(f"{Colors.CYAN}👉 จำนวนอาชีพที่พบ: {Colors.BOLD}{result['jobs_count']}{Colors.ENDC}")
    print(f"{Colors.CYAN}👉 บันทึกไฟล์ JSON: {Colors.GREEN if result.get('json_saved', False) else Colors.FAIL}{'✓' if result.get('json_saved', False) else '✗'}{Colors.ENDC}")
    print(f"{Colors.CYAN}👉 บันทึกไฟล์สรุป: {Colors.GREEN if result.get('summary_saved', False) else Colors.FAIL}{'✓' if result.get('summary_saved', False) else '✗'}{Colors.ENDC}")
    
    if result["success"]:
        print(f"{Colors.CYAN}👉 ไฟล์ JSON: {Colors.BOLD}{result.get('json_file', '')}{Colors.ENDC}")
        print(f"{Colors.CYAN}👉 ไฟล์สรุป: {Colors.BOLD}{result.get('summary_file', '')}{Colors.ENDC}")
        print(f"{Colors.CYAN}👉 สถานะโดยรวม: {Colors.GREEN}สำเร็จ ✓{Colors.ENDC}")
        print(f"\n{Colors.GREEN}🎉 การแปลงข้อมูลเสร็จสมบูรณ์! 🎉{Colors.ENDC}")
    else:
        print(f"{Colors.CYAN}👉 ข้อผิดพลาด: {Colors.FAIL}{result.get('error', 'ไม่ทราบสาเหตุ')}{Colors.ENDC}")
        print(f"{Colors.CYAN}👉 สถานะโดยรวม: {Colors.FAIL}ไม่สำเร็จ ✗{Colors.ENDC}")
        print(f"\n{Colors.FAIL}❌ การแปลงข้อมูลไม่สำเร็จ โปรดตรวจสอบล็อกเพื่อดูรายละเอียดเพิ่มเติม{Colors.ENDC}")


if __name__ == "__main__":
    main()