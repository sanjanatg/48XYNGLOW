import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_lottie import st_lottie
import json

# Configure the page
st.set_page_config(
    page_title="Find My Fund",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "# Fund Search App\nPowered by RAG + Mistral 7B"
    }
)

# API Endpoints
API_BASE = "http://localhost:5000/api"
SEARCH_ENDPOINT = f"{API_BASE}/search"
ANALYZE_ENDPOINT = f"{API_BASE}/analyze"
HEALTH_ENDPOINT = f"{API_BASE}/health"

# Custom CSS for dark theme
st.markdown("""
<style>
    .main {
        background-color: #121212;
        color: white;
    }
    .stApp {
        background-color: #121212;
    }
    .st-bw {
        background-color: #1E1E1E;
    }
    .st-cx {
        background-color: #1E1E1E;
    }
    .st-c0 {
        background-color: #2E2E2E;
    }
    .st-emotion-cache-16txtl3 {
        background-color: #1E1E1E;
    }
    h1, h2, h3 {
        color: white;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #2E2E2E;
        border-radius: 4px 4px 0px 0px;
        padding: 10px 20px;
        color: white;
    }
    .stTabs [aria-selected="true"] {
        background-color: #6E48AA;
    }
    div[data-testid="stForm"] {
        border: 1px solid #6E48AA;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    div[data-testid="stVerticalBlock"] > div[style] {
        background-color: #1E1E1E;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .fund-card {
        border: 1px solid #333;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        background-color: #1E1E1E;
    }
    .fund-card-matched {
        border-left: 4px solid #4CAF50;
    }
    .fund-card-neutral {
        border-left: 4px solid #2196F3;
    }
    .fund-card-low-match {
        border-left: 4px solid #F44336;
    }
    .stButton>button {
        background-color: #6E48AA;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        background-color: #8E68CA;
    }
    .gradient-text {
        background: linear-gradient(90deg, #6E48AA, #9755D3);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
    }
    .subtitle {
        color: #AAA;
        font-size: 1.2rem;
    }
    /* Adjust the search input box */
    div[data-baseweb="input"] {
        border-radius: 8px;
    }
    div[data-baseweb="input"] > div {
        background-color: #2E2E2E;
    }
    </style>
""", unsafe_allow_html=True)

# Check API availability
@st.cache_data(ttl=5)  # Cache for 5 seconds
def check_api_health():
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=2)
        return response.status_code == 200 and response.json().get('status') == 'ok'
    except:
        return False

# Show a loading animation
def load_lottie_url(url: str):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

# Search for funds
def search_funds(query, top_k=5):
    try:
        response = requests.post(
            SEARCH_ENDPOINT, 
            json={"query": query, "top_k": top_k},
            timeout=10
        )
        return response.json()
    except Exception as e:
        st.error(f"Error while searching: {str(e)}")
        return {"success": False, "results": [], "llm_response": ""}

# Analyze a fund
def analyze_fund(fund_id):
    try:
        response = requests.post(
            ANALYZE_ENDPOINT, 
            json={"fundId": fund_id},
            timeout=10
        )
        return response.json()
    except Exception as e:
        st.error(f"Error while analyzing fund: {str(e)}")
        return {"success": False}

# Get score color
def get_score_color(score):
    try:
        score_val = float(score)
        if score_val >= 0.8:
            return "fund-card-matched"
        elif score_val >= 0.5:
            return "fund-card-neutral"
        else:
            return "fund-card-low-match"
    except:
        return ""

# Header
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    st.markdown("<h1 style='text-align: center;'><span class='gradient-text'>Find My Fund</span></h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle' style='text-align: center;'>Intelligent fund search powered by RAG + Mistral 7B</p>", unsafe_allow_html=True)

# Check API availability
api_available = check_api_health()
if not api_available:
    st.warning("⚠️ API server is not available. Please start the API server with `python api_server.py`")

