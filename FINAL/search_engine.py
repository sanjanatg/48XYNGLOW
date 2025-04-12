import os
import json
import numpy as np
import faiss
import pandas as pd
from sentence_transformers import SentenceTransformer
import logging
from query_parser import QueryParser  # Import the query parser
from enhanced_retrieval import EnhancedRetrieval  # Import the enhanced retrieval component
import utils  # Import the utils module

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MutualFundSearchEngine:
    """
    A search engine for mutual funds using embedding-based semantic search.
    """
    
    def __init__(self, 
                 model_name="all-MiniLM-L6-v2",
                 embeddings_path=None,
                 index_path=None,
                 id_mapping_path=None,
                 funds_data_path=None,
                 corpus_path=None):
        """
        Initialize the search engine by loading the FAISS index, fund data, and embedding model.
        
        Args:
            model_name (str): The name of the SentenceTransformer model to use
            embeddings_path (str): Path to the stored fund embeddings
            index_path (str): Path to the FAISS index file
            id_mapping_path (str): Path to the fund ID to index mapping
            funds_data_path (str): Path to the preprocessed fund data
            corpus_path (str): Path to the fund description corpus
        """
        logger.info("Initializing Mutual Fund Search Engine")
        
        # Get paths from utils if not provided
        output_paths = utils.get_output_paths()
        if embeddings_path is None:
            embeddings_path = output_paths["fund_embeddings"]
        if index_path is None:
            index_path = output_paths["faiss_index"]
        if id_mapping_path is None:
            id_mapping_path = output_paths["fund_id_to_index"]
        if funds_data_path is None:
            funds_data_path = output_paths["preprocessed_funds"]
        if corpus_path is None:
            corpus_path = output_paths["fund_corpus"]
            
        logger.info(f"Using paths: embeddings={embeddings_path}, index={index_path}, id_mapping={id_mapping_path}")
        
        # Initialize the query parser
        self.query_parser = QueryParser()
        logger.info("Initialized query parser")
        
        # Initialize the enhanced retrieval component
        self.enhanced_retrieval = EnhancedRetrieval()
        logger.info("Initialized enhanced retrieval component")
        
        # Load the embedding model
        try:
            logger.info(f"Loading embedding model: {model_name}")
            self.model = SentenceTransformer(model_name)
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            raise
        
        # Load the FAISS index
        try:
            logger.info(f"Loading FAISS index from {index_path}")
            self.index = faiss.read_index(index_path)
        except Exception as e:
            logger.error(f"Failed to load FAISS index: {str(e)}")
            raise
        
        # Load the fund embeddings
        try:
            logger.info(f"Loading fund embeddings from {embeddings_path}")
            self.embeddings = np.load(embeddings_path)
        except Exception as e:
            logger.error(f"Failed to load fund embeddings: {str(e)}")
            raise
            
        # Load the fund ID to index mapping
        try:
            logger.info(f"Loading fund ID to index mapping from {id_mapping_path}")
            with open(id_mapping_path, 'r') as f:
                self.fund_id_to_index = json.load(f)
                # Create reverse mapping (index to fund ID)
                self.index_to_fund_id = {v: k for k, v in self.fund_id_to_index.items()}
        except Exception as e:
            logger.error(f"Failed to load fund ID mapping: {str(e)}")
            raise
            
        # Load the fund data
        try:
            logger.info(f"Loading fund data from {funds_data_path}")
            with open(funds_data_path, 'r') as f:
                self.funds_data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load fund data: {str(e)}")
            raise
        
        # Load the fund description corpus
        try:
            if os.path.exists(corpus_path):
                logger.info(f"Loading fund description corpus from {corpus_path}")
                with open(corpus_path, 'r', encoding='utf-8') as f:
                    self.corpus = f.read().splitlines()
                logger.info(f"Loaded {len(self.corpus)} fund descriptions")
            else:
                logger.warning(f"Fund description corpus not found at {corpus_path}")
                self.corpus = []
        except Exception as e:
            logger.error(f"Failed to load fund description corpus: {str(e)}")
            self.corpus = []
            
        logger.info("Search engine initialization complete")
        
    def generate_fund_description(self, fund_data):
        """
        Generate a descriptive text about a fund based on its data.
        This helps in explaining why the fund was matched to the query.
        
        Args:
            fund_data (dict): Fund data dictionary
            
        Returns:
            str: A human-readable description of the fund
        """
        description = f"{fund_data.get('fund_name', 'This fund')} is a {fund_data.get('category', '').lower()} "
        description += f"fund from {fund_data.get('fund_house', '')}. "
        
        # Add risk level if available
        if fund_data.get('risk_level'):
            description += f"It has a {fund_data.get('risk_level', '').lower()} risk profile. "
            
        # Add return information if available
        if fund_data.get('return_3yr'):
            description += f"The 3-year return is {fund_data.get('return_3yr', 0):.2f}%. "
        if fund_data.get('return_5yr'):
            description += f"The 5-year return is {fund_data.get('return_5yr', 0):.2f}%. "
            
        # Add expense ratio if available
        if fund_data.get('expense_ratio'):
            description += f"The expense ratio is {fund_data.get('expense_ratio', 0):.2f}%. "
            
        # Add information about top holdings if available
        if fund_data.get('top_holdings') and len(fund_data.get('top_holdings')) > 0:
            top_holdings = fund_data.get('top_holdings')[:3]  # Get top 3 holdings
            description += f"Top holdings include {', '.join(top_holdings)}. "
            
        # Add information about sector allocation if available
        if fund_data.get('sector_allocation') and len(fund_data.get('sector_allocation')) > 0:
            top_sectors = fund_data.get('sector_allocation')[:2]  # Get top 2 sectors
            sector_info = [f"{s[0]} ({s[1]:.1f}%)" for s in top_sectors]
            description += f"Major sector allocations: {', '.join(sector_info)}. "
            
        return description
        
    def search(self, query, top_k=5, apply_filters=True, use_enhanced_scoring=True):
        """
        Search for mutual funds based on a natural language query.
        
        Args:
            query (str): Natural language query
            top_k (int): Number of top results to return
            apply_filters (bool): Whether to apply structured filters extracted from the query
            use_enhanced_scoring (bool): Whether to use the enhanced scoring algorithm
            
        Returns:
            list: List of dictionaries containing the search results with fund data
        """
        logger.info(f"Searching for query: {query}")
        
        try:
            # Extract structured filters from the query using QueryParser
            extracted_filters = {}
            if apply_filters:
                extracted_filters = self.query_parser.parse_query(query)
                logger.info(f"Extracted filters from query: {extracted_filters}")
                
                # Get human-readable explanation of filters
                filter_explanation = self.query_parser.explain_filters(extracted_filters)
                logger.info(f"Filter explanation: {filter_explanation}")
            
            # Generate embedding for the query
            query_embedding = self.model.encode([query])[0]
            
            # Normalize the embedding (if the index was created with normalized vectors)
            faiss.normalize_L2(np.array([query_embedding], dtype=np.float32))
            
            # Search the index
            # In Phase 4, we get more initial candidates (top_k * 3) to allow for reranking
            D, I = self.index.search(np.array([query_embedding], dtype=np.float32), top_k * 3)
            
            # Process results
            results = []
            for i, (distance, idx) in enumerate(zip(D[0], I[0])):
                # Convert distance to similarity score (1 - distance for normalized vectors)
                similarity = 1 - distance
                
                # Get fund ID
                fund_id = self.index_to_fund_id.get(str(idx))
                
                if fund_id and fund_id in self.funds_data:
                    fund_data = self.funds_data[fund_id]
                    
                    # Generate a descriptive text about the fund
                    description = self.generate_fund_description(fund_data)
                    
                    results.append({
                        'fund_id': fund_id,
                        'similarity': float(similarity),
                        'rank': i + 1,
                        'fund_data': fund_data,
                        'description': description,
                        'fund_name': fund_data.get('fund_name', 'Unknown'),
                        'category': fund_data.get('category', 'Unknown'),
                        'amc': fund_data.get('amc', 'Unknown'),
                        'risk_level': fund_data.get('risk_level', 'Unknown'),
                        'score': float(similarity)
                    })
            
            # Apply filters if any were extracted
            if extracted_filters and apply_filters:
                results = self.filter_results(results, extracted_filters)
            
            # Apply enhanced scoring if enabled
            if use_enhanced_scoring:
                results = self.enhanced_retrieval.compute_final_scores(results, query, extracted_filters)
                
                # Optionally add BM25 results if available
                if self.corpus:
                    results = self.enhanced_retrieval.add_bm25_results(
                        results, query, self.corpus, self.index_to_fund_id, top_k=2
                    )
                
            # Limit to top_k results
            results = results[:top_k]
            
            # Add filter explanation to the results
            if apply_filters and extracted_filters:
                for result in results:
                    result['filter_explanation'] = filter_explanation
                    result['extracted_filters'] = extracted_filters
            
            logger.info(f"Found {len(results)} results for query")
            return results
            
        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            raise
            
    def filter_results(self, results, filters):
        """
        Apply filters to search results.
        
        Args:
            results (list): Search results from the search method
            filters (dict): Dictionary of filters to apply
                Example: {'category': 'Equity', 'risk_level': 'High', 'min_return_3yr': 10}
                
        Returns:
            list: Filtered search results
        """
        if not filters:
            return results
        
        filtered_results = []
        
        for result in results:
            fund_data = result.get('fund_data', {})
            include = True
            
            # Apply each filter
            for filter_key, filter_value in filters.items():
                # Handle different types of filters
                if filter_key == 'amc' and 'amc' in fund_data:
                    if fund_data['amc'].lower() != filter_value.lower():
                        include = False
                        break
                    
                elif filter_key == 'category' and 'category' in fund_data:
                    if fund_data['category'].lower() != filter_value.lower():
                        include = False
                        break
                    
                elif filter_key == 'risk_level' and 'risk_level' in fund_data:
                    if fund_data['risk_level'].lower() != filter_value.lower():
                        include = False
                        break
                    
                elif filter_key == 'sector' and 'sectors' in fund_data:
                    # Check if the filter sector is in the fund's sectors
                    fund_sectors = [s.lower() for s in fund_data.get('sectors', [])]
                    if filter_value.lower() not in fund_sectors:
                        include = False
                        break
                    
                # Handle numeric filters like min_return_*
                elif filter_key.startswith('min_return_') and filter_key[11:] in ['1yr', '3yr', '5yr']:
                    period = filter_key[11:]  # Extract the period (1yr, 3yr, 5yr)
                    fund_return_key = f'return_{period}'
                    
                    if fund_return_key not in fund_data or fund_data[fund_return_key] < filter_value:
                        include = False
                        break
                    
                # Handle expense ratio filter
                elif filter_key == 'max_expense_ratio' and 'expense_ratio' in fund_data:
                    if fund_data['expense_ratio'] > filter_value:
                        include = False
                        break
                
                # Handle AUM filter
                elif filter_key == 'min_aum' and 'aum' in fund_data:
                    # Extract numeric value from AUM string (e.g., "27,434.33 Cr" -> 27434.33)
                    fund_aum = fund_data['aum']
                    if isinstance(fund_aum, str):
                        # Extract numeric portion from string like "₹27,434.33 Cr"
                        aum_value = fund_aum.replace('₹', '').replace(',', '').split()[0]
                        try:
                            aum_value = float(aum_value)
                        except ValueError:
                            # If we can't parse the AUM value, skip this filter
                            logger.warning(f"Couldn't parse AUM value from {fund_aum}")
                            continue
                    else:
                        aum_value = float(fund_aum)
                    
                    if aum_value < filter_value:
                        include = False
                        break
            
            if include:
                filtered_results.append(result)
        
        logger.info(f"Filtered results from {len(results)} to {len(filtered_results)} based on {len(filters)} filters")
        return filtered_results

    def get_fund_details(self, fund_id):
        """
        Get detailed information about a specific fund.
        
        Args:
            fund_id (str): Fund ID
            
        Returns:
            dict: Fund data with detailed description
        """
        if fund_id in self.funds_data:
            fund_data = self.funds_data[fund_id]
            description = self.generate_fund_description(fund_data)
            return {
                'fund_id': fund_id,
                'fund_data': fund_data,
                'description': description
            }
        return None 