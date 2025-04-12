import numpy as np
import pandas as pd
from rank_bm25 import BM25Okapi
from typing import List, Dict, Tuple, Any
from loguru import logger

class LexicalSearch:
    """
    BM25 lexical search implementation for fund matching.
    """
    
    def __init__(self):
        """Initialize the lexical search module."""
        self.bm25 = None
        self.corpus = None
        self.fund_data = None
        self.is_fitted = False
    
    def preprocess_text(self, text: str) -> List[str]:
        """
        Preprocess text for BM25 indexing.
        
        Args:
            text: Input text
            
        Returns:
            List of tokenized words
        """
        # Simple preprocessing: lowercase and split by space
        # For production, consider more advanced tokenization (e.g., handling apostrophes, special characters)
        return text.lower().split()
    
    def fit(self, fund_data: pd.DataFrame, text_column: str = "fund_name") -> None:
        """
        Fit BM25 model on fund data.
        
        Args:
            fund_data: DataFrame containing fund information
            text_column: Column to use for BM25 indexing
        """
        self.fund_data = fund_data
        
        # Create corpus for BM25
        texts = fund_data[text_column].values
        tokenized_corpus = [self.preprocess_text(text) for text in texts]
        
        # Initialize and fit BM25
        self.bm25 = BM25Okapi(tokenized_corpus)
        self.corpus = tokenized_corpus
        self.is_fitted = True
        
        logger.info(f"BM25 lexical search fitted on {len(texts)} funds")
    
    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search for funds matching the query.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of dicts containing fund info and scores
        """
        if not self.is_fitted:
            raise ValueError("BM25 model not fitted. Call fit() first.")
        
        # Preprocess the query
        tokenized_query = self.preprocess_text(query)
        
        # Get BM25 scores
        scores = self.bm25.get_scores(tokenized_query)
        
        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        # Prepare results
        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Only include relevant results
                fund_info = self.fund_data.iloc[idx].to_dict()
                fund_info['bm25_score'] = float(scores[idx])
                results.append(fund_info)
        
        logger.info(f"Lexical search for '{query}' returned {len(results)} results")
        return results
    
    def batch_search(self, queries: List[str], top_k: int = 10) -> List[List[Dict[str, Any]]]:
        """
        Perform batch search for multiple queries.
        
        Args:
            queries: List of search queries
            top_k: Number of results to return per query
            
        Returns:
            List of result lists, one per query
        """
        return [self.search(query, top_k) for query in queries] 