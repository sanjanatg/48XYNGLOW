import json

class RAGPromptGenerator:
    def __init__(self):
        """Initialize RAG prompt generator"""
        # Define prompt templates
        self.system_template = """You are a helpful fund advisor assistant that helps users find mutual funds that match their criteria.
Your responses should be accurate, informative, and based only on the fund data provided below.
If you're not sure about something, say so rather than making up information.
Keep your answers concise and focused on helping the user find the right fund."""
        
        self.user_template = """I'm looking for: {query}

Here are the top funds that match your criteria, in order of relevance:

{fund_context}

Based on this information, please recommend the most suitable fund(s) for me and explain why.
Include key details like risk level, returns, expense ratio, and why these are good matches for my query.
If none of these funds match my criteria well, please say so and explain why."""

    def format_fund_data(self, fund, rank):
        """
        Format a single fund's data for inclusion in the prompt
        
        Args:
            fund: dictionary with fund details
            rank: ranking of this fund in the results
            
        Returns:
            formatted string with fund details
        """
        # Extract key fund details
        fund_name = fund.get('fund_name', 'Unknown Fund')
        fund_type = fund.get('category', fund.get('fund_type', 'N/A'))
        risk_score = fund.get('risk_score', 'N/A')
        expense_ratio = fund.get('expense_ratio', 'N/A')
        
        # Extract returns data - check common field patterns
        returns_data = []
        for key, value in fund.items():
            if 'return' in key.lower() or 'performance' in key.lower():
                if isinstance(value, (int, float)):
                    returns_data.append(f"{key}: {value}%")
                else:
                    returns_data.append(f"{key}: {value}")
        
        returns_str = ", ".join(returns_data) if returns_data else "Returns: N/A"
        
        # Format detailed description
        description = fund.get('description', '')
        if not description and 'summary' in fund:
            description = fund['summary']
        
        # Format the fund data
        fund_str = f"Fund #{rank}: {fund_name}\n"
        fund_str += f"Type: {fund_type}\n"
        fund_str += f"Risk Level: {risk_score}\n"
        fund_str += f"Expense Ratio: {expense_ratio}\n"
        fund_str += f"{returns_str}\n"
        
        if description:
            fund_str += f"Description: {description}\n"
            
        return fund_str
    
    def generate_prompt(self, query, ranked_funds, top_k=5):
        """
        Generate RAG prompt with query and top fund details
        
        Args:
            query: original user query
            ranked_funds: list of funds ranked by relevance
            top_k: number of funds to include in prompt
            
        Returns:
            dict with system and user prompts ready for LLM
        """
        # Format context with top funds
        fund_context = ""
        for i, fund in enumerate(ranked_funds[:top_k], 1):
            fund_context += self.format_fund_data(fund, i) + "\n"
            
        # Fill templates
        user_prompt = self.user_template.format(
            query=query,
            fund_context=fund_context
        )
        
        return {
            "system": self.system_template,
            "user": user_prompt
        }
    
    def generate_json_prompt(self, query, ranked_funds, top_k=5):
        """
        Generate RAG prompt in JSON format for model APIs
        
        Args:
            query: original user query
            ranked_funds: list of funds ranked by relevance
            top_k: number of funds to include in prompt
            
        Returns:
            JSON formatted prompt for API calls
        """
        prompt_dict = self.generate_prompt(query, ranked_funds, top_k)
        
        # Convert to messages format for APIs
        messages = [
            {"role": "system", "content": prompt_dict["system"]},
            {"role": "user", "content": prompt_dict["user"]}
        ]
        
        return json.dumps({"messages": messages}, indent=2)

# Example usage
if __name__ == "__main__":
    # Sample ranked funds
    sample_funds = [
        {
            'fund_name': 'HDFC Technology Fund',
            'category': 'Equity: Sectoral - Technology',
            'risk_score': 'High',
            'expense_ratio': '1.8%',
            'returns_3yr': 12.5,
            'returns_5yr': 15.2,
            'description': 'HDFC Technology Fund is an open-ended equity scheme investing in technology and technology related sectors.'
        },
        {
            'fund_name': 'SBI Technology Opportunities Fund',
            'category': 'Equity: Sectoral - Technology',
            'risk_score': 'High',
            'expense_ratio': '1.65%',
            'returns_3yr': 11.8,
            'returns_5yr': 14.3,
            'description': 'SBI Technology Opportunities Fund aims to provide long term capital appreciation by investing in technology companies.'
        }
    ]
    
    # Create prompt generator
    prompt_gen = RAGPromptGenerator()
    
    # Generate prompt
    prompt = prompt_gen.generate_prompt("I want a technology fund with good long-term returns", sample_funds, top_k=2)
    
    # Print prompt
    print("System prompt:")
    print(prompt["system"])
    print("\nUser prompt:")
    print(prompt["user"]) 