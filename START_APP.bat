@echo off
title Find My Fund - Launcher
echo ========================================
echo  Find My Fund - Launcher
echo ========================================
echo.
echo This script will launch all components of the Find My Fund application:
echo 1. Ollama with Mistral model
echo 2. Flask Backend API
echo 3. React Frontend UI
echo.

REM Check if Python is available
echo Checking Python installation...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed or not in the PATH.
    echo Please install Python and try again.
    echo You can download Python from: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

REM Check if Ollama exists
echo Checking Ollama installation...
if exist "%USERPROFILE%\AppData\Local\Programs\Ollama\ollama.exe" (
    echo Found Ollama at %USERPROFILE%\AppData\Local\Programs\Ollama\ollama.exe
) else (
    echo.
    echo WARNING: Ollama might not be installed at the expected location.
    echo If the application fails to start Ollama, please install it from:
    echo https://ollama.ai/download
    echo.
    timeout /t 3 >nul
)

REM Check if the project directories exist
echo Checking project structure...
if not exist "FINAL\api_server.py" (
    echo ERROR: Could not find FINAL\api_server.py
    echo Please make sure you're running this script from the project root directory.
    pause
    exit /b 1
)

if not exist "ui\package.json" (
    echo ERROR: Could not find ui\package.json
    echo Please make sure you're running this script from the project root directory.
    pause
    exit /b 1
)

REM Check for running processes on required ports
echo Checking ports availability...
powershell -Command "If (Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue) { Write-Host 'WARNING: Port 5000 is already in use. API server may fail to start.' }"
powershell -Command "If (Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue) { Write-Host 'WARNING: Port 3000 is already in use. UI may use port 3001 instead.' }"

echo.
echo Please wait while the application starts...
echo.

REM Launch the application using run.py
echo Starting Find My Fund Application...
python run.py

REM If the script exits with an error, provide additional instructions
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo The application encountered an error during startup.
    echo.
    echo Troubleshooting steps:
    echo 1. Make sure Ollama is installed and running
    echo 2. Check if ports 5000, 3000, and 11434 are available
    echo 3. Ensure all dependencies are installed
    echo 4. Try running 'python run.py' directly from a command prompt for more detailed error messages
    echo.
    echo See LAUNCH_INSTRUCTIONS.md for more information.
    echo.
)

REM Keep the window open
echo.
echo Application startup process has completed.
echo You can close this window, but the application components will continue running.
echo To fully stop the application, close each component window.
pause 