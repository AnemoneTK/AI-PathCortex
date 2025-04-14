#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM utilities for Career AI Advisor.

This module provides functions for interacting with large language models.
"""

import asyncio
import json
from typing import Dict, Any, Optional, List, Union
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
    use_fine_tuned: Optional[bool] = None,
    user_context: Optional[Dict[str, Any]] = None 
) -> str:
    """
    สร้างคำตอบจาก LLM
    
    Args:...
    """
    try:
        # ตรวจสอบว่าใช้ fine-tuned model หรือไม่
        if use_fine_tuned is None:
            from src.utils.config import USE_FINE_TUNED, FINE_TUNED_MODEL
            should_use_fine_tuned = USE_FINE_TUNED and FINE_TUNED_MODEL
        else:
            should_use_fine_tuned = use_fine_tuned and FINE_TUNED_MODEL
        
        # เลือกโมเดลที่จะใช้
        model = FINE_TUNED_MODEL if should_use_fine_tuned else LLM_MODEL
        
        # เพิ่ม logging ตรงนี้
        print(f"==== LLM DETAILS ====")
        print(f"Using model: {model} ({'fine-tuned' if should_use_fine_tuned else 'base'})")
        print(f"Personality: {personality}")
        print(f"User data available: {'Yes' if user_context else 'No'}")
        if user_context:
            print(f"User: {user_context.get('name', 'Unknown')}")
            print(f"Skills: {[s.get('name', '') for s in user_context.get('skills', [])]}")
        print(f"=====================")
        
        logger.info(f"กำลังใช้โมเดล: {model} ({'fine-tuned' if should_use_fine_tuned else 'base'})")
        
        
        # เพิ่มข้อมูลผู้ใช้ลงในคำถาม (ถ้ามี)
        enhanced_prompt = prompt
        if user_context:
            user_name = user_context.get('name', '')
            user_skills = []
            
            # รวบรวมทักษะของผู้ใช้
            if 'skills' in user_context and isinstance(user_context['skills'], list):
                for skill in user_context['skills']:
                    if isinstance(skill, dict):
                        skill_name = skill.get('name', '')
                        proficiency = skill.get('proficiency', 0)
                        if skill_name:
                            user_skills.append(f"{skill_name} (ระดับ {proficiency}/5)")
                    elif isinstance(skill, str):
                        user_skills.append(skill)
            
            # รวบรวมภาษาโปรแกรมที่ผู้ใช้รู้
            user_languages = user_context.get('programming_languages', [])
            
            # สร้างข้อมูลผู้ใช้เพิ่มเติม
            user_info = f"""
