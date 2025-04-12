import os
import time
from search_engine import MutualFundSearchEngine
from llm_interface import LLMInterface
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress
import json

# Initialize console for rich output
console = Console()

def display_llm_response(query, response, context_funds, time_taken):
    """Display LLM response with context information"""
    console.print(Panel(f"[bold blue]Query:[/bold blue] {query}", expand=False))
    
    # Display used context funds
    if context_funds:
        fund_names = [f.get('fund_name', 'Unknown Fund') for f in context_funds]
        console.print(f"[dim]Using context from {len(context_funds)} funds: {', '.join(fund_names)}[/dim]")
    
    console.print(f"[italic]Response time: {time_taken:.2f} seconds[/italic]")
    
    # Display response as Markdown
    console.print(Panel(Markdown(response), title="LLM Response", expand=False))

def run_conversation_mode():
    """Run an interactive conversation mode with the LLM"""
    console.print(Panel("[bold]Mutual Fund Analysis with LLM[/bold] - Conversation Mode", style="blue"))
    
    # Initialize search engine and LLM
    with Progress() as progress:
        task1 = progress.add_task("[yellow]Initializing search engine...", total=1)
        search_engine = MutualFundSearchEngine()
        progress.update(task1, completed=1)
        
        task2 = progress.add_task("[green]Initializing LLM interface...", total=1)
        llm = LLMInterface(verbose=False)
        progress.update(task2, completed=1)
    
    if not llm.is_model_loaded():
        console.print(Panel("[bold red]Model not loaded[/bold red] - Please download the model file", expand=False))
        console.print(Panel(llm.download_model_instructions(), title="Download Instructions", expand=False))
        return
    
    console.print("[bold green]LLM and search engine ready![/bold green]")
    console.print("[italic]Type 'exit' or 'quit' to end the conversation.[/italic]")
    
    # Start conversation loop
    while True:
        # Get user query
        console.print("\n[bold]Ask about mutual funds:[/bold] ", end="")
        query = input()
        
        if query.lower() in ['exit', 'quit', 'bye', 'goodbye']:
            console.print("[bold green]Goodbye![/bold green]")
            break
        
        if not query.strip():
            continue
            
        try:
            # Search for relevant funds
            with Progress() as progress:
                task1 = progress.add_task("[yellow]Searching for relevant funds...", total=1)
                results = search_engine.search(query, top_k=3)
                progress.update(task1, completed=1)
            
            if not results:
                console.print("[bold yellow]No relevant funds found. Please try a different query.[/bold yellow]")
                continue
                
            # Extract fund data for context
            context_funds = [result['fund_data'] for result in results]
            
            # Generate LLM response
            with Progress() as progress:
                task = progress.add_task("[green]Generating LLM response...", total=1)
                response, time_taken = llm.generate_response(query, context_funds)
                progress.update(task, completed=1)
            
            # Display response
            display_llm_response(query, response, context_funds, time_taken)
            
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")

