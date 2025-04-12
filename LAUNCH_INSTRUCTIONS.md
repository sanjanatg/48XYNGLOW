# Find My Fund - Launch Instructions

This document provides step-by-step instructions for launching the Find My Fund application.

## Prerequisites

Before starting the application, make sure you have:

1. **Python** installed (version 3.8 or higher)
2. **Node.js and npm** installed for the UI
3. **Ollama** installed with the Mistral model available

## Quick Start Methods

Choose one of the following methods to start the application:

### Method 1: Using the Batch File (Recommended for Windows)

1. Double-click the `START_APP.bat` file in Windows Explorer
2. The batch file will launch all components in sequence:
   - Ollama with Mistral model
   - Flask Backend API
   - React Frontend UI
3. Once all components are running, your browser should open automatically to the UI

### Method 2: Using PowerShell (Better Visual Output)

1. Right-click on `START_APP.ps1` and select "Run with PowerShell"
   - If you get a security warning, you may need to run: `Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process`
2. The PowerShell script will launch all components with colored status messages
3. Once all components are running, your browser should open automatically to the UI

### Method 3: Using Python Directly

Run the following command in your terminal:

```
python run.py
```

## Component Details

The application consists of three main components:

1. **Ollama** - Serves the Mistral language model
   - Default port: 11434
   - Status URL: http://localhost:11434/api/version

2. **Backend API** - Flask server that handles search requests
   - Default port: 5000
   - Status URL: http://localhost:5000/api/health

3. **Frontend UI** - React application for user interaction
   - Default port: 3000 (may use 3001 if 3000 is in use)
   - URL: http://localhost:3000 or http://localhost:3001

## Troubleshooting

If you encounter issues:

1. **Ollama not starting**: 
   - Ensure Ollama is installed correctly
   - Check if it's already running in another process

2. **API server errors**:
   - Check the API window for error messages
   - Verify that all Python dependencies are installed

3. **UI not starting**:
   - Ensure Node.js and npm are installed
   - Check if the UI is already running on port 3000 or 3001

4. **Connection errors**:
   - Verify that all components are running
   - Check for firewall restrictions on the ports

## Stopping the Application

To stop the application:

1. Close each component window (Ollama, API, UI)
2. Or press Ctrl+C in the terminal where you started the application (components will continue running)

## Advanced Options

The run.py script accepts several command-line options:

```
python run.py --no-ollama     # Don't start Ollama
python run.py --no-api        # Don't start API server
python run.py --no-ui         # Don't start UI
python run.py --no-browser    # Don't open browser
``` 