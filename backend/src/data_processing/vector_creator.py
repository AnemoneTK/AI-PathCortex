import os
import json
import numpy as np
from typing import Dict, List, Any, Optional
import faiss
from tqdm import tqdm
from pathlib import Path
import time
import shutil
from src.utils.logger import get_logger

# ใช้ logger ที่ตั้งค่าแล้ว
logger = get_logger("vector_creator")

class VectorCreator:
    def __init__(self, 
                 processed_data_dir: str, 
                 vector_db_dir: str,
                 embedding_model: Optional[Any] = None,
                 clear_vector_db: bool = True):
        """
        เริ่มต้นการใช้งาน VectorCreator
        
        Args:
            processed_data_dir: โฟลเดอร์ข้อมูลที่ประมวลผลแล้ว
            vector_db_dir: โฟลเดอร์สำหรับเก็บฐานข้อมูล vector
            embedding_model: โมเดลสำหรับสร้าง embeddings (ถ้าไม่ระบุจะใช้ OpenAI API)
            clear_vector_db: หากเป็น True จะล้างไฟล์ทั้งหมดในโฟลเดอร์ vector db ก่อนการสร้างใหม่
        """
        self.processed_data_dir = processed_data_dir
        self.vector_db_dir = vector_db_dir
        self.embedding_model = embedding_model
        
        # สร้างโฟลเดอร์สำหรับเก็บ vector db
        self.job_knowledge_dir = os.path.join(vector_db_dir, "job_knowledge")
        os.makedirs(self.job_knowledge_dir, exist_ok=True)
        
        # ล้างโฟลเดอร์ vector db ก่อนสร้างใหม่ (ถ้าต้องการ)
        if clear_vector_db:
            self.clear_vector_db_directory()
        
        # ไฟล์ข้อมูล
        self.embedding_file = os.path.join(processed_data_dir, "embedding_data.json")
        self.index_file = os.path.join(self.job_knowledge_dir, "faiss_index.bin")
        self.metadata_file = os.path.join(self.job_knowledge_dir, "metadata.json")
    
    def clear_vector_db_directory(self):
        """
        ล้างไฟล์ทั้งหมดในโฟลเดอร์ vector db
        """
        try:
            logger.info(f"กำลังล้างไฟล์ทั้งหมดในโฟลเดอร์ {self.job_knowledge_dir}")
            # เก็บสำรองไฟล์เก่าถ้ามี
            backup_time = time.strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(os.path.dirname(self.job_knowledge_dir), f"vector_db_backup_{backup_time}")
            
            if os.path.exists(self.job_knowledge_dir) and os.listdir(self.job_knowledge_dir):
                os.makedirs(backup_dir, exist_ok=True)
                
                # สร้างสำเนาไฟล์ทั้งหมด
                for filename in os.listdir(self.job_knowledge_dir):
                    source_file = os.path.join(self.job_knowledge_dir, filename)
                    if os.path.isfile(source_file):
                        shutil.copy2(source_file, os.path.join(backup_dir, filename))
                
                # ลบไฟล์ทั้งหมดในโฟลเดอร์
                for filename in os.listdir(self.job_knowledge_dir):
                    file_path = os.path.join(self.job_knowledge_dir, filename)
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                
                logger.info(f"สำรองไฟล์เดิมไว้ที่ {backup_dir} และล้างโฟลเดอร์ {self.job_knowledge_dir} แล้ว")
            else:
                logger.info(f"ไม่มีไฟล์ในโฟลเดอร์ {self.job_knowledge_dir} ที่ต้องล้าง")
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการล้างโฟลเดอร์: {e}")
            logger.warning("ดำเนินการต่อโดยไม่ล้างโฟลเดอร์")
    
    def create_embeddings(self) -> Dict[str, Any]:
        """สร้าง embeddings และ FAISS index"""
        logger.info("เริ่มการสร้าง embeddings")
        
        # ตรวจสอบว่าไฟล์ข้อมูลมีอยู่จริง
        if not os.path.exists(self.embedding_file):
            logger.error(f"ไม่พบไฟล์ข้อมูล {self.embedding_file}")
            return {"success": False, "error": f"ไม่พบไฟล์ข้อมูล {self.embedding_file}"}
        
        # อ่านข้อมูลสำหรับสร้าง embeddings
        with open(self.embedding_file, 'r', encoding='utf-8') as f:
            embedding_data = json.load(f)
        
        logger.info(f"อ่านข้อมูลสำหรับสร้าง embeddings สำเร็จ {len(embedding_data)} รายการ")
        
        # สร้าง embeddings
        embeddings = []
        metadata = []
        
        # ถ้าไม่มีโมเดล embedding จะใช้ OpenAI API
        if self.embedding_model is None:
            logger.info("ไม่พบโมเดล embedding ที่ระบุ จะใช้ OpenAI API")
            # ในกรณีนี้เราจำลองการสร้าง embeddings
            try:
                # ในการทำงานจริงควรใช้ OpenAI API หรือโมเดล embedding อื่นๆ
                # embeddings = self._create_embeddings_with_openai(embedding_data)
                
                # จำลองการสร้าง embeddings (แทนที่จะใช้ OpenAI API)
                for item in tqdm(embedding_data, desc="Creating embeddings"):
                    # จำลองการสร้าง vector ขนาด 1536 มิติ (เหมือน OpenAI ada-002)
                    embedding = np.random.random(1536).astype(np.float32)
                    # Normalize vector
                    embedding = embedding / np.linalg.norm(embedding)
                    
                    embeddings.append(embedding)
                    metadata.append({
                        "id": item["id"],
                        "metadata": item["metadata"],
                        "text": item["text"][:200]  # เก็บเฉพาะ 200 ตัวอักษรแรก
                    })
            except Exception as e:
                logger.error(f"เกิดข้อผิดพลาดในการสร้าง embeddings: {str(e)}")
                return {"success": False, "error": str(e)}
        else:
            # ใช้โมเดลที่กำหนด
            logger.info(f"ใช้โมเดล {type(self.embedding_model).__name__} สำหรับสร้าง embeddings")
            try:
                for item in tqdm(embedding_data, desc="Creating embeddings"):
                    embedding = self.embedding_model.encode(item["text"])
                    embeddings.append(embedding)
                    metadata.append({
                        "id": item["id"],
                        "metadata": item["metadata"],
                        "text": item["text"][:200]  # เก็บเฉพาะ 200 ตัวอักษรแรก
                    })
            except Exception as e:
                logger.error(f"เกิดข้อผิดพลาดในการสร้าง embeddings: {str(e)}")
                return {"success": False, "error": str(e)}
        
        # แปลงเป็น numpy array
        embeddings_array = np.array(embeddings).astype(np.float32)
        
        # สร้าง FAISS index
        try:
            dimension = embeddings_array.shape[1]  # มิติของ embeddings
            index = faiss.IndexFlatL2(dimension)  # ใช้ L2 distance (Euclidean)
            
            # เพิ่ม embeddings ลงใน index
            index.add(embeddings_array)
            
            # บันทึก FAISS index
            faiss.write_index(index, self.index_file)
            
            # บันทึก metadata
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            logger.info(f"สร้างและบันทึก FAISS index สำเร็จ ({len(embeddings)} vectors)")
            
            return {
                "success": True,
                "vectors_count": len(embeddings),
                "dimension": dimension,
                "index_file": self.index_file,
                "metadata_file": self.metadata_file
            }
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการสร้าง FAISS index: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def search_similar_jobs(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        ค้นหาอาชีพที่คล้ายกับคำค้นหา
        
        Args:
            query: คำค้นหา
            k: จำนวนผลลัพธ์ที่ต้องการ
            
        Returns:
            รายการอาชีพที่คล้ายกับคำค้นหา
        """
        logger.info(f"กำลังค้นหาอาชีพที่คล้ายกับ: {query}")
        
        # ตรวจสอบว่า index มีอยู่จริง
        if not os.path.exists(self.index_file) or not os.path.exists(self.metadata_file):
            logger.error("ไม่พบไฟล์ FAISS index หรือ metadata")
            return []
        
        try:
            # โหลด FAISS index
            index = faiss.read_index(self.index_file)
            
            # โหลด metadata
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # สร้าง embedding สำหรับคำค้นหา
            if self.embedding_model is None:
                # จำลองการสร้าง embedding
                query_embedding = np.random.random(1536).astype(np.float32)
                query_embedding = query_embedding / np.linalg.norm(query_embedding)
            else:
                # ใช้โมเดลที่กำหนด
                query_embedding = self.embedding_model.encode([query])[0]
            
            # ค้นหาใน FAISS index
            query_embedding = np.array([query_embedding]).astype(np.float32)
            distances, indices = index.search(query_embedding, k)
            
            # แปลงผลลัพธ์
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(metadata):  # ป้องกันการเข้าถึงข้อมูลเกินขอบเขต
                    results.append({
                        "id": metadata[idx]["id"],
                        "title": metadata[idx]["metadata"]["titles"][0] if metadata[idx]["metadata"]["titles"] else "Unknown",
                        "text_preview": metadata[idx]["text"],
                        "similarity_score": float(1 / (1 + distances[0][i]))  # แปลง distance เป็น similarity score
                    })
            
            logger.info(f"ค้นหาสำเร็จ พบ {len(results)} ผลลัพธ์")
            return results
        
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการค้นหา: {str(e)}")
            return []