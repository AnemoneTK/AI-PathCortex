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
import logging

# ตั้งค่า logger สำหรับไฟล์นี้โดยเฉพาะ
from src.utils.logger import get_logger
logger = get_logger("llm")

# ฟังก์ชันใหม่สำหรับการสนทนากับ LLM
async def safe_chat_with_context(
    query: str,
    search_results: Optional[List[Dict[str, Any]]] = None,
    user_context: Optional[Dict[str, Any]] = None,
    personality: str = "friendly",
    use_fine_tuned: bool = False,
    llm_api_base: Optional[str] = None,
    llm_api_key: Optional[str] = None,
    llm_model: Optional[str] = None,
) -> str:
    """
    ฟังก์ชันปลอดภัยสำหรับสนทนากับ LLM โดยใช้บริบทที่กำหนด
    
    Args:
        query: คำถามจากผู้ใช้
        search_results: ผลลัพธ์การค้นหาข้อมูลที่เกี่ยวข้อง (ถ้ามี)
        user_context: ข้อมูลผู้ใช้ (ถ้ามี)
        personality: บุคลิกของ AI (formal, friendly, fun)
        use_fine_tuned: ใช้โมเดล fine-tuned หรือไม่
        llm_api_base: URL ของ LLM API
        llm_api_key: API key สำหรับ LLM
        llm_model: ชื่อโมเดล LLM
        
    Returns:
        str: คำตอบจาก LLM
    """
    # นำเข้าค่าคอนฟิกถ้าไม่ได้ระบุ
    if llm_api_base is None or llm_api_key is None or llm_model is None:
        try:
            from src.utils.config import LLM_API_BASE, LLM_API_KEY, LLM_MODEL, FINE_TUNED_MODEL, USE_FINE_TUNED
            llm_api_base = llm_api_base or LLM_API_BASE
            llm_api_key = llm_api_key or LLM_API_KEY
            llm_model = llm_model or (FINE_TUNED_MODEL if use_fine_tuned and USE_FINE_TUNED else LLM_MODEL)
        except ImportError:
            # ถ้าไม่สามารถนำเข้าได้ ใช้ค่าดีฟอลต์
            llm_api_base = llm_api_base or "http://host.docker.internal:11434"
            llm_api_key = llm_api_key or ""
            llm_model = llm_model or "llama3.1:latest"
    
    # สร้างคำแนะนำบุคลิกตามประเภท
    personality_instructions = get_personality_instructions(personality)
    
    # สร้างบริบทจากข้อมูลการค้นหา
    context_text = build_search_context(search_results)
    
    # สร้างบริบทจากข้อมูลผู้ใช้
    user_context_text = build_user_context(user_context)
    
    # รวมบริบททั้งหมด
    combined_context = "\n\n==========\n\n".join(filter(None, [context_text, user_context_text]))
    
    # สร้าง prompt พื้นฐานสำหรับ LLM
    prompt = f"""
    คุณเป็นที่ปรึกษาด้านอาชีพให้คำแนะนำแก่นักศึกษาวิทยาการคอมพิวเตอร์และผู้สนใจงานด้าน IT
    ตอบคำถามเกี่ยวกับอาชีพและตำแหน่ง เพื่อช่วยพัฒนาทักษะ หรือเตรียมตัวเข้าทำงาน เป็นภาษาไทย
    ใช้ข้อมูลต่อไปนี้เป็นหลักในการตอบ และอ้างอิงชื่อตำแหน่งงานเพื่อให้คำตอบน่าเชื่อถือ และตอบคำถามตามบุคลิกที่กำหนด

    {personality_instructions}

    กฎสำหรับการตอบ:
    1. ตอบคำถามตามบุคลิกที่กำหนด
    2. กรณีที่มีการถามถึงเงินเดือน ให้เสริมว่า "เงินเดือนอาจแตกต่างกันตามโครงสร้างบริษัท ขนาดบริษัท และภูมิภาค"
    3. ถ้าผู้ใช้ไม่รู้ว่าตัวเองถนัดอะไร ให้ถามว่า "ช่วยบอกสกิล ภาษาโปรแกรม หรือเครื่องมือที่เคยใช้ 
       โปรเจกต์ที่เคยทำ หรือประเมินทักษะของตัวเองแต่ละด้านจาก 1-5 คะแนนได้ไหม"
    4. ตอบให้กระชับ มีหัวข้อ หรือรายการข้อสั้นๆ เพื่อให้อ่านง่าย
    5. ถ้ามีข้อมูลผู้ใช้ ให้นำมาประกอบการตอบโดยแนะนำอาชีพหรือทักษะที่เหมาะสมกับประวัติและความสามารถของผู้ใช้
    6. ถ้าไม่มีข้อมูลเพียงพอในการตอบคำถาม ให้ตอบว่า "ขออภัย ฉันไม่มีข้อมูลเพียงพอในการตอบคำถามนี้"
    7. นำข้อมูลที่ได้มาจัดเรียง และแก้ไขคำอธิบายให้เป็นสไตล์ของตัวเอง โดยยังคงเนื้อหาสำคัญ
    """
    
    # ตรวจสอบคำถามเพื่อปรับ prompt ให้เหมาะสม
    prompt = customize_prompt_for_query(prompt, query, user_context)
    
    # เพิ่มบริบทและคำถาม
    prompt += f"""
    
    ข้อมูล:
    {combined_context}

    คำถาม: {query}
    คำตอบ:
    """
    
    # ส่ง prompt ไปยัง LLM
    try:
        response = await call_llm_api(
            prompt=prompt,
            model=llm_model,
            api_base=llm_api_base,
            api_key=llm_api_key
        )
        
        # ตกแต่งคำตอบตามบุคลิกหากจำเป็น
        response = format_response_with_personality(response, user_context, personality)
        
        return response
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการเรียกใช้ LLM API: {str(e)}")
        # คำตอบฉุกเฉินในกรณีที่ LLM ไม่ตอบสนอง
        return f"ขออภัย เกิดข้อผิดพลาดในระบบ ไม่สามารถตอบคำถามได้ในขณะนี้ โปรดลองใหม่ภายหลัง"

