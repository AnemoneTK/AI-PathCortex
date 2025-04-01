import os
import re
import json
import logging
from typing import Dict, List, Any, Optional
from difflib import SequenceMatcher

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("src/logs/json_normalizer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("job_normalizer_json")

class JSONJobNormalizer:
    """
    Class to normalize and merge job data from JSON sources
    """
    def __init__(self, raw_data_folder: str = "data/raw", output_folder: str = "data/processed"):
        self.raw_data_folder = raw_data_folder
        self.output_folder = output_folder
        self.similarity_threshold = 0.75
        
        # Create output directory if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        # Define job groups with their keywords and classifications
        self.job_groups = {
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

    def normalize_job_title(self, job_title: str) -> str:
        """
        Normalize job title to a standard group
        
        Args:
            job_title: Raw job title to normalize
            
        Returns:
            Normalized job group
        """
        # Convert to lowercase for easier matching
        normalized_title = job_title.lower()
        
        # First, check for direct matches
        for group, group_data in self.job_groups.items():
            for keyword in group_data["keywords"]:
                if keyword.lower() in normalized_title:
                    # Check for incompatible keywords
                    is_compatible = True
                    for incompatible in group_data["incompatible_with"]:
                        if incompatible in normalized_title:
                            is_compatible = False
                            break
                    
                    if is_compatible:
                        return group
        
        # If no direct match, use similarity
        best_match = None
        best_score = 0
        
        for group, group_data in self.job_groups.items():
            for keyword in group_data["keywords"]:
                similarity = SequenceMatcher(None, normalized_title, keyword.lower()).ratio()
                
                if similarity > best_score and similarity >= self.similarity_threshold:
                    # Check for incompatible keywords
                    is_compatible = True
                    for incompatible in group_data["incompatible_with"]:
                        if incompatible in normalized_title:
                            is_compatible = False
                            break
                    
                    if is_compatible:
                        best_match = group
                        best_score = similarity
        
        # If no good match, return a generic normalized version
        if best_match:
            return best_match
        
        # Last resort: create a generic group name
        normalized = re.sub(r'[^a-z0-9-]', '-', normalized_title.replace(' ', '-'))
        return normalized

    def merge_job_data(self, jobs_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge job data from different sources
        
        Args:
            jobs_data: Dictionary of job data from different sources
            
        Returns:
            Merged job data
        """
        merged_jobs = {}
        
        for job_title, job_info in jobs_data.items():
            # Normalize job title
            normalized_title = self.normalize_job_title(job_title)
            
            # Initialize merged job entry if not exists
            if normalized_title not in merged_jobs:
                merged_jobs[normalized_title] = {
                    "id": normalized_title,
                    "titles": set([job_title]),
                    "skills": set(),
                    "description": "",
                    "responsibilities": set(),
                    "salary_info": [],
                    "sources": set()
                }
            
            # Merge titles
            merged_jobs[normalized_title]["titles"].add(job_title)
            
            # Merge skills
            if "skills" in job_info:
                merged_skills = job_info["skills"].split(", ") if isinstance(job_info["skills"], str) else job_info["skills"]
                merged_jobs[normalized_title]["skills"].update(merged_skills)
            
            # Merge description (prefer longer description)
            if "description" in job_info:
                if len(job_info["description"]) > len(merged_jobs[normalized_title]["description"]):
                    merged_jobs[normalized_title]["description"] = job_info["description"]
            
            # Merge responsibilities
            if "responsibilities" in job_info:
                if isinstance(job_info["responsibilities"], list):
                    merged_jobs[normalized_title]["responsibilities"].update(job_info["responsibilities"])
                elif isinstance(job_info["responsibilities"], str):
                    # If it's a string, split by comma or newline
                    responsibilities = re.split(r'[,\n]', job_info["responsibilities"])
                    merged_jobs[normalized_title]["responsibilities"].update(
                        [resp.strip() for resp in responsibilities if resp.strip()]
                    )
            
            # Merge salary information
            if "salary" in job_info:
                for salary_entry in job_info["salary"]:
                    # Check if this salary entry is already in the list
                    is_duplicate = False
                    for existing_salary in merged_jobs[normalized_title]["salary_info"]:
                        if (existing_salary.get("experience") == salary_entry.get("experience") and 
                            existing_salary.get("salary") == salary_entry.get("salary")):
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        merged_jobs[normalized_title]["salary_info"].append(salary_entry)
            
            # Add source
            merged_jobs[normalized_title]["sources"].add(job_title)
        
        # Convert sets back to lists for JSON serialization
        for job_id, job_data in merged_jobs.items():
            job_data["titles"] = list(job_data["titles"])
            job_data["skills"] = list(job_data["skills"])
            job_data["responsibilities"] = list(job_data["responsibilities"])
            job_data["sources"] = list(job_data["sources"])
        
        return merged_jobs

    def load_json_files(self) -> Dict[str, Any]:
        """
        Load JSON files from the raw data folder
        
        Returns:
            Combined job data dictionary
        """
        combined_jobs = {}
        
        # Scan the raw data folder for JSON files
        try:
            json_files = [f for f in os.listdir(self.raw_data_folder) if f.endswith('.json')]
        except OSError:
            logger.error(f"Could not list files in {self.raw_data_folder}")
            return combined_jobs
        
        for filename in json_files:
            filepath = os.path.join(self.raw_data_folder, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Skip files that are not dictionaries or have no job data
                if not isinstance(data, dict) or not data:
                    logger.warning(f"Skipping {filename}: no valid job data")
                    continue
                
                # Merge with existing jobs, handling different structures
                combined_jobs.update(data)
                
                logger.info(f"Loaded {filename} successfully")
            except FileNotFoundError:
                logger.warning(f"File not found: {filename}")
            except json.JSONDecodeError:
                logger.error(f"Error decoding JSON from {filename}")
            except Exception as e:
                logger.error(f"Unexpected error processing {filename}: {str(e)}")
        
        return combined_jobs

    def process_job_data(self):
        """
        Main method to process and merge job data
        """
        # Load job data from JSON files
        jobs_data = self.load_json_files()
        
        # Merge job data
        merged_jobs = self.merge_job_data(jobs_data)
        
        # Prepare output folders
        os.makedirs(self.output_folder, exist_ok=True)
        
        # Save merged jobs to JSON
        merged_jobs_file = os.path.join(self.output_folder, "merged_jobs.json")
        with open(merged_jobs_file, 'w', encoding='utf-8') as f:
            json.dump(merged_jobs, f, ensure_ascii=False, indent=2)
        
        # Create a summary markdown
        summary_file = os.path.join(self.output_folder, "README.md")
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("# Job Data Merge Summary\n\n")
            f.write(f"## Total Merged Job Groups: {len(merged_jobs)}\n\n")
            f.write("## Job Groups\n\n")
            
            for job_id, job_data in merged_jobs.items():
                f.write(f"### {job_data['id']}\n")
                f.write(f"- **Original Titles**: {', '.join(job_data['titles'])}\n")
                f.write(f"- **Skills**: {len(job_data['skills'])} skills\n")
                f.write(f"- **Salary Ranges**: {len(job_data['salary_info'])} ranges\n")
                f.write(f"- **Responsibilities**: {len(job_data['responsibilities'])} items\n\n")
        
        logger.info(f"Processed {len(merged_jobs)} job groups")
        logger.info(f"Merged job data saved to {merged_jobs_file}")
        logger.info(f"Summary saved to {summary_file}")
        
        return merged_jobs

def main():
    """Main function to run the JSON job normalizer"""
    normalizer = JSONJobNormalizer(
        raw_data_folder="data/json",
        output_folder="data/processed"
    )
    
    # Process job data
    merged_jobs = normalizer.process_job_data()

if __name__ == "__main__":
    main()