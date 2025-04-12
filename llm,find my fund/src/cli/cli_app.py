import os
import sys
import json
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any
import typer
from loguru import logger

# Add the project root to sys.path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.search_engine import SearchEngine

# Initialize Typer app
app = typer.Typer(help="LLM, Find My Fund - Search engine for financial funds")

# Initialize logger
logger.remove()
logger.add(sys.stderr, level="INFO")

def display_result(result: Dict[str, Any], rank: int = 1) -> None:
    """
    Display a search result in a formatted way.
    
    Args:
        result: Fund result dictionary
        rank: Rank of the result
    """
    typer.echo(f"\n[{rank}] {result['fund_name']}")
    typer.echo("=" * (len(result['fund_name']) + 4))
    
    # Display metadata
    metadata_fields = ["fund_house", "category", "sub_category", "asset_class", "fund_type", "sector"]
    for field in metadata_fields:
        if field in result and result[field] not in ["unknown", "nan", "None", None]:
            typer.echo(f"  {field.replace('_', ' ').title()}: {result[field]}")
    
    # Display scores
    typer.echo("\n  Scores:")
    if "bm25_score" in result:
        typer.echo(f"    Lexical: {result['bm25_score']:.4f}")
    if "semantic_score" in result:
        typer.echo(f"    Semantic: {result['semantic_score']:.4f}")
    if "combined_score" in result:
        typer.echo(f"    Combined: {result['combined_score']:.4f}")
    
    typer.echo("")

@app.command()
def search(
    query: str = typer.Argument(..., help="Search query for finding funds"),
    data_path: str = typer.Option("data/funds.csv", help="Path to the fund data file"),
    model_dir: str = typer.Option("models", help="Directory containing saved models"),
    top_k: int = typer.Option(5, help="Number of results to display"),
    search_type: str = typer.Option("hybrid", help="Search type: lexical, semantic, or hybrid"),
    force_retrain: bool = typer.Option(False, help="Force retraining of models")
):
    """
    Search for funds matching the query.
    """
    typer.echo(f"Searching for: {query}")
    
    # Initialize search engine
    engine = SearchEngine(data_path=data_path)
    
    # Check if models exist
    model_path = os.path.join(model_dir, "hnsw_index.bin")
    metadata_path = os.path.join(model_dir, "index_metadata.json")
    processed_data_path = os.path.join(model_dir, "processed_funds.csv")
    
    models_exist = (
        os.path.exists(model_path) and 
        os.path.exists(metadata_path) and 
        os.path.exists(processed_data_path)
    )
    
    if models_exist and not force_retrain:
        typer.echo("Loading pre-trained models...")
        engine.load_models(directory=model_dir, data_path=processed_data_path)
    else:
        typer.echo("Training models...")
        engine.fit(force_reload=True)
        
        # Save models for future use
        os.makedirs(model_dir, exist_ok=True)
        engine.save_models(directory=model_dir)
    
    # Perform search
    typer.echo(f"Performing {search_type} search...")
    results = engine.search(query, top_k=top_k, search_type=search_type)
    
    # Display results
    if not results:
        typer.echo("No matching funds found.")
        return
    
    typer.echo(f"\nFound {len(results)} matching funds:")
    
    for i, result in enumerate(results, 1):
        display_result(result, i)

@app.command()
def train(
    data_path: str = typer.Option("data/funds.csv", help="Path to the fund data file"),
    model_dir: str = typer.Option("models", help="Directory to save models"),
    force: bool = typer.Option(False, help="Force retraining of models")
):
    """
    Train models and save them for later use.
    """
    typer.echo(f"Loading fund data from: {data_path}")
    
    # Initialize and train search engine
    engine = SearchEngine(data_path=data_path)
    engine.fit(force_reload=True)
    
    # Save models
    os.makedirs(model_dir, exist_ok=True)
    engine.save_models(directory=model_dir)
    
    typer.echo(f"Models trained and saved to {model_dir}")

@app.command()
def interactive(
    data_path: str = typer.Option("data/funds.csv", help="Path to the fund data file"),
    model_dir: str = typer.Option("models", help="Directory containing saved models"),
    top_k: int = typer.Option(5, help="Number of results to display")
):
    """
    Start an interactive search session.
    """
    typer.echo("LLM, Find My Fund - Interactive Search")
    typer.echo("=====================================")
    typer.echo("Type 'exit' or 'quit' to end the session.")
    
    # Initialize search engine
    engine = SearchEngine(data_path=data_path)
    
    # Check if models exist
    model_path = os.path.join(model_dir, "hnsw_index.bin")
    metadata_path = os.path.join(model_dir, "index_metadata.json")
    processed_data_path = os.path.join(model_dir, "processed_funds.csv")
    
    models_exist = (
        os.path.exists(model_path) and 
        os.path.exists(metadata_path) and 
        os.path.exists(processed_data_path)
    )
    
    if models_exist:
        typer.echo("Loading pre-trained models...")
        engine.load_models(directory=model_dir, data_path=processed_data_path)
    else:
        typer.echo("Training models (this may take a while)...")
        engine.fit(force_reload=True)
        
        # Save models for future use
        os.makedirs(model_dir, exist_ok=True)
        engine.save_models(directory=model_dir)
    
    typer.echo("\nModels loaded successfully. Ready for search queries.")
    
    while True:
        query = typer.prompt("\nEnter search query")
        
        if query.lower() in ["exit", "quit"]:
            typer.echo("Goodbye!")
            break
        
        # Perform search
        results = engine.search(query, top_k=top_k)
        
        # Display results
        if not results:
            typer.echo("No matching funds found.")
            continue
        
        typer.echo(f"\nFound {len(results)} matching funds:")
        
        for i, result in enumerate(results, 1):
            display_result(result, i)

if __name__ == "__main__":
    app() 