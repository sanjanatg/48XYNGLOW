import re
import numpy as np
from pathlib import Path

class RuleEngine:
    """
    Rule Engine for filtering mutual fund search results
    based on natural language queries and metadata criteria.
    """
    
    def __init__(self):
        """Initialize the rule engine with patterns and criteria."""
        # Define commonly used terms for categories
        self.category_terms = {
            'equity': ['equity', 'stock', 'share'],
            'debt': ['debt', 'bond', 'fixed income', 'income'],
            'hybrid': ['hybrid', 'balanced', 'asset allocation', 'equity hybrid', 'debt hybrid'],
            'elss': ['elss', 'tax saving', 'tax saver', 'tax relief', '80c'],
            'index': ['index', 'etf', 'exchange traded', 'nifty', 'sensex', 'passive'],
            'liquid': ['liquid', 'ultra short', 'overnight', 'money market'],
            'gilt': ['gilt', 'government', 'g-sec', 'gsec'],
            'international': ['international', 'global', 'overseas', 'foreign', 'world']
        }
        
        # Define terms for sectors
        self.sector_terms = {
            'technology': ['tech', 'technology', 'software', 'it', 'digital'],
            'healthcare': ['health', 'healthcare', 'pharma', 'pharmaceutical', 'medical'],
            'banking': ['bank', 'banking', 'financial', 'finance', 'nbfc'],
            'energy': ['energy', 'power', 'oil', 'gas', 'petroleum'],
            'infrastructure': ['infra', 'infrastructure', 'construction'],
            'consumer': ['consumer', 'fmcg', 'retail'],
            'automobile': ['auto', 'automobile', 'car']
        }
        
        # Define terms for risk profiles
        self.risk_terms = {
            'low': ['low risk', 'conservative', 'safe', 'stable'],
            'moderate': ['moderate risk', 'balanced', 'medium'],
            'high': ['high risk', 'aggressive', 'growth', 'risky']
        }
        
        # Define terms for fund houses
        self.fund_house_terms = {
            'icici': ['icici', 'icici pru', 'icici prudential'],
            'hdfc': ['hdfc'],
            'sbi': ['sbi', 'state bank'],
            'axis': ['axis'],
            'kotak': ['kotak'],
            'aditya birla': ['aditya', 'birla', 'aditya birla', 'absl'],
            'mirae': ['mirae'],
            'nippon': ['nippon', 'reliance'],
            'dsp': ['dsp'],
            'uti': ['uti'],
            'tata': ['tata'],
            'quant': ['quant'],
            'parag parikh': ['parag', 'parikh', 'ppfas'],
            'motilal oswal': ['motilal', 'oswal', 'mofsl'],
            'idfc': ['idfc']
        }
        
        # Performance-based patterns
        self.performance_patterns = {
            'high_returns': [
                r'high(?:\s+returns?|(?:\s+)yield)',
                r'best(?:\s+)returns?',
                r'top(?:\s+)performing',
                r'highest(?:\s+)returns?'
            ],
            'returns_above': [
                r'returns?(?:\s+)(?:more than|greater than|above|over|exceeding)(?:\s+)(\d+(?:\.\d+)?)(?:\s*%)',
                r'returns?(?:\s+)(?:>|≥)(?:\s*)(\d+(?:\.\d+)?)(?:\s*%)',
                r'(\d+(?:\.\d+)?)(?:\s*%)(?:\s+)(?:or more|or higher|and above|and higher|plus)(?:\s+)returns?'
            ],
            'returns_below': [
                r'returns?(?:\s+)(?:less than|lower than|below|under)(?:\s+)(\d+(?:\.\d+)?)(?:\s*%)',
                r'returns?(?:\s+)(?:<|≤)(?:\s*)(\d+(?:\.\d+)?)(?:\s*%)'
            ]
        }
        
        # AUM-based patterns
        self.aum_patterns = {
            'large_aum': [
                r'large(?:\s+)(?:aum|asset|fund size)',
                r'big(?:\s+)(?:aum|asset|fund size)'
            ],
            'aum_above': [
                r'aum(?:\s+)(?:more than|greater than|above|over|exceeding)(?:\s+)(\d+(?:,\d+)*(?:\.\d+)?)(?:\s*)(cr|crore|lakh|million|billion)',
                r'aum(?:\s+)(?:>|≥)(?:\s*)(\d+(?:,\d+)*(?:\.\d+)?)(?:\s*)(cr|crore|lakh|million|billion)',
                r'asset(?:\s+)(?:(?:under|size|more than|greater than|above))(?:\s+)(\d+(?:,\d+)*(?:\.\d+)?)(?:\s*)(cr|crore|lakh|million|billion)'
            ],
            'aum_below': [
                r'aum(?:\s+)(?:less than|lower than|below|under)(?:\s+)(\d+(?:,\d+)*(?:\.\d+)?)(?:\s*)(cr|crore|lakh|million|billion)',
                r'aum(?:\s+)(?:<|≤)(?:\s*)(\d+(?:,\d+)*(?:\.\d+)?)(?:\s*)(cr|crore|lakh|million|billion)'
            ]
        }
        
        # Expense ratio patterns
        self.expense_patterns = {
            'low_expense': [
                r'low(?:\s+)expense(?:\s+)ratio',
                r'lowest(?:\s+)expense(?:\s+)ratio',
                r'cheap(?:\s+)expense'
            ],
            'expense_below': [
                r'expense(?:\s+)(?:ratio)?(?:\s+)(?:less than|lower than|below|under)(?:\s+)(\d+(?:\.\d+)?)(?:\s*%)?',
                r'expense(?:\s+)(?:ratio)?(?:\s+)(?:<|≤)(?:\s*)(\d+(?:\.\d+)?)(?:\s*%)?'
            ]
        }
        
        # Holdings-based patterns
        self.holdings_patterns = {
            'has_holdings': [
                r'(?:with|containing|has|having|holds|holding)(?:\s+)(.*?)(?:\s+)(?:holdings?|stocks?|companies|exposure)',
                r'(?:investing in|invests in|exposure to)(?:\s+)(.*?)(?:\s+)(?:stocks?|shares|companies)',
                r'funds?(?:\s+)(?:with|holding|having)(?:\s+)(.*?)(?:\s+)(?:stocks?|shares|holding)'
            ]
        }
    
    def extract_filters(self, query):
        """
        Extract filters from the query for search engine filtering.
        This is a wrapper for the extract_criteria method to maintain
        compatibility with the Streamlit app.
        
        Args:
            query: The search query string
            
        Returns:
            Dictionary with extracted filters in a format compatible with SearchEngine
        """
        raw_criteria = self.extract_criteria(query)
        filters = {}
        
        # Convert criteria format to be compatible with SearchEngine's filter format
        if 'category' in raw_criteria:
            category = raw_criteria['category']
            # Map our internal categories to the ones in the dataset
            category_mapping = {
                'equity': 'Equity',
                'debt': 'Debt',
                'hybrid': 'Hybrid',
                'elss': 'Equity - ELSS',
                'index': 'Equity - Index'
            }
            if category in category_mapping:
                filters['category'] = category_mapping[category]
            else:
                filters['category'] = category.capitalize()
        
        if 'risk' in raw_criteria:
            risk = raw_criteria['risk']
            # Map to risk_level in the dataset
            risk_mapping = {
                'low': 'Low',
                'moderate': 'Moderate',
                'high': 'High'
            }
            if risk in risk_mapping:
                filters['risk_level'] = risk_mapping[risk]
        
        if 'min_returns' in raw_criteria:
            # Create a range filter for returns_1yr
            filters['returns_1yr'] = {'min': raw_criteria['min_returns']}
        
        if 'max_returns' in raw_criteria:
            # Add max to existing range filter or create new one
            if 'returns_1yr' in filters:
                filters['returns_1yr']['max'] = raw_criteria['max_returns']
            else:
                filters['returns_1yr'] = {'max': raw_criteria['max_returns']}
        
        if 'min_aum' in raw_criteria:
            # Create a range filter for aum_crore
            filters['aum_crore'] = {'min': raw_criteria['min_aum']}
        
        if 'max_aum' in raw_criteria:
            # Add max to existing range filter or create new one
            if 'aum_crore' in filters:
                filters['aum_crore']['max'] = raw_criteria['max_aum']
            else:
                filters['aum_crore'] = {'max': raw_criteria['max_aum']}
        
        if 'fund_house' in raw_criteria:
            # Map to amc in the dataset
            filters['amc'] = raw_criteria['fund_house'].upper()
        
        if 'holdings' in raw_criteria:
            # This will be handled separately by searching in the holdings text field
            holdings_list = raw_criteria['holdings']
            if isinstance(holdings_list, list) and holdings_list:
                filters['holdings'] = holdings_list
        
        return filters
    
    def extract_criteria(self, query):
        """
        Extract criteria from the query for rule-based filtering.
        
        Args:
            query: The search query string
            
        Returns:
            Dictionary with extracted criteria
        """
        criteria = {}
        
        # Convert query to lowercase for case-insensitive matching
        query_lower = query.lower()
        
        # Extract category
        category = self._extract_category(query_lower)
        if category:
            criteria['category'] = category
        
        # Extract sector
        sector = self._extract_sector(query_lower)
        if sector:
            criteria['sector'] = sector
        
        # Extract risk level
        risk = self._extract_risk(query_lower)
        if risk:
            criteria['risk'] = risk
        
        # Extract fund house
        fund_house = self._extract_fund_house(query_lower)
        if fund_house:
            criteria['fund_house'] = fund_house
        
        # Extract returns criteria
        returns_criteria = self._extract_returns_criteria(query_lower)
        if returns_criteria:
            criteria.update(returns_criteria)
        
        # Extract AUM criteria
        aum_criteria = self._extract_aum_criteria(query_lower)
        if aum_criteria:
            criteria.update(aum_criteria)
        
        # Extract expense ratio criteria
        expense_criteria = self._extract_expense_criteria(query_lower)
        if expense_criteria:
            criteria.update(expense_criteria)
        
        # Extract holdings criteria
        holdings_criteria = self._extract_holdings_criteria(query_lower)
        if holdings_criteria:
            criteria.update(holdings_criteria)
        
        return criteria
    
    def _extract_category(self, query):
        """Extract fund category from query."""
        for category, terms in self.category_terms.items():
            for term in terms:
                if re.search(r'\b{}\b'.format(re.escape(term)), query):
                    return category
        return None
    
    def _extract_sector(self, query):
        """Extract fund sector from query."""
        for sector, terms in self.sector_terms.items():
            for term in terms:
                if re.search(r'\b{}\b'.format(re.escape(term)), query):
                    return sector
        return None
    
    def _extract_risk(self, query):
        """Extract risk level from query."""
        for risk, terms in self.risk_terms.items():
            for term in terms:
                if term in query:
                    return risk
        return None
    
    def _extract_fund_house(self, query):
        """Extract fund house from query."""
        for house, terms in self.fund_house_terms.items():
            for term in terms:
                if re.search(r'\b{}\b'.format(re.escape(term)), query):
                    return house
        return None
    
    def _extract_returns_criteria(self, query):
        """Extract returns-related criteria from query."""
        criteria = {}
        
        # Check for high returns
        for pattern in self.performance_patterns['high_returns']:
            if re.search(pattern, query):
                criteria['min_returns'] = 15.0  # Assume high returns means >15%
                break
        
        # Check for returns above specific percentage
        for pattern in self.performance_patterns['returns_above']:
            match = re.search(pattern, query)
            if match:
                try:
                    criteria['min_returns'] = float(match.group(1))
                except (ValueError, IndexError):
                    pass
                break
        
        # Check for returns below specific percentage
        for pattern in self.performance_patterns['returns_below']:
            match = re.search(pattern, query)
            if match:
                try:
                    criteria['max_returns'] = float(match.group(1))
                except (ValueError, IndexError):
                    pass
                break
        
        return criteria
    
    def _extract_aum_criteria(self, query):
        """Extract AUM-related criteria from query."""
        criteria = {}
        
        # Check for large AUM
        for pattern in self.aum_patterns['large_aum']:
            if re.search(pattern, query):
                criteria['min_aum'] = 1000.0  # Assume large AUM means >1000 crore
                break
        
        # Check for AUM above specific value
        for pattern in self.aum_patterns['aum_above']:
            match = re.search(pattern, query)
            if match:
                try:
                    value = float(match.group(1).replace(',', ''))
                    unit = match.group(2).lower()
                    
                    # Convert to crore
                    if unit in ['lakh']:
                        value = value / 100  # 1 crore = 100 lakh
                    elif unit in ['million']:
                        value = value / 10  # Approx 1 crore = 10 million INR
                    elif unit in ['billion']:
                        value = value * 100  # Approx 1 billion INR = 100 crore
                    
                    criteria['min_aum'] = value
                except (ValueError, IndexError):
                    pass
                break
        
        # Check for AUM below specific value
        for pattern in self.aum_patterns['aum_below']:
            match = re.search(pattern, query)
            if match:
                try:
                    value = float(match.group(1).replace(',', ''))
                    unit = match.group(2).lower()
                    
                    # Convert to crore
                    if unit in ['lakh']:
                        value = value / 100
                    elif unit in ['million']:
                        value = value / 10
                    elif unit in ['billion']:
                        value = value * 100
                    
                    criteria['max_aum'] = value
                except (ValueError, IndexError):
                    pass
                break
        
        return criteria
    
    def _extract_expense_criteria(self, query):
        """Extract expense ratio-related criteria from query."""
        criteria = {}
        
        # Check for low expense ratio
        for pattern in self.expense_patterns['low_expense']:
            if re.search(pattern, query):
                criteria['max_expense'] = 0.75  # Assume low expense means <0.75%
                break
        
        # Check for expense ratio below specific percentage
        for pattern in self.expense_patterns['expense_below']:
            match = re.search(pattern, query)
            if match:
                try:
                    criteria['max_expense'] = float(match.group(1))
                except (ValueError, IndexError):
                    pass
                break
        
        return criteria
    
    def _extract_holdings_criteria(self, query):
        """Extract holdings-related criteria from query."""
        criteria = {}
        
        # Check for specific holdings
        for pattern in self.holdings_patterns['has_holdings']:
            match = re.search(pattern, query)
            if match:
                try:
                    holdings_text = match.group(1).strip()
                    # Extract company names - split by common separators
                    holdings = re.split(r',|\sand\s|\sor\s', holdings_text)
                    holdings = [h.strip() for h in holdings if h.strip()]
                    
                    if holdings:
                        criteria['holdings'] = holdings
                except (ValueError, IndexError):
                    pass
                break
        
        # Check for simple company mentions
        for company in ['hdfc', 'icici', 'tcs', 'reliance', 'infosys', 'sbi', 'adani', 'tata', 'bharti', 'bajaj', 'airtel']:
            holdings_pattern = rf'(?:with|holding|having|exposure to)(?:\s+){company}(?:\s+|$)'
            if re.search(holdings_pattern, query):
                criteria.setdefault('holdings', []).append(company)
        
        return criteria
    
    def filter_results(self, results, criteria):
        """
        Apply rule-based filtering to search results.
        
        Args:
            results: List of search results from SearchEngine
            criteria: Dictionary with filtering criteria
            
        Returns:
            Filtered list of results with match explanations
        """
        if not criteria or not results:
            # Return original results if no criteria or no results
            for result in results:
                # Convert the similarity score to match score on a 0-100% scale
                # (scaling from [-1, 1] range to 0-100%)
                score = result.get("similarity_score", 0)
                if score <= 1: # If in range [-1, 1]
                    score = (score + 1) * 50
                
                # Add match score and match reasons
                result["match_score"] = min(100, max(0, score))
                
                if "final_score" in result:
                    result["match_score"] = result["final_score"]
                    
                result["match_reasons"] = ["Matches your search query semantically"]
            
            return results
        
        filtered_results = []
        
        for result in results:
            metadata = result.get("metadata", {})
            match_reasons = []
            score_adjustments = []
            
            # Check if fund meets all criteria
            passes_criteria = True
            
            # Get the base score
            score = result.get("final_score", result.get("similarity_score", 0))
            if score <= 1: # If in range [-1, 1]
                score = (score + 1) * 50
                
            # Check holdings criteria (boost score for holdings match)
            if "holdings" in criteria and "holdings_match" in result and result["holdings_match"]:
                holdings_match_details = ", ".join(result.get("holdings_match_details", []))
                match_reasons.append(f"Has holdings in {holdings_match_details}")
                score_adjustments.append(1.3) # 30% boost
            
            # Check category
            if "category" in criteria and "category" in metadata:
                if criteria["category"].lower() in metadata["category"].lower():
                    match_reasons.append(f"Category: {metadata['category']}")
                    score_adjustments.append(1.2) # 20% boost
                else:
                    passes_criteria = False
            
            # Check sector
            if "sector" in criteria and "sector" in metadata:
                if criteria["sector"].lower() in str(metadata["sector"]).lower():
                    match_reasons.append(f"Sector: {metadata['sector']}")
                    score_adjustments.append(1.2)
                else:
                    passes_criteria = False
            
            # Check risk level
            if "risk" in criteria and "risk" in metadata:
                if criteria["risk"].lower() == metadata["risk"].lower():
                    match_reasons.append(f"Risk level: {metadata['risk']}")
                    score_adjustments.append(1.1)
                else:
                    passes_criteria = False
            
            # Check fund house
            if "fund_house" in criteria and "fund_house" in metadata:
                if criteria["fund_house"].lower() in metadata["fund_house"].lower():
                    match_reasons.append(f"Fund house: {metadata['fund_house']}")
                    score_adjustments.append(1.2)
                else:
                    passes_criteria = False
            
            # Check minimum returns
            if "min_returns" in criteria and "returns_1y" in metadata:
                returns = float(metadata["returns_1y"])
                if returns >= criteria["min_returns"]:
                    match_reasons.append(f"Returns: {returns}% (above {criteria['min_returns']}%)")
                    # Bonus boost for significantly higher returns
                    if returns > criteria["min_returns"] * 1.5:
                        score_adjustments.append(1.3)
                    else:
                        score_adjustments.append(1.1)
                else:
                    passes_criteria = False
            
            # Check maximum returns
            if "max_returns" in criteria and "returns_1y" in metadata:
                returns = float(metadata["returns_1y"])
                if returns <= criteria["max_returns"]:
                    match_reasons.append(f"Returns: {returns}% (below {criteria['max_returns']}%)")
                    score_adjustments.append(1.1)
                else:
                    passes_criteria = False
            
            # Check minimum AUM
            if "min_aum" in criteria and "aum" in metadata:
                aum = float(metadata["aum"])
                if aum >= criteria["min_aum"]:
                    match_reasons.append(f"AUM: ₹{aum:,.2f} Cr (above ₹{criteria['min_aum']:,.2f} Cr)")
                    score_adjustments.append(1.1)
                else:
                    passes_criteria = False
            
            # Check maximum AUM
            if "max_aum" in criteria and "aum" in metadata:
                aum = float(metadata["aum"])
                if aum <= criteria["max_aum"]:
                    match_reasons.append(f"AUM: ₹{aum:,.2f} Cr (below ₹{criteria['max_aum']:,.2f} Cr)")
                    score_adjustments.append(1.1)
                else:
                    passes_criteria = False
            
            # Check maximum expense ratio
            if "max_expense" in criteria and "expense_ratio" in metadata:
                expense = float(metadata["expense_ratio"])
                if expense <= criteria["max_expense"]:
                    match_reasons.append(f"Expense ratio: {expense}% (below {criteria['max_expense']}%)")
                    score_adjustments.append(1.1)
                else:
                    passes_criteria = False
            
            if passes_criteria:
                # Apply all score adjustments
                for adjustment in score_adjustments:
                    score *= adjustment
                
                # Cap score at 100%
                score = min(100, score)
                
                result["match_score"] = score
                result["match_reasons"] = match_reasons
                
                # Add at least one reason if none specified
                if not match_reasons:
                    result["match_reasons"] = ["Matches your search query semantically"]
                
                filtered_results.append(result)
        
        # Sort by match score
        filtered_results = sorted(filtered_results, key=lambda x: x["match_score"], reverse=True)
        
        return filtered_results 