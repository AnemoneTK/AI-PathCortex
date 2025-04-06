#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import logging
import argparse
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Set, Optional
from urllib3.exceptions import InsecureRequestWarning

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
import colorama
from tqdm import tqdm

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
        logging.FileHandler(log_dir / "resp_scraper.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("resp_scraper")

class JobResponsibilityScraper:
    def __init__(self, url: str = "https://www.talance.tech/blog/it-job-responsibility/", 
                 output_folder: str = "data/raw/other_sources", 
                 filename: str = "job_responsibilities.json",
                 timeout: int = 30):
        self.url = url
        self.output_folder = output_folder
        self.filename = filename
        self.timeout = timeout
        self.json_file_path = os.path.join(output_folder, filename)
        
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
        
        # รายการที่ต้องลบออกจาก responsibilities
        self.unwanted_items = {
            "Career Path", "Specialisations", "Find Talents", "Permanent Recruitment",
            "Contract Staffing (Outsource)", "Executive Search", "Freelance", "Jobs",
            "Job Seekers", "Send your CV", "Salary Reports", "Career Advices",
            "Hiring Advices", "E-Books", "Case Study", "About Us", "Contact Us",
            "Our Team", "Career", "Facebook", "Linkedin", "Customer privacy policy",
            "Service terms & conditions", "บทความที่เกี่ยวข้อง"
        }
        
        # รายการชื่องานที่ไม่ต้องการ
        self.unwanted_titles = {
            "บทความที่เกี่ยวข้อง"
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
            logger.info(f"กำลังดึงข้อมูลจาก {self.url}")
            print(f"{Colors.CYAN}🌐 กำลังดึงข้อมูลจาก {self.url}{Colors.ENDC}")
            
            response = requests.get(
                self.url, 
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
    
    def extract_job_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        try:
            logger.info("กำลังสกัดข้อมูลความรับผิดชอบตำแหน่งงาน")
            print(f"{Colors.CYAN}🔍 กำลังสกัดข้อมูลความรับผิดชอบตำแหน่งงาน...{Colors.ENDC}")
            
            # ดึงเนื้อหาทั้งหมดที่อยู่ใน <h2>, <h3>, <p>, <ul>
            elements = soup.find_all(["h2", "h3", "p", "ul"])
            logger.info(f"พบองค์ประกอบที่เกี่ยวข้องทั้งหมด {len(elements)} รายการ")
            
            # ข้อมูลที่จะเก็บ
            job_data = {}
            current_title = None
            current_desc = ""
            current_responsibilities = []
            last_element_was_ul = False  # ใช้ตรวจสอบว่า <ul> เพิ่งปิดไปหรือไม่
            
            for element in tqdm(elements, desc="📊 ประมวลผลข้อมูลตำแหน่งงาน", unit="element"):
                # ถ้าเป็น h2 หรือ h3 (หัวข้อใหม่)
                if element.name in ["h2", "h3"]:
                    # บันทึกข้อมูลของหัวข้อก่อนหน้า (ถ้ามี)
                    if current_title and current_title not in self.unwanted_titles:
                        # กรองรายการที่ไม่ต้องการออก
                        filtered_responsibilities = [
                            item for item in current_responsibilities 
                            if item not in self.unwanted_items and len(item.strip()) > 0
                        ]
                        
                        # เก็บเฉพาะหัวข้อที่มีข้อมูลเท่านั้น
                        if (current_desc.strip() or filtered_responsibilities) and self.is_valid_description(current_desc):
                            job_data[current_title] = {
                                "description": current_desc.strip(),
                                "responsibilities": filtered_responsibilities
                            }
                    
                    # รีเซ็ตตัวแปรสำหรับหัวข้อใหม่
                    current_title = element.text.strip()
                    # ตัดตัวเลขนำหน้าและคำว่า "Job Responsibility" ออก
                    if ". " in current_title:
                        current_title = current_title.split(". ", 1)[-1]
                    
                    current_desc = ""
                    current_responsibilities = []
                    last_element_was_ul = False
                
                # ถ้าเป็น <p> และยังไม่เคยมี <ul> ปิดก่อนหน้านี้
                elif element.name == "p" and not last_element_was_ul:
                    # ตรวจสอบว่าไม่ใช่ลิงก์หรือข้อความที่ไม่ต้องการ
                    p_text = element.text.strip()
                    if p_text and not any(unwanted in p_text for unwanted in self.unwanted_items):
                        if current_desc:
                            current_desc += " " + p_text
                        else:
                            current_desc = p_text
                
                # ถ้าเป็น <ul> ให้เก็บรายการ <li>
                elif element.name == "ul":
                    last_element_was_ul = True
                    for li in element.find_all("li"):
                        li_text = li.text.strip()
                        if li_text and not any(unwanted in li_text for unwanted in self.unwanted_items):
                            current_responsibilities.append(li_text)
                else:
                    last_element_was_ul = False
            
            # บันทึกข้อมูลของหัวข้อสุดท้าย (ถ้ามี)
            if current_title and current_title not in self.unwanted_titles:
                filtered_responsibilities = [
                    item for item in current_responsibilities 
                    if item not in self.unwanted_items and len(item.strip()) > 0
                ]
                
                if (current_desc.strip() or filtered_responsibilities) and self.is_valid_description(current_desc):
                    job_data[current_title] = {
                        "description": current_desc.strip(),
                        "responsibilities": filtered_responsibilities
                    }
            
            # กรองข้อมูลที่ไม่เกี่ยวข้องออก
            job_data = self.filter_invalid_job_data(job_data)
            
            # จัดเรียงตาม key เพื่อความเป็นระเบียบ
            job_data = {k: job_data[k] for k in sorted(job_data.keys())}
            
            logger.info(f"สกัดข้อมูลความรับผิดชอบตำแหน่งงานสำเร็จ {len(job_data)} ตำแหน่ง")
            print(f"{Colors.GREEN}✅ สกัดข้อมูลความรับผิดชอบตำแหน่งงานสำเร็จ {len(job_data)} ตำแหน่ง{Colors.ENDC}")
            
            self.job_data = job_data
            return job_data
            
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการสกัดข้อมูลความรับผิดชอบตำแหน่งงาน: {str(e)}")
            print(f"{Colors.FAIL}❌ เกิดข้อผิดพลาดในการสกัดข้อมูลความรับผิดชอบตำแหน่งงาน: {str(e)}{Colors.ENDC}")
            return {}
    
    def is_valid_description(self, description: str) -> bool:
        # ถ้าคำอธิบายว่าง จะถือว่าไม่ถูกต้อง
        if not description:
            return False
        
        # ตรวจสอบคำอธิบายที่ไม่มีความหมาย (เช่น "Jo Jo Jo Jo Jo Jo")
        if re.match(r'^(jo\s*)+$', description.lower()):
            return False
        
        # ตรวจสอบคำอธิบายที่สั้นเกินไป (น้อยกว่า 10 ตัวอักษร)
        if len(description) < 10:
            return False
        
        return True
    
    def filter_invalid_job_data(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        filtered_data = {}
        
        for job_title, data in job_data.items():
            # ข้ามชื่องานที่ไม่ต้องการ
            if job_title in self.unwanted_titles:
                continue
            
            # ตรวจสอบว่าคำอธิบายถูกต้องหรือไม่
            if not self.is_valid_description(data.get("description", "")):
                continue
            
            # ตรวจสอบว่ามีความรับผิดชอบอย่างน้อย 1 รายการ
            if not data.get("responsibilities", []):
                # ถ้าไม่มีความรับผิดชอบ แต่มีคำอธิบายที่ยาวพอ (มากกว่า 100 ตัวอักษร) ก็จะเก็บไว้
                if len(data.get("description", "")) > 100:
                    filtered_data[job_title] = data
            else:
                filtered_data[job_title] = data
        
        return filtered_data
    
    def clean_job_titles(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            logger.info("กำลังทำความสะอาดชื่อตำแหน่งงาน")
            
            cleaned_job_data = {}
            
            # คำสั่งแทนที่
            replacements = {
                "Job Responsibility": "",
                "Job Responsibilities": "",
                "JobResponsibility": "",
                "Job Role": "",
                "Job Description": "",
                "IT Job": "",
                "Responsibilities": "",
                "of a": "",
                "of an": "",
                "of the": "",
                "for a": "",
                "for an": "",
                "for the": "",
            }
            
            for job_title, data in job_data.items():
                # ทำความสะอาดชื่อตำแหน่งงาน
                clean_title = job_title
                for old, new in replacements.items():
                    clean_title = clean_title.replace(old, new)
                
                # ตัดช่องว่างที่ไม่จำเป็น
                clean_title = " ".join(clean_title.split())
                
                # เพิ่มข้อมูลที่ทำความสะอาดแล้ว
                cleaned_job_data[clean_title] = data
            
            logger.info("ทำความสะอาดชื่อตำแหน่งงานสำเร็จ")
            return cleaned_job_data
            
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการทำความสะอาดชื่อตำแหน่งงาน: {str(e)}")
            return job_data
    
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
            summary_path = os.path.join(self.output_folder, "job_responsibilities_summary.md")
            logger.info(f"กำลังสร้างไฟล์สรุป {summary_path}")
            print(f"{Colors.CYAN}📊 กำลังสร้างไฟล์สรุป {summary_path}{Colors.ENDC}")
            
            # สร้างโฟลเดอร์หากยังไม่มี
            os.makedirs(os.path.dirname(summary_path), exist_ok=True)
            
            with open(summary_path, "w", encoding="utf-8") as file:
                file.write("# สรุปข้อมูลความรับผิดชอบตำแหน่งงาน IT\n\n")
                file.write(f"ข้อมูลจาก: [{self.url}]({self.url})\n\n")
                file.write(f"วันที่ดึงข้อมูล: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                file.write(f"จำนวนตำแหน่งงานทั้งหมด: {len(self.job_data)}\n\n")
                
                for job_title, job_info in self.job_data.items():
                    file.write(f"## {job_title}\n\n")
                    
                    if job_info["description"]:
                        file.write(f"{job_info['description']}\n\n")
                    
                    file.write("### ความรับผิดชอบ\n\n")
                    
                    for resp in job_info["responsibilities"]:
                        file.write(f"- {resp}\n")
                    
                    file.write("\n---\n\n")
            
            logger.info("สร้างไฟล์สรุปสำเร็จ")
            print(f"{Colors.GREEN}✅ สร้างไฟล์สรุปสำเร็จ{Colors.ENDC}")
            return True
            
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการสร้างไฟล์สรุป: {str(e)}")
            print(f"{Colors.FAIL}❌ เกิดข้อผิดพลาดในการสร้างไฟล์สรุป: {str(e)}{Colors.ENDC}")
            return False
    
    def scrape(self) -> Dict[str, Any]:
        print(f"\n{Colors.BOLD}{Colors.HEADER}===== Talance Job Responsibility Scraper ====={Colors.ENDC}\n")
        
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
        
        # สกัดข้อมูลความรับผิดชอบตำแหน่งงาน
        job_data = self.extract_job_data(soup)
        if not job_data:
            return {
                "success": False,
                "error": "ไม่สามารถสกัดข้อมูลความรับผิดชอบตำแหน่งงานได้",
                "jobs_count": 0
            }
        
        # ทำความสะอาดชื่อตำแหน่งงาน
        self.job_data = self.clean_job_titles(job_data)
        
        # บันทึกข้อมูลลงในไฟล์ JSON
        json_result = self.save_to_json()
        
        # สร้างไฟล์สรุป
        summary_result = self.create_summary_file()
        
        return {
            "success": json_result and summary_result,
            "jobs_count": len(self.job_data),
            "json_file": self.json_file_path,
            "summary_file": os.path.join(self.output_folder, "job_responsibilities_summary.md"),
            "json_saved": json_result,
            "summary_saved": summary_result
        }


def main():
    # สร้างตัวแยกวิเคราะห์อาร์กิวเมนต์
    parser = argparse.ArgumentParser(description='เครื่องมือดึงข้อมูลความรับผิดชอบตำแหน่งงาน IT จาก Talance')
    parser.add_argument('-u', '--url', type=str, default="https://www.talance.tech/blog/it-job-responsibility/",
                        help='URL ของเว็บไซต์ที่ต้องการดึงข้อมูล')
    parser.add_argument('-o', '--output', type=str, default="data/raw/other_sources",
                        help='พาธของโฟลเดอร์ที่ต้องการบันทึกผลลัพธ์')
    parser.add_argument('-f', '--filename', type=str, default="job_responsibilities.json",
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
    scraper = JobResponsibilityScraper(args.url, args.output, args.filename, args.timeout)
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

    # แสดงไอคอนอีโมจิสวยๆ ตอนจบการทำงาน
    if result["success"]:
        print(f"\n{Colors.GREEN}🎉 การดึงข้อมูลเสร็จสมบูรณ์! 🎉{Colors.ENDC}")
    else:
        print(f"\n{Colors.FAIL}❌ การดึงข้อมูลไม่สำเร็จ โปรดตรวจสอบล็อกเพื่อดูรายละเอียดเพิ่มเติม{Colors.ENDC}")


if __name__ == "__main__":
    main()