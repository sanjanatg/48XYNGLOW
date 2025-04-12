"""
Utility functions for the Find My Fund application
"""

import re
import json
from typing import Dict, List, Any
import string
from difflib import get_close_matches
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Common stopwords to filter out from queries
STOPWORDS = {
    'a', 'an', 'the', 'and', 'or', 'but', 'of', 'in', 'on', 'at', 'by', 'for',
    'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before',
    'after', 'above', 'below', 'to', 'from', 'up', 'down', 'i', 'me', 'my', 'myself',
    'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 'yourself',
    'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself',
    'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what',
    'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are',
    'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do',
    'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because',
    'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against',
    'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
    'to', 'from', 'up', 'down', 'further', 'then', 'once', 'here', 'there', 'when',
    'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most',
    'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
    'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now'
}

# Common fund-related terms to keep even if they're stopwords
KEEP_TERMS = {
    'tax', 'equity', 'debt', 'growth', 'dividend', 'balance', 'balanced',
    'low', 'high', 'medium', 'moderate', 'risk', 'return', 'returns',
    'small', 'mid', 'large', 'cap', 'index', 'elss', 'sip', 'lumpsum',
    'aum', 'expense', 'ratio', 'nav', 'liquidity', 'holdings', 'portfolio',
    'diversified', 'international', 'sectoral', 'focused', 'short', 'long',
    'term', 'duration', 'overnight', 'liquid', 'ultra', 'hybrid', 'direct',
    'regular', 'plan', 'scheme', 'fund', 'funds'
}

# Fund houses and companies for spell checking
FUND_HOUSES = [
    'icici', 'icici prudential', 'hdfc', 'sbi', 'axis', 'kotak', 
    'aditya birla', 'aditya birla sun life', 'absl', 'nippon', 'reliance', 
    'dsp', 'uti', 'tata', 'idfc', 'mirae', 'mirae asset', 'edelweiss', 
    'franklin', 'franklin templeton', 'invesco', 'l&t', 'bandhan', 'hsbc', 
    'lic', 'motilal oswal', 'parag parikh', 'ppfas', 'quant', 'quantum', 
    'baroda', 'principal', 'canara robeco', 'itdfc', 'jm', 'sundaram', 
    'union', 'boi', 'bank of india', 'pgim'
]

# Stock companies for holdings matching
COMMON_STOCKS = [
    'hdfc', 'icici', 'sbi', 'reliance', 'tcs', 'infosys', 'l&t', 'itc',
    'bharti airtel', 'axis', 'kotak', 'tata motors', 'tata steel', 'bajaj',
    'hindustan unilever', 'hul', 'asian paints', 'maruti', 'mahindra',
    'adani', 'sun pharma', 'nestle', 'titan', 'ultratech', 'wipro', 'ongc',
    'coal india', 'ntpc', 'power grid', 'gail', 'hero', 'eicher', 'tvs'
]

def clean_query(query: str) -> str:
    """
    Clean and normalize a search query by removing punctuation, 
    extra whitespace, and converting to lowercase.
    """
    # Convert to lowercase
    query = query.lower()
    
    # Remove punctuation except for % and numbers with decimal points
    punctuation_to_remove = string.punctuation.replace('%', '').replace('.', '')
    translator = str.maketrans('', '', punctuation_to_remove)
    query = query.translate(translator)
    
    # Fix decimal points (ensure they're only in numbers)
    parts = query.split()
    cleaned_parts = []
    for part in parts:
        if '.' in part:
            try:
                # Check if it's a valid float number
                float(part)
                cleaned_parts.append(part)  # Keep as is
            except ValueError:
                # Not a valid number, remove periods
                cleaned_parts.append(part.replace('.', ' '))
        else:
            cleaned_parts.append(part)
    
    query = ' '.join(cleaned_parts)
    
    # Remove extra whitespace
    query = ' '.join(query.split())
    
    return query

