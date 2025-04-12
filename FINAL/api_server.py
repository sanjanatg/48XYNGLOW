# Fix import paths - ensures modules can be found regardless of where script is run from
import os
import sys
# Add the directory containing this file to Python's path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

# Import our RAG system components
from query_parser import QueryParser
from lexical_search import BM25Retriever
from semantic_search import SemanticSearch
from metadata_filter import MetadataFilter
from score_fusion import ScoreFusion
from rag_prompt import RAGPromptGenerator
from ollama_client import OllamaClient
from rag_ui_bridge import RAGUIBridge

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize the RAG system
rag_bridge = RAGUIBridge("sample_funds.csv", model_name="mistral:latest")

# Global flag for showing explanations
show_explanation = True

def map_risk_score_to_text(risk_score: int) -> str:
    """Convert numeric risk score to text representation"""
    if isinstance(risk_score, str):
        return risk_score
    
    if risk_score == 1:
        return "Low"
    elif risk_score == 2:
        return "Moderate"
    elif risk_score == 3:
        return "High"
    elif risk_score >= 4:
        return "Very High"
    else:
        return "Unknown"

def fund_to_ui_format(fund: Dict[str, Any], include_scores: bool = True) -> Dict[str, Any]:
    """Convert fund data from RAG system format to UI format"""
    # Generate a deterministic ID based on fund name
    fund_id = str(hash(fund.get('fund_name', '')))[:8]
    
    # Map the fund data to the UI format
    ui_fund = {
        "id": fund_id,
        "name": fund.get('fund_name', 'Unknown Fund'),
        "ticker": fund.get('ticker', fund.get('fund_name', 'UNKNOWN')[:5]),
        "fundHouse": fund.get('fund_house', fund.get('category', 'Unknown').split(':')[0] if ':' in fund.get('category', '') else 'Unknown'),
        "category": fund.get('category', 'Unknown'),
        "aum": fund.get('aum', '10M'),  # Default AUM
        "risk": map_risk_score_to_text(fund.get('risk_score', 'Unknown')),
        "description": fund.get('description', 'No description available.'),
        "returns": {
            "oneYear": fund.get('returns_1yr', fund.get('returns_1yr', 0)) if isinstance(fund.get('returns_1yr', 0), (int, float)) else 0,
            "threeYear": fund.get('returns_3yr', fund.get('returns_3yr', 0)) if isinstance(fund.get('returns_3yr', 0), (int, float)) else 0,
            "fiveYear": fund.get('returns_5yr', fund.get('returns_5yr', 0)) if isinstance(fund.get('returns_5yr', 0), (int, float)) else 0,
        },
    }

    # Add scores if requested
    if include_scores and show_explanation:
        semantic_score = fund.get('semantic_score', 0)
        bm25_score = fund.get('bm25_score', 0)
        fuzzy_name_score = fund.get('fuzzy_name_score', 0)
        combined_score = fund.get('combined_score', 0)
        
        ui_fund["scoreExplanation"] = {
            "semantic": f"{semantic_score:.2f}" if isinstance(semantic_score, (int, float)) else "0.00",
            "metadata": f"{bm25_score:.2f}" if isinstance(bm25_score, (int, float)) else "0.00",
            "fuzzy": f"{fuzzy_name_score:.2f}" if isinstance(fuzzy_name_score, (int, float)) else "0.00",
            "final": f"{combined_score:.2f}" if isinstance(combined_score, (int, float)) else "0.00"
        }
    
    return ui_fund

