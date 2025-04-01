import os
import json
import logging
import re
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
import difflib

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s',
    handlers=[
        logging.FileHandler("data_processor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self, input_file: str, output_folder: str = "processed_data"):
        """
        Initialize DataProcessor
        
        Args:
            input_file: Path to the merged jobs JSON file
            output_folder: Folder to save processed files
        """
        self.input_file = input_file
        self.output_folder = output_folder
        self.jobs_data = self._load_jobs_data()
        
        # Create output directory if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        # Define skill categories
        self.skill_categories = self._define_skill_categories()
    
    def _load_jobs_data(self) -> Dict[str, Any]:
        """
        Load jobs data from JSON file
        
        Returns:
            Loaded jobs data
        """
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading jobs data: {e}")
            return {}
    
    def _define_skill_categories(self) -> Dict[str, List[str]]:
        """
        Define categories of skills for better organization
        
        Returns:
            Dictionary mapping skill categories to lists of related skills
        """
        return {
            "programming_languages": [
                "java", "python", "javascript", "typescript", "c#", "c++", "php", 
                "ruby", "go", "kotlin", "swift", "r", "dart", "scala"
            ],
            "frontend_technologies": [
                "html", "css", "react", "angular", "vue", "jquery", "bootstrap", 
                "tailwind", "sass", "less", "webpack", "redux"
            ],
            "backend_technologies": [
                "node.js", "django", "flask", "spring", "express", "laravel", 
                "ruby on rails", "asp.net", "fastapi"
            ],
            "databases": [
                "sql", "mysql", "postgresql", "mongodb", "oracle", "sqlite", 
                "redis", "cassandra", "dynamodb"
            ],
            "cloud_platforms": [
                "aws", "azure", "google cloud", "gcp", "heroku", "digitalocean", 
                "kubernetes", "docker", "openshift"
            ],
            "mobile_development": [
                "android", "ios", "react native", "flutter", "kotlin", "swift", 
                "xamarin", "ionic"
            ],
            "data_science": [
                "machine learning", "data analysis", "numpy", "pandas", "scipy", 
                "tensorflow", "pytorch", "scikit-learn", "deep learning"
            ],
            "devops_tools": [
                "jenkins", "gitlab", "github actions", "travis ci", "ansible", 
                "terraform", "ci/cd", "kubernetes", "docker"
            ]
        }
    
    def categorize_skills(self, skills: List[str]) -> Dict[str, List[str]]:
        """
        Categorize skills into predefined categories
        
        Args:
            skills: List of skills to categorize
            
        Returns:
            Dictionary of categorized skills
        """
        categorized_skills = defaultdict(list)
        uncategorized = []
        
        for skill in skills:
            skill_lower = skill.lower().strip()
            matched = False
            
            for category, category_skills in self.skill_categories.items():
                for cat_skill in category_skills:
                    # Use sequence matcher for fuzzy matching
                    if (cat_skill in skill_lower or 
                        difflib.SequenceMatcher(None, skill_lower, cat_skill).ratio() > 0.8):
                        categorized_skills[category].append(skill)
                        matched = True
                        break
                
                if matched:
                    break
            
                if not matched:
                    uncategorized.append(skill)
        
        # Add uncategorized skills to "other" category if any exist
        if uncategorized:
            categorized_skills["other"] = uncategorized
        
        return dict(categorized_skills)
    
    def extract_salary_statistics(self) -> Dict[str, Any]:
        """
        Extract and analyze salary statistics across different job groups
        
        Returns:
            Dictionary with salary statistics
        """
        salary_stats = defaultdict(list)
        
        for job_key, job_data in self.jobs_data.items():
            # Check if salary information exists
            if 'salary' in job_data:
                group = job_data.get('group', {}).get('main_group', 'unknown')
                
                for salary_entry in job_data['salary']:
                    try:
                        exp_range = salary_entry.get('experience', 'unknown')
                        salary_range = salary_entry.get('salary', '0 - 0')
                        
                        # Extract numeric salary values
                        salary_values = re.findall(r'\d+', salary_range.replace(',', ''))
                        
                        if len(salary_values) >= 2:
                            min_salary = int(salary_values[0])
                            max_salary = int(salary_values[1])
                            
                            salary_stats[group].append({
                                'experience': exp_range,
                                'min_salary': min_salary,
                                'max_salary': max_salary,
                                'avg_salary': (min_salary + max_salary) / 2
                            })
                    except Exception as e:
                        logger.warning(f"Error processing salary for {job_key}: {e}")
        
        # Calculate summary statistics for each group
        salary_summary = {}
        for group, salaries in salary_stats.items():
            if not salaries:
                continue
            
            salary_summary[group] = {
                'total_jobs': len(salaries),
                'min_overall': min(s['min_salary'] for s in salaries),
                'max_overall': max(s['max_salary'] for s in salaries),
                'avg_overall': sum(s['avg_salary'] for s in salaries) / len(salaries),
                'experience_breakdown': self._analyze_salary_by_experience(salaries)
            }
        
        return salary_summary
    
    def _analyze_salary_by_experience(self, salaries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze salary statistics by experience level
        
        Args:
            salaries: List of salary entries
            
        Returns:
            Dictionary with salary statistics by experience
        """
        exp_salary_stats = defaultdict(list)
        
        # Categorize experience levels
        for salary in salaries:
            exp = salary['experience']
            
            if re.search(r'1\s*-\s*3', exp):
                exp_salary_stats['entry_level'].append(salary)
            elif re.search(r'3\s*-\s*5', exp):
                exp_salary_stats['mid_level'].append(salary)
            elif re.search(r'5\s*-\s*8', exp):
                exp_salary_stats['senior_level'].append(salary)
            elif re.search(r'8\s*-\s*12', exp):
                exp_salary_stats['expert_level'].append(salary)
            else:
                exp_salary_stats['other'].append(salary)
        
        # Calculate statistics for each experience level
        experience_breakdown = {}
        for level, level_salaries in exp_salary_stats.items():
            if not level_salaries:
                continue
            
            experience_breakdown[level] = {
                'total_jobs': len(level_salaries),
                'min_salary': min(s['min_salary'] for s in level_salaries),
                'max_salary': max(s['max_salary'] for s in level_salaries),
                'avg_salary': sum(s['avg_salary'] for s in level_salaries) / len(level_salaries)
            }
        
        return experience_breakdown
    
    def find_related_jobs(self, num_related: int = 3) -> Dict[str, List[Dict[str, Any]]]:
        """
        Find related jobs based on skill and group similarity
        
        Args:
            num_related: Number of related jobs to find
            
        Returns:
            Dictionary of related jobs for each job
        """
        related_jobs = {}
        
        for current_job_key, current_job in self.jobs_data.items():
            # Get current job skills and group
            current_skills = set(current_job.get('skills', []))
            current_group = current_job.get('group', {}).get('main_group')
            
            # Calculate similarities with other jobs
            similarities = []
            for compare_job_key, compare_job in self.jobs_data.items():
                if compare_job_key == current_job_key:
                    continue
                
                # Compare skills
                compare_skills = set(compare_job.get('skills', []))
                skill_overlap = len(current_skills.intersection(compare_skills))
                
                # Compare groups
                group_score = 10 if current_group == compare_job.get('group', {}).get('main_group') else 0
                
                # Calculate total similarity score
                total_similarity = skill_overlap + group_score
                
                similarities.append({
                    'job_key': compare_job_key,
                    'title': compare_job.get('title', ''),
                    'similarity_score': total_similarity,
                    'overlapping_skills': list(current_skills.intersection(compare_skills))
                })
            
            # Sort by similarity and take top N
            related_jobs[current_job_key] = sorted(
                similarities, 
                key=lambda x: x['similarity_score'], 
                reverse=True
            )[:num_related]
        
        return related_jobs
    
    def generate_career_paths(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate potential career paths based on skills and job groups
        
        Returns:
            Dictionary of career paths for each job group
        """
        # Organize jobs by group and complexity
        job_groups = defaultdict(list)
        for job_key, job_data in self.jobs_data.items():
            group = job_data.get('group', {}).get('main_group', 'unknown')
            skills = job_data.get('skills', [])
            responsibilities = job_data.get('responsibilities', [])
            
            # Estimate job complexity
            complexity = len(skills) + len(responsibilities)
            
            job_groups[group].append({
                'job_key': job_key,
                'title': job_data.get('title', ''),
                'skills': skills,
                'complexity': complexity
            })
        
        # Generate career paths within each group
        career_paths = {}
        for group, jobs in job_groups.items():
            # Sort jobs by complexity
            sorted_jobs = sorted(jobs, key=lambda x: x['complexity'])
            
            paths = []
            for i, current_job in enumerate(sorted_jobs):
                # Find potential next steps
                next_steps = []
                for next_job in sorted_jobs[i+1:]:
                    # Calculate skill overlap
                    current_skills = set(current_job['skills'])
                    next_skills = set(next_job['skills'])
                    
                    # Prevent division by zero
                    if not current_skills:
                        # If no skills, use other criteria
                        if next_job['complexity'] > current_job['complexity']:
                            next_steps.append({
                                'job_key': next_job['job_key'],
                                'title': next_job['title'],
                                'skill_overlap': []
                            })
                        continue
                    
                    # Calculate overlap ratio
                    overlap = current_skills.intersection(next_skills)
                    overlap_ratio = len(overlap) / len(current_skills)
                    
                    # If skill overlap is significant, add as potential next step
                    if overlap_ratio > 0.4:  # At least 40% skill overlap
                        next_steps.append({
                            'job_key': next_job['job_key'],
                            'title': next_job['title'],
                            'skill_overlap': list(overlap)
                        })
                
                if next_steps:
                    paths.append({
                        'current_job': current_job,
                        'next_steps': next_steps
                    })
            
            career_paths[group] = paths
        
        return career_paths
    
    def process_and_enrich_data(self) -> Dict[str, Any]:
        """
        Process and enrich job data with various analyses
        
        Returns:
            Enriched job data dictionary
        """
        logger.info("Starting data enrichment process")
        
        # Analyze skills
        logger.info("Categorizing skills across jobs")
        skill_analysis = {}
        for job_key, job_data in self.jobs_data.items():
            skills = job_data.get('skills', [])
            skill_analysis[job_key] = self.categorize_skills(skills)
        
        # Salary statistics
        logger.info("Extracting salary statistics")
        salary_stats = self.extract_salary_statistics()
        
        # Related jobs
        logger.info("Finding related jobs")
        related_jobs = self.find_related_jobs()
        
        # Career paths
        logger.info("Generating career paths")
        career_paths = self.generate_career_paths()
        
        # Combine enriched data
        enriched_data = {
            'skill_analysis': skill_analysis,
            'salary_statistics': salary_stats,
            'related_jobs': related_jobs,
            'career_paths': career_paths
        }
        
        # Save enriched data to JSON
        output_file = os.path.join(self.output_folder, 'enriched_job_data.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(enriched_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved enriched job data to {output_file}")
        
        return enriched_data

def main():
    """
    Main function to run data processing
    """
    input_file = "processed_data/merged_jobs.json"
    processor = DataProcessor(input_file)
    
    # Process and enrich data
    enriched_data = processor.process_and_enrich_data()
    
    logger.info("Data processing completed successfully")

if __name__ == "__main__":
    main()