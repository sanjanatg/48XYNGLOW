import sys
import os
import json
import gradio as gr
import pandas as pd
import numpy as np
import requests
from pathlib import Path
import markdown
import re

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules from app directory
from app.search_engine import SearchEngine
from app.rules import RuleEngine
from app.utils import clean_query, extract_metadata
from app.metadata_parser import explain_results

# Import config
from config import SAMPLE_QUERIES, THEME

# Initialize search engine and rule engine
search_engine = SearchEngine()
rule_engine = RuleEngine()

# CSS for dark theme
css = """
.dark-theme {
    background-color: #1a1c21;
    color: #ffffff;
}

.message-container {
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 10px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.user-message {
    background-color: #2d3748;
    margin-left: 20%;
    border-top-right-radius: 0;
}

.assistant-message {
    background-color: #38404e;
    margin-right: 20%;
    border-top-left-radius: 0;
}

.fund-card {
    background-color: #2d3748;
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 15px;
    border-left: 4px solid #4299e1;
    display: flex;
    flex-direction: column;
}

.fund-name {
    font-size: 18px;
    font-weight: bold;
    margin-bottom: 8px;
    color: #4299e1;
}

.fund-amc {
    font-size: 14px;
    color: #a0aec0;
    margin-bottom: 10px;
}

.fund-stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin-bottom: 10px;
}

.stat-item {
    display: flex;
    flex-direction: column;
}

.stat-label {
    font-size: 12px;
    color: #a0aec0;
}

.stat-value {
    font-size: 16px;
    font-weight: bold;
}

.positive-returns {
    color: #48bb78;
}

.negative-returns {
    color: #f56565;
}

.moderate-risk {
    color: #ecc94b;
}

.high-risk {
    color: #ed8936;
}

.low-risk {
    color: #48bb78;
}

.fund-description {
    font-size: 14px;
    line-height: 1.5;
    color: #e2e8f0;
    margin-top: 10px;
}

.explanation {
    font-style: italic;
    color: #a0aec0;
    border-top: 1px solid #4a5568;
    padding-top: 10px;
    margin-top: 10px;
}

/* Button styling */
.custom-button {
    background-color: #4299e1;
    color: white;
    border: none;
    padding: 10px 15px;
    border-radius: 5px;
    cursor: pointer;
    transition: background-color 0.3s;
}

.custom-button:hover {
    background-color: #3182ce;
}

/* Input styling */
.custom-input {
    background-color: #2d3748;
    color: #e2e8f0;
    border: 1px solid #4a5568;
    border-radius: 5px;
    padding: 10px;
}

.custom-input:focus {
    border-color: #4299e1;
    outline: none;
}

/* Heading styling */
.heading {
    color: #4299e1;
    font-size: 24px;
    font-weight: bold;
    margin-bottom: 20px;
    text-align: center;
}
"""

# Format returns with color based on value
def format_returns(value):
    try:
        value_float = float(value)
        if value_float > 0:
            return f"<span class='positive-returns'>+{value_float:.1f}%</span>"
        elif value_float < 0:
            return f"<span class='negative-returns'>{value_float:.1f}%</span>"
        else:
            return f"{value_float:.1f}%"
    except:
        return value

# Format risk level with color
def format_risk(risk):
    risk = risk.lower() if isinstance(risk, str) else str(risk).lower()
    if "high" in risk:
        return f"<span class='high-risk'>{risk.capitalize()}</span>"
    elif "moderate" in risk:
        return f"<span class='moderate-risk'>{risk.capitalize()}</span>"
    elif "low" in risk:
        return f"<span class='low-risk'>{risk.capitalize()}</span>"
    else:
        return risk.capitalize()

