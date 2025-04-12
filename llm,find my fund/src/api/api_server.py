import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Query, HTTPException, Body, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from loguru import logger
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to sys.path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.search_engine import SearchEngine

# Initialize logger
logger.remove()
logger.add(sys.stderr, level="INFO")

# Define API models
class SearchQuery(BaseModel):
    """Model for search query parameters."""
    query: str = Field(..., description="Search query for finding funds")
    top_k: int = Field(5, description="Number of results to return", ge=1, le=50)
    search_type: str = Field("hybrid", description="Type of search (lexical, semantic, or hybrid)")
    language: Optional[str] = Field("en", description="Language code for response (en, hi, ta, te, kn, mr)")

class SearchResult(BaseModel):
    """Model for a single search result."""
    fund_name: str
    fund_house: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    asset_class: Optional[str] = None
    fund_type: Optional[str] = None
    sector: Optional[str] = None
    bm25_score: Optional[float] = None
    semantic_score: Optional[float] = None
    combined_score: Optional[float] = None

class SearchResponse(BaseModel):
    """Model for search response."""
    query: str
    search_type: str
    results: List[SearchResult]
    result_count: int
    language: str = "en"

class ExplainRequest(BaseModel):
    """Model for fund explanation request."""
    fund_name: str = Field(..., description="Name of the fund to explain")
    user_context: Optional[str] = Field(None, description="Additional user context like investment goals or risk appetite")
    language: Optional[str] = Field("en", description="Language code for response (en, hi, ta, te, kn, mr)")

class ExplainResponse(BaseModel):
    """Model for fund explanation response."""
    fund_name: str
    explanation: str
    suitability: Optional[str] = None
    risk_level: Optional[str] = None
    language: str = "en"

class TranslationRequest(BaseModel):
    """Model for translation request."""
    text: str = Field(..., description="Text to translate")
    source_language: Optional[str] = Field("en", description="Source language code")
    target_language: str = Field(..., description="Target language code")

class TranslationResponse(BaseModel):
    """Model for translation response."""
    original_text: str
    translated_text: str
    source_language: str
    target_language: str

class ChatMessage(BaseModel):
    """Model for a chat message."""
    role: str
    content: str

class ChatRequest(BaseModel):
    """Model for chat request."""
    messages: List[ChatMessage]
    language: Optional[str] = Field("en", description="Language code for response (en, hi, ta, te, kn, mr)")

class ChatResponse(BaseModel):
    """Model for chat response."""
    response: str
    language: str = "en"

# Initialize FastAPI app
app = FastAPI(
    title="LLM, Find My Fund API",
    description="API for searching and finding mutual funds and securities.",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store the SearchEngine instance
search_engine = None

# Supported languages
SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "mr": "Marathi"
}

def get_search_engine() -> SearchEngine:
    """
    Get or initialize the search engine.
    
    Returns:
        SearchEngine instance
    """
    global search_engine
    
    if search_engine is None:
        data_path = os.environ.get("FUND_DATA_PATH", "data/funds.csv")
        model_dir = os.environ.get("MODEL_DIR", "models")
        
        # Initialize engine
        engine = SearchEngine(data_path=data_path)
        
        # Check if models exist
        model_path = os.path.join(model_dir, "hnsw_index.bin")
        metadata_path = os.path.join(model_dir, "index_metadata.json")
        processed_data_path = os.path.join(model_dir, "processed_funds.csv")
        
        models_exist = (
            os.path.exists(model_path) and 
            os.path.exists(metadata_path) and 
            os.path.exists(processed_data_path)
        )
        
        if models_exist:
            logger.info("Loading pre-trained models...")
            engine.load_models(directory=model_dir, data_path=processed_data_path)
        else:
            logger.info("Training models...")
            engine.fit(force_reload=True)
            
            # Save models for future use
            os.makedirs(model_dir, exist_ok=True)
            engine.save_models(directory=model_dir)
        
        search_engine = engine
        logger.info("Search engine initialized successfully")
    
    return search_engine

