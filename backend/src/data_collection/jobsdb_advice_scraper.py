# backend/src/data_collection/jobsdb_advice_scraper.py
from bs4 import BeautifulSoup
import json
import os
import requests
from pathlib import Path
import time
import random
from colorama import init, Fore, Style, Back
import datetime

# เริ่มต้นใช้งาน colorama
init(autoreset=True)

class SimpleArticleScraper:
    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.advices = []
        self.start_time = datetime.datetime.now()
        self.successful_count = 0
        self.failed_count = 0
        
        # แสดงข้อความเริ่มต้น
        print(f"{Fore.CYAN}{Style.BRIGHT}=== ระบบเก็บข้อมูลบทความแนะนำอาชีพ ==={Style.RESET_ALL}")
        print(f"{Fore.CYAN}เริ่มต้นเวลา: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{Fore.CYAN}ไดเรกทอรีเก็บข้อมูล: {self.output_dir.absolute()}\n")
        
        # ถ้ามีไฟล์ข้อมูลอยู่แล้ว ให้โหลดมาก่อน
        self.advice_file = self.output_dir / "career_advices.json"
        if self.advice_file.exists():
            with open(self.advice_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.advices = data.get("career_advices", [])
            print(f"{Fore.GREEN}โหลดข้อมูลเดิม: {len(self.advices)} บทความ")
        else:
            print(f"{Fore.YELLOW}ไม่พบไฟล์ข้อมูลเดิม จะสร้างไฟล์ใหม่")
        
        # HTTP Headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7'
        }
    
    def generate_id_from_url(self, url):
        """สร้าง ID จาก URL"""
        # ตัดส่วนท้ายของ URL มาใช้เป็น ID
        parts = url.split('/')
        last_part = parts[-1].split('?')[0]  # ตัด query parameters ออก
        return last_part
    
    def scrape_article(self, url):
        """ดึงข้อมูล h1 และ p จากบทความ"""
        try:
            print(f"{Fore.CYAN}[ดึงข้อมูล] กำลังดึงข้อมูลจาก {url}")
            
            # หน่วงเวลาเล็กน้อยเพื่อไม่ให้ส่งคำขอถี่เกินไป
            delay = random.uniform(0.5, 2.0)
            print(f"{Fore.CYAN}[รอ] หน่วงเวลา {delay:.2f} วินาที...")
            time.sleep(delay)
            
            # ส่งคำขอ
            print(f"{Fore.CYAN}[HTTP] กำลังส่งคำขอ...")
            response = requests.get(url, headers=self.headers)
            
            if response.status_code != 200:
                print(f"{Fore.RED}[ผิดพลาด] ไม่สามารถดึงบทความ: {url}")
                print(f"{Fore.RED}[ผิดพลาด] สถานะ HTTP: {response.status_code}")
                self.failed_count += 1
                return None
            
            print(f"{Fore.GREEN}[สำเร็จ] ได้รับการตอบกลับจากเซิร์ฟเวอร์")
            
            # แปลงเป็น BeautifulSoup
            print(f"{Fore.CYAN}[ประมวลผล] กำลังแปลงข้อมูล HTML...")
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # เก็บหัวข้อใหญ่ (H1)
            title_element = soup.select_one('h1')
            if not title_element:
                print(f"{Fore.RED}[ผิดพลาด] ไม่พบหัวข้อ (h1) ในบทความ")
                self.failed_count += 1
                return None
                
            title = title_element.text.strip()
            print(f"{Fore.GREEN}[พบ] หัวข้อบทความ: {title}")
            
            # เก็บเนื้อหาบทความเฉพาะ p
            print(f"{Fore.CYAN}[ประมวลผล] กำลังดึงย่อหน้า (p)...")
            paragraphs = soup.select('p')
            
            # แยกเนื้อหาเป็นรายย่อหน้า
            content_paragraphs = []
            filtered_out = 0
            for p in paragraphs:
                text = p.text.strip()
                if text:  # เก็บเฉพาะย่อหน้าที่มีข้อความ
                    # ตัดข้อความที่ไม่ต้องการออก
                    if "เรื่องอื่น ๆ ที่น่าสนใจ" not in text and "ปิดจุดด้อย เสริมจุดเด่น" not in text and "พฤติกรรมผู้สมัครงานที่ HR ไม่ปลื้ม" not in text:
                        content_paragraphs.append(text)
                    else:
                        filtered_out += 1
            
            print(f"{Fore.GREEN}[พบ] จำนวนย่อหน้า: {len(content_paragraphs)} (คัดกรองออก: {filtered_out})")
            
            # รวมเนื้อหาทั้งหมด
            full_content = "\n\n".join(content_paragraphs)
            
            # กำหนด tags ตามเนื้อหาของบทความ
            print(f"{Fore.CYAN}[ประมวลผล] กำลังวิเคราะห์แท็ก...")
            tags = ["คำแนะนำอาชีพ"]  # เริ่มต้นด้วยแท็กพื้นฐาน
            
            # เพิ่มแท็กตามเนื้อหา
            content_lower = full_content.lower() + " " + title.lower()
            
            # แท็กเกี่ยวกับการหางาน
            if any(keyword in content_lower for keyword in ["หางาน", "สมัครงาน", "ตลาดงาน", "ตำแหน่งงาน"]):
                tags.append("การหางาน")
            
            # แท็กเกี่ยวกับการสัมภาษณ์
            if any(keyword in content_lower for keyword in ["สัมภาษณ์", "interview", "คำถามสัมภาษณ์", "ตอบคำถาม"]):
                tags.append("การสัมภาษณ์งาน")
            
            # แท็กเกี่ยวกับ resume
            if any(keyword in content_lower for keyword in ["เรซูเม่", "resume", "cv", "ประวัติส่วนตัว", "portfolio", "โปรไฟล์"]):
                tags.append("การเขียน Resume")
            
            # แท็กเกี่ยวกับการพัฒนาตนเอง
            if any(keyword in content_lower for keyword in ["พัฒนาตนเอง", "พัฒนาทักษะ", "เพิ่มศักยภาพ", "upskill", "reskill", "เพิ่มทักษะ"]):
                tags.append("การพัฒนาตัวเอง")
            
            # แท็กเกี่ยวกับเทคนิคการทำงาน
            if any(keyword in content_lower for keyword in ["เทคนิค", "วิธีการ", "ทริค", "เคล็ดลับ", "tips", "how to"]):
                tags.append("เทคนิคและเคล็ดลับ")
            
            # แท็กเกี่ยวกับการวางแผนอาชีพ
            if any(keyword in content_lower for keyword in ["วางแผนอาชีพ", "เส้นทางอาชีพ", "career path", "เปลี่ยนสายงาน", "career planning"]):
                tags.append("การวางแผนอาชีพ")
            
            # ตัดแท็กซ้ำ
            tags = list(set(tags))
            print(f"{Fore.GREEN}[พบ] แท็ก: {', '.join(tags)}")
            
            # สร้าง ID จาก URL
            article_id = self.generate_id_from_url(url)
            print(f"{Fore.GREEN}[กำหนด] ID บทความ: {article_id}")
            
            # สร้างโครงสร้างข้อมูล
            article_data = {
                "id": article_id,
                "title": title,
                "source": url.split('/')[2],  # เช่น th.jobsdb.com
                "url": url,
                "content": full_content,
                "paragraphs": content_paragraphs,
                "tags": tags
            }
            
            self.successful_count += 1
            print(f"{Fore.GREEN}[สำเร็จ] ดึงข้อมูลบทความเรียบร้อย")
            return article_data
            
        except Exception as e:
            print(f"{Fore.RED}[ข้อผิดพลาด] เกิดข้อผิดพลาดในการดึงบทความ: {url}")
            print(f"{Fore.RED}[ข้อผิดพลาด] รายละเอียด: {str(e)}")
            self.failed_count += 1
            return None
    
    def save_article(self, article_data):
        """บันทึกข้อมูลบทความ"""
        if not article_data:
            return False
            
        print(f"{Fore.CYAN}[บันทึก] กำลังบันทึกบทความ '{article_data['title']}'...")
            
        # ตรวจสอบว่ามีบทความนี้อยู่แล้วหรือไม่
        existing_index = None
        for i, advice in enumerate(self.advices):
            if advice.get("id") == article_data["id"] or advice.get("url") == article_data["url"]:
                existing_index = i
                break
        
        if existing_index is not None:
            # อัปเดตข้อมูลที่มีอยู่
            print(f"{Fore.YELLOW}[อัปเดต] พบบทความนี้ในระบบแล้ว จะทำการอัปเดต")
            self.advices[existing_index] = article_data
        else:
            # เพิ่มข้อมูลใหม่
            print(f"{Fore.GREEN}[เพิ่ม] เพิ่มบทความใหม่ลงในระบบ")
            self.advices.append(article_data)
        
        # บันทึกลงไฟล์
        try:
            with open(self.advice_file, 'w', encoding='utf-8') as f:
                json.dump({"career_advices": self.advices}, f, ensure_ascii=False, indent=2)
            print(f"{Fore.GREEN}[สำเร็จ] บันทึกบทความ '{article_data['title']}' เรียบร้อยแล้ว")
            return True
        except Exception as e:
            print(f"{Fore.RED}[ข้อผิดพลาด] ไม่สามารถบันทึกข้อมูลได้: {str(e)}")
            return False
    
    def print_summary(self):
        """แสดงสรุปผลการทำงาน"""
        end_time = datetime.datetime.now()
        duration = end_time - self.start_time
        
        print(f"\n{Fore.CYAN}{Style.BRIGHT}=== สรุปผลการทำงาน ==={Style.RESET_ALL}")
        print(f"{Fore.CYAN}เวลาเริ่มต้น: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{Fore.CYAN}เวลาสิ้นสุด: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{Fore.CYAN}ใช้เวลาทั้งหมด: {duration}")
        print(f"{Fore.GREEN}บทความที่ดึงสำเร็จ: {self.successful_count}")
        print(f"{Fore.RED}บทความที่ดึงไม่สำเร็จ: {self.failed_count}")
        print(f"{Fore.GREEN}จำนวนบทความทั้งหมดในระบบ: {len(self.advices)}")
        print(f"{Fore.CYAN}ไฟล์ข้อมูล: {self.advice_file.absolute()}")
        print(f"{Fore.CYAN}{Style.BRIGHT}=============================={Style.RESET_ALL}")

    def scrape(self):
        """เรียกใช้งานฟังก์ชัน main ภายในคลาส"""
        print(f"{Fore.CYAN}{Style.BRIGHT}=== เริ่มต้นการเก็บข้อมูลบทความแนะนำอาชีพ ==={Style.RESET_ALL}")
        
        # รายการชื่อบทความที่ต้องการเก็บข้อมูล
        article_slugs = [
            "โดดเด่นพอที่จะได้งาน",
            "ตอบคำถามสัมภาษณ์งาน-4",
            "differences-between-resume-and-portfolio",
            "ทำงานไม่ตรงสาย",
            "คุณสมบัติ-มัดใจนายจ้าง",
            "บริษัทเล็ก-vs-บริษัทใหญ่-2",
            "skillsต้องมีเพื่อตลาดงานai",
            "ลงทะเบียนว่างงาน",
            "คำถามที่จะทำให้คุณเด่น",
            "การเขียนจดหมายสมัครงาน-2",
            "จุดมุ่งหมายในอาชีพ",
            "ตัวอย่าง-เขียนเรซูเม่",
            "วิธีการเขียนเรซูเม่",
            "นัด-ไม่ไปสัมภาษณ์งาน",
            "เตรียม-ก่อนสัมภาษณ์งาน",
            "เรซูเม่ที่ไม่น่าอ่าน",
            "resume-vs-cv-2022",
            "เปลี่ยนสายงานไปสายไอที",
            "งานไอที-อาชีพสุดปัง",
            "ต่อรองเงินเดือนจบใหม่",
            "ai-tools",
            "แนะนำตัวสัมภาษณ์งาน",
            "เด็กจบใหม่สู่อาเซียน",
            "สมัครงานบริษัทเล็ก-ใหญ่",
            "ทักษะ-เด็กจบใหม่",
            "หลักสูตรเรซูเม่-จบใหม่",
            "freshgrad-first-job-hunt",
        ]
        
        def create_jobsdb_url(article_slug):
            """สร้าง URL เต็มจากส่วนท้ายของ URL"""
            return f"https://th.jobsdb.com/th/career-advice/article/{article_slug}"
        
        # สร้าง URL เต็ม
        urls = [create_jobsdb_url(slug) for slug in article_slugs]
        
        print(f"{Fore.CYAN}{Style.BRIGHT}=== เริ่มต้นดึงข้อมูล {len(urls)} บทความ ==={Style.RESET_ALL}")
        
        # ดึงข้อมูลจากแต่ละ URL
        for i, url in enumerate(urls):
            print(f"\n{Fore.CYAN}{Style.BRIGHT}=== บทความที่ {i+1}/{len(urls)} ==={Style.RESET_ALL}")
            article_data = self.scrape_article(url)
            if article_data:
                self.save_article(article_data)
            print(f"{Fore.CYAN}{'=' * 50}")
        
        # แสดงสรุปผลการทำงาน
        self.print_summary()
        return True

