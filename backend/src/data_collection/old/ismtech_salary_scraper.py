import requests
from bs4 import BeautifulSoup
import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple, Optional
from tqdm import tqdm

# กำหนด logger สำหรับการบันทึกข้อมูล
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("src/logs/ismtech_salary_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ismtech_salary_scraper")

class ISMTechSalaryScraper:
    """
    คลาสสำหรับการดึงข้อมูลเงินเดือนจากเว็บไซต์ ISM Technology
    """
    def __init__(self, output_folder: str = "data/raw/other_sources"):
        """
        เริ่มต้นการทำงานของ scraper
        
        Args:
            output_folder: โฟลเดอร์สำหรับบันทึกข้อมูล
        """
        self.base_url = "https://www.ismtech.net/th/it-salary-report/"
        self.output_folder = output_folder
        self.json_file_path = os.path.join(output_folder, "it_salary_data.json")
        
        # สร้างโฟลเดอร์ output ถ้ายังไม่มี
        Path(self.output_folder).mkdir(parents=True, exist_ok=True)
        
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
            logger.info(f"กำลังดึงข้อมูลจาก {self.base_url}")
            response = requests.get(self.base_url, headers=self.headers, timeout=30)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                logger.error(f"ไม่สามารถเข้าถึงเว็บไซต์ สถานะ: {response.status_code}")
                return None
            
            logger.info("ดึงข้อมูลจากเว็บไซต์สำเร็จ")
            return BeautifulSoup(response.text, "html.parser")
            
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล: {str(e)}")
            return None
    
    def extract_salary_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        สกัดข้อมูลเงินเดือนจาก BeautifulSoup object
        
        Args:
            soup: BeautifulSoup object ที่มีข้อมูล HTML
            
        Returns:
            พจนานุกรมที่มีข้อมูลเงินเดือน
        """
        try:
            logger.info("กำลังสกัดข้อมูลเงินเดือน")
            
            # ดึงข้อมูลตำแหน่งงานทั้งหมด
            job_titles = [title.text.strip() for title in soup.find_all(class_="entry-title")]
            logger.info(f"พบตำแหน่งงานทั้งหมด {len(job_titles)} ตำแหน่ง")
            
            # ดึงข้อมูลทักษะที่ต้องใช้
            job_skills = [skill.text.strip() for skill in soup.find_all(class_="entry-skill")]
            logger.info(f"พบทักษะทั้งหมด {len(job_skills)} รายการ")
            
            # ค้นหาตารางเงินเดือนทั้งหมด
            salary_tables = soup.find_all("div", class_="entry-summary")
            logger.info(f"พบตารางเงินเดือนทั้งหมด {len(salary_tables)} ตาราง")
            
            # เก็บข้อมูลทั้งหมด
            job_data = {}
            
            for index, table in enumerate(tqdm(salary_tables, desc="Processing job data")):
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
                salary_set = set()  # ใช้ set() เพื่อตรวจสอบค่าซ้ำ
                
                for raw_text in salary_raw:
                    parts = raw_text.split(" | ")  # แยกข้อมูลออกจาก "|"
                    
                    for i in range(0, len(parts), 2):
                        if i + 1 < len(parts):  # ตรวจสอบว่ามีคู่
                            exp_part = parts[i].strip()
                            salary_part = parts[i + 1].strip()
                            
                            # ตรวจสอบความถูกต้องของข้อมูล
                            if exp_part and salary_part:
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
            return job_data
            
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการสกัดข้อมูลเงินเดือน: {str(e)}")
            return {}
    
    def save_to_json(self, data: Dict[str, Any]) -> bool:
        """
        บันทึกข้อมูลลงในไฟล์ JSON
        
        Args:
            data: ข้อมูลที่ต้องการบันทึก
            
        Returns:
            True ถ้าบันทึกสำเร็จ, False ถ้าไม่สำเร็จ
        """
        try:
            logger.info(f"กำลังบันทึกข้อมูลลงในไฟล์ {self.json_file_path}")
            
            with open(self.json_file_path, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
            
            logger.info("บันทึกข้อมูลลงในไฟล์ JSON สำเร็จ")
            return True
            
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการบันทึกข้อมูลลงในไฟล์ JSON: {str(e)}")
            return False
    
    def create_summary_file(self, data: Dict[str, Any]) -> bool:
        """
        สร้างไฟล์สรุปข้อมูลเงินเดือน
        
        Args:
            data: ข้อมูลที่ต้องการสรุป
            
        Returns:
            True ถ้าสร้างสำเร็จ, False ถ้าไม่สำเร็จ
        """
        try:
            summary_path = os.path.join(self.output_folder, "salary_summary.md")
            logger.info(f"กำลังสร้างไฟล์สรุป {summary_path}")
            
            with open(summary_path, "w", encoding="utf-8") as file:
                file.write("# สรุปข้อมูลเงินเดือนในสาขา IT\n\n")
                file.write(f"ข้อมูลจาก: [{self.base_url}]({self.base_url})\n\n")
                file.write(f"จำนวนตำแหน่งงานทั้งหมด: {len(data)}\n\n")
                
                for job_title, job_info in data.items():
                    file.write(f"## {job_title}\n\n")
                    
                    if job_info["skills"]:
                        file.write(f"**ทักษะที่ต้องการ:** {job_info['skills']}\n\n")
                    
                    file.write("**ช่วงเงินเดือน:**\n\n")
                    
                    for salary_info in job_info["salary"]:
                        file.write(f"- {salary_info['experience']}: {salary_info['salary']}\n")
                    
                    file.write("\n---\n\n")
            
            logger.info("สร้างไฟล์สรุปสำเร็จ")
            return True
            
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการสร้างไฟล์สรุป: {str(e)}")
            return False
    
    def scrape(self) -> Dict[str, Any]:
        """
        ดึงข้อมูลเงินเดือนทั้งหมด
        
        Returns:
            ผลลัพธ์การดึงข้อมูล
        """
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
        json_result = self.save_to_json(salary_data)
        
        # สร้างไฟล์สรุป
        summary_result = self.create_summary_file(salary_data)
        
        return {
            "success": json_result and summary_result,
            "jobs_count": len(salary_data),
            "json_file": self.json_file_path,
            "json_saved": json_result,
            "summary_saved": summary_result
        }


def main():
    """
    ฟังก์ชันหลักสำหรับการดึงข้อมูลเงินเดือน
    """
    scraper = ISMTechSalaryScraper()
    result = scraper.scrape()
    
    print("\nISM Tech Salary Scraping Summary:")
    print(f"- จำนวนตำแหน่งงานที่พบ: {result['jobs_count']}")
    print(f"- บันทึกไฟล์ JSON: {'✓' if result.get('json_saved', False) else '✗'}")
    print(f"- บันทึกไฟล์สรุป: {'✓' if result.get('summary_saved', False) else '✗'}")
    
    if result["success"]:
        print(f"- ไฟล์ JSON: {result.get('json_file', '')}")
        print("- สถานะโดยรวม: สำเร็จ ✓")
    else:
        print(f"- ข้อผิดพลาด: {result.get('error', 'ไม่ทราบสาเหตุ')}")
        print("- สถานะโดยรวม: ไม่สำเร็จ ✗")


if __name__ == "__main__":
    main()