async def translate_text(text: str, target_language: str, source_language: str = "en") -> str:
    """
    Translate text to the target language.
    
    Args:
        text: Text to translate
        target_language: Target language code
        source_language: Source language code
        
    Returns:
        Translated text
    """
    if target_language == source_language or target_language == "en":
        return text
    
    try:
        # Placeholder translations for demo
        # In a real implementation, you would call a translation API here
        
        # Some simple placeholder translations for demo
        translations = {
            "hi": {
                "Fund House": "फंड हाउस",
                "Category": "श्रेणी",
                "Sub-Category": "उप-श्रेणी",
                "Match Score": "मैच स्कोर",
                "Would you like me to explain any of these funds in detail?": "क्या आप चाहेंगे कि मैं इनमें से किसी भी फंड के बारे में विस्तार से बताऊं?"
            },
            "ta": {
                "Fund House": "நிதி நிறுவனம்",
                "Category": "வகை",
                "Sub-Category": "துணை-வகை",
                "Match Score": "பொருத்த மதிப்பெண்",
                "Would you like me to explain any of these funds in detail?": "இந்த நிதிகளில் ஏதேனும் ஒன்றை விரிவாக விளக்க வேண்டுமா?"
            }
        }
        
        # For demo, just do simple word replacement for common terms
        if target_language in translations:
            result = text
            for en_term, translated_term in translations[target_language].items():
                result = result.replace(en_term, translated_term)
            
            # Add language code prefix to show it's "translated"
            return f"[{target_language}] {result}"
        
        # For languages without placeholders, just add the language code
        return f"[{target_language}] {text}"
        
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        return text  # Return original text if translation fails

@app.get("/", tags=["Status"])
async def read_root():
    """API status endpoint."""
    return {"status": "online", "message": "LLM, Find My Fund API is running"}

@app.get("/languages", tags=["Languages"])
async def get_supported_languages():
    """Get supported languages."""
    return {"languages": SUPPORTED_LANGUAGES}

@app.post("/translate", response_model=TranslationResponse, tags=["Languages"])
async def translate(
    translation_params: TranslationRequest
):
    """
    Translate text to the target language.
    
    Args:
        translation_params: Translation parameters
        
    Returns:
        Translated text
    """
    try:
        if translation_params.target_language not in SUPPORTED_LANGUAGES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported target language: {translation_params.target_language}. Supported languages: {', '.join(SUPPORTED_LANGUAGES.keys())}"
            )
            
        translated_text = await translate_text(
            text=translation_params.text,
            target_language=translation_params.target_language,
            source_language=translation_params.source_language
        )
        
        return TranslationResponse(
            original_text=translation_params.text,
            translated_text=translated_text,
            source_language=translation_params.source_language,
            target_language=translation_params.target_language
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Translation error: {str(e)}")

@app.post("/search", response_model=SearchResponse, tags=["Search"])
async def search_funds(
    search_params: SearchQuery,
    engine: SearchEngine = Depends(get_search_engine)
):
    """
    Search for funds matching the query.
    
    Args:
        search_params: Search parameters
        engine: SearchEngine instance
        
    Returns:
        Search results
    """
    try:
        # Validate search type
        if search_params.search_type not in ["lexical", "semantic", "hybrid"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid search type: {search_params.search_type}. Must be one of [lexical, semantic, hybrid]"
            )
        
        # Validate language
        language = search_params.language or "en"
        if language not in SUPPORTED_LANGUAGES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported language: {language}. Supported languages: {', '.join(SUPPORTED_LANGUAGES.keys())}"
            )
        
        # Perform search
        logger.info(f"Searching for: {search_params.query} (type: {search_params.search_type}, top_k: {search_params.top_k}, language: {language})")
        
        results = engine.search(
            query=search_params.query,
            top_k=search_params.top_k,
            search_type=search_params.search_type
        )
        
        # Create response
        response = SearchResponse(
            query=search_params.query,
            search_type=search_params.search_type,
            results=[SearchResult(**result) for result in results],
            result_count=len(results),
            language=language
        )
        
        return response
    
    except Exception as e:
        logger.error(f"Error processing search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing search: {str(e)}")

