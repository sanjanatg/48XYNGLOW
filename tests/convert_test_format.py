#!/usr/bin/env python
"""
Convert different test formats to the standard JSON format for Find My Fund tests.

This script can handle:
1. Tab/CSV delimited text files
2. Python dictionaries/lists in .py files
3. JSON files with different structures
"""

import json
import os
import sys
import csv
import re
import argparse
from typing import List, Dict, Any, Optional

def convert_csv_tsv(input_file: str, output_file: str, has_header: bool = True, 
                    query_col: int = 0, expected_col: Optional[int] = 1, 
                    delimiter: str = '\t') -> None:
    """
    Convert a CSV/TSV file to the standard JSON format.
    
    Args:
        input_file: Path to input CSV/TSV file
        output_file: Path to output JSON file
        has_header: Whether the input file has a header row
        query_col: Column index for query (0-based)
        expected_col: Column index for expected fund (0-based), None if not available
        delimiter: Field delimiter ('\t' for TSV, ',' for CSV)
    """
    test_cases = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=delimiter)
        
        # Skip header if needed
        if has_header:
            next(reader, None)
        
        for row in reader:
            if not row or len(row) <= query_col:
                continue
                
            test_case = {"query": row[query_col].strip()}
            
            if expected_col is not None and len(row) > expected_col and row[expected_col].strip():
                test_case["expected_fund"] = row[expected_col].strip()
                
            test_cases.append(test_case)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(test_cases, f, indent=2)
    
    print(f"Converted {len(test_cases)} test cases to {output_file}")

def convert_python_format(input_file: str, output_file: str, var_name: Optional[str] = None) -> None:
    """
    Extract test cases from a Python file.
    
    Args:
        input_file: Path to input Python file
        output_file: Path to output JSON file
        var_name: Name of the variable containing test cases, if None will try to find automatically
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to extract the variable containing test cases
        if var_name:
            pattern = fr'{var_name}\s*=\s*(\[[\s\S]*?\])'
            matches = re.findall(pattern, content)
            if not matches:
                print(f"Error: Could not find variable '{var_name}' in {input_file}")
                return
            test_data_str = matches[0]
        else:
            # Try to find list definitions that look like test cases
            pattern = r'(\w+)\s*=\s*(\[[\s\S]*?\])'
            matches = re.findall(pattern, content)
            
            if not matches:
                print(f"Error: Could not find any list variables in {input_file}")
                return
            
            # Look for list variables that contain dictionaries with 'query' keys
            test_data_str = None
            for var, data_str in matches:
                if "'query'" in data_str or '"query"' in data_str:
                    var_name = var
                    test_data_str = data_str
                    break
            
            if not test_data_str:
                print(f"Error: Could not find test cases with 'query' field in {input_file}")
                return
        
        # Convert the Python list literal to JSON format
        # Replace Python True/False/None with JSON true/false/null
        json_str = test_data_str.replace("True", "true").replace("False", "false").replace("None", "null")
        # Replace Python-style quotes with JSON-style quotes
        json_str = re.sub(r"'([^']*)':", r'"\1":', json_str)  # Replace keys
        json_str = re.sub(r":\s*'([^']*)'", r': "\1"', json_str)  # Replace string values
        
        try:
            test_cases = json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"Error converting Python format to JSON: {e}")
            print("This might be due to complex Python structures that can't be easily converted.")
            print("Try simplifying the Python data structure or use a different approach.")
            return
        
        # Convert to our expected format
        standard_cases = []
        for i, case in enumerate(test_cases):
            if not isinstance(case, dict):
                print(f"Warning: Skipping non-dictionary test case at index {i}")
                continue
                
            if "query" not in case:
                print(f"Warning: Skipping test case at index {i} without 'query' field")
                continue
                
            standard_case = {"query": case["query"]}
            
            if "expected_fund" in case:
                standard_case["expected_fund"] = case["expected_fund"]
            elif "expected" in case:
                standard_case["expected_fund"] = case["expected"]
            
            standard_cases.append(standard_case)
        
        if not standard_cases:
            print(f"Warning: No valid test cases found in {input_file}")
            return
            
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(standard_cases, f, indent=2)
        
        print(f"Converted {len(standard_cases)} test cases to {output_file}")
        
    except Exception as e:
        print(f"Error processing file {input_file}: {str(e)}")
        import traceback
        traceback.print_exc()

def convert_json_format(input_file: str, output_file: str, 
                        query_key: str = "query", expected_key: Optional[str] = "expected_fund") -> None:
    """
    Convert a JSON file with a different structure to our standard format.
    
    Args:
        input_file: Path to input JSON file
        output_file: Path to output JSON file
        query_key: Key for the query field in the input
        expected_key: Key for the expected fund field in the input, None if not available
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error loading JSON: {e}")
        return
    
    standard_cases = []
    
    # Handle different JSON structures
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and query_key in item:
                case = {"query": item[query_key]}
                
                if expected_key and expected_key in item:
                    case["expected_fund"] = item[expected_key]
                    
                standard_cases.append(case)
    elif isinstance(data, dict):
        # Handle case where data is a dict with test cases as values
        for key, item in data.items():
            if isinstance(item, dict) and query_key in item:
                case = {"query": item[query_key]}
                
                if expected_key and expected_key in item:
                    case["expected_fund"] = item[expected_key]
                    
                standard_cases.append(case)
    
    if not standard_cases:
        print(f"Error: Could not find test cases with '{query_key}' field in {input_file}")
        return
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(standard_cases, f, indent=2)
    
    print(f"Converted {len(standard_cases)} test cases to {output_file}")