def run_guided_demo():
    """Run a guided demo with predefined queries"""
    console.print(Panel("[bold]Mutual Fund Analysis with LLM[/bold] - Guided Demo", style="blue"))
    
    # Initialize search engine and LLM
    with Progress() as progress:
        task1 = progress.add_task("[yellow]Initializing search engine...", total=1)
        search_engine = MutualFundSearchEngine()
        progress.update(task1, completed=1)
        
        task2 = progress.add_task("[green]Initializing LLM interface...", total=1)
        llm = LLMInterface(verbose=False)
        progress.update(task2, completed=1)
    
    if not llm.is_model_loaded():
        console.print(Panel("[bold red]Model not loaded[/bold red] - Please download the model file", expand=False))
        console.print(Panel(llm.download_model_instructions(), title="Download Instructions", expand=False))
        return
    
    console.print("[bold green]LLM and search engine ready![/bold green]")
    
    # Sample analysis queries
    sample_queries = [
        "Which HDFC mutual funds are best for long-term investment?",
        "Compare large cap vs mid cap funds in terms of risk and returns",
        "Explain expense ratio and how it affects mutual fund returns",
        "What are the best tax-saving ELSS funds available?",
        "How do I build a balanced mutual fund portfolio for moderate risk?",
        "Which are the best performing debt funds in the last 3 years?"
    ]
    
    # Run each analysis query
    for i, query in enumerate(sample_queries, 1):
        console.print(f"\n[bold]Demo {i}/{len(sample_queries)}:[/bold] {query}")
        
        try:
            # Search for relevant funds
            with Progress() as progress:
                task = progress.add_task("[yellow]Searching for relevant funds...", total=1)
                results = search_engine.search(query, top_k=5)
                progress.update(task, completed=1)
            
            # Extract fund data for context
            context_funds = [result['fund_data'] for result in results[:3]]  # Use top 3 for context
            
            # Generate LLM response
            with Progress() as progress:
                task = progress.add_task("[green]Generating LLM response...", total=1)
                response, time_taken = llm.generate_response(query, context_funds)
                progress.update(task, completed=1)
            
            # Display response
            display_llm_response(query, response, context_funds, time_taken)
            
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
        
        # Pause between demos
        if i < len(sample_queries):
            console.print("\nPress Enter for next demo...", style="italic")
            input()
    
    console.print("\n[bold green]Demo completed![/bold green]")

def run_fund_specific_analysis():
    """Run specific fund analysis with LLM"""
    console.print(Panel("[bold]Mutual Fund Analysis with LLM[/bold] - Fund-Specific Analysis", style="blue"))
    
    # Initialize search engine and LLM
    with Progress() as progress:
        task1 = progress.add_task("[yellow]Initializing search engine...", total=1)
        search_engine = MutualFundSearchEngine()
        progress.update(task1, completed=1)
        
        task2 = progress.add_task("[green]Initializing LLM interface...", total=1)
        llm = LLMInterface(verbose=False)
        progress.update(task2, completed=1)
    
    if not llm.is_model_loaded():
        console.print(Panel("[bold red]Model not loaded[/bold red] - Please download the model file", expand=False))
        console.print(Panel(llm.download_model_instructions(), title="Download Instructions", expand=False))
        return
    
    console.print("[bold green]LLM and search engine ready![/bold green]")
    
    # Sample funds to analyze
    sample_funds = [
        "HDFC Midcap Opportunities Fund",
        "SBI Blue Chip Fund",
        "Axis Long Term Equity Fund",
        "Mirae Asset Emerging Bluechip Fund"
    ]
    
    # Analysis aspects
    analysis_aspects = [
        "key strengths and weaknesses",
        "suitability for different investor profiles",
        "comparison with similar funds",
        "historical performance and future outlook"
    ]
    
    # Run analysis for each fund
    for i, fund_name in enumerate(sample_funds, 1):
        console.print(f"\n[bold]Fund Analysis {i}/{len(sample_funds)}:[/bold] {fund_name}")
        
        try:
            # Search for the specific fund
            with Progress() as progress:
                task = progress.add_task(f"[yellow]Finding {fund_name}...", total=1)
                results = search_engine.search(fund_name, top_k=1)
                progress.update(task, completed=1)
            
            if not results:
                console.print(f"[bold yellow]Fund '{fund_name}' not found. Skipping analysis.[/bold yellow]")
                continue
                
            # Get the fund data
            fund_data = results[0]['fund_data']
            
            # Generate analysis query with random aspects
            aspect = analysis_aspects[i % len(analysis_aspects)]
            analysis_query = f"Analyze {fund_name} focusing on {aspect}."
            
            # Generate LLM response
            with Progress() as progress:
                task = progress.add_task("[green]Generating analysis...", total=1)
                response, time_taken = llm.analyze_fund(fund_data, analysis_query)
                progress.update(task, completed=1)
            
            # Display response
            display_llm_response(analysis_query, response, [fund_data], time_taken)
            
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
        
        # Pause between analyses
        if i < len(sample_funds):
            console.print("\nPress Enter for next fund analysis...", style="italic")
            input()
    
    console.print("\n[bold green]Fund analysis completed![/bold green]")

