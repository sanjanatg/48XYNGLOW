@echo off
title Ollama - Direct Launcher
echo ========================================
echo        Ollama Direct Launcher
echo ========================================
echo.

REM Get current directory
set BASE_DIR=%~dp0
cd /d %BASE_DIR%

REM Create logs directory
if not exist "logs" mkdir logs

REM Set path to Ollama
set OLLAMA_PATH=%USERPROFILE%\AppData\Local\Programs\Ollama\ollama.exe

echo Checking for Ollama executable...

if exist "%OLLAMA_PATH%" (
  echo Found Ollama at %OLLAMA_PATH%
) else (
  where ollama >NUL 2>&1
  if %ERRORLEVEL% EQU 0 (
    set OLLAMA_PATH=ollama
    echo Found Ollama in PATH
  ) else (
    echo ERROR: Could not find Ollama!
    echo Install Ollama from https://ollama.ai/download
    pause
    exit /b 1
  )
)

REM Kill any existing Ollama processes
echo Terminating any existing Ollama processes...
taskkill /F /IM ollama.exe >NUL 2>&1
timeout /t 3 >NUL

REM This is the most important part - stay in the current window
echo Starting Ollama directly in this window...
echo.
echo If Ollama starts successfully, you'll see messages below.
echo If you see an error, it will be displayed here.
echo.
echo To stop Ollama, press Ctrl+C
echo.
echo ========================================
echo Starting Ollama...
echo ========================================
echo.

cd /d %USERPROFILE%
"%OLLAMA_PATH%" serve

REM If Ollama exits with an error, this code will run
echo.
echo ========================================
echo Ollama has stopped or encountered an error!
echo Error code: %ERRORLEVEL%
echo ========================================
echo.
echo Please check for error messages above.
echo.
pause 