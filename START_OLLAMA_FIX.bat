@echo off
title Ollama Starter (Fixed)
echo ========================================
echo      Ollama Starter (Fixed)
echo ========================================
echo.

REM Stay in the current directory
set BASE_DIR=%~dp0
cd /d %BASE_DIR%

REM Kill any existing Ollama processes
echo Checking for existing Ollama processes...
taskkill /F /IM ollama.exe >NUL 2>&1
echo Waiting for processes to terminate...
timeout /t 5 >NUL

REM Create a log file directory
if not exist "logs" mkdir logs

REM Set path to Ollama (try multiple locations)
echo Locating Ollama executable...

set OLLAMA_PATHS=(
  "%USERPROFILE%\AppData\Local\Programs\Ollama\ollama.exe"
  "%ProgramFiles%\Ollama\ollama.exe"
  "%ProgramFiles(x86)%\Ollama\ollama.exe"
  "%LOCALAPPDATA%\Ollama\ollama.exe"
)

set OLLAMA_PATH=

for %%P in %OLLAMA_PATHS% do (
  if exist %%P (
    set OLLAMA_PATH=%%P
    echo Found Ollama at: %%P
    goto :found
  )
)

echo Checking PATH for Ollama...
where ollama >NUL 2>&1
if %ERRORLEVEL% EQU 0 (
  set OLLAMA_PATH=ollama
  echo Found Ollama in PATH
  goto :found
)

:notfound
echo ========================================
echo ERROR: Ollama executable not found!
echo ========================================
echo.
echo Please install Ollama from https://ollama.ai/download
echo After installing, run this script again.
echo.
echo Press any key to exit...
pause >NUL
exit /b 1

:found
echo Using Ollama at: %OLLAMA_PATH%
echo.

REM Check if Ollama can actually run
echo Testing Ollama version...
"%OLLAMA_PATH%" -v >NUL 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo ========================================
  echo ERROR: Ollama is installed but failed to run!
  echo ========================================
  echo This could be due to missing dependencies or permissions.
  echo.
  echo Try reinstalling Ollama or running as administrator.
  echo.
  echo Press any key to exit...
  pause >NUL
  exit /b 1
)

echo Ollama version test successful.
echo.

REM Create a batch file that will keep the window open on error
echo Creating launch script...
echo @echo off > run_ollama.bat
echo cd /d %%USERPROFILE%% >> run_ollama.bat
echo echo Starting Ollama... >> run_ollama.bat
echo echo If you see this message for more than a few seconds, Ollama may have encountered an error. >> run_ollama.bat
echo. >> run_ollama.bat
echo "%OLLAMA_PATH%" serve ^> "%BASE_DIR%\logs\ollama_log.txt" 2^>^&1 >> run_ollama.bat
echo. >> run_ollama.bat
echo if %%ERRORLEVEL%% NEQ 0 ( >> run_ollama.bat
echo   echo. >> run_ollama.bat
echo   echo ========================================= >> run_ollama.bat
echo   echo ERROR: Ollama failed to start! >> run_ollama.bat
echo   echo ========================================= >> run_ollama.bat
echo   echo Error code: %%ERRORLEVEL%% >> run_ollama.bat
echo   echo. >> run_ollama.bat
echo   echo Check the log file at: "%BASE_DIR%\logs\ollama_log.txt" >> run_ollama.bat
echo   echo. >> run_ollama.bat
echo   type "%BASE_DIR%\logs\ollama_log.txt" >> run_ollama.bat
echo   echo. >> run_ollama.bat
echo   echo. >> run_ollama.bat
echo   echo Press any key to exit... >> run_ollama.bat
echo   pause ^>NUL >> run_ollama.bat
echo   exit /b %%ERRORLEVEL%% >> run_ollama.bat
echo ) >> run_ollama.bat

echo Starting Ollama in a separate window...
start "Ollama Server" cmd /k "%BASE_DIR%\run_ollama.bat"

echo.
echo Waiting for Ollama to start (15 seconds)...
timeout /t 15 >NUL

REM Check if Ollama is running
echo Checking if Ollama is running...
curl -s http://localhost:11434/api/version >NUL
if %ERRORLEVEL% NEQ 0 (
  echo ========================================
  echo WARNING: Ollama may not be running properly!
  echo ========================================
  echo.
  echo Check the Ollama window for error messages.
  echo If Ollama has not started, check the log at:
  echo %BASE_DIR%\logs\ollama_log.txt
  echo.
) else (
  echo ========================================
  echo SUCCESS: Ollama is running!
  echo ========================================
  echo.
  echo Ollama is running at http://localhost:11434
)

echo.
echo Press any key to exit this window...
pause >NUL 