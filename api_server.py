import os
import json
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import utils
from data_preprocessing import preprocess_data, generate_fund_descriptions
from embedding_indexing import load_or_create_embeddings, create_faiss_index
from search_engine import SearchEngine
from query_parser import QueryParser
from enhanced_retrieval import EnhancedRetrieval
from llm_interface import LLMInterface
from evaluation import SystemEvaluator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize components
search_engine = None
query_parser = None
enhanced_retrieval = None
llm = None
evaluator = None
explanation_enabled = False

@app.before_first_request
def initialize_components():
    global search_engine, query_parser, enhanced_retrieval, llm, evaluator
    
    logger.info("Initializing server components...")
    try:
        # Initialize components
        search_engine = SearchEngine()
        query_parser = QueryParser()
        enhanced_retrieval = EnhancedRetrieval()
        llm = LLMInterface()
        evaluator = SystemEvaluator(search_engine, query_parser, enhanced_retrieval, llm)
        
        logger.info("All components initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing components: {str(e)}")
        raise

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "ok",
        "components": {
            "search_engine": search_engine is not None,
            "query_parser": query_parser is not None,
            "enhanced_retrieval": enhanced_retrieval is not None,
            "llm": llm is not None if llm else False,
            "llm_loaded": llm.is_model_loaded() if llm else False
        }
    })

