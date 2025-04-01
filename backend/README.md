# IT Career Advisor Data Pipeline

ระบบประมวลผลและเตรียมข้อมูลอาชีพด้าน IT สำหรับนำไปใช้ในแอปพลิเคชันให้คำแนะนำด้านอาชีพ

## 🌟 คุณสมบัติของระบบ

- ✅ รวบรวมข้อมูลอาชีพด้าน IT จากหลายแหล่งข้อมูล (JobsDB, Talance, ข้อมูลเงินเดือน)
- ✅ จัดกลุ่มและปรับมาตรฐานชื่อตำแหน่งงาน
- ✅ ประมวลผลเนื้อหาและสกัดส่วนสำคัญ (ความรับผิดชอบ, ทักษะ, ข้อมูลเงินเดือน)
- ✅ เปรียบเทียบและวิเคราะห์ความสัมพันธ์ระหว่างอาชีพต่างๆ
- ✅ สร้าง Vector Database สำหรับการค้นหาเชิงความหมาย (Semantic Search)
- ✅ API สำหรับเชื่อมต่อกับ Frontend

## 📂 โครงสร้างโปรเจค

```
backend/
├── data/
│   ├── raw/                       # ข้อมูลดิบจากแหล่งต่างๆ
│   │   ├── jobsdb/               # ข้อมูลจาก JobsDB
│   │   ├── salary/               # ข้อมูลเงินเดือน
│   │   └── talance/              # ข้อมูลจาก Talance
│   ├── processed/                 # ข้อมูลที่ผ่านการประมวลผลแล้ว
│   │   ├── enriched/             # ข้อมูลที่เพิ่มการวิเคราะห์เชิงลึก
│   │   ├── processed_jobs.json   # ข้อมูลรวมที่ประมวลผลแล้ว
│   │   └── embedding_data.json   # ข้อมูลสำหรับสร้าง embeddings
│   └── vector_db/                 # Vector Database สำหรับการค้นหา
├── src/
│   ├── data_collection/          # โค้ดสำหรับรวบรวมข้อมูล
│   │   └── enhanced_scraper.py   # ตัวดึงข้อมูลที่ปรับปรุงแล้ว
│   ├── data_processing/          # โค้ดสำหรับประมวลผลข้อมูล
│   │   ├── enhanced_normalizer.py # ตัวปรับมาตรฐานข้อมูล
│   │   └── enhanced_processor.py # ตัวประมวลผลข้อมูลขั้นสูง
│   ├── vector_db/                # โค้ดสำหรับ Vector Database
│   │   └── create_vector_db.py   # สร้าง Vector Database
│   ├── api/                      # โค้ดสำหรับ API
│   │   └── app.py                # FastAPI แอปพลิเคชัน
│   └── run_pipeline.py           # สคริปต์หลักสำหรับรันทั้งระบบ
├── requirements.txt              # แพ็คเกจที่จำเป็น
└── README.md                     # ไฟล์นี้
```

## 🚀 การติดตั้ง

1. สร้าง Virtual Environment และติดตั้งแพ็คเกจที่จำเป็น:

```bash
# สร้าง virtual environment
python -m venv venv

# เปิดใช้งาน virtual environment
# สำหรับ Windows
venv\Scripts\activate
# สำหรับ macOS/Linux
source venv/bin/activate

# ติดตั้งแพ็คเกจที่จำเป็น
pip install -r requirements.txt
```

## 📋 การใช้งาน

### 1. รันระบบเต็มรูปแบบ

เพื่อประมวลผลข้อมูลทั้งหมดในครั้งเดียว:

```bash
python src/run_pipeline.py --all
```

### 2. รันเฉพาะขั้นตอนที่ต้องการ

```bash
# รันเฉพาะขั้นตอนการรวบรวมข้อมูล
python src/run_pipeline.py --collection

# รันเฉพาะขั้นตอนการจัดกลุ่มและปรับมาตรฐาน
python src/run_pipeline.py --normalization

# รันเฉพาะขั้นตอนการวิเคราะห์เชิงลึก
python src/run_pipeline.py --enrichment
```

### 3. สร้าง Vector Database สำหรับการค้นหา

```bash
python src/vector_db/create_vector_db.py --input data/processed/enriched/vector_db_data.json --output data/vector_db
```

### 4. เปิดให้บริการ API

```bash
# รันโดยตรง
python src/api/app.py

# หรือรันผ่าน uvicorn
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
```

หลังจากเปิดให้บริการ API แล้ว คุณสามารถเข้าถึงเอกสาร API ได้ที่ `http://localhost:8000/docs`

## 🔍 ผลลัพธ์ที่ได้

ระบบประมวลผลข้อมูลและสร้างไฟล์ต่างๆ ดังนี้:

