#!/usr/bin/env python3
"""
FastAPI application for IT Career Advisor API.
Provides endpoints for job information, semantic search, and career recommendations.
"""

import os
import sys
import json
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("career_api")

# Check for required packages
try:
    import faiss
    from fastapi import FastAPI, HTTPException, Query, Depends
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field
    from sentence_transformers import SentenceTransformer
except ImportError:
    logger.error("Required packages not found. Please install with:")
    logger.error("pip install fastapi uvicorn faiss-cpu sentence-transformers")
    sys.exit(1)

# Define path to data
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
ENRICHED_DIR = PROCESSED_DIR / "enriched"
VECTOR_DB_DIR = DATA_DIR / "vector_db"

# Initialize FastAPI app
app = FastAPI(
    title="IT Career Advisor API",
    description="API for accessing IT career information, job recommendations, and more",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class JobBasic(BaseModel):
    id: str
    title: str
    description: str = Field(default="")
    
class JobDetail(JobBasic):
    descriptions: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    salary_info: List[Dict[str, Any]] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)

class JobSummary(BaseModel):
    id: str
    title: str
    description: str
    key_responsibilities: List[str] = Field(default_factory=list)
    categorized_skills: Dict[str, List[str]] = Field(default_factory=dict)
    salary_range: Optional[Dict[str, int]] = None

class SearchResult(BaseModel):
    id: str
    title: str
    chunk_type: str
    text: str
    score: float
    
class SalaryStats(BaseModel):
    min: int
    max: int
    avg: float
    count: int

class RelatedJob(BaseModel):
    id: str
    title: str
    similarity: float
    common_skills: List[str] = Field(default_factory=list)


# Load data on startup
job_data: List[Dict[str, Any]] = []
job_summaries: Dict[str, Any] = {}
salary_stats: Dict[str, Any] = {}
related_jobs: Dict[str, Any] = {}
vector_index: Optional[faiss.Index] = None
vector_metadata: List[Dict[str, Any]] = []
vector_chunks: List[str] = []
embedding_model = None

@app.on_event("startup")
async def startup_event():
    global job_data, job_summaries, salary_stats, related_jobs
    global vector_index, vector_metadata, vector_chunks, embedding_model
    
    # Load processed job data
    try:
        job_data_path = PROCESSED_DIR / "processed_jobs.json"
        with open(job_data_path, 'r', encoding='utf-8') as f:
            job_data = json.load(f)
        logger.info(f"Loaded {len(job_data)} job records from {job_data_path}")
    except Exception as e:
        logger.error(f"Error loading job data: {str(e)}")
        job_data = []
    
    # Load enriched data
    try:
        enriched_data_path = ENRICHED_DIR / "enriched_job_data.json"
        with open(enriched_data_path, 'r', encoding='utf-8') as f:
            enriched_data = json.load(f)
            
        job_summaries = enriched_data.get("job_summaries", {})
        salary_stats = enriched_data.get("salary_statistics", {})
        related_jobs = enriched_data.get("related_jobs", {})
        
        logger.info(f"Loaded enriched data with {len(job_summaries)} job summaries")
    except Exception as e:
        logger.error(f"Error loading enriched data: {str(e)}")
        job_summaries = {}
        salary_stats = {}
        related_jobs = {}
    
    # Load vector database if available
    try:
        index_path = VECTOR_DB_DIR / "faiss_index"
        metadata_path = VECTOR_DB_DIR / "metadata.json"
        chunks_path = VECTOR_DB_DIR / "chunks.json"
        
        if index_path.exists() and metadata_path.exists() and chunks_path.exists():
            # Load index
            vector_index = faiss.read_index(str(index_path))
            
            # Load metadata
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata_dict = json.load(f)
                vector_metadata = metadata_dict.get("items", [])
            
            # Load chunks
            with open(chunks_path, 'r', encoding='utf-8') as f:
                chunks_dict = json.load(f)
                vector_chunks = chunks_dict.get("items", [])
            
            # Load embedding model
            model_name = metadata_dict.get("model", "paraphrase-multilingual-MiniLM-L12-v2")
            embedding_model = SentenceTransformer(model_name)
            
            logger.info(f"Loaded vector database with {len(vector_chunks)} chunks")
        else:
            logger.warning("Vector database not found")
    except Exception as e:
        logger.error(f"Error loading vector database: {str(e)}")
        vector_index = None
        vector_metadata = []
        vector_chunks = []
        embedding_model = None


