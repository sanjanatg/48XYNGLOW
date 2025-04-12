import os
import json
import pandas as pd
from loguru import logger
from typing import Dict, List, Union, Optional

class DataLoader:
    """
    Class to load and preprocess financial fund data.
    """

    def __init__(self, data_path: str = "data/funds.csv"):
        """
        Initialize the DataLoader.

        Args:
            data_path: Path to the fund data file
        """
        self.data_path = data_path
        self.data = None
        self.metadata_fields = [
            "fund_house", "category", "sub_category", 
            "asset_class", "fund_type", "sector"
        ]

    def load_data(self) -> pd.DataFrame:
        """
        Load data from file.

        Returns:
            Pandas DataFrame of fund data
        """
        try:
            if self.data_path.endswith('.csv'):
                self.data = pd.read_csv(self.data_path)
            elif self.data_path.endswith('.json'):
                self.data = pd.read_json(self.data_path)
            else:
                raise ValueError(f"Unsupported file format: {self.data_path}")
            
            logger.info(f"Loaded {len(self.data)} funds from {self.data_path}")
            return self.data
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise

    def preprocess_data(self) -> pd.DataFrame:
        """
        Preprocess the fund data.

        Returns:
            Preprocessed DataFrame
        """
        if self.data is None:
            self.load_data()
        
        # Fill missing values
        for field in self.metadata_fields:
            if field in self.data.columns:
                self.data[field] = self.data[field].fillna("unknown")
        
        # Ensure fund name is a string
        self.data['fund_name'] = self.data['fund_name'].astype(str)
        
        # Create combined text for each fund for semantic search
        self.data['combined_text'] = self.data.apply(self.create_combined_text, axis=1)
        
        logger.info("Data preprocessing completed")
        return self.data
    
    def create_combined_text(self, row: pd.Series) -> str:
        """
        Create a combined text representation of a fund for semantic search.

        Args:
            row: Pandas Series representing a fund

        Returns:
            Combined text string
        """
        text_parts = [row['fund_name']]
        
        for field in self.metadata_fields:
            if field in row and pd.notna(row[field]) and row[field] != "unknown":
                text_parts.append(f"{field}: {row[field]}")
                
        return ". ".join(text_parts)
    
    def save_processed_data(self, output_path: str = "data/processed_funds.csv") -> None:
        """
        Save the processed data to a file.

        Args:
            output_path: Path to save the processed data
        """
        if self.data is None:
            raise ValueError("No data to save. Call preprocess_data() first.")
            
        self.data.to_csv(output_path, index=False)
        logger.info(f"Saved processed data to {output_path}")

    def get_data(self) -> pd.DataFrame:
        """
        Get the current data.

        Returns:
            Current DataFrame
        """
        if self.data is None:
            return self.preprocess_data()
        return self.data 