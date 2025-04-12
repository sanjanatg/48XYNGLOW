import os
import numpy as np
import pandas as pd
import hnswlib
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple, Any, Optional
from loguru import logger

class SemanticSearch:
    """
    Semantic search implementation using sentence transformers and HNSW for ANN.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the semantic search module.
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model_name = model_name
        self.model = None
        self.index = None
        self.fund_data = None
        self.embedding_dim = None
        self.is_fitted = False
        self.ef_search = 50  # Store ef value for searching
        self.M = 16  # Store M value for the index
    
    def _load_model(self) -> None:
        """Load sentence transformer model."""
        if self.model is None:
            logger.info(f"Loading sentence transformer model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            logger.info(f"Model loaded with embedding dimension: {self.embedding_dim}")
    
    def fit(self, fund_data: pd.DataFrame, text_column: str = "combined_text", 
            index_params: Dict[str, Any] = None) -> None:
        """
        Fit the semantic search model on fund data.
        
        Args:
            fund_data: DataFrame containing fund information
            text_column: Column to use for embedding generation
            index_params: Parameters for HNSW index
        """
        self._load_model()
        self.fund_data = fund_data
        
        # Default index parameters
        if index_params is None:
            index_params = {
                "ef_construction": 200,  # Higher for better quality but slower indexing
                "M": 16,                 # Higher for better recall but more memory
            }
        
        # Store M value
        self.M = index_params["M"]
        
        # Get texts to embed
        texts = fund_data[text_column].values
        num_elements = len(texts)
        
        logger.info(f"Generating embeddings for {num_elements} funds...")
        
        # Generate embeddings
        embeddings = self.model.encode(texts, show_progress_bar=True, 
                                      convert_to_numpy=True)
        
        # Create HNSW index
        self.index = hnswlib.Index(space='cosine', dim=self.embedding_dim)
        self.index.init_index(max_elements=num_elements, 
                              ef_construction=index_params["ef_construction"], 
                              M=index_params["M"])
        
        # Add embeddings to index
        self.index.add_items(embeddings, list(range(num_elements)))
        
        # Set search parameters
        self.ef_search = 50  # Higher for better recall, lower for faster search
        self.index.set_ef(self.ef_search)
        
        self.is_fitted = True
        logger.info("Semantic search index built successfully")
    
    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search for funds semantically matching the query.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of dicts containing fund info and scores
        """
        if not self.is_fitted:
            raise ValueError("Semantic search model not fitted. Call fit() first.")
        
        # Generate query embedding
        query_embedding = self.model.encode(query)
        
        # Search in HNSW index
        indices, distances = self.index.knn_query(query_embedding, k=top_k)
        
        # Convert distances to similarities (cosine distance to similarity)
        similarities = 1 - distances[0]
        
        # Prepare results
        results = []
        for idx, similarity in zip(indices[0], similarities):
            fund_info = self.fund_data.iloc[idx].to_dict()
            fund_info['semantic_score'] = float(similarity)
            results.append(fund_info)
        
        logger.info(f"Semantic search for '{query}' returned {len(results)} results")
        return results
    
    def save_index(self, index_path: str = "models/hnsw_index.bin", 
                  metadata_path: str = "models/index_metadata.json") -> None:
        """
        Save the HNSW index to disk.
        
        Args:
            index_path: Path to save the index
            metadata_path: Path to save metadata
        """
        if not self.is_fitted:
            raise ValueError("Cannot save index; model not fitted.")
            
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        
        # Save index
        self.index.save_index(index_path)
        
        # Save metadata
        import json
        metadata = {
            "model_name": self.model_name,
            "embedding_dim": self.embedding_dim,
            "num_elements": len(self.fund_data),
            "ef": self.ef_search,  # Use stored ef value
            "M": self.M  # Use stored M value
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
            
        logger.info(f"Index saved to {index_path} and metadata to {metadata_path}")
    
    def load_index(self, index_path: str = "models/hnsw_index.bin", 
                  metadata_path: str = "models/index_metadata.json") -> None:
        """
        Load a saved HNSW index.
        
        Args:
            index_path: Path to the saved index
            metadata_path: Path to saved metadata
        """
        import json
        
        # Load metadata
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Initialize model if needed
        if self.model is None or self.model_name != metadata["model_name"]:
            self.model_name = metadata["model_name"]
            self._load_model()
        
        # Initialize index
        self.embedding_dim = metadata["embedding_dim"]
        self.index = hnswlib.Index(space='cosine', dim=self.embedding_dim)
        
        # Load index
        self.index.load_index(index_path, max_elements=metadata["num_elements"])
        
        # Set search parameters
        self.ef_search = metadata["ef"]
        self.index.set_ef(self.ef_search)
        self.M = metadata["M"]
        
        self.is_fitted = True
        logger.info(f"Loaded index from {index_path} with {metadata['num_elements']} elements") 