# Helper function to get job by ID
def get_job_by_id(job_id: str) -> Optional[Dict[str, Any]]:
    for job in job_data:
        if job.get("id") == job_id:
            return job
    return None


# Routes
@app.get("/")
async def root():
    """Root endpoint returning API info"""
    return {
        "name": "IT Career Advisor API",
        "version": "1.0.0",
        "status": "online",
        "endpoints": [
            "/jobs", 
            "/jobs/{job_id}", 
            "/jobs/summary/{job_id}",
            "/search",
            "/salary-stats/{job_id}",
            "/related-jobs/{job_id}"
        ]
    }

@app.get("/jobs", response_model=List[JobBasic])
async def list_jobs():
    """Get a list of all jobs with basic information"""
    if not job_data:
        raise HTTPException(status_code=404, detail="No job data available")
    
    basic_jobs = []
    for job in job_data:
        description = job.get("descriptions", [""])[0] if job.get("descriptions") else ""
        basic_jobs.append({
            "id": job.get("id", ""),
            "title": job.get("title", ""),
            "description": description
        })
    
    return basic_jobs

@app.get("/jobs/{job_id}", response_model=JobDetail)
async def get_job(job_id: str):
    """Get detailed information about a specific job"""
    job = get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")
    
    # Default description to first description if available
    description = job.get("descriptions", [""])[0] if job.get("descriptions") else ""
    
    return {
        "id": job.get("id", ""),
        "title": job.get("title", ""),
        "description": description,
        "descriptions": job.get("descriptions", []),
        "responsibilities": job.get("responsibilities", []),
        "skills": job.get("skills", []),
        "salary_info": job.get("salary_info", []),
        "sources": job.get("sources", [])
    }

@app.get("/jobs/summary/{job_id}", response_model=JobSummary)
async def get_job_summary(job_id: str):
    """Get a summarized view of a job with categorized skills"""
    if job_id not in job_summaries:
        raise HTTPException(status_code=404, detail=f"Job summary for ID {job_id} not found")
    
    summary = job_summaries[job_id]
    return {
        "id": job_id,
        "title": summary.get("title", ""),
        "description": summary.get("description", ""),
        "key_responsibilities": summary.get("key_responsibilities", []),
        "categorized_skills": summary.get("categorized_skills", {}),
        "salary_range": summary.get("salary_range")
    }

@app.get("/search", response_model=List[SearchResult])
async def search_jobs(
    query: str = Query(..., description="Search query"),
    limit: int = Query(5, description="Number of results to return"),
    threshold: float = Query(0.5, description="Minimum similarity score (0-1)")
):
    """Search for jobs using semantic search"""
    if not vector_index or not embedding_model or not vector_chunks:
        raise HTTPException(status_code=503, detail="Vector search not available")
    
    try:
        # Encode query to embedding
        query_embedding = embedding_model.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # Search in vector index
        scores, indices = vector_index.search(query_embedding, limit * 2)
        
        # Filter results by threshold and prepare response
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if score < threshold or idx >= len(vector_chunks):
                continue
                
            metadata = vector_metadata[idx] if idx < len(vector_metadata) else {}
            job_id = metadata.get("job_id", "")
            job_title = metadata.get("job_title", "")
            chunk_type = metadata.get("chunk_type", "unknown")
            
            results.append({
                "id": job_id,
                "title": job_title,
                "chunk_type": chunk_type,
                "text": vector_chunks[idx],
                "score": float(score)
            })
            
            if len(results) >= limit:
                break
        
        return results
    
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error performing search")

@app.get("/salary-stats/{job_id}", response_model=Dict[str, SalaryStats])
async def get_salary_stats(job_id: str):
    """Get salary statistics for a specific job"""
    if job_id not in salary_stats:
        raise HTTPException(status_code=404, detail=f"Salary statistics for job ID {job_id} not found")
    
    return salary_stats[job_id]

@app.get("/related-jobs/{job_id}", response_model=List[RelatedJob])
async def get_related_jobs(job_id: str):
    """Get jobs related to a specific job"""
    if job_id not in related_jobs:
        raise HTTPException(status_code=404, detail=f"Related jobs for ID {job_id} not found")
    
    return related_jobs[job_id]


# Run the API server if executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)