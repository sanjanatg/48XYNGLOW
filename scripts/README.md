# Find My Fund - Scripts

This folder contains scripts to help you run the Find My Fund application easily using Windows PowerShell.

## Requirements

- Python 3.8 or higher
- PowerShell 5.1 or higher
- Node.js 16 or higher
- Ollama installed

## Available Scripts

### 1. `run_all.ps1` - Main Application Launcher

This PowerShell script starts all components of the Find My Fund application:
1. Ollama with Mistral
2. Backend API server
3. Frontend UI

**Usage:**
```powershell
.\run_all.ps1
```

**Options:**
```powershell
.\run_all.ps1 --no-ollama   # Don't start Ollama
.\run_all.ps1 --no-api      # Don't start the API server
.\run_all.ps1 --no-ui       # Don't start the UI
.\run_all.ps1 --no-browser  # Don't open the browser
.\run_all.ps1 --run-tests   # Run tests after starting services
```

### 2. `run_tests.ps1` - Test Runner

This PowerShell script ensures that Ollama and the API server are running, then runs the test suite.

**Usage:**
```powershell
.\run_tests.ps1
```

### 3. `run_all.cmd` - Batch File Alternative

This is a batch file alternative to `run_all.ps1`. It does the same thing but can be run from a command prompt.

**Usage:**
```
run_all.cmd
```

## Manual Commands

If you prefer to run commands manually, here's what the scripts do:

### 1. Start Ollama with Mistral
```powershell
Start-Process -FilePath "C:\Users\username\AppData\Local\Programs\Ollama\ollama.exe" -ArgumentList "serve" -WindowStyle Minimized
```

### 2. Start the Backend API Server
```powershell
cd ..\FINAL
python api_server.py
```

### 3. Start the Frontend UI
```powershell
cd ..\ui
npm run dev
```

### 4. Run Tests
```powershell
cd ..\tests
python test_runner.py
```

## Troubleshooting

1. **Ollama not starting**
   - Make sure Ollama is installed
   - Check that the path to ollama.exe is correct
   - You can manually run `ollama serve` to start Ollama

2. **API server not starting**
   - Make sure you're in the FINAL directory when running api_server.py
   - Check for error messages in the terminal
   - Ensure all Python dependencies are installed

3. **UI not starting**
   - Make sure you're in the ui directory when running npm run dev
   - Ensure Node.js and npm are installed
   - Run `npm install` if modules are missing 