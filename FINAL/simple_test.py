import os
import pandas as pd
import time
from rag_ui_bridge import RAGUIBridge

def create_sample_data():
    """Create a sample fund dataset for testing"""
    # Check if sample data already exists
    if os.path.exists("sample_funds.csv"):
        print("Sample data already exists.")
        return
        
    print("Creating sample fund data...")
    
    # Create sample fund data
    funds = [
        {
            'fund_name': 'HDFC Technology Fund',
            'description': 'HDFC Technology Fund invests in technology companies focusing on innovation and growth. The fund primarily targets software, hardware, and tech service companies with strong growth potential.',
            'sector': 'Technology',
            'category': 'Equity: Sectoral - Technology',
            'risk_score': 3,
            'expense_ratio': 1.8,
            'returns_1yr': 8.5,
            'returns_3yr': 12.5,
            'returns_5yr': 15.2
        },
        {
            'fund_name': 'SBI Technology Opportunities Fund',
            'description': 'SBI Technology Opportunities Fund aims to provide long term capital appreciation by investing in technology companies. It focuses on companies that benefit from the development, advancement, and use of technology.',
            'sector': 'Technology',
            'category': 'Equity: Sectoral - Technology',
            'risk_score': 3,
            'expense_ratio': 1.65,
            'returns_1yr': 7.9,
            'returns_3yr': 11.8,
            'returns_5yr': 14.3
        },
        {
            'fund_name': 'ICICI Prudential Technology Fund',
            'description': 'ICICI Prudential Technology Fund invests in stocks of technology and technology-related companies including software, hardware, tech services and telecommunications.',
            'sector': 'Technology',
            'category': 'Equity: Sectoral - Technology',
            'risk_score': 3,
            'expense_ratio': 1.72,
            'returns_1yr': 8.2,
            'returns_3yr': 12.1,
            'returns_5yr': 14.8
        },
        {
            'fund_name': 'Axis Technology ETF',
            'description': 'Axis Technology ETF tracks a technology-focused index and provides exposure to top technology companies. It offers a low-cost way to invest in the technology sector.',
            'sector': 'Technology',
            'category': 'Equity: ETF - Sectoral',
            'risk_score': 2,
            'expense_ratio': 0.85,
            'returns_1yr': 6.8,
            'returns_3yr': 10.5,
            'returns_5yr': 13.2
        },
        {
            'fund_name': 'SBI Healthcare Fund',
            'description': 'SBI Healthcare Fund focuses on pharmaceutical and healthcare sector companies for long-term growth. It invests in pharma, hospitals, medical devices, and healthcare service providers.',
            'sector': 'Healthcare',
            'category': 'Equity: Sectoral - Healthcare',
            'risk_score': 2,
            'expense_ratio': 1.2,
            'returns_1yr': 5.6,
            'returns_3yr': 10.2,
            'returns_5yr': 12.1
        },
        {
            'fund_name': 'ICICI Low Risk Bond Fund',
            'description': 'ICICI Low Risk Bond Fund is a debt fund with a conservative approach for stable returns. It invests in high-quality corporate and government bonds with low credit risk.',
            'sector': 'Debt',
            'category': 'Debt: Low Duration',
            'risk_score': 1,
            'expense_ratio': 0.5,
            'returns_1yr': 3.8,
            'returns_3yr': 5.5,
            'returns_5yr': 6.2
        },
        {
            'fund_name': 'HDFC Low Duration Fund',
            'description': 'HDFC Low Duration Fund aims to generate income through investments in low duration debt securities and money market instruments. It maintains a low risk profile with high liquidity.',
            'sector': 'Debt',
            'category': 'Debt: Low Duration',
            'risk_score': 1,
            'expense_ratio': 0.45,
            'returns_1yr': 3.5,
            'returns_3yr': 5.2,
            'returns_5yr': 5.9
        },
        {
            'fund_name': 'Axis Banking & PSU Debt Fund',
            'description': 'Axis Banking & PSU Debt Fund invests in debt instruments of banks, Public Sector Undertakings, and Public Financial Institutions. It aims to provide reasonable returns with low risk.',
            'sector': 'Debt',
            'category': 'Debt: Banking and PSU',
            'risk_score': 1,
            'expense_ratio': 0.35,
            'returns_1yr': 3.2,
            'returns_3yr': 4.8,
            'returns_5yr': 5.5
        },
        {
            'fund_name': 'SBI Equity Hybrid Fund',
            'description': 'SBI Equity Hybrid Fund invests in a mix of equity and debt instruments to provide both growth and regular income. The balanced approach aims to reduce volatility while capturing market upside.',
            'sector': 'Hybrid',
            'category': 'Hybrid: Equity-oriented',
            'risk_score': 2,
            'expense_ratio': 1.1,
            'returns_1yr': 6.2,
            'returns_3yr': 9.5,
            'returns_5yr': 11.3
        },
        {
            'fund_name': 'HDFC Mid-Cap Opportunities Fund',
            'description': 'HDFC Mid-Cap Opportunities Fund focuses on mid-sized companies with potential for becoming large-caps in the future. It aims for capital appreciation over long term through identifying future market leaders.',
            'sector': 'Equity',
            'category': 'Equity: Mid Cap',
            'risk_score': 3,
            'expense_ratio': 1.45,
            'returns_1yr': 7.5,
            'returns_3yr': 11.2,
            'returns_5yr': 13.5
        }
    ]
    
    # Convert to DataFrame and save
    df = pd.DataFrame(funds)
    df.to_csv("sample_funds.csv", index=False)
    print(f"Created sample dataset with {len(df)} funds.")
    return df

def run_test_queries():
    """Run some test queries to demonstrate the system"""
    bridge = RAGUIBridge("sample_funds.csv", model_name="mistral")
    
    # List of test queries
    test_queries = [
        "I want a low risk debt fund with low expense ratio",
        "Suggest a technology fund with good long-term returns",
        "Which healthcare funds have moderate risk?", 
        "I need a mid-cap fund with returns above 10% for 3 years",
        "What are the best low risk options for conservative investors?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n\n===== Test Query {i}: '{query}' =====\n")
        
        # Process query
        start_time = time.time()
        results = bridge.process_query(query)
        elapsed = time.time() - start_time
        
        # Print results
        print(f"Query processed in {elapsed:.2f} seconds")
        print("\nTop matching funds:")
        for j, fund in enumerate(results.get("ranked_funds", []), 1):
            fund_name = fund.get('fund_name', 'Unknown')
            risk = fund.get('risk_score', 'N/A')
            expense = fund.get('expense_ratio', 'N/A')
            
            # Get returns
            returns = []
            for key, value in fund.items():
                if 'return' in key.lower():
                    returns.append(f"{key}: {value}")
            returns_str = ", ".join(returns) if returns else "N/A"
            
            print(f"{j}. {fund_name} - Risk: {risk}, Expense: {expense}, Returns: {returns_str}")
            
        print("\nLLM Response:")
        print(results["llm_response"])
        
        # Add a separator
        print("\n" + "="*80)
        
        # Short pause between queries
        time.sleep(1)

if __name__ == "__main__":
    # Create sample data if needed
    create_sample_data()
    
    # Run test queries
    print("\nRunning test queries to demonstrate the system...")
    run_test_queries() 