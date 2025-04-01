import requests
from bs4 import BeautifulSoup
import os
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Set, Optional
from tqdm import tqdm

# กำหนด logger สำหรับการบันทึกข้อมูล
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("src/logs/talance_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("talance_scraper")

class TalanceScraper:
    """
    คลาสสำหรับการดึงข้อมูลตำแหน่งงานจากเว็บไซต์ Talance Tech
    """
    def __init__(self, output_folder: str = "data/json"):
        """
        เริ่มต้นการทำงานของ scraper
        
        Args:
            output_folder: โฟลเดอร์สำหรับบันทึกข้อมูล
        """
        self.base_url = "https://www.talance.tech/blog/it-job-responsibility/"
        self.output_folder = output_folder
        
        # สร้างโฟลเดอร์ output ถ้ายังไม่มี
        Path(self.output_folder).mkdir(parents=True, exist_ok=True)
        
        # รายการที่ต้องลบออกจาก responsibilities
        self.unwanted_items = {
            "Career Path", "Specialisations", "Find Talents", "Permanent Recruitment",
            "Contract Staffing (Outsource)", "Executive Search", "Freelance", "Jobs",
            "Job Seekers", "Send your CV", "Salary Reports", "Career Advices",
            "Hiring Advices", "E-Books", "Case Study", "About Us", "Contact Us",
            "Our Team", "Career", "Facebook", "Linkedin", "Customer privacy policy",
            "Service terms & conditions", "สายงาน", "อาชีพในสายงาน", "อ่านบทความเพิ่มเติม","บทความที่เกี่ยวข้อง"
        }
        
        # Header สำหรับการส่งคำขอ HTTP
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    
    def fetch_page(self) -> Optional[BeautifulSoup]:
        """
        ดึงข้อมูลจากเว็บไซต์
        
        Returns:
            BeautifulSoup object หรือ None ถ้าเกิดข้อผิดพลาด
        """
        try:
            response = requests.get(self.base_url, headers=self.headers, timeout=30)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                logger.error(f"ไม่สามารถเข้าถึงเว็บไซต์ สถานะ: {response.status_code}")
                return None
            
            return BeautifulSoup(response.text, "html.parser")
            
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล: {str(e)}")
            return None
    
    def sanitize_filename(self, filename: str) -> str:
        """
        ทำความสะอาดชื่อไฟล์เพื่อไม่ให้มีอักขระที่ไม่สามารถใช้ในชื่อไฟล์ได้
        
        Args:
            filename: ชื่อไฟล์ที่ต้องการทำความสะอาด
            
        Returns:
            ชื่อไฟล์ที่ทำความสะอาดแล้ว
        """
        # แทนที่อักขระพิเศษ
        sanitized = re.sub(r'[\\/*?:"<>|]', '-', filename)
        # ปรับให้มีความยาวไม่เกิน 200 ตัวอักษร
        if len(sanitized) > 200:
            sanitized = sanitized[:197] + "..."
        
        return sanitized
    
    def is_wanted_responsibility(self, text: str) -> bool:
        """
        ตรวจสอบว่าข้อความเป็นความรับผิดชอบที่ต้องการหรือไม่
        
        Args:
            text: ข้อความที่ต้องการตรวจสอบ
            
        Returns:
            True ถ้าเป็นความรับผิดชอบที่ต้องการ, False ถ้าไม่ใช่
        """
        # ตรวจสอบว่าข้อความอยู่ในรายการที่ไม่ต้องการหรือไม่
        if text in self.unwanted_items:
            return False
        
        # ตรวจสอบว่าข้อความเป็นลิงก์หรือไม่
        if text.startswith("http") or ".com" in text or ".co.th" in text or ".org" in text:
            return False
        
        # ตรวจสอบรูปแบบที่ไม่ต้องการ (เช่น "ตำแหน่งงาน:")
        unwanted_patterns = [
            r"^ตำแหน่งงาน:", r"^อัตราเงินเดือน:", r"^แหล่งข้อมูล:", 
            r"^ที่มา:", r"^ข้อมูลจาก:", r"^อ้างอิง:", r"^หมายเหตุ:"
        ]
        for pattern in unwanted_patterns:
            if re.match(pattern, text):
                return False
        
        return True
    
    def extract_job_data(self, soup: BeautifulSoup) -> Dict[str, Dict[str, Any]]:
        """
        สกัดข้อมูลตำแหน่งงานจาก BeautifulSoup object
        
        Args:
            soup: BeautifulSoup object ที่มีข้อมูล HTML
            
        Returns:
            พจนานุกรมที่มีข้อมูลตำแหน่งงาน
        """
        job_data = {}
        current_title = None
        current_desc = ""
        current_responsibilities = []
        last_element_was_ul = False
        
        # ดึงเนื้อหาทั้งหมดที่อยู่ใน <h2>, <h3>, <p>, <ul>
        elements = soup.find_all(["h2", "h3", "p", "ul"])
        
        for element in elements:
            # ถ้าเป็น h2 หรือ h3 (หัวข้อใหม่)
            if element.name in ["h2", "h3"]:
                if current_title:
                    # กรองความรับผิดชอบที่ไม่ต้องการออก
                    filtered_responsibilities = [
                        item for item in current_responsibilities 
                        if self.is_wanted_responsibility(item)
                    ]
                    
                    # เก็บเฉพาะหัวข้อที่มีข้อมูลเท่านั้น
                    if current_desc.strip() or filtered_responsibilities:
                        job_data[current_title] = {
                            "description": current_desc.strip(),
                            "responsibilities": filtered_responsibilities
                        }
                
                # รีเซ็ตตัวแปรสำหรับหัวข้อใหม่
                header_text = element.text.strip()
                # ตัดตัวเลขนำหน้า (เช่น "1. Developer" -> "Developer")
                if re.match(r'^\d+\.', header_text):
                    current_title = re.sub(r'^\d+\.\s*', '', header_text)
                else:
                    current_title = header_text
                
                current_desc = ""
                current_responsibilities = []
                last_element_was_ul = False
            
            # ถ้าเป็น <p> และยังไม่เคยมี <ul> ปิดก่อนหน้านี้
            elif element.name == "p" and not last_element_was_ul:
                p_text = element.text.strip()
                # ตรวจสอบว่า p_text ไม่ใช่ลิงก์หรือข้อความที่ไม่ต้องการ
                if p_text and not p_text.startswith("http"):
                    current_desc += " " + p_text
            
            # ถ้าเป็น <ul> ให้เก็บรายการ <li>
            elif element.name == "ul":
                last_element_was_ul = True
                for li in element.find_all("li"):
                    li_text = li.text.strip()
                    if li_text:
                        current_responsibilities.append(li_text)
            
            # หลังจากประมวลผล <ul> เสร็จแล้ว ตั้งค่า last_element_was_ul
            if element.name != "ul":
                last_element_was_ul = False
        
        # บันทึกข้อมูลของหัวข้อสุดท้าย (เฉพาะอันที่มีข้อมูล)
        if current_title:
            filtered_responsibilities = [
                item for item in current_responsibilities 
                if self.is_wanted_responsibility(item)
            ]
            
            if current_desc.strip() or filtered_responsibilities:
                job_data[current_title] = {
                    "description": current_desc.strip(),
                    "responsibilities": filtered_responsibilities
                }
        
        return job_data
    
    def save_job_data(self, job_data: Dict[str, Dict[str, Any]]) -> int:
        """
        บันทึกข้อมูลตำแหน่งงานลงในไฟล์
        
        Args:
            job_data: พจนานุกรมที่มีข้อมูลตำแหน่งงาน
            
        Returns:
            จำนวนไฟล์ที่บันทึกสำเร็จ
        """
        success_count = 0
        
        for job_title, data in tqdm(job_data.items(), desc="Saving job data"):
            # ทำความสะอาดชื่อไฟล์
            safe_filename = self.sanitize_filename(job_title)
            file_path = os.path.join(self.output_folder, f"{safe_filename}.txt")
            
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    # บันทึก description
                    file.write(f"Description:\n{data['description']}\n\n")
                    
                    # บันทึก responsibilities
                    if data['responsibilities']:
                        file.write("Responsibilities:\n")
                        for responsibility in data['responsibilities']:
                            file.write(f"• {responsibility}\n")
                
                logger.info(f"ข้อมูลสำหรับ {job_title} ถูกบันทึกที่: {file_path}")
                success_count += 1
                
            except Exception as e:
                logger.error(f"เกิดข้อผิดพลาดในการบันทึกข้อมูลสำหรับ {job_title}: {str(e)}")
        
        return success_count
    
    def create_summary_file(self, job_data: Dict[str, Dict[str, Any]]) -> None:
        """
        สร้างไฟล์สรุปข้อมูลตำแหน่งงาน
        
        Args:
            job_data: พจนานุกรมที่มีข้อมูลตำแหน่งงาน
        """
        try:
            summary_path = os.path.join(self.output_folder, "_summary.txt")
            
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write("# สรุปข้อมูลตำแหน่งงาน IT จาก Talance Tech\n\n")
                f.write(f"จำนวนตำแหน่งงานทั้งหมด: {len(job_data)}\n\n")
                
                f.write("## รายการตำแหน่งงาน\n\n")
                for i, job_title in enumerate(sorted(job_data.keys()), 1):
                    resp_count = len(job_data[job_title]["responsibilities"])
                    f.write(f"{i}. {job_title} ({resp_count} ความรับผิดชอบ)\n")
                
                f.write("\n## ที่มาข้อมูล\n\n")
                f.write(f"ข้อมูลดึงมาจาก: {self.base_url}\n")
                f.write(f"วันที่ดึงข้อมูล: {logging.root.handlers[0].formatter.converter()}\n")
            
            logger.info(f"สร้างไฟล์สรุป {summary_path} สำเร็จ")
            
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการสร้างไฟล์สรุป: {str(e)}")
    
    def scrape(self) -> Dict[str, Any]:
        """
        ดึงข้อมูลตำแหน่งงานทั้งหมด
        
        Returns:
            ผลลัพธ์การดึงข้อมูล
        """
        logger.info(f"เริ่มดึงข้อมูลจาก {self.base_url}")
        
        # ดึงข้อมูลจากเว็บไซต์
        soup = self.fetch_page()
        if not soup:
            logger.error("ไม่สามารถดึงข้อมูลจากเว็บไซต์ได้")
            return {
                "success": False,
                "jobs_count": 0,
                "files_saved": 0,
                "error": "ไม่สามารถดึงข้อมูลจากเว็บไซต์ได้"
            }
        
        # สกัดข้อมูลตำแหน่งงาน
        job_data = self.extract_job_data(soup)
        logger.info(f"สกัดข้อมูลตำแหน่งงานสำเร็จ {len(job_data)} ตำแหน่ง")
        
        # บันทึกข้อมูลลงในไฟล์
        files_saved = self.save_job_data(job_data)
        logger.info(f"บันทึกข้อมูลสำเร็จ {files_saved} ไฟล์")
        
        # สร้างไฟล์สรุป
        self.create_summary_file(job_data)
        
        return {
            "success": files_saved > 0,
            "jobs_count": len(job_data),
            "files_saved": files_saved,
            "output_folder": self.output_folder
        }


def main():
    """
    ฟังก์ชันหลักสำหรับการดึงข้อมูล
    """
    scraper = TalanceScraper()
    result = scraper.scrape()
    
    print("\nTalance Scraping Summary:")
    print(f"- จำนวนตำแหน่งงานที่พบ: {result['jobs_count']}")
    print(f"- ไฟล์ที่บันทึกสำเร็จ: {result['files_saved']}")
    print(f"- บันทึกไว้ที่: {result['output_folder']}")
    print(f"- สถานะโดยรวม: {'สำเร็จ' if result['success'] else 'ไม่สำเร็จ'}")
    
    # หากไม่สำเร็จและมีข้อความข้อผิดพลาด
    if not result['success'] and 'error' in result:
        print(f"- ข้อผิดพลาด: {result['error']}")


if __name__ == "__main__":
    main()