import os
import sys
import json
import pandas as pd
import streamlit as st
from pathlib import Path
from typing import List, Dict, Any
import asyncio
import nest_asyncio
import importlib.util
import traceback

# Add the project root to sys.path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Apply nest_asyncio to fix "no running event loop" error
try:
    nest_asyncio.apply()
except Exception as e:
    pass

# Fix for torch.__path__._path error - try to modify the attribute access method
try:
    import torch
    original_getattr = torch._classes.__getattr__
    
    def safe_getattr(self, attr):
        if attr == '__path__':
            return type('MockPath', (), {'_path': []})()
        return original_getattr(self, attr)
    
    torch._classes.__getattr__ = safe_getattr
except Exception as e:
    pass

# Try to import the search modules with additional error handling
engine_import_error = None
try:
    from src.core.search_engine import SearchEngine
except Exception as e:
    engine_import_error = str(e)
    st.error(f"Error importing SearchEngine: {str(e)}")

# Try to import the test_search module for fallback
test_search = None
try:
    # Import test_search.py module
    spec = importlib.util.spec_from_file_location("test_search", "test_search.py")
    test_search = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(test_search)
except Exception as e:
    pass

# Set page config
st.set_page_config(
    page_title="LLM, Find My Fund",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def load_search_engine(data_path: str, model_dir: str) -> SearchEngine:
    """
    Load the search engine (cached for better performance).
    
    Args:
        data_path: Path to the fund data
        model_dir: Directory containing saved models
        
    Returns:
        Initialized SearchEngine
    """
    if engine_import_error:
        return None
        
    # Ensure asyncio has a running event loop
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # Create a search engine object
    try:
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
            engine.load_models(directory=model_dir, data_path=processed_data_path)
        else:
            engine.fit(force_reload=True)
            
            # Save models for future use
            os.makedirs(model_dir, exist_ok=True)
            engine.save_models(directory=model_dir)
        
        return engine
    except Exception as e:
        st.error(f"Error loading search engine: {str(e)}")
        st.error("Please check the console for detailed error logs.")
        return None

def display_fund_card(result: Dict[str, Any], rank: int = 1) -> None:
    """
    Display a fund result as a nice card in Streamlit.
    
    Args:
        result: Fund result dictionary
        rank: Rank of the result
    """
    # Create a card-like container
    with st.container():
        # Header with fund name
        st.subheader(f"{rank}. {result['fund_name']}")
        
        # Two columns: one for metadata, one for scores
        col1, col2 = st.columns([3, 1])
        
        # Display metadata in the first column
        with col1:
            metadata_fields = ["fund_house", "category", "sub_category", "asset_class", "fund_type", "sector"]
            for field in metadata_fields:
                if field in result and result[field] not in ["unknown", "nan", "None", None]:
                    st.write(f"**{field.replace('_', ' ').title()}**: {result[field]}")
        
        # Display scores in the second column
        with col2:
            st.write("**Scores**")
            if "bm25_score" in result:
                st.write(f"Lexical: {result['bm25_score']:.4f}")
            if "semantic_score" in result:
                st.write(f"Semantic: {result['semantic_score']:.4f}")
            if "combined_score" in result:
                st.write(f"**Combined**: {result['combined_score']:.4f}")
        
        # Separator
        st.markdown("---")

def main():
    """Main Streamlit app function."""
    # App title and description
    st.title("LLM, Find My Fund 💰")
    st.markdown("""
    This app uses a hybrid search system (BM25 + Semantic Search) to find the most relevant 
    mutual funds or securities based on your query. It understands ambiguous or partial fund names,
    and utilizes metadata to improve search quality.
    """)
    
    # Sidebar for app settings
    st.sidebar.title("Settings")
    
    data_path = st.sidebar.text_input(
        "Data Path", 
        value="data/funds.csv",
        help="Path to the CSV file containing fund data"
    )
    
    model_dir = st.sidebar.text_input(
        "Model Directory", 
        value="models",
        help="Directory to save/load models"
    )
    
    search_type = st.sidebar.selectbox(
        "Search Type",
        options=["hybrid", "lexical", "semantic"],
        index=0,
        help="Hybrid combines lexical and semantic search for best results"
    )
    
    top_k = st.sidebar.slider(
        "Number of Results", 
        min_value=1, 
        max_value=20, 
        value=5,
        help="How many results to display"
    )
    
    # Fallback mode switch
    use_fallback = st.sidebar.checkbox("Use Fallback Mode", value=False, 
                                        help="Use a simplified search when the main engine fails")
    
    # Force retrain button
    retrain = st.sidebar.button("Force Retrain Models")
    
    # Try to load the search engine with error handling
    engine = None
    error_message = None
    
    if not use_fallback:
        try:
            # Attempt to load through the cached function first
            engine = load_search_engine(data_path, model_dir)
            
            # If that fails, try direct initialization as a fallback
            if engine is None and engine_import_error is None:
                st.warning("Using fallback method to load search engine...")
                engine = SearchEngine(data_path=data_path)
                engine.load_models(directory=model_dir, data_path=os.path.join(model_dir, "processed_funds.csv"))
        except Exception as e:
            error_message = str(e)
            st.error(f"Error loading search engine: {error_message}")
    
    # Search interface
    query = st.text_input("Enter your search query", placeholder="e.g., ICICI prudential technology fund")
    
    # Example queries
    st.markdown("**Example queries:** `SBI blue chip fund`, `HDFC top 100`, `ICICI multi-asset fund`")
    
    # Search button
    search_button = st.button("Search", type="primary")
    
    # Perform search when button is clicked and query is not empty
    if search_button and query:
        # Track if search was successful
        search_success = False
        
        # Try using the main engine first
        if engine is not None and not use_fallback:
            try:
                with st.spinner(f"Searching for: {query}..."):
                    results = engine.search(query, top_k=top_k, search_type=search_type)
                
                # Display results
                if not results:
                    st.warning("No matching funds found.")
                else:
                    st.success(f"Found {len(results)} matching funds")
                    
                    # Display results
                    for i, result in enumerate(results, 1):
                        display_fund_card(result, i)
                
                search_success = True
            except Exception as e:
                st.error(f"Error performing search with main engine: {str(e)}")
                st.error("Falling back to alternative search method...")
                traceback.print_exc()
        
        # If main engine search failed or we're using fallback mode, try the test_search fallback
        if (not search_success or use_fallback) and test_search is not None:
            try:
                with st.spinner(f"Searching with fallback method: {query}..."):
                    results = test_search.run_search(query, top_k=top_k, search_type=search_type)
                
                if results:
                    st.success(f"Found {len(results)} matching funds using fallback search")
                    search_success = True
            except Exception as e:
                st.error(f"Error with fallback search: {str(e)}")
            
        # If all else fails, try loading the data directly and doing a basic search
        if not search_success:
            try:
                with st.spinner("Loading data for basic search..."):
                    df = pd.read_csv(data_path)
                    
                    # Very basic substring search
                    query_lower = query.lower()
                    matches = df[df['fund_name'].str.lower().str.contains(query_lower)]
                    
                    if not matches.empty:
                        st.success(f"Found {len(matches)} basic matches")
                        
                        for i, (_, row) in enumerate(matches.iterrows(), 1):
                            with st.container():
                                st.subheader(f"{i}. {row['fund_name']}")
                                
                                col1, col2 = st.columns([3, 1])
                                
                                with col1:
                                    metadata_fields = ["fund_house", "category", "sub_category", "asset_class", "fund_type", "sector"]
                                    for field in metadata_fields:
                                        if field in row and pd.notna(row[field]) and row[field] not in ["unknown", "nan", "None", None]:
                                            st.write(f"**{field.replace('_', ' ').title()}**: {row[field]}")
                                
                                st.markdown("---")
                    else:
                        st.warning("No matches found with basic search.")
            except Exception as e:
                st.error(f"All search methods failed: {str(e)}")
    
    # Information about the search engine
    with st.expander("About this Search Engine"):
        st.markdown("""
        ### How it works
        
        This search engine uses a hybrid approach combining:
        
        1. **BM25 Lexical Search**: For exact keyword matching (similar to what databases use)
        2. **Semantic Search**: Using sentence transformers and HNSW for approximate nearest neighbor search
        3. **Metadata Boosting**: Utilizes fund metadata (category, fund house, etc.) to improve results
        
        The search results are ranked using a weighted combination of lexical and semantic scores.
        """)

if __name__ == "__main__":
    main() 