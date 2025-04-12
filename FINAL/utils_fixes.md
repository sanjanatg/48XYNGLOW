# Utils Module: Bug Fixes and Improvements

## Overview
This document details the bug fixes and improvements made to the `utils.py` module, which provides core utilities for path handling, data processing, and configuration management across the entire mutual fund search engine system.

## Issues Identified and Fixed

### 1. Path Configuration Issues
- **Issue**: Hard-coded paths that might fail on different environments or directory structures.
- **Fix**: Implemented dynamic path detection and resolution:
```python
# Project directories
PROJECT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
# Check if we're in the FINAL directory, and handle paths accordingly
if PROJECT_DIR.name == 'FINAL':
    DATA_DIR = PROJECT_DIR.parent / "datasets"
else:
    DATA_DIR = PROJECT_DIR / "datasets"
```

### 2. Missing Output Path for preprocessed_funds.json
- **Issue**: The `get_output_paths` function was missing the path to the preprocessed_funds.json file.
- **Fix**: Added the missing path to the output paths dictionary:
```python
def get_output_paths():
    """Return paths to output files"""
    return {
        "enriched_fund_data": PROCESSED_DIR / "enriched_fund_data.csv",
        "fund_descriptions": PROCESSED_DIR / "fund_descriptions.csv",
        "fund_corpus": PROCESSED_DIR / "fund_corpus.txt",
        "fund_embeddings": PROCESSED_DIR / "fund_embeddings.npy",
        "faiss_index": PROCESSED_DIR / "faiss_index.bin",
        "fund_id_to_index": PROCESSED_DIR / "fund_id_to_index.json",
        "preprocessed_funds": PROCESSED_DIR / "preprocessed_funds.json"  # Added missing path
    }
```

### 3. Error Handling for Missing Directories
- **Issue**: No error handling when data directories don't exist.
- **Fix**: Added code to handle missing directories gracefully:
```python
# Ensure data directory exists (if it doesn't, log a warning but don't fail)
if not os.path.exists(DATA_DIR):
    print(f"Warning: Data directory '{DATA_DIR}' does not exist. Creating it, but you need to add data files.")
    os.makedirs(DATA_DIR, exist_ok=True)
```

### 4. Type Safety in Utility Functions
- **Issue**: Potential errors when handling non-string inputs in text processing functions.
- **Fix**: Added type checking for inputs:
```python
def clean_text(text):
    """Clean and normalize text for better matching"""
    if not isinstance(text, str):
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove extra whitespace
    text = " ".join(text.split())
    
    return text
```

## Code Improvements

### Path Handling
Improved path handling with robust directory detection and creation:
```python
# Create processed and models directories within the project directory
PROCESSED_DIR = PROJECT_DIR / "processed_data"
MODELS_DIR = PROJECT_DIR / "models"

# Ensure directories exist
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)
```

### Data Loading
Enhanced the load_processed_data function with better error handling and logging:
```python
def load_processed_data():
    """Load preprocessed data"""
    output_paths = get_output_paths()
    
    data = {}
    
    # Load enriched fund data
    if os.path.exists(output_paths["enriched_fund_data"]):
        data["enriched_fund_data"] = pd.read_csv(output_paths["enriched_fund_data"])
        print(f"Loaded enriched fund data: {len(data['enriched_fund_data'])} funds")
    # ... additional loading code ...
    
    return data
```

### Type Safety
Added type safety for formatting functions:
```python
def format_percentage(value):
    """Format value as percentage"""
    if pd.isna(value):
        return "N/A"
    
    return f"{value:.2f}%"
```

## Impact

These improvements to the utils module provide:
1. More reliable path handling across different environments
2. Consistent access to all required file paths
3. Graceful handling of missing directories
4. Type-safe utility functions
5. Better logging and error reporting

Since the utils module is used throughout the entire codebase, these changes have a significant positive impact on the overall system reliability and maintainability. 