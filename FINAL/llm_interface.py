import os
import logging
import json
import time
from pathlib import Path
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from llama_cpp import Llama
import utils

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LLMInterface:
    """
    Interface for local LLM integration with RAG for mutual fund analysis and recommendations.
    Uses Mistral-7B (Q4_K_M quantization) via llama-cpp-python.
    """
    
    def __init__(self, 
                 model_path: str = None,
                 max_tokens: int = 512,
                 temperature: float = 0.7,
                 top_p: float = 0.9,
                 context_window: int = 8192,
                 verbose: bool = False):
        """
        Initialize the LLM interface.
        
        Args:
            model_path: Path to the GGUF model file. If None, will use default path.
            max_tokens: Maximum number of tokens to generate.
            temperature: Sampling temperature (higher = more creative, lower = more deterministic).
            top_p: Nucleus sampling parameter.
            context_window: Maximum context window size.
            verbose: Whether to print verbose output.
        """
        logger.info("Initializing LLM Interface")
        
        # Get model path
        if model_path is None:
            model_paths = utils.get_model_paths()
            model_path = model_paths.get("llm_model", "models/mistral-7b-instruct-v0.2.Q4_K_M.gguf")
        
        self.model_path = model_path
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.context_window = context_window
        self.verbose = verbose
        
        # Check if model file exists
        if not os.path.exists(self.model_path):
            logger.warning(f"Model file not found at {self.model_path}")
            logger.info("Please download the model file manually and place it at the specified path.")
            logger.info("For Mistral-7B (Q4_K_M): https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF")
            self.model = None
        else:
            try:
                # Initialize the model
                logger.info(f"Loading LLM from {self.model_path}")
                self.model = Llama(
                    model_path=self.model_path,
                    n_ctx=self.context_window,
                    n_gpu_layers=-1,  # Use all available GPU layers
                    verbose=self.verbose
                )
                logger.info("LLM loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load LLM: {str(e)}")
                self.model = None
    
    def is_model_loaded(self) -> bool:
        """Check if the model is loaded."""
        return self.model is not None
    
    def generate_system_prompt(self) -> str:
        """Generate the system prompt for the LLM."""
        return """You are MutualFundGPT, an AI assistant specialized in analyzing and explaining mutual funds.
You provide clear, concise, factual information about mutual funds and help investors make informed decisions.
Always base your responses on the provided context information about mutual funds.
Never make up fund details, returns, or holdings that are not mentioned in the context.
Your analysis should be balanced, mentioning both potential benefits and risks.
When comparing funds, use objective metrics like returns, risk level, and expense ratio."""
    
    def generate_response(self, 
                         user_query: str, 
                         context_data: List[Dict[str, Any]],
                         max_length: int = 512) -> Tuple[str, float]:
        """
        Generate a response to a user query using RAG with the mutual fund data.
        
        Args:
            user_query: The user's query about mutual funds.
            context_data: List of relevant mutual fund data to use as context.
            max_length: Maximum response length in tokens.
            
        Returns:
            Tuple of (generated_response, execution_time)
        """
        if not self.is_model_loaded():
            return "Model not loaded. Please download the model file.", 0.0
        
        start_time = time.time()
        
        # Prepare context from the fund data
        context_str = self._prepare_context(context_data)
        
        # Prepare the prompt
        system_prompt = self.generate_system_prompt()
        
        # Format prompt following Mistral chat template
        # See: https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF
        prompt = f"""<s>[INST] {system_prompt}

Here's information about mutual funds relevant to the query:
{context_str}

User query: {user_query} [/INST]"""
        
        try:
            # Generate response
            response = self.model.create_completion(
                prompt=prompt,
                max_tokens=max_length,
                temperature=self.temperature,
                top_p=self.top_p,
                stop=["</s>", "[INST]"],  # Stop at end of generation or new instruction
            )
            
            # Extract generated text
            generated_text = response['choices'][0]['text'].strip()
            
            execution_time = time.time() - start_time
            logger.info(f"Generated response in {execution_time:.2f} seconds")
            
            return generated_text, execution_time
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return f"Error generating response: {str(e)}", time.time() - start_time
    
    def analyze_fund(self, 
                    fund_data: Dict[str, Any], 
                    user_query: Optional[str] = None) -> Tuple[str, float]:
        """
        Analyze a specific mutual fund and generate insights.
        
        Args:
            fund_data: Data for the fund to analyze.
            user_query: Optional specific question about the fund.
            
        Returns:
            Tuple of (analysis_text, execution_time)
        """
        if not self.is_model_loaded():
            return "Model not loaded. Please download the model file.", 0.0
        
        # Default query if none provided
        if user_query is None or user_query.strip() == "":
            user_query = f"Analyze this mutual fund ({fund_data.get('fund_name', 'Unknown Fund')}) and provide key insights about its performance, risk, holdings, and suitability for different investors."
        
        # Prepare context with just this fund
        context_data = [fund_data]
        
        return self.generate_response(user_query, context_data)
    
    def compare_funds(self, 
                     fund_list: List[Dict[str, Any]], 
                     comparison_aspects: Optional[List[str]] = None) -> Tuple[str, float]:
        """
        Compare multiple mutual funds across various aspects.
        
        Args:
            fund_list: List of fund data dictionaries to compare.
            comparison_aspects: Optional list of aspects to focus on in the comparison.
            
        Returns:
            Tuple of (comparison_text, execution_time)
        """
        if not self.is_model_loaded():
            return "Model not loaded. Please download the model file.", 0.0
        
        if not fund_list or len(fund_list) < 2:
            return "Need at least two funds to compare.", 0.0
        
        # Default comparison aspects
        if comparison_aspects is None:
            comparison_aspects = ["performance", "risk", "expense ratio", "holdings", "suitability"]
        
        # Create comparison query
        fund_names = [f.get('fund_name', 'Unknown Fund') for f in fund_list]
        comparison_query = f"Compare these mutual funds: {', '.join(fund_names)}. "
        comparison_query += f"Focus on these aspects: {', '.join(comparison_aspects)}. "
        comparison_query += "Which fund might be better for different types of investors?"
        
        return self.generate_response(comparison_query, fund_list)
    
    def recommend_funds(self, 
                       user_profile: Dict[str, Any], 
                       fund_candidates: List[Dict[str, Any]]) -> Tuple[str, float]:
        """
        Recommend funds to a user based on their profile and preferences.
        
        Args:
            user_profile: Dictionary with user investment profile information.
            fund_candidates: List of fund data dictionaries to consider for recommendations.
            
        Returns:
            Tuple of (recommendation_text, execution_time)
        """
        if not self.is_model_loaded():
            return "Model not loaded. Please download the model file.", 0.0
        
        # Build a profile description
        profile_str = "Investor profile: "
        for key, value in user_profile.items():
            profile_str += f"{key}: {value}, "
        profile_str = profile_str.rstrip(", ")
        
        # Create recommendation query
        recommendation_query = f"Based on this {profile_str}, recommend the most suitable mutual funds from the options provided. "
        recommendation_query += "Explain your recommendations and why they match the investor's profile."
        
        return self.generate_response(recommendation_query, fund_candidates)
    
    def explain_financial_concept(self, 
                                concept: str, 
                                related_funds: Optional[List[Dict[str, Any]]] = None) -> Tuple[str, float]:
        """
        Explain a financial concept with examples from related funds if provided.
        
        Args:
            concept: The financial concept to explain.
            related_funds: Optional list of funds that showcase this concept.
            
        Returns:
            Tuple of (explanation_text, execution_time)
        """
        if not self.is_model_loaded():
            return "Model not loaded. Please download the model file.", 0.0
        
        explanation_query = f"Explain the financial concept of '{concept}' in the context of mutual funds. "
        
        if related_funds and len(related_funds) > 0:
            explanation_query += "Use the provided mutual funds as examples to illustrate this concept."
            return self.generate_response(explanation_query, related_funds)
        else:
            explanation_query += "Provide a clear explanation with general examples."
            return self.generate_response(explanation_query, [])
    
    def _prepare_context(self, fund_data_list: List[Dict[str, Any]]) -> str:
        """
        Prepare context string from fund data for the LLM.
        
        Args:
            fund_data_list: List of fund data dictionaries.
            
        Returns:
            Formatted context string
        """
        if not fund_data_list:
            return "No fund information available."
        
        context_parts = []
        
        for i, fund in enumerate(fund_data_list, 1):
            # Start with fund name and basic info
            fund_str = f"Fund {i}: {fund.get('fund_name', 'Unknown Fund')}\n"
            
            # Add key details
            details = [
                (f"AMC: {fund.get('amc', 'N/A')}"),
                (f"Category: {fund.get('category', 'N/A')}"),
                (f"Risk Level: {fund.get('risk_level', 'N/A')}")
            ]
            
            # Add performance metrics
            if 'return_1yr' in fund and fund['return_1yr'] is not None:
                details.append(f"1-Year Return: {fund.get('return_1yr')}%")
            if 'return_3yr' in fund and fund['return_3yr'] is not None:
                details.append(f"3-Year Return: {fund.get('return_3yr')}%")
            if 'return_5yr' in fund and fund['return_5yr'] is not None:
                details.append(f"5-Year Return: {fund.get('return_5yr')}%")
            
            # Add expense ratio
            if 'expense_ratio' in fund and fund['expense_ratio'] is not None:
                details.append(f"Expense Ratio: {fund.get('expense_ratio')}%")
            
            # Add AUM (Assets Under Management)
            if 'aum_crore' in fund and fund['aum_crore'] is not None:
                details.append(f"AUM: ₹{fund.get('aum_crore')} crores")
            
            # Add top holdings if available
            if 'top_holdings' in fund and fund['top_holdings']:
                holdings_str = ", ".join(fund['top_holdings'][:5])  # Limit to top 5
                details.append(f"Top Holdings: {holdings_str}")
            
            # Add sector allocation if available
            if 'sector_allocation' in fund and fund['sector_allocation']:
                sectors = fund['sector_allocation'][:3]  # Limit to top 3
                sector_str = ", ".join([f"{s[0]} ({s[1]}%)" for s in sectors])
                details.append(f"Top Sectors: {sector_str}")
            
            # Add description if available
            if 'description' in fund and fund['description']:
                details.append(f"Description: {fund['description']}")
            
            # Combine all details
            fund_str += "\n".join(details)
            context_parts.append(fund_str)
        
        # Join all fund contexts with separators
        return "\n\n".join(context_parts)

    def download_model_instructions(self) -> str:
        """
        Provide instructions for downloading the model.
        
        Returns:
            Instructions text
        """
        instructions = """
# Instructions for downloading Mistral-7B Model

## Option 1: Download from Hugging Face (Recommended)
1. Visit: https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF
2. Download the Q4_K_M quantized version: mistral-7b-instruct-v0.2.Q4_K_M.gguf (~4.2 GB)
3. Save the file to the `models` directory in your project

## Option 2: Using Hugging Face CLI
```
pip install huggingface_hub
python -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='TheBloke/Mistral-7B-Instruct-v0.2-GGUF', filename='mistral-7b-instruct-v0.2.Q4_K_M.gguf', local_dir='./models')"
```

## Option 3: Using wget/curl
```
# For Linux/Mac:
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf -O ./models/mistral-7b-instruct-v0.2.Q4_K_M.gguf

# For Windows (PowerShell):
curl -L "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf" -o "./models/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
```

## System Requirements
- At least 8GB RAM
- VRAM: 6-8GB for optimal performance
- Disk space: ~4.5GB for the model file

Once downloaded, the LLM interface will automatically detect and load the model.
"""
        return instructions

    def generate_rag_response(self, 
                              user_query: str, 
                              rag_prompt: str,
                              max_length: int = 512) -> Tuple[str, float]:
        """
        Generate a response using a pre-formatted RAG prompt.
        This is specifically for the Phase 6 implementation where the prompt
        is already formatted with the fund information.
        
        Args:
            user_query: The user's original query
            rag_prompt: The pre-formatted RAG prompt
            max_length: Maximum response length in tokens
            
        Returns:
            Tuple of (generated_response, execution_time)
        """
        if not self.is_model_loaded():
            return "Model not loaded. Please download the model file.", 0.0
        
        start_time = time.time()
        
        try:
            # Generate response
            response = self.model.create_completion(
                prompt=rag_prompt,
                max_tokens=max_length,
                temperature=self.temperature,
                top_p=self.top_p,
                stop=["</s>", "[INST]"],  # Stop at end of generation or new instruction
            )
            
            # Extract generated text with proper error handling
            if 'choices' in response and len(response['choices']) > 0 and 'text' in response['choices'][0]:
                generated_text = response['choices'][0]['text'].strip()
            else:
                logger.warning(f"Unexpected response format from LLM: {response}")
                generated_text = "Sorry, I couldn't generate a proper response. The model returned an unexpected format."
            
            execution_time = time.time() - start_time
            logger.info(f"Generated RAG response in {execution_time:.2f} seconds")
            
            return generated_text, execution_time
            
        except Exception as e:
            logger.error(f"Error generating RAG response: {str(e)}")
            return f"Error generating RAG response: {str(e)}", time.time() - start_time