def get_fund_analysis(fund: Dict[str, Any], llm_response: str) -> Dict[str, Any]:
    """Generate fund analysis data based on the fund and LLM response"""
    # Extract strengths and weaknesses from LLM response (simple heuristic approach)
    strengths = []
    weaknesses = []
    
    # Simple parsing to extract strengths and weaknesses
    lines = llm_response.split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        if "strength" in line.lower() or "advantage" in line.lower() or "pro" in line.lower():
            current_section = "strengths"
            continue
        elif "weakness" in line.lower() or "drawback" in line.lower() or "con" in line.lower():
            current_section = "weaknesses"
            continue
        elif line.startswith('-') or line.startswith('•'):
            if current_section == "strengths":
                strengths.append(line[1:].strip())
            elif current_section == "weaknesses":
                weaknesses.append(line[1:].strip())
    
    # If we couldn't extract strengths/weaknesses, create some based on fund data
    if not strengths:
        risk = map_risk_score_to_text(fund.get('risk_score', 'Unknown'))
        returns_3yr = fund.get('returns_3yr', 0)
        
        if risk == "Low":
            strengths.append("Lower risk compared to other funds in the same category")
        if risk == "High" and returns_3yr > 10:
            strengths.append("Higher potential returns with higher risk")
        if isinstance(returns_3yr, (int, float)) and returns_3yr > 10:
            strengths.append(f"Strong 3-year returns of {returns_3yr}%")
        
        strengths.append("Professional fund management")
    
    if not weaknesses:
        risk = map_risk_score_to_text(fund.get('risk_score', 'Unknown'))
        expense_ratio = fund.get('expense_ratio', 0)
        
        if risk == "High":
            weaknesses.append("Higher volatility and potential for losses")
        if expense_ratio > 1.5:
            weaknesses.append(f"Relatively high expense ratio of {expense_ratio}%")
        
        weaknesses.append("Past performance is not indicative of future results")
    
    # Create sector allocation data (placeholder)
    sectors = [
        {"name": "Technology", "value": 35},
        {"name": "Financials", "value": 25},
        {"name": "Healthcare", "value": 15},
        {"name": "Consumer", "value": 15},
        {"name": "Others", "value": 10}
    ]
    
    # Create analysis object
    analysis = {
        "summary": llm_response,
        "strengths": strengths[:3],  # Limit to top 3
        "weaknesses": weaknesses[:3],  # Limit to top 3
        "performance": {
            "1yr": {
                "fund": fund.get('returns_1yr', 0),
                "category": fund.get('returns_1yr', 0) * 0.9,  # 90% of fund performance
                "benchmark": fund.get('returns_1yr', 0) * 0.95  # 95% of fund performance
            },
            "3yr": {
                "fund": fund.get('returns_3yr', 0),
                "category": fund.get('returns_3yr', 0) * 0.9,
                "benchmark": fund.get('returns_3yr', 0) * 0.95
            },
            "5yr": {
                "fund": fund.get('returns_5yr', 0),
                "category": fund.get('returns_5yr', 0) * 0.9,
                "benchmark": fund.get('returns_5yr', 0) * 0.95
            }
        },
        "sectorAllocation": sectors,
        "riskMetrics": {
            "sharpeRatio": "1.2",
            "standardDeviation": "12.5",
            "beta": "0.95",
            "alpha": "2.1"
        },
        "benchmarkComparison": {
            "oneYear": {
                "fund": fund.get('returns_1yr', 0),
                "benchmark": fund.get('returns_1yr', 0) * 0.95
            },
            "threeYear": {
                "fund": fund.get('returns_3yr', 0),
                "benchmark": fund.get('returns_3yr', 0) * 0.95
            },
            "fiveYear": {
                "fund": fund.get('returns_5yr', 0),
                "benchmark": fund.get('returns_5yr', 0) * 0.95
            }
        },
        "recommendation": llm_response
    }
    
    return {"analysis": analysis}

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "service": "fund-search-api",
        "ollama_available": rag_bridge.llm_client.is_available
    })

@app.route('/api/toggle-explanation', methods=['POST'])
def toggle_explanation():
    """Toggle explanation visibility"""
    global show_explanation
    data = request.json
    show_explanation = data.get('showExplanation', True)
    return jsonify({
        "success": True,
        "showExplanation": show_explanation
    })

@app.route('/api/search', methods=['POST'])
def search():
    """Search endpoint that uses the RAG system"""
    start_time = time.time()
    
    # Parse request data
    data = request.json
    query = data.get('query', '')
    filters = data.get('filters', {})
    top_k = int(data.get('top_k', 10))
    
    if not query:
        return jsonify({
            "success": False,
            "error": "Query is required",
            "results": []
        })
    
    # Process the query through the RAG system
    try:
        results = rag_bridge.process_query(query, top_k=top_k)
        
        # Apply additional filters from the UI if provided
        filtered_results = results["ranked_funds"]
        
        # Convert results to UI format
        ui_results = [fund_to_ui_format(fund, include_scores=True) for fund in filtered_results]
        
        return jsonify({
            "success": True,
            "query": query,
            "results": ui_results,
            "llm_response": results.get("llm_response", ""),
            "timing": {
                "total": time.time() - start_time,
                "breakdown": results.get("timing", {})
            }
        })
    except Exception as e:
        print(f"Error processing search: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "results": []
        })

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Analyze a specific fund using the RAG system"""
    data = request.json
    fund_id = data.get('fundId', '')
    
    if not fund_id:
        return jsonify({
            "success": False,
            "error": "Fund ID is required"
        })
    
    try:
        # For demo purposes, we'll use the search functionality to find the fund
        # In a real system, you would have a database lookup
        all_funds = rag_bridge.fund_data.to_dict('records')
        
        # Find the fund by ID (which we're generating from the fund name hash)
        found_fund = None
        for fund in all_funds:
            if str(hash(fund.get('fund_name', '')))[:8] == fund_id:
                found_fund = fund
                break
                
        if not found_fund:
            return jsonify({
                "success": False,
                "error": "Fund not found"
            })
        
        # Generate a query about this specific fund
        query = f"Analyze the {found_fund.get('fund_name')} fund"
        
        # Use the RAG system to generate an analysis
        results = rag_bridge.process_query(query, top_k=1)
        llm_response = results.get("llm_response", "")
        
        # Generate detailed analysis
        analysis = get_fund_analysis(found_fund, llm_response)
        
        return jsonify({
            "success": True,
            "fund": fund_to_ui_format(found_fund),
            **analysis
        })
        
    except Exception as e:
        print(f"Error analyzing fund: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 