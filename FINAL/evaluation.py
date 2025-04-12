import os
import json
import pandas as pd
import numpy as np
import logging
from tqdm import tqdm
import matplotlib.pyplot as plt
from tabulate import tabulate
from collections import defaultdict

# Import components from previous phases
import utils
from data_preprocessing import preprocess_data, generate_fund_descriptions
from embedding_indexing import load_or_create_embeddings, create_faiss_index
from search_engine import SearchEngine
from query_parser import QueryParser
from enhanced_retrieval import EnhancedRetrieval
from llm_interface import LLMInterface

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SystemEvaluator:
    """
    Comprehensive evaluator for the mutual fund recommendation system.
    Tests various aspects of the system including search accuracy, query parsing,
    and result relevance.
    """
    
    def __init__(self, search_engine=None, query_parser=None, retrieval=None, llm=None):
        """Initialize the evaluator with system components or create them"""
        logger.info("Initializing System Evaluator")
        
        # Initialize components if not provided
        if search_engine is None:
            logger.info("Initializing SearchEngine")
            self.search_engine = SearchEngine()
        else:
            self.search_engine = search_engine
            
        if query_parser is None:
            logger.info("Initializing QueryParser")
            self.query_parser = QueryParser()
        else:
            self.query_parser = query_parser
            
        if retrieval is None:
            logger.info("Initializing EnhancedRetrieval")
            self.retrieval = EnhancedRetrieval()
        else:
            self.retrieval = retrieval
            
        if llm is None:
            logger.info("Initializing LLMInterface")
            self.llm = LLMInterface()
        else:
            self.llm = llm
            
        # Load ground truth data for evaluation
        self.load_ground_truth()
        
        # Create test cases
        self.create_test_cases()
    
    def load_ground_truth(self):
        """Load ground truth data for evaluation"""
        logger.info("Loading ground truth data")
        
        try:
            # Load the full fund data for reference
            output_paths = utils.get_output_paths()
            self.fund_data = pd.read_json(output_paths["PREPROCESSED_FUNDS_PATH"])
            logger.info(f"Loaded {len(self.fund_data)} funds as ground truth")
        except Exception as e:
            logger.error(f"Error loading ground truth data: {str(e)}")
            self.fund_data = pd.DataFrame()
            
    def create_test_cases(self):
        """Create test cases for evaluation"""
        logger.info("Creating test cases")
        
        # 1. Fuzzy fund name test cases
        self.fuzzy_name_tests = [
            {
                "query": "hdfc top 100",
                "expected_fund_id": "hdfc_top_100_direct_growth",
                "description": "Abbreviated fund name"
            },
            {
                "query": "sbi blue chip",
                "expected_fund_id": "sbi_bluechip_direct_growth",
                "description": "Slightly misspelled fund name"
            },
            {
                "query": "axis midcap fund",
                "expected_fund_id": "axis_midcap_direct_growth",
                "description": "Brand name misspelled (axIs vs axIs)"
            },
            {
                "query": "icici pru technology",
                "expected_fund_id": "icici_prudential_technology_direct_growth",
                "description": "Abbreviated AMC name"
            },
            {
                "query": "kotak emerging equity",
                "expected_fund_id": "kotak_emerging_equity_direct_growth",
                "description": "Partial fund name"
            }
        ]
        
        # 2. Slang/common terms test cases
        self.slang_tests = [
            {
                "query": "tax saver fund",
                "expected_category": "ELSS",
                "description": "Tax saver slang for ELSS funds"
            },
            {
                "query": "liquid funds for emergency",
                "expected_category": "Liquid",
                "description": "Emergency fund for liquid funds"
            },
            {
                "query": "mutual fund for retirement",
                "expected_category": "Hybrid|Long Duration",
                "description": "Retirement planning term" 
            },
            {
                "query": "SIPs for wealth creation",
                "expected_category": "Equity|Multi Cap",
                "description": "SIP and wealth creation terms"
            },
            {
                "query": "blue chip companies fund",
                "expected_category": "Large Cap",
                "description": "Blue chip slang for large cap"
            }
        ]
        
        # 3. Filter logic test cases
        self.filter_tests = [
            {
                "query": "high return and low risk funds",
                "expected_filters": {"min_return_1yr": 10, "risk_level": "Low|Moderately Low"},
                "description": "High return AND low risk"
            },
            {
                "query": "debt funds with expense ratio less than 1%",
                "expected_filters": {"category": "Debt", "max_expense_ratio": 1.0},
                "description": "Category AND expense ratio filter"
            },
            {
                "query": "HDFC mutual funds in banking sector",
                "expected_filters": {"amc": "HDFC", "sector": "Banking|Financial"},
                "description": "AMC AND sector filter"
            },
            {
                "query": "low volatility funds with 3 year returns above 15%",
                "expected_filters": {"risk_level": "Low|Moderately Low", "min_return_3yr": 15},
                "description": "Risk level AND 3yr return filter"
            },
            {
                "query": "equity funds from top AMCs with expense ratio under 0.8%",
                "expected_filters": {"category": "Equity", "max_expense_ratio": 0.8},
                "description": "Category AND expense ratio filter"
            }
        ]
        
        logger.info(f"Created {len(self.fuzzy_name_tests)} fuzzy name test cases")
        logger.info(f"Created {len(self.slang_tests)} slang test cases")
        logger.info(f"Created {len(self.filter_tests)} filter logic test cases")
    
    def evaluate_fuzzy_name_searches(self):
        """Evaluate fuzzy fund name search accuracy"""
        logger.info("Evaluating fuzzy fund name searches")
        
        results = []
        correct = 0
        
        for test in tqdm(self.fuzzy_name_tests, desc="Testing fuzzy name searches"):
            query = test["query"]
            expected_fund_id = test["expected_fund_id"]
            
            # Run the search
            try:
                search_results = self.search_engine.search(query, top_k=5)
                
                # Check if expected fund is in top results
                found = False
                found_rank = None
                for i, result in enumerate(search_results):
                    if result.get("fund_id") == expected_fund_id:
                        found = True
                        found_rank = i + 1
                        if i == 0:  # Top result is correct
                            correct += 1
                        break
                
                # Record results
                results.append({
                    "query": query,
                    "expected_fund_id": expected_fund_id,
                    "description": test["description"],
                    "found": found,
                    "rank": found_rank,
                    "top_result": search_results[0].get("fund_id") if search_results else None
                })
                
            except Exception as e:
                logger.error(f"Error evaluating fuzzy search '{query}': {str(e)}")
                results.append({
                    "query": query,
                    "expected_fund_id": expected_fund_id,
                    "description": test["description"],
                    "found": False,
                    "rank": None,
                    "top_result": None,
                    "error": str(e)
                })
        
        # Calculate accuracy
        accuracy = (correct / len(self.fuzzy_name_tests)) * 100 if self.fuzzy_name_tests else 0
        logger.info(f"Fuzzy search accuracy: {accuracy:.1f}% ({correct}/{len(self.fuzzy_name_tests)})")
        
        return {
            "accuracy": accuracy,
            "results": results
        }
    
    def evaluate_slang_searches(self):
        """Evaluate slang/common terms search accuracy"""
        logger.info("Evaluating slang/common terms searches")
        
        results = []
        correct = 0
        
        for test in tqdm(self.slang_tests, desc="Testing slang searches"):
            query = test["query"]
            expected_categories = test["expected_category"].split("|")
            
            # Run the search
            try:
                search_results = self.search_engine.search(query, top_k=5)
                
                # Check if top result is in expected category
                found = False
                for result in search_results[:1]:  # Check only top result
                    fund_data = result.get("fund_data", {})
                    category = fund_data.get("category", "")
                    for expected in expected_categories:
                        if expected.lower() in category.lower():
                            found = True
                            correct += 1
                            break
                    if found:
                        break
                
                # Record results
                results.append({
                    "query": query,
                    "expected_category": test["expected_category"],
                    "description": test["description"],
                    "found": found,
                    "top_result_category": search_results[0].get("fund_data", {}).get("category", "") if search_results else None
                })
                
            except Exception as e:
                logger.error(f"Error evaluating slang search '{query}': {str(e)}")
                results.append({
                    "query": query,
                    "expected_category": test["expected_category"],
                    "description": test["description"],
                    "found": False,
                    "top_result_category": None,
                    "error": str(e)
                })
        
        # Calculate accuracy
        accuracy = (correct / len(self.slang_tests)) * 100 if self.slang_tests else 0
        logger.info(f"Slang search accuracy: {accuracy:.1f}% ({correct}/{len(self.slang_tests)})")
        
        return {
            "accuracy": accuracy,
            "results": results
        }
    
    def evaluate_filter_logic(self):
        """Evaluate filter logic extraction and application"""
        logger.info("Evaluating filter logic")
        
        results = []
        correct = 0
        
        for test in tqdm(self.filter_tests, desc="Testing filter logic"):
            query = test["query"]
            expected_filters = test["expected_filters"]
            
            # Parse query to extract filters
            try:
                parsed = self.query_parser.parse_query(query)
                extracted_filters = parsed.get("filters", {})
                
                # Check if extracted filters match expected filters
                matches = 0
                total_expected = len(expected_filters)
                
                # Check each expected filter
                for key, expected_value in expected_filters.items():
                    if key in extracted_filters:
                        # For string values that allow multiple options (separated by |)
                        if isinstance(expected_value, str) and "|" in expected_value:
                            options = expected_value.split("|")
                            extracted_value = extracted_filters[key]
                            if any(opt.lower() in str(extracted_value).lower() for opt in options):
                                matches += 1
                        # For numeric values, allow some tolerance
                        elif isinstance(expected_value, (int, float)):
                            extracted_value = extracted_filters.get(key, 0)
                            # Allow 20% tolerance for numeric values
                            if abs(extracted_value - expected_value) <= 0.2 * expected_value:
                                matches += 1
                        # For exact matches
                        elif extracted_filters[key] == expected_value:
                            matches += 1
                
                # Calculate match percentage
                match_pct = (matches / total_expected) * 100 if total_expected > 0 else 0
                
                # Consider it correct if at least 70% of filters matched
                if match_pct >= 70:
                    correct += 1
                
                # Record results
                results.append({
                    "query": query,
                    "expected_filters": expected_filters,
                    "extracted_filters": extracted_filters,
                    "description": test["description"],
                    "match_percentage": match_pct,
                    "correct": match_pct >= 70
                })
                
            except Exception as e:
                logger.error(f"Error evaluating filter logic '{query}': {str(e)}")
                results.append({
                    "query": query,
                    "expected_filters": expected_filters,
                    "extracted_filters": {},
                    "description": test["description"],
                    "match_percentage": 0,
                    "correct": False,
                    "error": str(e)
                })
        
        # Calculate accuracy
        accuracy = (correct / len(self.filter_tests)) * 100 if self.filter_tests else 0
        logger.info(f"Filter logic accuracy: {accuracy:.1f}% ({correct}/{len(self.filter_tests)})")
        
        return {
            "accuracy": accuracy,
            "results": results
        }
    
    def evaluate_end_to_end(self, test_queries=None):
        """Evaluate the complete system with end-to-end test queries"""
        logger.info("Running end-to-end evaluation")
        
        if test_queries is None:
            # Use a mix of queries from different test categories
            test_queries = [
                self.fuzzy_name_tests[0]["query"],
                self.slang_tests[0]["query"],
                self.filter_tests[0]["query"],
                "HDFC funds with high returns and low expense ratio",
                "Best tax saving funds for long term"
            ]
        
        results = []
        
        for query in tqdm(test_queries, desc="Testing end-to-end"):
            try:
                # 1. Parse the query
                parsed_query = self.query_parser.parse_query(query)
                
                # 2. Search for funds
                search_results = self.search_engine.search(
                    query, 
                    filters=parsed_query.get("filters", {}),
                    top_k=5
                )
                
                # 3. Apply enhanced retrieval scoring
                enhanced_results = self.retrieval.compute_final_scores(
                    search_results, 
                    query, 
                    parsed_query.get("filters", {})
                )
                
                # 4. Generate RAG prompt
                prompt = self.retrieval.generate_rag_prompt(query, enhanced_results[:3])
                
                # 5. Get LLM response
                llm_response = self.llm.generate_response(prompt)
                
                # Record results
                results.append({
                    "query": query,
                    "parsed_query": parsed_query,
                    "top_results": [r.get("fund_id", "unknown") for r in enhanced_results[:3]],
                    "top_result_scores": [r.get("final_score", 0) for r in enhanced_results[:3]],
                    "llm_response": llm_response
                })
                
            except Exception as e:
                logger.error(f"Error in end-to-end evaluation for '{query}': {str(e)}")
                results.append({
                    "query": query,
                    "error": str(e)
                })
        
        logger.info(f"Completed end-to-end evaluation for {len(test_queries)} queries")
        return results
    
    def run_complete_evaluation(self):
        """Run a complete evaluation of all components"""
        logger.info("Starting complete system evaluation")
        
        evaluation_results = {
            "fuzzy_name_tests": self.evaluate_fuzzy_name_searches(),
            "slang_tests": self.evaluate_slang_searches(),
            "filter_tests": self.evaluate_filter_logic(),
            "end_to_end_tests": self.evaluate_end_to_end()
        }
        
        # Calculate overall scores
        overall_accuracy = (
            evaluation_results["fuzzy_name_tests"]["accuracy"] +
            evaluation_results["slang_tests"]["accuracy"] +
            evaluation_results["filter_tests"]["accuracy"]
        ) / 3
        
        evaluation_results["overall_accuracy"] = overall_accuracy
        
        logger.info(f"Overall system accuracy: {overall_accuracy:.1f}%")
        
        return evaluation_results
    
    def generate_evaluation_report(self, eval_results=None):
        """Generate a detailed evaluation report"""
        if eval_results is None:
            eval_results = self.run_complete_evaluation()
            
        # Create a report structure
        report = {
            "summary": {
                "overall_accuracy": eval_results["overall_accuracy"],
                "fuzzy_name_accuracy": eval_results["fuzzy_name_tests"]["accuracy"],
                "slang_accuracy": eval_results["slang_tests"]["accuracy"],
                "filter_logic_accuracy": eval_results["filter_tests"]["accuracy"]
            },
            "detailed_results": eval_results
        }
        
        # Save results to a JSON file
        output_dir = utils.PROCESSED_DIR
        os.makedirs(output_dir, exist_ok=True)
        report_path = os.path.join(output_dir, "evaluation_report.json")
        
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
            
        logger.info(f"Evaluation report saved to {report_path}")
        
        # Print summary table
        summary_table = [
            ["Metric", "Accuracy"],
            ["Overall Accuracy", f"{report['summary']['overall_accuracy']:.1f}%"],
            ["Fuzzy Fund Name Search", f"{report['summary']['fuzzy_name_accuracy']:.1f}%"],
            ["Slang & Common Terms", f"{report['summary']['slang_accuracy']:.1f}%"],
            ["Filter Logic", f"{report['summary']['filter_logic_accuracy']:.1f}%"]
        ]
        
        print("\n" + tabulate(summary_table, headers="firstrow", tablefmt="fancy_grid"))
        
        # Generate visualization
        self.generate_evaluation_visualization(report)
        
        return report
        
    def generate_evaluation_visualization(self, report):
        """Generate visualizations of evaluation results"""
        try:
            # Create bar chart of accuracies
            categories = ['Fuzzy Names', 'Slang Terms', 'Filter Logic', 'Overall']
            accuracies = [
                report['summary']['fuzzy_name_accuracy'],
                report['summary']['slang_accuracy'],
                report['summary']['filter_logic_accuracy'],
                report['summary']['overall_accuracy']
            ]
            
            plt.figure(figsize=(10, 6))
            bars = plt.bar(categories, accuracies, color=['#3498db', '#2ecc71', '#e74c3c', '#9b59b6'])
            
            # Add value labels on top of bars
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + 1,
                        f'{height:.1f}%', ha='center', va='bottom')
            
            plt.title('Mutual Fund Search System Evaluation', fontsize=16)
            plt.ylabel('Accuracy (%)', fontsize=12)
            plt.ylim(0, 105)  # Add some space at the top for labels
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            
            # Add a horizontal line at 90% as a target threshold
            plt.axhline(y=90, color='r', linestyle='--', alpha=0.5)
            plt.text(3.5, 91, 'Target Threshold (90%)', color='r', ha='right')
            
            # Save the visualization
            output_dir = utils.PROCESSED_DIR
            viz_path = os.path.join(output_dir, "evaluation_results.png")
            plt.tight_layout()
            plt.savefig(viz_path)
            plt.close()
            
            logger.info(f"Evaluation visualization saved to {viz_path}")
            
        except Exception as e:
            logger.error(f"Error generating visualization: {str(e)}")


def main():
    """Run the Phase 7 evaluation"""
    print("=" * 50)
    print("Phase 7: Evaluation & Test Query Defense")
    print("=" * 50)
    
    # Initialize components
    search_engine = SearchEngine()
    query_parser = QueryParser()
    retrieval = EnhancedRetrieval()
    llm = LLMInterface()
    
    # Initialize evaluator
    evaluator = SystemEvaluator(search_engine, query_parser, retrieval, llm)
    
    # Run evaluation
    report = evaluator.generate_evaluation_report()
    
    print("\nEvaluation complete!")
    print(f"Overall system accuracy: {report['summary']['overall_accuracy']:.1f}%")
    print(f"Full report saved to {os.path.join(utils.PROCESSED_DIR, 'evaluation_report.json')}")
    print(f"Visualization saved to {os.path.join(utils.PROCESSED_DIR, 'evaluation_results.png')}")
    

if __name__ == "__main__":
    main() 