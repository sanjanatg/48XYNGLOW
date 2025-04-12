import os
import sys
import pandas as pd
import streamlit as st
from pathlib import Path
from typing import List, Dict, Any
from rank_bm25 import BM25Okapi
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string

# Add the project root to sys.path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Download NLTK resources if needed
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

# Set page config
st.set_page_config(
    page_title="LLM, Find My Fund (Simple Version)",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="expanded"
)

def preprocess_text(text):
    """Preprocess text for BM25 search"""
    if not isinstance(text, str):
        return []
    # Convert to lowercase
    text = text.lower()
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    # Tokenize
    tokens = word_tokenize(text)
    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if word not in stop_words]
    return tokens

def load_fund_data(data_path):
    """Load and preprocess fund data"""
    try:
        df = pd.read_csv(data_path)
        # Combine text fields for better search
        df['combined_text'] = df['fund_name'] + ' ' + df['fund_house'] + ' ' + df['category'] + ' ' + df['sub_category']
        # Preprocess for BM25
        df['tokenized_text'] = df['combined_text'].apply(preprocess_text)
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

def search_funds(query, funds_df, num_results=5):
    """Perform BM25 search on funds"""
    # Create BM25 model
    corpus = funds_df['tokenized_text'].tolist()
    bm25 = BM25Okapi(corpus)
    
    # Preprocess query
    tokenized_query = preprocess_text(query)
    
    # Get scores
    doc_scores = bm25.get_scores(tokenized_query)
    
    # Combine scores with fund data
    results_with_scores = list(zip(funds_df.index, doc_scores))
    
    # Sort by score
    sorted_results = sorted(results_with_scores, key=lambda x: x[1], reverse=True)
    
    # Get top results
    top_indices = [idx for idx, score in sorted_results[:num_results] if score > 0]
    
    if not top_indices:
        return []
    
    # Get fund data for top results
    results = []
    for i, idx in enumerate(top_indices):
        fund = funds_df.iloc[idx].to_dict()
        fund['score'] = sorted_results[i][1]
        results.append(fund)
    
    return results

def display_fund_card(result, rank=1):
    """Display fund result as a card"""
    with st.container():
        st.subheader(f"{rank}. {result['fund_name']}")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            metadata_fields = ["fund_house", "category", "sub_category", "asset_class", "fund_type", "sector"]
            for field in metadata_fields:
                if field in result and pd.notna(result[field]) and result[field] not in ["unknown", "nan", "None", None]:
                    st.write(f"**{field.replace('_', ' ').title()}**: {result[field]}")
        
        with col2:
            st.write("**Score**")
            st.write(f"{result['score']:.4f}")
        
        st.markdown("---")

def main():
    """Main function"""
    st.title("LLM, Find My Fund (Simple Version) 💰")
    st.markdown("""
    This is a simplified version of the fund search app. It uses basic BM25 search
    to find mutual funds based on your query.
    """)
    
    # Sidebar
    st.sidebar.title("Settings")
    
    data_path = st.sidebar.text_input(
        "Data Path", 
        value="data/funds.csv",
        help="Path to the fund data CSV file"
    )
    
    num_results = st.sidebar.slider(
        "Number of Results",
        min_value=1,
        max_value=20,
        value=5
    )
    
    # Load data
    funds_df = load_fund_data(data_path)
    
    if funds_df is not None:
        # Search interface
        query = st.text_input("Enter your search query", placeholder="e.g., ICICI prudential technology fund")
        
        # Example queries
        st.markdown("**Example queries:** `SBI blue chip fund`, `HDFC top 100`, `ICICI multi-asset fund`")
        
        # Search button
        search_button = st.button("Search", type="primary")
        
        if search_button and query:
            with st.spinner(f"Searching for: {query}..."):
                results = search_funds(query, funds_df, num_results)
            
            if not results:
                st.warning("No matching funds found.")
            else:
                st.success(f"Found {len(results)} matching funds")
                
                for i, result in enumerate(results, 1):
                    display_fund_card(result, i)
    else:
        st.error(f"Could not load data from {data_path}. Please check the file path and format.")

if __name__ == "__main__":
    main() 