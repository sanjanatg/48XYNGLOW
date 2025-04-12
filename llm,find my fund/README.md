# LLM, Find My Fund 💰

A smart search engine for financial funds and securities using a hybrid approach of BM25 lexical search and semantic search with sentence transformers.

## Features

- **Hybrid Search System**: Combines BM25 lexical search with semantic embeddings for optimal results
- **Metadata Boosting**: Utilizes fund metadata (fund house, category, sector, etc.) to improve search quality
- **RAG-powered Explanations**: Generates detailed, natural language explanations of funds using retrieval-augmented generation
- **Multiple Interfaces**: CLI, Web UI (Streamlit), AI Chatbot (Next.js), and RESTful API (FastAPI)
- **Voice Interaction**: Ask questions and get responses using voice commands
- **Multilingual Support**: Interface and responses in 6 Indian languages (English, Hindi, Tamil, Telugu, Kannada, Marathi)
- **Efficient Vectorization**: Uses HNSW (Hierarchical Navigable Small Worlds) for fast approximate nearest neighbor search
- **Small Model Footprint**: Uses lightweight models that can run on commodity hardware

## Installation

### Prerequisites

- Python 3.9+
- Node.js 18+ (for the chatbot interface)
- [Microsoft Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) (required for hnswlib)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/llm-find-my-fund.git
   cd llm-find-my-fund
   ```

2. Create a virtual environment and install Python dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set up the chatbot interface:
   ```bash
   cd chatbot
   npm install
   cd ..
   ```

4. Configure environment variables:
   - Copy `chatbot/.env.local.example` to `chatbot/.env.local`
   - Add your DeepSeek API key (if using DeepSeek for general chat capabilities)
   ```
   DEEPSEEK_API_KEY=your_api_key_here
   ```

## Usage

### All-in-one Starter

Start both the API server and chatbot interface with a single command:

```bash
python start_all.py
```

### Prepare Your Data

Place your fund data in CSV format in the `data/funds.csv` file with the following columns:
- `fund_name`: Name of the fund
- `fund_house`: Fund house or AMC (Asset Management Company)
- `category`: Fund category (e.g., Equity, Debt, Hybrid)
- `sub_category`: Fund subcategory (e.g., Large Cap, Mid Cap, Small Cap)
- `asset_class`: Asset class (e.g., Equity, Debt, Commodity)
- `fund_type`: Fund type (e.g., Open Ended, Close Ended)
- `sector`: Sector focus (e.g., Technology, Banking, Diversified)

A sample dataset is provided in `data/sample_funds.csv`.

### Using the Command Line Interface

```bash
# Basic search
python -m main --cli search "ICICI tech fund"

# Interactive mode
python -m main --cli interactive

# Train models explicitly
python -m main --cli train
```

### Using the Web Interface

```bash
python -m main --web
```

Then open your browser at `http://localhost:8501`

### Using the Chatbot Interface

Start the FastAPI backend:
```bash
python -m main --api
```

In a separate terminal, start the chatbot:
```bash
cd chatbot
npm run dev
```

Then open your browser at `http://localhost:3000`

### Using the API

```bash
python -m main --api
```

The API will be available at `http://localhost:8000`. You can access the API documentation at `http://localhost:8000/docs`.

## API Endpoints

- `GET /`: API status
- `GET /search?query=ICICI tech fund&top_k=5&search_type=hybrid`: Search for funds
- `POST /search`: Search for funds (JSON body)
- `POST /explain`: Get detailed explanation of a specific fund
- `GET /languages`: Get supported languages
- `POST /translate`: Translate text between supported languages
- `POST /train`: Train models

## Features in Detail

### RAG-powered Fund Explanations

The system uses Retrieval-Augmented Generation to provide detailed explanations about funds:

1. Search for the fund in the database to retrieve metadata
2. Generate a natural language explanation using the metadata
3. Include risk level assessment and investor suitability information
4. Personalize explanations based on user context (e.g., retirement planning)

To use this feature, ask the chatbot questions like:
- "Explain ICICI Prudential Technology Fund"
- "Tell me more about SBI Blue Chip Fund"
- "Is HDFC Flexicap fund good for retirement?"

### Voice Interaction

The chatbot interface includes voice interaction capabilities:

1. Click the microphone button to start voice recognition
2. Speak your query about funds or investments
3. The system will process your query and respond with fund information
4. The response will also be read aloud using text-to-speech

Voice commands work best when:
- You speak clearly and at a moderate pace
- You include specific fund keywords (e.g., "ICICI", "SBI", "mutual fund", etc.)
- You are in a quiet environment with minimal background noise

### Multilingual Support

The system supports 6 Indian languages with the language selector in the chatbot header:

- 🇬🇧 English (default)
- 🇮🇳 Hindi (हिंदी)
- 🇮🇳 Tamil (தமிழ்)
- 🇮🇳 Telugu (తెలుగు)
- 🇮🇳 Kannada (ಕನ್ನಡ)
- 🇮🇳 Marathi (मराठी)

The language selection affects:
- UI elements and response translations
- Voice recognition language
- Text-to-speech pronunciation

## How It Works

This search engine uses a hybrid approach combining:

1. **BM25 Lexical Search**: For exact keyword matching (similar to what databases use)
2. **Semantic Search**: Using sentence transformers and HNSW for approximate nearest neighbor search
3. **Metadata Boosting**: Utilizes fund metadata to improve results
4. **RAG Explanations**: Combines retrieval with LLM-based text generation
5. **LLM Integration**: DeepSeek API for general investment advice (optional)
6. **Voice Processing**: Web Speech API for speech recognition and synthesis
7. **Language Support**: Translation for multilingual capabilities

The search results are ranked using a weighted combination of lexical and semantic scores.

## Project Structure

```
.
├── chatbot/             # Next.js chatbot interface with voice capabilities
├── data/                # Data files
│   ├── funds.csv        # Main fund data
│   └── sample_funds.csv # Sample fund data
├── models/              # Saved models and indices
├── src/                 # Source code
│   ├── api/             # FastAPI server
│   ├── cli/             # CLI interface
│   ├── core/            # Core search functionality
│   └── web/             # Streamlit web interface
├── main.py              # Main entry point
├── start_all.py         # Script to start both API and chatbot
├── README.md            # This README file
└── requirements.txt     # Dependencies
```

## Tech Stack

- **sentence-transformers**: For generating semantic embeddings
- **hnswlib**: For efficient ANN (Approximate Nearest Neighbors) search
- **rank_bm25**: For BM25 lexical search
- **typer**: For CLI interface
- **streamlit**: For web interface
- **fastapi + uvicorn**: For API server
- **Next.js + React**: For chatbot interface
- **Web Speech API**: For voice interaction
- **DeepSeek API**: For general chat capabilities and RAG explanations (optional)
- **Multilingual APIs**: Translation capabilities for various Indian languages
- **pandas**: For data manipulation
- **loguru**: For logging

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Developed as part of the "LLM, Find My Fund" hackathon challenge
- Uses the Sentence Transformers library by UKPLab
- Inspired by modern search systems like Elasticsearch and Pinecone 