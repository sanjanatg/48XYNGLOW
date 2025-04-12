# Find My Fund: LLM-Powered Mutual Fund Search

A smart mutual fund search assistant that understands natural language queries and matches them to the right funds using vector search and metadata reasoning.

## 🔍 Problem We're Solving

Most FinTech apps (Groww, Zerodha, PayTM Money) offer basic keyword search for mutual funds and stocks. They:
- Fail on **typos**, **partial names**, **abbreviations**
- Can't handle **natural language** like "Show me tax-saving funds with high return"
- Don't **explain why** a result was shown

## 💡 Our Solution

An intelligent search assistant that:
- Understands user queries *like a financial advisor*
- Links them to relevant funds using **metadata**, not just keywords
- Works in **real-time**
- Explains why the fund was selected

## 🔧 Technical Approach

### Overall Flow:
1. **Understand the Query** (Intent + Entities)
2. **Use Embeddings to Fetch Candidates**
3. **Rerank with Metadata**
4. **Explain why the result was chosen**

### Tech Stack:
- **Query Understanding**: SLM (MiniLM) + Rule-based keyword detection
- **Embedding Search**: FAISS with MiniLM embeddings
- **Metadata Filtering**: Smart reranker + rules (AUM > 1000cr, sector match)
- **Explainability**: Return what metadata matched (e.g., "Matched: Sector=Tech")
- **UI**: Chatbot frontend with Gradio
- **Deployment**: FastAPI + Gradio UI

## 🚀 Features

- **Natural Language Understanding**: Ask questions in plain English
- **Fuzzy Matching**: Handles typos and partial names
- **Metadata-Driven**: Matches on fund categories, sectors, risk levels, and more
- **Explanations**: Shows why each fund was recommended
- **Sample Queries**: Try pre-built examples to see what's possible

## 📊 Demo Data

The application includes demo data with 10 sample mutual funds covering different:
- Categories (Equity, ELSS, Index)
- Sectors (Technology, Healthcare, etc.)
- Risk levels (Low, Moderate, High)
- Returns and AUM (Assets Under Management) values

## 📋 Installation & Setup

### Prerequisites
- Python 3.10+
- Pip / Conda
- Git

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd llm-find-my-fund
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Application

#### Option 1: Run the Gradio UI directly (recommended for quick start)
```bash
python ui/chatbot_gradio.py
```

#### Option 2: Run as a FastAPI service + separate UI
```bash
# Terminal 1: Start the API server
python app/main.py

# Terminal 2: Start the UI (with API_URL in config.py set to http://localhost:8000)
python ui/chatbot_gradio.py
```

## 📚 Usage Examples

- "Show me tax saving funds with high returns"
- "Funds from the technology sector with low volatility"
- "Large cap funds with good track record"
- "Show me funds with returns above 15% and AUM > 1000 crore"
- "I'm planning for retirement in 20 years, what funds should I consider?"

## 🔄 Project Structure

```
llm-find-my-fund/
├── app/                          # Backend + chatbot logic
│   ├── main.py                   # FastAPI main server
│   ├── search_engine.py          # Core retrieval logic (vector + rerank)
│   ├── rules.py                  # Rule-based filters (like AUM > 1000cr)
│   ├── utils.py                  # Helper functions
│   ├── metadata_parser.py        # Metadata extraction & matching logic
│   └── sample_queries.json       # Demo queries
│
├── data/                         # Data directory
│   ├── funds.csv                 # Fund names + metadata
│   ├── holdings.csv              # Fund holdings data
│   └── processed/                # Processed files
│       └── funds_embeddings.pkl  # Pickled vector store (FAISS)
│
├── models/                       # Model files (if downloading locally)
│
├── notebooks/                    # Notebooks for training or testing
│   ├── 01_build_vector_store.ipynb
│   └── 02_train_or_finetune.ipynb
│
├── ui/                           # Frontend 
│   └── chatbot_gradio.py         # Gradio UI
│
├── requirements.txt              # Python dependencies
├── README.md                     # Project documentation
└── config.py                     # Configuration settings
```

## 📝 Next Steps & Future Enhancements

- **Custom Fine-tuned SLM**: Train a model specifically for financial queries
- **Live Data Integration**: Connect to real-time market data APIs
- **Portfolio Recommendation**: Suggest a balanced portfolio based on user goals
- **Comparison Feature**: Side-by-side comparison of multiple funds
- **Voice Interface**: Add voice input/output capability
- **Mobile App**: Develop a mobile interface

## 📄 License

MIT License

## 🙏 Acknowledgements

- Sentence Transformers library
- FAISS vector search
- Gradio & FastAPI frameworks 