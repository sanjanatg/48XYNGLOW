# Find My Fund: Intelligent Fund Search

A powerful mutual fund search application powered by RAG (Retrieval Augmented Generation) and Mistral 7B. This application allows users to search for mutual funds using natural language queries and get AI-powered analysis.

## Features

- **Natural Language Search**: Find funds matching your criteria using everyday language
- **Semantic Search**: Understand the meaning behind your query for better results
- **AI Analysis**: Get in-depth analysis of funds powered by LLM
- **Performance Visualization**: Compare fund performance with category average and benchmark
- **Dark UI**: Modern dark-themed interface with a clean design

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Required packages (install via `pip install -r requirements.txt`)
- [Ollama](https://ollama.ai/) with the Mistral model (for LLM functionality)

### Installation

1. Clone this repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Make sure Ollama is running with the Mistral model:
   ```
   ollama run mistral
   ```

### Running the Application

#### Option 1: Using the Batch File (Windows)

Simply run the included batch file:
```
start_application.bat
```

This will start both the API server and Streamlit UI in separate windows.

#### Option 2: Manual Start

1. Start the API server:
   ```
   python api_server.py
   ```
   
2. In a separate terminal, start the Streamlit UI:
   ```
   streamlit run streamlit_app.py
   ```

3. Open your browser and go to http://localhost:8501 to access the application

## Usage Examples

Try searching for funds with queries like:
- "low risk debt fund with good returns"
- "equity fund focused on technology sector"
- "balanced fund with moderate risk and stable returns"
- "fund with high exposure to healthcare sector"

## Architecture

- **Flask Backend**: RESTful API for fund search and analysis
- **Streamlit Frontend**: User-friendly interface for search and visualization
- **RAG Pipeline**: Combines BM25, vector search, and metadata filtering for better results
- **Mistral 7B**: Powers the natural language understanding and fund analysis

## Technical Details

The application uses a sophisticated RAG pipeline:

1. **Query Parsing**: Extracts key information from natural language queries
2. **BM25 Search**: Finds initial candidates using keyword matching
3. **Semantic Search**: Uses embeddings to understand the meaning behind queries
4. **Metadata Filtering**: Applies constraints based on risk, sector, etc.
5. **Score Fusion**: Combines different retrieval methods for optimal results
6. **LLM Analysis**: Generates insights and explanations using Mistral 7B

## License

This project is licensed under the MIT License - see the LICENSE file for details. 