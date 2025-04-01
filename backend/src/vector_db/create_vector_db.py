#!/usr/bin/env python3
"""
Script to create a FAISS vector database from processed job data.
This allows semantic search of job information.
"""

import os
import sys
import json
import logging
import argparse
import numpy as np
from typing import Dict, List, Any, Optional
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("src/logs/vector_db.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("vector_db_creator")

# Check for required packages
try:
    import faiss
    from sentence_transformers import SentenceTransformer
except ImportError:
    logger.error("Required packages not found. Please install with:")
    logger.error("pip install faiss-cpu sentence-transformers")
    sys.exit(1)

class VectorDBCreator:
    """
    Class to create a FAISS vector database from text data
    """
    def __init__(
        self,
        input_file: str,
        output_dir: str,
        model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"
    ):
        """
        Initialize the vector database creator
        
        Args:
            input_file: Path to input JSON file with text chunks
            output_dir: Directory to save the vector database
            model_name: Name of the sentence transformer model to use
        """
        self.input_file = input_file
        self.output_dir = output_dir
        self.model_name = model_name
        self.model = None
        self.chunks = []
        self.metadata = []
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.info(f"Created output directory: {output_dir}")
    
    def load_data(self) -> int:
        """
        Load text chunks from the input file
        
        Returns:
            Number of chunks loaded
        """
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different possible structures
            if isinstance(data, list):
                chunks = data
            elif isinstance(data, dict) and 'chunks' in data:
                chunks = data['chunks']
            else:
                logger.error(f"Unexpected data structure in {self.input_file}")
                return 0
            
            # Extract text and metadata
            for chunk in chunks:
                if 'text' in chunk and chunk['text'].strip():
                    self.chunks.append(chunk['text'])
                    self.metadata.append(chunk.get('metadata', {}))
            
            logger.info(f"Loaded {len(self.chunks)} chunks from {self.input_file}")
            return len(self.chunks)
        
        except Exception as e:
            logger.error(f"Error loading data from {self.input_file}: {str(e)}")
            return 0
    
    def load_model(self) -> bool:
        """
        Load the sentence transformer model
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Loading sentence transformer model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Model loaded successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            return False
    
    def create_index(self) -> Optional[faiss.Index]:
        """
        Create a FAISS index from the text chunks
        
        Returns:
            FAISS index or None if failed
        """
        if not self.chunks:
            logger.error("No chunks to index")
            return None
        
        if not self.model:
            if not self.load_model():
                return None
        
        try:
            # Encode text chunks to embeddings
            logger.info(f"Encoding {len(self.chunks)} chunks to embeddings")
            embeddings = self.model.encode(self.chunks, show_progress_bar=True)
            
            # Get dimension of embeddings
            dimension = embeddings.shape[1]
            logger.info(f"Embedding dimension: {dimension}")
            
            # Create FAISS index
            logger.info("Creating FAISS index")
            index = faiss.IndexFlatL2(dimension)
            
            # Add embeddings to index
            faiss.normalize_L2(embeddings)
            index = faiss.IndexIDMap(index)
            index.add_with_ids(embeddings, np.array(range(len(embeddings))))
            
            logger.info(f"Created FAISS index with {index.ntotal} vectors")
            return index
        
        except Exception as e:
            logger.error(f"Error creating index: {str(e)}")
            return None
    
    def save_index(self, index: faiss.Index) -> bool:
        """
        Save the FAISS index and metadata
        
        Args:
            index: FAISS index to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Save FAISS index
            index_path = os.path.join(self.output_dir, "faiss_index")
            logger.info(f"Saving FAISS index to {index_path}")
            faiss.write_index(index, index_path)
            
            # Save metadata
            metadata_path = os.path.join(self.output_dir, "metadata.json")
            logger.info(f"Saving metadata to {metadata_path}")
            
            # Create metadata file with mapping from index to chunk metadata
            metadata_dict = {
                "count": len(self.metadata),
                "items": self.metadata,
                "model": self.model_name
            }
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata_dict, f, ensure_ascii=False, indent=2)
            
            # Save chunks for reference
            chunks_path = os.path.join(self.output_dir, "chunks.json")
            logger.info(f"Saving chunks to {chunks_path}")
            
            chunks_dict = {
                "count": len(self.chunks),
                "items": self.chunks
            }
            
            with open(chunks_path, 'w', encoding='utf-8') as f:
                json.dump(chunks_dict, f, ensure_ascii=False, indent=2)
            
            logger.info("Vector database created successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error saving index: {str(e)}")
            return False
    
    def create_database(self) -> bool:
        """
        Create the vector database
        
        Returns:
            True if successful, False otherwise
        """
        # Load data
        if not self.load_data():
            return False
        
        # Create index
        index = self.create_index()
        if index is None:
            return False
        
        # Save index and metadata
        return self.save_index(index)


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Create a FAISS vector database from processed job data",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Required arguments
    parser.add_argument(
        "--input", 
        required=True,
        help="Path to input JSON file with text chunks"
    )
    
    parser.add_argument(
        "--output", 
        required=True,
        help="Directory to save the vector database"
    )
    
    # Optional arguments
    parser.add_argument(
        "--model",
        default="paraphrase-multilingual-MiniLM-L12-v2",
        help="Name of the sentence transformer model to use"
    )
    
    return parser.parse_args()


def main() -> int:
    """
    Main function
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Parse arguments
    args = parse_arguments()
    
    logger.info("Starting vector database creation")
    
    # Create vector database
    creator = VectorDBCreator(
        input_file=args.input,
        output_dir=args.output,
        model_name=args.model
    )
    
    if creator.create_database():
        logger.info("Vector database created successfully")
        return 0
    else:
        logger.error("Failed to create vector database")
        return 1


if __name__ == "__main__":
    sys.exit(main())