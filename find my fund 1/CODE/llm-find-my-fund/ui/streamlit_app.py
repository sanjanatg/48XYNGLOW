import sys
import os
import json
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules from app directory
from app.search_engine import SearchEngine
from app.rules import RuleEngine
from app.utils import clean_query, extract_metadata
from app.metadata_parser import explain_results

# Set page configuration
st.set_page_config(
    page_title="Find My Fund - AI Mutual Fund Search",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "Find My Fund - AI Mutual Fund Search Engine"
    }
)

# Set dark theme with custom CSS
st.markdown("""
<style>
    /* Dark theme */
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #1a1c21;
    }
    
    /* Fund card styling */
    .fund-card {
        background-color: #1e293b;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 15px;
        border-left: 4px solid #3b82f6;
    }
    
    .fund-name {
        font-size: 20px;
        font-weight: bold;
        margin-bottom: 5px;
        color: #60a5fa;
    }
    
    .fund-amc {
        font-size: 14px;
        color: #94a3b8;
        margin-bottom: 10px;
    }
    
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 10px;
        margin-bottom: 15px;
    }
    
    .stat-box {
        background-color: #263449;
        padding: 10px;
        border-radius: 4px;
        text-align: center;
    }
    
    .stat-label {
        font-size: 12px;
        color: #94a3b8;
    }
    
    .stat-value {
        font-size: 16px;
        font-weight: bold;
    }
    
    .positive-returns {
        color: #10b981;
    }
    
    .negative-returns {
        color: #ef4444;
    }
    
    .high-risk {
        color: #f97316;
    }
    
    .moderate-risk {
        color: #facc15;
    }
    
    .low-risk {
        color: #10b981;
    }
    
    .fund-description {
        font-size: 14px;
        color: #cbd5e1;
        margin: 15px 0;
    }
    
    .explanation {
        background-color: #263449;
        border-radius: 4px;
        padding: 10px;
        font-style: italic;
        color: #94a3b8;
        margin-top: 10px;
    }
    
    /* Search box styling */
    .stTextInput > div > div > input {
        background-color: #1e293b;
        color: #fff;
        border: 1px solid #3b82f6;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: #3b82f6;
        color: white;
        border: none;
        padding: 10px 24px;
        font-weight: 600;
    }
    
    .stButton > button:hover {
        background-color: #2563eb;
    }
    
    /* Heading styling */
    h1, h2, h3 {
        color: #60a5fa;
    }
    
    /* Radio button styling */
    .stRadio > div {
        background-color: #1e293b;
        padding: 10px;
        border-radius: 4px;
        margin-bottom: 10px;
    }
    
    /* Slider styling */
    .stSlider > div > div {
        background-color: #3b82f6;
    }
</style>
""", unsafe_allow_html=True)

# Initialize search engine and rule engine
@st.cache_resource
def load_search_engine():
    return SearchEngine()

@st.cache_resource
def load_rule_engine():
    return RuleEngine()

search_engine = load_search_engine()
rule_engine = load_rule_engine()

# Sample queries for the sidebar
SAMPLE_QUERIES = [
    "Show me tax saving ELSS funds with good returns",
    "I want a large cap fund with consistent returns",
    "Find a debt fund with low risk for short-term investment",
    "Which fund invests in technology companies?",
    "Show me small cap funds with high returns",
    "I need a hybrid fund for balanced investment"
]

# Format functions for display
def format_returns(value):
    """Format returns with color based on value"""
    try:
        value_float = float(value)
        if value_float > 0:
            return f"<span class='positive-returns'>+{value_float:.1f}%</span>"
        elif value_float < 0:
            return f"<span class='negative-returns'>{value_float:.1f}%</span>"
        else:
            return f"{value_float:.1f}%"
    except:
        return str(value)

def format_risk(risk):
    """Format risk level with appropriate color"""
    risk = risk.lower() if isinstance(risk, str) else str(risk).lower()
    if "high" in risk:
        return f"<span class='high-risk'>{risk.capitalize()}</span>"
    elif "moderate" in risk:
        return f"<span class='moderate-risk'>{risk.capitalize()}</span>"
    elif "low" in risk:
        return f"<span class='low-risk'>{risk.capitalize()}</span>"
    else:
        return risk.capitalize()

