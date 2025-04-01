import os
import re
import json
import logging
from difflib import SequenceMatcher
from typing import Dict, List, Any, Tuple, Set, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("src/logs/normalizer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("job_normalizer")

class JobNormalizer:
    """
    Enhanced class to normalize job titles and group similar jobs together
    with improved content filtering and categorization
    """
    def __init__(self, raw_data_folder: str = "data/raw", output_folder: str = "data/processed"):
        self.raw_data_folder = raw_data_folder
        self.output_folder = output_folder
        self.similarity_threshold = 0.75  # Minimum similarity for matching
        self.job_groups = self._define_job_groups()
        self.exclude_keywords = self._define_exclude_keywords()
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            logger.info(f"Created output folder: {output_folder}")

    def _define_exclude_keywords(self) -> List[str]:
        """
        Define keywords that should be excluded from responsibilities and descriptions
        
        Returns:
            List of keywords to exclude
        """
        return [
            "การเป็น", "วิธีการเป็น", "เป็นอย่างไร", "ล่าสุด", "ทักษะและประสบการณ์ที่ดีที่สุดสำหรับ",
            "งาน", "ตำแหน่ง", "experience", "salary", "บาท", "ทักษะและประสบการณ์", "ที่ดีที่สุด"
        ]
    
    def _define_job_groups(self) -> Dict[str, Dict[str, Any]]:
        """
        Define job groups with related keywords and incompatible job titles
        
        Returns:
            Dictionary mapping standardized job titles to keywords and other metadata
        """
        return {
            "software-engineer": {
                "keywords": [
                    "software engineer", "software-engineer", "วิศวกรซอฟต์แวร์", 
                    "software development engineer", "engineer", "software"
                ],
                "incompatible_with": ["test", "qa", "quality", "data", "business intelligence", "web", "frontend"]
            },
            "software-developer": {
                "keywords": [
                    "software developer", "software-developer", "programmer", "coder",
                    "นักพัฒนาซอฟต์แวร์", "software development", "applications-developer",
                    "applications developer", "programmer", "software analyst"
                ],
                "incompatible_with": ["test", "qa", "quality", "data", "business intelligence", "web", "frontend"]
            },
            "web-developer": {
                "keywords": [
                    "web developer", "web-developer", "web development", "นักพัฒนาเว็บ",
                    "website developer"
                ],
                "incompatible_with": ["android", "ios", "mobile", "test", "qa"]
            },
            "frontend-developer": {
                "keywords": [
                    "frontend", "front end", "front-end", "frontend developer", 
                    "frontend-developer", "front-end developer", "front end developer",
                    "ui developer"
                ],
                "incompatible_with": ["backend", "back end", "back-end", "android", "ios", "data"]
            },
            "backend-developer": {
                "keywords": [
                    "backend", "back end", "back-end", "backend developer",
                    "backend-developer", "back-end developer", "back end developer",
                    "server side developer"
                ],
                "incompatible_with": ["frontend", "front end", "front-end", "android", "ios", "data"]
            },
            "full-stack-developer": {
                "keywords": [
                    "full stack", "fullstack", "full-stack", "full stack developer",
                    "fullstack developer", "full-stack developer", "full-stack-developer"
                ],
                "incompatible_with": ["android", "ios", "data", "test", "qa"]
            },
            "mobile-developer": {
                "keywords": [
                    "mobile developer", "mobile-developer", "mobile app developer",
                    "นักพัฒนาแอพ", "mobile application developer"
                ],
                "incompatible_with": ["web", "backend", "data", "test", "qa"]
            },
            "android-developer": {
                "keywords": [
                    "android developer", "android-developer", "android app developer",
                    "นักพัฒนาแอนดรอยด์", "android programmer", "android"
                ],
                "incompatible_with": ["ios", "iphone", "web", "backend", "data", "test", "qa"]
            },
            "ios-developer": {
                "keywords": [
                    "ios developer", "ios-developer", "ios app developer",
                    "นักพัฒนา ios", "swift developer", "iphone developer"
                ],
                "incompatible_with": ["android", "web", "backend", "data", "test", "qa"]
            },
            "ux-designer": {
                "keywords": [
                    "ux designer", "ux-designer", "ui designer", "ui-designer", "ux/ui designer",
                    "user experience", "user interface", "webdesigner", "web designer"
                ],
                "incompatible_with": ["developer", "engineer", "data", "test", "qa"]
            },
            "data-scientist": {
                "keywords": [
                    "data scientist", "data-scientist", "นักวิทยาศาสตร์ข้อมูล",
                    "machine learning engineer", "ml engineer", "ai engineer"
                ],
                "incompatible_with": ["developer", "web", "frontend", "backend", "android", "ios", "test", "qa"]
            },
            "data-analyst": {
                "keywords": [
                    "data analyst", "data-analyst", "นักวิเคราะห์ข้อมูล", 
                    "data analytics", "business analyst"
                ],
                "incompatible_with": ["developer", "web", "frontend", "backend", "android", "ios", "test", "qa"]
            },
            "devops-engineer": {
                "keywords": [
                    "devops engineer", "devops-engineer", "devops", "dev ops",
                    "site reliability engineer", "sre", "deployment engineer",
                    "infrastructure engineer"
                ],
                "incompatible_with": ["data", "frontend", "android", "ios", "test", "qa"]
            },
            "project-manager": {
                "keywords": [
                    "project manager", "it project manager", "information technology project manager",
                    "project management", "it project lead", "project lead", "scrum master"
                ],
                "incompatible_with": ["developer", "engineer", "data", "test", "qa"]
            },
            "qa-engineer": {
                "keywords": [
                    "qa engineer", "quality assurance", "qa", "tester", "test engineer",
                    "testing engineer", "quality control", "test analyst"
                ],
                "incompatible_with": ["developer", "frontend", "backend", "data", "android", "ios"]
            },
            "system-administrator": {
                "keywords": [
                    "system administrator", "system admin", "sysadmin", "it administrator",
                    "network administrator", "infrastructure administrator", "it support"
                ],
                "incompatible_with": ["developer", "engineer", "data", "frontend", "backend"]
            },
            "business-intelligence-analyst": {
                "keywords": [
                    "business intelligence", "bi analyst", "business intelligence analyst",
                    "data visualization specialist", "bi specialist"
                ],
                "incompatible_with": ["developer", "engineer", "frontend", "backend", "android", "ios"]
            }
        }
    
    def clean_content(self, content: str) -> str:
        """
        Clean content by removing non-relevant sections
        
        Args:
            content: Raw content to clean
            
        Returns:
            Cleaned content
        """
        # Remove sections with excluded keywords
        for keyword in self.exclude_keywords:
            content = re.sub(r'(?i).*' + re.escape(keyword) + r'.*\n?', '', content)
        
        # Remove numbered lines (e.g. "1. ...")
        content = re.sub(r'\d+\.\s*\d+\..*?(?=\n|\Z)', '', content)
        
        # Filter empty or numeric-only lines
        lines = content.split('\n')
        cleaned_lines = []
        for line in lines:
            # Skip lines with only numbers
            if re.match(r'^\s*\d+\s*$', line):
                continue
            # Skip very short lines (less than 5 chars)
            if len(line.strip()) < 5:
                continue
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def normalize_job_title(self, filename: str, content: str = None) -> str:
        """
        Match a filename and content with job groups and return the appropriate group
        
        Args:
            filename: Filename to normalize
            content: Optional content to help determine job type
            
        Returns:
            Standardized job title
        """
        # Remove file extension and convert dashes to spaces
        base_name = os.path.splitext(os.path.basename(filename))[0]
        job_title = base_name.replace('-', ' ').replace('_', ' ').lower()
        
        # List to store potential matches
        potential_matches = []
        
        # 1. Check for exact matches with keywords in groups
        for group, group_data in self.job_groups.items():
            keywords = group_data["keywords"]
            incompatible = group_data["incompatible_with"]
            
            # Check if any incompatible keywords are in the title or content
            has_incompatible = False
            for inc in incompatible:
                if inc.lower() in job_title:
                    has_incompatible = True
                    break
                if content and inc.lower() in content.lower():
                    has_incompatible = True
                    break
            
            if has_incompatible:
                continue
                
            # Check for keyword matches
            for keyword in keywords:
                if keyword.lower() in job_title:
                    # Direct match in filename has high confidence
                    potential_matches.append((group, 0.9))
                    break
                elif content and keyword.lower() in content.lower():
                    # Match in content has medium confidence
                    potential_matches.append((group, 0.7))
                    break
        
        # 2. If no direct keyword match, use similarity
        if not potential_matches:
            for group, group_data in self.job_groups.items():
                keywords = group_data["keywords"]
                incompatible = group_data["incompatible_with"]
                
                # Skip if incompatible
                has_incompatible = False
                for inc in incompatible:
                    if inc.lower() in job_title:
                        has_incompatible = True
                        break
                    if content and inc.lower() in content.lower():
                        has_incompatible = True
                        break
                        
                if has_incompatible:
                    continue
                
                # Compare with group name
                group_name = group.replace('-', ' ')
                similarity = SequenceMatcher(None, job_title, group_name).ratio()
                
                if similarity > self.similarity_threshold:
                    potential_matches.append((group, similarity))
                    
                # Compare with all keywords in the group
                for keyword in keywords:
                    similarity = SequenceMatcher(None, job_title, keyword.lower()).ratio()
                    if similarity > self.similarity_threshold:
                        potential_matches.append((group, similarity))
                        break
        
        # 3. Select the best match if we have potential matches
        if potential_matches:
            # Sort by confidence score
            potential_matches.sort(key=lambda x: x[1], reverse=True)
            best_match = potential_matches[0][0]
            logger.debug(f"Normalized '{job_title}' to '{best_match}' with score {potential_matches[0][1]:.2f}")
            return best_match
            
        # 4. If no good match found, use the cleaned filename
        normalized = re.sub(r'[^a-z0-9-]', '-', job_title.replace(' ', '-'))
        logger.debug(f"No good match for '{job_title}', using cleaned version '{normalized}'")
        return normalized
    
    def read_file_content(self, file_path: str) -> str:
        """
        Read and clean file content
        
        Args:
            file_path: Path to the file
            
        Returns:
            Cleaned file content
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            return self.clean_content(content)
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            return ""
    
    def extract_content_sections(self, file_path: str) -> Dict[str, Any]:
        """
        Extract different content sections from a file with improved cleaning
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            Dictionary with extracted content sections
        """
        try:
            content = self.read_file_content(file_path)
                
            # Extract Description section
            desc_pattern = r'(## Description|Description:|# Description)(.*?)(?=##|\Z)'
            desc_match = re.search(desc_pattern, content, re.DOTALL | re.IGNORECASE)
            description = ""
            if desc_match:
                # Remove the heading
                description = re.sub(r'^(## Description|Description:|# Description)', '', desc_match.group(2), flags=re.IGNORECASE)
                description = description.strip()
            
            # If no description found with heading, use first substantial paragraph
            if not description:
                paragraphs = content.split('\n\n')
                for para in paragraphs:
                    # Skip headings and bullet points
                    if not para.strip().startswith(('#', '-', '•')) and len(para.strip()) > 50:
                        description = para.strip()
                        break
            
            # Extract Responsibilities section with improved cleaning
            resp_pattern = r'(## Responsibilities|Responsibilities:|# Responsibilities)(.*?)(?=##|\Z)'
            resp_match = re.search(resp_pattern, content, re.DOTALL | re.IGNORECASE)
            responsibilities = []
            
            if resp_match:
                resp_text = resp_match.group(2).strip()
                # Extract bullet points
                for line in resp_text.split('\n'):
                    line = line.strip()
                    # Check for bullet points or numbered lists
                    if line and (line.startswith('•') or line.startswith('-') or re.match(r'^\d+\.', line)):
                        # Remove the bullet/number and clean
                        clean_line = re.sub(r'^[•\-]\s*|\d+\.\s*', '', line).strip()
                        
                        # Skip lines with excluded keywords
                        if any(keyword.lower() in clean_line.lower() for keyword in self.exclude_keywords):
                            continue
                            
                        if clean_line:
                            responsibilities.append(clean_line)
            
            # Extract Skills section with better filtering
            skills_pattern = r'(## Skills|Skills:|# Skills|ทักษะที่ต้องการ)(.*?)(?=##|\Z)'
            skills_match = re.search(skills_pattern, content, re.DOTALL | re.IGNORECASE)
            skills = []
            
            if skills_match:
                skills_text = skills_match.group(2).strip()
                
                # First, check if skills section contains salary info by mistake
                if re.search(r'experience|\d+\s*-\s*\d+\s*บาท|\d+,\d+', skills_text):
                    # This might be salary data - try to extract proper skills elsewhere
                    # Look for skills in the content outside the "Skills" section
                    skill_candidates = re.findall(r'(?:ทักษะ|มีความรู้ด้าน|สามารถใช้|programming|language|framework)(?:[^.]*)([\w\s,\-\+]+)', content, re.IGNORECASE)
                    
                    for candidate in skill_candidates:
                        # Split by commas if they exist
                        if ',' in candidate:
                            skill_list = [s.strip() for s in candidate.split(',')]
                            skills.extend([s for s in skill_list if len(s) > 2 and len(s) < 40])
                        else:
                            # Clean and add if it looks like a skill
                            clean_candidate = candidate.strip()
                            if clean_candidate and len(clean_candidate) > 2 and len(clean_candidate) < 40:
                                skills.append(clean_candidate)
                else:
                    # Process normal skills section
                    # Check if skills are in a bullet list
                    if '-' in skills_text or '•' in skills_text:
                        for line in skills_text.split('\n'):
                            line = line.strip()
                            if line and (line.startswith('•') or line.startswith('-')):
                                clean_line = re.sub(r'^[•\-]\s*', '', line).strip()
                                
                                # Skip if it has salary or experience info
                                if re.search(r'experience|\d+\s*บาท|\d+,\d+', clean_line):
                                    continue
                                    
                                if clean_line:
                                    skills.append(clean_line)
                    # Check if skills are comma-separated
                    elif ',' in skills_text:
                        for skill in skills_text.split(','):
                            clean_skill = skill.strip()
                            
                            # Skip if it has salary or experience info
                            if re.search(r'experience|\d+\s*บาท|\d+,\d+', clean_skill):
                                continue
                                
                            if clean_skill:
                                skills.append(clean_skill)
                    # Otherwise use the whole text if it's not too long
                    elif len(skills_text) < 100:
                        skills = [skills_text]
            
            # If we still don't have skills, try to extract them from the content
            if not skills:
                # Common tech skills to look for
                tech_skills = [
                    "Python", "Java", "JavaScript", "HTML", "CSS", "PHP", "SQL", "NoSQL", 
                    "MongoDB", "MySQL", "Git", "React", "Angular", "Vue", "Node.js", "Express", 
                    "Django", "Flask", "Spring", "Ruby", "C#", "C++", "Swift", "Kotlin", 
                    "Docker", "Kubernetes", "AWS", "Azure", "GCP", "DevOps", "CI/CD"
                ]
                
                for skill in tech_skills:
                    if re.search(r'\b' + re.escape(skill) + r'\b', content, re.IGNORECASE):
                        skills.append(skill)
            
            # Extract Salary section with improved parsing
            salary_pattern = r'(## ช่วงเงินเดือน|## Salary|Salary:|# Salary)(.*?)(?=##|\Z)'
            salary_match = re.search(salary_pattern, content, re.DOTALL | re.IGNORECASE)
            salary_info = []
            
            if salary_match:
                salary_text = salary_match.group(2).strip()
                # Extract salary ranges by experience level
                salary_exp_pattern = r'[-•]?\s*(\d+\s*-\s*\d+\+?)\s*(?:experience|ปี|years?)[:：]\s*(\d+(?:,\d+)?)\s*-\s*(\d+(?:,\d+)?)'
                salary_matches = re.findall(salary_exp_pattern, salary_text)
                
                for exp_range, min_salary, max_salary in salary_matches:
                    salary_info.append({
                        "experience": exp_range.strip(),
                        "min_salary": min_salary.replace(',', ''),
                        "max_salary": max_salary.replace(',', '')
                    })
            
            # Fallback for more general salary patterns
            if not salary_info:
                # Look for salary information in the entire content
                exp_salary_pattern = r'(\d+\s*-\s*\d+\+?)\s*(?:experience|ปี|years?)[:：]\s*(\d+(?:,\d+)?)\s*-\s*(\d+(?:,\d+)?)'
                exp_salary_matches = re.findall(exp_salary_pattern, content)
                
                for exp_range, min_salary, max_salary in exp_salary_matches:
                    salary_info.append({
                        "experience": exp_range.strip(),
                        "min_salary": min_salary.replace(',', ''),
                        "max_salary": max_salary.replace(',', '')
                    })
                
                # If still no match, look for general salary ranges
                if not salary_info:
                    general_salary_pattern = r'เงินเดือน\s*(?:ประมาณ|:)?\s*(\d+(?:,\d+)?)\s*-\s*(\d+(?:,\d+)?)'
                    general_salary_match = re.search(general_salary_pattern, content)
                    if general_salary_match:
                        salary_info.append({
                            "experience": "all",
                            "min_salary": general_salary_match.group(1).replace(',', ''),
                            "max_salary": general_salary_match.group(2).replace(',', '')
                        })
            
            return {
                "description": description,
                "responsibilities": responsibilities,
                "skills": skills,
                "salary_info": salary_info,
                "source_file": os.path.basename(file_path)
            }
        
        except Exception as e:
            logger.error(f"Error extracting content from {file_path}: {str(e)}")
            return {
                "description": "",
                "responsibilities": [],
                "skills": [],
                "salary_info": [],
                "source_file": os.path.basename(file_path)
            }
    
    def group_files_by_job(self) -> Dict[str, List[str]]:
        """
        Group files by normalized job title with content-aware classification
        
        Returns:
            Dictionary mapping normalized job titles to lists of file paths
        """
        job_files = {}
        txt_files = self.find_all_txt_files()
        logger.info(f"Found {len(txt_files)} text files to process")
        
        for file_path in txt_files:
            # Read file content to help with classification
            content = self.read_file_content(file_path)
            
            # Get normalized job title using both filename and content
            group = self.normalize_job_title(file_path, content)
            
            if group not in job_files:
                job_files[group] = []
                
            job_files[group].append(file_path)
        
        # Log statistics
        logger.info(f"Grouped into {len(job_files)} job categories")
        for group, files in sorted(job_files.items()):
            logger.info(f"  {group}: {len(files)} files")
            
        return job_files
    
    def find_all_txt_files(self, directory: str = None) -> List[str]:
        """
        Find all .txt files in a directory and its subdirectories
        
        Args:
            directory: Directory to search (defaults to raw_data_folder)
            
        Returns:
            List of paths to .txt files
        """
        if directory is None:
            directory = self.raw_data_folder
            
        txt_files = []
        
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.txt') and not file.startswith('_'):
                    txt_files.append(os.path.join(root, file))
                    
        return txt_files
    
    def extract_content_sections(self, file_path: str) -> Dict[str, Any]:
        """
        Extract different content sections from a file
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            Dictionary with extracted content sections
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            # Extract Description section
            desc_pattern = r'(## Description|Description:|# Description)(.*?)(?=##|\Z)'
            desc_match = re.search(desc_pattern, content, re.DOTALL | re.IGNORECASE)
            description = ""
            if desc_match:
                # Remove the heading
                description = re.sub(r'^(## Description|Description:|# Description)', '', desc_match.group(2), flags=re.IGNORECASE)
                description = description.strip()
            
            # If no description found with heading, use first substantial paragraph
            if not description:
                paragraphs = content.split('\n\n')
                for para in paragraphs:
                    # Skip headings and bullet points
                    if not para.strip().startswith(('#', '-', '•')) and len(para.strip()) > 50:
                        description = para.strip()
                        break
            
            # Extract Responsibilities section
            resp_pattern = r'(## Responsibilities|Responsibilities:|# Responsibilities)(.*?)(?=##|\Z)'
            resp_match = re.search(resp_pattern, content, re.DOTALL | re.IGNORECASE)
            responsibilities = []
            
            if resp_match:
                resp_text = resp_match.group(2).strip()
                # Extract bullet points
                for line in resp_text.split('\n'):
                    line = line.strip()
                    # Check for bullet points or numbered lists
                    if line and (line.startswith('•') or line.startswith('-') or re.match(r'^\d+\.', line)):
                        # Remove the bullet/number and clean
                        clean_line = re.sub(r'^[•\-]\s*|\d+\.\s*', '', line).strip()
                        if clean_line:
                            responsibilities.append(clean_line)
                    elif line and not line.startswith('#'):  # Plain text that's not a heading
                        responsibilities.append(line)
            
            # If no responsibilities found with heading, look for bullet points
            if not responsibilities:
                bullet_pattern = r'(?:^|\n)[•\-]\s*([^\n]+)'
                bullet_matches = re.findall(bullet_pattern, content)
                for match in bullet_matches:
                    if match.strip() and len(match.strip()) > 10:  # Ensure it's substantive
                        responsibilities.append(match.strip())
            
            # Extract Skills section
            skills_pattern = r'(## Skills|Skills:|# Skills|ทักษะที่ต้องการ)(.*?)(?=##|\Z)'
            skills_match = re.search(skills_pattern, content, re.DOTALL | re.IGNORECASE)
            skills = []
            
            if skills_match:
                skills_text = skills_match.group(2).strip()
                # Check if skills are in a list
                if '-' in skills_text or '•' in skills_text:
                    for line in skills_text.split('\n'):
                        line = line.strip()
                        if line and (line.startswith('•') or line.startswith('-')):
                            clean_line = re.sub(r'^[•\-]\s*', '', line).strip()
                            if clean_line:
                                skills.append(clean_line)
                # Check if skills are comma-separated
                elif ',' in skills_text:
                    skills = [s.strip() for s in skills_text.split(',') if s.strip()]
                # Otherwise use the whole text
                else:
                    skills = [skills_text]
            
            # Extract Salary section
            salary_pattern = r'(## ช่วงเงินเดือน|## Salary|Salary:|# Salary)(.*?)(?=##|\Z)'
            salary_match = re.search(salary_pattern, content, re.DOTALL | re.IGNORECASE)
            salary_info = []
            
            if salary_match:
                salary_text = salary_match.group(2).strip()
                # Extract salary ranges by experience level
                salary_exp_pattern = r'[-•]?\s*(\d+\s*-\s*\d+\+?)\s*(?:experience|ปี|years?)[:：]\s*(\d+(?:,\d+)?)\s*-\s*(\d+(?:,\d+)?)'
                salary_matches = re.findall(salary_exp_pattern, salary_text)
                
                for exp_range, min_salary, max_salary in salary_matches:
                    salary_info.append({
                        "experience": exp_range.strip(),
                        "min_salary": min_salary.replace(',', ''),
                        "max_salary": max_salary.replace(',', '')
                    })
            
            # Fallback for more general salary format
            if not salary_info:
                general_salary_pattern = r'(\d+(?:,\d+)?)\s*-\s*(\d+(?:,\d+)?)'
                general_salary_match = re.search(general_salary_pattern, content)
                if general_salary_match:
                    salary_info.append({
                        "experience": "all",
                        "min_salary": general_salary_match.group(1).replace(',', ''),
                        "max_salary": general_salary_match.group(2).replace(',', '')
                    })
            
            return {
                "description": description,
                "responsibilities": responsibilities,
                "skills": skills,
                "salary_info": salary_info,
                "source_file": os.path.basename(file_path)
            }
        
        except Exception as e:
            logger.error(f"Error extracting content from {file_path}: {str(e)}")
            return {
                "description": "",
                "responsibilities": [],
                "skills": [],
                "salary_info": [],
                "source_file": os.path.basename(file_path)
            }
    
    def group_files_by_job(self) -> Dict[str, List[str]]:
        """
        Group files by normalized job title
        
        Returns:
            Dictionary mapping normalized job titles to lists of file paths
        """
        job_files = {}
        txt_files = self.find_all_txt_files()
        logger.info(f"Found {len(txt_files)} text files to process")
        
        for file_path in txt_files:
            group = self.normalize_job_title(file_path)
            
            if group not in job_files:
                job_files[group] = []
                
            job_files[group].append(file_path)
        
        # Log statistics
        logger.info(f"Grouped into {len(job_files)} job categories")
        for group, files in sorted(job_files.items()):
            logger.info(f"  {group}: {len(files)} files")
            
        return job_files

    def merge_job_data(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Merge data from multiple files for the same job category
        
        Args:
            file_paths: List of files to merge
            
        Returns:
            Dictionary with merged job data
        """
        all_descriptions = []
        all_responsibilities = set()
        all_skills = set()
        all_salary_info = []
        source_files = []
        
        for file_path in file_paths:
            content = self.extract_content_sections(file_path)
            
            # Add non-duplicate description
            if content["description"] and content["description"].strip():
                # Filter duplicative descriptions using similarity
                is_duplicate = False
                for existing_desc in all_descriptions:
                    if SequenceMatcher(None, content["description"].lower(), existing_desc.lower()).ratio() > 0.7:
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    all_descriptions.append(content["description"])
            
            # Add non-duplicate responsibilities
            for resp in content["responsibilities"]:
                if resp.strip():
                    # Filter duplicative responsibilities using similarity
                    is_duplicate = False
                    for existing_resp in all_responsibilities:
                        if SequenceMatcher(None, resp.lower(), existing_resp.lower()).ratio() > 0.8:
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        all_responsibilities.add(resp)
            
            # Add non-duplicate skills
            for skill in content["skills"]:
                if skill.strip():
                    # Filter duplicative skills
                    is_duplicate = False
                    for existing_skill in all_skills:
                        if SequenceMatcher(None, skill.lower(), existing_skill.lower()).ratio() > 0.8:
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        all_skills.add(skill)
            
            # Add salary info
            for salary in content["salary_info"]:
                if salary not in all_salary_info:
                    all_salary_info.append(salary)
            
            source_files.append(content["source_file"])
        
        # Sort responsibilities by length (shorter first)
        sorted_responsibilities = sorted(list(all_responsibilities), key=len)
        # Sort skills alphabetically
        sorted_skills = sorted(list(all_skills))
        
        return {
            "descriptions": all_descriptions,
            "responsibilities": sorted_responsibilities,
            "skills": sorted_skills,
            "salary_info": all_salary_info,
            "source_files": source_files
        }
    
    def create_merged_files(self, output_folder: Optional[str] = None) -> Dict[str, Any]:
        """
        Create merged job data files from grouped files
        
        Args:
            output_folder: Folder to save merged files (defaults to self.output_folder)
            
        Returns:
            Summary of the merging process
        """
        if output_folder is None:
            output_folder = self.output_folder
        
        # Create output folder if needed
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            
        # Group files by job title
        job_groups = self.group_files_by_job()
        
        # Prepare summary data
        summary = {
            "total_groups": len(job_groups),
            "total_files": sum(len(files) for files in job_groups.values()),
            "groups": {},
            "group_details": {}
        }
        
        # Process each job group
        all_jobs_data = []
        
        for group, files in job_groups.items():
            logger.info(f"Processing job group: {group} ({len(files)} files)")
            merged_data = self.merge_job_data(files)
            
            # Create display name
            display_name = group.replace('-', ' ').title()
            
            # Create content for individual text file
            content = f"# {display_name}\n\n"
            
            # Add descriptions
            content += "## Description\n\n"
            for i, desc in enumerate(merged_data["descriptions"], 1):
                content += f"### Description {i}\n{desc}\n\n"
            
            # Add responsibilities
            content += "## Responsibilities\n\n"
            for resp in merged_data["responsibilities"]:
                content += f"- {resp}\n"
                
            # Add skills
            content += "\n## Skills\n\n"
            for skill in merged_data["skills"]:
                content += f"- {skill}\n"
                
            # Add salary information
            content += "\n## Salary Information\n\n"
            if merged_data["salary_info"]:
                for salary in merged_data["salary_info"]:
                    exp = salary.get("experience", "")
                    min_sal = salary.get("min_salary", "")
                    max_sal = salary.get("max_salary", "")
                    content += f"- {exp} ปี: {min_sal}-{max_sal} บาท\n"
            else:
                content += "No specific salary information available.\n"
                
            # Add source information
            content += f"\n## Sources\n\n"
            for source in merged_data["source_files"]:
                content += f"- {source}\n"
            
            # Save individual text file
            text_file = os.path.join(output_folder, f"{group}.txt")
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
            # Prepare data for JSON
            job_json = {
                "id": group,
                "title": display_name,
                "descriptions": merged_data["descriptions"],
                "responsibilities": merged_data["responsibilities"],
                "skills": merged_data["skills"],
                "salary_info": merged_data["salary_info"],
                "sources": merged_data["source_files"]
            }
            
            all_jobs_data.append(job_json)
                
            # Update summary
            summary["groups"][display_name] = len(files)
            summary["group_details"][group] = {
                "display_name": display_name,
                "file_count": len(files),
                "source_files": merged_data["source_files"],
                "output_file": text_file
            }
        
        # Save all jobs data to JSON
        json_file = os.path.join(output_folder, "processed_jobs.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(all_jobs_data, f, ensure_ascii=False, indent=2)
        
        # Save summary to JSON
        with open(os.path.join(output_folder, "summary.json"), 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
            
        # Create README with summary
        readme_content = f"# ข้อมูลอาชีพด้าน IT ที่รวมแล้ว\n\n"
        readme_content += f"## สรุปข้อมูล\n\n"
        readme_content += f"- จำนวนกลุ่มอาชีพทั้งหมด: {summary['total_groups']}\n"
        readme_content += f"- จำนวนไฟล์ที่นำมารวม: {summary['total_files']}\n\n"
        
        readme_content += f"## รายการกลุ่มอาชีพ\n\n"
        for group_name, count in sorted(summary["groups"].items()):
            readme_content += f"- {group_name}: {count} ไฟล์\n"
            
        with open(os.path.join(output_folder, "README.md"), 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        logger.info(f"Created merged files in {output_folder}")
        logger.info(f"Saved combined data to {json_file}")
        
        return summary
    
    def prepare_embeddings_data(self) -> List[Dict[str, Any]]:
        """
        Prepare data for creating embeddings
        
        Returns:
            List of dictionaries with text and metadata for embeddings
        """
        # Load processed job data
        json_file = os.path.join(self.output_folder, "processed_jobs.json")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                jobs_data = json.load(f)
        except FileNotFoundError:
            logger.error(f"Could not find processed data file: {json_file}")
            logger.info("Run create_merged_files() first to generate the data")
            return []
        
        embedding_data = []
        
        for job in jobs_data:
            job_id = job["id"]
            job_title = job["title"]
            
            # Create description chunks
            for i, description in enumerate(job["descriptions"]):
                desc_chunk = {
                    "text": f"ตำแหน่งงาน: {job_title}\n\nคำอธิบาย: {description}",
                    "metadata": {
                        "job_id": job_id,
                        "job_title": job_title,
                        "chunk_type": "description",
                        "chunk_index": i
                    }
                }
                embedding_data.append(desc_chunk)
            
            # Create responsibilities chunk
            if job["responsibilities"]:
                resp_text = "ความรับผิดชอบ:\n" + "\n".join([f"- {r}" for r in job["responsibilities"]])
                resp_chunk = {
                    "text": f"ตำแหน่งงาน: {job_title}\n\n{resp_text}",
                    "metadata": {
                        "job_id": job_id,
                        "job_title": job_title,
                        "chunk_type": "responsibilities"
                    }
                }
                embedding_data.append(resp_chunk)
            
            # Create skills chunk
            if job["skills"]:
                skills_text = "ทักษะที่ต้องการ:\n" + "\n".join([f"- {s}" for s in job["skills"]])
                skills_chunk = {
                    "text": f"ตำแหน่งงาน: {job_title}\n\n{skills_text}",
                    "metadata": {
                        "job_id": job_id,
                        "job_title": job_title,
                        "chunk_type": "skills"
                    }
                }
                embedding_data.append(skills_chunk)
            
            # Create salary chunk
            if job["salary_info"]:
                salary_text = "ข้อมูลเงินเดือน:\n"
                for salary in job["salary_info"]:
                    exp = salary.get("experience", "")
                    min_sal = salary.get("min_salary", "")
                    max_sal = salary.get("max_salary", "")
                    salary_text += f"- {exp} ปี: {min_sal}-{max_sal} บาท\n"
                
                salary_chunk = {
                    "text": f"ตำแหน่งงาน: {job_title}\n\n{salary_text}",
                    "metadata": {
                        "job_id": job_id,
                        "job_title": job_title,
                        "chunk_type": "salary"
                    }
                }
                embedding_data.append(salary_chunk)
        
        # Save embedding data to JSON
        embedding_file = os.path.join(self.output_folder, "embedding_data.json")
        with open(embedding_file, 'w', encoding='utf-8') as f:
            json.dump(embedding_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Created {len(embedding_data)} chunks for embeddings")
        logger.info(f"Saved embedding data to {embedding_file}")
        
        return embedding_data


def main():
    """Main function to run the job normalizer"""
    normalizer = JobNormalizer(
        raw_data_folder="data/raw",
        output_folder="data/processed"
    )
    
    # Group and merge job data
    summary = normalizer.create_merged_files()
    logger.info(f"Processed {summary['total_groups']} job groups from {summary['total_files']} files")
    
    # Prepare data for embeddings
    embedding_data = normalizer.prepare_embeddings_data()
    logger.info(f"Created {len(embedding_data)} chunks for embeddings")


if __name__ == "__main__":
    main()