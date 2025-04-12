import os
import time
from search_engine import MutualFundSearchEngine
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.syntax import Syntax
import json

# Initialize console for rich output
console = Console()

def display_score_breakdown(result):
    """Display the score breakdown for a search result"""
    if 'score_explanation' not in result:
        return ""
    
    score_data = result['score_explanation']
    
    breakdown = f"""
**Score Breakdown:**
- Semantic Similarity: {score_data.get('semantic_similarity', 'N/A')}
- Metadata Match: {score_data.get('metadata_match', 'N/A')}
- Fuzzy Match: {score_data.get('fuzzy_match', 'N/A')}
- **Final Score:** {score_data.get('final_score', 'N/A')}
    """
    return breakdown

def display_results(query, results, time_taken):
    """Display search results in a formatted table"""
    console.print(Panel(f"[bold blue]Query:[/bold blue] {query}", expand=False))
    console.print(f"[italic]Time taken: {time_taken:.4f} seconds[/italic]")
    
    # Display extracted filters if available
    if results and 'filter_explanation' in results[0]:
        filter_explanation = results[0]['filter_explanation']
        console.print(Panel(f"[bold green]Smart Query Parsing:[/bold green] {filter_explanation}", expand=False))
        
        if 'extracted_filters' in results[0]:
            syntax = Syntax(json.dumps(results[0]['extracted_filters'], indent=2), "json", theme="monokai")
            console.print(Panel(syntax, title="Extracted Filters", expand=False))
    
    if not results:
        console.print("[bold red]No results found.[/bold red]")
        return
    
    # Display results table
    table = Table(show_header=True, header_style="bold")
    table.add_column("Fund Name", style="cyan")
    table.add_column("Category", style="green")
    table.add_column("AMC", style="yellow")
    table.add_column("Risk Level", style="red")
    table.add_column("Score", style="blue")
    
    for result in results:
        table.add_row(
            result.get('fund_name', 'N/A'),
            result.get('category', 'N/A'),
            result.get('amc', 'N/A'),
            result.get('risk_level', 'N/A'),
            f"{result.get('score', 0):.4f}"
        )
    
    console.print(table)
    
    # Display detailed info for top result
    if results:
        top_result = results[0]
        description = top_result.get('description', '')
        score_breakdown = display_score_breakdown(top_result)
        
        details = f"""
## {top_result.get('fund_name', 'Unknown Fund')}

**Category:** {top_result.get('category', 'N/A')}  
**AMC:** {top_result.get('amc', 'N/A')}  
**Risk Level:** {top_result.get('risk_level', 'N/A')}  

**Description:**  
{description}

{score_breakdown}
        """
        
        console.print(Panel(Markdown(details), title="Top Result Details", expand=False))
        
        # If we have score components, show a comparison for top 3 results
        if len(results) >= 2 and 'semantic_score' in results[0]:
            compare_table = Table(show_header=True, header_style="bold")
            compare_table.add_column("Rank", style="dim")
            compare_table.add_column("Fund Name", style="cyan")
            compare_table.add_column("Semantic", style="green")
            compare_table.add_column("Metadata", style="yellow")
            compare_table.add_column("Fuzzy", style="red")
            compare_table.add_column("Final", style="blue bold")
            
            for i, result in enumerate(results[:3], 1):
                compare_table.add_row(
                    str(i),
                    result.get('fund_name', 'N/A'),
                    f"{result.get('semantic_score', 0):.4f}",
                    f"{result.get('metadata_score', 0):.4f}",
                    f"{result.get('fuzzy_score', 0):.4f}", 
                    f"{result.get('final_score', 0):.4f}"
                )
            
            console.print(Panel(compare_table, title="[bold]Score Comparison (Top 3)[/bold]", expand=False))

def run_demo():
    """Run search engine demo with sample queries"""
    console.print(Panel("[bold]Mutual Fund Search Engine Demo[/bold] with Smart Query Parsing and Enhanced Scoring", style="blue"))
    
    # Initialize search engine
    console.print("Initializing search engine...", style="yellow")
    try:
        search_engine = MutualFundSearchEngine()
        console.print("Search engine initialized successfully!", style="green")
    except Exception as e:
        console.print(f"Error initializing search engine: {str(e)}", style="bold red")
        return
    
    # Sample queries to demonstrate smart query parsing & enhanced scoring
    sample_queries = [
        "Show me SBI funds with low risk and good performance",
        "I want a large cap fund with 3-year returns above 15% from HDFC",
        "Find debt funds with expense ratio less than 1% suitable for conservative investors",
        "Show me funds that invest in technology sector with high returns",
        "HDFC mutual funds with moderate risk in banking sector",
        "Tax saving ELSS funds with high returns for long term investment",
        "Find infrastructure funds with returns over 12% and low expense ratio",
        "Show me mid cap funds from ICICI with at least 10% returns",
        "Recommend low risk liquid funds for short term investment",
        "Show me funds investing in healthcare sector with 5-year returns above 18%"
    ]
    
    # Run each sample query
    for i, query in enumerate(sample_queries, 1):
        console.print(f"\n[bold]Query {i}/{len(sample_queries)}[/bold]")
        
        try:
            # Measure search time
            start_time = time.time()
            
            # Search with enhanced scoring enabled
            results = search_engine.search(query, top_k=5, use_enhanced_scoring=True)
            
            end_time = time.time()
            
            # Store extracted filters in results for display
            if results and hasattr(search_engine, 'query_parser'):
                extracted_filters = search_engine.query_parser.parse_query(query)
                for result in results:
                    result['extracted_filters'] = extracted_filters
            
            # Display results
            display_results(query, results, end_time - start_time)
            
        except Exception as e:
            console.print(f"Error processing query: {str(e)}", style="bold red")
        
        # Pause between queries for better readability
        if i < len(sample_queries):
            console.print("\nPress Enter for next query...", style="italic")
            input()
    
    console.print("\n[bold green]Demo completed![/bold green]")

if __name__ == "__main__":
    run_demo() 