@app.get("/search", response_model=SearchResponse, tags=["Search"])
async def search_funds_get(
    query: str = Query(..., description="Search query for finding funds"),
    top_k: int = Query(5, description="Number of results to return", ge=1, le=50),
    search_type: str = Query("hybrid", description="Type of search (lexical, semantic, or hybrid)"),
    language: str = Query("en", description="Language code for response"),
    engine: SearchEngine = Depends(get_search_engine)
):
    """
    Search for funds matching the query (GET method).
    
    Args:
        query: Search query
        top_k: Number of results to return
        search_type: Type of search
        language: Language code for response
        engine: SearchEngine instance
        
    Returns:
        Search results
    """
    # Create a SearchQuery object and reuse the POST endpoint logic
    search_params = SearchQuery(query=query, top_k=top_k, search_type=search_type, language=language)
    return await search_funds(search_params, engine)

@app.post("/explain", response_model=ExplainResponse, tags=["Explanations"])
async def explain_fund(
    explain_params: ExplainRequest,
    engine: SearchEngine = Depends(get_search_engine)
):
    """
    Generate a natural language explanation for a specific fund.
    
    Args:
        explain_params: Fund explanation parameters
        engine: SearchEngine instance
        
    Returns:
        Fund explanation
    """
    try:
        # Validate language
        language = explain_params.language or "en"
        if language not in SUPPORTED_LANGUAGES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported language: {language}. Supported languages: {', '.join(SUPPORTED_LANGUAGES.keys())}"
            )
        
        # First, search for the fund to get its details
        logger.info(f"Getting explanation for fund: {explain_params.fund_name}")
        
        # Search for exact fund name first
        results = engine.search(
            query=explain_params.fund_name,
            top_k=5,
            search_type="hybrid"
        )
        
        # Find the closest match
        fund_data = None
        for result in results:
            # Check for exact match first
            if result["fund_name"].lower() == explain_params.fund_name.lower():
                fund_data = result
                break
        
        # If no exact match, use the top result
        if fund_data is None and results:
            fund_data = results[0]
            logger.info(f"Using closest match: {fund_data['fund_name']}")
        
        if not fund_data:
            raise HTTPException(status_code=404, detail=f"Fund not found: {explain_params.fund_name}")
        
        # Build prompt for the LLM
        prompt = f"""
        Generate a comprehensive explanation for the following mutual fund:
        
        Fund Name: {fund_data['fund_name']}
        Fund House: {fund_data.get('fund_house', 'Unknown')}
        Category: {fund_data.get('category', 'Unknown')}
        Sub-Category: {fund_data.get('sub_category', 'Unknown')}
        Asset Class: {fund_data.get('asset_class', 'Unknown')}
        Fund Type: {fund_data.get('fund_type', 'Unknown')}
        Sector: {fund_data.get('sector', 'Unknown')}
        
        {f"User Context: {explain_params.user_context}" if explain_params.user_context else ""}
        
        Provide:
        1. A concise explanation of what this fund invests in
        2. The typical risk profile of this fund
        3. What kind of investors this fund is suitable for
        4. Any key considerations or warnings
        
        Format your response as a cohesive paragraph that's easy to understand for someone without financial expertise.
        """
        
        # Check if DeepSeek API key is available
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        
        explanation = ""
        risk_level = get_risk_level(fund_data)
        suitability = get_suitability(fund_data)
        
        if not api_key:
            # Fallback to a rule-based explanation if no API key
            logger.warning("No LLM API key available. Using rule-based explanation.")
            explanation = generate_rule_based_explanation(fund_data)
        else:
            # Call DeepSeek API for the explanation
            try:
                response = requests.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {api_key}"
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": [
                            {"role": "system", "content": "You are a financial advisor specializing in mutual funds."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 500
                    },
                    timeout=10
                )
                
                if response.status_code != 200:
                    logger.error(f"DeepSeek API error: {response.text}")
                    raise Exception(f"DeepSeek API error: {response.status_code}")
                    
                result = response.json()
                explanation = result["choices"][0]["message"]["content"]
                
            except Exception as e:
                logger.error(f"Error calling DeepSeek API: {str(e)}")
                # Fallback to rule-based explanation
                explanation = generate_rule_based_explanation(fund_data)
        
        # Translate if necessary
        if language != "en":
            explanation = await translate_text(explanation, language)
            risk_level = await translate_text(risk_level, language)
            suitability = await translate_text(suitability, language) if suitability else None
        
        return ExplainResponse(
            fund_name=fund_data["fund_name"],
            explanation=explanation,
            suitability=suitability,
            risk_level=risk_level,
            language=language
        )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating fund explanation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating fund explanation: {str(e)}")

