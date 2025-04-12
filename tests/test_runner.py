import json
import requests
import time
import os
import sys
from colorama import init, Fore, Style

# Initialize colorama for colored terminal output
init()

# Add parent directory to sys.path to import from FINAL
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from FINAL.fix_imports import add_project_root_to_path

# Define endpoints
API_URL = "http://localhost:5000/api/search"
HEALTH_URL = "http://localhost:5000/api/health"

def load_test_queries(file_path):
    """Load test queries from a JSON file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"{Fore.RED}Error: Test file {file_path} not found.{Style.RESET_ALL}")
        return []
    except json.JSONDecodeError:
        print(f"{Fore.RED}Error: Invalid JSON format in {file_path}.{Style.RESET_ALL}")
        return []

def check_api_health():
    """Check if the API server is running"""
    try:
        response = requests.get(HEALTH_URL, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "ok":
                print(f"{Fore.GREEN}✓ API server is running{Style.RESET_ALL}")
                ollama_status = data.get("ollama_available", False)
                if ollama_status:
                    print(f"{Fore.GREEN}✓ Ollama LLM is available{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}✗ Ollama LLM is not available. Please start Ollama with 'ollama serve'.{Style.RESET_ALL}")
                return True
        return False
    except requests.exceptions.RequestException:
        print(f"{Fore.RED}✗ API server is not running. Please start it with 'cd FINAL && python api_server.py'.{Style.RESET_ALL}")
        return False

def test_query(query, expected_fund=None, top_k=5):
    """Test a single query against the API"""
    print(f"\n{Fore.CYAN}Testing query:{Style.RESET_ALL} {query}")
    
    try:
        payload = {
            "query": query,
            "filters": {},
            "top_k": top_k
        }
        
        start_time = time.time()
        response = requests.post(API_URL, json=payload, timeout=60)
        elapsed_time = time.time() - start_time
        
        if response.status_code != 200:
            print(f"{Fore.RED}Error: API returned status code {response.status_code}{Style.RESET_ALL}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        
        if not data.get("success", False):
            print(f"{Fore.RED}Error: API request failed - {data.get('error', 'Unknown error')}{Style.RESET_ALL}")
            return False
        
        results = data.get("results", [])
        if not results:
            print(f"{Fore.YELLOW}Warning: No results returned for query.{Style.RESET_ALL}")
            return False
        
        # Display results
        top_fund = results[0] if results else None
        
        if top_fund:
            print(f"\n{Fore.GREEN}Top result:{Style.RESET_ALL}")
            print(f"  Name: {top_fund.get('name', 'N/A')}")
            print(f"  Category: {top_fund.get('category', 'N/A')}")
            print(f"  Risk: {top_fund.get('risk', 'N/A')}")
            
            if expected_fund:
                if expected_fund.lower() in top_fund.get('name', '').lower():
                    print(f"{Fore.GREEN}✓ Expected fund match: {expected_fund}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}✗ Expected fund '{expected_fund}' not matched!{Style.RESET_ALL}")
            
            # Print scores if available
            if 'scoreExplanation' in top_fund:
                print(f"\n{Fore.CYAN}Relevance scores:{Style.RESET_ALL}")
                scores = top_fund['scoreExplanation']
                print(f"  Semantic: {scores.get('semantic', 'N/A')}")
                print(f"  Metadata: {scores.get('metadata', 'N/A')}")
                print(f"  Fuzzy: {scores.get('fuzzy', 'N/A')}")
                print(f"  Final: {scores.get('final', 'N/A')}")
        
        # Print LLM response
        llm_response = data.get("llm_response", "")
        if llm_response:
            print(f"\n{Fore.CYAN}LLM analysis:{Style.RESET_ALL}")
            # Limit output to 300 characters for readability
            print(f"  {llm_response[:300]}..." if len(llm_response) > 300 else llm_response)
        
        print(f"\n{Fore.CYAN}Query time:{Style.RESET_ALL} {elapsed_time:.2f} seconds")
        return True
        
    except requests.exceptions.Timeout:
        print(f"{Fore.RED}Error: Request timed out after 60 seconds.{Style.RESET_ALL}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
        return False
    except Exception as e:
        print(f"{Fore.RED}Unexpected error: {str(e)}{Style.RESET_ALL}")
        return False

def run_tests_from_file(file_path, top_k=5):
    """Run all tests from a JSON file"""
    test_cases = load_test_queries(file_path)
    if not test_cases:
        return
    
    print(f"\n{Fore.CYAN}Running {len(test_cases)} test queries from {file_path}{Style.RESET_ALL}\n")
    
    # Track success rate
    successes = 0
    matches = 0
    total = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{Fore.CYAN}Test {i}/{total}{Style.RESET_ALL}")
        query = test_case.get("query", "")
        expected_fund = test_case.get("expected_fund")
        
        if not query:
            print(f"{Fore.YELLOW}Warning: Empty query in test case #{i}, skipping.{Style.RESET_ALL}")
            continue
        
        success = test_query(query, expected_fund, top_k)
        if success:
            successes += 1
        
        # If expected fund was provided and top result matches, count as a match
        if expected_fund and success and any(expected_fund.lower() in result.get('name', '').lower() 
                                           for result in requests.post(API_URL, 
                                                                      json={"query": query, "top_k": top_k}).json().get("results", [])[:1]):
            matches += 1
        
        # Add a separator between tests
        print("\n" + "-" * 80)
        
        # Optional: add a slight delay between tests to avoid overwhelming the API
        if i < total:
            time.sleep(1)
    
    # Print summary
    print(f"\n{Fore.CYAN}Test Summary:{Style.RESET_ALL}")
    print(f"  Total tests: {total}")
    print(f"  Successful API calls: {successes}/{total} ({successes/total*100:.0f}%)")
    
    if any(test.get("expected_fund") for test in test_cases):
        print(f"  Expected fund matches: {matches}/{sum(1 for test in test_cases if test.get('expected_fund'))} "
              f"({matches/sum(1 for test in test_cases if test.get('expected_fund'))*100:.0f}%)")

def run_manual_tests(top_k=5):
    """Run tests from manual input"""
    print(f"\n{Fore.CYAN}Manual Testing Mode{Style.RESET_ALL}")
    print("Enter queries one by one. Type 'exit' to quit.")
    
    query_num = 1
    while True:
        print(f"\n{Fore.CYAN}Query #{query_num}:{Style.RESET_ALL}")
        query = input("Enter query (or 'exit' to quit): ")
        
        if query.lower() == 'exit':
            break
        
        expected = input("Expected fund (optional, press Enter to skip): ")
        expected_fund = expected if expected else None
        
        test_query(query, expected_fund, top_k)
        query_num += 1

def main():
    """Main function to run tests"""
    print(f"{Fore.CYAN}==============================================={Style.RESET_ALL}")
    print(f"{Fore.CYAN}Find My Fund - Test Runner{Style.RESET_ALL}")
    print(f"{Fore.CYAN}==============================================={Style.RESET_ALL}")
    
    # Check if API is running before proceeding
    if not check_api_health():
        return
    
    # Get input parameters
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        top_k = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        run_tests_from_file(file_path, top_k)
    else:
        # No file provided, try default location or offer manual testing
        default_file = os.path.join(os.path.dirname(__file__), 'test_queries.json')
        
        if os.path.exists(default_file):
            print(f"\n{Fore.CYAN}Using default test file: {default_file}{Style.RESET_ALL}")
            top_k = 5
            run_tests_from_file(default_file, top_k)
        else:
            print(f"\n{Fore.YELLOW}No test file found or provided.{Style.RESET_ALL}")
            mode = input("Choose test mode (1: Manual input, 2: Exit): ")
            
            if mode == '1':
                run_manual_tests()
            else:
                print("Exiting test runner.")

if __name__ == "__main__":
    main() 