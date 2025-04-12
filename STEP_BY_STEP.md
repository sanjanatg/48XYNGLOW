# Find My Fund - Step-by-Step Startup Guide

This guide provides exact instructions for starting the Find My Fund application in the correct sequence.

## ONE-COMMAND STARTUP (RECOMMENDED)

From the project root directory:

```
python run.py
```

This single command will handle everything for you in the correct order:
1. Start Ollama with Mistral
2. Start the Flask backend API
3. Start the React frontend UI
4. Open your browser

## MANUAL STARTUP (IF NEEDED)

If you prefer starting each component separately or need more control, follow these exact steps:

### STEP 1: Start Ollama

```
ollama serve
```

Wait until you see that Ollama is running (usually takes 5-10 seconds).

### STEP 2: Start the Flask Backend API

In a new terminal window:

```
cd FINAL
python api_server.py
```

Wait until you see the message that the API server is running (usually takes 10-15 seconds).

### STEP 3: Start the React Frontend UI

In a third terminal window:

```
cd ui
npm run dev
```

Wait until the development server is ready (usually takes 10-20 seconds).

### STEP 4: Open the Application

Open your web browser and navigate to:
```
http://localhost:3000
```

(If port 3000 is already in use, try http://localhost:3001)

## VERIFYING COMPONENTS ARE RUNNING

To check if all components are running correctly:

1. **Ollama**: Visit http://localhost:11434/api/version in your browser - should show a JSON response
2. **API Server**: Visit http://localhost:5000/api/health - should show status "ok"
3. **UI**: Visit http://localhost:3000 or http://localhost:3001 - should show the application interface

## STOPPING THE APPLICATION

To properly stop all components:

1. Close the browser tab with the UI
2. Press Ctrl+C in each terminal window to stop each service
3. Start with the UI first, then the API, then Ollama

## RUNNING TESTS

To run the test suite after all components are running:

```
cd tests
python test_runner.py
```

## COMMON ERRORS AND SOLUTIONS

1. **"Ollama not found"**: Make sure Ollama is installed and in your PATH
2. **"API server not starting"**: Check all Python dependencies are installed
3. **"UI not starting"**: Make sure Node.js and npm are installed and run `npm install` in the ui directory first 