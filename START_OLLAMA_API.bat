@echo off
title Ollama + API Server
echo ========================================
echo    Ollama + API Server Launcher
echo ========================================
echo.
echo This script will:
echo 1. Start the Ollama server
echo 2. Start the API server
echo.

REM Get the base directory
set BASE_DIR=%~dp0
cd /d %BASE_DIR%

REM Try to locate Ollama
set OLLAMA_PATH=%USERPROFILE%\AppData\Local\Programs\Ollama\ollama.exe

if exist "%OLLAMA_PATH%" (
    echo Found Ollama at: %OLLAMA_PATH%
) else (
    echo Ollama not found at default location.
    echo Trying to use "ollama" from PATH...
    set OLLAMA_PATH=ollama
)

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

REM Verify API server exists
if not exist "FINAL\api_server.py" (
    echo ERROR: Could not find FINAL\api_server.py
    echo Please make sure you're running this script from the project root directory.
    pause
    exit /b 1
)

REM Kill any existing Ollama processes that might be stuck
echo Checking for existing Ollama processes...
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo Found existing Ollama process. Attempting to terminate...
    taskkill /F /IM ollama.exe >NUL 2>&1
    timeout /t 3 >NUL
)

REM Start Ollama with serve command in a new window
echo.
echo Starting Ollama server...
start "Ollama Server" cmd /c "cd /d %USERPROFILE% && "%OLLAMA_PATH%" serve"

REM Wait for Ollama to start
echo Waiting for Ollama to start (15 seconds)...
timeout /t 15 >nul

REM Start the API server
echo Starting API server...
start "API Server" cmd /c "cd /d %BASE_DIR%FINAL && python api_server.py"

echo.
echo Ollama and API server should now be running in separate windows.
echo.
echo - Ollama API: http://localhost:11434
echo - Backend API: http://localhost:5000
echo.
echo To stop the servers, close their respective windows.
echo.
pause 