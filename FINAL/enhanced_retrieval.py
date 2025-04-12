import os
import json
import numpy as np
import pandas as pd
import logging
from rapidfuzz import fuzz
from rank_bm25 import BM25Okapi
import utils

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedRetrieval:
    """
    Enhanced retrieval system that combines semantic search with metadata filtering
    and fuzzy matching for improved mutual fund search results.
    """
    
    def __init__(self):
        """Initialize the enhanced retrieval component"""
        logger.info("Initializing Enhanced Retrieval")
        
        # Score weights (can be adjusted)
        self.weights = {
            'semantic': 0.6,
            'metadata': 0.3,
            'fuzzy': 0.1
        }
        
        # Fields to use for fuzzy matching
        self.fuzzy_fields = ['fund_name', 'amc', 'category']
        
        # Metadata importance weights (for scoring)
        self.metadata_weights = {
            'amc': 2.0,           # Higher weight for exact AMC match
            'category': 1.5,      # Medium-high weight for category match
            'risk_level': 1.2,    # Medium weight for risk level match
            'sector': 1.2,        # Medium weight for sector match
            'returns': 1.0,       # Base weight for returns criteria
            'expense_ratio': 0.8  # Lower weight for expense ratio match
        }
        
        logger.info("Enhanced Retrieval initialized with weights: %s", self.weights)
    
    def compute_metadata_match_score(self, fund_data, filters):
        """
        Compute a metadata match score between a fund and the query filters.
        
        Args:
            fund_data (dict): Fund data dictionary
            filters (dict): Extracted filters from query
            
        Returns:
            float: Metadata match score (0.0 to 1.0)
        """
        if not filters:
            return 0.0
            
        total_score = 0.0
        total_weight = 0.0
        
        # Check AMC match
        if 'amc' in filters and 'amc' in fund_data:
            weight = self.metadata_weights.get('amc', 1.0)
            total_weight += weight
            if fund_data['amc'].lower() == filters['amc'].lower():
                total_score += weight
        
        # Check category match
        if 'category' in filters and 'category' in fund_data:
            weight = self.metadata_weights.get('category', 1.0)
            total_weight += weight
            if fund_data['category'].lower() == filters['category'].lower():
                total_score += weight
        
        # Check risk level match
        if 'risk_level' in filters and 'risk_level' in fund_data:
            weight = self.metadata_weights.get('risk_level', 1.0)
            total_weight += weight
            if fund_data['risk_level'].lower() == filters['risk_level'].lower():
                total_score += weight
        
        # Check sector match
        if 'sector' in filters and 'sectors' in fund_data:
            weight = self.metadata_weights.get('sector', 1.0)
            total_weight += weight
            if any(sector.lower() == filters['sector'].lower() for sector in fund_data.get('sectors', [])):
                total_score += weight
        
        # Check returns match (partial credit for being close)
        for period in ['1yr', '3yr', '5yr']:
            key = f'min_return_{period}'
            data_key = f'return_{period}'
            if key in filters and data_key in fund_data:
                weight = self.metadata_weights.get('returns', 1.0)
                total_weight += weight
                
                # Get target and actual values
                target_value = filters[key]
                actual_value = fund_data[data_key]
                
                # Calculate how close the fund is to meeting the criteria
                if actual_value >= target_value:
                    # Fully meets criteria
                    total_score += weight
                elif actual_value >= target_value * 0.8:
                    # Partially meets criteria (at least 80% of target)
                    ratio = actual_value / target_value
                    total_score += weight * ratio
        
        # Check expense ratio match (partial credit for being close)
        if 'max_expense_ratio' in filters and 'expense_ratio' in fund_data:
            weight = self.metadata_weights.get('expense_ratio', 1.0)
            total_weight += weight
            
            target_value = filters['max_expense_ratio']
            actual_value = fund_data['expense_ratio']
            
            if actual_value <= target_value:
                # Fully meets criteria
                total_score += weight
            elif actual_value <= target_value * 1.2:
                # Partially meets criteria (within 20% above target)
                ratio = target_value / actual_value
                total_score += weight * ratio
        
        # Compute final score (normalized)
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def compute_fuzzy_match_score(self, fund_data, query):
        """
        Compute a fuzzy match score between fund data and query using rapidfuzz.
        
        Args:
            fund_data (dict): Fund data dictionary
            query (str): Original query string
            
        Returns:
            float: Fuzzy match score (0.0 to 1.0)
        """
        # Clean query
        clean_query = utils.clean_text(query)
        
        # Initialize scores for each field
        field_scores = {}
        
        for field in self.fuzzy_fields:
            if field in fund_data and isinstance(fund_data[field], str):
                field_value = utils.clean_text(fund_data[field])
                
                # Calculate token set ratio (handles word order and partial matches well)
                ratio = fuzz.token_set_ratio(clean_query, field_value) / 100.0
                
                # Store score
                field_scores[field] = ratio
        
        # Return average of all field scores, or 0 if no fields matched
        if field_scores:
            return sum(field_scores.values()) / len(field_scores)
        else:
            return 0.0
    
    def compute_final_scores(self, results, query, filters):
        """
        Compute final scores using weighted combination of semantic similarity,
        metadata match, and fuzzy text match.
        
        Args:
            results (list): Search results
            query (str): Original query string
            filters (dict): Extracted filters from query
            
        Returns:
            list: Results with new score and explanation
        """
        logger.info("Computing enhanced scores for %d results", len(results))
        
        for result in results:
            # Extract fund data
            fund_data = result['fund_data']
            
            # Get semantic similarity score (already computed)
            semantic_score = result['similarity']
            
            # Compute metadata match score
            metadata_score = self.compute_metadata_match_score(fund_data, filters)
            
            # Compute fuzzy match score
            fuzzy_score = self.compute_fuzzy_match_score(fund_data, query)
            
            # Compute final weighted score
            final_score = (
                self.weights['semantic'] * semantic_score +
                self.weights['metadata'] * metadata_score +
                self.weights['fuzzy'] * fuzzy_score
            )
            
            # Store all scores in the result
            result['final_score'] = final_score
            result['semantic_score'] = semantic_score
            result['metadata_score'] = metadata_score
            result['fuzzy_score'] = fuzzy_score
            result['score'] = final_score  # Update the main score field
            
            # Add score breakdown explanation
            result['score_explanation'] = {
                'semantic_similarity': f"{semantic_score:.4f} × {self.weights['semantic']:.1f}",
                'metadata_match': f"{metadata_score:.4f} × {self.weights['metadata']:.1f}",
                'fuzzy_match': f"{fuzzy_score:.4f} × {self.weights['fuzzy']:.1f}",
                'final_score': f"{final_score:.4f}"
            }
        
        # Sort results by final score
        results.sort(key=lambda x: x['final_score'], reverse=True)
        
        logger.info("Enhanced scoring complete")
        return results
        
    def add_bm25_results(self, results, query, corpus, fund_mapping, top_k=3):
        """
        Add BM25 keyword search results if they're not already in the top results.
        
        Args:
            results (list): Current search results
            query (str): Original query string
            corpus (list): List of fund descriptions
            fund_mapping (dict): Mapping of corpus indices to fund IDs
            top_k (int): Number of BM25 results to consider
            
        Returns:
            list: Enhanced results with BM25 additions
        """
        # Get current fund IDs
        current_fund_ids = set(r['fund_id'] for r in results)
        
        # Tokenize corpus and query
        tokenized_corpus = [utils.clean_text(doc).split() for doc in corpus]
        tokenized_query = utils.clean_text(query).split()
        
        # Create BM25 index
        bm25 = BM25Okapi(tokenized_corpus)
        
        # Get BM25 scores
        bm25_scores = bm25.get_scores(tokenized_query)
        
        # Get top BM25 results
        top_bm25_indices = np.argsort(bm25_scores)[-top_k*2:][::-1]  # Get more than we need
        
        # Add new results from BM25 (only ones not already in results)
        new_results = []
        for idx in top_bm25_indices:
            # Get fund ID
            fund_id = fund_mapping.get(str(idx))
            
            # Skip if this fund is already in results
            if fund_id in current_fund_ids:
                continue
                
            # Skip if BM25 score is too low
            bm25_score = bm25_scores[idx]
            if bm25_score < 1.0:  # Minimum relevance threshold
                continue
                
            # TODO: Create result object for this fund
            # For now, we'll just log it
            logger.info(f"Would add BM25 result: {fund_id} with score {bm25_score}")
            
            # Stop after adding top_k new results
            if len(new_results) >= top_k:
                break
                
        # Return combined results (original + new)
        return results + new_results 

    def generate_rag_prompt(self, user_query, top_results):
        """
        Generate a RAG prompt for LLM based on user query and top fund results.
        This follows the template for Phase 6: PROMPT ENGINEERING.
        
        Args:
            user_query (str): The user's query about mutual funds
            top_results (list): List of top fund results from search engine
            
        Returns:
            str: Formatted prompt for the LLM
        """
        logger.info("Generating RAG prompt from top %d results", len(top_results))
        
        # Ensure we have results to work with
        if not top_results:
            logger.warning("No results provided to generate RAG prompt")
            return f"""
You are a mutual fund advisor. A user asked: "{user_query}".

Here are top matching funds:
No fund data available.
No additional fund data available.
No additional fund data available.

Which one is the best match? Explain why in 3 sentences.
"""
        
        # Extract top 3 funds (or fewer if less than 3 results)
        top_3_funds = top_results[:min(3, len(top_results))]
        
        # Format each fund context
        fund_contexts = []
        for i, result in enumerate(top_3_funds, 1):
            try:
                # Safely get fund_data, handling potential missing keys
                fund_data = result.get('fund_data', {}) if isinstance(result, dict) else {}
                if not fund_data:
                    logger.warning(f"Missing fund_data in result {i}")
                    fund_contexts.append(f"FUND {i}: No data available.")
                    continue
                
                # Create a formatted string with key fund information
                fund_context = f"FUND {i}: {fund_data.get('fund_name', 'Unknown Fund')}\n"
                fund_context += f"- AMC: {fund_data.get('amc', 'N/A')}\n"
                fund_context += f"- Category: {fund_data.get('category', 'N/A')}\n"
                fund_context += f"- Risk Level: {fund_data.get('risk_level', 'N/A')}\n"
                
                # Add returns information if available
                returns_info = []
                for period in ['1yr', '3yr', '5yr']:
                    key = f'return_{period}'
                    if key in fund_data and fund_data[key] is not None:
                        try:
                            returns_info.append(f"{period}: {float(fund_data[key]):.2f}%")
                        except (ValueError, TypeError):
                            logger.warning(f"Invalid return value for {key}: {fund_data[key]}")
                            returns_info.append(f"{period}: N/A")
                
                if returns_info:
                    fund_context += f"- Returns: {', '.join(returns_info)}\n"
                
                # Add expense ratio if available
                if 'expense_ratio' in fund_data and fund_data['expense_ratio'] is not None:
                    try:
                        fund_context += f"- Expense Ratio: {float(fund_data['expense_ratio']):.2f}%\n"
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid expense ratio: {fund_data['expense_ratio']}")
                        fund_context += f"- Expense Ratio: N/A\n"
                    
                # Add investment objective if available
                if 'investment_objective' in fund_data and fund_data['investment_objective']:
                    fund_context += f"- Investment Objective: {fund_data['investment_objective']}\n"
                    
                fund_contexts.append(fund_context)
            except Exception as e:
                logger.error(f"Error formatting fund {i}: {str(e)}")
                fund_contexts.append(f"FUND {i}: Error retrieving fund data.")
        
        # Create the prompt using the template from Phase 6
        context_fund_1 = fund_contexts[0] if len(fund_contexts) > 0 else "No fund data available."
        context_fund_2 = fund_contexts[1] if len(fund_contexts) > 1 else "No additional fund data available."
        context_fund_3 = fund_contexts[2] if len(fund_contexts) > 2 else "No additional fund data available."
        
        prompt = f"""
You are a mutual fund advisor. A user asked: "{user_query}".

Here are top matching funds:
{context_fund_1}
{context_fund_2}
{context_fund_3}

Which one is the best match? Explain why in 3 sentences.
"""
        
        logger.info("RAG prompt generated successfully")
        return prompt 