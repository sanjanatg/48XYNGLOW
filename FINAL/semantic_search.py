import numpy as np
import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer
import torch

class SemanticSearch:
    def __init__(self, fund_data, model_name="all-MiniLM-L6-v2"):
        """
        Initialize semantic search with fund data
        
        Args:
            fund_data: pandas DataFrame containing fund information with at least
                      'fund_name' and 'description' columns
            model_name: name of the sentence-transformers model to use
        """
        self.fund_data = fund_data
        self.corpus = self.fund_data['description'].tolist()
        
        # Load model
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        
        # Get embedding dimension
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        
        # Create FAISS index
        self._create_index()
        
    def _create_index(self):
        """Create FAISS index from fund descriptions"""
        # Generate embeddings for all fund descriptions
        print("Generating embeddings for fund corpus...")
        self.corpus_embeddings = self.model.encode(
            self.corpus, 
            show_progress_bar=True, 
            convert_to_numpy=True
        )
        
        # Normalize embeddings to unit length for cosine similarity
        faiss.normalize_L2(self.corpus_embeddings)
        
        # Create FAISS index
        self.index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product for cosine similarity
        self.index.add(self.corpus_embeddings)
        
        print(f"FAISS index created with {self.index.ntotal} vectors")
        
    def search(self, query, top_k=10):
        """
        Search for funds semantically similar to the query
        
        Args:
            query: query string
            top_k: number of top results to return (default 10)
            
        Returns:
            list of dictionaries with fund details and similarity scores
        """
        # Generate embedding for the query
        query_embedding = self.model.encode(query)
        
        # Normalize query embedding for cosine similarity
        faiss.normalize_L2(np.reshape(query_embedding, (1, -1)))
        
        # Search the index
        scores, indices = self.index.search(np.reshape(query_embedding, (1, -1)), k=top_k)
        
        # Return fund details with scores
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < 0 or idx >= len(self.corpus):
                continue  # Skip invalid indices
                
            fund_details = self.fund_data.iloc[idx].to_dict()
            fund_details['semantic_score'] = float(scores[0][i])  # Convert to native Python float
            results.append(fund_details)
        
        return results

# Example usage
if __name__ == "__main__":
    # Check if CUDA is available
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"Using GPU: {torch.cuda.get_device_name(0)}")
    
    # Sample data for testing
    sample_data = pd.DataFrame({
        'fund_name': ['HDFC Technology Fund', 'SBI Healthcare Fund', 'ICICI Low Risk Bond Fund'],
        'description': [
            'HDFC Technology Fund invests in technology companies focusing on innovation and growth.',
            'SBI Healthcare Fund focuses on pharmaceutical and healthcare sector for long-term growth.',
            'ICICI Low Risk Bond Fund is a debt fund with conservative approach for stable returns.'
        ]
    })
    
    semantic_search = SemanticSearch(sample_data)
    results = semantic_search.search("I need a fund for tech innovation")
    
    print("\nTop semantic matches:")
    for result in results:
        print(f"{result['fund_name']}: {result['semantic_score']:.4f}") 