ข้อมูลผู้ใช้:
ชื่อ: {user_name}
"""
            if 'institution' in user_context and user_context['institution']:
                user_info += f"สถาบัน: {user_context['institution']}\n"
            
            if 'education_status' in user_context and user_context['education_status']:
                user_info += f"สถานะการศึกษา: {user_context['education_status']}\n"
            
            if user_skills:
                user_info += f"ทักษะ: {', '.join(user_skills)}\n"
            
            if user_languages:
                user_info += f"ภาษาโปรแกรม: {', '.join(user_languages)}\n"
            
            # เพิ่มข้อมูลผู้ใช้ลงในคำถาม
            enhanced_prompt = f"{enhanced_prompt}\n\n{user_info}"
        
        # ปรับ prompt ตามบุคลิก
        prompt_with_personality = _add_personality_to_prompt(enhanced_prompt, personality)
        
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
        
        # สร้าง headers
        headers = {}
        if LLM_API_KEY:
            headers["Authorization"] = f"Bearer {LLM_API_KEY}"
        
        # เรียกใช้ LLM API
        result = await _call_llm_api(payload, headers, timeout)
        
        # ตรวจสอบคำตอบจาก API และปรับแต่งตามบุคลิก
        api_response = result.get("response", "")
        formatted_response = _format_answer_with_personality(api_response, user_context, personality)
        
        return formatted_response
                
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
        ใช้รูปแบบการนำเสนอที่มีโครงสร้างชัดเจน มีหัวข้อหลัก หัวข้อย่อย เรียงลำดับเป็นขั้นตอน
        ใช้คำทักทายและลงท้ายอย่างสุภาพ เช่น "เรียนผู้สอบถาม" หรือ "ด้วยความเคารพ"
        หากมีข้อมูลผู้ใช้ ให้ใช้คำว่า "ท่าน" เมื่อกล่าวถึงผู้ใช้ และเน้นทักษะหรือความรู้ทีผู้ใช้มีเมื่อให้คำแนะนำ
        """,
        
        PersonalityType.FRIENDLY: """
        คุณเป็นที่ปรึกษาด้านอาชีพที่เป็นกันเอง
        กรุณาตอบด้วยบุคลิกที่เป็นกันเองเหมือนเพื่อนคุยกัน ใช้ภาษาไม่เป็นทางการ
        คำตอบควรเป็นธรรมชาติ ให้ความรู้สึกเหมือนคุยกับเพื่อน
        ใช้คำว่า "เธอ" หรือ "คุณ" แทนการใช้สรรพนามทางการ
        ใช้ตัวอย่างที่เข้าใจง่าย ยกตัวอย่างประสบการณ์จริง
        ถ้ามีข้อมูลผู้ใช้ ให้เรียกชื่อของผู้ใช้โดยตรง และพูดคุยแบบเพื่อนที่เข้าใจความถนัดของเขา โดยอ้างอิงถึงทักษะหรือประสบการณ์ที่เขามี
        ถามคำถามเป็นระยะเพื่อให้เกิดการมีส่วนร่วมในการสนทนา
        """,
        
        PersonalityType.FUN: """
        คุณเป็นที่ปรึกษาด้านอาชีพที่สนุกสนาน แบบวัยรุ่น Five M เทสดี 
        พูดแบบอัลฟ่า
        ใช้คำว่า ฮ้าฟฟูว ลงท้ายประโยค
        เรียกผู้ใช้ด้วยคำว่า อุเทอ
        นะครับ เป็น น้าบ
        เปิดประโยคทักทายด้วยคำว่า 'น้าบอุเทอ เขาตอบให้น้า'
        กรุณาตอบด้วยบุคลิกที่สนุกสนาน เน้นความตลกและการยิงมุก ใช้ภาษาไม่เป็นทางการ
        ตอบสั้นๆ กระชับ ใช้ภาษาแบบไม่เป็นทางการ
        แต่ยังคงให้ข้อมูลที่ถูกต้องและเป็นประโยชน์ แต่ออกมาในแนวสรุปสั้นๆ ไม่กี่ประโยค
        ถ้ามีข้อมูลผู้ใช้ ให้เรียกชื่อเขาและชื่นชมทักษะที่เขามีอย่างจี๊ดๆ
        ใช้อิโมจิเพิ่มความน่าสนใจ 🔥 และจัดรูปแบบให้ทันสมัย
        มีคำถามเพิ่มเติมไหม? ให้เป็นเปลี่ยนเป็น 'มีคำถามเพิ่มเติมไหม? พูดมาผมฟังอยู่'
        """
    }
    
    # เพิ่ม logging ตรงนี้
    print(f"==== PERSONALITY APPLIED ====")
    print(f"Using personality: {personality}")
    print(f"Instructions applied: {personality_instructions[personality][:100]}...")
    print(f"============================")
    
    resume_keywords = ["resume", "เรซูเม่", "เรซูเม", "cv", "ประวัติ", "สมัครงาน"]
    is_resume_question = any(keyword in prompt.lower() for keyword in resume_keywords)

    # เลือกคำแนะนำตามบุคลิก
    personality_instruction = personality_instructions.get(personality, personality_instructions[PersonalityType.FRIENDLY])
    
    if is_resume_question:
        if personality == PersonalityType.FORMAL:
            personality_instruction += "\nสำหรับคำถามเกี่ยวกับการเตรียม Resume นี้ กรุณาให้คำแนะนำที่ละเอียด ครบถ้วน และเป็นระบบ"
        elif personality == PersonalityType.FRIENDLY:
            personality_instruction += "\nเห็นว่าถามเกี่ยวกับ Resume นะ ให้คำแนะนำแบบเพื่อนที่เคยทำงานมาก่อน ให้ทิปส์เด็ดๆ เล่าประสบการณ์จริง"
        elif personality == PersonalityType.FUN:
            personality_instruction += "\nเห็นถามเรื่อง Resume ก็ต้องตอบให้เทสสุดๆ เน้นเคล็ดลับแบบเอาไปใช้ได้เลย"
    
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
    """
    # เพิ่มข้อมูลการแสดงผล
    print(f"==== CONTEXT INFO ====")
    print(f"Query: {query}")
    print(f"Job contexts available: {len(job_contexts)}")
    print(f"User context available: {'Yes' if user_context else 'No'}")
    if user_context:
        print(f"User: {user_context.get('name', 'Unknown')}")
    print(f"Advice contexts available: {len(advice_contexts) if advice_contexts else 0}")
    print(f"Using fine-tuned model: {'Yes' if use_fine_tuned else 'No'}")
    print(f"Personality: {personality}")
    print(f"=====================")

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
    return await generate_response(prompt, personality=personality, use_fine_tuned=use_fine_tuned, user_context=user_context)

async def chat_with_combined_context(
    query: str,
    search_results: Union[List[Dict[str, Any]], List[str]],
    user_context: Optional[Dict[str, Any]] = None,
    personality: PersonalityType = PersonalityType.FRIENDLY,
    use_fine_tuned: Optional[bool] = None
) -> str:
    """
    สนทนากับ LLM โดยใช้บริบทรวมจากการค้นหา
    """
    # เพิ่มตรงนี้
    if search_results and isinstance(search_results[0], str):
        search_results = [json.loads(result) for result in search_results]
    print("==== DEBUG INFO ====")
    print(f"Type of search_results: {type(search_results)}")
    if search_results:
        print(f"Type of first result: {type(search_results[0])}")
        print(f"First result: {search_results[0][:100] if isinstance(search_results[0], str) else str(search_results[0])[:100]}...")
    print("====================")

    # เพิ่ม defensive code
    if search_results and all(isinstance(result, str) for result in search_results):
        try:
            search_results = [json.loads(result) for result in search_results]
            print("Converted string results to dictionaries")
        except Exception as e:
            print(f"Error converting string results: {e}")

    print(f"==== COMBINED CONTEXT INFO ====")
    print(f"Query: {query}")
    print(f"Search results available: {len(search_results)}")
    print(f"User context available: {'Yes' if user_context else 'No'}")
    if user_context:
        print(f"User: {user_context.get('name', 'Unknown')}")
    print(f"Using fine-tuned model: {'Yes' if use_fine_tuned else 'No'}")
    print(f"Personality: {personality}")
    
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
    
    print(f"Job results: {len(job_results)}")
    print(f"Advice results: {len(advice_results)}")
    print(f"User results: {len(user_results)}")
    print(f"=============================")
    
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
    
    # สร้าง prompt พื้นฐานสำหรับ LLM
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
    9. ถ้ามีข้อมูลผู้ใช้ ให้ปรับแต่งคำตอบให้สอดคล้องกับชื่อ ทักษะ และความเชี่ยวชาญของผู้ใช้ ใช้ชื่อผู้ใช้ในคำทักทาย
    10. ถ้ามีข้อมูลเกี่ยวกับภาษาโปรแกรมที่ผู้ใช้ถนัด ให้เน้นแนะนำอาชีพที่ใช้ภาษาเหล่านั้น
    """
    
    # ตรวจสอบหาคำเกี่ยวกับ resume และอาชีพในคำถาม
    resume_keywords = ["resume", "เรซูเม่", "เรซูเม", "cv", "ประวัติ", "สมัครงาน"]
    is_resume_question = any(keyword in query.lower() for keyword in resume_keywords)

    # ตรวจสอบหาคำเกี่ยวกับอาชีพใน query
    job_keywords = ["developer", "programmer", "engineer", "fullstack", "full stack", "frontend", "backend"]
    job_name = next((kw for kw in job_keywords if kw in query.lower()), None)

    # ตรวจสอบคำถามเกี่ยวกับเงินเดือน
    salary_keywords = ["เงินเดือน", "salary", "รายได้", "ค่าตอบแทน"]
    is_salary_question = any(keyword in query.lower() for keyword in salary_keywords)

    if user_context:
        user_name = user_context.get('name', '')
        user_skills = []
        
        # รวบรวมทักษะของผู้ใช้
        if 'skills' in user_context and isinstance(user_context['skills'], list):
            for skill in user_context['skills']:
                if isinstance(skill, dict):
                    skill_name = skill.get('name', '')
                    if skill_name:
                        user_skills.append(skill_name)
        
        # รวบรวมภาษาโปรแกรมที่ผู้ใช้รู้
        user_languages = user_context.get('programming_languages', [])
        
        # เพิ่มคำแนะนำเฉพาะสำหรับผู้ใช้นี้
        prompt += f"\n11. ใช้ชื่อ '{user_name}' เมื่อทักทาย ตามรูปแบบที่เหมาะสมกับบุคลิก"
        
        if user_skills:
            prompt += f"\n12. ผู้ใช้มีทักษะด้าน {', '.join(user_skills)} ให้แนะนำการต่อยอดจากทักษะเหล่านี้"
        
        if user_languages:
            prompt += f"\n13. ผู้ใช้เชี่ยวชาญภาษา {', '.join(user_languages)} ให้แนะนำการพัฒนาต่อยอดจากภาษาเหล่านี้"

    # ปรับ prompt ตามประเภทคำถาม
    if is_resume_question and job_name and is_salary_question:
        # คำถามเกี่ยวกับทั้งรายละเอียดงาน เงินเดือน และการเตรียม resume
        prompt += f"\nคำถามนี้ถามเกี่ยวกับงาน {job_name}, เงินเดือน, และการเตรียม resume"
        prompt += f"\nกรุณาให้คำตอบที่ครอบคลุมทั้งหน้าที่งาน {job_name}, ช่วงเงินเดือน, และคำแนะนำในการเตรียม resume สำหรับตำแหน่งนี้โดยเฉพาะ"
        prompt += f"\nแยกคำตอบออกเป็นหัวข้อชัดเจน"
    elif is_resume_question and job_name:
        # คำถามเกี่ยวกับทั้งรายละเอียดงานและการเตรียม resume
        prompt += f"\nคำถามนี้ถามเกี่ยวกับงาน {job_name} และการเตรียม resume"
        prompt += f"\nกรุณาให้คำตอบที่ครอบคลุมทั้งหน้าที่งาน {job_name} และคำแนะนำในการเตรียม resume สำหรับตำแหน่งนี้โดยเฉพาะ"
        prompt += f"\nแยกคำตอบออกเป็นหัวข้อชัดเจน"
    elif job_name and is_salary_question:
        # คำถามเกี่ยวกับทั้งรายละเอียดงานและเงินเดือน
        prompt += f"\nคำถามนี้ถามเกี่ยวกับงาน {job_name} และเงินเดือน"
        prompt += f"\nกรุณาให้คำตอบที่ครอบคลุมทั้งหน้าที่งาน {job_name} และช่วงเงินเดือนโดยประมาณ"
    elif is_resume_question and is_salary_question:
        # คำถามเกี่ยวกับทั้งเงินเดือนและการเตรียม resume
        prompt += f"\nคำถามนี้ถามเกี่ยวกับเงินเดือนและการเตรียม resume"
        prompt += f"\nกรุณาให้คำตอบที่ครอบคลุมทั้งช่วงเงินเดือนและคำแนะนำในการเตรียม resume"
    elif job_name:
        # คำถามเกี่ยวกับเฉพาะรายละเอียดงาน
        prompt += f"\nคำถามนี้ถามเกี่ยวกับงาน {job_name}"
        prompt += f"\nกรุณาให้คำตอบที่ครอบคลุมรายละเอียดงาน {job_name} อย่างชัดเจน"
    elif is_resume_question:
        # คำถามเกี่ยวกับเฉพาะการเตรียม resume
        prompt += "\nคำถามนี้ถามเกี่ยวกับการเตรียม resume"
        prompt += "\nกรุณาให้คำแนะนำที่เป็นประโยชน์และเฉพาะเจาะจงในการเตรียม resume"
    elif is_salary_question:
        # คำถามเกี่ยวกับเฉพาะเงินเดือน
        prompt += "\nคำถามนี้ถามเกี่ยวกับเงินเดือน"
        prompt += "\nกรุณาให้ข้อมูลช่วงเงินเดือนโดยประมาณ และแนะนำว่าเงินเดือนอาจแตกต่างกันตามโครงสร้างบริษัท ขนาดบริษัท และภูมิภาค"
    
    # เพิ่มบริบทและคำถาม
    prompt += f"""
    
    ข้อมูล:
    {combined_context}

    คำถาม: {query}
    คำตอบ:
    """
    
    # ส่ง prompt ไปยัง LLM
    return await generate_response(prompt, personality=personality, use_fine_tuned=use_fine_tuned, user_context=user_context)


