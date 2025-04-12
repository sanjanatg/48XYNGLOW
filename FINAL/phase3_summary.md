# Phase 3: Smart Query Parsing

## Overview

In this phase, we implemented a natural language query parser that extracts structured filters from user queries. This enhances the search functionality by enabling more precise and relevant search results.

The query parser uses a combination of techniques:
1. Rule-based pattern matching
2. Keyword dictionaries
3. Regular expressions for numeric values
4. Abbreviation and synonym handling

## Key Components

### Query Parser

The core of this phase is the `QueryParser` class that:

1. **Parses natural language**: Extracts structured information from free-form text
2. **Handles domain-specific terms**: Recognizes financial terms, fund types, and AMC names
3. **Detects numeric constraints**: Identifies return expectations and expense ratio limits
4. **Normalizes terminology**: Maps synonyms and abbreviations to standard terminology
5. **Explains filters**: Generates human-readable explanations of extracted parameters

### Dictionary-Based Extraction

We've implemented several specialized dictionaries:

- **AMC Dictionary**: Maps various ways users might refer to asset management companies
  - Example: "sbi", "SBI Mutual Fund" → "SBI"

- **Risk Level Dictionary**: Identifies risk preferences
  - Example: "low risk", "conservative" → "Low"

- **Category Dictionary**: Maps fund category mentions
  - Example: "large cap", "large-cap" → "Large Cap"

- **Sector Dictionary**: Identifies sector preferences with synonym handling
  - Example: "tech", "technology", "IT" → "Technology"

### Pattern-Based Extraction

Advanced regular expressions capture:

- **Performance requirements**: "3-year returns above 15%"
- **Expense ratio constraints**: "expense ratio less than 1%"
- **Investment horizons**: "for short term", "long term investment"

## Integration with Search Engine

The query parser has been integrated with the search engine:

1. When a user submits a query, it first passes through the query parser
2. Extracted filters are applied to refine search results
3. The system provides a human-readable explanation of the applied filters
4. Results are ranked based on both semantic relevance and filter criteria

## Benefits

1. **Improved Precision**: Combines semantic search with structured filters
2. **Enhanced User Experience**: Users can express complex search criteria naturally
3. **Transparency**: Explains how the query was interpreted
4. **Flexibility**: Handles various ways users might express the same intent
5. **Domain-Specific Understanding**: Recognizes financial terminology and abbreviations

## Example Transformations

1. "Show me SBI funds with low risk"
   ```json
   {
     "amc": "SBI",
     "risk_level": "Low"
   }
   ```

2. "I want a large cap fund with 3-year returns above 15%"
   ```json
   {
     "category": "Large Cap",
     "min_return_3yr": 15.0
   }
   ```

3. "HDFC mutual funds with moderate risk in banking sector"
   ```json
   {
     "amc": "HDFC",
     "risk_level": "Moderate",
     "sector": "Financial Services"
   }
   ```

4. "Find infrastructure funds with returns over 12%"
   ```json
   {
     "sector": "Infrastructure",
     "min_return_3yr": 12.0
   }
   ```

## Future Enhancements

1. **Machine Learning Integration**: Train a model on query-filter pairs
2. **Contextual Understanding**: Improve handling of complex queries with multiple constraints
3. **Spelling Correction**: Add fuzzy matching for misspelled terms
4. **Query Expansion**: Expand queries with related terms from a domain ontology
5. **Personalization**: Adjust parsing based on user preferences and history

This phase significantly enhances the search experience by bringing together the best of both worlds: the natural language interface that users prefer and the structured filtering that produces precise results.

## Bug Fixes and Improvements

During code review, we identified and fixed several issues in the search engine implementation phase:

1. **Path Configuration Issues**:
   - **Issue**: Hard-coded file paths in the `MutualFundSearchEngine.__init__` method that could fail on different environments
   - **Fix**: Updated to use the utils.get_output_paths() function for consistent path handling:
     ```python
     # Get paths from utils if not provided
     output_paths = utils.get_output_paths()
     if embeddings_path is None:
         embeddings_path = output_paths["fund_embeddings"]
     if index_path is None:
         index_path = output_paths["faiss_index"]
     # ... and so on
     ```

2. **Error Handling in Search Engine Initialization**:
   - **Issue**: Insufficient error handling when initializing critical components
   - **Fix**: Added comprehensive try/except blocks with informative error messages:
     ```python
     try:
         logger.info(f"Loading embedding model: {model_name}")
         self.model = SentenceTransformer(model_name)
     except Exception as e:
         logger.error(f"Failed to load embedding model: {str(e)}")
         raise
     ```

3. **Fund Description Generation Issues**:
   - **Issue**: The generate_fund_description method could fail with missing or inconsistent data
   - **Fix**: Implemented safe data access patterns with proper defaults:
     ```python
     description = f"{fund_data.get('fund_name', 'This fund')} is a {fund_data.get('category', '').lower()} "
     description += f"fund from {fund_data.get('fund_house', '')}. "
     ```

4. **Search Result Consistency**:
   - **Issue**: Inconsistent search result format across different search methods
   - **Fix**: Standardized the search result format with consistent field names and types:
     ```python
     results.append({
         'fund_id': fund_id,
         'similarity': float(similarity),
         'rank': i + 1,
         'fund_data': fund_data,
         'description': description,
         'fund_name': fund_data.get('fund_name', 'Unknown'),
         'category': fund_data.get('category', 'Unknown'),
         'amc': fund_data.get('amc', 'Unknown'),
         'risk_level': fund_data.get('risk_level', 'Unknown'),
         'score': float(similarity)
     })
     ```

5. **Logging Improvements**:
   - **Issue**: Inconsistent and insufficient logging across the search process
   - **Fix**: Added consistent logging with appropriate log levels:
     ```python
     logger.info(f"Searching for query: {query}")
     # ...
     logger.info(f"Found {len(results)} results for query")
     ```

These improvements make the search engine implementation more robust, with better error handling, consistent result formats, and improved logging. The changes help ensure that the search engine functions reliably even when dealing with unexpected inputs or data inconsistencies. 