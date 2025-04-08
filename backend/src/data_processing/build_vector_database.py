import os
import sys
import argparse
from pathlib import Path
from colorama import init, Fore, Style

# เริ่มต้นใช้งาน colorama
init(autoreset=True)

# เพิ่มโฟลเดอร์ปัจจุบันเข้าไปใน PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))  # ขึ้นไป 3 ระดับ
sys.path.append(project_root)

try:
    from backend.src.utils.vector_creator import VectorCreator
    print(f"{Fore.GREEN}✅ นำเข้าโมดูล VectorCreator สำเร็จ{Style.RESET_ALL}")
except ImportError as e:
    print(f"{Fore.RED}❌ ไม่สามารถนำเข้าโมดูล VectorCreator: {str(e)}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}ℹ️ ตรวจสอบว่า PYTHONPATH ได้รับการตั้งค่าอย่างถูกต้อง และมีไฟล์ src/utils/vector_creator.py{Style.RESET_ALL}")
    sys.exit(1)

def main():
    # ตั้งค่า argument parser
    parser = argparse.ArgumentParser(description='สร้าง vector database จากข้อมูลที่เตรียมไว้')
    parser.add_argument('--processed-data-dir', type=str, help='โฟลเดอร์ข้อมูลที่ประมวลผลแล้ว')
    parser.add_argument('--vector-db-dir', type=str, help='โฟลเดอร์สำหรับเก็บฐานข้อมูล vector')
    parser.add_argument('--model', type=str, default='intfloat/multilingual-e5-large', 
                        help='ชื่อโมเดล SentenceTransformer ที่ต้องการใช้')
    parser.add_argument('--no-clear', action='store_true', 
                        help='ไม่ล้างฐานข้อมูล vector เดิมก่อนสร้างใหม่')
    
    args = parser.parse_args()
    
    # กำหนดตำแหน่งโฟลเดอร์จาก arguments หรือใช้ค่าเริ่มต้น
    processed_data_dir = args.processed_data_dir if args.processed_data_dir else os.path.join(project_root,"backend", "data", "processed")
    vector_db_dir = args.vector_db_dir if args.vector_db_dir else os.path.join(project_root,"backend", "data", "vector_db")
    
    print(f"\n{Fore.CYAN}{'='*50}")
    print(f"{Fore.CYAN}= เริ่มต้นการสร้าง Vector Database ={Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*50}\n")
    
    print(f"{Fore.CYAN}📂 โฟลเดอร์ข้อมูลที่ประมวลผลแล้ว: {processed_data_dir}")
    print(f"{Fore.CYAN}📂 โฟลเดอร์สำหรับเก็บฐานข้อมูล vector: {vector_db_dir}")
    print(f"{Fore.CYAN}🔄 โมเดล SentenceTransformer: {args.model}")
    print(f"{Fore.CYAN}🔄 ล้างฐานข้อมูลเดิม: {'ไม่' if args.no_clear else 'ใช่'}{Style.RESET_ALL}\n")
    
    # สร้างโฟลเดอร์ถ้ายังไม่มี
    os.makedirs(vector_db_dir, exist_ok=True)
    
    # โหลดโมเดล SentenceTransformer
    try:
        print(f"{Fore.CYAN}🔄 กำลังโหลดโมเดล SentenceTransformer...{Style.RESET_ALL}")
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(args.model)
        print(f"{Fore.GREEN}✅ โหลดโมเดล {args.model} สำเร็จ{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}❌ เกิดข้อผิดพลาดในการโหลดโมเดล: {str(e)}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}ℹ️ จะใช้การจำลอง vector แทน{Style.RESET_ALL}")
        model = None
    
    # สร้าง VectorCreator
    try:
        vector_creator = VectorCreator(
            processed_data_dir=processed_data_dir,
            vector_db_dir=vector_db_dir,
            embedding_model=model,
            clear_vector_db=not args.no_clear
        )
        
        # สร้าง embeddings ทั้งหมด
        results = vector_creator.create_all_embeddings()
        
        # ทดสอบการค้นหา
        if results["job_embeddings"]["success"]:
            print(f"\n{Fore.CYAN}{'='*20} ทดสอบการค้นหาอาชีพ {'='*20}{Style.RESET_ALL}")
            test_queries = ["นักพัฒนาซอฟต์แวร์", "data scientist", "ผู้จัดการโครงการ","รายได้ fullstack","fullstack คืออะไร เงินเดือนเท่าไหร่ และต้องเตรียมตัวยังไง"]
            for query in test_queries:
                print(f"\n{Fore.CYAN}🔍 ทดสอบค้นหา: \"{query}\"{Style.RESET_ALL}")
                vector_creator.search_similar_jobs(query, k=3)
        
        if results["advice_embeddings"]["success"]:
            print(f"\n{Fore.CYAN}{'='*20} ทดสอบการค้นหาคำแนะนำอาชีพ {'='*20}{Style.RESET_ALL}")
            test_queries = ["วิธีการทำ resume ให้โดดเด่น", "การเตรียมตัวสัมภาษณ์งาน", "การพัฒนาทักษะในการทำงาน"]
            for query in test_queries:
                print(f"\n{Fore.CYAN}🔍 ทดสอบค้นหา: \"{query}\"{Style.RESET_ALL}")
                vector_creator.search_relevant_advices(query, k=3)
        
        # สรุปผล
        print(f"\n{Fore.CYAN}{'='*20} สรุปผลการสร้าง Vector Database {'='*20}{Style.RESET_ALL}")
        if results["job_embeddings"]["success"] and results["advice_embeddings"]["success"]:
            print(f"{Fore.GREEN}✅ สร้าง Vector Database สำเร็จทั้งหมด{Style.RESET_ALL}")
            print(f"  - ข้อมูลอาชีพ: {results['job_embeddings']['vectors_count']} vectors")
            print(f"  - ข้อมูลคำแนะนำอาชีพ: {results['advice_embeddings']['vectors_count']} vectors")
        else:
            print(f"{Fore.YELLOW}⚠️ สร้าง Vector Database สำเร็จบางส่วน{Style.RESET_ALL}")
            if results["job_embeddings"]["success"]:
                print(f"{Fore.GREEN}✅ ข้อมูลอาชีพ: {results['job_embeddings']['vectors_count']} vectors{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}❌ ข้อมูลอาชีพ: ไม่สำเร็จ - {results['job_embeddings'].get('error', 'ไม่ทราบสาเหตุ')}{Style.RESET_ALL}")
            
            if results["advice_embeddings"]["success"]:
                print(f"{Fore.GREEN}✅ ข้อมูลคำแนะนำอาชีพ: {results['advice_embeddings']['vectors_count']} vectors{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}❌ ข้อมูลคำแนะนำอาชีพ: ไม่สำเร็จ - {results['advice_embeddings'].get('error', 'ไม่ทราบสาเหตุ')}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}❌ เกิดข้อผิดพลาดในการสร้าง Vector Database: {str(e)}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()