# Search endpoint
@app.route('/api/search', methods=['POST'])
def search_funds():
    data = request.json
    query = data.get('query', '')
    filters = data.get('filters', {})
    show_explanation = data.get('showExplanation', False)
    
    try:
        logger.info(f"Searching for: {query} with filters: {filters}")
        
        # Parse query to extract structured filters
        parsed_result = query_parser.parse_query(query)
        extracted_filters = parsed_result.get('filters', {})
        
        # Merge explicit filters with extracted filters (explicit ones take precedence)
        combined_filters = {**extracted_filters, **filters}
        
        # Convert API filter format to internal filter format
        internal_filters = convert_filters(combined_filters)
        
        # Get search results
        search_results = search_engine.search(
            query=query,
            filters=internal_filters,
            top_k=10  # Get more results for ranking
        )
        
        # Apply enhanced retrieval scoring
        enhanced_results = enhanced_retrieval.compute_final_scores(
            search_results,
            query,
            internal_filters
        )
        
        # Convert results to API format
        api_results = convert_results_to_api_format(enhanced_results, show_explanation)
        
        return jsonify({
            "success": True,
            "results": api_results,
            "query": query,
            "appliedFilters": combined_filters
        })
    
    except Exception as e:
        logger.error(f"Error in search: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Fund analysis endpoint
@app.route('/api/analyze/<fund_id>', methods=['GET'])
def analyze_fund(fund_id):
    try:
        # Get fund details
        fund_data = get_fund_by_id(fund_id)
        
        if not fund_data:
            return jsonify({
                "success": False,
                "error": "Fund not found"
            }), 404
        
        # Convert to API format
        api_format_fund = convert_fund_to_api_format(fund_data)
        
        # Generate analysis using LLM
        analysis_prompt = f"""
You are a mutual fund advisor. Analyze the following fund:

Fund Name: {fund_data.get('fund_name', 'Unknown')}
Fund Category: {fund_data.get('category', 'Unknown')}
Fund House: {fund_data.get('amc', 'Unknown')}
1-Year Return: {fund_data.get('return_1yr', 'N/A')}%
3-Year Return: {fund_data.get('return_3yr', 'N/A')}%
5-Year Return: {fund_data.get('return_5yr', 'N/A')}%
Risk Level: {fund_data.get('risk_level', 'Unknown')}
Expense Ratio: {fund_data.get('expense_ratio', 'N/A')}%

Provide a concise analysis of this fund's performance, risk, and suitability for investors.
Focus on strengths, weaknesses, and who this fund might be appropriate for.
"""
        
        # Get LLM analysis
        analysis, _ = llm.generate_response(analysis_prompt, max_length=512)
        
        # Return combined data
        return jsonify({
            "success": True,
            "fund": api_format_fund,
            "analysis": analysis
        })
    
    except Exception as e:
        logger.error(f"Error in fund analysis: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Fund comparison endpoint
@app.route('/api/compare', methods=['POST'])
def compare_funds():
    data = request.json
    fund_ids = data.get('fundIds', [])
    
    if not fund_ids or len(fund_ids) < 2:
        return jsonify({
            "success": False,
            "error": "At least 2 fund IDs are required for comparison"
        }), 400
    
    try:
        # Get fund details for all IDs
        funds_data = []
        for fund_id in fund_ids:
            fund_data = get_fund_by_id(fund_id)
            if fund_data:
                api_format_fund = convert_fund_to_api_format(fund_data)
                funds_data.append(api_format_fund)
        
        if len(funds_data) < 2:
            return jsonify({
                "success": False,
                "error": "Not enough valid funds found for comparison"
            }), 404
        
        # Generate comparison using LLM
        fund_names = [f["name"] for f in funds_data]
        comparison_prompt = f"""
You are a mutual fund advisor. Compare the following funds:

{', '.join(fund_names)}

Analyze their performance, risk profiles, expense ratios, and suitability for different investor types.
Highlight the key differences and make a recommendation on which fund(s) might be better for different investor profiles.
"""
        
        # Get LLM comparison
        comparison, _ = llm.generate_response(comparison_prompt, max_length=768)
        
        # Return comparison data
        return jsonify({
            "success": True,
            "funds": funds_data,
            "comparison": comparison
        })
    
    except Exception as e:
        logger.error(f"Error in fund comparison: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Toggle explanation endpoint
@app.route('/api/toggle-explanation', methods=['POST'])
def toggle_explanation():
    global explanation_enabled
    data = request.json
    show_explanation = data.get('showExplanation', False)
    explanation_enabled = show_explanation
    
    return jsonify({
        "success": True,
        "showExplanation": explanation_enabled
    })

# Helper functions

def convert_filters(filters):
    """Convert API filter format to internal filter format"""
    internal_filters = {}
    
    # Fund type to category mapping
    if filters.get('fundType') and filters.get('fundType') != 'all':
        fund_type = filters.get('fundType')
        if fund_type == 'equity':
            internal_filters['category'] = 'Equity'
        elif fund_type == 'debt':
            internal_filters['category'] = 'Debt'
        elif fund_type == 'hybrid':
            internal_filters['category'] = 'Hybrid'
        elif fund_type == 'index':
            internal_filters['category'] = 'Index'
        elif fund_type == 'etf':
            internal_filters['category'] = 'ETF'
    
    # Risk level mapping
    if filters.get('riskLevel') and filters.get('riskLevel') != 'all':
        risk_level = filters.get('riskLevel')
        if risk_level == 'low':
            internal_filters['risk_level'] = 'Low'
        elif risk_level == 'moderate':
            internal_filters['risk_level'] = 'Moderate'
        elif risk_level == 'high':
            internal_filters['risk_level'] = 'High'
        elif risk_level == 'very-high':
            internal_filters['risk_level'] = 'Very High'
    
    # Minimum return (map to 1-year return)
    if filters.get('minReturn') and float(filters.get('minReturn')) > 0:
        internal_filters['min_return_1yr'] = float(filters.get('minReturn'))
    
    # Other filters can be passed through directly
    if filters.get('amc'):
        internal_filters['amc'] = filters.get('amc')
        
    if filters.get('sector'):
        internal_filters['sector'] = filters.get('sector')
        
    if filters.get('max_expense_ratio'):
        internal_filters['max_expense_ratio'] = float(filters.get('max_expense_ratio'))
    
    return internal_filters

def convert_results_to_api_format(results, show_explanation=False):
    """Convert internal search results to API format"""
    api_results = []
    
    for result in results:
        fund_data = result.get('fund_data', {})
        api_fund = convert_fund_to_api_format(fund_data)
        
        # Add search-specific data
        api_fund['searchScore'] = result.get('final_score', 0)
        
        # Add score explanation if enabled
        if show_explanation and 'score_explanation' in result:
            api_fund['scoreExplanation'] = {
                'semantic': result['score_explanation'].get('semantic_similarity', 'N/A'),
                'metadata': result['score_explanation'].get('metadata_match', 'N/A'),
                'fuzzy': result['score_explanation'].get('fuzzy_match', 'N/A'),
                'final': result['score_explanation'].get('final_score', 'N/A')
            }
        
        api_results.append(api_fund)
    
    return api_results

def convert_fund_to_api_format(fund_data):
    """Convert internal fund data to API format"""
    return {
        "id": fund_data.get('fund_id', 'unknown'),
        "name": fund_data.get('fund_name', 'Unknown Fund'),
        "ticker": fund_data.get('ticker', fund_data.get('fund_id', 'unknown').upper()),
        "fundHouse": fund_data.get('amc', 'Unknown'),
        "category": fund_data.get('category', 'Unknown'),
        "returns": {
            "oneYear": fund_data.get('return_1yr', 0),
            "threeYear": fund_data.get('return_3yr', 0),
            "fiveYear": fund_data.get('return_5yr', 0)
        },
        "aum": f"₹{fund_data.get('aum_crore', 0)} Cr",
        "risk": fund_data.get('risk_level', 'Moderate'),
        "description": fund_data.get('description', 'No description available.')
    }

def get_fund_by_id(fund_id):
    """Get fund data by ID"""
    # Get output paths
    output_paths = utils.get_output_paths()
    
    try:
        # Load the preprocessed fund data
        with open(output_paths["preprocessed_funds"], 'r') as f:
            all_funds = json.load(f)
        
        # Return the fund data if found
        if fund_id in all_funds:
            return all_funds[fund_id]
        
        # If not found directly, try case-insensitive search
        for id_key, fund in all_funds.items():
            if id_key.lower() == fund_id.lower():
                return fund
        
        # Not found
        return None
    
    except Exception as e:
        logger.error(f"Error getting fund by ID: {str(e)}")
        return None

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 