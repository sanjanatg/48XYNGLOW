import os
import json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from search_engine import SearchEngine
from utils import clean_query, extract_metadata
from metadata_parser import explain_results

# Initialize FastAPI app
app = FastAPI(title="Find My Fund - Smart Search API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize search engine
search_engine = SearchEngine()

@app.get("/")
async def root():
    return {"message": "Welcome to Find My Fund API. Use /search endpoint to query funds."}

@app.get("/search")
async def search(query: str):
    """
    Search for funds based on natural language query.
    """
    # Clean and process the query
    processed_query = clean_query(query)
    
    # Get search results
    results = search_engine.search(processed_query)
    
    # Extract metadata that matched for explanation
    metadata = extract_metadata(query, results)
    
    # Generate explanations for why each fund was selected
    explained_results = explain_results(results, metadata)
    
    return JSONResponse(content=explained_results)

@app.get("/sample-queries")
async def get_sample_queries():
    """
    Return sample queries to help users get started.
    """
    try:
        with open(os.path.join(os.path.dirname(__file__), "sample_queries.json"), "r") as f:
            sample_queries = json.load(f)
        return JSONResponse(content=sample_queries)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 