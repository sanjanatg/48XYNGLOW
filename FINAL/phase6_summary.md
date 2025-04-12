# Phase 6: Prompt Engineering for RAG

## Overview
In Phase 6, we've implemented Retrieval-Augmented Generation (RAG) prompt engineering for the mutual fund search engine. The goal is to create structured prompts for the LLM that incorporate the most relevant fund information to improve the quality and relevance of responses.

## Implementation Details

### RAG Prompt Template
We've implemented the following template for RAG:

```python
prompt = f"""
You are a mutual fund advisor. A user asked: "{user_query}".

Here are top matching funds:
{context_fund_1}
{context_fund_2}
{context_fund_3}

Which one is the best match? Explain why in 3 sentences.
"""
```

This template combines:
1. A role-based instruction that sets the context ("You are a mutual fund advisor")
2. The original user query
3. Relevant fund information as context (top 3 matches from search)
4. A specific task with a defined format (recommendation in 3 sentences)

### Enhanced Retrieval Component
We've extended the `EnhancedRetrieval` class with a new `generate_rag_prompt` method that:
- Takes a user query and search results as input
- Extracts the top 3 funds from the results
- Formats each fund's information in a structured way
- Builds the final prompt using the template

The fund information includes key attributes like:
- Fund name
- AMC (Asset Management Company)
- Category
- Risk level
- Returns (1yr, 3yr, 5yr)
- Expense ratio
- Investment objective

### RAG Demo Script
We've created a dedicated `run_rag_demo.py` script for testing the RAG implementation:
- It initializes all necessary components (search engine, LLM interface, enhanced retrieval)
- Provides an interactive CLI interface for users to enter queries
- Searches for relevant funds based on user queries
- Generates RAG prompts using the enhanced retrieval component
- Sends the prompts to the LLM (via llama.cpp) and displays the responses
- Offers a "show prompt" feature for debugging the generated prompts

## Bug Fixes and Improvements

During code review, we identified and fixed several issues to make the RAG implementation more robust:

1. **Enhanced Error Handling**:
   - Added comprehensive error handling in the `run_rag_demo.py` script
   - Implemented try/except blocks around all critical operations
   - Added proper error messages and user feedback

2. **Data Validation**:
   - Added validation of fund data in the `generate_rag_prompt` method
   - Implemented safe access to fund data fields with proper default values
   - Added type checking for numeric fields like returns and expense ratio

3. **LLM Response Format Validation**:
   - Added validation of the LLM response format in the `generate_rag_response` method
   - Implemented error handling for unexpected response formats
   - Added fallback responses when the LLM returns errors

4. **Improved User Experience**:
   - Added better error messages and user feedback in the RAG demo
   - Enhanced the display of fund information in the RAG prompt
   - Created a simpler version (`simple_rag.py`) with more robust error handling

These improvements make the RAG implementation more reliable, user-friendly, and robust against unexpected errors.

## Benefits of this Approach

1. **Structured Information**: The LLM receives well-structured, consistent information about each fund
2. **Focused Responses**: By asking for 3 sentences, we encourage concise, to-the-point recommendations
3. **Context-Aware**: The LLM can make recommendations based on specific fund attributes
4. **Transparency**: Users can see which funds were considered by the system

## Usage

To run the RAG demo:
```
python FINAL/run_rag_demo.py
```

Sample queries to try:
- "Which fund is best for long-term retirement savings?"
- "I'm looking for a low-risk debt fund with good returns"
- "Recommend a tax-saving fund with high growth potential"
- "Which fund has the best 5-year performance?"

To view the generated prompt, include "show prompt" in your query.

## Future Improvements

1. Fine-tune the prompt template based on user feedback
2. Add more structured context about fund performance
3. Implement multiple prompt templates for different query types
4. Add comparative analysis for similar funds
5. Include market context and trend information in the prompts 