def run_fund_comparison():
    """Run comparison of multiple funds with LLM"""
    console.print(Panel("[bold]Mutual Fund Analysis with LLM[/bold] - Fund Comparison", style="blue"))
    
    # Initialize search engine and LLM
    with Progress() as progress:
        task1 = progress.add_task("[yellow]Initializing search engine...", total=1)
        search_engine = MutualFundSearchEngine()
        progress.update(task1, completed=1)
        
        task2 = progress.add_task("[green]Initializing LLM interface...", total=1)
        llm = LLMInterface(verbose=False)
        progress.update(task2, completed=1)
    
    if not llm.is_model_loaded():
        console.print(Panel("[bold red]Model not loaded[/bold red] - Please download the model file", expand=False))
        console.print(Panel(llm.download_model_instructions(), title="Download Instructions", expand=False))
        return
    
    console.print("[bold green]LLM and search engine ready![/bold green]")
    
    # Sample comparison scenarios
    comparisons = [
        {
            "title": "Large Cap Funds Comparison",
            "query": "Compare top performing large cap funds",
            "aspects": ["returns", "risk", "portfolio composition", "expense ratio"]
        },
        {
            "title": "Tax-Saving ELSS Funds Comparison",
            "query": "Compare best ELSS funds for tax saving",
            "aspects": ["tax benefits", "lock-in period", "historical performance", "dividend options"]
        },
        {
            "title": "Debt Funds for Conservative Investors",
            "query": "Compare low risk debt funds",
            "aspects": ["safety", "returns", "liquidity", "taxation"]
        }
    ]
    
    # Run each comparison
    for i, comparison in enumerate(comparisons, 1):
        console.print(f"\n[bold]Comparison {i}/{len(comparisons)}:[/bold] {comparison['title']}")
        
        try:
            # Search for relevant funds
            with Progress() as progress:
                task = progress.add_task("[yellow]Finding relevant funds...", total=1)
                results = search_engine.search(comparison["query"], top_k=4)  # Get 4 funds to compare
                progress.update(task, completed=1)
            
            if len(results) < 2:
                console.print(f"[bold yellow]Not enough funds found for comparison. Need at least 2 funds.[/bold yellow]")
                continue
                
            # Extract fund data for comparison
            funds_to_compare = [result['fund_data'] for result in results]
            
            # Generate comparison query
            aspects_str = ", ".join(comparison["aspects"])
            comparison_query = f"Compare these mutual funds focusing on these aspects: {aspects_str}. Which fund would be most suitable for different investor profiles?"
            
            # Generate LLM response
            with Progress() as progress:
                task = progress.add_task("[green]Generating comparison...", total=1)
                response, time_taken = llm.compare_funds(funds_to_compare, comparison["aspects"])
                progress.update(task, completed=1)
            
            # Display response
            display_llm_response(comparison_query, response, funds_to_compare, time_taken)
            
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
        
        # Pause between comparisons
        if i < len(comparisons):
            console.print("\nPress Enter for next comparison...", style="italic")
            input()
    
    console.print("\n[bold green]Fund comparisons completed![/bold green]")

def main():
    """Main function to run the LLM demo"""
    console.print(Panel("[bold]Mutual Fund RAG System with Mistral-7B[/bold]", style="blue"))
    
    options = [
        ("1", "Guided Demo (Predefined Queries)"),
        ("2", "Conversation Mode (Interactive)"),
        ("3", "Fund-Specific Analysis"),
        ("4", "Fund Comparison"),
        ("5", "Exit")
    ]
    
    while True:
        console.print("\n[bold]Choose a demo mode:[/bold]")
        for option, description in options:
            console.print(f"  {option}. {description}")
        
        choice = input("\nEnter your choice (1-5): ")
        
        if choice == "1":
            run_guided_demo()
        elif choice == "2":
            run_conversation_mode()
        elif choice == "3":
            run_fund_specific_analysis()
        elif choice == "4":
            run_fund_comparison()
        elif choice == "5":
            console.print("[bold green]Goodbye![/bold green]")
            break
        else:
            console.print("[bold red]Invalid choice. Please try again.[/bold red]")

if __name__ == "__main__":
    main() 