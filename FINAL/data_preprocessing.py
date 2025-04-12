import os
import json
import pandas as pd
import numpy as np
from tqdm import tqdm
import utils

# Set paths to data files
DATA_DIR = "../datasets"
MF_DATA_PATH = os.path.join(DATA_DIR, "mutual_funds_data.json")
STOCK_DATA_PATH = os.path.join(DATA_DIR, "stock_data.json")
HOLDINGS_DATA_PATH = os.path.join(DATA_DIR, "mf_holdings_data.json")
QUERIES_PATH = os.path.join(DATA_DIR, "Dataset Queries-Securities for Model Creation.csv")

# Create a directory for processed data
PROCESSED_DIR = "processed_data"
os.makedirs(PROCESSED_DIR, exist_ok=True)

def load_data():
    """
    Load all datasets and return as pandas DataFrames
    """
    paths = utils.get_data_paths()
    
    print("Loading mutual funds data...")
    with open(paths["mf_data"], 'r') as f:
        mf_data = json.load(f)
    mf_df = pd.DataFrame(mf_data)
    
    print("Loading stock data...")
    with open(paths["stock_data"], 'r') as f:
        stock_data = json.load(f)
    stock_df = pd.DataFrame(stock_data)
    
    print("Loading holdings data...")
    with open(paths["holdings_data"], 'r') as f:
        holdings_data = json.load(f)
    holdings_df = pd.DataFrame(holdings_data)
    
    print("Loading query data...")
    queries_df = pd.read_csv(paths["queries_data"])
    
    print(f"Loaded {len(mf_df)} mutual funds, {len(stock_df)} stocks, {len(holdings_df)} holdings, and {len(queries_df)} queries.")
    
    return mf_df, stock_df, holdings_df, queries_df

def preprocess_funds(mf_df):
    """
    Preprocess mutual fund data
    """
    # Convert relevant columns to appropriate types
    numeric_cols = ['returns_1yr', 'returns_3yr', 'returns_5yr', 'expense_ratio', 'aum_crore', 'min_investment']
    for col in numeric_cols:
        if col in mf_df.columns:
            mf_df[col] = pd.to_numeric(mf_df[col], errors='coerce')
    
    # Ensure string columns are properly formatted
    string_cols = ['fund_name', 'amc', 'category', 'sub_category', 'risk_level']
    for col in string_cols:
        if col in mf_df.columns:
            mf_df[col] = mf_df[col].fillna('').astype(str)
            
    # Standardize AMC names to uppercase
    if 'amc' in mf_df.columns:
        mf_df['amc'] = mf_df['amc'].str.upper()
    
    # Normalize fund names
    if 'fund_name' in mf_df.columns:
        mf_df['normalized_name'] = mf_df['fund_name'].apply(utils.normalize_fund_name)
    
    return mf_df

def preprocess_stocks(stock_df):
    """
    Preprocess stock data
    """
    # Ensure company names are strings
    if 'company_name' in stock_df.columns:
        stock_df['company_name'] = stock_df['company_name'].fillna('').astype(str)
    
    # Standardize stock symbols to uppercase
    if 'stock_symbol' in stock_df.columns:
        stock_df['stock_symbol'] = stock_df['stock_symbol'].str.upper()
    
    return stock_df

def create_fund_holdings_map(mf_df, holdings_df, stock_df):
    """
    Create a mapping of fund_id to their holdings
    Returns a dictionary: {fund_id: [(stock_id, percentage, company_name), ...]}
    """
    print("Creating fund-holdings mapping...")
    fund_holdings = {}
    
    # Create a lookup for stock names
    stock_id_to_name = {}
    if 'stock_id' in stock_df.columns and 'company_name' in stock_df.columns:
        for _, row in stock_df.iterrows():
            stock_id_to_name[row['stock_id']] = row['company_name']
    
    # Group holdings by fund_id
    for fund_id, group in tqdm(holdings_df.groupby('fund_id'), desc="Processing funds"):
        # Sort by percentage (descending)
        sorted_holdings = group.sort_values('percentage', ascending=False)
        
        # Get top N holdings (or all if fewer)
        top_holdings = []
        for _, holding in sorted_holdings.iterrows():
            stock_id = holding['stock_id']
            percentage = holding['percentage']
            
            company_name = stock_id_to_name.get(stock_id, stock_id)
            top_holdings.append((stock_id, percentage, company_name))
        
        fund_holdings[fund_id] = top_holdings
    
    return fund_holdings

