import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

class QueryParser:
    def __init__(self):
        # Define known sectors for mutual funds
        self.sectors = [
            "technology", "tech", "healthcare", "pharma", "pharmaceutical", 
            "banking", "financial", "finance", "consumer", "retail", 
            "energy", "infrastructure", "manufacturing", "automobile", "auto",
            "real estate", "property", "debt", "bond", "equity", "large cap",
            "mid cap", "small cap", "multi cap", "index", "gold", "commodity"
        ]
        
        # Define risk levels
        self.risk_levels = ["low risk", "medium risk", "high risk", "moderate risk", "very high risk"]
        
        # Define other fund attributes
        self.attributes = ["expense ratio", "returns", "dividend", "growth", "performance", "aum", "nav"]
        
        # Initialize stopwords
        self.stop_words = set(stopwords.words('english'))
    
    def normalize_query(self, query):
        """Normalize query: lowercase, correct typos, etc."""
        # Convert to lowercase
        query = query.lower()
        
        # Basic spell correction for common terms
        # This is a simple implementation - could be enhanced with a proper spell checker
        corrections = {
            "tecnology": "technology", 
            "pharma": "pharmaceutical",
            "risky": "high risk",
            "safe": "low risk",
            "moderate": "medium risk"
        }
        
        for misspelled, correct in corrections.items():
            query = query.replace(misspelled, correct)
            
        return query
    
    def detect_filters(self, query):
        """Extract structured filters from the query"""
        filters = {
            "sector": [],
            "risk": [],
            "other_attributes": {}
        }
        
        # Extract sectors
        for sector in self.sectors:
            if sector in query:
                filters["sector"].append(sector)
        
        # Extract risk levels
        for risk in self.risk_levels:
            if risk in query:
                filters["risk"].append(risk)
                
        # Extract specific value filters like "expense ratio < 1%"
        expense_ratio_pattern = r"expense ratio\s*(<|>|<=|>=|less than|more than|below|above)\s*([\d.]+)(%|percent)?"
        match = re.search(expense_ratio_pattern, query)
        if match:
            operator = match.group(1)
            value = float(match.group(2))
            
            # Convert text operators to symbols
            if operator in ["less than", "below"]:
                operator = "<"
            elif operator in ["more than", "above"]:
                operator = ">"
                
            filters["other_attributes"]["expense_ratio"] = {
                "operator": operator,
                "value": value
            }
            
        # Extract returns filter like "returns > 10%"
        returns_pattern = r"returns\s*(<|>|<=|>=|less than|more than|below|above)\s*([\d.]+)(%|percent)?"
        match = re.search(returns_pattern, query)
        if match:
            operator = match.group(1)
            value = float(match.group(2))
            
            # Convert text operators to symbols
            if operator in ["less than", "below"]:
                operator = "<"
            elif operator in ["more than", "above"]:
                operator = ">"
                
            filters["other_attributes"]["returns"] = {
                "operator": operator,
                "value": value
            }
        
        return filters
    
    def extract_keywords(self, query):
        """Extract important keywords after removing stopwords"""
        word_tokens = word_tokenize(query)
        keywords = [word for word in word_tokens if word.isalnum() and word not in self.stop_words]
        return keywords
    
    def process_query(self, query):
        """Main function to process the query"""
        normalized_query = self.normalize_query(query)
        filters = self.detect_filters(normalized_query)
        keywords = self.extract_keywords(normalized_query)
        
        return {
            "original_query": query,
            "normalized_query": normalized_query,
            "filters": filters,
            "keywords": keywords
        }

# Example usage
if __name__ == "__main__":
    parser = QueryParser()
    test_query = "I want a low risk technology fund with expense ratio less than 1%"
    result = parser.process_query(test_query)
    print(result) 