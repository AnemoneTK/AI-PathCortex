"""
Utility functions for the IT Career Data Processing Pipeline.
This module provides common functions used across different components of the pipeline.
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Union, Optional, Set
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

def ensure_directory(directory: str) -> bool:
    """
    Ensure that a directory exists, creating it if necessary.
    
    Args:
        directory: Path to the directory to ensure
        
    Returns:
        True if the directory exists or was created, False otherwise
    """
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {directory}: {e}")
        return False

def read_text_file(file_path: str) -> Optional[str]:
    """
    Read text content from a file.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        File content as a string, or None if reading fails
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        return None

def write_text_file(file_path: str, content: str) -> bool:
    """
    Write text content to a file.
    
    Args:
        file_path: Path to the file to write
        content: Content to write to the file
        
    Returns:
        True if writing succeeds, False otherwise
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"Failed to write to file {file_path}: {e}")
        return False

def read_json_file(file_path: str) -> Optional[Union[List, Dict]]:
    """
    Read JSON content from a file.
    
    Args:
        file_path: Path to the JSON file to read
        
    Returns:
        Parsed JSON content, or None if reading or parsing fails
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to read or parse JSON file {file_path}: {e}")
        return None

def write_json_file(file_path: str, content: Union[List, Dict], indent: int = 2) -> bool:
    """
    Write JSON content to a file.
    
    Args:
        file_path: Path to the file to write
        content: Content to write to the file
        indent: Number of spaces to use for indentation
        
    Returns:
        True if writing succeeds, False otherwise
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False, indent=indent)
        return True
    except Exception as e:
        logger.error(f"Failed to write to JSON file {file_path}: {e}")
        return False

def find_files(directory: str, extension: str = '.txt') -> List[str]:
    """
    Find all files with a specific extension in a directory and its subdirectories.
    
    Args:
        directory: Directory to search
        extension: File extension to look for
        
    Returns:
        List of file paths
    """
    file_paths = []
    
    try:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(extension):
                    file_paths.append(os.path.join(root, file))
    except Exception as e:
        logger.error(f"Error finding files in {directory}: {e}")
    
    return file_paths

def clean_text(text: str, exclude_keywords: Optional[Set[str]] = None) -> str:
    """
    Clean text by removing unwanted content and standardizing format.
    
    Args:
        text: Text to clean
        exclude_keywords: Set of keywords to exclude lines containing them
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Define default exclude keywords if not provided
    if exclude_keywords is None:
        exclude_keywords = {
            "ค้นหางาน", "โปรไฟล์", "งานแนะนำ", "บันทึกการค้นหา", "งานที่บันทึก", 
            "ประวัติการสมัครงาน", "ครบเครื่องเรื่องงาน", "สำรวจอาชีพ", "สำรวจเงินเดือน",
            "บริษัทที่น่าสนใจ", "ดาวน์โหลด", "app", "Jobsdb @ Google Play", "Jobsdb @ App Store",
            "ลงทะเบียนฟรี", "ลงประกาศงาน", "ผลิตภัณฑ์และราคา", "บริการลูกค้า",
            "คำแนะนำเกี่ยวกับการจ้างงาน", "ข้อมูลเชิงลึกของตลาด", "พันธมิตรซอฟต์แวร์", 
            "เกี่ยวกับเรา", "ห้องข่าว", "นักลงทุนสัมพันธ์", "ร่วมงานกับเรา", 
            "Bdjobs", "Jobstreet", "Jora", "SEEK", "GradConnection", "GO1", "FutureLearn", "JobAdder",
            "Sidekicker", "ศูนย์ความช่วยเหลือ", "ติดต่อเรา", "บล็อกผลิตภัณฑ์", "โซเชียล",
            "Facebook", "Instagram", "Twitter", "YouTube", "ในหน้านี้", "เลือกดูอาชีพที่ใกล้เคียง",
            "อ่านเพิ่มเติมจาก", "สมัครรับคำแนะนำ", "เปรียบเทียบเงินเดือน"
        }
    
    # กรองส่วน "### ในหน้านี้" และส่วนที่ตามมา
    text = re.sub(r'### ในหน้านี้.*?(?=##|\Z)', '', text, flags=re.DOTALL)
    
    # กรองบรรทัดที่มีคำที่ไม่ต้องการ
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if line should be excluded
        skip = False
        
        # Skip lines with excluded keywords
        for keyword in exclude_keywords:
            if keyword.lower() in line.lower():
                skip = True
                break
                
        # Skip lines that are just numbers or bullet points without content
        if re.match(r'^\s*\d+\s*$', line) or line in ['•', '-']:
            skip = True
            
        if not skip:
            cleaned_lines.append(line)
    
    # Join lines and normalize whitespace
    cleaned_text = '\n'.join(cleaned_lines)
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)  # Replace multiple newlines with two
    
    return cleaned_text

def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two text strings.
    
    Args:
        text1: First text string
        text2: Second text string
        
    Returns:
        Similarity score between 0 and 1
    """
    if not text1 or not text2:
        return 0.0
        
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

def extract_skills_from_text(text: str) -> List[str]:
    """
    Extract potential skills from a text.
    
    Args:
        text: Text to extract skills from
        
    Returns:
        List of extracted skills
    """
    skills = []
    
    # Common IT skills to look for
    common_skills = [
        'Python', 'Java', 'JavaScript', 'TypeScript', 'C#', 'C++', 'PHP', 'Ruby', 'Go',
        'HTML', 'CSS', 'SQL', 'NoSQL', 'React', 'Angular', 'Vue', 'Node.js', 'Django',
        'Flask', 'Spring', 'Express', 'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes',
        'Git', 'Jenkins', 'CI/CD', 'Agile', 'Scrum', 'REST API', 'GraphQL', 'MongoDB',
        'MySQL', 'PostgreSQL', 'Oracle', 'Redis', 'Elasticsearch', 'TensorFlow', 'PyTorch',
        'Machine Learning', 'Deep Learning', 'AI', 'Data Science', 'Big Data', 'Hadoop',
        'Spark', 'UI/UX', 'Figma', 'Adobe XD', 'Photoshop', 'Illustrator', 'Linux',
        'Windows', 'macOS', 'Mobile Development', 'iOS', 'Android', 'Swift', 'Kotlin',
        'React Native', 'Flutter', 'WordPress', 'Drupal', 'Joomla', 'Shopify', 'Magento',
        'Security', 'Networking', 'Cloud Computing', 'DevOps', 'SysAdmin', 'Database',
        'Blockchain', 'IoT', 'AR/VR', 'Game Development', 'Unity', 'Unreal Engine'
    ]
    
    # Look for common skills in the text
    for skill in common_skills:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            skills.append(skill)
    
    # Look for bullet points that might contain skills
    bullet_points = re.findall(r'[-•]\s*([^-•].+?)(?=\n[-•]|\n\n|\Z)', text, re.DOTALL)
    for point in bullet_points:
        point = point.strip()
        if 'มีความรู้' in point or 'ใช้งาน' in point or 'เขียน' in point or 'พัฒนา' in point:
            # Look for potential technology names
            tech_words = re.findall(r'([A-Za-z\+\#\.]+(?:\s*[A-Za-z\+\#\.]+)?)', point)
            for tech in tech_words:
                tech = tech.strip()
                if len(tech) > 1 and tech not in skills:
                    skills.append(tech)
    
    return list(set(skills))  # Remove duplicates