import os
import pickle
import numpy as np
import pandas as pd
import json
from sentence_transformers import SentenceTransformer
import faiss
from pathlib import Path

class SearchEngine:
    def __init__(self, model_name="BAAI/bge-small-en-v1.5", 
                 embeddings_path=None, funds_data_path=None):
        """
        Initialize the search engine with the embedding model and data.
        
        Args:
            model_name: The name of the SentenceTransformer model to use for embeddings
            embeddings_path: Path to the pickled embeddings
            funds_data_path: Path to the funds data CSV
        """
        # Set default paths if not provided
        self.base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Import config here to avoid circular imports
        import sys
        sys.path.append(str(self.base_dir))
        from config import FUNDS_DATA_PATH, EMBEDDINGS_PATH, INDEX_PATH, METADATA_PATH, MODEL_NAME
        
        self.model_name = model_name or MODEL_NAME
        self.embeddings_path = embeddings_path or EMBEDDINGS_PATH
        self.funds_data_path = funds_data_path or FUNDS_DATA_PATH
        self.index_path = INDEX_PATH
        self.metadata_path = METADATA_PATH
        
        print(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        
        # Load data and index
        self.load_data()
        self.load_index()
    
    def load_data(self):
        """Load fund data from CSV or JSON."""
        try:
            if os.path.exists(self.funds_data_path):
                self.data = pd.read_csv(self.funds_data_path)
                print(f"Loaded fund data from {self.funds_data_path}")
            else:
                print(f"Warning: Funds data file not found at {self.funds_data_path}")
                self.data = pd.DataFrame()
            
            # Load metadata if available
            if os.path.exists(self.metadata_path):
                with open(self.metadata_path, 'r') as f:
                    self.metadata = json.load(f)
                print(f"Loaded metadata from {self.metadata_path}")
            else:
                # Create metadata from data
                self.metadata = []
                for idx, row in self.data.iterrows():
                    self.metadata.append(dict(row))
        except Exception as e:
            print(f"Error loading data: {e}")
            self.data = pd.DataFrame()
            self.metadata = []
    
    def load_index(self):
        """Load index and embeddings from disk."""
        try:
            # Load embeddings
            if os.path.exists(self.embeddings_path):
                with open(self.embeddings_path, 'rb') as f:
                    self.embeddings = pickle.load(f)
                print(f"Loaded embeddings from {self.embeddings_path}")
            else:
                print(f"Warning: Embeddings file not found at {self.embeddings_path}")
                self.embeddings = None
            
            # Load index
            if os.path.exists(self.index_path):
                with open(self.index_path, 'rb') as f:
                    self.index = pickle.load(f)
                print(f"Loaded index from {self.index_path}")
            else:
                # Create empty index
                d = self.model.get_sentence_embedding_dimension()
                self.index = faiss.IndexFlatIP(d)
                print(f"Initialized empty index with dimension {d}")
        except Exception as e:
            print(f"Error loading index: {e}")
            d = self.model.get_sentence_embedding_dimension()
            self.index = faiss.IndexFlatIP(d)
    
    def search(self, query, top_k=5, filters=None):
        """
        Search for funds matching the query and optional filters.
        
        Args:
            query: The search query
            top_k: Number of results to return
            filters: Dictionary of metadata filters to apply
            
        Returns:
            List of fund dictionaries with metadata
        """
        if self.index.ntotal == 0:
            print("No index data available. Cannot perform search.")
            return []
        
        # Generate query embedding
        query_embedding = self.model.encode([query])[0]
        
        # Reshape for FAISS
        query_embedding = query_embedding.reshape(1, -1).astype(np.float32)
        
        # Normalize for cosine similarity
        faiss.normalize_L2(query_embedding)
        
        # Search index
        scores, indices = self.index.search(query_embedding, top_k*3)  # Get more results for filtering
        
        # Prepare results
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.metadata):
                # Get metadata for this fund
                fund = self.metadata[idx]
                
                # Add score
                fund['score'] = float(scores[0][i])
                
                # Apply filters if provided
                if filters and not self._apply_filters(fund, filters):
                    continue
                
                results.append(fund)
            
            # Stop once we have enough results
            if len(results) >= top_k:
                break
        
        return results
    
    def _apply_filters(self, fund, filters):
        """Apply filters to a fund to determine if it should be included."""
        for key, value in filters.items():
            if key not in fund:
                continue
            
            # Handle different filter types
            if isinstance(value, dict):
                # Range filter (min/max)
                if 'min' in value and fund[key] < value['min']:
                    return False
                if 'max' in value and fund[key] > value['max']:
                    return False
            elif isinstance(value, list):
                # List of possible values
                if fund[key] not in value:
                    return False
            else:
                # Exact match
                if fund[key] != value:
                    return False
        
        return True 