def get_personality_instructions(personality: str) -> str:
    """
    สร้างคำแนะนำสำหรับบุคลิกที่กำหนด
    
    Args:
        personality: บุคลิกของ AI
        
    Returns:
        str: คำแนะนำสำหรับบุคลิก
    """
    personality_instructions = {
        "formal": """
        คุณเป็นที่ปรึกษาด้านอาชีพมืออาชีพที่มีความเชี่ยวชาญสูง
        กรุณาตอบด้วยบุคลิกที่เป็นทางการและจริงจัง ใช้ภาษาสุภาพ เป็นทางการ หลีกเลี่ยงคำแสลง
        ให้ข้อมูลที่เป็นข้อเท็จจริง มีการอ้างอิงแหล่งที่มา และให้คำแนะนำที่มีความน่าเชื่อถือ
        ใช้รูปแบบการนำเสนอที่มีโครงสร้างชัดเจน มีหัวข้อหลัก หัวข้อย่อย เรียงลำดับเป็นขั้นตอน
        ใช้คำทักทายและลงท้ายอย่างสุภาพ เช่น "เรียนผู้สอบถาม" หรือ "ด้วยความเคารพ"
        หากมีข้อมูลผู้ใช้ ให้ใช้คำว่า "ท่าน" เมื่อกล่าวถึงผู้ใช้ และเน้นทักษะหรือความรู้ทีผู้ใช้มีเมื่อให้คำแนะนำ
        """,
        
        "friendly": """
        คุณเป็นที่ปรึกษาด้านอาชีพที่เป็นกันเอง
        กรุณาตอบด้วยบุคลิกที่เป็นกันเองเหมือนเพื่อนคุยกัน ใช้ภาษาไม่เป็นทางการ
        คำตอบควรเป็นธรรมชาติ ให้ความรู้สึกเหมือนคุยกับเพื่อน
        ใช้คำว่า "เธอ" หรือ "คุณ" แทนการใช้สรรพนามทางการ
        ใช้ตัวอย่างที่เข้าใจง่าย ยกตัวอย่างประสบการณ์จริง
        ถ้ามีข้อมูลผู้ใช้ ให้เรียกชื่อของผู้ใช้โดยตรง และพูดคุยแบบเพื่อนที่เข้าใจความถนัดของเขา โดยอ้างอิงถึงทักษะหรือประสบการณ์ที่เขามี
        ถามคำถามเป็นระยะเพื่อให้เกิดการมีส่วนร่วมในการสนทนา
        """,
        
        "fun": """
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
    
    # ให้ใช้บุคลิกเป็นมิตรถ้าไม่พบบุคลิกที่ระบุ
    return personality_instructions.get(personality.lower(), personality_instructions["friendly"])

def build_search_context(search_results: Optional[List[Dict[str, Any]]]) -> str:
    """
    สร้างบริบทจากผลการค้นหา
    
    Args:
        search_results: ผลลัพธ์การค้นหา
        
    Returns:
        str: บริบทที่สร้างขึ้น
    """
    if not search_results:
        return ""

    # แยกผลลัพธ์ตามประเภท
    job_results = []
    advice_results = []

    for result in search_results:
        if isinstance(result, dict):
            result_type = result.get("type", "")
            if result_type == "job":
                job_results.append(result)
            elif result_type == "advice":
                advice_results.append(result)
    
    # สร้างบริบทจากข้อมูลอาชีพ
    job_context_text = ""
    if job_results:
        job_parts = []
        for i, job in enumerate(job_results):
            content = job.get("content", {})
            title = job.get("title", "ไม่ระบุ")
            
            # ตรวจสอบว่า content เป็น dictionary หรือไม่
            if not isinstance(content, dict):
                content = {}
            
            job_part = f"ตำแหน่ง {i+1}: {title}\n"
            
            # เพิ่มคำอธิบาย
            description = content.get("description", "")
            if description:
                job_part += f"คำอธิบาย: {description}\n"
            
            # เพิ่มความรับผิดชอบ
            responsibilities = content.get("responsibilities", [])
            if responsibilities and isinstance(responsibilities, list):
                job_part += "ความรับผิดชอบ:\n"
                for resp in responsibilities:
                    job_part += f"- {resp}\n"
            
            # เพิ่มทักษะ
            skills = content.get("skills", [])
            if skills and isinstance(skills, list):
                job_part += f"ทักษะที่ต้องการ: {', '.join(skills)}\n"
            
            # เพิ่มเงินเดือน
            salary_ranges = content.get("salary_ranges", [])
            if salary_ranges and isinstance(salary_ranges, list):
                job_part += "ช่วงเงินเดือน:\n"
                for salary in salary_ranges:
                    if isinstance(salary, dict):
                        job_part += f"- ประสบการณ์ {salary.get('experience', 'ไม่ระบุ')}: {salary.get('salary', 'ไม่ระบุ')}\n"
            
            job_parts.append(job_part)
        
        job_context_text = "\n---\n".join(job_parts)
    
    # สร้างบริบทจากข้อมูลคำแนะนำ
    advice_context_text = ""
    if advice_results:
        advice_parts = []
        for i, advice in enumerate(advice_results):
            content = advice.get("content", {})
            title = advice.get("title", "ไม่ระบุ")
            
            # ตรวจสอบว่า content เป็น dictionary หรือไม่
            if not isinstance(content, dict):
                content = {}
            
            advice_part = f"คำแนะนำ {i+1}: {title}\n"
            advice_part += f"{content.get('text_preview', 'ไม่มีรายละเอียด')}\n"
            
            # เพิ่มแท็ก
            tags = content.get("tags", [])
            if tags and isinstance(tags, list):
                advice_part += f"แท็ก: {', '.join(tags)}\n"
            
            # เพิ่มแหล่งที่มา
            source = content.get("source", "")
            if source:
                advice_part += f"แหล่งที่มา: {source}\n"
            
            advice_parts.append(advice_part)
        
        advice_context_text = "\n---\n".join(advice_parts)
    
    # รวมบริบทเข้าด้วยกัน
    contexts = []
    if job_context_text:
        contexts.append(f"ข้อมูลอาชีพ:\n{job_context_text}")
    if advice_context_text:
        contexts.append(f"คำแนะนำเพิ่มเติม:\n{advice_context_text}")
    
    return "\n\n==========\n\n".join(contexts)

def build_user_context(user_context: Optional[Dict[str, Any]]) -> str:
    """
    สร้างบริบทจากข้อมูลผู้ใช้
    
    Args:
        user_context: ข้อมูลผู้ใช้
        
    Returns:
        str: บริบทผู้ใช้ที่สร้างขึ้น
    """
    if not user_context:
        return ""
    
    user_context_text = "ข้อมูลผู้ใช้ปัจจุบัน:\n"
    
    # ข้อมูลพื้นฐาน
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
        edu_status = user_context['education_status']
        if isinstance(edu_status, str):
            user_context_text += f"สถานะการศึกษา: {status_mapping.get(edu_status, edu_status)}\n"
    
    if user_context.get('year'):
        user_context_text += f"ชั้นปี: {user_context['year']}\n"
    
    # ทักษะ
    if user_context.get('skills'):
        skills_text = []
        if isinstance(user_context['skills'], list):
            for skill in user_context['skills']:
                if isinstance(skill, dict) and 'name' in skill:
                    proficiency = skill.get('proficiency', 0)
                    skills_text.append(f"{skill['name']} (ระดับ {proficiency}/5)")
                elif isinstance(skill, str):
                    skills_text.append(skill)
        
        if skills_text:
            user_context_text += f"ทักษะ: {', '.join(skills_text)}\n"
    
    # ภาษาโปรแกรม
    if user_context.get('programming_languages'):
        prog_langs = []
        if isinstance(user_context['programming_languages'], list):
            for lang in user_context['programming_languages']:
                if isinstance(lang, dict) and 'name' in lang:
                    proficiency = lang.get('proficiency', 0)
                    prog_langs.append(f"{lang['name']} (ระดับ {proficiency}/5)")
                elif isinstance(lang, str):
                    prog_langs.append(lang)
        
        if prog_langs:
            user_context_text += f"ภาษาโปรแกรม: {', '.join(prog_langs)}\n"
    
    # เครื่องมือ
    if user_context.get('tools'):
        tools_text = []
        if isinstance(user_context['tools'], list):
            for tool in user_context['tools']:
                if isinstance(tool, dict) and 'name' in tool:
                    proficiency = tool.get('proficiency', 0)
                    tools_text.append(f"{tool['name']} (ระดับ {proficiency}/5)")
                elif isinstance(tool, str):
                    tools_text.append(tool)
        
        if tools_text:
            user_context_text += f"เครื่องมือ: {', '.join(tools_text)}\n"
    
    # โปรเจกต์
    if user_context.get('projects'):
        if isinstance(user_context['projects'], list) and user_context['projects']:
            user_context_text += "โปรเจกต์:\n"
            for project in user_context['projects'][:3]:  # จำกัดจำนวนโปรเจกต์ที่แสดง
                if isinstance(project, dict):
                    project_name = project.get('name', 'ไม่ระบุ')
                    project_text = f"- {project_name}"
                    
                    if project.get('description'):
                        project_text += f": {project['description']}"
                    
                    if project.get('technologies') and isinstance(project['technologies'], list):
                        project_text += f" (เทคโนโลยี: {', '.join(project['technologies'])})"
                    
                    user_context_text += project_text + "\n"
    
    return user_context_text

def customize_prompt_for_query(prompt: str, query: str, user_context: Optional[Dict[str, Any]]) -> str:
    """
    ปรับแต่ง prompt ให้เหมาะสมกับคำถาม
    
    Args:
        prompt: prompt เดิม
        query: คำถามจากผู้ใช้
        user_context: ข้อมูลผู้ใช้
        
    Returns:
        str: prompt ที่ปรับแต่งแล้ว
    """
    # ตรวจสอบหาคำเกี่ยวกับ resume และอาชีพในคำถาม
    resume_keywords = ["resume", "เรซูเม่", "เรซูเม", "cv", "ประวัติ", "สมัครงาน"]
    is_resume_question = any(keyword in query.lower() for keyword in resume_keywords)

    # ตรวจสอบหาคำเกี่ยวกับอาชีพใน query
    job_keywords = ["developer", "programmer", "engineer", "fullstack", "full stack", "frontend", "backend", "software"]
    job_name = next((kw for kw in job_keywords if kw in query.lower()), None)

    # ตรวจสอบคำถามเกี่ยวกับเงินเดือน
    salary_keywords = ["เงินเดือน", "salary", "รายได้", "ค่าตอบแทน"]
    is_salary_question = any(keyword in query.lower() for keyword in salary_keywords)

    # เพิ่มคำแนะนำเฉพาะหากมีข้อมูลผู้ใช้
    if user_context:
        user_name = user_context.get('name', '')
        
        if user_name:
            prompt += f"\n11. ใช้ชื่อ '{user_name}' เมื่อทักทาย ตามรูปแบบที่เหมาะสมกับบุคลิก"
        
        # ดึงทักษะผู้ใช้
        user_skills = []
        if 'skills' in user_context and isinstance(user_context['skills'], list):
            for skill in user_context['skills']:
                if isinstance(skill, dict) and 'name' in skill:
                    user_skills.append(skill['name'])
                elif isinstance(skill, str):
                    user_skills.append(skill)
        
        if user_skills:
            prompt += f"\n12. ผู้ใช้มีทักษะด้าน {', '.join(user_skills)} ให้แนะนำการต่อยอดจากทักษะเหล่านี้"
        
        # ดึงภาษาโปรแกรม
        user_languages = []
        if 'programming_languages' in user_context and isinstance(user_context['programming_languages'], list):
            for lang in user_context['programming_languages']:
                if isinstance(lang, dict) and 'name' in lang:
                    user_languages.append(lang['name'])
                elif isinstance(lang, str):
                    user_languages.append(lang)
        
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
    
    return prompt