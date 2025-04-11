#!/usr/bin/env python3
# save as test_data_pipeline.py

import os
import shutil
import subprocess
import time

# คำสั่งลบโฟลเดอร์ data ทั้งหมด
def clean_data_folders():
    data_path = "/app/data"
    for subdir in ["raw", "processed", "embedding", "vector_db"]:
        target_dir = os.path.join(data_path, subdir)
        if os.path.exists(target_dir):
            print(f"กำลังลบ {target_dir}...")
            shutil.rmtree(target_dir)
            os.makedirs(target_dir, exist_ok=True)
    print("ลบและสร้างโฟลเดอร์ใหม่เรียบร้อย")

# รันกระบวนการเก็บข้อมูลและสร้าง vector database
def run_data_processing():
    cmd = ["python", "-m", "src.run_data_processing", "--verbose"]
    print(f"กำลังรัน: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("ข้อผิดพลาด:")
        print(result.stderr)
    return result.returncode

# รันกระบวนการทั้งหมด
def main():
    print("เริ่มต้นทดสอบ pipeline ข้อมูล")
    clean_data_folders()
    time.sleep(2)  # รอให้ระบบไฟล์พร้อม
    return_code = run_data_processing()
    if return_code == 0:
        print("กระบวนการทำงานเสร็จสิ้นสมบูรณ์")
    else:
        print(f"กระบวนการทำงานเสร็จสิ้นแต่มีข้อผิดพลาด (return code: {return_code})")

if __name__ == "__main__":
    main()