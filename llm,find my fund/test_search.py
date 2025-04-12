from src.core.search_engine import SearchEngine
import sys

def run_search(query, top_k=5, search_type="hybrid"):
    # Initialize the search engine
    search_engine = SearchEngine(
        data_path="data/funds.csv",
        semantic_model="all-MiniLM-L6-v2",
        lexical_weight=0.4,
        semantic_weight=0.6
    )

    # Load pre-trained models instead of fitting from scratch
    search_engine.load_models(directory="models", data_path="models/processed_funds.csv")

    # Test search functionality
    results = search_engine.search(query, top_k=top_k, search_type=search_type)

    # Print the results
    print(f"Search results for query: '{query}'")
    print("-" * 50)
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['fund_name']} (Score: {result.get('combined_score', 0):.4f})")
        print(f"   Fund House: {result['fund_house']}")
        print(f"   Category: {result['category']} - {result['sub_category']}")
        print()
    
    return results

if __name__ == "__main__":
    # Get query from command line arguments or use default
    query = "SBI blue chip fund"
    if len(sys.argv) > 1:
        query = sys.argv[1]
    
    # Run search
    run_search(query) 