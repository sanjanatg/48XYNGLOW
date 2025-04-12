@echo off
title Ollama Server
echo ========================================
echo        Ollama Server Launcher
echo ========================================
echo.
echo This script will start the Ollama server
echo.

REM Try to locate Ollama
set OLLAMA_PATH=%USERPROFILE%\AppData\Local\Programs\Ollama\ollama.exe

if exist "%OLLAMA_PATH%" (
    echo Found Ollama at: %OLLAMA_PATH%
) else (
    echo Ollama not found at default location.
    echo Trying to use "ollama" from PATH...
    set OLLAMA_PATH=ollama
)

REM Kill any existing Ollama processes that might be stuck
echo Checking for existing Ollama processes...
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo Found existing Ollama process. Attempting to terminate...
    taskkill /F /IM ollama.exe >NUL 2>&1
    timeout /t 3 >NUL
)

REM Start Ollama with serve command
echo.
echo Starting Ollama server...
echo.
echo When you want to stop Ollama, close this window or press Ctrl+C
echo.
cd /d %USERPROFILE%
"%OLLAMA_PATH%" serve

REM If Ollama exits, keep the window open so the user can see any error messages
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Ollama exited with error code: %ERRORLEVEL%
    echo.
    echo If you're having trouble, please check:
    echo 1. Ollama is properly installed
    echo 2. Port 11434 is not already in use
    echo 3. Your firewall is not blocking Ollama
    echo.
)

pause 