"""
Configuration settings for the Find My Fund application.
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

# Data paths
DATA_DIR = BASE_DIR / 'data'
PROCESSED_DATA_DIR = DATA_DIR / 'processed'
FUNDS_DATA_PATH = DATA_DIR / 'mutual_funds.csv'

# Ensure directories exist
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

# Model settings
MODEL_NAME = "BAAI/bge-small-en-v1.5"  # BGE small English model
EMBEDDINGS_PATH = PROCESSED_DATA_DIR / 'fund_embeddings.pkl'
INDEX_PATH = PROCESSED_DATA_DIR / 'faiss_index.pkl'
METADATA_PATH = PROCESSED_DATA_DIR / 'fund_metadata.json'

# Search settings
TOP_K = 5  # Number of results to return
VECTOR_DISTANCE = "cosine"  # Distance metric (cosine or L2)
RERANK_METHOD = "rule_based"  # Reranking method (rule_based or cross_encoder)

# UI settings
THEME = "dark"
DEFAULT_TEMPLATE = "I'm looking for a mutual fund that {criteria}."
SAMPLE_QUERIES = [
    "I want a large cap fund with consistent returns",
    "Show me tax saving ELSS funds with good long-term performance",
    "Find a debt fund with low risk for short-term investment",
    "Which fund invests in technology companies?",
    "Show me small cap funds with high returns",
    "I need a hybrid fund for balanced investment"
]

# Base paths
MODELS_DIR = BASE_DIR / "models"
APP_DIR = BASE_DIR / "app"

# Ensure directories exist
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(APP_DIR, exist_ok=True)

# Data files
HOLDINGS_DATA_PATH = DATA_DIR / "holdings.csv"

# Model settings
EMBEDDING_DIMENSION = 384  # For the MiniLM model

# API settings
API_HOST = "0.0.0.0"
API_PORT = 8000
API_URL = f"http://localhost:{API_PORT}"

# Search settings
DEFAULT_TOP_K = 10
SIMILARITY_THRESHOLD = 0.6

# UI settings
UI_TITLE = "Find My Fund - Smart Mutual Fund Search"
UI_DESCRIPTION = "Ask natural language questions to find the perfect mutual fund"
UI_THEME = "soft"  # Options: default, soft, glass, monochrome
UI_SHARE = True  # Set to True to create a public link

# Vector search settings
INDEX_TYPE = "faiss"  # Options: faiss

# Rule engine settings
MIN_RULE_MATCH_SCORE = 1  # Minimum rule match score to include in results

# Demo mode settings
DEMO_MODE = True  # Use demo data if real data is not available
MIN_DEMO_FUNDS = 10  # Minimum number of demo funds to create 