def create_fund_sector_map(holdings_df, stock_df):
    """
    Create a mapping of fund_id to their sector allocation
    Returns a dictionary: {fund_id: {sector: percentage, ...}}
    """
    print("Creating fund-sector mapping...")
    fund_sectors = {}
    
    # Create a lookup for stock sectors
    stock_id_to_sector = {}
    if 'stock_id' in stock_df.columns and 'sector' in stock_df.columns:
        for _, row in stock_df.iterrows():
            stock_id_to_sector[row['stock_id']] = row['sector']
    
    # Group holdings by fund_id
    for fund_id, group in tqdm(holdings_df.groupby('fund_id'), desc="Processing sectors"):
        sectors = {}
        
        for _, holding in group.iterrows():
            stock_id = holding['stock_id']
            percentage = holding['percentage']
            
            sector = stock_id_to_sector.get(stock_id, 'Unknown')
            sectors[sector] = sectors.get(sector, 0) + percentage
        
        fund_sectors[fund_id] = sectors
    
    return fund_sectors

def generate_fund_descriptions(mf_df, fund_holdings, fund_sectors):
    """
    Generate natural language descriptions for each fund
    """
    print("Generating fund descriptions...")
    descriptions = []
    
    for _, fund in tqdm(mf_df.iterrows(), total=len(mf_df), desc="Creating descriptions"):
        # Basic fund info
        fund_id = fund.get('fund_id', '')
        fund_name = fund.get('fund_name', '')
        amc = fund.get('amc', '')
        category = fund.get('category', '')
        sub_category = fund.get('sub_category', '')
        
        # Create description parts
        desc_parts = []
        
        # Fund name and type
        if fund_name and category:
            desc_parts.append(f"{fund_name} is a {sub_category.lower() if sub_category else ''} {category.lower()} fund managed by {amc}.")
        elif fund_name:
            desc_parts.append(f"{fund_name} is a mutual fund managed by {amc}.")
        
        # Returns info
        returns_info = []
        if 'returns_1yr' in fund and pd.notna(fund['returns_1yr']):
            returns_info.append(f"1-year return of {fund['returns_1yr']:.2f}%")
        if 'returns_3yr' in fund and pd.notna(fund['returns_3yr']):
            returns_info.append(f"3-year return of {fund['returns_3yr']:.2f}%")
        if 'returns_5yr' in fund and pd.notna(fund['returns_5yr']):
            returns_info.append(f"5-year return of {fund['returns_5yr']:.2f}%")
        
        if returns_info:
            desc_parts.append(f"It has a {', '.join(returns_info)}.")
        
        # Risk and expense ratio
        risk_expense = []
        if 'risk_level' in fund and fund['risk_level']:
            risk_expense.append(f"risk level is {fund['risk_level']}")
        if 'expense_ratio' in fund and pd.notna(fund['expense_ratio']):
            risk_expense.append(f"expense ratio is {fund['expense_ratio']:.2f}%")
        
        if risk_expense:
            desc_parts.append(f"Its {' and '.join(risk_expense)}.")
        
        # AUM info
        if 'aum_crore' in fund and pd.notna(fund['aum_crore']):
            desc_parts.append(f"The fund has an AUM of ₹{fund['aum_crore']:.2f} crore.")
        
        # Holdings info
        if fund_id in fund_holdings and fund_holdings[fund_id]:
            top_holdings = fund_holdings[fund_id][:5]  # Top 5 holdings
            companies = [h[2] for h in top_holdings]  # Get company names
            
            if companies:
                companies_text = ", ".join(companies[:-1]) + f" and {companies[-1]}" if len(companies) > 1 else companies[0]
                desc_parts.append(f"It holds stocks like {companies_text}.")
        
        # Sector allocation
        if fund_id in fund_sectors and fund_sectors[fund_id]:
            # Get top 3 sectors by allocation
            top_sectors = sorted(fund_sectors[fund_id].items(), key=lambda x: x[1], reverse=True)[:3]
            
            if top_sectors:
                sectors_text = ", ".join([f"{sector} ({percentage:.1f}%)" for sector, percentage in top_sectors])
                desc_parts.append(f"Its top sectors include {sectors_text}.")
        
        # Combine all parts
        description = " ".join(desc_parts)
        
        # Store description
        fund_entry = {
            'fund_id': fund_id,
            'fund_name': fund_name,
            'description': description
        }
        
        descriptions.append(fund_entry)
    
    return pd.DataFrame(descriptions)

