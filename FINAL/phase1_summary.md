# Phase 1: Data Preprocessing

## Overview
In Phase 1, we've implemented the data preprocessing pipeline for the mutual fund search engine. The goal is to clean, transform, and enrich the raw mutual fund data to make it suitable for semantic search and retrieval.

## Implementation Details

### Data Loading
We load multiple datasets to create a complete picture of the mutual fund landscape:
- `mutual_funds_data.json`: Core mutual fund information (name, AMC, category, returns, etc.)
- `stock_data.json`: Details about individual stocks and securities
- `mf_holdings_data.json`: Holdings information (which stocks each fund holds)
- `queries_data.csv`: Sample queries for testing

### Data Enrichment
The preprocessing pipeline enriches the basic fund data with additional information:

1. **Linking Holdings to Funds**:
   - For each fund, we identify its top holdings
   - We map stock IDs to company names for better readability
   - We calculate holding percentages for portfolio composition

2. **Sector Allocation**:
   - We calculate sector allocation percentages for each fund
   - We map stocks to their respective sectors
   - We identify the top sectors for each fund

3. **Text Normalization**:
   - Fund names are normalized to handle variations
   - Text fields are cleaned and standardized 
   - AMC names are standardized to upper case

### Natural Language Description Generation
A key output of the preprocessing is a natural language description for each fund:

```python
def generate_fund_descriptions(mf_df, fund_holdings, fund_sectors):
    """Generate natural language descriptions for each fund"""
    # ...
    for _, fund in tqdm(mf_df.iterrows(), total=len(mf_df), desc="Creating descriptions"):
        # Basic fund info
        fund_id = fund.get('fund_id', '')
        fund_name = fund.get('fund_name', '')
        amc = fund.get('amc', '')
        category = fund.get('category', '')
        
        # Create description parts
        desc_parts = []
        
        # Fund name and type
        desc_parts.append(f"{fund_name} is a {category.lower()} fund managed by {amc}.")
        
        # Returns, risk level, holdings, sectors info...
        
        # Combine all parts
        description = " ".join(desc_parts)
        
        descriptions.append({
            'fund_id': fund_id,
            'fund_name': fund_name,
            'description': description
        })
```

These descriptions form the basis for vector search in later phases.

### Output Files
The preprocessing phase generates several key output files:

1. `fund_descriptions.csv`: Contains fund IDs, names, and natural language descriptions
2. `fund_corpus.txt`: A text file with all fund descriptions (one per line)
3. `enriched_fund_data.csv`: Complete fund data with added holdings and sector information
4. `preprocessed_funds.json`: JSON format of the enriched fund data for easy loading

## Bug Fixes and Improvements

During code review, we identified and fixed several issues in the data preprocessing phase:

1. **Path Configuration Issues**:
   - **Issue**: Hard-coded paths in data_preprocessing.py could fail on different environments
   - **Fix**: Updated to use utils.get_data_paths() and utils.get_output_paths() for consistent path handling

2. **Missing Output Files**:
   - **Issue**: The script wasn't consistently generating all required output files
   - **Fix**: Added explicit code to generate and save:
     - fund_corpus.txt (one description per line)
     - preprocessed_funds.json (complete fund data in JSON format)

3. **Data Type Errors**:
   - **Issue**: Potential errors when handling numeric values in fund data
   - **Fix**: Added proper type checking and safe conversion for numeric fields

4. **Error Handling**:
   - **Issue**: Insufficient error handling when processing data
   - **Fix**: Added try/except blocks with informative error messages

5. **Fund Data Enrichment**:
   - **Issue**: Incomplete enrichment of fund data with holdings and sector information
   - **Fix**: Improved the enrichment process to include more detailed information:
     ```python
     # Create a dictionary of enriched fund data
     enriched_funds = {}
     for _, fund in mf_df.iterrows():
         fund_id = fund["fund_id"]
         fund_dict = fund.to_dict()
         
         # Add holdings data
         if fund_id in fund_holdings:
             top_holdings = fund_holdings[fund_id]
             fund_dict["top_holdings"] = [holding[2] for holding in top_holdings[:10]]
         
         # Add sector allocation data
         if fund_id in fund_sectors:
             sectors = fund_sectors[fund_id]
             sector_list = sorted(sectors.items(), key=lambda x: x[1], reverse=True)
             fund_dict["sector_allocation"] = sector_list[:5]
         
         enriched_funds[fund_id] = fund_dict
     ```

These improvements make the data preprocessing more robust, ensuring that all required data is properly processed and saved for subsequent phases.

## Benefits of this Approach

1. **Rich Context**: The natural language descriptions provide rich context for semantic search
2. **Data Integration**: The preprocessing links disparate data sources into a cohesive whole
3. **Standardization**: Data fields are standardized for consistent processing
4. **Enrichment**: Basic fund data is enriched with holdings and sector information

## Usage

To run the data preprocessing:
```
python FINAL/data_preprocessing.py
```

To test the preprocessing with a small sample:
```
python FINAL/data_preprocessing_test.py
``` 