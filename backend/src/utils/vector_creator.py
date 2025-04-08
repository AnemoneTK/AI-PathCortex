import os
import json
import shutil
import faiss
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from sentence_transformers import SentenceTransformer
from colorama import init, Fore, Style

# เริ่มต้นใช้งาน colorama
init(autoreset=True)

class VectorCreator:
    """
    คลาสสำหรับสร้าง vector embeddings และฐานข้อมูล FAISS
    สำหรับการค้นหาข้อมูลด้วย semantic search
    """
    def __init__(self, 
                processed_data_dir: str, 
                vector_db_dir: str,
                embedding_model=None,
                clear_vector_db: bool = True):
        """
        กำหนดค่าเริ่มต้นสำหรับ VectorCreator
        
        Args:
            processed_data_dir: โฟลเดอร์ที่เก็บข้อมูลที่ผ่านการประมวลผลแล้ว
            vector_db_dir: โฟลเดอร์ที่จะเก็บฐานข้อมูล vector
            embedding_model: โมเดลสำหรับสร้าง embedding หากไม่ระบุจะใช้การจำลอง
            clear_vector_db: ล้างฐานข้อมูล vector เดิมก่อนสร้างใหม่
        """
        self.processed_data_dir = Path(processed_data_dir)
        self.vector_db_dir = Path(vector_db_dir)
        self.embedding_model = embedding_model
        
        # โฟลเดอร์ย่อยสำหรับแต่ละประเภทของข้อมูล
        self.job_vector_dir = self.vector_db_dir / "job_knowledge"
        self.advice_vector_dir = self.vector_db_dir / "career_advice"
        
        # สร้างโฟลเดอร์ถ้ายังไม่มี
        self.job_vector_dir.mkdir(parents=True, exist_ok=True)
        self.advice_vector_dir.mkdir(parents=True, exist_ok=True)
        
        # ไฟล์ FAISS index และ metadata
        self.job_index_path = self.job_vector_dir / "faiss_index.bin"
        self.job_metadata_path = self.job_vector_dir / "job_metadata.json"
        
        self.advice_index_path = self.advice_vector_dir / "faiss_index.bin"
        self.advice_metadata_path = self.advice_vector_dir / "metadata.json"
        
        # ล้างฐานข้อมูล vector เดิมถ้าจำเป็น
        if clear_vector_db:
            self._clear_vector_database()
        
        print(f"{Fore.CYAN}VectorCreator เริ่มต้นเรียบร้อย")
        print(f"{Fore.CYAN}📂 โฟลเดอร์ข้อมูลที่ประมวลผลแล้ว: {self.processed_data_dir}")
        print(f"{Fore.CYAN}📂 โฟลเดอร์สำหรับเก็บฐานข้อมูล vector: {self.vector_db_dir}")
        print(f"{Fore.CYAN}🤖 โมเดล Embedding: {type(self.embedding_model).__name__ if self.embedding_model else 'ไม่ได้ระบุ (จะใช้การจำลอง)'}") 
    
    def _clear_vector_database(self) -> None:
        """ล้างฐานข้อมูล vector เดิม"""
        print(f"{Fore.YELLOW}ℹ️ กำลังล้างฐานข้อมูล vector เดิม...")
        
        # ลบไฟล์ FAISS index ถ้ามีอยู่
        if self.job_index_path.exists():
            os.remove(self.job_index_path)
            print(f"{Fore.GREEN}✅ ลบไฟล์ {self.job_index_path} เรียบร้อย")
        
        if self.job_metadata_path.exists():
            os.remove(self.job_metadata_path)
            print(f"{Fore.GREEN}✅ ลบไฟล์ {self.job_metadata_path} เรียบร้อย")
        
        if self.advice_index_path.exists():
            os.remove(self.advice_index_path)
            print(f"{Fore.GREEN}✅ ลบไฟล์ {self.advice_index_path} เรียบร้อย")
        
        if self.advice_metadata_path.exists():
            os.remove(self.advice_metadata_path)
            print(f"{Fore.GREEN}✅ ลบไฟล์ {self.advice_metadata_path} เรียบร้อย")
    
    def _create_mock_embedding(self, text: str, dimension: int = 384) -> np.ndarray:
        """
        สร้าง embedding จำลองในกรณีที่ไม่มีโมเดล Embedding
        
        Args:
            text: ข้อความที่ต้องการสร้าง embedding
            dimension: ขนาดของ vector (default: 384 สำหรับ MiniLM)
            
        Returns:
            numpy array ที่เป็น embedding
        """
        # ใช้ hash ของข้อความเพื่อให้ได้ค่าเดิมเมื่อให้ข้อความเดียวกัน
        np.random.seed(hash(text) % 2**32)
        vector = np.random.random(dimension).astype(np.float32)
        # Normalize vector ให้มีความยาวเท่ากับ 1
        return vector / np.linalg.norm(vector)
    
    def _get_embedding(self, text: str, dimension: int = 384) -> np.ndarray:
        if self.embedding_model:
            # Ensure normalization
            embedding = self.embedding_model.encode(text)
            return embedding / np.linalg.norm(embedding)
        else:
            return self._create_mock_embedding(text, dimension)
    
    def _load_job_data(self) -> List[Dict[str, Any]]:
        """
        โหลดข้อมูลอาชีพจากไฟล์ที่ทำความสะอาดแล้ว
        
        Returns:
            List ของข้อมูลอาชีพ
        """
        cleaned_jobs_dir = self.processed_data_dir / "cleaned_jobs"
        job_files = list(cleaned_jobs_dir.glob("*.json"))
        
        if not job_files:
            print(f"{Fore.RED}❌ ไม่พบไฟล์ข้อมูลอาชีพใน {cleaned_jobs_dir}")
            return []
        
        print(f"{Fore.CYAN}📚 พบไฟล์ข้อมูลอาชีพ {len(job_files)} ไฟล์")
        
        job_data = []
        for file_path in job_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    job_data.append(data)
            except Exception as e:
                print(f"{Fore.RED}❌ เกิดข้อผิดพลาดในการอ่านไฟล์ {file_path}: {str(e)}")
        
        print(f"{Fore.GREEN}✅ โหลดข้อมูลอาชีพสำเร็จ: {len(job_data)} รายการ")
        return job_data
    
    def _load_career_advice_data(self) -> List[Dict[str, Any]]:
        """
        โหลดข้อมูลคำแนะนำอาชีพ
        
        Returns:
            List ของข้อมูลคำแนะนำอาชีพ
        """
        advice_file = self.processed_data_dir / "career_advices" / "career_advices.json"
        
        if not advice_file.exists():
            print(f"{Fore.RED}❌ ไม่พบไฟล์ข้อมูลคำแนะนำอาชีพที่ {advice_file}")
            return []
        
        try:
            with open(advice_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                if isinstance(data, dict) and "career_advices" in data:
                    advices = data["career_advices"]
                    print(f"{Fore.GREEN}✅ โหลดข้อมูลคำแนะนำอาชีพสำเร็จ: {len(advices)} รายการ")
                    return advices
                elif isinstance(data, list):
                    print(f"{Fore.GREEN}✅ โหลดข้อมูลคำแนะนำอาชีพสำเร็จ: {len(data)} รายการ")
                    return data
                else:
                    print(f"{Fore.RED}❌ รูปแบบข้อมูลคำแนะนำอาชีพไม่ถูกต้อง")
                    return []
        except Exception as e:
            print(f"{Fore.RED}❌ เกิดข้อผิดพลาดในการอ่านไฟล์ {advice_file}: {str(e)}")
            return []
    
    def _prepare_job_text_for_embedding(self, job: Dict[str, Any]) -> str:
        """
        เตรียมข้อความจากข้อมูลอาชีพสำหรับสร้าง embedding
        
        Args:
            job: ข้อมูลอาชีพ
            
        Returns:
            ข้อความที่พร้อมสำหรับสร้าง embedding
        """
        text_parts = []
        
        # เพิ่มชื่อตำแหน่งงาน
        if "titles" in job and job["titles"]:
            text_parts.append(f"ตำแหน่งงาน: {', '.join(job['titles'])}")
        
        # เพิ่มคำอธิบาย
        if "description" in job and job["description"]:
            text_parts.append(f"คำอธิบาย: {job['description']}")
        
        # เพิ่มความรับผิดชอบ
        if "responsibilities" in job and job["responsibilities"]:
            resp_text = " ".join(f"- {resp}" for resp in job["responsibilities"])
            text_parts.append(f"ความรับผิดชอบ: {resp_text}")
        
        # เพิ่มทักษะ
        if "skills" in job and job["skills"]:
            skills_text = ", ".join(job["skills"])
            text_parts.append(f"ทักษะ: {skills_text}")
        
        # เพิ่มระดับเงินเดือนและประสบการณ์
        if "salary_ranges" in job and job["salary_ranges"]:
            salary_info = []
            for salary_range in job["salary_ranges"]:
                if "experience" in salary_range and "salary" in salary_range:
                    salary_info.append(f"ประสบการณ์ {salary_range['experience']} ปี: เงินเดือน {salary_range['salary']} บาท")
            
            if salary_info:
                text_parts.append(f"ข้อมูลเงินเดือน: {' '.join(salary_info)}")
        
        # รวมทุกส่วนเข้าด้วยกัน
        return " ".join(text_parts)
    
    def _prepare_advice_text_for_embedding(self, advice: Dict[str, Any]) -> str:
        text_parts = []
        
        # เน้นหัวข้อ
        if "title" in advice and advice["title"]:
            text_parts.append(f"หัวข้อ: {advice['title']} " * 3)
        
        # เพิ่มเนื้อหา
        if "content" in advice and advice["content"]:
            text_parts.append(f"เนื้อหา: {advice['content']}")
        
        # เน้นแท็ก
        if "tags" in advice and advice["tags"]:
            tags_text = ", ".join(advice["tags"])
            text_parts.append(f"แท็ก: {tags_text} " * 2)
        
        return " ".join(text_parts)
    
    def create_job_embeddings(self) -> Dict[str, Any]:
        """
        สร้าง embeddings สำหรับข้อมูลอาชีพและบันทึกลงใน FAISS
        
        Returns:
            ผลลัพธ์ของการสร้าง embeddings
        """
        result = {
            "success": False,
            "vectors_count": 0,
            "error": None
        }
        
        try:
            # โหลดข้อมูลอาชีพ
            job_data = self._load_job_data()
            
            if not job_data:
                result["error"] = "ไม่พบข้อมูลอาชีพ"
                return result
            
            print(f"{Fore.CYAN}🔄 กำลังสร้าง embeddings สำหรับข้อมูลอาชีพ {len(job_data)} รายการ...")
            
            # เตรียมข้อมูลสำหรับสร้าง embeddings
            job_ids = []
            job_texts = []
            job_ids_to_index = {}
            
            for job in job_data:
                if "id" not in job:
                    continue
                
                job_text = self._prepare_job_text_for_embedding(job)
                job_texts.append(job_text)
                job_ids.append(job["id"])
            
            # ตรวจสอบข้อมูล
            if not job_texts:
                result["error"] = "ไม่สามารถเตรียมข้อความสำหรับสร้าง embeddings ได้"
                return result
            
            # สร้าง embeddings
            print(f"{Fore.CYAN}🧠 กำลังสร้าง embeddings จำนวน {len(job_texts)} รายการ...")
            
            if self.embedding_model:
                # ใช้โมเดลจริง
                embeddings = self.embedding_model.encode(job_texts, show_progress_bar=True)
            else:
                # ใช้การจำลอง
                print(f"{Fore.YELLOW}⚠️ ไม่พบโมเดล embedding จะใช้การจำลอง")
                embeddings = np.array([self._get_embedding(text) for text in job_texts])
            
            # สร้าง FAISS index
            print(f"{Fore.CYAN}📊 กำลังสร้าง FAISS index...")
            
            dimension = embeddings.shape[1]
            index = faiss.IndexFlatL2(dimension)
            index.add(embeddings.astype(np.float32))
            
            # สร้าง mapping ระหว่าง job_id กับ index
            for i, job_id in enumerate(job_ids):
                job_ids_to_index[job_id] = i
            
            # บันทึก FAISS index
            print(f"{Fore.CYAN}💾 กำลังบันทึก FAISS index ไปที่ {self.job_index_path}...")
            faiss.write_index(index, str(self.job_index_path))
            
            # บันทึก metadata
            print(f"{Fore.CYAN}💾 กำลังบันทึก metadata ไปที่ {self.job_metadata_path}...")
            metadata = {
                "job_ids": job_ids,
                "job_ids_to_index": job_ids_to_index,
                "job_data": job_data
            }
            
            with open(self.job_metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            print(f"{Fore.GREEN}✅ สร้าง embeddings สำหรับข้อมูลอาชีพสำเร็จ: {len(job_ids)} vectors")
            
            result["success"] = True
            result["vectors_count"] = len(job_ids)
            
            return result
            
        except Exception as e:
            print(f"{Fore.RED}❌ เกิดข้อผิดพลาดในการสร้าง embeddings สำหรับข้อมูลอาชีพ: {str(e)}")
            result["error"] = str(e)
            return result
    
    def create_advice_embeddings(self) -> Dict[str, Any]:
        """
        สร้าง embeddings สำหรับข้อมูลคำแนะนำอาชีพและบันทึกลงใน FAISS
        
        Returns:
            ผลลัพธ์ของการสร้าง embeddings
        """
        result = {
            "success": False,
            "vectors_count": 0,
            "error": None
        }
        
        try:
            # โหลดข้อมูลคำแนะนำอาชีพ
            advice_data = self._load_career_advice_data()
            
            if not advice_data:
                result["error"] = "ไม่พบข้อมูลคำแนะนำอาชีพ"
                return result
            
            print(f"{Fore.CYAN}🔄 กำลังสร้าง embeddings สำหรับข้อมูลคำแนะนำอาชีพ {len(advice_data)} รายการ...")
            
            # เตรียมข้อมูลสำหรับสร้าง embeddings
            advice_ids = []
            advice_texts = []
            advice_ids_to_index = {}
            
            for i, advice in enumerate(advice_data):
                # ตรวจสอบ ID
                if "id" not in advice:
                    advice["id"] = f"advice_{i}"
                
                advice_text = self._prepare_advice_text_for_embedding(advice)
                advice_texts.append(advice_text)
                advice_ids.append(advice["id"])
            
            # ตรวจสอบข้อมูล
            if not advice_texts:
                result["error"] = "ไม่สามารถเตรียมข้อความสำหรับสร้าง embeddings ได้"
                return result
            
            # สร้าง embeddings
            print(f"{Fore.CYAN}🧠 กำลังสร้าง embeddings จำนวน {len(advice_texts)} รายการ...")
            
            if self.embedding_model:
                # ใช้โมเดลจริง
                embeddings = self.embedding_model.encode(advice_texts, show_progress_bar=True)
            else:
                # ใช้การจำลอง
                print(f"{Fore.YELLOW}⚠️ ไม่พบโมเดล embedding จะใช้การจำลอง")
                embeddings = np.array([self._get_embedding(text) for text in advice_texts])
            
            # สร้าง FAISS index
            print(f"{Fore.CYAN}📊 กำลังสร้าง FAISS index...")
            
            dimension = embeddings.shape[1]
            index = faiss.IndexFlatL2(dimension)
            index.add(embeddings.astype(np.float32))
            
            # สร้าง mapping ระหว่าง advice_id กับ index
            for i, advice_id in enumerate(advice_ids):
                advice_ids_to_index[advice_id] = i
            
            # บันทึก FAISS index
            print(f"{Fore.CYAN}💾 กำลังบันทึก FAISS index ไปที่ {self.advice_index_path}...")
            faiss.write_index(index, str(self.advice_index_path))
            
            # บันทึก metadata
            print(f"{Fore.CYAN}💾 กำลังบันทึก metadata ไปที่ {self.advice_metadata_path}...")
            
            # สร้างข้อมูล metadata ที่กระชับ
            simplified_advice_data = []
            for advice in advice_data:
                simplified = {
                    "id": advice["id"],
                    "title": advice.get("title", ""),
                    "tags": advice.get("tags", []),
                    "source": advice.get("source", ""),
                    "url": advice.get("url", "")
                }
                
                # ดึงเนื้อหาอ่านง่ายสำหรับแสดงผล
                if "content" in advice:
                    simplified["text"] = advice["content"][:500] + "..." if len(advice["content"]) > 500 else advice["content"]
                elif "paragraphs" in advice and advice["paragraphs"]:
                    joined_text = " ".join(advice["paragraphs"][:3])
                    simplified["text"] = joined_text[:500] + "..." if len(joined_text) > 500 else joined_text
                
                simplified_advice_data.append(simplified)
            
            metadata = {
                "advice_ids": advice_ids,
                "advice_ids_to_index": advice_ids_to_index,
                "advice_data": simplified_advice_data
            }
            
            with open(self.advice_metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            print(f"{Fore.GREEN}✅ สร้าง embeddings สำหรับข้อมูลคำแนะนำอาชีพสำเร็จ: {len(advice_ids)} vectors")
            
            result["success"] = True
            result["vectors_count"] = len(advice_ids)
            
            return result
            
        except Exception as e:
            print(f"{Fore.RED}❌ เกิดข้อผิดพลาดในการสร้าง embeddings สำหรับข้อมูลคำแนะนำอาชีพ: {str(e)}")
            result["error"] = str(e)
            return result
    
    def create_all_embeddings(self) -> Dict[str, Any]:
        """
        สร้าง embeddings ทั้งหมด ทั้งข้อมูลอาชีพและคำแนะนำอาชีพ
        
        Returns:
            ผลลัพธ์ของการสร้าง embeddings
        """
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}= เริ่มต้นการสร้าง Vector Database ทั้งหมด")
        print(f"{Fore.CYAN}{'='*60}")
        
        # สร้าง embeddings สำหรับข้อมูลอาชีพ
        print(f"\n{Fore.CYAN}{'='*20} สร้าง embeddings สำหรับข้อมูลอาชีพ {'='*20}")
        job_result = self.create_job_embeddings()
        
        # สร้าง embeddings สำหรับข้อมูลคำแนะนำอาชีพ
        print(f"\n{Fore.CYAN}{'='*20} สร้าง embeddings สำหรับข้อมูลคำแนะนำอาชีพ {'='*20}")
        advice_result = self.create_advice_embeddings()
        
        return {
            "job_embeddings": job_result,
            "advice_embeddings": advice_result
        }
    
    def search_similar_jobs(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        ค้นหาอาชีพที่เกี่ยวข้องกับคำค้นหา
        
        Args:
            query: คำค้นหา
            k: จำนวนผลลัพธ์ที่ต้องการ
            
        Returns:
            รายการอาชีพที่เกี่ยวข้อง
        """
        # ตรวจสอบว่า vector database มีอยู่จริง
        if not self.job_index_path.exists() or not self.job_metadata_path.exists():
            print(f"{Fore.RED}❌ ไม่พบ vector database สำหรับข้อมูลอาชีพ")
            return []
        
        try:
            # โหลด FAISS index
            index = faiss.read_index(str(self.job_index_path))
            
            # โหลด metadata
            with open(self.job_metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # สร้าง embedding สำหรับคำค้นหา
            query_embedding = None
            if self.embedding_model:
                query_embedding = self.embedding_model.encode([query])[0]
            else:
                query_embedding = self._get_embedding(query)
            
            # ค้นหาใน FAISS
            query_embedding = np.array([query_embedding]).astype(np.float32)
            distances, indices = index.search(query_embedding, k)
            
            # แปลงผลลัพธ์
            results = []
            for i, idx in enumerate(indices[0]):
                if idx == -1 or idx >= len(metadata["job_ids"]):
                    continue
                
                job_id = metadata["job_ids"][idx]
                job_data = None
                
                # หาข้อมูลอาชีพจาก job_id
                for job in metadata["job_data"]:
                    if job["id"] == job_id:
                        job_data = job
                        break
                
                if job_data is None:
                    continue
                
                # คำนวณคะแนนความคล้ายคลึง (1 - ระยะทาง)
                similarity = 1.0 / (1.0 + distances[0][i])
                
                # สร้างข้อมูลสำหรับผลลัพธ์
                result = {
                    "id": job_id,
                    "title": job_data["titles"][0] if job_data["titles"] else job_id,
                    "similarity": similarity,
                    "description": job_data.get("description", ""),
                    "responsibilities": job_data.get("responsibilities", []),
                    "skills": job_data.get("skills", []),
                }
                
                results.append(result)
                
                # แสดงผล
                print(f"{i+1}. {Fore.GREEN}{result['title']}{Style.RESET_ALL} " + 
                     f"(คะแนนความเหมือน: {Fore.YELLOW}{result['similarity']:.2f}{Style.RESET_ALL})")
            
            return results
        
        except Exception as e:
            print(f"{Fore.RED}❌ เกิดข้อผิดพลาดในการค้นหาอาชีพ: {str(e)}")
            return []
    
    def search_relevant_advices(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        ค้นหาคำแนะนำอาชีพที่เกี่ยวข้องกับคำค้นหา
        
        Args:
            query: คำค้นหา
            k: จำนวนผลลัพธ์ที่ต้องการ
            
        Returns:
            รายการคำแนะนำอาชีพที่เกี่ยวข้อง
        """
        # ตรวจสอบว่า vector database มีอยู่จริง
        if not self.advice_index_path.exists() or not self.advice_metadata_path.exists():
            print(f"{Fore.RED}❌ ไม่พบ vector database สำหรับข้อมูลคำแนะนำอาชีพ")
            return []
        
        try:
            # โหลด FAISS index
            index = faiss.read_index(str(self.advice_index_path))
            
            # โหลด metadata
            with open(self.advice_metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # สร้าง embedding สำหรับคำค้นหา
            query_embedding = None
            if self.embedding_model:
                query_embedding = self.embedding_model.encode([query])[0]
            else:
                query_embedding = self._get_embedding(query)
            
            # ค้นหาใน FAISS
            query_embedding = np.array([query_embedding]).astype(np.float32)
            distances, indices = index.search(query_embedding, k)
            
            # แปลงผลลัพธ์
            results = []
            for i, idx in enumerate(indices[0]):
                if idx == -1 or idx >= len(metadata["advice_ids"]):
                    continue
                
                advice_id = metadata["advice_ids"][idx]
                advice_data = None
                
                # หาข้อมูลคำแนะนำจาก advice_id
                for advice in metadata["advice_data"]:
                    if advice["id"] == advice_id:
                        advice_data = advice
                        break
                
                if advice_data is None:
                    continue
                
                # คำนวณคะแนนความคล้ายคลึง (1 - ระยะทาง)
                similarity = 1.0 / (1.0 + distances[0][i])
                
                # สร้างข้อมูลสำหรับผลลัพธ์
                result = {
                    "id": advice_id,
                    "title": advice_data.get("title", ""),
                    "similarity": similarity,
                    "text": advice_data.get("text", ""),
                    "tags": advice_data.get("tags", []),
                    "source": advice_data.get("source", ""),
                    "url": advice_data.get("url", "")
                }
                
                results.append(result)
                
                # แสดงผล
                tags_str = f", แท็ก: {', '.join(result['tags'])}" if result['tags'] else ""
                print(f"{i+1}. {Fore.GREEN}{result['title']}{Style.RESET_ALL} " + 
                    f"(คะแนนความเหมือน: {Fore.YELLOW}{result['similarity']:.2f}{Style.RESET_ALL}{tags_str})")
            
            return results
        
        except Exception as e:
            print(f"{Fore.RED}❌ เกิดข้อผิดพลาดในการค้นหาคำแนะนำ: {str(e)}")
            return []

    def get_job_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        ดึงข้อมูลอาชีพโดย ID
        
        Args:
            job_id: ID ของอาชีพที่ต้องการ
            
        Returns:
            ข้อมูลอาชีพหรือ None ถ้าไม่พบ
        """
        # ตรวจสอบว่า metadata มีอยู่จริง
        if not self.job_metadata_path.exists():
            print(f"{Fore.RED}❌ ไม่พบไฟล์ metadata สำหรับข้อมูลอาชีพ")
            return None
        
        try:
            # โหลด metadata
            with open(self.job_metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # หาข้อมูลอาชีพจาก job_id
            for job in metadata["job_data"]:
                if job["id"] == job_id:
                    return job
            
            print(f"{Fore.YELLOW}⚠️ ไม่พบข้อมูลอาชีพสำหรับ ID: {job_id}")
            return None
            
        except Exception as e:
            print(f"{Fore.RED}❌ เกิดข้อผิดพลาดในการดึงข้อมูลอาชีพ: {str(e)}")
            return None
    
    def get_advice_by_id(self, advice_id: str) -> Optional[Dict[str, Any]]:
        """
        ดึงข้อมูลคำแนะนำอาชีพโดย ID
        
        Args:
            advice_id: ID ของคำแนะนำที่ต้องการ
            
        Returns:
            ข้อมูลคำแนะนำหรือ None ถ้าไม่พบ
        """
        # ตรวจสอบว่า metadata มีอยู่จริง
        if not self.advice_metadata_path.exists():
            print(f"{Fore.RED}❌ ไม่พบไฟล์ metadata สำหรับข้อมูลคำแนะนำอาชีพ")
            return None
        
        try:
            # โหลด metadata
            with open(self.advice_metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # หาข้อมูลคำแนะนำจาก advice_id
            for advice in metadata["advice_data"]:
                if advice["id"] == advice_id:
                    return advice
            
            print(f"{Fore.YELLOW}⚠️ ไม่พบข้อมูลคำแนะนำสำหรับ ID: {advice_id}")
            return None
            
        except Exception as e:
            print(f"{Fore.RED}❌ เกิดข้อผิดพลาดในการดึงข้อมูลคำแนะนำ: {str(e)}")
            return None


# ตัวอย่างการใช้งาน
if __name__ == "__main__":
    # สร้างโมเดล SentenceTransformer (ถ้ามี)
    model = None
    try:
        from sentence_transformers import SentenceTransformer
        print(f"{Fore.CYAN}🔄 กำลังโหลดโมเดล SentenceTransformer...")
        model = SentenceTransformer('intfloat/multilingual-e5-large')
        print(f"{Fore.GREEN}✅ โหลดโมเดลสำเร็จ")
    except Exception as e:
        print(f"{Fore.YELLOW}⚠️ ไม่สามารถโหลดโมเดลได้: {str(e)}")
        print(f"{Fore.YELLOW}⚠️ จะใช้การจำลอง embedding แทน")
    
    # กำหนดพาธของไฟล์
    processed_data_dir = "data/processed"
    vector_db_dir = "data/vector_db"
    
    try:
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}= ทดสอบการใช้งาน VectorCreator")
        print(f"{Fore.CYAN}{'='*60}")
        
        # สร้าง VectorCreator
        creator = VectorCreator(
            processed_data_dir=processed_data_dir,
            vector_db_dir=vector_db_dir,
            embedding_model=model,
            clear_vector_db=True  # ล้างข้อมูลเดิมก่อนสร้างใหม่
        )
        
        # สร้าง embeddings ทั้งหมด
        results = creator.create_all_embeddings()
        
        # ทดสอบการค้นหา
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}= ทดสอบการค้นหา")
        print(f"{Fore.CYAN}{'='*60}")
        
        # ทดสอบค้นหาอาชีพ
        print(f"\n{Fore.CYAN}🔍 ทดสอบค้นหาอาชีพที่เกี่ยวข้องกับ: 'นักพัฒนาซอฟต์แวร์'{Style.RESET_ALL}")
        creator.search_similar_jobs("นักพัฒนาซอฟต์แวร์", k=3)
        
        print(f"\n{Fore.CYAN}🔍 ทดสอบค้นหาอาชีพที่เกี่ยวข้องกับ: 'การจัดการโครงการ'{Style.RESET_ALL}")
        creator.search_similar_jobs("การจัดการโครงการ", k=3)
        
        # ทดสอบค้นหาคำแนะนำอาชีพ
        print(f"\n{Fore.CYAN}🔍 ทดสอบค้นหาคำแนะนำอาชีพที่เกี่ยวข้องกับ: 'การเขียน resume'{Style.RESET_ALL}")
        creator.search_relevant_advices("การเขียน resume", k=3)
        
        print(f"\n{Fore.CYAN}🔍 ทดสอบค้นหาคำแนะนำอาชีพที่เกี่ยวข้องกับ: 'การเตรียมตัวสัมภาษณ์งาน'{Style.RESET_ALL}")
        creator.search_relevant_advices("การเตรียมตัวสัมภาษณ์งาน", k=3)
        
        print(f"\n{Fore.GREEN}✅ ทดสอบเสร็จสิ้น")
        
    except Exception as e:
        print(f"{Fore.RED}❌ เกิดข้อผิดพลาดในการทดสอบ: {str(e)}")