# Search form
with st.form(key="search_form"):
    col1, col2 = st.columns([4, 1])
    with col1:
        query = st.text_input(
            "Search for funds",
            placeholder="Try queries like 'low risk tech fund' or 'debt fund with high returns'",
            key="search_query"
        )
    with col2:
        top_k = st.selectbox("Results to show", [3, 5, 10, 15], index=1)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        search_button = st.form_submit_button("🔍 Search")

# Process search 
if search_button and query and api_available:
    with st.spinner("Searching for funds..."):
        response = search_funds(query, top_k)
        
    if response.get("success", False) or response.get("results"):
        # Show LLM response if available
        llm_response = response.get("llm_response", "")
        if llm_response:
            st.info(f"💡 **AI Recommendation:**\n\n{llm_response}")
        
        # Show results
        st.markdown(f"### Search Results for \"{query}\"")
        results = response.get("results", [])
        
        if results:
            st.write(f"Found {len(results)} matching funds")
            
            # Create columns for the grid layout
            cols = st.columns(2)
            
            # Display funds in a grid
            for i, fund in enumerate(results):
                col_idx = i % 2
                
                # Determine card style based on match score
                card_class = ""
                if fund.get("scoreExplanation"):
                    final_score = fund["scoreExplanation"].get("final", "0")
                    card_class = get_score_color(final_score)
                
                with cols[col_idx]:
                    with st.container():
                        st.markdown(f"<div class='fund-card {card_class}'>", unsafe_allow_html=True)
                        
                        # Fund title and basic info
                        st.markdown(f"#### {fund.get('name', 'Unknown Fund')}")
                        st.markdown(f"{fund.get('ticker', 'N/A')} • {fund.get('fundHouse', 'N/A')}")
                        
                        # Risk and category
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Risk:** {fund.get('risk', 'N/A')}")
                        with col2:
                            st.markdown(f"**Category:** {fund.get('category', 'N/A')}")
                        
                        # Returns
                        if "returns" in fund:
                            st.markdown("##### Returns")
                            ret_col1, ret_col2, ret_col3 = st.columns(3)
                            with ret_col1:
                                st.metric("1 Year", f"{fund['returns'].get('oneYear', 0)}%")
                            with ret_col2:
                                st.metric("3 Years", f"{fund['returns'].get('threeYear', 0)}%")
                            with ret_col3:
                                st.metric("5 Years", f"{fund['returns'].get('fiveYear', 0)}%")
                        
                        # Match scores if available
                        if fund.get("scoreExplanation"):
                            with st.expander("Match Scores"):
                                scores = fund["scoreExplanation"]
                                score_cols = st.columns(4)
                                with score_cols[0]:
                                    st.metric("Semantic", scores.get("semantic", "0"))
                                with score_cols[1]:
                                    st.metric("Metadata", scores.get("metadata", "0"))
                                with score_cols[2]:
                                    st.metric("Fuzzy", scores.get("fuzzy", "0"))
                                with score_cols[3]:
                                    st.metric("Final", scores.get("final", "0"))
                        
                        # View details button
                        if st.button(f"View Details", key=f"view_{fund.get('id', i)}"):
                            st.session_state.selected_fund = fund
                            st.session_state.show_analysis = True
                            st.experimental_rerun()
                            
                        st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.warning("No funds found matching your query. Try a different search term.")
    else:
        st.error("Failed to retrieve search results. Please try again.")

