import os
import time
import numpy as np
import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer
import matplotlib.pyplot as plt
import utils
from embedding_indexing import load_data, load_or_create_embeddings, create_faiss_index, create_bm25_index, test_search

def test_embedding_accuracy():
    """Test the accuracy of the embeddings"""
    print("\n=== Testing Embedding Accuracy ===")
    
    # Load data
    descriptions, fund_df = load_data()
    
    # Load or create embeddings
    embeddings = load_or_create_embeddings(descriptions)
    
    # Create FAISS index
    index = create_faiss_index(embeddings)
    
    # Load embedding model
    print("Loading embedding model...")
    model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    
    # Test queries that should match specific kinds of funds
    test_cases = [
        {
            "query": "HDFC Mid Cap Opportunities Fund",
            "expected_matches": ["HDFC", "mid cap", "opportunities"]
        },
        {
            "query": "SBI Blue Chip Fund",
            "expected_matches": ["SBI", "blue chip", "large cap"]
        },
        {
            "query": "ICICI Prudential Technology Fund",
            "expected_matches": ["ICICI", "technology", "sector"]
        },
        {
            "query": "Tax saving ELSS fund",
            "expected_matches": ["ELSS", "tax", "saving"]
        },
        {
            "query": "Low risk debt fund",
            "expected_matches": ["debt", "low risk", "bond"]
        }
    ]
    
    success_count = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases):
        query = test_case["query"]
        expected_matches = test_case["expected_matches"]
        
        print(f"\nTest {i+1}: '{query}'")
        print(f"Expected matches: {', '.join(expected_matches)}")
        
        # Encode query
        query_embedding = model.encode([query])[0]
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        query_embedding = np.array([query_embedding], dtype=np.float32)
        
        # Search in FAISS
        k = 3  # top-k results
        distances, indices = index.search(query_embedding, k)
        
        # Check results
        success = False
        
        print("Top matches:")
        for j, (idx, distance) in enumerate(zip(indices[0], distances[0])):
            fund_name = fund_df.iloc[idx]['fund_name'] if idx < len(fund_df) else "Unknown"
            description = descriptions[idx][:150] + "..." if idx < len(descriptions) else "?"
            
            print(f"{j+1}. {fund_name} (Score: {distance:.4f})")
            print(f"   {description}")
            
            # Check if this match contains any of the expected terms
            match_text = (fund_name + " " + description).lower()
            matches_found = [term for term in expected_matches if term.lower() in match_text]
            
            if matches_found:
                success = True
                print(f"   ✓ Found matches: {', '.join(matches_found)}")
        
        if success:
            success_count += 1
            print("✅ Test passed!")
        else:
            print("❌ Test failed! No expected matches found in top results.")
    
    # Calculate overall accuracy
    accuracy = (success_count / total_tests) * 100
    print(f"\nOverall accuracy: {accuracy:.1f}% ({success_count}/{total_tests} tests passed)")
    
    return accuracy

