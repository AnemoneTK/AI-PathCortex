#!/usr/bin/env python3
"""
Main entry point for the IT Career Data Processing Pipeline.
This script orchestrates the data collection, processing, and analysis steps.
"""

import os
import argparse
import logging
import sys
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("src/logs/main.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("pipeline")

# Ensure we can import from src
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))

# Import pipeline components
try:
    from src.data_collection.jobsdb_scraper import JobsDBScraper
    from src.data_collection.ismtech_salary_scraper import ISMTechSalaryScraper
    from backend.src.data_collection.old.talance_scraper import TalanceScraper
    from src.data_collection.salary_extractor import SalaryExtractor
    from backend.src.data_processing.job_normalizer_old import JobNormalizer
    from src.data_processing.processor import EnhancedDataProcessor
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.error("Please make sure all required modules are installed and in the correct location.")
    sys.exit(1)


def setup_directories():
    """Create necessary directories if they don't exist"""
    directories = [
        "data/raw/other_sources",
        "data/raw/salary",
        "data/processed",
        "data/processed/enriched",
        "src/logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.debug(f"Ensured directory exists: {directory}")


def run_data_collection(args):
    """Run the data collection phase"""
    logger.info("Starting data collection phase")
    
    success = True
    
    # JobsDB Scraper
    if args.jobsdb or args.all:
        try:
            logger.info("Running JobsDB scraper")
            jobsdb_scraper = JobsDBScraper(output_folder="data/raw/jobsdb")
            jobsdb_results = jobsdb_scraper.scrape_all_jobs()
            logger.info(f"JobsDB scraping complete: {jobsdb_results}")
        except Exception as e:
            logger.error(f"Error in JobsDB scraper: {e}")
            success = False
    
    # ISM Tech Salary Scraper
    if args.salary or args.all:
        try:
            logger.info("Running ISM Tech salary scraper")
            salary_scraper = ISMTechSalaryScraper(output_folder="data/raw/salary")
            salary_results = salary_scraper.scrape()
            logger.info(f"Salary scraping complete: {salary_results}")
        except Exception as e:
            logger.error(f"Error in salary scraper: {e}")
            success = False
    
    # Talance Scraper
    if args.talance or args.all:
        try:
            logger.info("Running Talance scraper")
            talance_scraper = TalanceScraper(output_folder="data/raw/talance")
            talance_results = talance_scraper.scrape()
            logger.info(f"Talance scraping complete: {talance_results}")
        except Exception as e:
            logger.error(f"Error in Talance scraper: {e}")
            success = False
    # ISM Tech Salary Scraper
    if args.salary or args.all:
        try:
            logger.info("Running ISM Tech salary scraper")
            # เรียกใช้โดยใช้พารามิเตอร์ที่ถูกต้อง
            salary_scraper = ISMTechSalaryScraper(output_folder="data/raw/other_sources")
            # เรียกเมธอด scrape() ซึ่งเป็นเมธอดหลักที่ถูกต้อง
            salary_results = salary_scraper.scrape()
            logger.info(f"Salary scraping complete: {salary_results}")
        except Exception as e:
            logger.error(f"Error in salary scraper: {e}")
            logger.warning("Skipping salary scraping and continuing with the pipeline")

    # Salary Extractor
    # Salary Extractor
    if args.extract_salary or args.all:
        try:
            logger.info("Running salary extractor")
            # ใช้พารามิเตอร์ที่ถูกต้อง
            salary_extractor = SalaryExtractor(
                json_file_path='data/raw/other_sources/it_salary_data.json',
                output_folder='data/raw/salary'
            )
            # เรียกเมธอด extract_all() ที่ถูกต้อง
            extraction_results = salary_extractor.extract_all()
            logger.info(f"Salary extraction complete: {extraction_results}")
        except Exception as e:
            logger.error(f"Error in salary extractor: {e}")
            logger.warning("Skipping salary extraction and continuing with the pipeline")
    
    return success


def run_data_processing(args):
    """Run the data processing phase"""
    logger.info("Starting data processing phase")
    
    success = True
    
    # Job Normalizer
    if args.normalize or args.all:
        try:
            logger.info("Running job normalizer")
            normalizer = JobNormalizer(raw_data_folder="data/raw", output_folder="data/processed")
            normalization_results = normalizer.create_merged_files()
            logger.info(f"Job normalization complete: {normalization_results}")
        except Exception as e:
            logger.error(f"Error in job normalizer: {e}")
            success = False
    
    # Processor
    # Processor
    if args.process or args.all:
        try:
            logger.info("Running data processor")
            # สร้าง instance ของ EnhancedDataProcessor ก่อน
            processor = EnhancedDataProcessor(
                input_folder="data/processed", 
                output_folder="data/processed/enriched"
            )
            # เรียกเมธอด process_and_enrich_data() ผ่าน instance
            processing_results = processor.process_and_enrich_data()
            logger.info(f"Data processing complete: {processing_results}")
        except Exception as e:
            logger.error(f"Error in data processor: {e}")
            success = False
    
    return success


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="IT Career Data Processing Pipeline")
    
    # Phase selection
    parser.add_argument("--all", action="store_true", help="Run all pipeline phases")
    parser.add_argument("--collect", action="store_true", help="Run data collection phase")
    parser.add_argument("--process", action="store_true", help="Run data processing phase")
    
    # Data collection options
    parser.add_argument("--jobsdb", action="store_true", help="Run JobsDB scraper")
    parser.add_argument("--salary", action="store_true", help="Run salary scraper")
    parser.add_argument("--talance", action="store_true", help="Run Talance scraper")
    parser.add_argument("--extract-salary", action="store_true", help="Run salary extractor")
    
    # Data processing options
    parser.add_argument("--normalize", action="store_true", help="Run job normalizer")
    parser.add_argument("--enrich", action="store_true", help="Run data enrichment")
    
    # Other options
    parser.add_argument("--clean", action="store_true", help="Clean output directories before processing")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set defaults if no specific action is selected
    if not any([args.all, args.collect, args.process, args.jobsdb, args.salary, 
                args.talance, args.extract_salary, args.normalize, args.enrich]):
        args.all = True
    
    # Set verbose logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    return args


def main():
    """Main function to run the pipeline"""
    # Parse arguments
    args = parse_args()
    
    # Set up directories
    setup_directories()
    
    # Clean directories if requested
    if args.clean:
        logger.info("Cleaning output directories")
        directories_to_clean = ["data/processed", "data/processed/enriched"]
        for directory in directories_to_clean:
            if os.path.exists(directory):
                for item in os.listdir(directory):
                    item_path = os.path.join(directory, item)
                    if os.path.isfile(item_path):
                        os.unlink(item_path)
                    # Be careful with rmdir/rmtree as it can delete important data
    
    # Run pipeline phases
    success = True
    
    # Data collection phase
    if args.collect or args.all or args.jobsdb or args.salary or args.talance or args.extract_salary:
        if not run_data_collection(args):
            logger.error("Data collection phase failed")
            success = False
    
    # Data processing phase
    if success and (args.process or args.all or args.normalize or args.enrich):
        if not run_data_processing(args):
            logger.error("Data processing phase failed")
            success = False
    
    # Final status
    if success:
        logger.info("Pipeline completed successfully")
        return 0
    else:
        logger.error("Pipeline failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())