def generate_fund_card(fund):
    """Generate HTML for a fund card with styling"""
    returns_1yr = format_returns(fund.get('returns_1yr', 'N/A'))
    returns_3yr = format_returns(fund.get('returns_3yr', 'N/A'))
    returns_5yr = format_returns(fund.get('returns_5yr', 'N/A'))
    risk_level = format_risk(fund.get('risk_level', 'N/A'))
    
    card = f"""
    <div class="fund-card">
        <div class="fund-name">{fund.get('fund_name', 'Unnamed Fund')}</div>
        <div class="fund-amc">{fund.get('amc', 'Unknown AMC')} | {fund.get('category', 'Uncategorized')}</div>
        
        <div class="fund-stats">
            <div class="stat-item">
                <div class="stat-label">1Y Returns</div>
                <div class="stat-value">{returns_1yr}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">3Y Returns</div>
                <div class="stat-value">{returns_3yr}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">5Y Returns</div>
                <div class="stat-value">{returns_5yr}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">Risk Level</div>
                <div class="stat-value">{risk_level}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">AUM (₹ Cr)</div>
                <div class="stat-value">{fund.get('aum_crore', 'N/A')}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">Expense Ratio</div>
                <div class="stat-value">{fund.get('expense_ratio', 'N/A')}%</div>
            </div>
        </div>
        
        <div class="fund-description">
            {fund.get('description', 'No description available.')}
        </div>
    </div>
    """
    return card

def search_funds(query, chat_history):
    """Search for funds based on user query and update chat history"""
    if not query.strip():
        return chat_history + [[query, "Please enter a valid query about mutual funds."]]
    
    # Clean the query
    cleaned_query = clean_query(query)
    
    # Extract metadata filters
    metadata_filters = extract_metadata(cleaned_query)
    
    # Extract rule-based filters
    rule_filters = rule_engine.extract_filters(cleaned_query)
    
    # Combine all filters
    combined_filters = {**metadata_filters, **rule_filters}
    
    # Search for funds
    results = search_engine.search(cleaned_query, top_k=5, filters=combined_filters)
    
    if not results:
        return chat_history + [[query, "I couldn't find any mutual funds matching your criteria. Please try a different query."]]
    
    # Generate explanations for the results
    explanations = explain_results(query, results)
    
    # Generate HTML response with fund cards
    response = "<div class='assistant-content'>"
    
    # Add introduction text
    if len(results) == 1:
        response += f"<p>I found 1 mutual fund that matches your criteria:</p>"
    else:
        response += f"<p>I found {len(results)} mutual funds that match your criteria:</p>"
    
    # Add fund cards
    for i, fund in enumerate(results):
        response += generate_fund_card(fund)
        
        # Add explanation if available
        if i < len(explanations):
            response += f"<div class='explanation'>{explanations[i]}</div>"
    
    response += "</div>"
    
    return chat_history + [[query, response]]

def create_chatbot_interface():
    """Create the Gradio interface for the chatbot"""
    with gr.Blocks(css=css, theme=gr.themes.Soft(primary_hue="blue")) as demo:
        gr.HTML("""
        <div class="heading">
            Find My Fund - AI Mutual Fund Search
        </div>
        """)
        
        # Chat interface
        chatbot = gr.Chatbot(
            [],
            elem_id="chatbot",
            bubble_full_width=False,
            height=600,
            avatar_images=("👤", "🤖"),
        )
        
        # Input components
        with gr.Row():
            with gr.Column(scale=6):
                msg = gr.Textbox(
                    placeholder="Ask me about mutual funds in India...",
                    show_label=False,
                    container=False,
                    scale=6,
                )
            with gr.Column(scale=1):
                submit = gr.Button("Search", variant="primary")
        
        # Sample queries
        with gr.Accordion("Sample Queries", open=False):
            sample_query_buttons = []
            for i in range(0, len(SAMPLE_QUERIES), 2):
                with gr.Row():
                    for j in range(2):
                        if i + j < len(SAMPLE_QUERIES):
                            query = SAMPLE_QUERIES[i + j]
                            sample_button = gr.Button(query)
                            sample_button.click(
                                lambda q: q, 
                                inputs=[sample_button], 
                                outputs=[msg]
                            )
                            sample_query_buttons.append(sample_button)
        
        # Set up interactions
        msg.submit(search_funds, [msg, chatbot], [chatbot], queue=False).then(
            lambda: "", None, [msg], queue=False
        )
        submit.click(search_funds, [msg, chatbot], [chatbot], queue=False).then(
            lambda: "", None, [msg], queue=False
        )
        
        # Add some initial instructions
        gr.HTML("""
        <div style="text-align: center; margin-top: 20px; color: #a0aec0;">
            Ask questions about mutual funds in India. You can search by fund type, returns, risk level, or AMC.
        </div>
        """)
        
    return demo

if __name__ == "__main__":
    demo = create_chatbot_interface()
    demo.launch(share=False)