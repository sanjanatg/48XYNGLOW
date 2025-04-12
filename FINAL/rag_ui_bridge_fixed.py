import pandas as pd
import json
import time
import os

from query_parser import QueryParser
from lexical_search import BM25Retriever
from semantic_search import SemanticSearch
from metadata_filter import MetadataFilter
from score_fusion import ScoreFusion
from rag_prompt import RAGPromptGenerator
from ollama_client import OllamaClient

class RAGUIBridge:
    def __init__(self, fund_data_path, model_name="mistral:latest"):
        """
        Initialize the RAG UI Bridge
        
        Args:
            fund_data_path: path to fund data CSV
            model_name: name of the model to use with Ollama
        """
        print(f"Initializing RAG system with {model_name}...")
        
        # Load fund data
        self.fund_data = self._load_fund_data(fund_data_path)
        
        # Initialize components
        self.parser = QueryParser()
        self.bm25_retriever = BM25Retriever(self.fund_data)
        self.semantic_search = SemanticSearch(self.fund_data)
        self.metadata_filter = MetadataFilter()
        self.score_fusion = ScoreFusion()
        self.prompt_generator = RAGPromptGenerator()
        self.llm_client = OllamaClient(model_name=model_name)
        
        print("RAG system initialized and ready!")
        
    def _load_fund_data(self, data_path):
        """Load fund data from CSV file"""
        print(f"Loading fund data from {data_path}...")
        
        # Check if file exists
        if not os.path.exists(data_path):
            print(f"Warning: {data_path} not found. Using dummy data.")
            # Create dummy data for testing
            return pd.DataFrame({
                'fund_name': ['HDFC Technology Fund', 'SBI Healthcare Fund', 'ICICI Low Risk Bond Fund'],
                'description': [
                    'HDFC Technology Fund invests in technology companies focusing on innovation and growth.',
                    'SBI Healthcare Fund focuses on pharmaceutical and healthcare sector for long-term growth.',
                    'ICICI Low Risk Bond Fund is a debt fund with conservative approach for stable returns.'
                ],
                'sector': ['Technology', 'Healthcare', 'Debt'],
                'category': ['Equity: Sectoral - Technology', 'Equity: Sectoral - Healthcare', 'Debt: Low Duration'],
                'risk_score': [3, 2, 1],
                'expense_ratio': [1.8, 1.2, 0.5],
                'returns_3yr': [12.5, 10.2, 5.5],
                'returns_5yr': [15.2, 12.1, 6.2]
            })
        
        # Load actual data
        try:
            df = pd.read_csv(data_path)
            print(f"Loaded {len(df)} funds.")
            return df
        except Exception as e:
            print(f"Error loading fund data: {e}")
            # Return empty DataFrame
            return pd.DataFrame()
    
    def process_query(self, query, top_k=5, explain=True):
        """
        Process a user query through the entire RAG pipeline
        
        Args:
            query: user's natural language query
            top_k: number of top funds to include in response
            explain: whether to include explanation of steps
            
        Returns:
            dict with LLM response and intermediate results
        """
        start_time = time.time()
        results = {"query": query}
        steps_info = []
        
        # Step 1: Parse and normalize query
        step_start = time.time()
        query_info = self.parser.process_query(query)
        results["parsed_query"] = query_info
        steps_info.append({
            "step": "Query Parsing",
            "time": time.time() - step_start,
            "output": f"Normalized: '{query_info['normalized_query']}' with {len(query_info['filters']['sector'])} sector filters, {len(query_info['filters']['risk'])} risk filters"
        })
        
        # Step 2: BM25 retrieval
        step_start = time.time()
        bm25_results = self.bm25_retriever.search_keywords(query_info["keywords"], top_k=100)
        steps_info.append({
            "step": "BM25 Retrieval",
            "time": time.time() - step_start,
            "output": f"Retrieved {len(bm25_results)} candidates with keyword matching"
        })
        
        # Step 3: Semantic search
        step_start = time.time()
        semantic_results = self.semantic_search.search(query_info["normalized_query"], top_k=10)
        steps_info.append({
            "step": "Semantic Search",
            "time": time.time() - step_start,
            "output": f"Retrieved {len(semantic_results)} candidates with semantic matching"
        })
        
        # Step 4: Metadata filtering
        step_start = time.time()
        filtered_results = None
        if query_info["filters"]["sector"] or query_info["filters"]["risk"] or query_info["filters"]["other_attributes"]:
            # Apply filters to BM25 results (more candidates)
            filtered_results = self.metadata_filter.apply_filters(bm25_results, query_info["filters"])
            steps_info.append({
                "step": "Metadata Filtering",
                "time": time.time() - step_start,
                "output": f"Applied filters, {len(filtered_results)} funds passed filters"
            })
        
        # Step 5: Score fusion
        step_start = time.time()
        final_results = self.score_fusion.fuse(
            bm25_results, 
            semantic_results, 
            filtered_results, 
            query_info["keywords"]
        )
        results["ranked_funds"] = [
            {k: v for k, v in fund.items() if not k.startswith("norm_")} 
            for fund in final_results[:top_k]
        ]
        steps_info.append({
            "step": "Score Fusion",
            "time": time.time() - step_start,
            "output": f"Combined scores and ranked {len(final_results)} candidates"
        })
        
        # Step 6: Generate RAG prompt
        step_start = time.time()
        prompt_data = self.prompt_generator.generate_prompt(query, final_results, top_k=top_k)
        steps_info.append({
            "step": "RAG Prompt Generation",
            "time": time.time() - step_start,
            "output": f"Generated prompt with {top_k} funds as context"
        })
        
        # Step 7: LLM response
        step_start = time.time()
        if self.llm_client.is_available:
            llm_response = self.llm_client.process_rag_prompt(prompt_data)
            steps_info.append({
                "step": "LLM Response",
                "time": time.time() - step_start,
                "output": f"Generated response with {len(llm_response.split())} words"
            })
        else:
            llm_response = "Error: LLM model not available. Please ensure Ollama is running with the mistral model."
            steps_info.append({
                "step": "LLM Response",
                "time": 0,
                "output": "Error: LLM not available"
            })
        
        results["llm_response"] = llm_response
        
        # Add timing information
        total_time = time.time() - start_time
        results["timing"] = {
            "total_time": total_time,
            "steps": steps_info
        }
        
        if explain:
            results["explanation"] = steps_info
        
        return results
    
    def generate_result_html(self, results):
        """
        Generate HTML display of results for UI
        
        Args:
            results: dict with process_query results
            
        Returns:
            HTML string for display
        """
        html = "<div class='rag-results'>"
        
        # Add LLM response
        html += f"<div class='llm-response'>{results['llm_response']}</div>"
        
        # Add top funds
        html += "<div class='top-funds'>"
        html += "<h3>Top Matching Funds</h3>"
        html += "<div class='funds-container'>"
        
        for i, fund in enumerate(results.get("ranked_funds", []), 1):
            html += f"<div class='fund-card'>"
            html += f"<h4>{i}. {fund.get('fund_name', 'Unknown Fund')}</h4>"
            html += f"<p><strong>Category:</strong> {fund.get('category', 'N/A')}</p>"
            html += f"<p><strong>Risk:</strong> {fund.get('risk_score', 'N/A')}</p>"
            html += f"<p><strong>Expense Ratio:</strong> {fund.get('expense_ratio', 'N/A')}</p>"
            
            # Add returns
            returns_keys = [key for key in fund.keys() if 'return' in key.lower()]
            if returns_keys:
                html += "<p><strong>Returns:</strong> "
                returns_items = []
                for key in returns_keys:
                    returns_items.append(f"{key}: {fund[key]}")
                html += ", ".join(returns_items)
                html += "</p>"
                
            # Add scores if available
            if 'combined_score' in fund:
                html += f"<p><strong>Match Score:</strong> {fund['combined_score']:.2f}</p>"
                
            html += "</div>"
        
        html += "</div></div>"
        
        # Add explanation if available
        if "explanation" in results:
            html += "<div class='explanation'>"
            html += "<h3>How Results Were Generated</h3>"
            
            for step in results["explanation"]:
                html += f"<div class='step'>"
                html += f"<strong>{step['step']}</strong> ({step['time']:.2f}s): {step['output']}"
                html += f"</div>"
                
            html += f"<p><strong>Total time:</strong> {results['timing']['total_time']:.2f}s</p>"
            html += "</div>"
            
        html += "</div>"
        
        return html

# Example usage
if __name__ == "__main__":
    # Initialize bridge with sample data
    bridge = RAGUIBridge("sample_funds.csv")
    
    # Process a query
    results = bridge.process_query("I want a low risk debt fund with good returns", top_k=3)
    
    # Print results
    print(json.dumps(results, indent=2)) 