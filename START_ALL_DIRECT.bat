@echo off
title Find My Fund - Direct Launcher
echo ========================================
echo    Find My Fund - Direct Launcher
echo ========================================
echo.
echo Starting all components directly...
echo.

REM Get the current directory
set BASE_DIR=%~dp0
cd /d %BASE_DIR%

REM Kill any existing Ollama processes
echo Checking for existing Ollama processes...
taskkill /F /IM ollama.exe >NUL 2>&1

REM Set paths
set OLLAMA_PATH=%USERPROFILE%\AppData\Local\Programs\Ollama\ollama.exe
set API_DIR=%BASE_DIR%FINAL
set UI_DIR=%BASE_DIR%ui

REM Check if Ollama exists
if not exist "%OLLAMA_PATH%" (
    echo Ollama not found at default location, checking PATH...
    where ollama >NUL 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: Ollama not found. Please install Ollama from https://ollama.ai/download
        pause
        exit /b 1
    ) else (
        set OLLAMA_PATH=ollama
    )
)

REM Start Ollama in its own window
echo Starting Ollama...
start "Ollama Server" cmd /k "cd /d %USERPROFILE% && "%OLLAMA_PATH%" serve"

REM Wait for Ollama to start
echo Waiting for Ollama to start (15 seconds)...
timeout /t 15 >NUL

REM Start the API server
echo Starting API server...
start "API Server" cmd /k "cd /d %API_DIR% && python api_server.py"

REM Wait for API server to start
echo Waiting for API server to start (10 seconds)...
timeout /t 10 >NUL

REM Start the UI
echo Starting UI...
start "UI Server" cmd /k "cd /d %UI_DIR% && npm run dev"

REM Wait for UI to start
echo Waiting for UI to start (10 seconds)...
timeout /t 10 >NUL

REM Open browser
echo Opening browser...
start http://localhost:3000

echo.
echo All components have been started:
echo - Ollama is running at http://localhost:11434
echo - API server is running at http://localhost:5000
echo - UI is running at http://localhost:3000
echo.
echo To stop the application, close all component windows.
echo.
pause 