def correct_fund_house_name(name: str) -> str:
    """
    Attempt to correct misspelled fund house names
    
    Args:
        name: Potential fund house name
        
    Returns:
        Corrected fund house name if a close match is found, otherwise original name
    """
    if not name:
        return name
    
    # Check for exact match first
    if name.lower() in [h.lower() for h in FUND_HOUSES]:
        return name
    
    # Find close matches
    matches = get_close_matches(name.lower(), [h.lower() for h in FUND_HOUSES], n=1, cutoff=0.7)
    
    if matches:
        # Return the correct case version from FUND_HOUSES
        index = [h.lower() for h in FUND_HOUSES].index(matches[0])
        return FUND_HOUSES[index]
    
    return name

def extract_fund_criteria(query: str) -> Dict[str, Any]:
    """
    Extract search criteria from the query
    (This is a simplified version - the rules.py module has more comprehensive logic)
    
    Args:
        query: User query
        
    Returns:
        Dictionary of extracted criteria
    """
    criteria = {}
    query_lower = query.lower()
    
    # Extract fund type (simplified)
    if 'tax' in query_lower or 'elss' in query_lower:
        criteria['category'] = 'ELSS'
    elif 'equity' in query_lower or 'stock' in query_lower:
        criteria['category'] = 'Equity'
    elif 'debt' in query_lower or 'bond' in query_lower:
        criteria['category'] = 'Debt'
    elif 'hybrid' in query_lower or 'balanced' in query_lower:
        criteria['category'] = 'Hybrid'
    elif 'index' in query_lower or 'nifty' in query_lower or 'sensex' in query_lower:
        criteria['category'] = 'Index'
    
    # Extract risk preference
    if 'high risk' in query_lower:
        criteria['risk'] = 'High'
    elif 'low risk' in query_lower:
        criteria['risk'] = 'Low'
    elif 'moderate risk' in query_lower or 'medium risk' in query_lower:
        criteria['risk'] = 'Moderate'
    
    # Extract returns expectations
    returns_pattern = r'(?:returns?|yield)(?:\s+)(?:above|>|greater than|more than)(?:\s+)(\d+(?:\.\d+)?)(?:\s*%)?' 
    returns_match = re.search(returns_pattern, query_lower)
    if returns_match:
        criteria['min_returns'] = float(returns_match.group(1))
    
    # Extract AUM expectations
    aum_pattern = r'aum(?:\s+)(?:above|>|greater than|more than)(?:\s+)(\d+(?:,\d+)*(?:\.\d+)?)(?:\s*)(cr|crore)?'
    aum_match = re.search(aum_pattern, query_lower)
    if aum_match:
        criteria['min_aum'] = float(aum_match.group(1).replace(',', ''))
    
    # Extract holdings information
    for stock in COMMON_STOCKS:
        if stock in query_lower and ('holding' in query_lower or 'invest' in query_lower):
            criteria.setdefault('holdings', []).append(stock)
    
    return criteria