def test_search_performance():
    """Test the search performance with various query types"""
    print("\n=== Testing Search Performance ===")
    
    # Load data
    descriptions, fund_df = load_data()
    
    # Load or create embeddings
    embeddings = load_or_create_embeddings(descriptions)
    
    # Create FAISS index
    index = create_faiss_index(embeddings)
    
    # Create BM25 index
    bm25_index = create_bm25_index(descriptions)
    
    # Test different types of queries
    query_types = [
        {
            "name": "Exact Fund Names",
            "queries": [
                "HDFC Top 100 Fund",
                "SBI Blue Chip Fund",
                "Axis Midcap Fund"
            ]
        },
        {
            "name": "Category Queries",
            "queries": [
                "tax saving funds",
                "debt funds with good returns",
                "liquid funds for short term"
            ]
        },
        {
            "name": "Complex Attribute Queries",
            "queries": [
                "low risk funds with exposure to banking sector",
                "high return large cap funds from HDFC",
                "funds investing in technology with moderate risk"
            ]
        }
    ]
    
    # Load embedding model
    print("Loading embedding model...")
    model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    
    # Test each query type
    for query_type in query_types:
        print(f"\n== Testing {query_type['name']} ==")
        
        total_time = 0
        top1_scores = []
        
        for query in query_type["queries"]:
            print(f"\nQuery: '{query}'")
            
            # Time the semantic search
            start_time = time.time()
            
            # Encode query
            query_embedding = model.encode([query])[0]
            query_embedding = query_embedding / np.linalg.norm(query_embedding)
            query_embedding = np.array([query_embedding], dtype=np.float32)
            
            # Search in FAISS
            k = 3  # top-k results
            distances, indices = index.search(query_embedding, k)
            
            end_time = time.time()
            search_time = end_time - start_time
            total_time += search_time
            
            # Save top1 score
            top1_scores.append(float(distances[0][0]))
            
            # Display results
            print(f"Search time: {search_time:.4f} seconds")
            print("Top matches:")
            for j, (idx, distance) in enumerate(zip(indices[0], distances[0])):
                fund_name = fund_df.iloc[idx]['fund_name'] if idx < len(fund_df) else "Unknown"
                print(f"{j+1}. {fund_name} (Score: {distance:.4f})")
                
                # Show part of the description
                if idx < len(descriptions):
                    print(f"   {descriptions[idx][:150]}...")
        
        # Report performance for this query type
        avg_time = total_time / len(query_type["queries"])
        avg_score = sum(top1_scores) / len(top1_scores)
        
        print(f"\nAverage search time: {avg_time:.4f} seconds")
        print(f"Average top-1 score: {avg_score:.4f}")
    
    # Compare with BM25 performance
    print("\n== BM25 vs Vector Search Comparison ==")
    
    # Pick one query from each type
    comparison_queries = [
        query_types[0]["queries"][0],  # Exact name query
        query_types[1]["queries"][0],  # Category query
        query_types[2]["queries"][0]   # Complex query
    ]
    
    for query in comparison_queries:
        print(f"\nQuery: '{query}'")
        
        # Vector search results
        query_embedding = model.encode([query])[0]
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        query_embedding = np.array([query_embedding], dtype=np.float32)
        v_distances, v_indices = index.search(query_embedding, 1)
        
        # BM25 search results
        tokenized_query = utils.clean_text(query).split()
        bm25_scores = bm25_index.get_scores(tokenized_query)
        top_bm25_idx = np.argmax(bm25_scores)
        
        # Compare results
        vector_result = fund_df.iloc[v_indices[0][0]]['fund_name'] if v_indices[0][0] < len(fund_df) else "Unknown"
        vector_score = float(v_distances[0][0])
        
        bm25_result = fund_df.iloc[top_bm25_idx]['fund_name'] if top_bm25_idx < len(fund_df) else "Unknown"
        bm25_score = float(bm25_scores[top_bm25_idx])
        
        print(f"Vector Search: {vector_result} (Score: {vector_score:.4f})")
        print(f"BM25 Search:   {bm25_result} (Score: {bm25_score:.4f})")
        
        # Check if they match
        if vector_result == bm25_result:
            print("✅ Both methods returned the same top result")
        else:
            print("⚠️ Different top results from vector vs keyword search")

