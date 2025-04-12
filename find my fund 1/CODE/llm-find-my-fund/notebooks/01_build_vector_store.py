"""
Build Vector Store for Mutual Fund Search

This script:
1. Loads the mutual fund dataset
2. Generates embeddings for fund names and descriptions using BGE-small-en model
3. Creates a FAISS index for similarity search
4. Saves the embeddings and index for later use
"""

import os
import pandas as pd
import numpy as np
import json
import pickle
import faiss
from tqdm import tqdm
from pathlib import Path
from sentence_transformers import SentenceTransformer

# Add parent directory to path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import config settings
from config import (
    FUNDS_DATA_PATH, EMBEDDINGS_PATH, MODEL_NAME,
    PROCESSED_DATA_DIR, VECTOR_DISTANCE, INDEX_PATH,
    METADATA_PATH
)

def load_data():
    """Load and preprocess mutual fund data."""
    # Check if the data file exists
    if not os.path.exists(FUNDS_DATA_PATH):
        print(f"No mutual fund data found at {FUNDS_DATA_PATH}. Using empty DataFrame.")
        return pd.DataFrame()
    
    # Load data
    df = pd.read_csv(FUNDS_DATA_PATH)
    
    if df.empty:
        print("No mutual fund data available. Cannot build vector store.")
        return df
    
    print(f"Loaded {len(df)} mutual funds.")
    return df

def create_search_texts(df):
    """Create search texts from fund data for better semantic matching."""
    search_texts = []
    
    for _, row in df.iterrows():
        # Combine fund name, category, and description to create a rich text for embedding
        text = f"{row['fund_name']} - {row['amc']} - {row['category']}. {row['description']}"
        search_texts.append(text)
    
    return search_texts

def generate_embeddings(texts, model_name=MODEL_NAME):
    """Generate embeddings for the given texts using the specified model."""
    print(f"Building vector store with {model_name}")
    
    # Initialize model
    model = SentenceTransformer(model_name)
    
    # Generate embeddings
    embeddings = model.encode(texts, show_progress_bar=True)
    
    return embeddings

def create_faiss_index(embeddings):
    """Create a FAISS index for the embeddings."""
    # Get number of dimensions
    d = embeddings.shape[1]
    
    # Create index
    if VECTOR_DISTANCE == "cosine":
        # Normalize vectors for cosine similarity
        faiss.normalize_L2(embeddings)
        index = faiss.IndexFlatIP(d)  # Inner product for cosine similarity with normalized vectors
    else:
        # L2 distance
        index = faiss.IndexFlatL2(d)
    
    # Add embeddings to index
    index.add(embeddings.astype(np.float32))
    
    return index

def create_metadata(df):
    """Create a metadata dictionary for each fund."""
    metadata = []
    
    for idx, row in df.iterrows():
        fund_meta = {
            'id': idx,
            'fund_name': row['fund_name'],
            'amc': row['amc'],
            'category': row['category'],
            'aum_crore': row['aum_crore'],
            'expense_ratio': row['expense_ratio'],
            'returns_1yr': row['returns_1yr'],
            'returns_3yr': row['returns_3yr'],
            'returns_5yr': row['returns_5yr'],
            'risk_level': row['risk_level'],
            'min_investment': row['min_investment'],
            'fund_age_years': row['fund_age_years'],
            'holdings': row['holdings'],
            'description': row['description']
        }
        metadata.append(fund_meta)
    
    return metadata

def save_artifacts(embeddings, index, metadata):
    """Save the embeddings, index, and metadata for later use."""
    # Save embeddings
    with open(EMBEDDINGS_PATH, 'wb') as f:
        pickle.dump(embeddings, f)
    
    # Save index
    with open(INDEX_PATH, 'wb') as f:
        pickle.dump(index, f)
    
    # Save metadata
    with open(METADATA_PATH, 'w') as f:
        json.dump(metadata, f)
    
    print(f"Saved artifacts to {PROCESSED_DATA_DIR}")

def main():
    # Load data
    df = load_data()
    
    if df.empty:
        return
    
    # Create search texts
    texts = create_search_texts(df)
    
    # Generate embeddings
    embeddings = generate_embeddings(texts)
    
    # Create FAISS index
    index = create_faiss_index(embeddings)
    
    # Create metadata
    metadata = create_metadata(df)
    
    # Save artifacts
    save_artifacts(embeddings, index, metadata)
    
    print("Vector store building completed successfully!")

if __name__ == "__main__":
    main() 