def main():
    # กำหนดไดเรกทอรีเก็บข้อมูล
    base_dir = Path(__file__).resolve().parent.parent.parent
    output_dir = base_dir / "data" / "processed" / "career_advices"
    
    # สร้างไดเรกทอรีถ้ายังไม่มี
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # สร้าง scraper
    scraper = SimpleArticleScraper(output_dir)
    
    def create_jobsdb_url(article_slug):
        """สร้าง URL เต็มจากส่วนท้ายของ URL"""
        return f"https://th.jobsdb.com/th/career-advice/article/{article_slug}"
    
    # รายการชื่อบทความที่ต้องการเก็บข้อมูล
    article_slugs = [
        "โดดเด่นพอที่จะได้งาน",
        "ตอบคำถามสัมภาษณ์งาน-4",
        "differences-between-resume-and-portfolio",
        "ทำงานไม่ตรงสาย",
        "คุณสมบัติ-มัดใจนายจ้าง",
        "บริษัทเล็ก-vs-บริษัทใหญ่-2",
        "skillsต้องมีเพื่อตลาดงานai",
        "ลงทะเบียนว่างงาน",
        "คำถามที่จะทำให้คุณเด่น",
        "การเขียนจดหมายสมัครงาน-2",
        "จุดมุ่งหมายในอาชีพ",
        "ตัวอย่าง-เขียนเรซูเม่",
        "วิธีการเขียนเรซูเม่",
        "นัด-ไม่ไปสัมภาษณ์งาน",
        "เตรียม-ก่อนสัมภาษณ์งาน",
        "เรซูเม่ที่ไม่น่าอ่าน",
        "resume-vs-cv-2022",
        "เปลี่ยนสายงานไปสายไอที",
        "งานไอที-อาชีพสุดปัง",
        "ต่อรองเงินเดือนจบใหม่",
        "ai-tools",
        "แนะนำตัวสัมภาษณ์งาน",
        "เด็กจบใหม่สู่อาเซียน",
        "สมัครงานบริษัทเล็ก-ใหญ่",
        "ทักษะ-เด็กจบใหม่",
        "หลักสูตรเรซูเม่-จบใหม่",
        "freshgrad-first-job-hunt",
    ]

    # สร้าง URL เต็ม
    urls = [create_jobsdb_url(slug) for slug in article_slugs]
    
    print(f"{Fore.CYAN}{Style.BRIGHT}=== เริ่มต้นดึงข้อมูล {len(urls)} บทความ ==={Style.RESET_ALL}")
    
    # ดึงข้อมูลจากแต่ละ URL
    for i, url in enumerate(urls):
        print(f"\n{Fore.CYAN}{Style.BRIGHT}=== บทความที่ {i+1}/{len(urls)} ==={Style.RESET_ALL}")
        article_data = scraper.scrape_article(url)
        if article_data:
            scraper.save_article(article_data)
        print(f"{Fore.CYAN}{'=' * 50}")
    
    # แสดงสรุปผลการทำงาน
    scraper.print_summary()
    
if __name__ == "__main__":
    main()