def test_scaling():
    """Test the scaling of the embedding and indexing pipeline"""
    print("\n=== Testing Scaling ===")
    
    # Load data
    descriptions, fund_df = load_data()
    
    # Define sample sizes (10%, 25%, 50%, 75%, 100%)
    sample_sizes = [
        int(len(descriptions) * 0.1),
        int(len(descriptions) * 0.25),
        int(len(descriptions) * 0.5),
        int(len(descriptions) * 0.75),
        len(descriptions)
    ]
    
    embedding_times = []
    indexing_times = []
    memory_usages = []
    
    for size in sample_sizes:
        print(f"\nTesting with {size} descriptions ({size / len(descriptions) * 100:.1f}% of data)")
        
        # Sample the data
        sample_descriptions = descriptions[:size]
        
        # Time embedding generation
        start_time = time.time()
        
        # Load model
        model = SentenceTransformer("BAAI/bge-small-en-v1.5")
        
        # Generate embeddings in batches
        batch_size = 32
        embeddings = []
        
        for i in range(0, len(sample_descriptions), batch_size):
            batch = sample_descriptions[i:i+min(batch_size, len(sample_descriptions) - i)]
            batch_embeddings = model.encode(batch, show_progress_bar=False)
            embeddings.append(batch_embeddings)
        
        # Combine batches
        embeddings = np.vstack(embeddings)
        
        end_time = time.time()
        embedding_time = end_time - start_time
        embedding_times.append(embedding_time)
        
        print(f"Embedding time: {embedding_time:.2f} seconds for {size} descriptions")
        print(f"Embeddings shape: {embeddings.shape}")
        
        # Time index creation
        start_time = time.time()
        
        # Normalize embeddings
        normalized_embeddings = embeddings.copy()
        faiss.normalize_L2(normalized_embeddings)
        
        # Create index
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)
        index.add(normalized_embeddings)
        
        end_time = time.time()
        indexing_time = end_time - start_time
        indexing_times.append(indexing_time)
        
        print(f"Indexing time: {indexing_time:.2f} seconds for {size} descriptions")
        
        # Estimate memory usage (embeddings + index)
        # Each float32 is 4 bytes
        embedding_memory = embeddings.shape[0] * embeddings.shape[1] * 4 / (1024 * 1024)  # MB
        index_memory = embedding_memory * 1.1  # FAISS index is roughly 10% larger than embeddings
        total_memory = embedding_memory + index_memory
        memory_usages.append(total_memory)
        
        print(f"Estimated memory usage: {total_memory:.2f} MB")
    
    # Plot results
    plt.figure(figsize=(15, 10))
    
    # Embedding time plot
    plt.subplot(2, 2, 1)
    plt.plot(sample_sizes, embedding_times, marker='o')
    plt.title('Embedding Generation Time vs. Dataset Size')
    plt.xlabel('Number of Descriptions')
    plt.ylabel('Time (seconds)')
    plt.grid(True)
    
    # Indexing time plot
    plt.subplot(2, 2, 2)
    plt.plot(sample_sizes, indexing_times, marker='o', color='orange')
    plt.title('Indexing Time vs. Dataset Size')
    plt.xlabel('Number of Descriptions')
    plt.ylabel('Time (seconds)')
    plt.grid(True)
    
    # Memory usage plot
    plt.subplot(2, 2, 3)
    plt.plot(sample_sizes, memory_usages, marker='o', color='green')
    plt.title('Memory Usage vs. Dataset Size')
    plt.xlabel('Number of Descriptions')
    plt.ylabel('Memory (MB)')
    plt.grid(True)
    
    # Combined plot
    plt.subplot(2, 2, 4)
    plt.plot(sample_sizes, [t1 + t2 for t1, t2 in zip(embedding_times, indexing_times)], marker='o', color='purple')
    plt.title('Total Processing Time vs. Dataset Size')
    plt.xlabel('Number of Descriptions')
    plt.ylabel('Time (seconds)')
    plt.grid(True)
    
    plt.tight_layout()
    
    # Save the plot
    output_dir = utils.PROCESSED_DIR
    os.makedirs(output_dir, exist_ok=True)
    plot_path = os.path.join(output_dir, 'scaling_results.png')
    plt.savefig(plot_path)
    print(f"\nScaling results chart saved to {plot_path}")
    
    # Return the results
    return {
        'sample_sizes': sample_sizes,
        'embedding_times': embedding_times,
        'indexing_times': indexing_times,
        'memory_usages': memory_usages
    }

def main():
    print("Testing Phase 2: Embedding + Indexing")
    
    # Test embedding accuracy
    accuracy = test_embedding_accuracy()
    
    # Test search performance
    test_search_performance()
    
    # Test scaling
    scaling_results = test_scaling()
    
    print("\nAll tests completed!")
    print(f"Embedding accuracy: {accuracy:.1f}%")
    
    total_times = [t1 + t2 for t1, t2 in zip(scaling_results['embedding_times'], scaling_results['indexing_times'])]
    largest_size = scaling_results['sample_sizes'][-1]
    largest_time = total_times[-1]
    
    print(f"Processing time for full dataset ({largest_size} descriptions): {largest_time:.2f} seconds")
    print(f"Estimated memory usage: {scaling_results['memory_usages'][-1]:.2f} MB")

if __name__ == "__main__":
    main() 