def generate_rule_based_explanation(fund_data: Dict[str, Any]) -> str:
    """
    Generate a rule-based explanation for a fund when LLM is not available.
    
    Args:
        fund_data: Fund data dictionary
        
    Returns:
        Rule-based explanation
    """
    fund_name = fund_data["fund_name"]
    fund_house = fund_data.get("fund_house", "Unknown")
    category = fund_data.get("category", "Unknown").lower()
    sub_category = fund_data.get("sub_category", "").lower()
    sector = fund_data.get("sector", "").lower()
    fund_type = fund_data.get("fund_type", "").lower()
    
    # Basic template
    explanation = f"{fund_name} is a {category} fund from {fund_house}."
    
    # Add category specific information
    if "equity" in category:
        explanation += f" This fund primarily invests in equity stocks"
        if sub_category:
            if "large" in sub_category:
                explanation += " of large, established companies, which typically offer more stability but potentially lower growth."
            elif "mid" in sub_category:
                explanation += " of mid-sized companies, which balance growth potential with moderate risk."
            elif "small" in sub_category:
                explanation += " of smaller companies with high growth potential but also higher volatility."
            elif "multi" in sub_category:
                explanation += " across companies of different sizes, providing diversification."
            else:
                explanation += "."
        else:
            explanation += "."
    
    elif "debt" in category:
        explanation += " This fund focuses on fixed income securities like bonds and government securities, aiming for regular income with lower volatility than equity funds."
    
    elif "hybrid" in category:
        explanation += " This balanced fund invests in a mix of equity and debt securities, aiming to provide growth while managing risk through diversification."
    
    # Add sector specific information
    if sector and sector != "unknown" and sector != "nan":
        explanation += f" It specializes in the {sector} sector, which means performance will be tied to how this specific industry performs."
    
    # Add fund type information
    if "open" in fund_type:
        explanation += " As an open-ended fund, you can buy or sell units at any time."
    elif "close" in fund_type:
        explanation += " As a closed-end fund, it can only be bought during the initial offering period and later traded on exchanges."
    
    # Add risk and suitability
    risk_level = get_risk_level(fund_data)
    explanation += f" This fund generally has a {risk_level} risk profile."
    
    suitability = get_suitability(fund_data)
    if suitability:
        explanation += f" {suitability}"
    
    return explanation

def get_risk_level(fund_data: Dict[str, Any]) -> str:
    """
    Determine the risk level based on fund data.
    
    Args:
        fund_data: Fund data dictionary
        
    Returns:
        Risk level (high, moderate, low)
    """
    category = fund_data.get("category", "").lower()
    sub_category = fund_data.get("sub_category", "").lower()
    
    if "equity" in category:
        if "small" in sub_category or "sectoral" in sub_category or "thematic" in sub_category:
            return "high"
        elif "mid" in sub_category:
            return "moderate to high"
        elif "large" in sub_category:
            return "moderate"
        else:
            return "moderate to high"
    elif "debt" in category:
        if "liquid" in sub_category or "ultra short" in sub_category:
            return "low"
        elif "short" in sub_category:
            return "low to moderate"
        else:
            return "moderate"
    elif "hybrid" in category:
        return "moderate"
    else:
        return "varies based on its specific investments"

