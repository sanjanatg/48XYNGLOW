import numpy as np
import pandas as pd

class ScoreFusion:
    def __init__(self, alpha=0.4, beta=0.4, gamma=0.2):
        """
        Initialize score fusion with weighting parameters
        
        Args:
            alpha: weight for semantic score (default 0.4)
            beta: weight for metadata match (default 0.4)
            gamma: weight for fuzzy string match (default 0.2)
        """
        self.alpha = alpha  # Semantic score weight
        self.beta = beta    # Metadata match weight
        self.gamma = gamma  # Fuzzy string match weight
        
    def normalize_scores(self, funds, score_field):
        """
        Normalize scores in the given field to [0,1] range
        
        Args:
            funds: list of fund dictionaries
            score_field: name of the score field to normalize
            
        Returns:
            funds with normalized scores
        """
        if not funds:
            return funds
            
        # Extract scores
        scores = [fund.get(score_field, 0) for fund in funds]
        
        # Check if all scores are the same
        if max(scores) == min(scores):
            for fund in funds:
                fund[f"norm_{score_field}"] = 1.0 if fund.get(score_field, 0) > 0 else 0.0
            return funds
            
        # Normalize to [0,1]
        min_score = min(scores)
        score_range = max(scores) - min_score
        
        for fund in funds:
            original_score = fund.get(score_field, 0)
            normalized_score = (original_score - min_score) / score_range if score_range > 0 else 0
            fund[f"norm_{score_field}"] = normalized_score
            
        return funds
    
    def combine_scores(self, funds):
        """
        Combine normalized scores using the weighting parameters
        
        Args:
            funds: list of fund dictionaries with normalized scores
            
        Returns:
            funds with added combined_score field, sorted by combined_score
        """
        for fund in funds:
            # Get normalized scores, default to 0 if not present
            semantic_score = fund.get("norm_semantic_score", 0)
            bm25_score = fund.get("norm_bm25_score", 0)
            fuzzy_name_score = fund.get("norm_fuzzy_name_score", 0)
            
            # Calculate weighted sum
            combined_score = (
                self.alpha * semantic_score +
                self.beta * bm25_score +
                self.gamma * fuzzy_name_score
            )
            
            fund["combined_score"] = combined_score
        
        # Sort by combined score (descending)
        sorted_funds = sorted(funds, key=lambda x: x.get("combined_score", 0), reverse=True)
        
        return sorted_funds
    
    def fuse(self, bm25_results, semantic_results, filtered_funds=None, keywords=None):
        """
        Fuse results from BM25, semantic search, and metadata filtering
        
        Args:
            bm25_results: list of fund dictionaries with bm25_score
            semantic_results: list of fund dictionaries with semantic_score
            filtered_funds: list of fund dictionaries that passed metadata filtering
            keywords: list of keywords for fuzzy name matching
            
        Returns:
            sorted list of funds with combined scores
        """
        # Start with semantic results as primary list
        all_funds = semantic_results.copy()
        
        # Create a lookup by fund name
        fund_lookup = {fund.get('fund_name', ''): fund for fund in all_funds}
        
        # Add BM25 scores to existing funds or add new funds
        for bm25_fund in bm25_results:
            fund_name = bm25_fund.get('fund_name', '')
            if fund_name in fund_lookup:
                fund_lookup[fund_name]['bm25_score'] = bm25_fund.get('bm25_score', 0)
            else:
                bm25_fund['semantic_score'] = 0  # Default semantic score
                all_funds.append(bm25_fund)
                fund_lookup[fund_name] = bm25_fund
        
        # Apply metadata filtering if provided
        if filtered_funds:
            # Create set of filtered fund names
            filtered_fund_names = {fund.get('fund_name', '') for fund in filtered_funds}
            
            # Mark funds that passed metadata filtering
            for fund in all_funds:
                fund_name = fund.get('fund_name', '')
                fund['metadata_match'] = 1.0 if fund_name in filtered_fund_names else 0.0
        else:
            # If no filtering was done, all funds pass
            for fund in all_funds:
                fund['metadata_match'] = 1.0
        
        # Calculate fuzzy name match scores if keywords provided
        if keywords:
            from metadata_filter import MetadataFilter
            metadata_filter = MetadataFilter()
            all_funds = metadata_filter.fuzzy_match_name(all_funds, keywords)
        else:
            for fund in all_funds:
                fund['fuzzy_name_score'] = 0.0
                
        # Normalize all scores
        all_funds = self.normalize_scores(all_funds, 'semantic_score')
        all_funds = self.normalize_scores(all_funds, 'bm25_score')
        all_funds = self.normalize_scores(all_funds, 'fuzzy_name_score')
        all_funds = self.normalize_scores(all_funds, 'metadata_match')
        
        # Combine scores and sort
        return self.combine_scores(all_funds)

# Example usage
if __name__ == "__main__":
    # Sample BM25 results
    bm25_results = [
        {'fund_name': 'HDFC Technology Fund', 'bm25_score': 0.85},
        {'fund_name': 'SBI Healthcare Fund', 'bm25_score': 0.65},
        {'fund_name': 'ICICI Low Risk Bond Fund', 'bm25_score': 0.45}
    ]
    
    # Sample semantic results
    semantic_results = [
        {'fund_name': 'HDFC Technology Fund', 'semantic_score': 0.78},
        {'fund_name': 'Axis Technology ETF', 'semantic_score': 0.72},
        {'fund_name': 'SBI Healthcare Fund', 'semantic_score': 0.55}
    ]
    
    # Sample filtered funds
    filtered_funds = [
        {'fund_name': 'HDFC Technology Fund'},
        {'fund_name': 'Axis Technology ETF'}
    ]
    
    # Keywords for fuzzy matching
    keywords = ['technology', 'fund']
    
    # Create fusion
    fusion = ScoreFusion(alpha=0.4, beta=0.4, gamma=0.2)
    
    # Fuse results
    final_results = fusion.fuse(bm25_results, semantic_results, filtered_funds, keywords)
    
    print("Final ranked results:")
    for i, result in enumerate(final_results[:5], 1):
        print(f"{i}. {result['fund_name']} - Score: {result['combined_score']:.4f}") 