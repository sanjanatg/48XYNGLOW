# Phase 4: Enhanced Retrieval and Scoring

## Overview

In Phase 4, we implemented an advanced retrieval and scoring system that combines semantic search with metadata filtering and fuzzy matching. This approach ensures that search results are not only semantically relevant but also closely match the specific criteria mentioned in the user's query.

The new system uses a weighted scoring formula that balances three key factors:
```
final_score = 0.6 * semantic_similarity + 0.3 * metadata_match + 0.1 * fuzzy_score
```

## Key Components

### Enhanced Retrieval System

We've implemented the `EnhancedRetrieval` class with the following capabilities:

1. **Metadata Match Scoring**: Calculates how well a fund matches the user's specified criteria (AMC, risk level, category, returns, etc.)
2. **Fuzzy Match Scoring**: Uses RapidFuzz to find partial text matches between queries and fund details
3. **Combined Scoring**: Intelligently combines multiple scoring methods with appropriate weights
4. **BM25 Integration**: Adds keyword-based search results to complement semantic ones

### Weighted Metadata Scoring

Not all metadata matches are equally important. We've implemented a weighted system:

- AMC (fund house) matches have the highest weight (2.0)
- Category matches have a medium-high weight (1.5) 
- Risk level and sector matches have medium weight (1.2)
- Return criteria have a standard weight (1.0)
- Expense ratio has a slightly lower weight (0.8)

### Partial Matching for Numeric Criteria

Returns and expense ratio matches now support partial credit:

- For returns: If a fund has returns close to but slightly below the requested level (at least 80%), it receives partial score
- For expense ratio: If a fund has an expense ratio slightly above the requested level (up to 20% higher), it receives partial score

### Result Reranking

The search process now follows these steps:

1. Get initial candidates using semantic search (more than needed)
2. Apply metadata filters to narrow down candidates
3. Score candidates using the weighted formula
4. Sort by final score and return the top results

## Implementation Details

### Search Process

1. **Query Parsing**: Extract structured filters from natural language query
2. **Semantic Search**: Embed query and find similar fund descriptions using FAISS
3. **Metadata Filtering**: Apply hard filters to eliminate clearly irrelevant results
4. **Enhanced Scoring**:
   - Calculate semantic similarity score
   - Calculate metadata match score
   - Calculate fuzzy match score
   - Combine using weighted formula
5. **Result Ranking**: Order results by final score

### Technical Improvements

- **Increased Initial Candidates**: We now retrieve 3x more initial candidates to ensure good coverage after filtering
- **Normalized Scoring**: All component scores are normalized to 0.0-1.0 range for fair weighting
- **Score Explanation**: Results include a detailed breakdown of how the final score was calculated
- **Visualization**: The demo now shows comparative scoring across top results

## Benefits

1. **More Relevant Results**: Funds that match both semantic meaning and specific criteria rank higher
2. **Better Handling of Numeric Constraints**: Partial matches for returns and expense ratios provide more nuanced results
3. **Transparent Scoring**: Users can see why a particular fund was ranked higher than others
4. **Improved Recall**: The system can still find relevant funds even if they don't perfectly match all criteria
5. **Balanced Approach**: No single factor dominates the ranking, creating a more holistic relevance score

## Example Scenarios

### Example 1: "Show me SBI funds with low risk and good performance"

- Semantic similarity identifies funds that match the concepts of SBI, low risk, and performance
- Metadata matching ensures funds from SBI with low risk level rank higher
- Fuzzy matching helps match variations like "SBI Mutual Fund" or "State Bank of India"

### Example 2: "Find infrastructure funds with returns over 12% and low expense ratio"

- Semantic search finds funds related to infrastructure
- Metadata scoring boosts funds that have at least 12% returns and low expenses
- Funds that precisely match sector + returns + low expenses will rank highest

## Future Enhancements

1. **User Preference Learning**: Adjust weights based on user interaction patterns
2. **Advanced Numeric Handling**: More sophisticated handling of numeric ranges and comparisons
3. **Cross-Field Matching**: Better handling when a term could apply to multiple fields
4. **Query Expansion**: Expand sector terms to include related concepts
5. **Online Learning**: Update ranking model based on user feedback

## Bug Fixes and Improvements

During code review, we identified and fixed several issues in the query parsing and filtering phase:

1. **Incomplete filter_results Method**:
   - **Issue**: The filter_results method was incomplete and didn't handle all filter types properly
   - **Fix**: Completely rewrote the method to properly handle all filter types with appropriate error handling:
     ```python
     def filter_results(self, results, filters):
         """Apply filters to search results."""
         if not filters:
             return results
         
         filtered_results = []
         
         for result in results:
             fund_data = result.get('fund_data', {})
             include = True
             
             # Apply each filter
             for filter_key, filter_value in filters.items():
                 # Handle different types of filters
                 if filter_key == 'amc' and 'amc' in fund_data:
                     if fund_data['amc'].lower() != filter_value.lower():
                         include = False
                         break
                 # ... additional filter handling
         
         return filtered_results
     ```

2. **Query Parser Edge Cases**:
   - **Issue**: The query parser didn't handle certain edge cases like incomplete phrases or ambiguous terms
   - **Fix**: Enhanced the regex patterns and added more robust matching logic:
     ```python
     # Improved regex pattern for returns
     'min_return_3yr': re.compile(r'(3[\s-]*year|three[\s-]*year|3[\s-]*yr)[\s-]*(return|returns)[\s-]*(>|greater than|more than|above|at least|exceeding|over)[\s-]*(\d+\.?\d*)(%)?', re.IGNORECASE)
     ```

3. **Missing Metadata Filters**:
   - **Issue**: Some metadata filters weren't properly extracted from queries
   - **Fix**: Added support for additional filter types and improved the extraction logic:
     ```python
     def _extract_category(self, query: str) -> Dict[str, str]:
         """Extract fund category from query"""
         for key, value in self.category_dict.items():
             if key in query:
                 return {'category': value}
         
         # Special case for tax-saving funds
         if any(term in query for term in ['tax saving', 'tax-saving', 'tax benefit', 'tax saver']):
             return {'category': 'ELSS'}
             
         return {}
     ```

4. **Sector Matching Issues**:
   - **Issue**: Sector matching was too permissive, leading to false matches
   - **Fix**: Improved sector matching to require whole word matches for single-word sectors:
     ```python
     def _extract_sector(self, query: str) -> Dict[str, str]:
         """Extract sector focus from query"""
         # Split query into words
         words = query.split()
         
         for key, value in self.sector_dict.items():
             # For multi-word sector names
             if len(key.split()) > 1 and key in query:
                 return {'sector': value}
             # For single-word sector names, ensure it's a complete word
             elif len(key.split()) == 1 and any(word == key for word in words):
                 return {'sector': value}
     ```

5. **Numeric Constraint Validation**:
   - **Issue**: Numeric constraints (like min returns) weren't validated properly
   - **Fix**: Added validation to ensure numeric values are within reasonable bounds:
     ```python
     if matches:
         value = float(matches.group(4))
         # Ensure the value is reasonable (e.g., return between 0% and 100%)
         if 0 <= value <= 100:
             constraints[constraint_key] = value
     ```

These improvements make the query parsing and filtering more accurate and robust, ensuring that user queries are properly interpreted and the right filters are applied to search results. The changes help bridge the gap between natural language queries and structured data filtering.

This phase significantly enhances the search quality by creating a more balanced and nuanced approach to fund ranking, ensuring that results are both semantically relevant and match the specific criteria users care about. 