def get_suitability(fund_data: Dict[str, Any]) -> str:
    """
    Determine fund suitability based on data.
    
    Args:
        fund_data: Fund data dictionary
        
    Returns:
        Suitability description
    """
    category = fund_data.get("category", "").lower()
    sub_category = fund_data.get("sub_category", "").lower()
    
    if "equity" in category:
        if "small" in sub_category:
            return "It's suitable for investors with a long-term horizon and high risk tolerance looking for growth."
        elif "large" in sub_category:
            return "It's suitable for investors seeking relatively stable equity exposure with a medium to long-term outlook."
        else:
            return "It's generally suitable for investors with a long-term investment horizon."
    elif "debt" in category:
        if "liquid" in sub_category:
            return "It's suitable for investors with short-term goals or those seeking to park emergency funds."
        else:
            return "It's suitable for investors seeking regular income with lower volatility than equity markets."
    elif "hybrid" in category:
        return "It's suitable for investors looking for a balanced approach to investing, with moderate risk tolerance."
    else:
        return "Suitability depends on your financial goals and risk tolerance."

@app.post("/train", tags=["Training"])
async def train_models(
    data_path: str = Body("data/funds.csv", description="Path to the fund data file"),
    force: bool = Body(True, description="Force retraining of models")
):
    """
    Train or retrain the search models.
    
    Args:
        data_path: Path to the fund data
        force: Whether to force retraining
        
    Returns:
        Training status
    """
    global search_engine
    
    try:
        # Initialize new engine with specified data path
        engine = SearchEngine(data_path=data_path)
        
        # Train models
        logger.info(f"Training models with data from: {data_path}")
        engine.fit(force_reload=True)
        
        # Save models
        model_dir = os.environ.get("MODEL_DIR", "models")
        os.makedirs(model_dir, exist_ok=True)
        engine.save_models(directory=model_dir)
        
        # Update global engine
        search_engine = engine
        
        return {"status": "success", "message": "Models trained and saved successfully"}
    
    except Exception as e:
        logger.error(f"Error training models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error training models: {str(e)}")

@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(
    chat_request: ChatRequest
):
    """
    Process a chat message using DeepSeek API.
    
    Args:
        chat_request: Chat request containing messages
        
    Returns:
        Chat response
    """
    try:
        # Validate language
        language = chat_request.language or "en"
        if language not in SUPPORTED_LANGUAGES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported language: {language}. Supported languages: {', '.join(SUPPORTED_LANGUAGES.keys())}"
            )
        
        # Get DeepSeek API key
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        
        if not api_key:
            return ChatResponse(
                response="I'm unable to answer general questions without the DeepSeek API key. Please ask about specific funds instead.",
                language=language
            )
        
        # Add system message
        system_message = {
            "role": "system", 
            "content": "You are a financial advisor assistant specialized in mutual funds and investments. Focus on providing helpful information about investment options, funds, and financial advice."
        }
        
        messages = [system_message] + chat_request.messages
        
        # Call DeepSeek API
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            json={
                "model": "deepseek-chat",
                "messages": [{"role": m.role, "content": m.content} for m in messages],
                "temperature": 0.7,
                "max_tokens": 500
            },
            timeout=10
        )
        
        if response.status_code != 200:
            logger.error(f"DeepSeek API error: {response.text}")
            raise Exception(f"DeepSeek API error: {response.status_code}")
            
        result = response.json()
        response_text = result["choices"][0]["message"]["content"]
        
        # Translate if necessary
        if language != "en":
            response_text = await translate_text(response_text, language)
        
        return ChatResponse(
            response=response_text,
            language=language
        )
            
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}")
        return ChatResponse(
            response=f"I'm sorry, I encountered an error while processing your request. Please try again or ask about specific funds.",
            language=language
        )

def start_server():
    """Start the API server."""
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    uvicorn.run("src.api.api_server:app", host=host, port=port, reload=True)

if __name__ == "__main__":
    start_server() 