def main():
    # Load all datasets
    mf_df, stock_df, holdings_df, queries_df = load_data()
    
    # Preprocess data
    mf_df = preprocess_funds(mf_df)
    stock_df = preprocess_stocks(stock_df)
    
    # Create mappings
    fund_holdings = create_fund_holdings_map(mf_df, holdings_df, stock_df)
    fund_sectors = create_fund_sector_map(holdings_df, stock_df)
    
    # Generate descriptions
    descriptions_df = generate_fund_descriptions(mf_df, fund_holdings, fund_sectors)
    
    # Get output paths
    output_paths = utils.get_output_paths()
    
    # Save processed data
    print("Saving processed data...")
    
    # Save fund descriptions
    descriptions_df.to_csv(output_paths["fund_descriptions"], index=False)
    print(f"Saved {len(descriptions_df)} fund descriptions to {output_paths['fund_descriptions']}")
    
    # Save fund corpus (one description per line)
    with open(output_paths["fund_corpus"], "w", encoding="utf-8") as f:
        f.write("\n".join(descriptions_df["description"].tolist()))
    print(f"Saved fund corpus to {output_paths['fund_corpus']}")
    
    # Create a dictionary of enriched fund data
    enriched_funds = {}
    for _, fund in mf_df.iterrows():
        fund_id = fund["fund_id"]
        fund_dict = fund.to_dict()
        
        # Add holdings data
        if fund_id in fund_holdings:
            top_holdings = fund_holdings[fund_id]
            fund_dict["top_holdings"] = [holding[2] for holding in top_holdings[:10]]  # Get top 10 company names
        
        # Add sector allocation data
        if fund_id in fund_sectors:
            sectors = fund_sectors[fund_id]
            # Convert to list of (sector, percentage) tuples, sorted by percentage
            sector_list = sorted(sectors.items(), key=lambda x: x[1], reverse=True)
            fund_dict["sector_allocation"] = sector_list[:5]  # Get top 5 sectors
        
        # Add the fund to the dictionary
        enriched_funds[fund_id] = fund_dict
    
    # Save enriched fund data as CSV
    enriched_df = pd.DataFrame(enriched_funds).T.reset_index().rename(columns={"index": "fund_id"})
    enriched_df.to_csv(output_paths["enriched_fund_data"], index=False)
    print(f"Saved enriched fund data to {output_paths['enriched_fund_data']}")
    
    # Save preprocessed funds as JSON
    with open(output_paths["preprocessed_funds"], "w") as f:
        json.dump(enriched_funds, f, indent=2)
    print(f"Saved preprocessed funds to {output_paths['preprocessed_funds']}")
    
    print("Data preprocessing complete!")

if __name__ == "__main__":
    main() 