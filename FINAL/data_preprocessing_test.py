import os
import sys
import pandas as pd
import utils
from data_preprocessing import load_data, preprocess_funds, preprocess_stocks, generate_fund_descriptions, create_fund_holdings_map, create_fund_sector_map

def test_preprocessing_pipeline(sample_size=5):
    """
    Test the preprocessing pipeline with a small sample of data
    """
    print("Testing preprocessing pipeline...")
    
    try:
        # Load data
        print("\n1. Testing data loading...")
        mf_df, stock_df, holdings_df, queries_df = load_data()
        
        # Print info about loaded data
        print("\nMutual funds data shape:", mf_df.shape)
        print("Mutual funds columns:", mf_df.columns.tolist())
        print("\nStock data shape:", stock_df.shape)
        print("Stock data columns:", stock_df.columns.tolist())
        print("\nHoldings data shape:", holdings_df.shape)
        print("Holdings data columns:", holdings_df.columns.tolist())
        print("\nQueries data shape:", queries_df.shape)
        print("Queries data columns:", queries_df.columns.tolist())
        
        # Sample data for faster testing
        print(f"\n2. Sampling data for testing ({sample_size} items each)...")
        mf_df_sample = mf_df.head(sample_size)
        stock_df_sample = stock_df.head(sample_size)
        
        # Get only holdings for the sampled funds
        if 'fund_id' in mf_df.columns and 'fund_id' in holdings_df.columns:
            sample_fund_ids = mf_df_sample['fund_id'].tolist()
            holdings_df_sample = holdings_df[holdings_df['fund_id'].isin(sample_fund_ids)]
        else:
            holdings_df_sample = holdings_df.head(sample_size * 5)  # More holdings since funds have multiple
        
        # Preprocess data
        print("\n3. Testing preprocessing functions...")
        mf_df_processed = preprocess_funds(mf_df_sample)
        stock_df_processed = preprocess_stocks(stock_df_sample)
        
        print("\nPreprocessed mutual funds:")
        print(mf_df_processed.head(2).to_string())
        
        print("\nPreprocessed stocks:")
        print(stock_df_processed.head(2).to_string())
        
        # Create mappings
        print("\n4. Testing mapping creation...")
        fund_holdings = create_fund_holdings_map(mf_df_processed, holdings_df_sample, stock_df_processed)
        fund_sectors = create_fund_sector_map(holdings_df_sample, stock_df_processed)
        
        print(f"\nCreated holdings mappings for {len(fund_holdings)} funds")
        if fund_holdings:
            fund_id = next(iter(fund_holdings))
            holdings = fund_holdings[fund_id]
            print(f"Sample holdings for fund {fund_id}: {holdings[:3]}")
        
        print(f"\nCreated sector mappings for {len(fund_sectors)} funds")
        if fund_sectors:
            fund_id = next(iter(fund_sectors))
            sectors = fund_sectors[fund_id]
            print(f"Sample sectors for fund {fund_id}: {list(sectors.items())[:3]}")
        
        # Generate descriptions
        print("\n5. Testing description generation...")
        descriptions_df = generate_fund_descriptions(mf_df_processed, fund_holdings, fund_sectors)
        
        print(f"\nGenerated {len(descriptions_df)} descriptions")
        print("\nSample descriptions:")
        for i, row in descriptions_df.head(2).iterrows():
            print(f"\nFund: {row['fund_name']}")
            print(f"Description: {row['description']}")
        
        # Test saving to files
        print("\n6. Testing file saving...")
        output_paths = utils.get_output_paths()
        
        # Save to temporary test files
        test_output_dir = os.path.join(utils.PROCESSED_DIR, "test")
        os.makedirs(test_output_dir, exist_ok=True)
        
        test_desc_file = os.path.join(test_output_dir, "test_descriptions.csv")
        descriptions_df.to_csv(test_desc_file, index=False)
        print(f"Saved test descriptions to {test_desc_file}")
        
        test_corpus_file = os.path.join(test_output_dir, "test_corpus.txt")
        with open(test_corpus_file, "w", encoding="utf-8") as f:
            for desc in descriptions_df['description'].head(2):
                f.write(desc + "\n")
        print(f"Saved test corpus to {test_corpus_file}")
        
        print("\nPreprocessing test complete!")
        return True
        
    except Exception as e:
        print(f"Error during preprocessing test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_preprocessing_pipeline() 