import json
import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Any

# กำหนด logger สำหรับการบันทึกข้อมูล
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("src/logs/salary_extractor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("salary_extractor")

class SalaryExtractor:
    """
    คลาสสำหรับการแปลงข้อมูลเงินเดือนจาก JSON เป็นไฟล์ .txt
    """
    def __init__(self, 
                 json_file_path: str = 'data/raw/other_sources/it_salary_data.json', 
                 output_folder: str = 'data/raw/salary'):
        """
        เริ่มต้นการทำงานของ extractor
        
        Args:
            json_file_path: พาธของไฟล์ JSON ที่มีข้อมูลเงินเดือน
            output_folder: โฟลเดอร์สำหรับบันทึกไฟล์ .txt
        """
        self.json_file_path = json_file_path
        self.output_folder = output_folder
        
        # สร้างโฟลเดอร์ output ถ้ายังไม่มี
        Path(self.output_folder).mkdir(parents=True, exist_ok=True)
        
    def load_json_data(self) -> Dict[str, Any]:
        """
        โหลดข้อมูลจากไฟล์ JSON
        
        Returns:
            ข้อมูลจากไฟล์ JSON
        """
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"โหลดข้อมูลจาก {self.json_file_path} สำเร็จ")
                return data
        except FileNotFoundError:
            logger.error(f"ไม่พบไฟล์ {self.json_file_path}")
            return {}
        except json.JSONDecodeError:
            logger.error(f"ไฟล์ {self.json_file_path} ไม่ใช่ไฟล์ JSON ที่ถูกต้อง")
            return {}
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการโหลดไฟล์ {self.json_file_path}: {str(e)}")
            return {}
    
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
        # แทนที่ช่องว่างด้วยขีด
        sanitized = sanitized.replace(' ', '-')
        # แทนที่ขีดซ้ำซ้อนด้วยขีดเดียว
        sanitized = re.sub(r'-+', '-', sanitized)
        # แปลงเป็นตัวพิมพ์เล็กทั้งหมด
        sanitized = sanitized.lower()
        
        return sanitized
    
    def generate_txt_files(self) -> int:
        """
        สร้างไฟล์ .txt จากข้อมูล JSON
        
        Returns:
            จำนวนไฟล์ที่สร้างสำเร็จ
        """
        job_data_json = self.load_json_data()
        
        if not job_data_json:
            logger.warning("ไม่มีข้อมูลสำหรับการสร้างไฟล์ .txt")
            return 0
        
        success_count = 0
        
        for job_title, data in job_data_json.items():
            try:
                # ทำความสะอาดชื่อไฟล์
                safe_job_title = self.sanitize_filename(job_title)
                
                # ตั้งชื่อไฟล์
                file_path = os.path.join(self.output_folder, f"salary_{safe_job_title}.txt")
                
                # บันทึกข้อมูลลงในไฟล์ .txt
                with open(file_path, 'w', encoding='utf-8') as file:
                    # บันทึกชื่อของตำแหน่งงาน
                    file.write(f"Job Title: {job_title}\n\n")
                    
                    # บันทึก skills
                    if 'skills' in data and data['skills']:
                        file.write(f"Skills: {data['skills']}\n\n")
                    
                    # บันทึก salary
                    file.write("Salary:\n")
                    if 'salary' in data and isinstance(data['salary'], list):
                        for salary_info in data['salary']:
                            if isinstance(salary_info, dict) and 'experience' in salary_info and 'salary' in salary_info:
                                file.write(f"  - {salary_info['experience']} experience: {salary_info['salary']}\n")
                            else:
                                logger.warning(f"ข้อมูลเงินเดือนของ {job_title} ไม่อยู่ในรูปแบบที่ถูกต้อง")
                    else:
                        logger.warning(f"ไม่พบข้อมูลเงินเดือนสำหรับ {job_title}")
                
                logger.info(f"ข้อมูลสำหรับ {job_title} ถูกบันทึกที่: {file_path}")
                success_count += 1
                
            except Exception as e:
                logger.error(f"เกิดข้อผิดพลาดในการบันทึกข้อมูลสำหรับ {job_title}: {str(e)}")
        
        logger.info(f"สร้างไฟล์ .txt สำเร็จ {success_count} ไฟล์ จากทั้งหมด {len(job_data_json)} ตำแหน่งงาน")
        return success_count
    
    def create_summary_file(self) -> None:
        """
        สร้างไฟล์สรุปข้อมูลเงินเดือน
        """
        job_data_json = self.load_json_data()
        
        if not job_data_json:
            return
        
        try:
            summary_path = os.path.join(self.output_folder, "_salary_summary.txt")
            
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write("# สรุปข้อมูลเงินเดือนตำแหน่งงาน IT\n\n")
                
                for job_title, data in job_data_json.items():
                    f.write(f"## {job_title}\n")
                    
                    if 'skills' in data and data['skills']:
                        f.write(f"**ทักษะที่ต้องการ:** {data['skills']}\n\n")
                    
                    f.write("**ช่วงเงินเดือน:**\n")
                    if 'salary' in data and isinstance(data['salary'], list):
                        for salary_info in data['salary']:
                            if isinstance(salary_info, dict) and 'experience' in salary_info and 'salary' in salary_info:
                                f.write(f"- {salary_info['experience']} experience: {salary_info['salary']}\n")
                    
                    f.write("\n---\n\n")
                
            logger.info(f"สร้างไฟล์สรุป {summary_path} สำเร็จ")
            
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการสร้างไฟล์สรุป: {str(e)}")
    
    def extract_all(self) -> Dict[str, Any]:
        """
        ดำเนินการแปลงข้อมูลทั้งหมด
        
        Returns:
            ผลลัพธ์การดำเนินการ
        """
        files_created = self.generate_txt_files()
        self.create_summary_file()
        
        return {
            "success": files_created > 0,
            "files_created": files_created,
            "output_folder": self.output_folder
        }


def main():
    """
    ฟังก์ชันหลักสำหรับการแปลงข้อมูลเงินเดือน
    """
    extractor = SalaryExtractor()
    result = extractor.extract_all()
    
    print("\nSalary Extraction Summary:")
    print(f"- ไฟล์ที่สร้างสำเร็จ: {result['files_created']}")
    print(f"- บันทึกไว้ที่: {result['output_folder']}")
    print(f"- สถานะโดยรวม: {'สำเร็จ' if result['success'] else 'ไม่สำเร็จ'}")


if __name__ == "__main__":
    main()