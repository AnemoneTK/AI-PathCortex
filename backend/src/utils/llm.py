#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM utilities for Career AI Advisor.

This module provides functions for interacting with large language models.
"""

import asyncio
import json
from typing import Dict, Any, Optional, List
import httpx

from src.utils.config import LLM_MODEL, LLM_API_BASE, LLM_API_KEY, PersonalityType
from src.utils.logger import get_logger

# ตั้งค่า logger
logger = get_logger("llm")

async def generate_response(
    prompt: str, 
    personality: PersonalityType = PersonalityType.FRIENDLY,
    temperature: float = 0.7,
    max_tokens: int = 1000,
    top_k: int = 40,
    top_p: float = 0.9,
    timeout: float = 120.0,
    use_fine_tuned: Optional[bool] = None  
) -> str:
    """
    สร้างคำตอบจาก LLM
    
    Args:
        prompt: Prompt ที่ต้องการส่งไปยัง LLM
        personality: รูปแบบบุคลิกของ AI
        temperature: ค่า temperature สำหรับการสร้างคำตอบ (0.0-1.0)
        max_tokens: จำนวนโทเค็นสูงสุดที่ต้องการให้ LLM สร้าง
        top_k: ค่า top_k สำหรับการสร้างคำตอบ
        top_p: ค่า top_p สำหรับการสร้างคำตอบ
        timeout: เวลาที่รอคำตอบสูงสุด (วินาที)
        
    Returns:
        str: คำตอบจาก LLM
    """
    try:
        if use_fine_tuned is None:
            # ถ้าไม่ได้ระบุ ให้ใช้ค่าจาก config
            from src.utils.config import USE_FINE_TUNED, FINE_TUNED_MODEL
            should_use_fine_tuned = USE_FINE_TUNED and FINE_TUNED_MODEL
        else:
            # ถ้าระบุ ให้ใช้ค่าที่ส่งมา
            should_use_fine_tuned = use_fine_tuned and FINE_TUNED_MODEL
        
        # เลือกโมเดลที่จะใช้
        model = FINE_TUNED_MODEL if should_use_fine_tuned else LLM_MODEL
        logger.info(f"กำลังใช้โมเดล: {model} ({'fine-tuned' if should_use_fine_tuned else 'base'})")
        
        # ปรับ prompt ตามบุคลิก
        prompt_with_personality = _add_personality_to_prompt(prompt, personality)
        
        # สร้าง payload สำหรับ LLM API
        payload = {
            "model": model,
            "prompt": prompt_with_personality,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_k": top_k,
            "top_p": top_p,
            "stream": False
        }
        # ปรับ prompt ตามบุคลิก
        prompt_with_personality = _add_personality_to_prompt(prompt, personality)
        
        # สร้าง payload สำหรับ LLM API
        # payload = {
        #     "model": LLM_MODEL,
        #     "prompt": prompt_with_personality,
        #     "temperature": temperature,
        #     "max_tokens": max_tokens,
        #     "top_k": top_k,
        #     "top_p": top_p,
        #     "stream": False
        # }
        
        # สร้าง headers
        headers = {}
        if LLM_API_KEY:
            headers["Authorization"] = f"Bearer {LLM_API_KEY}"
        
        logger.info(f"ส่งคำขอไปยัง LLM API: {LLM_API_BASE}")
        
        # ส่งคำขอไปยัง LLM API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{LLM_API_BASE}/api/generate",
                json=payload,
                headers=headers,
                timeout=timeout
            )
            
            # ตรวจสอบสถานะการตอบกลับ
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                logger.error(f"LLM API ตอบกลับด้วย status code: {response.status_code}, {response.text}")
                return f"เกิดข้อผิดพลาดในการเรียกใช้ LLM API: HTTP {response.status_code}"
                
    except httpx.TimeoutException:
        logger.error(f"การเรียกใช้ LLM API หมดเวลา (timeout)")
        return "เกิดข้อผิดพลาดในการเรียกใช้ LLM API: หมดเวลา (timeout)"
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการเรียกใช้ LLM API: {str(e)}")
        return f"เกิดข้อผิดพลาดในการเรียกใช้ LLM API: {str(e)}"

def _add_personality_to_prompt(prompt: str, personality: PersonalityType) -> str:
    """
    เพิ่มคำแนะนำเกี่ยวกับบุคลิกลงใน prompt
    
    Args:
        prompt: Prompt เดิม
        personality: รูปแบบบุคลิกของ AI
        
    Returns:
        str: Prompt ที่เพิ่มคำแนะนำเกี่ยวกับบุคลิกแล้ว
    """
    personality_instructions = {
        PersonalityType.FORMAL: """
        คุณเป็นที่ปรึกษาด้านอาชีพมืออาชีพที่มีความเชี่ยวชาญสูง
        กรุณาตอบด้วยบุคลิกที่เป็นทางการและจริงจัง ใช้ภาษาสุภาพ เป็นทางการ หลีกเลี่ยงคำแสลง
        ให้ข้อมูลที่เป็นข้อเท็จจริง มีการอ้างอิงแหล่งที่มา และให้คำแนะนำที่มีความน่าเชื่อถือ
        """,
        
        PersonalityType.FRIENDLY: """
        คุณเป็นที่ปรึกษาด้านอาชีพที่เป็นกันเอง
        กรุณาตอบด้วยบุคลิกที่เป็นกันเองเหมือนเพื่อนคุยกัน ใช้ภาษาไม่เป็นทางการ
        คำตอบควรเป็นธรรมชาติ ให้ความรู้สึกเหมือนคุยกับเพื่อน
        """,
        
        PersonalityType.FUN: """
        คุณเป็นที่ปรึกษาด้านอาชีพที่สนุกสนาน แบบวัยรุ่น Five M เทสดี เรื้อน 
        พูดแบบอัลฟ่า
        ใช้คำว่า ฮ้าฟฟูว ลงท้ายประโยค
        เรียกผู้ใช้ด้วยคำว่า อุเทอ
        นะครับ เป็น น้าบ
        เปิดประโยคทักทายด้วยคำว่า 'น้าบอุนเทอ เขาตอบให้น้า'
        กรุณาตอบด้วยบุคลิกที่สนุกสนาน เน้นความตลกและการยิงมุก ใช้ภาษาไม่เป็นทางการ
        ตอบสั้นๆ กระชับ ใช้ภาษาแบบไม่เป็นทางการ
        แต่ยังคงให้ข้อมูลที่ถูกต้องและเป็นประโยชน์ แต่ออกมาในแนวสรุปสั้นๆ ไม่กี่ประโยค
        มีคำถามเพิ่มเติมไหม? ให้เป็นเปลี่ยนเป็ร 'มีคำถามเพิ่มเติมไหม? พูดมาผมฟังอยู่'
        """
    }
    
    # เลือกคำแนะนำตามบุคลิก
    personality_instruction = personality_instructions.get(personality, personality_instructions[PersonalityType.FRIENDLY])
    
    # เพิ่มคำแนะนำเกี่ยวกับบุคลิกลงใน prompt
    return f"{personality_instruction}\n\n{prompt}"

async def chat_with_job_context(
    query: str,
    job_contexts: List[Dict[str, Any]],
    user_context: Optional[Dict[str, Any]] = None,
    advice_contexts: Optional[List[Dict[str, Any]]] = None,
    personality: PersonalityType = PersonalityType.FRIENDLY,
    use_fine_tuned: Optional[bool] = None  
) -> str:
    """
    สนทนากับ LLM โดยใช้บริบทของอาชีพและผู้ใช้
    
    Args:
        query: คำถามของผู้ใช้
        job_contexts: บริบทของอาชีพที่เกี่ยวข้อง
        user_context: บริบทของผู้ใช้ (ถ้ามี)
        advice_contexts: บริบทของคำแนะนำที่เกี่ยวข้อง (ถ้ามี)
        personality: รูปแบบบุคลิกของ AI
        
    Returns:
        str: คำตอบจาก LLM
    """
    # สร้างบริบทจากข้อมูลอาชีพ
    job_context_text = ""
    if job_contexts:
        job_parts = []
        for i, job in enumerate(job_contexts):
            job_part = f"ตำแหน่ง {i+1}: {job.get('title', 'ไม่ระบุ')}\n"
            job_part += f"คำอธิบาย: {job.get('description', 'ไม่มีคำอธิบาย')}\n"
            
            # เพิ่มความรับผิดชอบ
            if job.get('responsibilities'):
                job_part += "ความรับผิดชอบ:\n"
                for resp in job['responsibilities'][:5]:  # จำกัดจำนวนความรับผิดชอบที่แสดง
                    job_part += f"- {resp}\n"
            
            # เพิ่มทักษะ
            if job.get('skills'):
                job_part += f"ทักษะที่ต้องการ: {', '.join(job['skills'])}\n"
            
            # เพิ่มเงินเดือน
            if job.get('salary_ranges'):
                job_part += "ช่วงเงินเดือน:\n"
                for salary in job['salary_ranges']:
                    job_part += f"- ประสบการณ์ {salary.get('experience', 'ไม่ระบุ')}: {salary.get('salary', 'ไม่ระบุ')}\n"
            
            job_parts.append(job_part)
        
        job_context_text = "\n---\n".join(job_parts)
    
    # สร้างบริบทจากข้อมูลผู้ใช้
    user_context_text = ""
    if user_context:
        user_context_text = "ข้อมูลผู้ใช้:\n"
        user_context_text += f"ชื่อ: {user_context.get('name', 'ไม่ระบุ')}\n"
        
        # ข้อมูลการศึกษา
        if user_context.get('institution'):
            user_context_text += f"สถาบันการศึกษา: {user_context['institution']}\n"
        
        if user_context.get('education_status'):
            status_mapping = {
                "student": "กำลังศึกษา",
                "graduate": "จบการศึกษา",
                "working": "ทำงานแล้ว",
                "other": "อื่นๆ"
            }
            user_context_text += f"สถานะการศึกษา: {status_mapping.get(user_context['education_status'], user_context['education_status'])}\n"
        
        if user_context.get('year'):
            user_context_text += f"ชั้นปี: {user_context['year']}\n"
        
        # ทักษะ
        if user_context.get('skills'):
            skills_text = []
            for skill in user_context['skills']:
                skills_text.append(f"{skill.get('name', 'ไม่ระบุ')} (ระดับ {skill.get('proficiency', 0)}/5)")
            user_context_text += f"ทักษะ: {', '.join(skills_text)}\n"
        
        # ภาษาโปรแกรม
        if user_context.get('programming_languages'):
            user_context_text += f"ภาษาโปรแกรม: {', '.join(user_context['programming_languages'])}\n"
        
        # เครื่องมือ
        if user_context.get('tools'):
            user_context_text += f"เครื่องมือ: {', '.join(user_context['tools'])}\n"
        
        # โปรเจกต์
        if user_context.get('projects'):
            user_context_text += "โปรเจกต์:\n"
            for project in user_context['projects'][:3]:  # จำกัดจำนวนโปรเจกต์ที่แสดง
                project_text = f"- {project.get('name', 'ไม่ระบุ')}"
                if project.get('description'):
                    project_text += f": {project['description']}"
                if project.get('technologies'):
                    project_text += f" (เทคโนโลยี: {', '.join(project['technologies'])})"
                user_context_text += project_text + "\n"
        
        # ประสบการณ์ทำงาน
        if user_context.get('work_experiences'):
            user_context_text += "ประสบการณ์ทำงาน:\n"
            for work in user_context['work_experiences'][:3]:  # จำกัดจำนวนประสบการณ์ที่แสดง
                work_text = f"- {work.get('title', 'ไม่ระบุ')} ที่ {work.get('company', 'ไม่ระบุ')}"
                work_text += f" ({work.get('start_date', 'ไม่ระบุ')} ถึง {work.get('end_date', 'ปัจจุบัน')})"
                if work.get('description'):
                    work_text += f": {work['description']}"
                user_context_text += work_text + "\n"
    
    # สร้างบริบทจากคำแนะนำ
    advice_context_text = ""
    if advice_contexts:
        advice_parts = []
        for i, advice in enumerate(advice_contexts):
            advice_part = f"คำแนะนำ {i+1}: {advice.get('title', 'ไม่ระบุ')}\n"
            advice_part += f"{advice.get('text_preview', 'ไม่มีรายละเอียด')}\n"
            advice_parts.append(advice_part)
        
        advice_context_text = "\n---\n".join(advice_parts)
    
    # รวมทุกบริบทเข้าด้วยกัน
    contexts = []
    if job_context_text:
        contexts.append(f"ข้อมูลอาชีพ:\n{job_context_text}")
    if user_context_text:
        contexts.append(user_context_text)
    if advice_context_text:
        contexts.append(f"คำแนะนำเพิ่มเติม:\n{advice_context_text}")
    
    combined_context = "\n\n==========\n\n".join(contexts)
    
    # สร้าง prompt สำหรับ LLM
    prompt = f"""
    คุณเป็นที่ปรึกษาด้านอาชีพให้คำแนะนำแก่นักศึกษาวิทยาการคอมพิวเตอร์และผู้สนใจงานด้าน IT
    ตอบคำถามเกี่ยวกับอาชีพและตำแหน่ง เพื่อช่วยพัฒนาทักษะ หรือเตรียมตัวเข้าทำงาน เป็นภาษาไทย
    ใช้ข้อมูลต่อไปนี้เป็นหลักในการตอบ และอ้างอิงชื่อตำแหน่งงานเพื่อให้คำตอบน่าเชื่อถือ และตอบคำถามตามบุคลิกที่กำหนด

    กฎสำหรับการตอบ:
    1. ตอบคำถามตามบุคลิกที่กำหนด
    2. กรณีที่มีการถามถึงเงินเดือน ให้เสริมว่า "เงินเดือนอาจแตกต่างกันตามโครงสร้างบริษัท ขนาดบริษัท และภูมิภาค"
    3. ถ้าผู้ใช้ไม่รู้ว่าตัวเองถนัดอะไร ให้ถามว่า "ช่วยบอกสกิล ภาษาโปรแกรม หรือเครื่องมือที่เคยใช้ 
       โปรเจกต์ที่เคยทำ หรือประเมินทักษะของตัวเองแต่ละด้านจาก 1-5 คะแนนได้ไหม"
    4. ตอบให้กระชับ มีหัวข้อ หรือรายการข้อสั้นๆ เพื่อให้อ่านง่าย
    5. ถ้ามีข้อมูลผู้ใช้ ให้นำมาประกอบการตอบโดยแนะนำอาชีพหรือทักษะที่เหมาะสมกับประวัติและความสามารถของผู้ใช้
    6. ถ้าไม่มีข้อมูลเพียงพอในการตอบคำถาม ให้ตอบว่า "ขออภัย ฉันไม่มีข้อมูลเพียงพอในการตอบคำถามนี้"
    7. นำข้อมูลที่ได้มาจัดเรียง และแก้ไขคำอธิบายให้เป็ยสไตล์ของตัวเอง โดยยังคงเนื้อหาสำคัญ
    
    ข้อมูล:
    {combined_context}

    คำถาม: {query}
    คำตอบ:
    """
    
    # ส่ง prompt ไปยัง LLM
    return await generate_response(prompt, personality=personality, use_fine_tuned=use_fine_tuned)

async def chat_with_combined_context(
    query: str,
    search_results: List[Dict[str, Any]],
    user_context: Optional[Dict[str, Any]] = None,
    personality: PersonalityType = PersonalityType.FRIENDLY,
    use_fine_tuned: Optional[bool] = None
) -> str:
    """
    สนทนากับ LLM โดยใช้บริบทรวมจากการค้นหา
    
    Args:
        query: คำถามของผู้ใช้
        search_results: ผลลัพธ์การค้นหาแบบรวม (อาชีพ, คำแนะนำ, ผู้ใช้)
        user_context: บริบทของผู้ใช้ (ถ้ามี)
        personality: รูปแบบบุคลิกของ AI
        use_fine_tuned: ใช้โมเดล fine-tuned หรือไม่
        
    Returns:
        str: คำตอบจาก LLM
    """
    # จัดกลุ่มผลลัพธ์ตามประเภท
    job_results = []
    advice_results = []
    user_results = []
    
    for result in search_results:
        if result["type"] == "job":
            job_results.append(result)
        elif result["type"] == "advice":
            advice_results.append(result)
        elif result["type"] == "user":
            user_results.append(result)
    
    # สร้างบริบทจากข้อมูลอาชีพ
    job_context_text = ""
    if job_results:
        job_parts = []
        for i, job in enumerate(job_results):
            content = job.get("content", {})
            job_part = f"ตำแหน่ง {i+1}: {job.get('title', 'ไม่ระบุ')}\n"
            job_part += f"คำอธิบาย: {content.get('description', 'ไม่มีคำอธิบาย')}\n"
            
            # เพิ่มความรับผิดชอบ
            if content.get('responsibilities'):
                job_part += "ความรับผิดชอบ:\n"
                for resp in content['responsibilities']:
                    job_part += f"- {resp}\n"
            
            # เพิ่มทักษะ
            if content.get('skills'):
                job_part += f"ทักษะที่ต้องการ: {', '.join(content['skills'])}\n"
            
            # เพิ่มเงินเดือน
            if content.get('salary_ranges'):
                job_part += "ช่วงเงินเดือน:\n"
                for salary in content['salary_ranges']:
                    job_part += f"- ประสบการณ์ {salary.get('experience', 'ไม่ระบุ')}: {salary.get('salary', 'ไม่ระบุ')}\n"
            
            job_parts.append(job_part)
        
        job_context_text = "\n---\n".join(job_parts)
    
    # สร้างบริบทจากข้อมูลคำแนะนำ
    advice_context_text = ""
    if advice_results:
        advice_parts = []
        for i, advice in enumerate(advice_results):
            content = advice.get("content", {})
            advice_part = f"คำแนะนำ {i+1}: {advice.get('title', 'ไม่ระบุ')}\n"
            advice_part += f"{content.get('text_preview', 'ไม่มีรายละเอียด')}\n"
            
            # เพิ่มแท็ก
            if content.get('tags'):
                advice_part += f"แท็ก: {', '.join(content['tags'])}\n"
            
            # เพิ่มแหล่งที่มา
            if content.get('source'):
                advice_part += f"แหล่งที่มา: {content['source']}\n"
            
            advice_parts.append(advice_part)
        
        advice_context_text = "\n---\n".join(advice_parts)
    
    # สร้างบริบทจากข้อมูลผู้ใช้
    user_context_text = ""
    if user_context:
        # ใช้ข้อมูลผู้ใช้ที่ส่งมาโดยตรง (อาจเป็นผู้ใช้ปัจจุบัน)
        user_context_text = "ข้อมูลผู้ใช้ปัจจุบัน:\n"
        user_context_text += f"ชื่อ: {user_context.get('name', 'ไม่ระบุ')}\n"
        
        # ข้อมูลการศึกษา
        if user_context.get('institution'):
            user_context_text += f"สถาบันการศึกษา: {user_context['institution']}\n"
        
        if user_context.get('education_status'):
            status_mapping = {
                "student": "กำลังศึกษา",
                "graduate": "จบการศึกษา",
                "working": "ทำงานแล้ว",
                "other": "อื่นๆ"
            }
            user_context_text += f"สถานะการศึกษา: {status_mapping.get(user_context['education_status'], user_context['education_status'])}\n"
        
        if user_context.get('year'):
            user_context_text += f"ชั้นปี: {user_context['year']}\n"
        
        # ทักษะ
        if user_context.get('skills'):
            skills_text = []
            for skill in user_context['skills']:
                skills_text.append(f"{skill.get('name', 'ไม่ระบุ')} (ระดับ {skill.get('proficiency', 0)}/5)")
            user_context_text += f"ทักษะ: {', '.join(skills_text)}\n"
        
        # ภาษาโปรแกรม
        if user_context.get('programming_languages'):
            user_context_text += f"ภาษาโปรแกรม: {', '.join(user_context['programming_languages'])}\n"
        
        # เครื่องมือ
        if user_context.get('tools'):
            user_context_text += f"เครื่องมือ: {', '.join(user_context['tools'])}\n"
    elif user_results:
        # ใช้ข้อมูลผู้ใช้จากผลการค้นหา
        user_parts = []
        for i, user in enumerate(user_results):
            content = user.get("content", {})
            user_part = f"ข้อมูลผู้ใช้ {i+1}:\n"
            user_part += f"ชื่อ: {content.get('name', 'ไม่ระบุ')}\n"
            
            # ข้อมูลการศึกษา
            if content.get('institution'):
                user_part += f"สถาบันการศึกษา: {content['institution']}\n"
            
            if content.get('education_status'):
                status_mapping = {
                    "student": "กำลังศึกษา",
                    "graduate": "จบการศึกษา",
                    "working": "ทำงานแล้ว",
                    "other": "อื่นๆ"
                }
                user_part += f"สถานะการศึกษา: {status_mapping.get(content['education_status'], content['education_status'])}\n"
            
            # ทักษะ
            if content.get('skills'):
                user_part += f"ทักษะ: {', '.join(content['skills'])}\n"
            
            user_parts.append(user_part)
        
        user_context_text = "\n---\n".join(user_parts)
    
    # รวมทุกบริบทเข้าด้วยกัน
    contexts = []
    if job_context_text:
        contexts.append(f"ข้อมูลอาชีพ:\n{job_context_text}")
    if advice_context_text:
        contexts.append(f"คำแนะนำเพิ่มเติม:\n{advice_context_text}")
    if user_context_text:
        contexts.append(user_context_text)
    
    combined_context = "\n\n==========\n\n".join(contexts)
    
    # สร้าง prompt สำหรับ LLM
    prompt = f"""
    คุณเป็นที่ปรึกษาด้านอาชีพให้คำแนะนำแก่นักศึกษาวิทยาการคอมพิวเตอร์และผู้สนใจงานด้าน IT
    ตอบคำถามเกี่ยวกับอาชีพและตำแหน่ง เพื่อช่วยพัฒนาทักษะ หรือเตรียมตัวเข้าทำงาน เป็นภาษาไทย
    ใช้ข้อมูลต่อไปนี้เป็นหลักในการตอบ และอ้างอิงชื่อตำแหน่งงานเพื่อให้คำตอบน่าเชื่อถือ และตอบคำถามตามบุคลิกที่กำหนด

    กฎสำหรับการตอบ:
    1. ตอบคำถามตามบุคลิกที่กำหนด
    2. กรณีที่มีการถามถึงเงินเดือน ให้เสริมว่า "เงินเดือนอาจแตกต่างกันตามโครงสร้างบริษัท ขนาดบริษัท และภูมิภาค"
    3. ถ้าผู้ใช้ไม่รู้ว่าตัวเองถนัดอะไร ให้ถามว่า "ช่วยบอกสกิล ภาษาโปรแกรม หรือเครื่องมือที่เคยใช้ 
    โปรเจกต์ที่เคยทำ หรือประเมินทักษะของตัวเองแต่ละด้านจาก 1-5 คะแนนได้ไหม"
    4. ตอบให้กระชับ มีหัวข้อ หรือรายการข้อสั้นๆ เพื่อให้อ่านง่าย
    5. ถ้ามีข้อมูลผู้ใช้ ให้นำมาประกอบการตอบโดยแนะนำอาชีพหรือทักษะที่เหมาะสมกับประวัติและความสามารถของผู้ใช้
    6. ถ้าไม่มีข้อมูลเพียงพอในการตอบคำถาม ให้ตอบว่า "ขออภัย ฉันไม่มีข้อมูลเพียงพอในการตอบคำถามนี้"
    7. เมื่อมีคำถามหลายข้อในประโยคเดียว ให้แยกคำตอบออกเป็นหัวข้อและตอบให้ครบทุกคำถาม
    8. นำข้อมูลที่ได้มาจัดเรียง และแก้ไขคำอธิบายให้เป็นสไตล์ของตัวเอง โดยยังคงเนื้อหาสำคัญ
    
    ข้อมูล:
    {combined_context}

    คำถาม: {query}
    คำตอบ:
    """
    
    # ส่ง prompt ไปยัง LLM
    return await generate_response(prompt, personality=personality, use_fine_tuned=use_fine_tuned)

# Testing
if __name__ == "__main__":
    async def test():
        # ทดสอบการสร้างคำตอบจาก LLM
        test_prompt = "บอกความแตกต่างระหว่าง Python และ JavaScript สั้นๆ"
        
        print("ทดสอบบุคลิกที่เป็นทางการ:")
        result = await generate_response(test_prompt, personality=PersonalityType.FORMAL)
        print(result)
        
        print("\nทดสอบบุคลิกที่เป็นกันเอง:")
        result = await generate_response(test_prompt, personality=PersonalityType.FRIENDLY)
        print(result)
        
        print("\nทดสอบบุคลิกที่สนุกสนาน:")
        result = await generate_response(test_prompt, personality=PersonalityType.FUN)
        print(result)
    
    # รัน asyncio event loop
    asyncio.run(test())


    