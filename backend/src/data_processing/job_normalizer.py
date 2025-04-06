import json
import os
import re
from typing import Dict, Any, List, Set
from pathlib import Path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.utils.text_processor import TextProcessor  # Import the TextProcessor

class JobDataNormalizer:
    def __init__(self, 
                 jobs_data_path: str = 'data/raw/other_sources/jobs_data.json',
                 job_responsibilities_path: str = 'data/raw/other_sources/job_responsibilities.json', 
                 it_salary_data_path: str = 'data/raw/other_sources/it_salary_data.json',
                 output_dir: str = 'data/processed/normalized_jobs'):
        """
        Initialize the job data normalizer with paths to input files and output directory
        """
        self.jobs_data_path = jobs_data_path
        self.job_responsibilities_path = job_responsibilities_path
        self.it_salary_data_path = it_salary_data_path
        self.output_dir = output_dir
        
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Job title normalization mapping
        self.job_title_mapping = {
            # Software Engineering
            "software engineer": "software-engineer",
            "software developer": "software-engineer",
            "programmer": "software-engineer",
            "applications developer": "software-engineer",
            
            # Frontend Development
            "frontend developer": "web-developer",
            "front-end developer": "web-developer",
            "front end developer": "web-developer",
            
            
            # UX/UI Design
            "web designer": "ux-ui-designer",
            "webdesigner": "ux-ui-designer",
            "ux designer": "ux-ui-designer",
            "ui designer": "ux-ui-designer",
            "ux  ui designer": "ux-ui-designer",
            "user experience designer": "ux-ui-designer",
            
            # Backend Development
            "backend developer": "web-developer",
            "back-end developer": "web-developer",
            "back end developer": "web-developer",
            
            # Full Stack Development
            "full stack developer": "web-developer",
            "full-stack developer": "web-developer",
            "web developer": "web-developer",

            
            # Mobile Development
            "android developer": "mobile-developer",
            "ios developer": "mobile-developer",
            "mobile developer": "mobile-developer",
            
            # Data-related roles
            "data scientist": "data-scientist",
            "data analyst": "data-analyst",
            "data engineer": "data-engineer",
            "business intelligence analyst": "bi-analyst",
            "bi developer": "bi-developer",
            "data modeler": "data-modeler",
            "data architecture": "data-architect",
            
            # DevOps and Infrastructure
            "devops engineer": "devops-engineer",
            "devops": "devops-engineer",
            "cloud technology engineer": "cloud-engineer",
            "system engineer": "system-engineer",
            "system administrator": "system-administrator",
            "network engineer": "network-engineer",
            "network administrator": "network-administrator",
            "database administrator": "database-administrator",
            "dba": "database-administrator",
            
            # Security roles
            "security engineer": "security-engineer",
            "security analyst": "security-analyst",
            "network security administrator": "security-administrator",
            "cybersecurity specialist": "cybersecurity-specialist",
            "it security manager": "security-manager",
            
            # Testing/QA roles
            "software tester": "qa-engineer",
            "qa engineer": "qa-engineer",
            "uat specialist": "qa-engineer",
            "quality analyst": "qa-engineer",
            "test analyst": "qa-engineer",
            "testing engineer": "qa-engineer",
            
            # Management and analysis roles
            "project manager": "project-manager",
            "it project manager": "project-manager",
            "information technology project manager": "project-manager",
            "scrum master": "scrum-master",
            "business analyst": "business-analyst",
            "systems analyst": "systems-analyst",
            "system analyst": "systems-analyst",
            "software analyst": "systems-analyst",
            
            # Senior roles
            "software development manager": "software-development-manager",
            "it manager": "software-development-manager",
            "it director": "software-development-manager",
            "digital technology director": "software-development-manager",
            "cio": "software-development-manager",
            "chief information officer": "software-development-manager",
            "cto": "software-development-manager",
            "chief technology officer": "software-development-manager",
        }
        
        # Data storage
        self.jobs_data = {}
        self.job_responsibilities = {}
        self.it_salary_data = {}
        
    def normalize_job_title(self, job_title: str) -> str:
        """
        Normalize job title using both custom mapping and TextProcessor
        
        :param job_title: Original job title
        :return: Normalized job title
        """
        # First, use TextProcessor to clean the title
        cleaned_title = TextProcessor.clean_text(job_title, lowercase=True)
        
        # Convert to lowercase
        lowered_title = cleaned_title.lower().strip()
        
        # Check exact match first
        if lowered_title in self.job_title_mapping:
            return self.job_title_mapping[lowered_title]
        
        # Try partial matches
        for key, value in self.job_title_mapping.items():
            if key in lowered_title:
                return value
        
        # If no match, create a slug from the original title
        return re.sub(r'[^\w\s-]', '', lowered_title).replace(' ', '-').lower()
    
    def load_data(self):
        """Load data from JSON files"""
        try:
            with open(self.jobs_data_path, 'r', encoding='utf-8') as f:
                self.jobs_data = json.load(f)
            
            with open(self.job_responsibilities_path, 'r', encoding='utf-8') as f:
                self.job_responsibilities = json.load(f)
            
            with open(self.it_salary_data_path, 'r', encoding='utf-8') as f:
                self.it_salary_data = json.load(f)
            
            print("Successfully loaded all data files.")
        
        except FileNotFoundError as e:
            print(f"Error: {e}")
            raise
    
    def consolidate_salary_ranges(self, salary_ranges, titles):
        """
        Consolidate and normalize salary ranges with detailed job titles
        
        :param salary_ranges: List of salary range dictionaries
        :param titles: List of job titles
        :return: Consolidated list of detailed salary ranges
        """
        # Create a dictionary to store consolidated ranges
        consolidated_ranges = {}
        
        for entry in salary_ranges:
            experience = entry.get('experience', '').strip()
            salary = entry.get('salary', '').strip()
            
            # Skip empty entries
            if not experience or not salary:
                continue
            
            # If this experience level doesn't exist, add it
            if experience not in consolidated_ranges:
                try:
                    consolidated_ranges[experience] = {
                        'min_salary': float(salary.split(' - ')[0].replace(',', '')),
                        'max_salary': float(salary.split(' - ')[1].replace(',', '')),
                        'titles': titles
                    }
                except (ValueError, IndexError):
                    # Skip if salary parsing fails
                    continue
                continue
            
            # Try to merge salary ranges
            try:
                # Split existing and new salary ranges
                existing_min = consolidated_ranges[experience]['min_salary']
                existing_max = consolidated_ranges[experience]['max_salary']
                
                new_min, new_max = map(float, salary.replace(',', '').split(' - '))
                
                # Calculate new min and max
                merged_min = min(existing_min, new_min)
                merged_max = max(existing_max, new_max)
                
                # Update the consolidated range
                consolidated_ranges[experience] = {
                    'min_salary': merged_min,
                    'max_salary': merged_max,
                    'titles': list(set(consolidated_ranges[experience]['titles'] + titles))
                }
            
            except (ValueError, TypeError, IndexError):
                # If parsing fails, keep the first encountered range
                pass
        
        # Convert back to list of dictionaries with formatted output
        return [
            {
                "experience": exp, 
                "salary": f"{consolidated_ranges[exp]['min_salary']:,.0f} - {consolidated_ranges[exp]['max_salary']:,.0f}",
                "titles": consolidated_ranges[exp]['titles']
            } 
            for exp in sorted(consolidated_ranges.keys(), key=lambda x: float(x.split(' - ')[0]))
        ]

    def merge_job_data(self, normalized_title: str) -> Dict[str, Any]:
        """
        Merge job data from different sources for a given normalized job title
        
        :param normalized_title: Normalized job title
        :return: Merged job data dictionary
        """
        merged_data = {
            "id": normalized_title,
            "titles": [],
            "descriptions": {},  # เปลี่ยนจาก string เป็น dict เพื่อเก็บ description แยกตามอาชีพ
            "responsibilities": [],
            "skills": [],
            "salary_ranges": [],
            "education_requirements": []
        }
        
        # Collect titles and salary ranges
        collected_titles = []
        collected_salary_ranges = []
        
        # Merge from jobs_data
        for title, data in self.jobs_data.items():
            norm_title = self.normalize_job_title(title)
            if norm_title == normalized_title:
                # Normalize and clean titles
                normalized_titles = TextProcessor.normalize_job_titles([title])
                merged_data["titles"].extend(normalized_titles)
                collected_titles.extend(normalized_titles)
                
                # Clean and process description - เก็บแยกตาม job title
                if data.get("description"):
                    clean_title = title.lower().strip()
                    clean_desc = TextProcessor.clean_text(data["description"])
                    merged_data["descriptions"][clean_title] = clean_desc
                
                # Normalize responsibilities
                if data.get("responsibilities"):
                    normalized_resp = TextProcessor.normalize_responsibilities(data["responsibilities"])
                    merged_data["responsibilities"].extend(normalized_resp)
                
                # Process education requirements
                if data.get("education"):
                    education_reqs = [TextProcessor.clean_text(edu) for edu in data["education"]]
                    merged_data["education_requirements"].extend(education_reqs)
        
        # Merge from job_responsibilities
        for title, data in self.job_responsibilities.items():
            norm_title = self.normalize_job_title(title)
            if norm_title == normalized_title:
                # Clean description - เก็บแยกตาม job title
                if data.get("description"):
                    clean_title = title.lower().strip()
                    clean_desc = TextProcessor.clean_text(data["description"])
                    merged_data["descriptions"][clean_title] = clean_desc
                
                # Normalize responsibilities
                if data.get("responsibilities"):
                    normalized_resp = TextProcessor.normalize_responsibilities(data["responsibilities"])
                    merged_data["responsibilities"].extend(normalized_resp)
        
        # Merge from it_salary_data
        for title, data in self.it_salary_data.items():
            norm_title = self.normalize_job_title(title)
            if norm_title == normalized_title:
                # Normalize titles
                normalized_titles = TextProcessor.normalize_job_titles([title])
                collected_titles.extend(normalized_titles)
                
                # Normalize skills
                if data.get("skills"):
                    normalized_skills = TextProcessor.normalize_skills(data["skills"])
                    merged_data["skills"].extend(normalized_skills)
                
                # Collect salary ranges
                if data.get("salary"):
                    collected_salary_ranges.extend(data["salary"])
        
        # Consolidate salary ranges with collected titles
        merged_data["salary_ranges"] = self.consolidate_salary_ranges(
            collected_salary_ranges, 
            collected_titles
        )
        
        # Remove duplicates and clean up
        merged_data["titles"] = list(set(merged_data["titles"]))
        merged_data["responsibilities"] = list(set(merged_data["responsibilities"]))
        merged_data["skills"] = list(set(merged_data["skills"]))
        merged_data["education_requirements"] = list(set(merged_data["education_requirements"]))
        
        # สร้าง description แยกตามอาชีพจาก merged_data["descriptions"]
        # ถ้าไม่มี description เฉพาะสำหรับอาชีพใด ให้ใช้ค่าเริ่มต้น
        title_specific_descriptions = {}
        
        for job_title in merged_data["titles"]:
            title_lower = job_title.lower()
            # ค้นหา description ที่ตรงกับอาชีพนี้
            found_desc = False
            
            # ลองหา description ที่มีชื่อตรงกับ title หรือมีคำที่เกี่ยวข้อง
            for desc_title, desc in merged_data["descriptions"].items():
                if (title_lower in desc_title) or (desc_title in title_lower):
                    title_specific_descriptions[job_title] = desc
                    found_desc = True
                    break
            
            # ถ้าไม่เจอ description เฉพาะ สร้าง description มาตรฐานตามประเภทอาชีพ
            if not found_desc:
                title_specific_descriptions[job_title] = self.create_default_description(job_title)
        
        
        # ยังคงเก็บ description เดิมไว้เพื่อความเข้ากันได้กับโค้ดเดิม
        # ใช้ description แรกที่พบเป็นค่าเริ่มต้น
        if merged_data["descriptions"]:
            merged_data["description"] = list(merged_data["descriptions"].values())[0]
        else:
            # ถ้าไม่มี description เลย ใช้ description มาตรฐานของอาชีพแรก
            if merged_data["titles"]:
                merged_data["description"] = self.create_default_description(merged_data["titles"][0])
            else:
                merged_data["description"] = ""
        
        return merged_data
    
    def normalize_and_save_jobs(self):
        """
        Normalize job titles and save each category to a separate JSON file
        """
        # Collect all unique normalized job titles
        all_normalized_titles = set()
        
        # From jobs_data
        for title in self.jobs_data.keys():
            all_normalized_titles.add(self.normalize_job_title(title))
        
        # From job_responsibilities
        for title in self.job_responsibilities.keys():
            all_normalized_titles.add(self.normalize_job_title(title))
        
        # From it_salary_data
        for title in self.it_salary_data.keys():
            all_normalized_titles.add(self.normalize_job_title(title))
        
        # Process and save each job category
        for normalized_title in all_normalized_titles:
            job_data = self.merge_job_data(normalized_title)
            
            # Only save if there's meaningful data
            if job_data["titles"]:
                output_path = os.path.join(self.output_dir, f"{normalized_title}.json")
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(job_data, f, ensure_ascii=False, indent=2)
                
                print(f"Saved {output_path}")
    
    def process(self):
        """
        Main method to process and normalize job data
        """
        self.load_data()
        self.normalize_and_save_jobs()

def main():
    normalizer = JobDataNormalizer(
        jobs_data_path='data/raw/other_sources/jobs_data.json',
        job_responsibilities_path='data/raw/other_sources/job_responsibilities.json',
        it_salary_data_path='data/raw/other_sources/it_salary_data.json',
        output_dir='data/processed/normalized_jobs'
    )
    normalizer.process()

if __name__ == "__main__":
    main()