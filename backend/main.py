#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Career AI Data Pipeline

Main script to orchestrate the entire data processing workflow for the Career Advisor AI project.
This script handles:
1. Scrape job data from JobsDB
2. Convert scraped text to JSON
3. Web scraping job responsibilities
4. Web scraping salary information
5. Normalizing and merging job data
6. Preprocessing data for embeddings
"""

import os
import sys
import logging
import subprocess
from datetime import datetime
from pathlib import Path

# Import custom modules
from src.data_collection.jobsdb_scraper import JobsDBScraper
from src.data_collection.jobsdb_to_json import TextToJsonConverterFixed
from src.data_collection.responsibility_scraper import JobResponsibilityScraper
from src.data_collection.salary_scraper import ISMTechSalaryScraper
from src.data_processing.job_normalizer import JSONJobNormalizer
from src.data_processing.job_data_preprocessor import JobDataPreprocessor

# Add colorama for terminal coloring
import colorama
colorama.init()

# Logging configuration
class LoggerConfig:
    """Configuration for logging"""
    @staticmethod
    def setup_logging():
        """Set up logging with both file and console handlers"""
        # Create logs directory if it doesn't exist
        log_dir = Path("src/logs")
        log_dir.mkdir(parents=True, exist_ok=True)

        # Create a unique log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"career_data_pipeline_{timestamp}.log"

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        return log_file

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def run_jobsdb_scraper():
    """
    Run JobsDB web scraper to get job descriptions
    
    Returns:
        dict: Result of scraping job data
    """
    print(f"\n{Colors.HEADER}===== Running JobsDB Scraper ====={Colors.ENDC}")
    
    try:
        # Initialize the scraper
        scraper = JobsDBScraper(
            output_folder="data/raw/jobsdb",
            max_workers=5
        )
        
        # Run the scraper
        return scraper.scrape_all_jobs()
    except ImportError:
        print(f"{Colors.FAIL}Failed to import JobsDBScraper module. Skipping this step.{Colors.ENDC}")
        return {"success": 0, "failed": 0, "total": 0}
    except Exception as e:
        print(f"{Colors.FAIL}Error running JobsDB scraper: {str(e)}{Colors.ENDC}")
        return {"success": 0, "failed": 0, "total": 0, "error": str(e)}

def convert_text_to_json():
    """
    Convert scraped text files to structured JSON data
    
    Returns:
        dict: Result of text to JSON conversion
    """
    print(f"\n{Colors.HEADER}===== Converting Text to JSON ====={Colors.ENDC}")
    
    try:
        
        # Initialize the converter
        converter = TextToJsonConverterFixed(
            input_folder="data/raw/jobsdb",
            output_folder="data/json",
            output_filename="jobs_data.json"
        )
        
        # Run the converter
        return converter.convert()
    except ImportError:
        print(f"{Colors.FAIL}Failed to import TextToJsonConverterFixed module. Skipping this step.{Colors.ENDC}")
        return {"success": False, "jobs_count": 0}
    except Exception as e:
        print(f"{Colors.FAIL}Error converting text to JSON: {str(e)}{Colors.ENDC}")
        return {"success": False, "jobs_count": 0, "error": str(e)}

def fetch_job_responsibilities():
    """
    Fetch job responsibilities from Talance website
    
    Returns:
        dict: Result of scraping job responsibilities
    """
    print(f"\n{Colors.HEADER}===== Fetching Job Responsibilities ====={Colors.ENDC}")
    
    scraper = JobResponsibilityScraper(
        url="https://www.talance.tech/blog/it-job-responsibility/", 
        output_folder="data/json", 
        filename="job_responsibilities.json"
    )
    
    return scraper.scrape()

def fetch_salary_data():
    """
    Fetch salary data from ISM Technology website
    
    Returns:
        dict: Result of scraping salary data
    """
    print(f"\n{Colors.HEADER}===== Fetching Salary Data ====={Colors.ENDC}")
    
    scraper = ISMTechSalaryScraper(
        url="https://www.ismtech.net/th/it-salary-report/", 
        output_folder="data/json", 
        filename="it_salary_data.json"
    )
    
    return scraper.scrape()

def normalize_job_data():
    """
    Normalize and merge job data from different sources
    
    Returns:
        dict: Merged job data
    """
    print(f"\n{Colors.HEADER}===== Normalizing Job Data ====={Colors.ENDC}")
    
    normalizer = JSONJobNormalizer(
        raw_data_folder="data/json", 
        output_folder="data/processed"
    )
    
    return normalizer.process_job_data()

def preprocess_job_data(merged_jobs):
    """
    Preprocess job data for embedding
    
    Args:
        merged_jobs (dict): Merged job data
    
    Returns:
        dict: Preprocessed job data
    """
    print(f"\n{Colors.HEADER}===== Preprocessing Job Data ====={Colors.ENDC}")
    
    preprocessor = JobDataPreprocessor()
    
    # Process merged jobs file
    processed_jobs = preprocessor.process_jobs_file(
        input_file_path="data/processed/merged_jobs.json", 
        output_file_path="data/processed/cleaned_jobs.json"
    )
    
    return processed_jobs

def main():
    """
    Main function to run the entire data pipeline
    """
    # Setup logging
    log_file = LoggerConfig.setup_logging()
    logger = logging.getLogger("career_data_pipeline")

    try:
        # Start timing the entire pipeline
        start_time = datetime.now()
        
        print(f"\n{Colors.BOLD}===== Career AI Data Pipeline ====={Colors.ENDC}")
        print(f"{Colors.CYAN}🚀 Pipeline started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")

        # Create necessary directories
        Path("data/raw/jobsdb").mkdir(parents=True, exist_ok=True)
        Path("data/raw/other_sources").mkdir(parents=True, exist_ok=True)
        Path("data/json").mkdir(parents=True, exist_ok=True)
        Path("data/processed").mkdir(parents=True, exist_ok=True)

        # 1. Scrape job data from JobsDB
        jobsdb_result = run_jobsdb_scraper()
        
        # 2. Convert scraped text to JSON
        json_result = convert_text_to_json()
        
        # 3. Fetch Job Responsibilities
        resp_result = fetch_job_responsibilities()
        
        # 4. Fetch Salary Data
        salary_result = fetch_salary_data()
        
        # 5. Normalize Job Data
        merged_jobs = normalize_job_data()
        
        # 6. Preprocess Job Data
        processed_jobs = preprocess_job_data(merged_jobs)
        
        # End timing
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Summary
        print(f"\n{Colors.HEADER}===== Pipeline Summary ====={Colors.ENDC}")
        
        # JobsDB scraper results
        if "total" in jobsdb_result:
            print(f"{Colors.GREEN}✅ JobsDB Jobs Scraped: {jobsdb_result.get('success', 0)}/{jobsdb_result.get('total', 0)}{Colors.ENDC}")
        
        # Text to JSON conversion results
        if "jobs_count" in json_result:
            print(f"{Colors.GREEN}✅ Jobs Converted to JSON: {json_result.get('jobs_count', 0)} jobs{Colors.ENDC}")
        
        # Other results
        print(f"{Colors.GREEN}✅ Job Responsibilities Scraped: {resp_result['jobs_count']} jobs{Colors.ENDC}")
        print(f"{Colors.GREEN}✅ Salary Data Scraped: {salary_result['jobs_count']} jobs{Colors.ENDC}")
        print(f"{Colors.GREEN}✅ Jobs Normalized: {len(merged_jobs)} job groups{Colors.ENDC}")
        print(f"{Colors.GREEN}✅ Jobs Preprocessed: {len(processed_jobs)} jobs{Colors.ENDC}")
        print(f"\n{Colors.CYAN}⏱️  Total Pipeline Duration: {duration}{Colors.ENDC}")
        print(f"{Colors.CYAN}📄 Detailed logs: {log_file}{Colors.ENDC}")
        
        print(f"\n{Colors.BOLD}{Colors.GREEN}🎉 Data Pipeline Completed Successfully! 🎉{Colors.ENDC}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        print(f"\n{Colors.FAIL}❌ Pipeline Failed: {str(e)}{Colors.ENDC}")
        print(f"{Colors.CYAN}📄 Check log file for details: {log_file}{Colors.ENDC}")
        sys.exit(1)

if __name__ == "__main__":
    main()