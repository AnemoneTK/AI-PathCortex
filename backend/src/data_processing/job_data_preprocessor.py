import json
import re
import unicodedata

class JobDataPreprocessor:
    @staticmethod
    def clean_text(text):
        """
        Comprehensive text cleaning method
        
        Args:
            text (str): Input text to clean
        
        Returns:
            str: Cleaned text
        """
        # Handle non-string inputs
        if not isinstance(text, str):
            return ""
        
        # Normalize unicode characters (convert to standard form)
        text = unicodedata.normalize('NFKD', text)
        
        # Remove special characters and punctuation
        text = re.sub(r'[^\u0E00-\u0E7Fa-zA-Z0-9\s]', '', text)
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def prepare_job_data(self, jobs_data):
        """
        Prepare job data by combining and cleaning relevant fields
        
        Args:
            jobs_data (dict): Dictionary of job data
        
        Returns:
            dict: Processed job data with cleaned text
        """
        processed_jobs = {}
        
        for job_id, job_info in jobs_data.items():
            # Skip unwanted entries (like scraping summary)
            if job_id.startswith('-') or '_' in job_id:
                continue
            
            # Combine and clean relevant text fields
            combined_text_parts = []
            
            # Add description if exists
            description = self.clean_text(job_info.get('description', ''))
            
            # Add responsibilities
            responsibilities = [
                self.clean_text(resp) 
                for resp in job_info.get('responsibilities', []) 
                if resp
            ]
            
            # Add skills
            skills = [
                self.clean_text(skill) 
                for skill in job_info.get('skills', []) 
                if skill
            ]
            
            # Combine text parts
            if description:
                combined_text_parts.append(description)
            if responsibilities:
                combined_text_parts.extend(responsibilities)
            if skills:
                combined_text_parts.extend(skills)
            
            # Prepare processed job entry
            processed_jobs[job_id] = {
                'id': job_id,
                'titles': job_info.get('titles', []),
                'description': description,
                'responsibilities': responsibilities,
                'skills': skills,
                'salary_info': job_info.get('salary_info', []),
                'cleaned_text': ' '.join(combined_text_parts)
            }
        
        return processed_jobs
    
    def process_jobs_file(self, input_file_path, output_file_path=None):
        """
        Process entire jobs file
        
        Args:
            input_file_path (str): Path to input JSON file
            output_file_path (str, optional): Path to save processed data
        
        Returns:
            dict: Processed job data
        """
        # Read input file
        with open(input_file_path, 'r', encoding='utf-8') as f:
            jobs_data = json.load(f)
        
        # Process job data
        processed_jobs = self.prepare_job_data(jobs_data)
        
        # Optionally save to output file
        if output_file_path:
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(processed_jobs, f, ensure_ascii=False, indent=2)
        
        return processed_jobs
    
    def print_sample_processed_jobs(self, processed_jobs, num_samples=5):
        """
        Print sample of processed jobs for verification
        
        Args:
            processed_jobs (dict): Processed job data
            num_samples (int): Number of samples to print
        """
        print("Sample Processed Jobs:")
        for i, (job_id, job_data) in enumerate(processed_jobs.items()):
            if i >= num_samples:
                break
            print(f"\nJob ID: {job_id}")
            print(f"Titles: {job_data['titles']}")
            print(f"Cleaned Text: {job_data['cleaned_text'][:300]}...")  # Print first 300 chars

def main():
    # Create preprocessor instance
    preprocessor = JobDataPreprocessor()
    
    # Process jobs file
    input_file = 'data/processed/merged_jobs.json'
    output_file = 'data/processed/cleaned_jobs.json'
    
    # Process and optionally save processed jobs
    processed_jobs = preprocessor.process_jobs_file(
        input_file, 
        output_file
    )
    
    # Print sample processed jobs
    preprocessor.print_sample_processed_jobs(processed_jobs)

if __name__ == "__main__":
    main()