# Example usage if run directly
if __name__ == "__main__":
    # Create model directory if it doesn't exist
    models_dir = utils.get_model_paths()["llm_model"].parent
    os.makedirs(models_dir, exist_ok=True)
    
    # Initialize LLM interface
    llm = LLMInterface(verbose=True)
    
    if not llm.is_model_loaded():
        print("\n" + "="*80)
        print("Model not found. Please download it following these instructions:")
        print(llm.download_model_instructions())
        print("="*80 + "\n")
    else:
        # Test with sample query and context
        sample_fund = {
            "fund_name": "HDFC Midcap Opportunities Fund",
            "amc": "HDFC",
            "category": "Mid Cap",
            "risk_level": "Moderately High",
            "return_1yr": 24.5,
            "return_3yr": 17.3,
            "return_5yr": 15.8,
            "expense_ratio": 1.85,
            "aum_crore": 42560,
            "top_holdings": ["Tata Elxsi", "Cholamandalam Investment", "Bharat Electronics", "Coforge", "Astral"],
            "sector_allocation": [("Financial Services", 23.4), ("Technology", 18.2), ("Consumer Cyclical", 12.5)]
        }
        
        # Generate analysis
        analysis, time_taken = llm.analyze_fund(sample_fund)
        
        print("\n" + "="*80)
        print(f"Fund Analysis (generated in {time_taken:.2f}s):")
        print(analysis)
        print("="*80 + "\n") 