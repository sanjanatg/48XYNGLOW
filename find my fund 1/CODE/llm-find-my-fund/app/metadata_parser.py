"""
Metadata Parser for Fund Search Results

This module processes fund search results and generates explanations
about why particular funds were matched to the user's query.
"""

import re
from typing import Dict, List, Any

def extract_fund_type(fund_name: str) -> str:
    """Extract fund type from the fund name"""
    fund_types = {
        "ELSS": ["ELSS", "Tax Saver", "Tax Relief", "Tax Advantage"],
        "Large Cap": ["Large Cap", "Largecap", "Large-Cap", "Top 100"],
        "Mid Cap": ["Mid Cap", "Midcap", "Mid-Cap"],
        "Small Cap": ["Small Cap", "Smallcap", "Small-Cap"],
        "Multi Cap": ["Multi Cap", "Multicap", "Multi-Cap", "Flexi Cap", "Flexicap"],
        "Index": ["Index", "Nifty", "Sensex"],
        "Value": ["Value", "Contra"],
        "Debt": ["Debt", "Bond", "Income", "Credit Risk", "Corporate Bond"],
        "Liquid": ["Liquid", "Cash", "Money Market"],
        "Hybrid": ["Hybrid", "Balanced", "Equity Savings", "Asset Allocation"],
        "Technology": ["Technology", "Tech", "Digital", "IT"],
    }
    
    for fund_type, keywords in fund_types.items():
        for keyword in keywords:
            if keyword.lower() in fund_name.lower():
                return fund_type
    
    return "Other"

def format_aum(aum: float) -> str:
    """Format AUM value for display"""
    if aum is None:
        return "N/A"
    
    if aum >= 10000:
        return f"₹{aum/1000:.2f} Thousand Cr"
    elif aum >= 1000:
        return f"₹{aum:.2f} Cr"
    elif aum >= 100:
        return f"₹{aum:.2f} Cr"
    else:
        return f"₹{aum:.2f} Cr"

def format_returns(returns: float) -> str:
    """Format returns value for display"""
    if returns is None:
        return "N/A"
    
    return f"{returns:.2f}%"

def evaluate_returns(returns: float) -> str:
    """Evaluate returns level"""
    if returns is None:
        return "Unknown"
    
    if returns >= 25:
        return "excellent"
    elif returns >= 15:
        return "good"
    elif returns >= 10:
        return "average"
    else:
        return "below average"

def evaluate_risk(risk: str) -> str:
    """Standardize risk level"""
    if not risk:
        return "Unknown"
    
    risk = risk.lower()
    if "high" in risk:
        return "High"
    elif "moderate" in risk or "medium" in risk:
        return "Moderate"
    elif "low" in risk:
        return "Low"
    else:
        return risk.capitalize()

def explain_match(query: str, fund: Dict[str, Any]) -> str:
    """Generate an explanation for why a fund matched the query"""
    fund_name = fund.get("fund_name", "")
    amc = fund.get("amc", "")
    category = fund.get("category", "")
    returns_1yr = fund.get("returns_1yr", 0)
    returns_3yr = fund.get("returns_3yr", 0)
    returns_5yr = fund.get("returns_5yr", 0)
    risk_level = fund.get("risk_level", "")
    
    # Clean the query and fund details for matching
    query_terms = query.lower().split()
    
    # Look for matches in different fund attributes
    matches = []
    
    # Check for name match
    if any(term in fund_name.lower() for term in query_terms):
        matches.append("fund name")
    
    # Check for AMC match
    if any(term in amc.lower() for term in query_terms):
        matches.append("fund house")
    
    # Check for category match
    if any(term in category.lower() for term in query_terms):
        matches.append("category")
    
    # Check for specific terms in query
    if any(term in query.lower() for term in ["tax", "elss", "80c"]) and "elss" in category.lower():
        matches.append("tax-saving ELSS category")
    
    if any(term in query.lower() for term in ["high return", "top performing"]):
        if returns_1yr > 20:
            matches.append("high 1-year returns")
        elif returns_3yr > 15:
            matches.append("strong 3-year performance")
    
    if any(term in query.lower() for term in ["safe", "low risk"]) and "low" in risk_level.lower():
        matches.append("low risk profile")
    
    if "technology" in query.lower() and ("technology" in category.lower() or "technology" in fund_name.lower()):
        matches.append("technology sector focus")
    
    # Default explanations if no specific matches
    if not matches:
        if returns_1yr > 15:
            matches.append("strong 1-year performance")
        elif "large" in category.lower():
            matches.append("large-cap orientation")
        else:
            matches.append("diversified portfolio")
    
    # Create the explanation
    if len(matches) == 1:
        explanation = f"This fund matched your search due to its {matches[0]}."
    else:
        explanation = f"This fund matched your search due to its {', '.join(matches[:-1])} and {matches[-1]}."
    
    # Add performance context
    if returns_1yr > 0:
        explanation += f" It has delivered {returns_1yr:.1f}% returns over the past year"
        if returns_3yr > 0:
            explanation += f" and {returns_3yr:.1f}% annually over 3 years."
        else:
            explanation += "."
    
    return explanation

def explain_results(query: str, results: List[Dict[str, Any]]) -> List[str]:
    """Generate explanations for a list of fund results"""
    explanations = []
    
    for fund in results:
        explanation = explain_match(query, fund)
        explanations.append(explanation)
    
    return explanations

