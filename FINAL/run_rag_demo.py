import os
import time
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from search_engine import SearchEngine
from llm_interface import LLMInterface
from enhanced_retrieval import EnhancedRetrieval
from query_parser import QueryParser
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress
from rich.table import Table
from rich.text import Text

# Initialize console for rich output
console = Console()

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize global components
search_engine = None
llm_interface = None
enhanced_retrieval = None
query_parser = None

def initialize_components():
    """Initialize all required components for the API"""
    global search_engine, llm_interface, enhanced_retrieval, query_parser
    
    try:
        search_engine = SearchEngine()
        llm_interface = LLMInterface(verbose=False)
        enhanced_retrieval = EnhancedRetrieval()
        query_parser = QueryParser()
        return True
    except Exception as e:
        console.print(f"[bold red]Error initializing components:[/bold red] {str(e)}")
        return False

def display_rag_response(query, response, context_funds, time_taken, show_explanation=False):
    """Display RAG response with context information"""
    console.print(Panel(f"[bold blue]Query:[/bold blue] {query}", expand=False))
    
    # Display used context funds
    if context_funds:
        fund_names = [result['fund_data'].get('fund_name', 'Unknown Fund') for result in context_funds]
        console.print(f"[dim]Using context from {len(context_funds)} funds: {', '.join(fund_names)}[/dim]")
    
    console.print(f"[italic]Response time: {time_taken:.2f} seconds[/italic]")
    
    # If explainability is enabled, show score breakdown
    if show_explanation and context_funds:
        display_score_explanations(context_funds)
    
    # Display response as Markdown
    console.print(Panel(Markdown(response), title="LLM Response (RAG)", expand=False))

def display_score_explanations(results):
    """Display detailed score explanations for search results"""
    console.print("\n[bold]Search Result Score Explanations:[/bold]")
    
    # Create a table for score explanations
    table = Table(show_header=True)
    table.add_column("Rank", style="dim")
    table.add_column("Fund Name", style="cyan")
    table.add_column("Semantic", style="green")
    table.add_column("Metadata", style="yellow")
    table.add_column("Fuzzy", style="magenta")
    table.add_column("Final Score", style="bold blue")
    
    for i, result in enumerate(results):
        try:
            fund_name = result['fund_data'].get('fund_name', 'Unknown Fund')
            
            # Get score explanation if available, otherwise use the raw scores
            if 'score_explanation' in result:
                explanation = result['score_explanation']
                semantic = explanation.get('semantic_similarity', 'N/A')
                metadata = explanation.get('metadata_match', 'N/A')
                fuzzy = explanation.get('fuzzy_match', 'N/A')
                final = explanation.get('final_score', 'N/A')
            else:
                # Use raw scores if explanation not available
                semantic = f"{result.get('semantic_score', 0):.4f}"
                metadata = f"{result.get('metadata_score', 0):.4f}"
                fuzzy = f"{result.get('fuzzy_score', 0):.4f}"
                final = f"{result.get('final_score', result.get('score', 0)):.4f}"
            
            table.add_row(
                str(i+1),
                fund_name,
                semantic,
                metadata,
                fuzzy,
                final
            )
        except Exception as e:
            console.print(f"[red]Error displaying result {i+1}: {str(e)}[/red]")
    
    console.print(table)
    console.print("\n[dim]Explanation: The final score is a weighted combination of semantic, metadata, and fuzzy matching scores.[/dim]")