# Fund Analysis Section
if "selected_fund" in st.session_state and "show_analysis" in st.session_state and st.session_state.show_analysis:
    fund = st.session_state.selected_fund
    
    st.markdown("---")
    st.markdown(f"## Fund Analysis: {fund.get('name', 'Unknown Fund')}")
    
    with st.spinner("Loading fund analysis..."):
        analysis_data = analyze_fund(fund.get('id'))
    
    if analysis_data.get("success", False) or "analysis" in analysis_data:
        analysis = analysis_data.get("analysis", {})
        
        # Create tabs for different sections
        tab1, tab2, tab3 = st.tabs(["Overview", "Performance", "Allocation"])
        
        with tab1:
            # Summary
            st.markdown("### AI Analysis")
            st.write(analysis.get("summary", "No summary available."))
            
            # Strengths and Weaknesses
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### Strengths")
                for strength in analysis.get("strengths", ["No strengths data available"]):
                    st.markdown(f"✓ {strength}")
                    
            with col2:
                st.markdown("#### Weaknesses")
                for weakness in analysis.get("weaknesses", ["No weaknesses data available"]):
                    st.markdown(f"✗ {weakness}")
            
            # Risk Metrics
            st.markdown("#### Risk Metrics")
            if "riskMetrics" in analysis:
                metrics = analysis["riskMetrics"]
                metric_cols = st.columns(4)
                with metric_cols[0]:
                    st.metric("Sharpe Ratio", metrics.get("sharpeRatio", "N/A"))
                with metric_cols[1]:
                    st.metric("Standard Deviation", f"{metrics.get('standardDeviation', 'N/A')}%")
                with metric_cols[2]:
                    st.metric("Beta", metrics.get("beta", "N/A"))
                with metric_cols[3]:
                    st.metric("Alpha", metrics.get("alpha", "N/A"))
            else:
                st.info("Risk metrics data not available")
        
        with tab2:
            # Performance Chart
            st.markdown("### Performance Comparison")
            st.markdown("Fund performance vs. category average and benchmark")
            
            if "performance" in analysis:
                perf = analysis["performance"]
                # Prepare data for chart
                chart_data = []
                for period, values in perf.items():
                    period_name = period.replace("yr", " Year")
                    chart_data.append({
                        "Period": period_name,
                        "Fund": values.get("fund", 0),
                        "Category": values.get("category", 0),
                        "Benchmark": values.get("benchmark", 0)
                    })
                
                df = pd.DataFrame(chart_data)
                
                # Create and display chart
                fig = px.bar(
                    df, 
                    x="Period", 
                    y=["Fund", "Category", "Benchmark"],
                    barmode="group",
                    title="Returns Comparison (%)",
                    color_discrete_sequence=["#6E48AA", "#4CAF50", "#2196F3"]
                )
                
                fig.update_layout(
                    legend_title_text="",
                    plot_bgcolor="#1E1E1E",
                    paper_bgcolor="#1E1E1E",
                    font_color="white",
                    xaxis=dict(
                        title="",
                        titlefont_size=16,
                        tickfont_size=14,
                        gridcolor="#333333"
                    ),
                    yaxis=dict(
                        title="Returns (%)",
                        titlefont_size=16,
                        tickfont_size=14,
                        gridcolor="#333333"
                    ),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Performance data not available")
                
        with tab3:
            # Sector Allocation
            st.markdown("### Sector Allocation")
            st.markdown("Breakdown of fund allocation across sectors")
            
            if "sectorAllocation" in analysis and analysis["sectorAllocation"]:
                allocation = analysis["sectorAllocation"]
                
                # Create pie chart
                fig = px.pie(
                    names=[item.get("name", f"Sector {i}") for i, item in enumerate(allocation)],
                    values=[item.get("value", 0) for item in allocation],
                    title="Sector Allocation (%)",
                    color_discrete_sequence=px.colors.sequential.Plasma_r
                )
                
                fig.update_layout(
                    plot_bgcolor="#1E1E1E",
                    paper_bgcolor="#1E1E1E",
                    font_color="white"
                )
                
                fig.update_traces(
                    textposition='inside',
                    textinfo='percent+label'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sector allocation data not available")
        
        # Back button
        if st.button("← Back to Search Results"):
            st.session_state.show_analysis = False
            st.experimental_rerun()
    else:
        st.error("Failed to retrieve fund analysis. Please try again.")
        if st.button("← Back to Search Results"):
            st.session_state.show_analysis = False
            st.experimental_rerun()

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: #777777;'>Powered by RAG + Mistral 7B</p>", unsafe_allow_html=True) 