def extract_metadata(query: str, results: List[Dict]) -> Dict:
    """
    Extract metadata from the query that contributed to matching
    
    Args:
        query: The original user query
        results: The search results
    
    Returns:
        Dictionary of metadata that matched
    """
    # Convert query to lowercase for easier matching
    query_lower = query.lower()
    
    metadata_matches = {}
    
    # Extract category
    categories = ["equity", "debt", "hybrid", "elss", "tax", "index", "international"]
    for category in categories:
        if category in query_lower:
            metadata_matches["category"] = category.upper()
            break
    
    # Extract sector
    sectors = ["technology", "tech", "banking", "financial", "healthcare", "pharma", 
               "consumption", "infrastructure", "energy", "infra"]
    for sector in sectors:
        if sector in query_lower:
            metadata_matches["sector"] = sector.capitalize()
            break
    
    # Extract risk
    risks = ["high risk", "low risk", "moderate risk", "medium risk"]
    for risk in risks:
        if risk in query_lower:
            metadata_matches["risk"] = risk.split()[0].capitalize()
            break
    
    # Extract fund house
    fund_houses = ["icici", "hdfc", "sbi", "axis", "kotak", "aditya birla", "reliance", "nippon", 
                   "dsp", "uti", "tata"]
    for house in fund_houses:
        if house in query_lower:
            metadata_matches["fund_house"] = house.upper()
            break
    
    # Extract returns expectations
    returns_pattern = r"returns?\s+(?:above|more than|greater than|exceeding)\s+(\d+(?:\.\d+)?)\s*%"
    returns_match = re.search(returns_pattern, query_lower)
    if returns_match:
        metadata_matches["min_returns"] = float(returns_match.group(1))
    
    # Extract AUM expectations
    aum_pattern = r"aum\s+(?:above|more than|greater than|exceeding)\s+(\d+(?:\.\d+)?)\s*(?:cr|crore)"
    aum_match = re.search(aum_pattern, query_lower)
    if aum_match:
        metadata_matches["min_aum"] = float(aum_match.group(1))
    
    # Extract holdings
    holdings_pattern = r"(?:with|holding|having|contains?)\s+(\w+)\s+holdings"
    holdings_match = re.search(holdings_pattern, query_lower)
    if holdings_match:
        metadata_matches["holdings"] = [holdings_match.group(1)]
    
    # Check for commonly mentioned companies
    companies = ["hdfc", "icici", "tcs", "reliance", "infosys", "sbi", "adani", "tata", "bharti", "bajaj"]
    for company in companies:
        if f"{company} holdings" in query_lower or f"holding {company}" in query_lower:
            metadata_matches.setdefault("holdings", []).append(company)
    
    return metadata_matches

def compare_funds(fund1: Dict, fund2: Dict) -> Dict:
    """
    Compare two funds and highlight the differences
    
    Args:
        fund1: First fund data
        fund2: Second fund data
    
    Returns:
        Dictionary with comparison results
    """
    comparison = {
        "fund1_name": fund1.get("name", "Fund 1"),
        "fund2_name": fund2.get("name", "Fund 2"),
        "comparisons": []
    }
    
    # Compare returns
    returns1 = fund1.get("metadata", {}).get("returns_1y")
    returns2 = fund2.get("metadata", {}).get("returns_1y")
    
    if returns1 is not None and returns2 is not None:
        diff = returns1 - returns2
        comparison["comparisons"].append({
            "metric": "1 Year Returns",
            "fund1_value": f"{returns1:.2f}%",
            "fund2_value": f"{returns2:.2f}%",
            "difference": f"{abs(diff):.2f}%",
            "better": "fund1" if diff > 0 else "fund2"
        })
    
    # Compare risk
    risk1 = fund1.get("metadata", {}).get("risk")
    risk2 = fund2.get("metadata", {}).get("risk")
    
    if risk1 and risk2:
        comparison["comparisons"].append({
            "metric": "Risk Level",
            "fund1_value": risk1,
            "fund2_value": risk2,
            "difference": "Different" if risk1 != risk2 else "Same",
            "better": "Equal" # Risk is subjective to investor preference
        })
    
    # Compare AUM
    aum1 = fund1.get("metadata", {}).get("aum")
    aum2 = fund2.get("metadata", {}).get("aum")
    
    if aum1 is not None and aum2 is not None:
        diff = aum1 - aum2
        comparison["comparisons"].append({
            "metric": "Fund Size (AUM)",
            "fund1_value": format_aum(aum1),
            "fund2_value": format_aum(aum2),
            "difference": format_aum(abs(diff)),
            "better": "Equal" # Size is not necessarily better or worse
        })
    
    # Compare expense ratio
    expense1 = fund1.get("metadata", {}).get("expense_ratio")
    expense2 = fund2.get("metadata", {}).get("expense_ratio")
    
    if expense1 is not None and expense2 is not None:
        diff = expense1 - expense2
        comparison["comparisons"].append({
            "metric": "Expense Ratio",
            "fund1_value": f"{expense1:.2f}%",
            "fund2_value": f"{expense2:.2f}%",
            "difference": f"{abs(diff):.2f}%",
            "better": "fund2" if diff > 0 else "fund1" # Lower expense is better
        })
    
    # Generate recommendation
    recommendation = generate_comparison_recommendation(comparison)
    comparison["recommendation"] = recommendation
    
    return comparison

def generate_comparison_recommendation(comparison: Dict) -> str:
    """Generate a recommendation based on fund comparison"""
    fund1_name = comparison["fund1_name"]
    fund2_name = comparison["fund2_name"]
    
    better_count = {"fund1": 0, "fund2": 0, "Equal": 0}
    
    for comp in comparison["comparisons"]:
        better = comp.get("better", "Equal")
        better_count[better] += 1
    
    if better_count["fund1"] > better_count["fund2"]:
        return f"{fund1_name} appears to be the better option based on the compared metrics."
    elif better_count["fund2"] > better_count["fund1"]:
        return f"{fund2_name} appears to be the better option based on the compared metrics."
    else:
        return f"Both {fund1_name} and {fund2_name} are comparable. Consider your specific investment goals to choose between them." 