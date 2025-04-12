# Fund AI Navigator - Integration Guide

This guide explains how to integrate the Fund AI Navigator backend (mutual fund search engine) with the React UI.

## Project Structure

The integrated system consists of:

1. **Backend Components** (Phases 1-7):
   - Data preprocessing
   - Embedding and indexing
   - Query parsing and understanding
   - Enhanced retrieval with weighted scoring
   - RAG prompt engineering
   - Evaluation framework

2. **API Server**:
   - Flask server that connects the UI to the backend
   - REST endpoints for search, analysis, and comparison
   - Explainability toggle feature

3. **React UI**:
   - Modern UI with shadcn-ui components
   - Responsive design for search and dashboard
   - Explainability visualization

## Setup Instructions

### 1. Install Backend Dependencies

```bash
pip install -r requirements.txt
```

Additional requirements for the API server:
```bash
pip install flask flask-cors
```

### 2. Install UI Dependencies

```bash
cd ui
npm install
```

### 3. Run the Backend API Server

```bash
python api_server.py
```

The API server will run on http://localhost:5000 by default.

### 4. Run the UI Development Server

```bash
cd ui
npm run dev
```

The UI will be available at http://localhost:5173 by default.

## API Endpoints

The API server provides the following endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check endpoint |
| `/api/search` | POST | Search for mutual funds |
| `/api/analyze/:fundId` | GET | Get analysis for a specific fund |
| `/api/compare` | POST | Compare multiple funds |
| `/api/toggle-explanation` | POST | Toggle explainability feature |

### Example API Usage

#### Search

```javascript
// Search request
fetch('http://localhost:5000/api/search', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: 'low risk debt funds',
    filters: {
      fundType: 'debt',
      riskLevel: 'low',
      minReturn: 5
    },
    showExplanation: true
  }),
})
```

#### Analyze Fund

```javascript
// Fund analysis request
fetch('http://localhost:5000/api/analyze/hdfc_debt_fund_direct_growth')
```

#### Compare Funds

```javascript
// Fund comparison request
fetch('http://localhost:5000/api/compare', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    fundIds: ['fund1_id', 'fund2_id']
  }),
})
```

## Explainability Feature

The explainability feature can be toggled in the UI using the eye icon in the header. When enabled, search results will include score breakdowns that show how each result was ranked:

- **Semantic Score**: How well the fund matches the query semantically
- **Metadata Score**: How well the fund matches explicit filters (AMC, category, returns, etc.)
- **Fuzzy Score**: How well the fund matches by text similarity (for misspellings, etc.)
- **Final Score**: Weighted combination of all scores

### Adjusting Weights

You can adjust the scoring weights in `enhanced_retrieval.py`:

```python
self.weights = {
    'semantic': 0.6,  # Adjust semantic weight
    'metadata': 0.3,  # Adjust metadata weight
    'fuzzy': 0.1      # Adjust fuzzy match weight
}
```

## Error Handling

The UI is designed to gracefully handle API unavailability by falling back to mock data. This ensures a good user experience even during backend maintenance.

## Extending the System

### Adding New Fund Data

To add new fund data, update the preprocessing pipeline in Phase 1:

1. Add your data source to `data_preprocessing.py`
2. Run the preprocessing pipeline to generate new embeddings
3. Restart the API server to load the new data

### Adding New UI Features

The UI is built with React and shadcn-ui components. To add new features:

1. Add new React components in the `ui/src/components` folder
2. Update the services in `ui/src/services` to interact with backend APIs
3. Add new routes in `ui/src/App.tsx` if necessary

## Troubleshooting

### API Connection Issues

If the UI cannot connect to the API:

1. Ensure the API server is running on port 5000
2. Check CORS settings in `api_server.py`
3. Verify the API URL in `ui/src/services/fundService.ts`

### Search Issues

If search results are not as expected:

1. Try adjusting the weights in `enhanced_retrieval.py`
2. Run the evaluation script to measure performance: `python FINAL/evaluation.py`
3. Check the query parsing in the API server logs 