def create_returns_chart(fund):
    """Create a bar chart for fund returns"""
    returns = {
        '1 Year': fund.get('returns_1yr', 0),
        '3 Year': fund.get('returns_3yr', 0),
        '5 Year': fund.get('returns_5yr', 0)
    }
    
    colors = ['#3b82f6' if val >= 0 else '#ef4444' for val in returns.values()]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=list(returns.keys()),
        y=list(returns.values()),
        marker_color=colors,
        text=[f"{val:.1f}%" for val in returns.values()],
        textposition='auto'
    ))
    
    fig.update_layout(
        title="Returns Performance",
        title_font_color='#60a5fa',
        plot_bgcolor='#1e293b',
        paper_bgcolor='#1e293b',
        font=dict(color='#94a3b8'),
        height=200,
        margin=dict(l=10, r=10, t=40, b=20)
    )
    
    return fig

def create_fund_card(fund, index=None, explanation=None):
    """Create a UI card for a fund with all its details"""
    with st.container():
        # Create the header section
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"<h3 style='color:#60a5fa;margin-bottom:0'>#{index}: {fund.get('fund_name', 'Unnamed Fund')}</h3>", unsafe_allow_html=True)
            st.markdown(f"<p style='color:#94a3b8;margin-top:0'>{fund.get('amc', 'Unknown AMC')} | {fund.get('category', 'Uncategorized')}</p>", unsafe_allow_html=True)
        
        # Create the stats grid with columns for better layout
        col1, col2, col3 = st.columns(3)
        
        # 1Y Returns
        with col1:
            st.markdown("#### 1Y Returns")
            value = fund.get('returns_1yr', 'N/A')
            if isinstance(value, (int, float)):
                color = "#10b981" if value > 0 else "#ef4444"
                st.markdown(f"<h3 style='color:{color}'>{'+' if value > 0 else ''}{value:.1f}%</h3>", unsafe_allow_html=True)
            else:
                st.markdown(f"<h3>{value}</h3>", unsafe_allow_html=True)
                
        # 3Y Returns
        with col2:
            st.markdown("#### 3Y Returns")
            value = fund.get('returns_3yr', 'N/A')
            if isinstance(value, (int, float)):
                color = "#10b981" if value > 0 else "#ef4444"
                st.markdown(f"<h3 style='color:{color}'>{'+' if value > 0 else ''}{value:.1f}%</h3>", unsafe_allow_html=True)
            else:
                st.markdown(f"<h3>{value}</h3>", unsafe_allow_html=True)
                
        # 5Y Returns
        with col3:
            st.markdown("#### 5Y Returns")
            value = fund.get('returns_5yr', 'N/A')
            if isinstance(value, (int, float)):
                color = "#10b981" if value > 0 else "#ef4444"
                st.markdown(f"<h3 style='color:{color}'>{'+' if value > 0 else ''}{value:.1f}%</h3>", unsafe_allow_html=True)
            else:
                st.markdown(f"<h3>{value}</h3>", unsafe_allow_html=True)
        
        # Second row of stats
        col1, col2, col3 = st.columns(3)
        
        # Risk Level
        with col1:
            st.markdown("#### Risk Level")
            risk = fund.get('risk_level', 'N/A')
            if isinstance(risk, str):
                risk = risk.lower()
                if "high" in risk:
                    color = "#f97316"  # Orange
                elif "moderate" in risk:
                    color = "#facc15"  # Yellow
                elif "low" in risk:
                    color = "#10b981"  # Green
                else:
                    color = "#94a3b8"  # Default gray
                st.markdown(f"<h3 style='color:{color}'>{risk.capitalize()}</h3>", unsafe_allow_html=True)
            else:
                st.markdown(f"<h3>{risk}</h3>", unsafe_allow_html=True)
        
        # AUM
        with col2:
            st.markdown("#### AUM (₹ Cr)")
            aum = fund.get('aum_crore', 'N/A')
            st.markdown(f"<h3>{aum}</h3>", unsafe_allow_html=True)
        
        # Expense Ratio
        with col3:
            st.markdown("#### Expense Ratio")
            expense = fund.get('expense_ratio', 'N/A')
            if isinstance(expense, (int, float)):
                st.markdown(f"<h3>{expense:.2f}%</h3>", unsafe_allow_html=True)
            else:
                st.markdown(f"<h3>{expense}</h3>", unsafe_allow_html=True)
        
        # Description section
        st.markdown("### Description")
        st.markdown(f"{fund.get('description', 'No description available.')}")
        
        # Returns chart
        st.plotly_chart(create_returns_chart(fund), use_container_width=True)
        
        # Holdings section
        if fund.get('holdings'):
            with st.expander("Top Holdings"):
                holdings = fund.get('holdings', '').split(',')
                for holding in holdings:
                    st.markdown(f"- {holding.strip()}")
        
        # Explanation section
        if explanation:
            st.info(explanation)
        
        # Add divider after each fund card
        st.markdown("---")

