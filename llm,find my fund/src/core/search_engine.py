import os
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Any, Optional, Union
from loguru import logger

from src.core.data_loader import DataLoader
from src.core.lexical_search import LexicalSearch
from src.core.semantic_search import SemanticSearch

class SearchEngine:
    """
    Main search engine that combines lexical and semantic search for optimal fund matching.
    """
    
    def __init__(self, 
                data_path: str = "data/funds.csv",
                semantic_model: str = "all-MiniLM-L6-v2",
                lexical_weight: float = 0.4,
                semantic_weight: float = 0.6):
        """
        Initialize the search engine.
        
        Args:
            data_path: Path to the fund data
            semantic_model: Name of the sentence transformer model to use
            lexical_weight: Weight for lexical search scores in hybrid search
            semantic_weight: Weight for semantic search scores in hybrid search
        """
        self.data_loader = DataLoader(data_path)
        self.lexical_search = LexicalSearch()
        self.semantic_search = SemanticSearch(model_name=semantic_model)
        
        self.lexical_weight = lexical_weight
        self.semantic_weight = semantic_weight
        
        self.is_fitted = False
        self.metadata_fields = ["fund_house", "category", "sub_category", 
                             "asset_class", "fund_type", "sector"]
        
    def fit(self, force_reload: bool = False):
        """
        Fit the search engine on the fund data.
        
        Args:
            force_reload: Whether to force reload data and refit models
        """
        # Load and preprocess data
        if force_reload or self.data_loader.data is None:
            logger.info("Loading and preprocessing fund data...")
            fund_data = self.data_loader.preprocess_data()
        else:
            fund_data = self.data_loader.get_data()
        
        # Fit lexical search
        logger.info("Fitting lexical search (BM25)...")
        self.lexical_search.fit(fund_data, text_column="fund_name")
        
        # Fit semantic search
        logger.info("Fitting semantic search (HNSW)...")
        self.semantic_search.fit(fund_data, text_column="combined_text")
        
        self.is_fitted = True
        logger.info("Search engine fitted successfully")
        
    def search(self, query: str, top_k: int = 10, 
              search_type: str = "hybrid") -> List[Dict[str, Any]]:
        """
        Search for funds matching the query.
        
        Args:
            query: Search query
            top_k: Number of results to return
            search_type: Type of search to perform (lexical, semantic, or hybrid)
            
        Returns:
            List of fund matches with scores
        """
        if not self.is_fitted:
            raise ValueError("Search engine not fitted. Call fit() first.")
        
        if search_type == "lexical":
            return self.lexical_search.search(query, top_k=top_k)
        
        elif search_type == "semantic":
            return self.semantic_search.search(query, top_k=top_k)
        
        elif search_type == "hybrid":
            # Get results from both search methods
            # Get more results than needed for reranking
            lexical_results = self.lexical_search.search(query, top_k=top_k*2)
            semantic_results = self.semantic_search.search(query, top_k=top_k*2)
            
            # Combine and rerank results
            return self._hybrid_rerank(query, lexical_results, semantic_results, top_k)
        
        else:
            raise ValueError(f"Invalid search type: {search_type}. Must be one of [lexical, semantic, hybrid]")
    
    def _hybrid_rerank(self, query: str, lexical_results: List[Dict[str, Any]], 
                      semantic_results: List[Dict[str, Any]], 
                      top_k: int) -> List[Dict[str, Any]]:
        """
        Combine and rerank lexical and semantic search results.
        
        Args:
            query: Original search query
            lexical_results: Results from lexical search
            semantic_results: Results from semantic search
            top_k: Number of results to return
            
        Returns:
            Reranked list of results
        """
        # Create a dictionary to combine scores by fund ID
        combined_results = {}
        
        # Process lexical results
        for result in lexical_results:
            fund_id = result["id"] if "id" in result else result["fund_name"]
            
            if fund_id not in combined_results:
                combined_results[fund_id] = {
                    "fund_info": {k: v for k, v in result.items() if k not in ['bm25_score', 'semantic_score']},
                    "bm25_score": result.get("bm25_score", 0),
                    "semantic_score": 0
                }
            else:
                combined_results[fund_id]["bm25_score"] = result.get("bm25_score", 0)
        
        # Process semantic results
        for result in semantic_results:
            fund_id = result["id"] if "id" in result else result["fund_name"]
            
            if fund_id not in combined_results:
                combined_results[fund_id] = {
                    "fund_info": {k: v for k, v in result.items() if k not in ['bm25_score', 'semantic_score']},
                    "bm25_score": 0,
                    "semantic_score": result.get("semantic_score", 0)
                }
            else:
                combined_results[fund_id]["semantic_score"] = result.get("semantic_score", 0)
        
        # Apply metadata boost if query contains metadata keywords
        combined_results = self._apply_metadata_boost(query, combined_results)
        
        # Calculate combined score
        for fund_id, result in combined_results.items():
            # Normalize the scores (simple min-max scaling)
            bm25_score = result["bm25_score"]
            semantic_score = result["semantic_score"]
            
            # Calculate weighted combined score
            combined_score = (self.lexical_weight * bm25_score) + (self.semantic_weight * semantic_score)
            result["combined_score"] = combined_score
        
        # Sort by combined score and get top-k results
        sorted_results = sorted(combined_results.values(), 
                               key=lambda x: x["combined_score"], 
                               reverse=True)[:top_k]
        
        # Format results for return
        formatted_results = []
        for result in sorted_results:
            fund_info = result["fund_info"]
            fund_info["bm25_score"] = result["bm25_score"]
            fund_info["semantic_score"] = result["semantic_score"]
            fund_info["combined_score"] = result["combined_score"]
            formatted_results.append(fund_info)
        
        logger.info(f"Hybrid search for '{query}' returned {len(formatted_results)} results")
        return formatted_results
    
    def _apply_metadata_boost(self, query: str, 
                             results: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Apply boost to search results based on metadata matches.
        
        Args:
            query: Original search query
            results: Combined search results
            
        Returns:
            Boosted search results
        """
        query_lower = query.lower()
        
        # Check for metadata keywords in query
        metadata_boosts = {}
        for field in self.metadata_fields:
            if field.lower() in query_lower:
                # Extract potential metadata value
                field_index = query_lower.find(field.lower())
                remaining_text = query_lower[field_index + len(field):].strip()
                
                if remaining_text:
                    potential_value = remaining_text.split()[0].strip(",:;")
                    if potential_value:
                        metadata_boosts[field] = potential_value
            
            # Check for common fund houses if not already extracted
            if field == "fund_house" and field not in metadata_boosts:
                common_fund_houses = ["icici", "hdfc", "sbi", "axis", "kotak", "aditya", "birla", 
                                     "nippon", "tata", "uti", "reliance", "idfc", "dsp", "mirae"]
                for fund_house in common_fund_houses:
                    if fund_house in query_lower:
                        metadata_boosts["fund_house"] = fund_house
                        break
        
        # Apply boost to results
        if metadata_boosts:
            for fund_id, result in results.items():
                boost_factor = 1.0
                
                for field, value in metadata_boosts.items():
                    if field in result["fund_info"] and value.lower() in str(result["fund_info"][field]).lower():
                        # Apply boost
                        boost_factor += 0.2  # 20% boost per matched metadata field
                
                # Apply the boost
                result["bm25_score"] *= boost_factor
                result["semantic_score"] *= boost_factor
        
        return results
    
    def save_models(self, directory: str = "models") -> None:
        """
        Save the search models for later use.
        
        Args:
            directory: Directory to save models
        """
        if not self.is_fitted:
            raise ValueError("Cannot save models; search engine not fitted.")
            
        os.makedirs(directory, exist_ok=True)
        
        # Save the semantic search index
        self.semantic_search.save_index(
            index_path=os.path.join(directory, "hnsw_index.bin"),
            metadata_path=os.path.join(directory, "index_metadata.json")
        )
        
        # Save the data loader's processed data
        self.data_loader.save_processed_data(
            output_path=os.path.join(directory, "processed_funds.csv")
        )
        
        logger.info(f"Search engine models saved to {directory}")
    
    def load_models(self, directory: str = "models", 
                   data_path: str = "models/processed_funds.csv") -> None:
        """
        Load saved search models.
        
        Args:
            directory: Directory containing saved models
            data_path: Path to the processed fund data
        """
        # Load processed data
        self.data_loader = DataLoader(data_path)
        fund_data = self.data_loader.load_data()
        
        # Fit lexical search on the loaded data
        self.lexical_search.fit(fund_data, text_column="fund_name")
        
        # Load semantic search index
        self.semantic_search.load_index(
            index_path=os.path.join(directory, "hnsw_index.bin"),
            metadata_path=os.path.join(directory, "index_metadata.json")
        )
        
        # Set fund data for semantic search
        self.semantic_search.fund_data = fund_data
        
        self.is_fitted = True
        logger.info("Search engine models loaded successfully") 