def run_rag_demo():
    """Run an interactive RAG demo with the prompt template from Phase 6"""
    console.print(Panel("[bold]Phase 6: Prompt Engineering for RAG + Phase 7: Explainability[/bold]", style="blue"))
    
    # Initialize components
    try:
        with Progress() as progress:
            task1 = progress.add_task("[yellow]Initializing search engine...", total=1)
            search_engine = SearchEngine()
            progress.update(task1, completed=1)
            
            task2 = progress.add_task("[green]Initializing LLM interface...", total=1)
            llm = LLMInterface(verbose=False)
            progress.update(task2, completed=1)
            
            task3 = progress.add_task("[cyan]Initializing enhanced retrieval...", total=1)
            enhanced_retrieval = EnhancedRetrieval()
            progress.update(task3, completed=1)
    except Exception as e:
        console.print(f"[bold red]Error initializing components:[/bold red] {str(e)}")
        console.print("[bold red]Please check that all required files exist and paths are correctly configured.[/bold red]")
        return
    
    if not llm.is_model_loaded():
        console.print(Panel("[bold red]Model not loaded[/bold red] - Please download the model file", expand=False))
        console.print(Panel(llm.download_model_instructions(), title="Download Instructions", expand=False))
        return
    
    console.print("[bold green]All components initialized![/bold green]")
    console.print("[italic]Type 'exit' or 'quit' to end the demo.[/italic]")
    console.print("[italic]Type 'explain on' to enable explainability or 'explain off' to disable it.[/italic]")
    
    # Show the RAG template to the user
    rag_template = """
You are a mutual fund advisor. A user asked: "{user_query}".

Here are top matching funds:
{context_fund_1}
{context_fund_2}
{context_fund_3}

Which one is the best match? Explain why in 3 sentences.
"""
    console.print(Panel(rag_template, title="RAG Prompt Template", style="cyan"))
    
    # Sample queries to help the user get started
    sample_queries = [
        "Which fund is best for long-term retirement savings?",
        "I'm looking for a low-risk debt fund with good returns",
        "Recommend a tax-saving fund with high growth potential",
        "Which fund has the best 5-year performance?",
        "I need a fund for my child's education in 10 years"
    ]
    
    console.print(Panel("\n".join(sample_queries), title="Sample Queries", style="green"))
    
    # Explainability toggle (default: off)
    show_explanation = False
    
    # Start conversation loop
    while True:
        # Get user query
        console.print("\n[bold]Enter your mutual fund query:[/bold] ", end="")
        try:
            user_query = input()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold green]Exiting demo...[/bold green]")
            break
        
        if user_query.lower() in ['exit', 'quit', 'bye', 'goodbye']:
            console.print("[bold green]Goodbye![/bold green]")
            break
        
        # Handle explainability toggle
        if user_query.lower() == 'explain on':
            show_explanation = True
            console.print("[bold green]Explainability enabled. Score explanations will be shown.[/bold green]")
            continue
        
        if user_query.lower() == 'explain off':
            show_explanation = False
            console.print("[bold green]Explainability disabled. Score explanations will be hidden.[/bold green]")
            continue
        
        if not user_query.strip():
            continue
            
        try:
            # Search for relevant funds
            with Progress() as progress:
                task = progress.add_task("[yellow]Searching for relevant funds...", total=1)
                try:
                    search_results = search_engine.search(user_query, top_k=5)
                    progress.update(task, completed=1)
                except Exception as e:
                    progress.update(task, completed=1, description="[red]Search failed[/red]")
                    console.print(f"[bold red]Error during search:[/bold red] {str(e)}")
                    continue
            
            if not search_results:
                console.print("[bold yellow]No relevant funds found. Please try a different query.[/bold yellow]")
                continue
            
            # Apply enhanced retrieval scoring
            with Progress() as progress:
                task = progress.add_task("[magenta]Applying enhanced scoring...", total=1)
                try:
                    # Parse query for filters
                    from query_parser import QueryParser
                    query_parser = QueryParser()
                    parsed_query = query_parser.parse_query(user_query)
                    filters = parsed_query.get('filters', {})
                    
                    # Apply enhanced scoring
                    enhanced_results = enhanced_retrieval.compute_final_scores(
                        search_results, 
                        user_query, 
                        filters
                    )
                    progress.update(task, completed=1)
                except Exception as e:
                    progress.update(task, completed=1, description="[red]Enhanced scoring failed[/red]")
                    console.print(f"[bold red]Error during enhanced scoring:[/bold red] {str(e)}")
                    enhanced_results = search_results
                
            # Generate RAG prompt
            with Progress() as progress:
                task = progress.add_task("[cyan]Generating RAG prompt...", total=1)
                try:
                    rag_prompt = enhanced_retrieval.generate_rag_prompt(user_query, enhanced_results[:3])
                    progress.update(task, completed=1)
                except Exception as e:
                    progress.update(task, completed=1, description="[red]Prompt generation failed[/red]")
                    console.print(f"[bold red]Error generating prompt:[/bold red] {str(e)}")
                    continue
            
            # Show the generated prompt if requested
            if "show prompt" in user_query.lower():
                console.print(Panel(rag_prompt, title="Generated RAG Prompt", style="cyan"))
                continue
            
            # Send to LLM
            with Progress() as progress:
                task = progress.add_task("[green]Generating LLM response...", total=1)
                
                try:
                    # Use the new generate_rag_response method
                    generated_text, time_taken = llm.generate_rag_response(
                        user_query=user_query,
                        rag_prompt=rag_prompt,
                        max_length=512
                    )
                    progress.update(task, completed=1)
                except Exception as e:
                    progress.update(task, completed=1, description="[red]LLM response failed[/red]")
                    console.print(f"[bold red]Error generating response:[/bold red] {str(e)}")
                    continue
            
            # Display response
            display_rag_response(
                user_query, 
                generated_text, 
                enhanced_results[:3], 
                time_taken,
                show_explanation=show_explanation
            )
            
        except Exception as e:
            console.print(f"[bold red]Unexpected error:[/bold red] {str(e)}")
            console.print("[yellow]Please try again with a different query.[/yellow]")