def _format_answer_with_personality(response: str, user_context: Optional[Dict[str, Any]], personality: PersonalityType) -> str:
    """
    ปรับแต่งคำตอบให้เข้ากับบุคลิกและข้อมูลผู้ใช้
    
    Args:
        response: คำตอบจาก LLM
        user_context: ข้อมูลผู้ใช้ (ถ้ามี)
        personality: บุคลิกของ AI
        
    Returns:
        str: คำตอบที่ปรับแต่งแล้ว
    """
    # ถ้าไม่มีข้อมูลผู้ใช้ ส่งคืนคำตอบเดิม
    if not user_context:
        return response
    
    user_name = user_context.get('name', '')
    if not user_name:
        return response
    
    # ถ้ามีชื่อผู้ใช้ ให้ปรับการทักทายตามบุคลิก
    if personality == PersonalityType.FORMAL:
        # ตรวจสอบว่ามีการทักทายหรือไม่
        if not any(greeting in response[:50].lower() for greeting in ["เรียน", "สวัสดี", "ขอความเคารพ"]):
            return f"เรียน คุณ{user_name}\n\n{response}"
    
    elif personality == PersonalityType.FRIENDLY:
        # ตรวจสอบว่ามีการทักทายหรือไม่
        if not any(greeting in response[:30].lower() for greeting in ["สวัสดี", "หวัดดี", "ฮัลโหล"]):
            return f"สวัสดี {user_name}! \n\n{response}"
    
    elif personality == PersonalityType.FUN:
        # ตรวจสอบว่ามีการทักทายแบบ FUN หรือไม่
        if "น้าบอุเทอ" not in response[:50]:
            return f"น้าบอุเทอ {user_name} เขาตอบให้น้า! \n\n{response}"
    
    return response
# เพิ่มฟังก์ชัน: src/utils/llm.py


async def _call_llm_api(payload: Dict[str, Any], headers: Dict[str, str], timeout: float) -> Dict[str, Any]:
    """
    เรียกใช้ LLM API
    
    Args:
        payload: ข้อมูลที่ส่งไปยัง API
        headers: headers สำหรับ HTTP request
        timeout: เวลาที่รอคำตอบสูงสุด (วินาที)
        
    Returns:
        Dict[str, Any]: ผลลัพธ์จาก API
    """
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
            return result
        else:
            logger.error(f"LLM API ตอบกลับด้วย status code: {response.status_code}, {response.text}")
            return {"response": f"เกิดข้อผิดพลาดในการเรียกใช้ LLM API: HTTP {response.status_code}"}
        
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


    