# backend/src/data_processing/prepare_embedding_data.py
import os
import json
import glob
from pathlib import Path
from tqdm import tqdm
import argparse
from colorama import init, Fore, Style

# เริ่มต้นใช้งาน colorama สำหรับแสดงสีในเทอร์มินัล
init(autoreset=True)

def prepare_jobs_data(cleaned_jobs_dir, output_file):
    """เตรียมข้อมูลอาชีพสำหรับการสร้าง embeddings"""
    all_jobs = []
    job_files = glob.glob(os.path.join(cleaned_jobs_dir, "*.json"))
    
    print(f"{Fore.CYAN}📂 พบไฟล์อาชีพทั้งหมด {len(job_files)} ไฟล์{Style.RESET_ALL}")
    
    for job_file in tqdm(job_files, desc="เตรียมข้อมูลอาชีพ"):
        try:
            with open(job_file, 'r', encoding='utf-8') as f:
                job_data = json.load(f)
            
            # สร้างข้อความสำหรับทำ embedding
            text_to_embed = ""
            
            # เพิ่มชื่ออาชีพ
            if "titles" in job_data and job_data["titles"]:
                text_to_embed += "ชื่ออาชีพ: " + ", ".join(job_data["titles"]) + "\n\n"
            
            # เพิ่มคำอธิบาย
            if "description" in job_data and job_data["description"]:
                text_to_embed += "คำอธิบาย: " + job_data["description"] + "\n\n"
            
            # เพิ่มความรับผิดชอบ
            if "responsibilities" in job_data and job_data["responsibilities"]:
                text_to_embed += "ความรับผิดชอบ:\n"
                for resp in job_data["responsibilities"]:
                    text_to_embed += f"- {resp}\n"
                text_to_embed += "\n"
            
            # เพิ่มทักษะ
            if "skills" in job_data and job_data["skills"]:
                text_to_embed += "ทักษะที่ต้องการ:\n"
                for skill in job_data["skills"]:
                    text_to_embed += f"- {skill}\n"
                text_to_embed += "\n"
            
            # เพิ่มช่วงเงินเดือน
            if "salary_ranges" in job_data and job_data["salary_ranges"]:
                text_to_embed += "ช่วงเงินเดือน:\n"
                for salary_range in job_data["salary_ranges"]:
                    text_to_embed += f"- ประสบการณ์ {salary_range.get('experience', 'N/A')} ปี: {salary_range.get('salary', 'N/A')} บาท\n"
            
            # เตรียมข้อมูลสำหรับ vector database
            embedding_item = {
                "id": job_data["id"],
                "text": text_to_embed,
                "metadata": {
                    "titles": job_data.get("titles", []),
                    "skills": job_data.get("skills", []),
                    "salary_ranges": job_data.get("salary_ranges", []),
                    "file_path": os.path.basename(job_file)
                }
            }
            
            all_jobs.append(embedding_item)
        except Exception as e:
            print(f"{Fore.RED}❌ เกิดข้อผิดพลาดในการอ่านไฟล์ {job_file}: {str(e)}{Style.RESET_ALL}")
    
    # บันทึกข้อมูลที่เตรียมไว้
    try:
        # สร้างโฟลเดอร์หากยังไม่มี
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_jobs, f, ensure_ascii=False, indent=2)
        
        print(f"{Fore.GREEN}✅ บันทึกข้อมูลสำหรับสร้าง embeddings แล้ว: {len(all_jobs)} รายการ -> {output_file}{Style.RESET_ALL}")
        return True
    except Exception as e:
        print(f"{Fore.RED}❌ เกิดข้อผิดพลาดในการบันทึกไฟล์ {output_file}: {str(e)}{Style.RESET_ALL}")
        return False

def prepare_advices_data(advice_file, output_file):
    """เตรียมข้อมูลคำแนะนำอาชีพสำหรับการสร้าง embeddings"""
    # ตรวจสอบว่าไฟล์มีอยู่จริง
    if not os.path.exists(advice_file):
        print(f"{Fore.RED}❌ ไม่พบไฟล์ข้อมูลคำแนะนำ: {advice_file}{Style.RESET_ALL}")
        return False
    
    # อ่านข้อมูลคำแนะนำ
    try:
        # สร้างโฟลเดอร์หากยังไม่มี
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(advice_file, 'r', encoding='utf-8') as f:
            advice_data = json.load(f)
        
        # ตรวจสอบโครงสร้างข้อมูล
        if "career_advices" not in advice_data:
            print(f"{Fore.YELLOW}⚠️ ไม่พบข้อมูล 'career_advices' ในไฟล์ {advice_file}{Style.RESET_ALL}")
            # ลองตรวจสอบว่าข้อมูลเป็น list โดยตรงหรือไม่
            if isinstance(advice_data, list):
                advices = advice_data
            else:
                print(f"{Fore.RED}❌ รูปแบบข้อมูลไม่ถูกต้อง{Style.RESET_ALL}")
                return False
        else:
            advices = advice_data["career_advices"]
        
        print(f"{Fore.CYAN}📂 พบคำแนะนำทั้งหมด {len(advices)} รายการ{Style.RESET_ALL}")
        
        # เตรียมข้อมูลสำหรับ embedding
        embedding_advices = []
        for advice in advices:
            # ใช้ข้อความที่มีประโยชน์สำหรับทำ embedding
            text_to_embed = ""
            
            # เพิ่มชื่อบทความ
            if "title" in advice:
                text_to_embed += f"หัวข้อ: {advice['title']}\n\n"
            
            # เพิ่มเนื้อหา
            if "content" in advice:
                text_to_embed += f"เนื้อหา: {advice['content'][:1000]}...\n\n"  # จำกัดความยาวเพื่อประสิทธิภาพ
            
            # เพิ่มแท็ก
            if "tags" in advice:
                text_to_embed += f"แท็ก: {', '.join(advice['tags'])}\n"
            
            # เตรียมข้อมูลสำหรับ vector database
            embedding_item = {
                "id": advice.get("id", ""),
                "text": text_to_embed,
                "metadata": {
                    "title": advice.get("title", ""),
                    "source": advice.get("source", ""),
                    "url": advice.get("url", ""),
                    "tags": advice.get("tags", [])
                }
            }
            
            embedding_advices.append(embedding_item)
        
        # บันทึกไฟล์ embedding
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(embedding_advices, f, ensure_ascii=False, indent=2)
        
        print(f"{Fore.GREEN}✅ บันทึกข้อมูลคำแนะนำสำหรับสร้าง embeddings แล้ว: {len(embedding_advices)} รายการ -> {output_file}{Style.RESET_ALL}")
        return True
    except Exception as e:
        print(f"{Fore.RED}❌ เกิดข้อผิดพลาดในการประมวลผลข้อมูลคำแนะนำ: {str(e)}{Style.RESET_ALL}")
        return False

