import numpy as np
import pandas as pd
from rank_bm25 import BM25Okapi
from nltk.tokenize import word_tokenize
import nltk

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

class BM25Retriever:
    def __init__(self, fund_data):
        """
        Initialize BM25 retriever with fund data
        
        Args:
            fund_data: pandas DataFrame containing fund information with at least
                       'fund_name' and 'description' columns
        """
        self.fund_data = fund_data
        self.corpus = self.fund_data['description'].tolist()
        
        # Tokenize each document in corpus
        tokenized_corpus = [word_tokenize(doc.lower()) for doc in self.corpus]
        
        # Create BM25 model
        self.bm25 = BM25Okapi(tokenized_corpus)
        
    def retrieve(self, query, top_k=100):
        """
        Retrieve top k funds matching the query using BM25
        
        Args:
            query: preprocessed query string
            top_k: number of top funds to retrieve (default 100)
            
        Returns:
            list of dictionaries with fund details and relevance scores
        """
        # Tokenize query
        tokenized_query = word_tokenize(query.lower())
        
        # Get BM25 scores
        bm25_scores = self.bm25.get_scores(tokenized_query)
        
        # Get indices of top k scores
        top_indices = np.argsort(bm25_scores)[::-1][:top_k]
        
        # Return fund details with scores
        results = []
        for idx in top_indices:
            fund_details = self.fund_data.iloc[idx].to_dict()
            fund_details['bm25_score'] = bm25_scores[idx]
            results.append(fund_details)
        
        return results
    
    def search_keywords(self, keywords, top_k=100):
        """
        Retrieve top k funds matching a list of keywords
        
        Args:
            keywords: list of keywords
            top_k: number of top funds to retrieve (default 100)
            
        Returns:
            list of dictionaries with fund details and relevance scores
        """
        # Join keywords into a single string for BM25
        query = " ".join(keywords)
        return self.retrieve(query, top_k)
        
# Example usage
if __name__ == "__main__":
    # Sample data for testing
    sample_data = pd.DataFrame({
        'fund_name': ['HDFC Technology Fund', 'SBI Healthcare Fund', 'ICICI Low Risk Bond Fund'],
        'description': [
            'HDFC Technology Fund invests in technology companies focusing on innovation and growth.',
            'SBI Healthcare Fund focuses on pharmaceutical and healthcare sector for long-term growth.',
            'ICICI Low Risk Bond Fund is a debt fund with conservative approach for stable returns.'
        ]
    })
    
    retriever = BM25Retriever(sample_data)
    results = retriever.retrieve("technology innovation")
    
    print(f"Top match: {results[0]['fund_name']} with score {results[0]['bm25_score']:.2f}") 