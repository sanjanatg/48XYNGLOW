import os
import numpy as np
import pandas as pd
import json
import faiss
import time
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import utils

# Configuration
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"  # Alternatively: "sentence-transformers/all-MiniLM-L6-v2"
USE_BM25_FALLBACK = True  # Whether to create BM25 index as fallback

def load_data():
    """Load the preprocessed data"""
    # Get paths
    output_paths = utils.get_output_paths()
    
    # Check if descriptions file exists
    if not os.path.exists(output_paths["fund_corpus"]):
        raise FileNotFoundError(f"Fund corpus file not found at {output_paths['fund_corpus']}. "
                               "Please run data_preprocessing.py first.")
    
    # Load fund descriptions
    with open(output_paths["fund_corpus"], "r", encoding="utf-8") as f:
        descriptions = f.read().splitlines()
    
    # Load fund mapping
    fund_df = pd.read_csv(output_paths["fund_descriptions"])
    
    print(f"Loaded {len(descriptions)} fund descriptions")
    return descriptions, fund_df

def load_or_create_embeddings(descriptions):
    """Load existing embeddings or create new ones"""
    output_paths = utils.get_output_paths()
    embeddings_path = output_paths["fund_embeddings"]
    
    # Check if embeddings already exist
    if os.path.exists(embeddings_path):
        print(f"Loading existing embeddings from {embeddings_path}")
        embeddings = np.load(embeddings_path)
        return embeddings
    
    # Load model
    print(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    
    # Generate embeddings
    print(f"Generating embeddings for {len(descriptions)} descriptions")
    start_time = time.time()
    
    # Batch process to save memory
    batch_size = 32
    embeddings = []
    
    for i in tqdm(range(0, len(descriptions), batch_size)):
        batch = descriptions[i:i+batch_size]
        batch_embeddings = model.encode(batch, show_progress_bar=False)
        embeddings.append(batch_embeddings)
    
    # Combine batches
    embeddings = np.vstack(embeddings)
    
    # Save embeddings
    os.makedirs(os.path.dirname(embeddings_path), exist_ok=True)
    np.save(embeddings_path, embeddings)
    
    elapsed_time = time.time() - start_time
    print(f"Generated {len(embeddings)} embeddings in {elapsed_time:.2f} seconds")
    print(f"Embeddings shape: {embeddings.shape}")
    print(f"Saved embeddings to {embeddings_path}")
    
    return embeddings

def create_faiss_index(embeddings):
    """Create a FAISS index for the embeddings"""
    output_paths = utils.get_output_paths()
    index_path = output_paths["faiss_index"]
    
    # Check index dimensions
    dimension = embeddings.shape[1]
    print(f"Creating FAISS index with dimension {dimension}")
    
    # Normalize embeddings for cosine similarity
    faiss.normalize_L2(embeddings)
    
    # Create index (using inner product for cosine similarity)
    index = faiss.IndexFlatIP(dimension)
    
    # Alternative: Use HNSW index for better performance
    # index = faiss.IndexHNSWFlat(dimension, 32)  # 32 neighbors
    
    # Add vectors to index
    index.add(embeddings)
    print(f"Added {index.ntotal} vectors to index")
    
    # Save index
    faiss.write_index(index, str(index_path))
    print(f"Saved FAISS index to {index_path}")
    
    return index

def create_bm25_index(descriptions):
    """Create a BM25 index for keyword-based fallback search"""
    # Tokenize descriptions
    tokenized_corpus = [utils.clean_text(doc).split() for doc in descriptions]
    
    # Create BM25 index
    bm25_index = BM25Okapi(tokenized_corpus)
    print(f"Created BM25 index with {len(tokenized_corpus)} documents")
    
    return bm25_index

def test_search(index, embeddings, fund_df, descriptions, bm25_index=None):
    """Test the search functionality with a few queries"""
    # Load embedding model for queries
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    
    # Test queries
    test_queries = [
        "tax saving funds with high returns",
        "low risk debt funds for short term investment",
        "funds that invest in technology companies",
        "hdfc mid cap fund",
        "sbi mutual fund with exposure to banking sector"
    ]
    
    print("\n=== Testing Search ===")
    for query in test_queries:
        print(f"\nQuery: {query}")
        
        # Embed query
        query_embedding = model.encode([query])[0]
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        query_embedding = np.array([query_embedding], dtype=np.float32)
        
        # Search in FAISS
        k = 3  # top-k results
        distances, indices = index.search(query_embedding, k)
        
        print(f"Top {k} semantic search results:")
        for i, (idx, distance) in enumerate(zip(indices[0], distances[0])):
            fund_name = fund_df.iloc[idx]['fund_name'] if idx < len(fund_df) else "Unknown"
            print(f"{i+1}. {fund_name} (Score: {distance:.4f})")
            print(f"   {descriptions[idx][:150]}...")
        
        # BM25 fallback
        if bm25_index is not None:
            tokenized_query = utils.clean_text(query).split()
            bm25_scores = bm25_index.get_scores(tokenized_query)
            top_bm25 = np.argsort(bm25_scores)[-k:][::-1]
            
            print(f"\nTop {k} keyword search results:")
            for i, idx in enumerate(top_bm25):
                fund_name = fund_df.iloc[idx]['fund_name'] if idx < len(fund_df) else "Unknown"
                print(f"{i+1}. {fund_name} (Score: {bm25_scores[idx]:.4f})")
                print(f"   {descriptions[idx][:150]}...")

def main():
    # Load preprocessed data
    descriptions, fund_df = load_data()
    
    # Generate or load embeddings
    embeddings = load_or_create_embeddings(descriptions)
    
    # Create FAISS index
    index = create_faiss_index(embeddings)
    
    # Create BM25 index (optional)
    bm25_index = None
    if USE_BM25_FALLBACK:
        bm25_index = create_bm25_index(descriptions)
    
    # Create and save fund_id_to_index mapping
    output_paths = utils.get_output_paths()
    fund_id_to_index = {row['fund_id']: str(i) for i, row in fund_df.iterrows()}
    
    # Save the mapping
    with open(output_paths["fund_id_to_index"], 'w') as f:
        json.dump(fund_id_to_index, f)
    print(f"Saved fund_id_to_index mapping to {output_paths['fund_id_to_index']}")
    
    # Test search
    test_search(index, embeddings, fund_df, descriptions, bm25_index)
    
    print("\nEmbedding and indexing complete!")
    print("You can now use search_engine.py to perform searches.")

if __name__ == "__main__":
    main() 