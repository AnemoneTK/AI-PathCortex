import json
import re
import unicodedata
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel
import psycopg2
from pgvector.psycopg2 import register_vector

class JobDataPreprocessor:
    def __init__(self, model_name="airesearch/wangchanberta-base-wiki-punctuation"):
        """
        Initialize preprocessor with text cleaning and embedding model
        
        Args:
            model_name: Hugging Face model for embeddings
        """
        # Initialize tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        
        # Database connection parameters (modify as needed)
        self.db_params = {
            'dbname': 'career_ai_db',
            'user': 'your_username',
            'password': 'your_password',
            'host': 'localhost',
            'port': '5432'
        }
    
    def clean_text(self, text):
        """
        Clean and normalize text
        
        Args:
            text: Input text to clean
        
        Returns:
            Cleaned text
        """
        if not isinstance(text, str):
            return ""
        
        # Normalize unicode characters
        text = unicodedata.normalize('NFKD', text)
        
        # Remove special characters and extra whitespaces
        text = re.sub(r'[^\w\s]', '', text)
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def prepare_job_data(self, jobs_data):
        """
        Prepare job data by combining and cleaning relevant fields
        
        Args:
            jobs_data: Dictionary of job data
        
        Returns:
            Processed job data with cleaned text
        """
        processed_jobs = {}
        
        for job_id, job_info in jobs_data.items():
            # Combine relevant fields
            combined_text = " ".join([
                self.clean_text(job_info.get('description', '')),
                " ".join(self.clean_text(resp) for resp in job_info.get('responsibilities', [])),
                " ".join(self.clean_text(skill) for skill in job_info.get('skills', []))
            ])
            
            processed_jobs[job_id] = {
                'id': job_id,
                'title': self.clean_text(job_info.get('title', '')),
                'text': combined_text
            }
        
        return processed_jobs
    
    def create_embeddings(self, processed_jobs):
        """
        Create embeddings for processed job data
        
        Args:
            processed_jobs: Dictionary of processed job data
        
        Returns:
            Dictionary of job embeddings
        """
        embeddings = {}
        
        for job_id, job_data in processed_jobs.items():
            # Tokenize and create embedding
            inputs = self.tokenizer(
                job_data['text'], 
                return_tensors="pt", 
                truncation=True, 
                max_length=512
            )
            
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            # Mean pooling to get sentence embedding
            embedding = outputs.last_hidden_state.mean(dim=1).numpy().flatten()
            
            embeddings[job_id] = embedding
        
        return embeddings
    
    def chunk_embeddings(self, embeddings, chunk_size=100):
        """
        Chunk large embeddings for storage and processing
        
        Args:
            embeddings: Dictionary of embeddings
            chunk_size: Size of each chunk
        
        Returns:
            List of chunked embeddings
        """
        chunked_embeddings = []
        
        for job_id, embedding in embeddings.items():
            # Split large embedding into chunks
            chunks = [
                embedding[i:i+chunk_size] 
                for i in range(0, len(embedding), chunk_size)
            ]
            
            for i, chunk in enumerate(chunks):
                chunked_embeddings.append({
                    'job_id': job_id,
                    'chunk_index': i,
                    'embedding': chunk
                })
        
        return chunked_embeddings
    
    def store_embeddings_in_postgres(self, chunked_embeddings):
        """
        Store embeddings in PostgreSQL with pgvector
        
        Args:
            chunked_embeddings: List of chunked embeddings
        """
        try:
            # Establish connection
            conn = psycopg2.connect(**self.db_params)
            
            # Register vector extension
            register_vector(conn)
            
            # Create cursor
            cur = conn.cursor()
            
            # Create table if not exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS job_embeddings (
                    id SERIAL PRIMARY KEY,
                    job_id TEXT,
                    chunk_index INTEGER,
                    embedding vector(768)
                )
            """)
            
            # Insert embeddings
            for embed_data in chunked_embeddings:
                cur.execute(
                    "INSERT INTO job_embeddings (job_id, chunk_index, embedding) VALUES (%s, %s, %s)",
                    (
                        embed_data['job_id'], 
                        embed_data['chunk_index'], 
                        embed_data['embedding']
                    )
                )
            
            # Commit and close
            conn.commit()
            cur.close()
            conn.close()
            
            print(f"Stored {len(chunked_embeddings)} embedding chunks")
        
        except Exception as e:
            print(f"Error storing embeddings: {e}")
    
    def process_and_store_job_embeddings(self, jobs_data_path):
        """
        Full pipeline: load, preprocess, embed, and store job data
        
        Args:
            jobs_data_path: Path to jobs JSON file
        """
        # Load job data
        with open(jobs_data_path, 'r', encoding='utf-8') as f:
            jobs_data = json.load(f)
        
        # Prepare job data
        processed_jobs = self.prepare_job_data(jobs_data)
        
        # Create embeddings
        embeddings = self.create_embeddings(processed_jobs)
        
        # Chunk embeddings
        chunked_embeddings = self.chunk_embeddings(embeddings)
        
        # Store in PostgreSQL
        self.store_embeddings_in_postgres(chunked_embeddings)

def main():
    # Create preprocessor instance
    preprocessor = JobDataPreprocessor()
    
    # Process and store job embeddings
    preprocessor.process_and_store_job_embeddings(
        'backend/data/processed/merged_jobs.json'
    )

if __name__ == "__main__":
    main()