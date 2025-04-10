#!/bin/bash

# รันแอปพลิเคชัน
uvicorn src.api.app:app --host 0.0.0.0 --port 8000

# รันคำสั่งประมวลผลข้อมูล
python -m src.run_data_processing --verbose --skip-collection