def detect_and_convert(input_file: str, output_file: str) -> None:
    """
    Automatically detect file format and convert to standard format.
    
    Args:
        input_file: Path to input file
        output_file: Path to output JSON file
    """
    _, ext = os.path.splitext(input_file.lower())
    
    if ext == '.json':
        print(f"Detected JSON format for {input_file}")
        convert_json_format(input_file, output_file)
    elif ext == '.py':
        print(f"Detected Python format for {input_file}")
        convert_python_format(input_file, output_file)
    elif ext == '.csv':
        print(f"Detected CSV format for {input_file}")
        convert_csv_tsv(input_file, output_file, delimiter=',')
    elif ext == '.tsv':
        print(f"Detected TSV format for {input_file}")
        convert_csv_tsv(input_file, output_file, delimiter='\t')
    elif ext == '.txt':
        # Try to detect format based on content
        with open(input_file, 'r', encoding='utf-8') as f:
            sample = f.read(1000)
        
        if '\t' in sample:
            print(f"Detected tab-delimited format for {input_file}")
            convert_csv_tsv(input_file, output_file, delimiter='\t')
        elif ',' in sample:
            print(f"Detected comma-delimited format for {input_file}")
            convert_csv_tsv(input_file, output_file, delimiter=',')
        else:
            print(f"Detected line-by-line query format for {input_file}")
            # Treat each line as a query with no expected results
            with open(input_file, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
            
            test_cases = [{"query": line} for line in lines]
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(test_cases, f, indent=2)
            
            print(f"Converted {len(test_cases)} test cases to {output_file}")
    else:
        print(f"Error: Unsupported file format for {input_file}")

def main():
    parser = argparse.ArgumentParser(description='Convert test files to standard JSON format for Find My Fund tests')
    parser.add_argument('input_file', help='Path to input test file')
    parser.add_argument('-o', '--output', help='Path to output JSON file (default: input file base name + _converted.json)')
    parser.add_argument('-t', '--type', choices=['json', 'python', 'csv', 'tsv', 'text', 'auto'], 
                      default='auto', help='Input file format (default: auto-detect)')
    parser.add_argument('--query-key', default='query', help='Key for query field in input (for JSON/Python)')
    parser.add_argument('--expected-key', default='expected_fund', help='Key for expected fund field in input (for JSON/Python)')
    parser.add_argument('--query-col', type=int, default=0, help='Column index for query (0-based, for CSV/TSV)')
    parser.add_argument('--expected-col', type=int, default=1, help='Column index for expected fund (0-based, for CSV/TSV)')
    parser.add_argument('--var-name', help='Variable name containing test cases (for Python)')
    parser.add_argument('--no-header', action='store_true', help='Input CSV/TSV has no header row')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        print(f"Error: Input file {args.input_file} does not exist")
        return
    
    if not args.output:
        base, _ = os.path.splitext(args.input_file)
        args.output = f"{base}_converted.json"
    
    if args.type == 'auto':
        detect_and_convert(args.input_file, args.output)
    elif args.type == 'json':
        convert_json_format(args.input_file, args.output, args.query_key, args.expected_key)
    elif args.type == 'python':
        convert_python_format(args.input_file, args.output, args.var_name)
    elif args.type in ['csv', 'tsv']:
        delimiter = ',' if args.type == 'csv' else '\t'
        convert_csv_tsv(args.input_file, args.output, not args.no_header, 
                       args.query_col, args.expected_col, delimiter)
    elif args.type == 'text':
        # Treat each line as a query with no expected results
        with open(args.input_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        
        test_cases = [{"query": line} for line in lines]
        
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(test_cases, f, indent=2)
        
        print(f"Converted {len(test_cases)} test cases to {args.output}")

if __name__ == "__main__":
    main() 