def search_funds(query, num_results=5, search_type="hybrid"):
    """Search for funds based on user query"""
    if not query.strip():
        st.error("Please enter a valid query about mutual funds.")
        return []
    
    # Clean the query
    cleaned_query = clean_query(query)
    
    # Extract metadata filters
    metadata_filters = extract_metadata(cleaned_query)
    
    # Extract rule-based filters
    rule_filters = rule_engine.extract_filters(cleaned_query)
    
    # Combine all filters
    combined_filters = {**metadata_filters, **rule_filters}
    
    # Search for funds
    results = search_engine.search(cleaned_query, top_k=num_results, filters=combined_filters)
    
    return results

# Sidebar for app settings
with st.sidebar:
    st.title("Settings")
    
    # Data path setting
    st.subheader("Data Path")
    data_path = st.text_input("", "data/mutual_funds.csv")
    
    # Model directory setting
    st.subheader("Model Directory")
    model_dir = st.text_input("", "models")
    
    # Search type selection
    st.subheader("Search Type")
    search_type = st.selectbox("", 
                               options=["hybrid", "semantic", "lexical"], 
                               index=0)
    
    # Number of results slider
    st.subheader("Number of Results")
    num_results = st.slider("", min_value=1, max_value=20, value=5)
    
    # Force model retraining button
    st.button("Force Retrain Models")

# Main content
st.title("Find My Fund - AI Mutual Fund Search")

# App description
st.markdown("""
This app uses a hybrid search system (BM25 + Semantic Search) to find the most relevant mutual funds or 
securities based on your query. It understands ambiguous or partial fund names, and utilizes metadata to 
improve search quality.
""")

# Search input
query = st.text_input("Enter your search query", key="search_query", on_change=lambda: search_on_enter())

# Example queries
st.markdown("**Example queries:**")
example_cols = st.columns(3)
example_queries = ["SBI blue chip fund", "HDFC top 100", "ICICI multi-asset fund"]
for i, col in enumerate(example_cols):
    if i < len(example_queries):
        col.markdown(f"<span style='color: #3b82f6;'>{example_queries[i]}</span>", unsafe_allow_html=True)

# Function to search on Enter key
def search_on_enter():
    if "search_query" in st.session_state and st.session_state.search_query:
        st.session_state.should_search = True

# Initialize the session state for search flag
if "should_search" not in st.session_state:
    st.session_state.should_search = False

# Search button
search_button = st.button("Search")

# Execute search if button clicked or Enter pressed (via session state)
if search_button or st.session_state.should_search:
    if "search_query" in st.session_state and st.session_state.search_query:
        query = st.session_state.search_query
        with st.spinner("Searching for relevant funds..."):
            results = search_funds(query, num_results=num_results, search_type=search_type)
            
            if not results:
                st.error("No matching funds found. Please try a different query.")
            else:
                # Generate explanations for the results
                explanations = explain_results(query, results)
                
                # Show result count
                st.success(f"Found {len(results)} matching funds")
                
                # Display each fund
                for i, fund in enumerate(results):
                    explanation = explanations[i] if i < len(explanations) else None
                    create_fund_card(fund, index=i+1, explanation=explanation)
        
        # Reset the search flag
        st.session_state.should_search = False
    else:
        st.warning("Please enter a search query.")

# Sample queries in the sidebar
with st.sidebar:
    st.markdown("---")
    st.subheader("Sample Queries")
    for query in SAMPLE_QUERIES:
        if st.button(query, key=f"sample_{query}"):
            # Set the query in the main input and trigger search
            st.session_state.search_query = query
            st.experimental_rerun()

if __name__ == "__main__":
    # This will only run once when the app is loaded
    if "search_query" not in st.session_state:
        st.session_state.search_query = "" 