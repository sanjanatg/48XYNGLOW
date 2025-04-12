@echo off
title Ollama Direct Starter
echo ========================================
echo         Ollama Direct Starter
echo ========================================
echo.
echo This script will start Ollama directly.
echo.

REM Kill any existing Ollama processes
echo Checking for existing Ollama processes...
taskkill /F /IM ollama.exe >NUL 2>&1
timeout /t 3 >NUL

REM Set path to Ollama
set OLLAMA_PATH=%USERPROFILE%\AppData\Local\Programs\Ollama\ollama.exe

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

REM Start Ollama
echo Starting Ollama...
echo.
echo When you want to stop Ollama, close this window or press Ctrl+C
echo.
cd /d %USERPROFILE%
"%OLLAMA_PATH%" serve 