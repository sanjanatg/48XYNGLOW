# Find My Fund - Application Setup Instructions

## Quick Start

For the simplest experience, just run:

```
python run.py
```

This will automatically:
1. Start Ollama with Mistral model
2. Start the Flask backend API
3. Start the React frontend UI
4. Open your browser to the application

## Detailed Instructions

### Prerequisites

- Python 3.8 or higher
- Node.js 16+ and npm
- Ollama installed
- Required Python packages: `colorama`

To install the required Python package:
```
python -m pip install colorama
```

### Running the Application

The application must be started in the correct order:

1. **Ollama with Mistral model**: Handles LLM generation
2. **Flask Backend API**: Processes search requests and fund analysis
3. **React Frontend UI**: Provides the user interface

The `run.py` script handles this sequence automatically.

### Command Options

| Command | Description |
|---------|-------------|
| `python run.py` | Start all components in the correct order |
| `python run.py --no-ollama` | Start without Ollama (use if already running) |
| `python run.py --no-api` | Start without the API server (use if already running) |
| `python run.py --no-ui` | Start without the UI (backend only) |
| `python run.py --no-browser` | Don't open browser automatically |
| `python run.py --tests` | Run tests after starting all components |

### Troubleshooting

If you encounter issues with the automatic startup:

1. **Ollama not starting**:
   - Verify Ollama is installed
   - Try running `ollama serve` manually
   - Wait 10-15 seconds for Ollama to fully initialize

2. **API server not starting**:
   - Check that you're in the project root directory
   - Verify Python dependencies are installed
   - Try manually: `cd FINAL && python api_server.py`

3. **UI not starting**:
   - Check that Node.js and npm are installed
   - Try manually: `cd ui && npm run dev`

### Running Components Manually

If needed, you can start each component separately:

1. **Start Ollama**:
   ```
   ollama serve
   ```

2. **Start the API server**:
   ```
   cd FINAL
   python api_server.py
   ```

3. **Start the UI**:
   ```
   cd ui
   npm run dev
   ```

### Running Tests

To run the test suite:

```
python run.py --tests
```

Or manually:

```
cd tests
python test_runner.py
```

### Accessing the Application

- Ollama: http://localhost:11434
- API: http://localhost:5000
- UI: http://localhost:3000 or http://localhost:3001

## Alternative Startup Methods

### Using the Batch File (Windows CMD)

```
run.cmd
```

### Using PowerShell Script

```
.\run.ps1
```

## Common Issues and Solutions

1. **Port conflicts**: If any of the ports (3000, 5000, 11434) are already in use, close the conflicting applications

2. **Component timeouts**: Try starting components manually if the automatic startup times out

3. **Ollama model loading**: The first time you run the application, the Mistral model might take longer to load if it needs to be downloaded 