@app.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint for fund searches"""
    try:
        # Get request data
        data = request.json
        user_query = data.get('query', '')
        
        if not user_query:
            return jsonify({"error": "No query provided"}), 400
            
        # Search for relevant funds
        search_results = search_engine.search(user_query, top_k=10)
        
        if not search_results:
            return jsonify({"results": [], "message": "No relevant funds found"}), 200
        
        # Parse query for filters
        parsed_query = query_parser.parse_query(user_query)
        filters = parsed_query.get('filters', {})
        
        # Apply enhanced scoring
        enhanced_results = enhanced_retrieval.compute_final_scores(
            search_results, 
            user_query, 
            filters
        )
        
        # Convert to UI-friendly format
        ui_results = []
        for result in enhanced_results:
            fund_data = result['fund_data']
            
            # Get score explanations
            score_explanation = {
                "semantic": f"{result['similarity']:.2f}",
                "metadata": f"{result.get('metadata_score', 0):.2f}",
                "fuzzy": f"{result.get('fuzzy_score', 0):.2f}",
                "final": f"{result.get('final_score', 0):.2f}"
            }
            
            # Create UI-compatible fund object
            fund = {
                "id": fund_data.get('scheme_code', ''),
                "name": fund_data.get('fund_name', 'Unknown Fund'),
                "ticker": fund_data.get('scheme_code', ''),
                "fundHouse": fund_data.get('amc', 'Unknown'),
                "category": fund_data.get('category', 'Unknown'),
                "returns": {
                    "oneYear": fund_data.get('return_1yr', 0),
                    "threeYear": fund_data.get('return_3yr', 0),
                    "fiveYear": fund_data.get('return_5yr', 0)
                },
                "aum": fund_data.get('aum', 'N/A'),
                "risk": fund_data.get('risk_level', 'Moderate'),
                "description": fund_data.get('investment_objective', ''),
                "searchScore": result.get('final_score', 0),
                "scoreExplanation": score_explanation
            }
            
            # Match explanation for UI
            match_reason = ""
            if fund['returns']['oneYear'] > 30:
                match_reason = f"{fund['name']} has the highest return of {fund['returns']['oneYear']}% among the available funds, aligning with the query."
            elif fund['returns']['oneYear'] > 20:
                match_reason = f"{fund['name']} offers a high return of {fund['returns']['oneYear']}%, making it a strong match for the query."
            else:
                match_reason = f"{fund['name']} provides a significant return of {fund['returns']['oneYear']}%, satisfying the query requirement."
                
            fund["matchExplanation"] = match_reason
            
            ui_results.append(fund)
        
        return jsonify({"results": ui_results}), 200
    
    except Exception as e:
        console.print(f"[bold red]API Error:[/bold red] {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """API endpoint for detailed fund analysis"""
    try:
        # Get request data
        data = request.json
        fund_id = data.get('fundId', '')
        
        if not fund_id:
            return jsonify({"error": "No fund ID provided"}), 400
            
        # Mock analysis for now
        # In a real implementation, we would fetch actual fund data
        analysis = {
            "summary": "This fund has shown strong performance over the past 5 years with consistent returns above the category average. It maintains a well-diversified portfolio with a focus on high-growth sectors.",
            "strengths": [
                "Excellent historical returns",
                "Experienced fund management team",
                "Low expense ratio compared to peers",
                "Consistent performance across market cycles"
            ],
            "weaknesses": [
                "Slightly higher volatility than category average",
                "Moderate concentration risk in technology sector",
                "May underperform in bearish markets"
            ],
            "performance": {
                "1yr": {"fund": 28.5, "category": 22.4, "benchmark": 24.1},
                "3yr": {"fund": 15.2, "category": 12.8, "benchmark": 13.5},
                "5yr": {"fund": 12.8, "category": 10.1, "benchmark": 11.2}
            },
            "sectorAllocation": [
                {"name": "Finance", "value": 32},
                {"name": "Technology", "value": 28},
                {"name": "Consumer Goods", "value": 15},
                {"name": "Healthcare", "value": 12},
                {"name": "Others", "value": 13}
            ]
        }
        
        return jsonify({"analysis": analysis}), 200
    
    except Exception as e:
        console.print(f"[bold red]API Error:[/bold red] {str(e)}")
        return jsonify({"error": str(e)}), 500

def start_web_api(host='0.0.0.0', port=5000, debug=False):
    """Start the Flask API server"""
    if initialize_components():
        console.print(f"[bold green]Starting Web API on {host}:{port}[/bold green]")
        app.run(host=host, port=port, debug=debug)
    else:
        console.print("[bold red]Failed to initialize components. API cannot start.[/bold red]")

def main():
    """Entry point for the script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Mutual Fund RAG Demo')
    parser.add_argument('--web', action='store_true', help='Start the web API for UI integration')
    parser.add_argument('--port', type=int, default=5000, help='Port for web API (default: 5000)')
    args = parser.parse_args()
    
    if args.web:
        start_web_api(port=args.port, debug=True)
    else:
        run_rag_demo()

if __name__ == "__main__":
    main() 