def main():
    # ตั้งค่า argument parser
    parser = argparse.ArgumentParser(description='เตรียมข้อมูลสำหรับการสร้าง embeddings')
    parser.add_argument('--cleaned-jobs-dir', type=str, help='โฟลเดอร์ข้อมูลอาชีพที่ทำความสะอาดแล้ว')
    parser.add_argument('--advices-file', type=str, help='ไฟล์ข้อมูลคำแนะนำอาชีพ')
    parser.add_argument('--output-dir', type=str, help='โฟลเดอร์สำหรับเก็บผลลัพธ์')
    
    args = parser.parse_args()
    
    # กำหนดตำแหน่งไฟล์จาก arguments หรือใช้ค่าเริ่มต้น
    project_root = Path(__file__).parents[3]  # ย้อนกลับไป 3 ระดับจากไฟล์ปัจจุบัน
    processed_data_dir = project_root / "app" / "data"

    # โฟลเดอร์สำหรับเก็บข้อมูล embeddings
    embedding_dir = processed_data_dir / "embedding"
    os.makedirs(embedding_dir, exist_ok=True)  # สร้างโฟลเดอร์ถ้ายังไม่มี

    # ตำแหน่งไฟล์นำเข้า
    cleaned_jobs_dir = args.cleaned_jobs_dir if args.cleaned_jobs_dir else processed_data_dir / "processed" / "normalized_jobs"
    advices_file = args.advices_file if args.advices_file else processed_data_dir / "processed" / "career_advices" / "career_advices.json"

    # ตำแหน่งไฟล์ผลลัพธ์
    embedding_data_file = embedding_dir / "embedding_data.json"
    advices_output_file = embedding_dir / "career_advices_embeddings.json"  # แก้ไขชื่อไฟล์
    
    print(f"\n{Fore.CYAN}{'='*50}")
    print(f"{Fore.CYAN}= เริ่มต้นการเตรียมข้อมูลสำหรับสร้าง Embeddings ={Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*50}\n")
    
    print(f"{Fore.CYAN}📂 โฟลเดอร์ข้อมูลอาชีพ: {cleaned_jobs_dir}")
    print(f"{Fore.CYAN}📂 ไฟล์ข้อมูลคำแนะนำ: {advices_file}")
    print(f"{Fore.CYAN}📂 ไฟล์ผลลัพธ์สำหรับข้อมูล embedding: {embedding_data_file}")
    print(f"{Fore.CYAN}📂 ไฟล์ผลลัพธ์สำหรับข้อมูลคำแนะนำ: {advices_output_file}{Style.RESET_ALL}\n")
    
    # ตรวจสอบว่าโฟลเดอร์และไฟล์มีอยู่จริง
    if not os.path.exists(cleaned_jobs_dir):
        print(f"{Fore.RED}❌ ไม่พบโฟลเดอร์ข้อมูลอาชีพ: {cleaned_jobs_dir}{Style.RESET_ALL}")
        return
    
    # เตรียมข้อมูลอาชีพ
    print(f"\n{Fore.CYAN}{'='*20} เตรียมข้อมูลอาชีพ {'='*20}{Style.RESET_ALL}")
    jobs_success = prepare_jobs_data(cleaned_jobs_dir, embedding_data_file)
    
    # เตรียมข้อมูลคำแนะนำ
    print(f"\n{Fore.CYAN}{'='*20} เตรียมข้อมูลคำแนะนำอาชีพ {'='*20}{Style.RESET_ALL}")
    advices_success = prepare_advices_data(advices_file, advices_output_file)
    
    # สรุปผล
    print(f"\n{Fore.CYAN}{'='*20} สรุปผล {'='*20}{Style.RESET_ALL}")
    if jobs_success:
        print(f"{Fore.GREEN}✅ เตรียมข้อมูลอาชีพสำเร็จ{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}❌ เตรียมข้อมูลอาชีพไม่สำเร็จ{Style.RESET_ALL}")
    
    if advices_success:
        print(f"{Fore.GREEN}✅ เตรียมข้อมูลคำแนะนำอาชีพสำเร็จ{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}❌ เตรียมข้อมูลคำแนะนำอาชีพไม่สำเร็จ{Style.RESET_ALL}")
    
    if jobs_success and advices_success:
        print(f"\n{Fore.GREEN}✅ เตรียมข้อมูลสำหรับสร้าง embeddings เสร็จสิ้น{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.YELLOW}⚠️ เตรียมข้อมูลบางส่วนไม่สำเร็จ กรุณาตรวจสอบข้อผิดพลาดข้างต้น{Style.RESET_ALL}")

if __name__ == "__main__":
    main()