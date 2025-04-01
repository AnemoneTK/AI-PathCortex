import os
import re
import json
import logging
import difflib
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import Counter, defaultdict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("src/logs/processor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("data_processor")

class EnhancedDataProcessor:
    """
    Enhanced processor for IT job data with advanced analysis capabilities
    """
    def __init__(self, input_folder: str = "data/processed", output_folder: str = "data/processed/enriched"):
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.processed_jobs = []
        self.job_skills_map = {}
        self.skill_categories = self._define_skill_categories()
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            logger.info(f"Created output folder: {output_folder}")
    
    def _define_skill_categories(self) -> Dict[str, List[str]]:
        """
        Define categories of skills for better organization
        
        Returns:
            Dictionary mapping skill categories to lists of related skills
        """
        return {
            "programming_languages": [
                "java", "python", "javascript", "typescript", "c#", "c++", "php", "ruby", "go", "rust",
                "kotlin", "swift", "objective-c", "scala", "perl", "r", "matlab", "dart", "lua",
                "assembly", "fortran", "cobol", "visual basic", "vba", "delphi", "pl/sql", "groovy"
            ],
            "frontend": [
                "html", "css", "sass", "less", "javascript", "typescript", "jquery", "bootstrap",
                "react", "angular", "vue", "svelte", "redux", "mobx", "next.js", "gatsby", 
                "webpack", "babel", "tailwind", "material-ui", "styled-components", "emotion"
            ],
            "backend": [
                "node.js", "express", "django", "flask", "spring", "laravel", "ruby on rails",
                "asp.net", "fastapi", "nest.js", "koa", "phoenix", "gin", "echo", "symfony", "codeigniter"
            ],
            "database": [
                "sql", "mysql", "postgresql", "sqlite", "oracle", "mongodb", "cassandra", "redis",
                "dynamodb", "firestore", "mariadb", "couchdb", "neo4j", "elasticsearch", "nosql", 
                "graphql", "prisma", "sequelize", "mongoose", "typeorm", "sqlalchemy"
            ],
            "devops": [
                "docker", "kubernetes", "jenkins", "github actions", "circleci", "travis ci",
                "ansible", "terraform", "aws", "azure", "gcp", "nginx", "apache", "linux", "shell",
                "bash", "ci/cd", "helm", "prometheus", "grafana", "elasticsearch", "logstash", "kibana"
            ],
            "mobile": [
                "android", "ios", "swift", "kotlin", "objective-c", "react native", "flutter", 
                "xamarin", "ionic", "cordova", "capacitor", "android studio", "xcode", "dart", 
                "mobile app development", "mobile ui design", "responsive design"
            ],
            "cloud": [
                "aws", "azure", "gcp", "google cloud", "cloud computing", "serverless", "lambda",
                "ec2", "s3", "dynamodb", "firestore", "firebase", "heroku", "digitalocean", "netlify",
                "vercel", "cloudflare", "kubernetes", "docker", "container", "microservices"
            ],
            "data_science": [
                "machine learning", "deep learning", "tensorflow", "pytorch", "scikit-learn", "pandas",
                "numpy", "scipy", "matplotlib", "seaborn", "tableau", "power bi", "statistics", 
                "data visualization", "data analysis", "data mining", "big data", "hadoop", "spark",
                "nlp", "computer vision", "neural networks"
            ],
            "security": [
                "cybersecurity", "network security", "encryption", "penetration testing", "ethical hacking",
                "security audit", "vulnerability assessment", "firewall", "oauth", "jwt", "authentication",
                "authorization", "single sign-on", "kerberos", "ldap", "active directory"
            ],
            "soft_skills": [
                "communication", "teamwork", "problem solving", "critical thinking", "leadership",
                "time management", "project management", "agile", "scrum", "kanban", "jira",
                "presentation", "negotiation", "adaptability", "creativity"
            ]
        }
    
    def load_processed_jobs(self) -> List[Dict[str, Any]]:
        """
        Load the processed job data from JSON file
        
        Returns:
            List of processed job dictionaries
        """
        json_file = os.path.join(self.input_folder, "processed_jobs.json")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                self.processed_jobs = json.load(f)
            logger.info(f"Loaded {len(self.processed_jobs)} processed jobs from {json_file}")
            return self.processed_jobs
        except FileNotFoundError:
            logger.error(f"Could not find processed data file: {json_file}")
            return []
    
    def categorize_skills(self, skill_list: List[str]) -> Dict[str, List[str]]:
        """
        Categorize skills into different areas
        
        Args:
            skill_list: List of skills to categorize
            
        Returns:
            Dictionary mapping skill categories to skills in that category
        """
        categorized = defaultdict(list)
        uncategorized = []
        
        for skill in skill_list:
            skill_lower = skill.lower()
            assigned = False
            
            # Check which category this skill belongs to
            for category, keywords in self.skill_categories.items():
                for keyword in keywords:
                    if keyword in skill_lower or difflib.SequenceMatcher(None, keyword, skill_lower).ratio() > 0.9:
                        categorized[category].append(skill)
                        assigned = True
                        break
                if assigned:
                    break
            
            if not assigned:
                uncategorized.append(skill)
        
        # Add uncategorized skills
        if uncategorized:
            categorized["other"] = uncategorized
        
        return dict(categorized)
    
    def extract_common_skills(self) -> Dict[str, List[Tuple[str, int]]]:
        """
        Extract and count common skills across job categories
        
        Returns:
            Dictionary mapping job categories to lists of (skill, count) tuples
        """
        if not self.processed_jobs:
            self.load_processed_jobs()
        
        # Map to store skills by job category
        self.job_skills_map = defaultdict(list)
        
        # Group jobs by their primary category
        job_categories = defaultdict(list)
        for job in self.processed_jobs:
            job_id = job["id"]
            category = job_id.split('-')[0] if '-' in job_id else job_id
            job_categories[category].append(job)
            
            # Add skills to the job map
            for skill in job["skills"]:
                self.job_skills_map[job_id].append(skill.lower())
        
        # Count skills by category
        category_skills = {}
        for category, jobs in job_categories.items():
            all_skills = []
            for job in jobs:
                all_skills.extend([s.lower() for s in job["skills"]])
            
            # Count occurrences
            skill_counter = Counter(all_skills)
            # Sort by frequency
            sorted_skills = skill_counter.most_common()
            
            category_skills[category] = sorted_skills
        
        return category_skills
    
    def calculate_salary_statistics(self) -> Dict[str, Dict[str, Any]]:
        """
        Calculate salary statistics for each job category
        
        Returns:
            Dictionary with salary statistics by job category
        """
        if not self.processed_jobs:
            self.load_processed_jobs()
        
        salary_stats = {}
        
        for job in self.processed_jobs:
            job_id = job["id"]
            salary_info = job["salary_info"]
            
            if not salary_info:
                continue
            
            # Categorize by experience level
            by_experience = defaultdict(list)
            for salary in salary_info:
                exp = salary.get("experience", "all")
                if exp == "all":
                    exp_level = "all"
                else:
                    # Convert ranges like "1-3" to min value
                    match = re.search(r'(\d+)', exp)
                    if match:
                        min_exp = int(match.group(1))
                        if min_exp <= 3:
                            exp_level = "junior"
                        elif min_exp <= 5:
                            exp_level = "mid"
                        else:
                            exp_level = "senior"
                    else:
                        exp_level = "unspecified"
                
                # Extract min and max salary
                try:
                    min_salary = int(salary.get("min_salary", "0"))
                    max_salary = int(salary.get("max_salary", "0"))
                    
                    if min_salary > 0 and max_salary > 0:
                        by_experience[exp_level].append({
                            "min": min_salary,
                            "max": max_salary,
                            "avg": (min_salary + max_salary) / 2
                        })
                except (ValueError, TypeError):
                    continue
            
            # Calculate statistics for each experience level
            stats = {}
            for exp_level, salaries in by_experience.items():
                if not salaries:
                    continue
                
                min_values = [s["min"] for s in salaries]
                max_values = [s["max"] for s in salaries]
                avg_values = [s["avg"] for s in salaries]
                
                stats[exp_level] = {
                    "count": len(salaries),
                    "min": min(min_values),
                    "max": max(max_values),
                    "avg": sum(avg_values) / len(avg_values)
                }
            
            if stats:
                salary_stats[job_id] = stats
        
        return salary_stats
    
    def find_related_jobs(self, num_related: int = 3) -> Dict[str, List[Dict[str, Any]]]:
        """
        Find related jobs based on skill similarity
        
        Args:
            num_related: Number of related jobs to find for each job
            
        Returns:
            Dictionary mapping job IDs to lists of related jobs
        """
        if not self.job_skills_map:
            self.extract_common_skills()
        
        related_jobs = {}
        
        for job in self.processed_jobs:
            job_id = job["id"]
            job_skills = set(self.job_skills_map.get(job_id, []))
            
            if not job_skills:
                continue
            
            # Calculate similarity with all other jobs
            similarities = []
            for other_job in self.processed_jobs:
                other_id = other_job["id"]
                if other_id == job_id:
                    continue
                
                other_skills = set(self.job_skills_map.get(other_id, []))
                if not other_skills:
                    continue
                
                # Calculate Jaccard similarity
                intersection = len(job_skills.intersection(other_skills))
                union = len(job_skills.union(other_skills))
                similarity = intersection / union if union > 0 else 0
                
                similarities.append({
                    "id": other_id,
                    "title": other_job["title"],
                    "similarity": similarity,
                    "common_skills": list(job_skills.intersection(other_skills))
                })
            
            # Sort by similarity and take top N
            top_related = sorted(similarities, key=lambda x: x["similarity"], reverse=True)[:num_related]
            related_jobs[job_id] = top_related
        
        return related_jobs
    
    def analyze_career_paths(self) -> Dict[str, List[str]]:
        """
        Analyze possible career paths based on skill progression
        
        Returns:
            Dictionary mapping job categories to lists of potential next steps
        """
        if not self.processed_jobs:
            self.load_processed_jobs()
        
        # Group jobs by their primary category and skill complexity
        job_categories = defaultdict(list)
        job_complexity = {}
        
        for job in self.processed_jobs:
            job_id = job["id"]
            category = job_id.split('-')[0] if '-' in job_id else job_id
            job_categories[category].append(job)
            
            # Estimate job complexity by number of skills and responsibilities
            complexity = len(job.get("skills", [])) + len(job.get("responsibilities", []))
            
            # Check if roles contain leadership or senior indicators
            description_text = " ".join(job.get("descriptions", []))
            if any(word in description_text.lower() for word in ["lead", "senior", "manager", "architect", "director"]):
                complexity += 5
            
            job_complexity[job_id] = complexity
        
        # Define career paths based on complexity and skill overlap
        career_paths = {}
        
        for category, jobs in job_categories.items():
            # Sort jobs by complexity
            sorted_jobs = sorted(jobs, key=lambda j: job_complexity.get(j["id"], 0))
            
            # Create paths from less complex to more complex roles
            paths = []
            for i, job in enumerate(sorted_jobs):
                next_steps = []
                for j, higher_job in enumerate(sorted_jobs[i+1:]):
                    # Calculate skill overlap
                    job_skills = set(s.lower() for s in job.get("skills", []))
                    higher_skills = set(s.lower() for s in higher_job.get("skills", []))
                    
                    if job_skills and higher_skills:
                        overlap = len(job_skills.intersection(higher_skills)) / len(job_skills)
                        if overlap > 0.4:  # At least 40% skill overlap
                            next_steps.append(higher_job["id"])
                
                if next_steps:
                    paths.append({
                        "from": job["id"],
                        "to": next_steps
                    })
            
            if paths:
                career_paths[category] = paths
        
        return career_paths
    
    def generate_job_summaries(self) -> Dict[str, Dict[str, Any]]:
        """
        Generate concise summaries for each job
        
        Returns:
            Dictionary mapping job IDs to summary dictionaries
        """
        if not self.processed_jobs:
            self.load_processed_jobs()
        
        job_summaries = {}
        
        for job in self.processed_jobs:
            job_id = job["id"]
            
            # Select the best description (usually the first one)
            description = job["descriptions"][0] if job["descriptions"] else ""
            
            # Get top 5 responsibilities
            responsibilities = job["responsibilities"][:5] if job["responsibilities"] else []
            
            # Categorize skills
            categorized_skills = self.categorize_skills(job["skills"])
            
            # Extract salary range if available
            salary_range = None
            if job["salary_info"]:
                min_salaries = []
                max_salaries = []
                
                for salary in job["salary_info"]:
                    try:
                        min_sal = int(salary.get("min_salary", "0"))
                        max_sal = int(salary.get("max_salary", "0"))
                        
                        if min_sal > 0:
                            min_salaries.append(min_sal)
                        if max_sal > 0:
                            max_salaries.append(max_sal)
                    except (ValueError, TypeError):
                        continue
                
                if min_salaries and max_salaries:
                    salary_range = {
                        "min": min(min_salaries),
                        "max": max(max_salaries)
                    }
            
            # Create summary
            summary = {
                "title": job["title"],
                "description": description,
                "key_responsibilities": responsibilities,
                "categorized_skills": categorized_skills,
                "salary_range": salary_range
            }
            
            job_summaries[job_id] = summary
        
        return job_summaries
    
    def process_and_enrich_data(self) -> Dict[str, Any]:
        """
        Process and enrich the job data with additional analysis
        
        Returns:
            Dictionary with enriched data and analysis
        """
        # Load processed jobs if not already loaded
        if not self.processed_jobs:
            self.load_processed_jobs()
            
        if not self.processed_jobs:
            logger.error("No processed job data available. Please run data processing first.")
            return {}
        
        # Run various analyses
        logger.info("Extracting common skills by job category...")
        common_skills = self.extract_common_skills()
        
        logger.info("Calculating salary statistics...")
        salary_stats = self.calculate_salary_statistics()
        
        logger.info("Finding related jobs...")
        related_jobs = self.find_related_jobs()
        
        logger.info("Analyzing career paths...")
        career_paths = self.analyze_career_paths()
        
        logger.info("Generating job summaries...")
        job_summaries = self.generate_job_summaries()
        
        # Combine all enriched data
        enriched_data = {
            "common_skills": common_skills,
            "salary_statistics": salary_stats,
            "related_jobs": related_jobs,
            "career_paths": career_paths,
            "job_summaries": job_summaries
        }
        
        # Save enriched data to JSON file
        output_file = os.path.join(self.output_folder, "enriched_job_data.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(enriched_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved enriched job data to {output_file}")
        
        return enriched_data
    
    def prepare_for_vector_db(self) -> Dict[str, Any]:
        """
        Prepare structured data for loading into a vector database
        
        Returns:
            Dictionary with data ready for vector database
        """
        # Load embedding data if available
        embedding_file = os.path.join(self.input_folder, "embedding_data.json")
        
        try:
            with open(embedding_file, 'r', encoding='utf-8') as f:
                embedding_data = json.load(f)
            logger.info(f"Loaded {len(embedding_data)} embedding chunks from {embedding_file}")
        except FileNotFoundError:
            logger.error(f"Could not find embedding data file: {embedding_file}")
            return {}
        
        # Enhance embedding data with additional metadata
        enhanced_embedding_data = []
        
        for chunk in embedding_data:
            chunk_text = chunk["text"]
            metadata = chunk["metadata"]
            job_id = metadata.get("job_id", "")
            
            # Add display name if available
            for job in self.processed_jobs:
                if job["id"] == job_id:
                    metadata["display_title"] = job["title"]
                    break
            
            # Set content type
            chunk_type = metadata.get("chunk_type", "")
            metadata["content_type"] = "job_knowledge"
            
            # Add language (assuming content is in Thai)
            metadata["language"] = "th"
            
            # Add to enhanced data
            enhanced_embedding_data.append({
                "text": chunk_text,
                "metadata": metadata
            })
        
        # Save enhanced embedding data
        output_file = os.path.join(self.output_folder, "vector_db_data.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(enhanced_embedding_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved vector database data to {output_file}")
        
        return {"chunks": enhanced_embedding_data}


def main():
    """Main function to run the data processor"""
    processor = EnhancedDataProcessor(
        input_folder="data/processed",
        output_folder="data/processed/enriched"
    )
    
    # Process and enrich job data
    enriched_data = processor.process_and_enrich_data()
    logger.info("Data enrichment complete")
    
    # Prepare data for vector database
    vector_data = processor.prepare_for_vector_db()
    logger.info("Vector database preparation complete")


if __name__ == "__main__":
    main()