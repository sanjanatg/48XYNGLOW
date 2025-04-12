"""
Simple RAG (Retrieval-Augmented Generation) Script for Mutual Fund Advisor
This script demonstrates the RAG prompt engineering from Phase 6 in a simple format.
"""

import time
from search_engine import MutualFundSearchEngine
from llm_interface import LLMInterface
from enhanced_retrieval import EnhancedRetrieval

def run_simple_rag(query):
    """Run the RAG pipeline with a given query and print results"""
    print(f"\nQuery: {query}")
    print("-" * 50)
    
    # Initialize components
    print("Initializing components...")
    try:
        search_engine = MutualFundSearchEngine()
        llm = LLMInterface(verbose=False)
        enhanced_retrieval = EnhancedRetrieval()
    except Exception as e:
        print(f"Error initializing components: {str(e)}")
        return
    
    if not llm.is_model_loaded():
        print("Error: Model not loaded. Please download the model file.")
        print("=" * 50)
        print(llm.download_model_instructions())
        print("=" * 50)
        return
    
    # Search for relevant funds
    print("Searching for relevant funds...")
    try:
        search_results = search_engine.search(query, top_k=3)
    except Exception as e:
        print(f"Error during search: {str(e)}")
        return
    
    if not search_results:
        print("No relevant funds found. Please try a different query.")
        return
    
    # Print found funds
    print(f"Found {len(search_results)} relevant funds:")
    for i, result in enumerate(search_results, 1):
        fund_name = result['fund_data'].get('fund_name', 'Unknown Fund')
        print(f"  {i}. {fund_name}")
    
    # Generate RAG prompt
    print("Generating RAG prompt...")
    try:
        rag_prompt = enhanced_retrieval.generate_rag_prompt(query, search_results)
    except Exception as e:
        print(f"Error generating RAG prompt: {str(e)}")
        return
    
    # Send to LLM
    print("Generating LLM response...")
    try:
        start_time = time.time()
        generated_text, time_taken = llm.generate_rag_response(
            user_query=query,
            rag_prompt=rag_prompt,
            max_length=512
        )
        
        # Display response
        print("-" * 50)
        print("Response:")
        print(generated_text)
        print("-" * 50)
        print(f"Response time: {time_taken:.2f} seconds")
    except Exception as e:
        print(f"Error generating response: {str(e)}")
        return

def main():
    """Main entry point with demo queries"""
    print("Simple RAG Demo for Mutual Fund Advisor")
    print("======================================")
    
    # Sample queries to demonstrate
    sample_queries = [
        "Which fund is best for long-term retirement savings?",
        "I'm looking for a low-risk debt fund with good returns",
        "Recommend a tax-saving fund with high growth potential"
    ]
    
    print("Available demo queries:")
    for i, query in enumerate(sample_queries, 1):
        print(f"{i}. {query}")
    print("0. Enter your own query")
    
    # Get user choice
    choice = input("\nSelect a query (0-3) or press Enter to quit: ")
    
    if not choice:
        print("Goodbye!")
        return
    
    try:
        choice = int(choice)
        if choice == 0:
            custom_query = input("Enter your query: ")
            if custom_query.strip():
                run_simple_rag(custom_query)
        elif 1 <= choice <= len(sample_queries):
            run_simple_rag(sample_queries[choice-1])
        else:
            print("Invalid choice.")
    except ValueError:
        print("Please enter a number.")

if __name__ == "__main__":
    main() 