def extract_metadata(query: str) -> Dict[str, Any]:
    """
    Extract metadata filters from a natural language query.
    
    Args:
        query: The user's search query
        
    Returns:
        Dictionary with metadata filters
    """
    metadata = {}
    
    # Extract returns requirements
    returns_patterns = [
        r'(\d+(?:\.\d+)?)%\s+(?:or\s+)?(?:more|higher|greater|above|minimum)(?:\s+returns)?',
        r'(?:returns|yield)(?:\s+of)?(?:\s+at\s+least)?\s+(\d+(?:\.\d+)?)%',
        r'(?:more|higher|greater|above|at\s+least)\s+than\s+(\d+(?:\.\d+)?)%\s+returns',
    ]
    
    for pattern in returns_patterns:
        match = re.search(pattern, query)
        if match:
            try:
                returns_value = float(match.group(1))
                metadata['returns_1yr'] = {'min': returns_value}
                break
            except (ValueError, IndexError):
                pass
    
    # Extract risk level
    risk_patterns = {
        'low': [r'low\s+risk', r'safe', r'conservative', r'minimal\s+risk'],
        'moderate': [r'moderate\s+risk', r'balanced\s+risk', r'medium\s+risk'],
        'high': [r'high\s+risk', r'aggressive', r'risky', r'high\s+volatility']
    }
    
    for risk_level, patterns in risk_patterns.items():
        for pattern in patterns:
            if re.search(pattern, query):
                metadata['risk_level'] = risk_level
                break
        if 'risk_level' in metadata:
            break
    
    # Extract fund category
    category_patterns = {
        'Equity - Large Cap': [r'large\s+cap', r'bluechip', r'blue\s+chip', r'large\s+company'],
        'Equity - Mid Cap': [r'mid\s+cap', r'medium\s+cap', r'midcap', r'mid-cap'],
        'Equity - Small Cap': [r'small\s+cap', r'smallcap', r'small-cap'],
        'Equity - ELSS': [r'elss', r'tax\s+sav(?:ing|er)', r'80c', r'tax\s+benefit'],
        'Equity - Sectoral': [r'sector(?:al)?', r'thematic', r'banking', r'technology', r'pharma', r'healthcare', r'tech'],
        'Debt - Short Duration': [r'short\s+term', r'short\s+duration', r'liquid'],
        'Debt - Corporate Bond': [r'corporate\s+bond', r'credit', r'company\s+debt'],
        'Hybrid': [r'hybrid', r'balanced', r'asset\s+allocation', r'multi\s+asset']
    }
    
    for category, patterns in category_patterns.items():
        for pattern in patterns:
            if re.search(pattern, query):
                metadata['category'] = category
                break
        if 'category' in metadata:
            break
    
    # Extract AUM (Assets Under Management)
    aum_patterns = [
        r'(?:aum|assets|size)\s+(?:of\s+)?(?:at\s+least\s+)?(\d+(?:\.\d+)?)\s*k?crores?',
        r'(\d+(?:\.\d+)?)\s*k?crores?\s+(?:or\s+)?(?:more|higher|greater|above|minimum)\s+(?:aum|assets|size)'
    ]
    
    for pattern in aum_patterns:
        match = re.search(pattern, query)
        if match:
            try:
                aum_value = float(match.group(1))
                # If 'k' is in the match, multiply by 1000
                if 'k' in match.group(0).lower():
                    aum_value *= 1000
                metadata['aum_crore'] = {'min': aum_value}
                break
            except (ValueError, IndexError):
                pass
    
    return metadata

def normalize_fund_name(name: str) -> str:
    """
    Normalize a fund name for better matching
    
    Args:
        name: Fund name
        
    Returns:
        Normalized fund name
    """
    if not name:
        return ""
    
    # Convert to lowercase
    name = name.lower()
    
    # Remove punctuation
    name = re.sub(r'[^\w\s]', ' ', name)
    
    # Remove extra spaces
    name = re.sub(r'\s+', ' ', name).strip()
    
    # Remove common suffixes
    name = re.sub(r'\b(direct|plan|growth|dividend|option)\b', '', name)
    
    return name.strip()

def calculate_match_score(query: str, fund_name: str) -> float:
    """
    Calculate a simple keyword match score between query and fund name
    
    Args:
        query: User query
        fund_name: Fund name
        
    Returns:
        Match score (0-1)
    """
    if not query or not fund_name:
        return 0.0
    
    # Normalize both strings
    query = normalize_fund_name(query)
    fund_name = normalize_fund_name(fund_name)
    
    # Split into words
    query_words = set(query.split())
    fund_words = set(fund_name.split())
    
    # Calculate Jaccard similarity
    intersection = len(query_words.intersection(fund_words))
    union = len(query_words.union(fund_words))
    
    # Avoid division by zero
    if union == 0:
        return 0.0
    
    return intersection / union

def format_currency(amount: float, currency: str = "₹") -> str:
    """
    Format a number as currency with appropriate suffixes (K, L, Cr).
    
    Args:
        amount: The amount to format
        currency: Currency symbol
        
    Returns:
        Formatted currency string
    """
    if amount >= 10000000:  # 1 crore = 10 million
        return f"{currency}{amount/10000000:.2f} Cr"
    elif amount >= 100000:  # 1 lakh = 100 thousand
        return f"{currency}{amount/100000:.2f} L"
    elif amount >= 1000:
        return f"{currency}{amount/1000:.2f} K"
    else:
        return f"{currency}{amount:.2f}"

def format_percentage(value: float) -> str:
    """
    Format a number as percentage.
    
    Args:
        value: The value to format
        
    Returns:
        Formatted percentage string
    """
    return f"{value:.2f}%" 