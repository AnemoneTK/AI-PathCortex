import os
import requests
import sys
import json
import re
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from tqdm import tqdm
import logging

# ตั้งค่าการบันทึกล็อก
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("jobsdb_scraper")

class JobDataProcessor:
    def __init__(self, 
                 txt_output_folder="data/raw/jobsdb", 
                 json_output_folder="data/raw/other_sources", 
                 max_workers=5):
        
        # ตั้งค่าพาธโฟลเดอร์
        self.txt_output_folder = Path(txt_output_folder)
        self.json_output_folder = Path(json_output_folder)
        
        # สร้างโฟลเดอร์หากยังไม่มี
        self.txt_output_folder.mkdir(parents=True, exist_ok=True)
        self.json_output_folder.mkdir(parents=True, exist_ok=True)
        
        self.base_url = 'https://th.jobsdb.com/th/career-advice/role/{}'
        self.max_workers = max_workers
        
        # คำที่ไม่ต้องการ
        self.exclude_keywords = {
            "ค้นหางาน", "โปรไฟล์", "งานแนะนำ", "บันทึกการค้นหา", "งานที่บันทึก", 
            "ประวัติการสมัครงาน", "ครบเครื่องเรื่องงาน", "สำรวจอาชีพ", "สำรวจเงินเดือน",
            "บริษัทที่น่าสนใจ", "ดาวน์โหลด", "app", "Jobsdb @ Google Play", "Jobsdb @ App Store",
            "ลงทะเบียนฟรี", "ลงประกาศงาน", "ผลิตภัณฑ์และราคา", "บริการลูกค้า",
            "คำแนะนำเกี่ยวกับการจ้างงาน", "ข้อมูลเชิงลึกของตลาด", "พันธมิตรซอฟต์แวร์", 
            "เกี่ยวกับเรา", "ห้องข่าว", "นักลงทุนสัมพันธ์", "ร่วมงานกับเรา", 
            "Bdjobs", "Jobstreet", "Jora", "SEEK", "GradConnection", "GO1", "FutureLearn", "JobAdder",
            "Sidekicker", "ศูนย์ความช่วยเหลือ", "ติดต่อเรา", "บล็อกผลิตภัณฑ์", "โซเชียล",
            "Facebook", "Instagram", "Twitter", "YouTube", "ในหน้านี้", "เลือกดูอาชีพที่ใกล้เคียง",
            "อ่านเพิ่มเติมจาก", "สมัครรับคำแนะนำ", "เปรียบเทียบเงินเดือน"
        }

    def get_job_titles(self):
        return [
            'programmer',
            'software-developer',
            'web-developer',
            'software-engineer',
            'systems-analyst',
            'applications-developer',
            'data-scientist',
            'ux--ui-designer',
            'full-stack-developer',
            'frontend-developer',
            'backend-developer',
            'webdesigner',
            'android-developer',
            'ios-developer',
            'devops-engineer',
            'information-technology-project-manager',
            'information-technology-engineer',
            'testing-engineer',
            'network-administrator',
            'data-analyst',
            'security-engineer',
            'database-administrator',
            'scrum-master',
            'project-manager',
            'support-engineer',
            'software-development-manager',
            'user-experience-designer'
        ]

    def scrape_to_txt(self):
        job_titles = self.get_job_titles()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._scrape_single_job, job_title): job_title for job_title in job_titles}
            
            results = {
                "total": len(job_titles),
                "success": 0,
                "failed": 0,
                "failed_jobs": []
            }
            
            for future in tqdm(as_completed(futures), total=len(futures), desc="กำลังดึงข้อมูล"):
                job_title = futures[future]
                try:
                    success = future.result()
                    if success:
                        results["success"] += 1
                    else:
                        results["failed"] += 1
                        results["failed_jobs"].append(job_title)
                except Exception as e:
                    results["failed"] += 1
                    results["failed_jobs"].append(job_title)
                    logger.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล {job_title}: {str(e)}")
        
        logger.info(f"ดึงข้อมูลสำเร็จ {results['success']} ตำแหน่ง, ล้มเหลว {results['failed']} ตำแหน่ง")
        return results

    def _scrape_single_job(self, job_title):
        url = self.base_url.format(job_title)
        file_path = self.txt_output_folder / f"{job_title}.txt"
        
        try:
            # ตรวจสอบว่าไฟล์มีอยู่แล้วหรือไม่
            if file_path.exists():
                logger.info(f"ข้อมูลสำหรับ {job_title} มีอยู่แล้ว ข้ามไป")
                return True
            
            response = requests.get(url, timeout=30)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                logger.error(f"ไม่สามารถเข้าถึง {url}, สถานะ: {response.status_code}")
                return False
            
            soup = BeautifulSoup(response.text, 'html.parser')
            scraped_data = self._extract_content(soup)
            
            if not scraped_data:
                logger.warning(f"ไม่พบข้อมูลสำหรับ {job_title}")
                return False
            
            # บันทึกข้อมูลลงในไฟล์
            with open(file_path, 'w', encoding='utf-8') as file:
                for paragraph in scraped_data:
                    file.write(paragraph + "\n\n")
            
            logger.info(f"ดึงข้อมูลสำหรับ {job_title} สำเร็จ")
            return True
            
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล {job_title}: {str(e)}")
            return False

    def _extract_content(self, soup):
        # ดึงข้อมูลจาก <p>, <ul>, <ol> และ <li>
        p_tags = soup.find_all('p')
        ul_tags = soup.find_all('ul')
        ol_tags = soup.find_all('ol')
        
        # เก็บข้อมูลที่ดึงมาจาก <p>
        scraped_data = [
            p.text.strip() for p in p_tags 
            if p.text.strip() and not any(exclude in p.text for exclude in self.exclude_keywords)
        ]
        
        # เก็บข้อมูลจาก <ul> โดยดึง <li> แต่ละอันมา
        for ul in ul_tags:
            for li in ul.find_all('li'):
                text = li.text.strip()
                if text and not any(exclude in text for exclude in self.exclude_keywords):
                    scraped_data.append(f"• {text}")
        
        # เก็บข้อมูลจาก <ol> โดยดึง <li> แต่ละอันมา
        for ol in ol_tags:
            for i, li in enumerate(ol.find_all('li'), 1):
                text = li.text.strip()
                if text and not any(exclude in text for exclude in self.exclude_keywords):
                    scraped_data.append(f"{i}. {text}")
        
        # ดึงข้อมูลจาก <h1>, <h2>, <h3> สำหรับหัวข้อ
        h_tags = soup.find_all(['h1', 'h2', 'h3'])
        for h in h_tags:
            text = h.text.strip()
            if text and not any(exclude in text for exclude in self.exclude_keywords):
                tag_name = h.name
                prefix = "#" * int(tag_name[1])
                scraped_data.append(f"{prefix} {text}")
        
        return scraped_data

    def convert_txt_to_json(self):
        # รายการไฟล์ .txt ในโฟลเดอร์
        txt_files = list(self.txt_output_folder.glob('*.txt'))
        
        if not txt_files:
            logger.warning(f"ไม่พบไฟล์ .txt ในโฟลเดอร์: {self.txt_output_folder}")
            return
        
        all_jobs_data = {}
        
        for filepath in tqdm(txt_files, desc="กำลังแปลงเป็น JSON"):
            try:
                # อ่านเนื้อหาไฟล์
                with open(filepath, "r", encoding="utf-8") as file:
                    content = file.read().strip()
                
                # ดึงชื่อตำแหน่งงานจากชื่อไฟล์
                job_title = filepath.stem.replace("-", " ").title()
                
                # สกัดข้อมูล
                description = self._extract_first_paragraph(content)
                responsibilities = self._extract_responsibilities(content)
                
                # สร้างข้อมูล JSON
                job_data = {
                    "title": job_title,
                    "description": description,
                    "responsibilities": responsibilities,
                    "source_file": filepath.name
                }
                
                all_jobs_data[job_title] = job_data
                
            except Exception as e:
                logger.error(f"ไม่สามารถประมวลผลไฟล์ {filepath}: {str(e)}")
        
        # บันทึก JSON
        output_path = self.json_output_folder / "jobs_data.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_jobs_data, f, ensure_ascii=False, indent=4)
        
        logger.info(f"บันทึกข้อมูล JSON สำเร็จ: {output_path}")

    def _extract_first_paragraph(self, content):
        paragraphs = content.split('\n\n')
        return paragraphs[0] if paragraphs else ""

    def _extract_responsibilities(self, content):
        # ค้นหารายการที่ขึ้นต้นด้วย • หรือ -
        bullet_points = re.findall(r"(?:^|\n)[•\-]\s*(.+?)(?=\n[•\-]|\n\n|\Z)", content, re.DOTALL)
        
        # กรองและทำความสะอาดข้อมูล
        return [
            point.strip() for point in bullet_points 
            if point.strip() and not any(kw in point for kw in self.exclude_keywords)
        ]

    def process(self):
        # ขั้นตอนที่ 1: ดึงข้อมูลและบันทึกเป็น .txt
        self.scrape_to_txt()
        
        # ขั้นตอนที่ 2: แปลง .txt เป็น JSON
        self.convert_txt_to_json()

def main():
    processor = JobDataProcessor()
    processor.process()

if __name__ == "__main__":
    main()