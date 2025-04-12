@echo off
echo ===================================================
echo Find My Fund - Complete Application Startup Script
echo ===================================================
echo.

:: Check if Ollama is running
echo Checking if Ollama is already running...
curl -s http://localhost:11434/api/tags > nul
if %errorlevel% equ 0 (
    echo [✓] Ollama is already running
) else (
    echo [!] Starting Ollama server...
    start "Ollama Server" /MIN "C:\Users\sanja\AppData\Local\Programs\Ollama\ollama.exe" serve
    
    :: Wait a moment for Ollama to start
    timeout /t 5 /nobreak > nul
    
    :: Check if Ollama started successfully
    curl -s http://localhost:11434/api/tags > nul
    if %errorlevel% equ 0 (
        echo [✓] Ollama server started successfully
    ) else (
        echo [✗] Failed to start Ollama. Please start it manually with: ollama serve
        echo.
        echo Press any key to continue anyway...
        pause > nul
    )
)

:: Start the API server in the correct directory
echo.
echo Starting API server from the FINAL directory...
start "API Server" cmd /k "cd FINAL & python api_server.py"

:: Wait a moment for the API server to start
echo Waiting for API server to initialize...
timeout /t 5 /nobreak > nul

:: Check if API server is running
curl -s http://localhost:5000/api/health > nul
if %errorlevel% equ 0 (
    echo [✓] API server started successfully
) else (
    echo [!] API server may not have started. Continuing anyway...
)

:: Start the UI
echo.
echo Starting UI server...
start "UI Server" cmd /k "cd ui & npm run dev"

echo.
echo ===================================================
echo All components started!
echo.
echo - Ollama server: http://localhost:11434
echo - API server:    http://localhost:5000
echo - UI:            http://localhost:5173 (check terminal for actual port)
echo ===================================================
echo.
echo Press any key to exit this window (servers will keep running)...
pause > nul 