1. **ข้อมูลอาชีพแยกตามกลุ่ม** - ไฟล์ข้อความใน `data/processed/` แยกตามกลุ่มอาชีพ
2. **ข้อมูลอาชีพรวม (JSON)** - `data/processed/processed_jobs.json` สำหรับใช้ในแอพพลิเคชัน
3. **ข้อมูลสำหรับ Embeddings** - `data/processed/embedding_data.json` สำหรับสร้าง Vector Database
4. **ข้อมูลวิเคราะห์เชิงลึก** - `data/processed/enriched/enriched_job_data.json` ประกอบด้วย:
   - ข้อมูลทักษะที่พบบ่อยในแต่ละอาชีพ
   - สถิติเงินเดือนตามระดับประสบการณ์
   - อาชีพที่เกี่ยวข้องกันตามความคล้ายคลึงของทักษะ
   - การวิเคราะห์เส้นทางอาชีพ
   - ข้อมูลสรุปอาชีพ
5. **Vector Database** - ใน `data/vector_db/` สำหรับการค้นหาเชิงความหมาย

## 📊 API Endpoints

API มีเอนด์พอยต์หลักดังนี้:

- `GET /jobs` - รายการอาชีพทั้งหมด
- `GET /jobs/{job_id}` - ข้อมูลละเอียดของอาชีพเฉพาะ
- `GET /jobs/summary/{job_id}` - ข้อมูลสรุปของอาชีพพร้อมทักษะที่จัดกลุ่มแล้ว
- `GET /search?query={query}` - ค้นหาอาชีพด้วย semantic search
- `GET /salary-stats/{job_id}` - สถิติเงินเดือนของอาชีพ
- `GET /related-jobs/{job_id}` - อาชีพที่เกี่ยวข้องตามความคล้ายคลึงของทักษะ

## 🧩 การเชื่อมต่อกับ Frontend

Frontend สามารถเชื่อมต่อกับ API นี้ได้โดยใช้ RESTful HTTP Requests เช่น:

```javascript
// ตัวอย่างการใช้ fetch ในการเรียกดูรายการอาชีพ
fetch("http://localhost:8000/jobs")
  .then((response) => response.json())
  .then((data) => {
    // แสดงผลข้อมูล
    console.log(data);
  });

// ตัวอย่างการค้นหาด้วย semantic search
fetch(`http://localhost:8000/search?query=เขียนโปรแกรม web&limit=5`)
  .then((response) => response.json())
  .then((results) => {
    // แสดงผลการค้นหา
    console.log(results);
  });
```

## 📑 แหล่งข้อมูล

ระบบนี้รวบรวมและประมวลผลข้อมูลจากหลายแหล่ง:

1. **JobsDB** - บทความแนะนำอาชีพจาก JobsDB
2. **Talance Tech** - ข้อมูลอาชีพจาก Talance
3. **ข้อมูลเงินเดือน** - ข้อมูลเงินเดือนตามตำแหน่งงานและประสบการณ์

## ⚠️ ข้อจำกัด

- ระบบนี้ต้องการแพ็คเกจ `faiss-cpu` และ `sentence-transformers` สำหรับความสามารถในการค้นหาเชิงความหมาย
- การสร้าง Vector Database อาจใช้เวลาและทรัพยากรมากขึ้นตามปริมาณข้อมูล
- ข้อมูลอาจมีการเปลี่ยนแปลงและต้องอัปเดตเป็นระยะ

## 🔧 การแก้ไขปัญหา

หากคุณพบปัญหาในการใช้งานระบบ ให้ตรวจสอบสิ่งต่อไปนี้:

1. ตรวจสอบว่าติดตั้งแพ็คเกจทั้งหมดในไฟล์ `requirements.txt` แล้ว
2. ตรวจสอบเส้นทางไฟล์และโฟลเดอร์ให้ถูกต้อง
3. ตรวจสอบไฟล์บันทึก (log files) เพื่อดูข้อผิดพลาดที่เกิดขึ้น

## 🤝 การมีส่วนร่วมพัฒนา

ยินดีรับการมีส่วนร่วมพัฒนาระบบนี้! คุณสามารถเพิ่มคุณลักษณะใหม่ แก้ไขบัก หรือปรับปรุงเอกสารได้ โดยทำตามขั้นตอนต่อไปนี้:

1. Fork โปรเจคนี้
2. สร้าง branch ใหม่ (`git checkout -b feature/amazing-feature`)
3. Commit การเปลี่ยนแปลงของคุณ (`git commit -m 'Add some amazing feature'`)
4. Push ไปยัง branch (`git push origin feature/amazing-feature`)
5. เปิด Pull Request
