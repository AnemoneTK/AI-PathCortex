#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fine-tuning utilities for Career AI Advisor.

This module provides functions for preparing data and fine-tuning LLM models.
"""

import os
import json
import glob
import random
from typing import List, Dict, Any, Optional, Tuple
import httpx
import asyncio
from tqdm import tqdm
from pathlib import Path

from src.utils.config import (
    LLM_API_BASE, 
    LLM_API_KEY, 
    LLM_MODEL, 
    FINE_TUNED_MODEL, 
    DATA_DIR
)
from src.utils.logger import get_logger

# ตั้งค่า logger
logger = get_logger("fine_tune")

class FineTuneHelper:
    """
    คลาสช่วยเหลือสำหรับการสร้างชุดข้อมูลและทำ fine-tuning
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        เริ่มต้นใช้งาน FineTuneHelper
        
        Args:
            output_dir: โฟลเดอร์ที่จะบันทึกไฟล์ข้อมูล fine-tuning (ถ้าไม่ระบุจะใช้ค่าเริ่มต้น)
        """
        self.output_dir = output_dir or os.path.join(DATA_DIR, "fine_tune")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # โฟลเดอร์ข้อมูลอาชีพและคำแนะนำ
        self.embedding_dir = os.path.join(DATA_DIR, "embedding")
        self.job_data_file = os.path.join(self.embedding_dir, "embedding_data.json")
        self.career_advice_file = os.path.join(self.embedding_dir, "career_advices_embeddings.json")
        
        # ตรวจสอบไฟล์ข้อมูล
        if not os.path.exists(self.job_data_file):
            logger.warning(f"ไม่พบไฟล์ข้อมูลอาชีพ: {self.job_data_file}")
        
        if not os.path.exists(self.career_advice_file):
            logger.warning(f"ไม่พบไฟล์ข้อมูลคำแนะนำอาชีพ: {self.career_advice_file}")
    
    def _load_data(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        โหลดข้อมูลอาชีพและคำแนะนำอาชีพ
        
        Returns:
            Tuple ของ (job_data, career_advice_data)
        """
        job_data = []
        if os.path.exists(self.job_data_file):
            with open(self.job_data_file, 'r', encoding='utf-8') as f:
                job_data = json.load(f)
            logger.info(f"โหลดข้อมูลอาชีพสำเร็จ: {len(job_data)} รายการ")
        
        career_advice_data = []
        if os.path.exists(self.career_advice_file):
            with open(self.career_advice_file, 'r', encoding='utf-8') as f:
                career_advice_data = json.load(f)
            logger.info(f"โหลดข้อมูลคำแนะนำอาชีพสำเร็จ: {len(career_advice_data)} รายการ")
        
        return job_data, career_advice_data
    
    def _generate_prompts_from_job_data(self, job_data: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        สร้าง prompts จากข้อมูลอาชีพ
        
        Args:
            job_data: ข้อมูลอาชีพ
            
        Returns:
            List ของ prompt-response pairs
        """
        prompts = []
        
        # คำถามพื้นฐานเกี่ยวกับอาชีพ
        job_question_templates = [
            "อาชีพ {job_title} ทำอะไรบ้าง?",
            "{job_title} ต้องมีทักษะอะไรบ้าง?",
            "เงินเดือนของ {job_title} ประมาณเท่าไหร่?",
            "อยากเป็น {job_title} ต้องเรียนอะไร?",
            "หน้าที่ความรับผิดชอบของ {job_title} คืออะไร?",
            "ช่วยแนะนำวิธีเตรียมตัวเพื่อเป็น {job_title}",
            "ความก้าวหน้าในอาชีพของ {job_title} เป็นอย่างไร?",
            "{job_title} ต่างจาก {other_job} อย่างไร?"
        ]
        
        # สร้าง prompts จากข้อมูลอาชีพ
        for job in job_data:
            job_title = job.get("metadata", {}).get("titles", [""])[0]
            if not job_title:
                continue
            
            # หา job อื่นเพื่อใช้ในคำถามเปรียบเทียบ
            other_jobs = [j.get("metadata", {}).get("titles", [""])[0] for j in job_data if j != job and j.get("metadata", {}).get("titles")]
            other_job = random.choice(other_jobs) if other_jobs else "นักพัฒนาซอฟต์แวร์"
            
            for template in job_question_templates:
                question = template.format(job_title=job_title, other_job=other_job)
                
                # สร้าง context จากข้อมูลอาชีพ
                context = f"ข้อมูลอาชีพ:\n{job.get('text', '')}"
                
                # สร้าง prompt ในรูปแบบที่เหมาะสำหรับ fine-tuning
                prompt = {
                    "prompt": f"คำถาม: {question}\n\nบริบท:\n{context}\n\nคำตอบ:",
                    "completion": self._generate_mock_response(question, job)
                }
                
                prompts.append(prompt)
        
        return prompts
    
    def _generate_prompts_from_career_advice(self, career_advice_data: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        สร้าง prompts จากข้อมูลคำแนะนำอาชีพ
        
        Args:
            career_advice_data: ข้อมูลคำแนะนำอาชีพ
            
        Returns:
            List ของ prompt-response pairs
        """
        prompts = []
        
        # คำถามพื้นฐานเกี่ยวกับคำแนะนำอาชีพ
        advice_question_templates = [
            "มีเทคนิคในการเขียน Resume อย่างไร?",
            "เตรียมตัวอย่างไรสำหรับการสัมภาษณ์งาน?",
            "วิธีพัฒนาทักษะเพื่อเปลี่ยนสายงานเป็น {tag}?",
            "ทำงานไม่ตรงสายควรทำอย่างไร?",
            "เด็กจบใหม่ควรเลือกทำงานกับบริษัทขนาดเล็กหรือใหญ่?",
            "แนะนำวิธีต่อรองเงินเดือนสำหรับเด็กจบใหม่",
            "มีเทคนิคในการแนะนำตัวในการสัมภาษณ์งานอย่างไร?",
            "ทำอย่างไรให้โดดเด่นในการสัมภาษณ์งาน?",
            "เรซูเม่กับพอร์ตโฟลิโอต่างกันอย่างไร?"
        ]
        
        # สร้าง prompts จากข้อมูลคำแนะนำอาชีพ
        for advice in career_advice_data:
            tags = advice.get("metadata", {}).get("tags", [])
            if not tags:
                continue
            
            title = advice.get("metadata", {}).get("title", "")
            
            # เลือกคำถามที่เกี่ยวข้องกับแท็ก
            for template in advice_question_templates:
                # เลือกแท็กสุ่มสำหรับใช้ในคำถาม
                tag = random.choice(tags)
                question = template.format(tag=tag)
                
                # สร้าง context จากข้อมูลคำแนะนำ
                context = f"คำแนะนำ:\nหัวข้อ: {title}\n{advice.get('text', '')}"
                
                # สร้าง prompt ในรูปแบบที่เหมาะสำหรับ fine-tuning
                prompt = {
                    "prompt": f"คำถาม: {question}\n\nบริบท:\n{context}\n\nคำตอบ:",
                    "completion": self._generate_mock_response(question, advice)
                }
                
                prompts.append(prompt)
        
        return prompts
    
    def _generate_mock_response(self, question: str, data: Dict[str, Any]) -> str:
        """
        สร้างคำตอบจำลองสำหรับคำถาม (ในกรณีนี้คือตัวอย่างเท่านั้น)
        ในการใช้งานจริงควรใช้ LLM ที่มีอยู่แล้วสร้างคำตอบคุณภาพสูง
        
        Args:
            question: คำถาม
            data: ข้อมูลที่ใช้ในการสร้างคำตอบ
            
        Returns:
            คำตอบที่สร้างขึ้น
        """
        # ในการใช้งานจริง ควรเรียกใช้ LLM API เพื่อสร้างคำตอบคุณภาพสูง
        # โค้ดนี้เป็นเพียงตัวอย่างการสร้างคำตอบอย่างง่าย
        if "job_title" in data.get("metadata", {}):
            job_title = data.get("metadata", {}).get("job_title", "")
            return f"สำหรับตำแหน่ง {job_title}, จากข้อมูลที่มี ฉันสามารถแนะนำว่า...[คำตอบจะถูกสร้างจาก LLM จริง]"
        else:
            title = data.get("metadata", {}).get("title", "")
            return f"เกี่ยวกับ {title}, ฉันขอแนะนำว่า...[คำตอบจะถูกสร้างจาก LLM จริง]"
    
    def prepare_fine_tune_data(self, num_examples: int = 100) -> str:
        """
        เตรียมข้อมูลสำหรับการทำ fine-tuning
        
        Args:
            num_examples: จำนวนตัวอย่างที่ต้องการสร้าง
            
        Returns:
            พาธของไฟล์ข้อมูลที่สร้าง
        """
        logger.info(f"เริ่มต้นเตรียมข้อมูลสำหรับ fine-tuning ({num_examples} ตัวอย่าง)")
        
        # โหลดข้อมูล
        job_data, career_advice_data = self._load_data()
        
        # สร้าง prompts
        job_prompts = self._generate_prompts_from_job_data(job_data)
        advice_prompts = self._generate_prompts_from_career_advice(career_advice_data)
        
        # รวมและสุ่ม prompts
        all_prompts = job_prompts + advice_prompts
        random.shuffle(all_prompts)
        
        # จำกัดจำนวนตัวอย่าง
        selected_prompts = all_prompts[:num_examples]
        
        # บันทึกไฟล์
        timestamp = asyncio.get_event_loop().time()
        output_file = os.path.join(self.output_dir, f"fine_tune_data_{int(timestamp)}.jsonl")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for prompt in selected_prompts:
                f.write(json.dumps(prompt, ensure_ascii=False) + '\n')
        
        logger.info(f"สร้างข้อมูลสำหรับ fine-tuning สำเร็จ: {len(selected_prompts)} ตัวอย่าง -> {output_file}")
        return output_file
    
    async def start_fine_tuning(self, data_file: str) -> Dict[str, Any]:
        """
        เริ่มกระบวนการ fine-tuning
        
        Args:
            data_file: ไฟล์ข้อมูลสำหรับ fine-tuning
            
        Returns:
            ผลลัพธ์จาก API ในการเริ่ม fine-tuning
        """
        logger.info(f"เริ่มกระบวนการ fine-tuning ด้วยไฟล์ข้อมูล: {data_file}")
        
        # ตรวจสอบไฟล์ข้อมูล
        if not os.path.exists(data_file):
            error_msg = f"ไม่พบไฟล์ข้อมูล: {data_file}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        
        try:
            # อ่านไฟล์ข้อมูล
            with open(data_file, 'r', encoding='utf-8') as f:
                training_data = [json.loads(line) for line in f.readlines()]
            
            logger.info(f"อ่านข้อมูล fine-tuning สำเร็จ: {len(training_data)} ตัวอย่าง")
            
            # สร้าง payload สำหรับ API
            payload = {
                "base_model": LLM_MODEL,
                "training_data": training_data,
                "hyperparameters": {
                    "n_epochs": 3,
                    "batch_size": 4,
                    "learning_rate": 1e-5
                }
            }
            
            # สร้าง headers
            headers = {}
            if LLM_API_KEY:
                headers["Authorization"] = f"Bearer {LLM_API_KEY}"
            
            # ส่งคำขอไปยัง API
            logger.info(f"กำลังส่งคำขอ fine-tuning ไปยัง API: {LLM_API_BASE}")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{LLM_API_BASE}/v1/fine-tunes",  # ปรับ endpoint ตาม API ที่ใช้
                    json=payload,
                    headers=headers,
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"ส่งคำขอ fine-tuning สำเร็จ: {result}")
                    return {"success": True, "data": result}
                else:
                    error_msg = f"เกิดข้อผิดพลาดในการส่งคำขอ fine-tuning: HTTP {response.status_code}, {response.text}"
                    logger.error(error_msg)
                    return {"success": False, "error": error_msg}
        
        except Exception as e:
            error_msg = f"เกิดข้อผิดพลาดในการเริ่ม fine-tuning: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}