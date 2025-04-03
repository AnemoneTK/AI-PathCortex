# backend/src/data_collection/jobsdb_scraper.py

import os
import requests
import logging
from bs4 import BeautifulSoup
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import re

# กำหนด logger สำหรับการบันทึกข้อมูล
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("src/logs/scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("jobsdb_scraper")

class JobsDBScraper:
    def __init__(self, output_folder="data/raw/jobsdb", max_workers=5):
      
        self.base_url = 'https://th.jobsdb.com/th/career-advice/role/{}'
        self.output_folder = output_folder
        self.max_workers = max_workers
        
        # สร้างโฟลเดอร์ output ถ้ายังไม่มี
        Path(self.output_folder).mkdir(parents=True, exist_ok=True)
        
        # คำที่ต้องการข้ามในการดึงข้อมูล (เช่น เมนูเว็บไซต์)
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

    def clean_text(self, text):
        # กรองส่วน "### ในหน้านี้" และส่วนที่ตามมา
        text = re.sub(r'### ในหน้านี้.*?(?=##|\Z)', '', text, flags=re.DOTALL)
        
        # กรองบรรทัดที่ขึ้นต้นด้วย • และตามด้วยคำที่ไม่ต้องการ
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line.startswith('•') or line.startswith('-'):
                skip = False
                for keyword in self.exclude_keywords:
                    if keyword.lower() in line.lower():
                        skip = True
                        break
                if skip:
                    continue
            cleaned_lines.append(line)
        
        # รวมบรรทัดที่ผ่านการกรอง
        return '\n'.join(cleaned_lines)
    
    def get_job_titles(self):
        """
        กำหนดรายการตำแหน่งงานที่ต้องการดึงข้อมูล
        
        Returns:
            รายการตำแหน่งงาน
        """
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
            'machine-learning-engineer',
            'cloud-engineer',
            'security-engineer',
            'database-administrator'
        ]
    
    def _scrape_single_page(self, job_title):
        """
        ดึงข้อมูลจากหน้าเว็บเพจเดียว
        
        Args:
            job_title: ตำแหน่งงานที่ต้องการดึงข้อมูล
            
        Returns:
            bool: สถานะความสำเร็จในการดึงข้อมูล
        """
        url = self.base_url.format(job_title)
        file_path = os.path.join(self.output_folder, f"{job_title}.txt")
        
        try:
            # ตรวจสอบว่าไฟล์มีอยู่แล้วหรือไม่
            if os.path.exists(file_path):
                logger.info(f"ข้อมูลสำหรับ {job_title} มีอยู่แล้ว ข้ามไป")
                return True
            
            response = requests.get(url, timeout=30)
            response.encoding = 'utf-8'  # ตั้งค่าการเข้ารหัสให้รองรับภาษาไทย
            
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
        """
        สกัดเนื้อหาจาก BeautifulSoup object
        
        Args:
            soup: BeautifulSoup object ที่มีข้อมูล HTML
            
        Returns:
            list: รายการข้อความที่สกัดได้
        """
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
                    scraped_data.append(f"• {text}")  # เพิ่ม bullet point สำหรับ <li> ใน <ul>
        
        # เก็บข้อมูลจาก <ol> โดยดึง <li> แต่ละอันมา
        for ol in ol_tags:
            for i, li in enumerate(ol.find_all('li'), 1):
                text = li.text.strip()
                if text and not any(exclude in text for exclude in self.exclude_keywords):
                    scraped_data.append(f"{i}. {text}")  # เพิ่มเลขลำดับสำหรับ <li> ใน <ol>
        
        # ดึงข้อมูลจาก <h1>, <h2>, <h3> สำหรับหัวข้อ
        h_tags = soup.find_all(['h1', 'h2', 'h3'])
        for h in h_tags:
            text = h.text.strip()
            if text and not any(exclude in text for exclude in self.exclude_keywords):
                tag_name = h.name
                prefix = "#" * int(tag_name[1])
                scraped_data.append(f"{prefix} {text}")
        
        return scraped_data
    
    def scrape_all_jobs(self):
        """
        ดึงข้อมูลสำหรับตำแหน่งงานทั้งหมด
        
        Returns:
            dict: สรุปผลการดึงข้อมูล
        """
        job_titles = self.get_job_titles()
        results = {
            "total": len(job_titles),
            "success": 0,
            "failed": 0,
            "failed_jobs": []
        }
        
        logger.info(f"เริ่มดึงข้อมูลสำหรับ {len(job_titles)} ตำแหน่งงาน")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._scrape_single_page, job): job for job in job_titles}
            
            for future in tqdm(as_completed(futures), total=len(futures), desc="Scraping Progress"):
                job = futures[future]
                try:
                    success = future.result()
                    if success:
                        results["success"] += 1
                    else:
                        results["failed"] += 1
                        results["failed_jobs"].append(job)
                except Exception as e:
                    results["failed"] += 1
                    results["failed_jobs"].append(job)
                    logger.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล {job}: {str(e)}")
        
        logger.info(f"ดึงข้อมูลสำเร็จ {results['success']} ตำแหน่ง, ล้มเหลว {results['failed']} ตำแหน่ง")
        
        # บันทึกผลการดึงข้อมูล
        summary_path = os.path.join(self.output_folder, "_scraping_summary.txt")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(f"Total job titles: {results['total']}\n")
            f.write(f"Successfully scraped: {results['success']}\n")
            f.write(f"Failed to scrape: {results['failed']}\n")
            if results["failed_jobs"]:
                f.write("Failed job titles:\n")
                for job in results["failed_jobs"]:
                    f.write(f"- {job}\n")
        
        return results


def main():
    """
    ฟังก์ชันหลักสำหรับการดึงข้อมูล
    """
    scraper = JobsDBScraper()
    results = scraper.scrape_all_jobs()
    
    print("\nScraping Summary:")
    print(f"Total job titles: {results['total']}")
    print(f"Successfully scraped: {results['success']}")
    print(f"Failed to scrape: {results['failed']}")
    if results["failed_jobs"]:
        print("Failed job titles:")
        for job in results["failed_jobs"]:
            print(f"- {job}")


if __name__ == "__main__":
    main()