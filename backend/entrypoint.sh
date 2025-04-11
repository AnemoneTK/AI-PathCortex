#!/bin/bash

# ตรวจสอบและสร้างโฟลเดอร์ที่จำเป็น
DATA_PATH=${APP_PATH:-/app/data}
echo "Using DATA_PATH: $DATA_PATH"

# รายการโฟลเดอร์ที่ต้องมี
folders=(
  "$DATA_PATH/data"
  "$DATA_PATH/data/raw"
  "$DATA_PATH/data/raw/jobsdb"
  "$DATA_PATH/data/raw/other_sources"
  "$DATA_PATH/data/processed"
  "$DATA_PATH/data/processed/normalized_jobs"
  "$DATA_PATH/data/processed/cleaned_jobs"
  "$DATA_PATH/data/processed/career_advices"
  "$DATA_PATH/data/embedding"
  "$DATA_PATH/data/vector_db"
  "$DATA_PATH/data/vector_db/job_knowledge"
  "$DATA_PATH/data/vector_db/career_advice"
  "$DATA_PATH/data/vector_db/combined_knowledge"
  "$DATA_PATH/data/fine_tune"
  "$DATA_PATH/data/logs"
  "$DATA_PATH/data/uploads"
  "$DATA_PATH/data/users"
)

# สร้างโฟลเดอร์ที่ยังไม่มี
for folder in "${folders[@]}"; do
  mkdir -p "$folder"
  echo "Created folder: $folder"
done

# ตั้งค่าสิทธิ์การเข้าถึง
chmod -R 777 "$DATA_PATH"

# รันคำสั่งที่ส่งมา
exec "$@"