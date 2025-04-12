import os
import json
import pandas as pd
import numpy as np
from tqdm import tqdm
from pathlib import Path

# Project directories
PROJECT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
# Check if we're in the FINAL directory, and handle paths accordingly
if PROJECT_DIR.name == 'FINAL':
    DATA_DIR = PROJECT_DIR.parent / "datasets"
else:
    DATA_DIR = PROJECT_DIR / "datasets"

# Create processed and models directories within the project directory
PROCESSED_DIR = PROJECT_DIR / "processed_data"
MODELS_DIR = PROJECT_DIR / "models"

# Ensure directories exist
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)
# Ensure data directory exists (if it doesn't, log a warning but don't fail)
if not os.path.exists(DATA_DIR):
    print(f"Warning: Data directory '{DATA_DIR}' does not exist. Creating it, but you need to add data files.")
    os.makedirs(DATA_DIR, exist_ok=True)

def get_data_paths():
    """Return paths to data files"""
    return {
        "mf_data": DATA_DIR / "mutual_funds_data.json",
        "stock_data": DATA_DIR / "stock_data.json",
        "holdings_data": DATA_DIR / "mf_holdings_data.json",
        "queries_data": DATA_DIR / "Dataset Queries-Securities for Model Creation.csv"
    }

def get_output_paths():
    """Return paths to output files"""
    return {
        "enriched_fund_data": PROCESSED_DIR / "enriched_fund_data.csv",
        "fund_descriptions": PROCESSED_DIR / "fund_descriptions.csv",
        "fund_corpus": PROCESSED_DIR / "fund_corpus.txt",
        "fund_embeddings": PROCESSED_DIR / "fund_embeddings.npy",
        "faiss_index": PROCESSED_DIR / "faiss_index.bin",
        "fund_id_to_index": PROCESSED_DIR / "fund_id_to_index.json",
        "preprocessed_funds": PROCESSED_DIR / "preprocessed_funds.json"  # Added missing path
    }

def get_model_paths():
    """Return paths to model files"""
    return {
        "embedding_model": MODELS_DIR / "embedding_model",
        "llm_model": MODELS_DIR / "phi-2.gguf"
    }

def load_processed_data():
    """Load preprocessed data"""
    output_paths = get_output_paths()
    
    data = {}
    
    # Load enriched fund data
    if os.path.exists(output_paths["enriched_fund_data"]):
        data["enriched_fund_data"] = pd.read_csv(output_paths["enriched_fund_data"])
        print(f"Loaded enriched fund data: {len(data['enriched_fund_data'])} funds")
    
    # Load fund descriptions
    if os.path.exists(output_paths["fund_descriptions"]):
        data["fund_descriptions"] = pd.read_csv(output_paths["fund_descriptions"])
        print(f"Loaded fund descriptions: {len(data['fund_descriptions'])} descriptions")
    
    # Load fund corpus
    if os.path.exists(output_paths["fund_corpus"]):
        with open(output_paths["fund_corpus"], "r", encoding="utf-8") as f:
            data["fund_corpus"] = f.read().splitlines()
        print(f"Loaded fund corpus: {len(data['fund_corpus'])} descriptions")
    
    # Load fund_id to index mapping
    if os.path.exists(output_paths["fund_id_to_index"]):
        with open(output_paths["fund_id_to_index"], "r") as f:
            data["fund_id_to_index"] = json.load(f)
        print(f"Loaded fund_id to index mapping for {len(data['fund_id_to_index'])} funds")
    
    return data

def clean_text(text):
    """Clean and normalize text for better matching"""
    if not isinstance(text, str):
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove extra whitespace
    text = " ".join(text.split())
    
    return text

def normalize_fund_name(name):
    """Normalize fund names for better matching"""
    if not isinstance(name, str):
        return ""
    
    # Remove common suffixes
    suffixes = [
        "direct growth", "direct plan growth", "direct plan - growth",
        "regular growth", "regular plan growth", "regular plan - growth",
        "growth", "direct", "regular"
    ]
    
    name = name.lower()
    for suffix in suffixes:
        if name.endswith(f" - {suffix}"):
            name = name[:-len(f" - {suffix}")]
        elif name.endswith(f" {suffix}"):
            name = name[:-len(f" {suffix}")]
    
    # Remove extra whitespace
    name = " ".join(name.split())
    
    return name

def format_currency(amount, currency="₹"):
    """Format amount as currency"""
    if pd.isna(amount):
        return "N/A"
    
    if amount >= 10000000:  # 1 crore = 10 million
        return f"{currency}{amount/10000000:.2f} Cr"
    elif amount >= 100000:  # 1 lakh = 100 thousand
        return f"{currency}{amount/100000:.2f} L"
    else:
        return f"{currency}{amount:.2f}"

def format_percentage(value):
    """Format value as percentage"""
    if pd.isna(value):
        return "N/A"
    
    return f"{value:.2f}%" 