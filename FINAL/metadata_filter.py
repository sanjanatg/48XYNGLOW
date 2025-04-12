import pandas as pd
import numpy as np
from query_parser import QueryParser

class MetadataFilter:
    def __init__(self):
        """Initialize metadata filter"""
        # Map text risk levels to numeric values
        self.risk_mapping = {
            "low risk": 1,
            "medium risk": 2,
            "moderate risk": 2,
            "high risk": 3,
            "very high risk": 4
        }
        
        # Define sector aliases for normalization
        self.sector_aliases = {
            "tech": "technology",
            "pharma": "pharmaceutical",
            "finance": "financial",
            "auto": "automobile"
        }
    
    def normalize_sector(self, sector):
        """Normalize sector name using aliases"""
        return self.sector_aliases.get(sector.lower(), sector.lower())
    
    def filter_by_risk(self, funds, risk_filters):
        """
        Filter funds by risk level
        
        Args:
            funds: list of fund dictionaries from previous steps
            risk_filters: list of risk levels from query
            
        Returns:
            filtered list of funds
        """
        if not risk_filters:
            return funds
            
        filtered_funds = []
        for fund in funds:
            # Skip if fund doesn't have risk_score
            if 'risk_score' not in fund:
                continue
                
            fund_risk = fund['risk_score']
            
            # Check if numeric risk score matches any requested risk level
            for risk in risk_filters:
                target_risk = self.risk_mapping.get(risk.lower(), 0)
                
                # Allow for some flexibility in matching
                if isinstance(fund_risk, (int, float)) and abs(fund_risk - target_risk) <= 1:
                    filtered_funds.append(fund)
                    break
                    
                # Handle text risk levels
                elif isinstance(fund_risk, str) and risk.lower() in fund_risk.lower():
                    filtered_funds.append(fund)
                    break
        
        return filtered_funds if filtered_funds else funds  # Return original list if all filtered out
    
    def filter_by_sector(self, funds, sector_filters):
        """
        Filter funds by sector
        
        Args:
            funds: list of fund dictionaries from previous steps
            sector_filters: list of sectors from query
            
        Returns:
            filtered list of funds
        """
        if not sector_filters:
            return funds
            
        # Normalize sector names
        normalized_sectors = [self.normalize_sector(s) for s in sector_filters]
        
        filtered_funds = []
        for fund in funds:
            # Skip if fund doesn't have sector
            if 'sector' not in fund and 'category' not in fund:
                continue
                
            # Check both sector and category fields
            fund_sector = fund.get('sector', '').lower()
            fund_category = fund.get('category', '').lower()
            
            for sector in normalized_sectors:
                if (sector in fund_sector) or (sector in fund_category):
                    filtered_funds.append(fund)
                    break
        
        return filtered_funds if filtered_funds else funds  # Return original list if all filtered out
    
    def filter_by_attributes(self, funds, attribute_filters):
        """
        Filter funds by numeric attributes (expense_ratio, returns, etc.)
        
        Args:
            funds: list of fund dictionaries from previous steps
            attribute_filters: dict of attributes with operators and values
            
        Returns:
            filtered list of funds
        """
        if not attribute_filters:
            return funds
            
        filtered_funds = []
        
        for fund in funds:
            include_fund = True
            
            for attr, filter_spec in attribute_filters.items():
                # Convert attribute name to fund data field
                field_name = attr
                if attr == 'expense_ratio':
                    field_name = 'expense_ratio'
                elif attr == 'returns':
                    # Check various return fields
                    field_name = [f for f in fund if 'return' in f]
                    if not field_name:
                        include_fund = False
                        break
                    # Use first available return field
                    field_name = field_name[0]
                
                # Skip if fund doesn't have this attribute
                if field_name not in fund:
                    include_fund = False
                    break
                    
                value = fund[field_name]
                if not isinstance(value, (int, float)):
                    # Try to convert to float
                    try:
                        value = float(value.replace('%', '').strip())
                    except (ValueError, AttributeError):
                        include_fund = False
                        break
                
                # Apply comparison based on operator
                operator = filter_spec['operator']
                target_value = filter_spec['value']
                
                if operator == '<' and value >= target_value:
                    include_fund = False
                    break
                elif operator == '>' and value <= target_value:
                    include_fund = False
                    break
                elif operator == '<=' and value > target_value:
                    include_fund = False
                    break
                elif operator == '>=' and value < target_value:
                    include_fund = False
                    break
            
            if include_fund:
                filtered_funds.append(fund)
        
        return filtered_funds if filtered_funds else funds  # Return original list if all filtered out
    
    def apply_filters(self, funds, filters):
        """
        Apply all filters to fund list
        
        Args:
            funds: list of fund dictionaries from previous steps
            filters: filter dictionary from query parser
            
        Returns:
            filtered list of funds
        """
        # Apply filters in sequence
        filtered_funds = self.filter_by_risk(funds, filters.get('risk', []))
        filtered_funds = self.filter_by_sector(filtered_funds, filters.get('sector', []))
        filtered_funds = self.filter_by_attributes(filtered_funds, filters.get('other_attributes', {}))
        
        return filtered_funds
    
    def fuzzy_match_name(self, funds, keywords, min_score=0.6):
        """
        Add fuzzy string matching score for fund name
        
        Args:
            funds: list of fund dictionaries
            keywords: list of keywords from query
            min_score: minimum score to consider a match
            
        Returns:
            funds with added fuzzy_name_score
        """
        if not keywords:
            return funds
            
        query_text = " ".join(keywords).lower()
        
        for fund in funds:
            if 'fund_name' not in fund:
                fund['fuzzy_name_score'] = 0
                continue
                
            fund_name = fund['fund_name'].lower()
            
            # Simple word overlap score
            words = query_text.split()
            matching_words = sum(1 for word in words if word in fund_name)
            score = matching_words / len(words) if words else 0
            
            fund['fuzzy_name_score'] = score
        
        return funds

# Example usage
if __name__ == "__main__":
    # Sample data
    sample_funds = [
        {
            'fund_name': 'HDFC Technology Fund',
            'sector': 'Technology',
            'risk_score': 3,
            'expense_ratio': 1.8,
            'returns_3yr': 12.5
        },
        {
            'fund_name': 'SBI Healthcare Fund',
            'sector': 'Pharmaceutical',
            'risk_score': 2,
            'expense_ratio': 0.9,
            'returns_3yr': 8.5
        },
        {
            'fund_name': 'ICICI Low Risk Bond Fund',
            'sector': 'Debt',
            'risk_score': 1,
            'expense_ratio': 0.5,
            'returns_3yr': 5.2
        }
    ]
    
    # Create filter
    metadata_filter = MetadataFilter()
    
    # Parse query
    parser = QueryParser()
    query_info = parser.process_query("I want a low risk tech fund with expense ratio less than 1%")
    
    # Apply filters
    filtered_funds = metadata_filter.apply_filters(sample_funds, query_info['filters'])
    
    print(f"Original: {len(sample_funds)} funds")
    print(f"After filtering: {len(filtered_funds)} funds")
    
    for fund in filtered_funds:
        print(f"{fund['fund_name']} - Risk: {fund['risk_score']}, Expense: {fund['expense_ratio']}%") 