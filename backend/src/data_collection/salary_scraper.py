#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Set, Any, Optional
from urllib3.exceptions import InsecureRequestWarning

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from tqdm import tqdm
import colorama

# เริ่มต้นใช้งาน colorama
colorama.init()

# ปิดการแจ้งเตือน SSL เพื่อให้สามารถทำงานกับเว็บไซต์ที่ไม่มี SSL ได้
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

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
log_dir = Path("logs")
log_dir.mkdir(parents=True, exist_ok=True)

# ตั้งค่าการบันทึกล็อก
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "salary_scraper.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("salary_scraper")

class ISMTechSalaryScraper:
    def __init__(self, url: str = "https://www.ismtech.net/th/it-salary-report/", 
                 output_folder: str = "data/raw/other_sources", 
                 filename: str = "it_salary_data.json",
                 timeout: int = 30):
        self.base_url = url
        self.output_folder = output_folder
        self.filename = filename
        self.timeout = timeout
        self.json_file_path = os.path.join(output_folder, filename)
        self.summary_file_path = os.path.join(output_folder, "salary_summary.md")
        
        # สร้างโฟลเดอร์ output ถ้ายังไม่มี
        Path(self.output_folder).mkdir(parents=True, exist_ok=True)
        
        # Header สำหรับการส่งคำขอ HTTP
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Referer": "https://www.google.com/",
            "Connection": "keep-alive"
        }
        
        # ข้อมูลที่ดึงมา
        self.job_data = {}
    
    def backup_existing_file(self) -> None:
        if os.path.exists(self.json_file_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{os.path.splitext(self.json_file_path)[0]}_{timestamp}.json"
            
            try:
                import shutil
                shutil.copy2(self.json_file_path, backup_file)
                logger.info(f"สำรองไฟล์เดิมไว้ที่: {backup_file}")
                print(f"{Colors.CYAN}📋 สำรองไฟล์เดิมไว้ที่: {backup_file}{Colors.ENDC}")
            except Exception as e:
                logger.error(f"ไม่สามารถสำรองไฟล์เดิมได้: {str(e)}")
                print(f"{Colors.FAIL}❌ ไม่สามารถสำรองไฟล์เดิมได้: {str(e)}{Colors.ENDC}")
    
    def fetch_page(self) -> Optional[BeautifulSoup]:
        try:
            logger.info(f"กำลังดึงข้อมูลจาก {self.base_url}")
            print(f"{Colors.CYAN}🌐 กำลังดึงข้อมูลจาก {self.base_url}{Colors.ENDC}")
            
            response = requests.get(
                self.base_url, 
                headers=self.headers, 
                timeout=self.timeout,
                verify=False
            )
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                logger.error(f"ไม่สามารถเข้าถึงเว็บไซต์ สถานะ: {response.status_code}")
                print(f"{Colors.FAIL}❌ ไม่สามารถเข้าถึงเว็บไซต์! สถานะ: {response.status_code}{Colors.ENDC}")
                return None
            
            logger.info("ดึงข้อมูลจากเว็บไซต์สำเร็จ")
            print(f"{Colors.GREEN}✅ ดึงข้อมูลจากเว็บไซต์สำเร็จ{Colors.ENDC}")
            return BeautifulSoup(response.text, "html.parser")
            
        except requests.exceptions.Timeout:
            logger.error(f"การเชื่อมต่อหมดเวลา (timeout) หลังจาก {self.timeout} วินาที")
            print(f"{Colors.FAIL}❌ การเชื่อมต่อหมดเวลา (timeout) หลังจาก {self.timeout} วินาที{Colors.ENDC}")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("เกิดข้อผิดพลาดในการเชื่อมต่อ")
            print(f"{Colors.FAIL}❌ เกิดข้อผิดพลาดในการเชื่อมต่อ{Colors.ENDC}")
            return None
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล: {str(e)}")
            print(f"{Colors.FAIL}❌ เกิดข้อผิดพลาดในการดึงข้อมูล: {str(e)}{Colors.ENDC}")
            return None
    
    def extract_salary_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        try:
            logger.info("กำลังสกัดข้อมูลเงินเดือน")
            print(f"{Colors.CYAN}🔍 กำลังสกัดข้อมูลเงินเดือน...{Colors.ENDC}")
            
            # ดึงข้อมูลตำแหน่งงานทั้งหมด
            job_titles = [title.text.strip() for title in soup.find_all(class_="entry-title")]
            logger.info(f"พบตำแหน่งงานทั้งหมด {len(job_titles)} ตำแหน่ง")
            print(f"{Colors.GREEN}✓ พบตำแหน่งงานทั้งหมด {len(job_titles)} ตำแหน่ง{Colors.ENDC}")
            
            # ดึงข้อมูลทักษะที่ต้องใช้
            job_skills = [skill.text.strip() for skill in soup.find_all(class_="entry-skill")]
            logger.info(f"พบทักษะทั้งหมด {len(job_skills)} รายการ")
            print(f"{Colors.GREEN}✓ พบทักษะทั้งหมด {len(job_skills)} รายการ{Colors.ENDC}")
            
            # ค้นหาตารางเงินเดือนทั้งหมด
            salary_tables = soup.find_all("div", class_="entry-summary")
            logger.info(f"พบตารางเงินเดือนทั้งหมด {len(salary_tables)} ตาราง")
            print(f"{Colors.GREEN}✓ พบตารางเงินเดือนทั้งหมด {len(salary_tables)} ตาราง{Colors.ENDC}")
            
            # เก็บข้อมูลทั้งหมด
            job_data = {}
            
            # ใช้ tqdm สร้าง progress bar ที่สวยงาม
            for index, table in enumerate(tqdm(salary_tables, desc="📊 ประมวลผลข้อมูลตำแหน่งงาน", unit="job")):
                job_name = job_titles[index] if index < len(job_titles) else f"ตำแหน่งที่ {index+1}"
                skills = job_skills[index] if index < len(job_skills) else "ไม่พบข้อมูลทักษะ"
                
                # ค้นหาแถวของข้อมูลเงินเดือน
                salary_raw = []
                tbody = table.find("tbody")
                
                if tbody:
                    rows = tbody.find_all("tr")
                    
                    for row in rows:
                        # ดึงข้อความทั้งหมดของ <tr> เป็น 1 บรรทัด (เชื่อมด้วย " | ")
                        cells = row.find_all("td")
                        if cells:
                            row_text = " | ".join(cell.text.strip() for cell in cells)
                            
                            if row_text:
                                salary_raw.append(row_text)  # เก็บข้อมูลดิบก่อน
                
                # แยกข้อมูลเป็นคู่ (ประสบการณ์, เงินเดือน)
                salary_list = []
                salary_set: Set[Tuple[str, str]] = set()  # ใช้ set() เพื่อตรวจสอบค่าซ้ำ
                
                for raw_text in salary_raw:
                    parts = raw_text.split(" | ")  # แยกข้อมูลออกจาก "|"
                    
                    for i in range(0, len(parts), 2):
                        if i + 1 < len(parts):  # ตรวจสอบว่ามีคู่
                            exp_part = parts[i].strip()
                            salary_part = parts[i + 1].strip()
                            
                            # ตรวจสอบความถูกต้องของข้อมูล
                            if exp_part and salary_part and self._validate_salary_data(exp_part, salary_part):
                                salary_entry = (exp_part, salary_part)
                                
                                if salary_entry not in salary_set:  # ตรวจสอบค่าซ้ำ
                                    salary_set.add(salary_entry)
                                    salary_list.append({
                                        "experience": exp_part, 
                                        "salary": salary_part
                                    })
                
                # จัดเก็บข้อมูลลง dictionary
                job_data[job_name] = {
                    "skills": skills,
                    "salary": salary_list
                }
            
            logger.info(f"สกัดข้อมูลเงินเดือนสำเร็จ {len(job_data)} ตำแหน่ง")
            print(f"{Colors.GREEN}✅ สกัดข้อมูลเงินเดือนสำเร็จ {len(job_data)} ตำแหน่ง{Colors.ENDC}")
            
            self.job_data = job_data
            return job_data
            
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการสกัดข้อมูลเงินเดือน: {str(e)}")
            print(f"{Colors.FAIL}❌ เกิดข้อผิดพลาดในการสกัดข้อมูลเงินเดือน: {str(e)}{Colors.ENDC}")
            return {}
    
    def _validate_salary_data(self, experience: str, salary: str) -> bool:
        # ตรวจสอบว่าข้อมูลไม่ว่าง
        if not experience or not salary:
            return False
        
        # ตรวจสอบรูปแบบคร่าวๆ ว่าเป็นข้อมูลประสบการณ์และเงินเดือน
        if '-' not in experience or '-' not in salary:
            return False
        
        # เพิ่มเติมการตรวจสอบอื่นๆ ตามต้องการ
        # เช่น ตรวจสอบว่ามีตัวเลขในข้อมูล
        if not any(c.isdigit() for c in experience) or not any(c.isdigit() for c in salary):
            return False
        
        return True
    
    def save_to_json(self) -> bool:
        if not self.job_data:
            logger.error("ไม่มีข้อมูลที่จะบันทึก")
            print(f"{Colors.FAIL}❌ ไม่มีข้อมูลที่จะบันทึก{Colors.ENDC}")
            return False
        
        try:
            logger.info(f"กำลังบันทึกข้อมูลลงในไฟล์ {self.json_file_path}")
            print(f"{Colors.CYAN}📝 กำลังบันทึกข้อมูลลงในไฟล์ {self.json_file_path}{Colors.ENDC}")
            
            # สร้างโฟลเดอร์หากยังไม่มี
            os.makedirs(os.path.dirname(self.json_file_path), exist_ok=True)
            
            with open(self.json_file_path, "w", encoding="utf-8") as file:
                json.dump(self.job_data, file, indent=4, ensure_ascii=False)
            
            logger.info("บันทึกข้อมูลลงในไฟล์ JSON สำเร็จ")
            print(f"{Colors.GREEN}✅ บันทึกข้อมูลลงในไฟล์ JSON สำเร็จ{Colors.ENDC}")
            return True
            
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการบันทึกข้อมูลลงในไฟล์ JSON: {str(e)}")
            print(f"{Colors.FAIL}❌ เกิดข้อผิดพลาดในการบันทึกข้อมูลลงในไฟล์ JSON: {str(e)}{Colors.ENDC}")
            return False
    
    def create_summary_file(self) -> bool:
        if not self.job_data:
            logger.error("ไม่มีข้อมูลที่จะสรุป")
            print(f"{Colors.FAIL}❌ ไม่มีข้อมูลที่จะสรุป{Colors.ENDC}")
            return False
        
        try:
            logger.info(f"กำลังสร้างไฟล์สรุป {self.summary_file_path}")
            print(f"{Colors.CYAN}📊 กำลังสร้างไฟล์สรุป {self.summary_file_path}{Colors.ENDC}")
            
            # สร้างโฟลเดอร์หากยังไม่มี
            os.makedirs(os.path.dirname(self.summary_file_path), exist_ok=True)
            
            with open(self.summary_file_path, "w", encoding="utf-8") as file:
                file.write("# สรุปข้อมูลเงินเดือนในสาขา IT\n\n")
                file.write(f"ข้อมูลจาก: [{self.base_url}]({self.base_url})\n\n")
                file.write(f"วันที่ดึงข้อมูล: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                file.write(f"จำนวนตำแหน่งงานทั้งหมด: {len(self.job_data)}\n\n")
                
                for job_title, job_info in self.job_data.items():
                    file.write(f"## {job_title}\n\n")
                    
                    if job_info["skills"]:
                        file.write(f"**ทักษะที่ต้องการ:** {job_info['skills']}\n\n")
                    
                    file.write("**ช่วงเงินเดือน:**\n\n")
                    
                    for salary_info in job_info["salary"]:
                        file.write(f"- {salary_info['experience']}: {salary_info['salary']}\n")
                    
                    file.write("\n---\n\n")
            
            logger.info("สร้างไฟล์สรุปสำเร็จ")
            print(f"{Colors.GREEN}✅ สร้างไฟล์สรุปสำเร็จ{Colors.ENDC}")
            return True
            
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการสร้างไฟล์สรุป: {str(e)}")
            print(f"{Colors.FAIL}❌ เกิดข้อผิดพลาดในการสร้างไฟล์สรุป: {str(e)}{Colors.ENDC}")
            return False
    
    def scrape(self) -> Dict[str, Any]:
        print(f"\n{Colors.BOLD}{Colors.HEADER}===== ISM Tech Salary Scraper ====={Colors.ENDC}\n")
        
        # สำรองไฟล์เดิม
        self.backup_existing_file()
        
        # ดึงข้อมูลจากเว็บไซต์
        soup = self.fetch_page()
        if not soup:
            return {
                "success": False,
                "error": "ไม่สามารถดึงข้อมูลจากเว็บไซต์ได้",
                "jobs_count": 0
            }
        
        # สกัดข้อมูลเงินเดือน
        salary_data = self.extract_salary_data(soup)
        if not salary_data:
            return {
                "success": False,
                "error": "ไม่สามารถสกัดข้อมูลเงินเดือนได้",
                "jobs_count": 0
            }
        
        # บันทึกข้อมูลลงในไฟล์ JSON
        json_result = self.save_to_json()
        
        # สร้างไฟล์สรุป
        summary_result = self.create_summary_file()
        
        return {
            "success": json_result and summary_result,
            "jobs_count": len(salary_data),
            "json_file": self.json_file_path,
            "summary_file": self.summary_file_path,
            "json_saved": json_result,
            "summary_saved": summary_result
        }


def main():
    # สร้างตัวแยกวิเคราะห์อาร์กิวเมนต์
    parser = argparse.ArgumentParser(description='เครื่องมือดึงข้อมูลเงินเดือนตำแหน่งงาน IT จาก ISM Technology')
    parser.add_argument('-u', '--url', type=str, default="https://www.ismtech.net/th/it-salary-report/",
                        help='URL ของเว็บไซต์ที่ต้องการดึงข้อมูล')
    parser.add_argument('-o', '--output', type=str, default="data/raw/other_sources",
                        help='พาธของโฟลเดอร์ที่ต้องการบันทึกผลลัพธ์')
    parser.add_argument('-f', '--filename', type=str, default="it_salary_data.json",
                        help='ชื่อไฟล์ JSON ที่ต้องการบันทึกผลลัพธ์')
    parser.add_argument('-t', '--timeout', type=int, default=30,
                        help='เวลาหมดเวลาสำหรับการเชื่อมต่อ (วินาที)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='แสดงรายละเอียดการทำงานโดยละเอียด')
    
    # แยกวิเคราะห์อาร์กิวเมนต์
    args = parser.parse_args()
    
    # ตั้งค่าระดับการบันทึกล็อก
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)
    
    # สร้างและรันตัวดึงข้อมูล
    scraper = ISMTechSalaryScraper(args.url, args.output, args.filename, args.timeout)
    result = scraper.scrape()
    
    # สรุปผลการทำงาน
    print(f"\n{Colors.BOLD}{Colors.HEADER}===== สรุปผลการดึงข้อมูล ====={Colors.ENDC}")
    print(f"{Colors.CYAN}👉 จำนวนตำแหน่งงานที่พบ: {Colors.BOLD}{result['jobs_count']}{Colors.ENDC}")
    print(f"{Colors.CYAN}👉 บันทึกไฟล์ JSON: {Colors.GREEN if result.get('json_saved', False) else Colors.FAIL}{'✓' if result.get('json_saved', False) else '✗'}{Colors.ENDC}")
    print(f"{Colors.CYAN}👉 บันทึกไฟล์สรุป: {Colors.GREEN if result.get('summary_saved', False) else Colors.FAIL}{'✓' if result.get('summary_saved', False) else '✗'}{Colors.ENDC}")
    
    if result["success"]:
        print(f"{Colors.CYAN}👉 ไฟล์ JSON: {Colors.BOLD}{result.get('json_file', '')}{Colors.ENDC}")
        print(f"{Colors.CYAN}👉 ไฟล์สรุป: {Colors.BOLD}{result.get('summary_file', '')}{Colors.ENDC}")
        print(f"{Colors.CYAN}👉 สถานะโดยรวม: {Colors.GREEN}สำเร็จ ✓{Colors.ENDC}")
    else:
        print(f"{Colors.CYAN}👉 ข้อผิดพลาด: {Colors.FAIL}{result.get('error', 'ไม่ทราบสาเหตุ')}{Colors.ENDC}")
        print(f"{Colors.CYAN}👉 สถานะโดยรวม: {Colors.FAIL}ไม่สำเร็จ ✗{Colors.ENDC}")


if __name__ == "__main__":
    main()