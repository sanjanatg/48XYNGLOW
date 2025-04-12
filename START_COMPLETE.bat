@echo off
title Find My Fund - Complete Launcher
echo ========================================
echo   Find My Fund - Complete Launcher
echo ========================================
echo.

REM Set up environment
setlocal EnableDelayedExpansion
set BASE_DIR=%~dp0
cd /d %BASE_DIR%

REM Create logs directory
if not exist "logs" mkdir logs

REM Initialize log file
set LOG_FILE=%BASE_DIR%\logs\startup_%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log
echo [%date% %time%] Starting Find My Fund application > %LOG_FILE%

echo Step 1: Checking for existing Ollama processes...
echo [%date% %time%] Checking for existing Ollama processes >> %LOG_FILE%
taskkill /F /IM ollama.exe >NUL 2>&1
echo Waiting for processes to terminate...
timeout /t 5 >NUL

echo Step 2: Locating Ollama executable...
echo [%date% %time%] Locating Ollama executable >> %LOG_FILE%

REM Check common Ollama installation locations
set FOUND_OLLAMA=0
for %%L in (
  "%USERPROFILE%\AppData\Local\Programs\Ollama\ollama.exe"
  "%ProgramFiles%\Ollama\ollama.exe"
  "%ProgramFiles(x86)%\Ollama\ollama.exe"
  "%LOCALAPPDATA%\Ollama\ollama.exe"
) do (
  if exist %%L (
    set OLLAMA_PATH=%%L
    set FOUND_OLLAMA=1
    echo Found Ollama at: !OLLAMA_PATH!
    echo [%date% %time%] Found Ollama at: !OLLAMA_PATH! >> %LOG_FILE%
    goto :ollama_found
  )
)

REM Check if Ollama is in PATH
where ollama >NUL 2>&1
if %ERRORLEVEL% EQU 0 (
  set OLLAMA_PATH=ollama
  set FOUND_OLLAMA=1
  echo Found Ollama in PATH
  echo [%date% %time%] Found Ollama in PATH >> %LOG_FILE%
  goto :ollama_found
)

:ollama_not_found
echo [%date% %time%] ERROR: Ollama executable not found >> %LOG_FILE%
echo ========================================
echo ERROR: Ollama executable not found!
echo ========================================
echo.
echo Please install Ollama from https://ollama.ai/download
echo After installing, run this script again.
echo.
echo Do you want to continue without Ollama? (y/n)
set /p CONTINUE_WITHOUT_OLLAMA=
if /I "%CONTINUE_WITHOUT_OLLAMA%"=="y" (
  echo [%date% %time%] User chose to continue without Ollama >> %LOG_FILE%
  goto :skip_ollama
)
echo Exiting...
echo [%date% %time%] Exiting due to Ollama not found >> %LOG_FILE%
pause
exit /b 1

:ollama_found
echo Testing Ollama version...
echo [%date% %time%] Testing Ollama version >> %LOG_FILE%
"%OLLAMA_PATH%" -v >NUL 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo [%date% %time%] ERROR: Ollama version check failed >> %LOG_FILE%
  echo ========================================
  echo ERROR: Ollama is installed but failed to run!
  echo ========================================
  echo This could be due to missing dependencies or permissions.
  echo.
  echo Do you want to continue without Ollama? (y/n)
  set /p CONTINUE_WITHOUT_OLLAMA=
  if /I "%CONTINUE_WITHOUT_OLLAMA%"=="y" (
    echo [%date% %time%] User chose to continue without Ollama >> %LOG_FILE%
    goto :skip_ollama
  )
  echo Exiting...
  echo [%date% %time%] Exiting due to Ollama version check failure >> %LOG_FILE%
  pause
  exit /b 1
)

echo Step 3: Creating Ollama launch script...
echo [%date% %time%] Creating Ollama launch script >> %LOG_FILE%
(
echo @echo off
echo cd /d %%USERPROFILE%%
echo echo Starting Ollama...
echo echo If you see this message for more than a few seconds, Ollama may have encountered an error.
echo.
echo "%OLLAMA_PATH%" serve ^> "%BASE_DIR%\logs\ollama_log.txt" 2^>^&1
echo.
echo if %%ERRORLEVEL%% NEQ 0 (
echo   echo.
echo   echo =========================================
echo   echo ERROR: Ollama failed to start!
echo   echo =========================================
echo   echo Error code: %%ERRORLEVEL%%
echo   echo.
echo   echo Check the log file at: "%BASE_DIR%\logs\ollama_log.txt"
echo   echo.
echo   type "%BASE_DIR%\logs\ollama_log.txt"
echo   echo.
echo   echo.
echo   echo Press any key to exit...
echo   pause ^>NUL
echo   exit /b %%ERRORLEVEL%%
echo )
) > run_ollama.bat

echo Step 4: Starting Ollama...
echo [%date% %time%] Starting Ollama >> %LOG_FILE%
start "Ollama Server" cmd /k "%BASE_DIR%\run_ollama.bat"

echo Waiting for Ollama to start (20 seconds)...
echo [%date% %time%] Waiting for Ollama to start (20 seconds) >> %LOG_FILE%
timeout /t 20 >NUL

echo Checking if Ollama is running...
echo [%date% %time%] Checking if Ollama is running >> %LOG_FILE%
curl -s http://localhost:11434/api/version >NUL
if %ERRORLEVEL% NEQ 0 (
  echo [%date% %time%] WARNING: Ollama may not be running properly >> %LOG_FILE%
  echo ========================================
  echo WARNING: Ollama may not be running properly!
  echo ========================================
  echo.
  echo Check the Ollama window for error messages.
  echo If Ollama has not started, check the log at:
  echo %BASE_DIR%\logs\ollama_log.txt
  echo.
  echo Do you want to continue anyway? (y/n)
  set /p CONTINUE_ANYWAY=
  if /I not "!CONTINUE_ANYWAY!"=="y" (
    echo Exiting...
    echo [%date% %time%] Exiting due to Ollama not running properly >> %LOG_FILE%
    pause
    exit /b 1
  )
  echo [%date% %time%] User chose to continue despite Ollama issues >> %LOG_FILE%
) else (
  echo [%date% %time%] SUCCESS: Ollama is running >> %LOG_FILE%
  echo ========================================
  echo SUCCESS: Ollama is running!
  echo ========================================
  echo.
)

:skip_ollama

echo Step 5: Checking API server location...
echo [%date% %time%] Checking API server location >> %LOG_FILE%
set API_DIR=%BASE_DIR%FINAL
if not exist "%API_DIR%\api_server.py" (
  echo [%date% %time%] ERROR: API server not found at %API_DIR%\api_server.py >> %LOG_FILE%
  echo ========================================
  echo ERROR: API server not found!
  echo ========================================
  echo Could not find API server at: %API_DIR%\api_server.py
  echo.
  echo Make sure you're running this from the project root directory.
  echo.
  pause
  exit /b 1
)

echo Step 6: Starting API server...
echo [%date% %time%] Starting API server >> %LOG_FILE%

REM Create API server launch script
(
echo @echo off
echo cd /d "%API_DIR%"
echo echo Starting API server...
echo python api_server.py ^> "%BASE_DIR%\logs\api_log.txt" 2^>^&1
echo if %%ERRORLEVEL%% NEQ 0 (
echo   echo.
echo   echo =========================================
echo   echo ERROR: API server failed to start!
echo   echo =========================================
echo   echo Error code: %%ERRORLEVEL%%
echo   echo.
echo   echo Check the log file at: "%BASE_DIR%\logs\api_log.txt"
echo   echo.
echo   type "%BASE_DIR%\logs\api_log.txt"
echo   echo.
echo   echo Press any key to exit...
echo   pause ^>NUL
echo )
) > run_api.bat

start "API Server" cmd /k "%BASE_DIR%\run_api.bat"

echo Waiting for API server to start (15 seconds)...
echo [%date% %time%] Waiting for API server to start (15 seconds) >> %LOG_FILE%
timeout /t 15 >NUL

echo Checking if API server is running...
echo [%date% %time%] Checking if API server is running >> %LOG_FILE%
curl -s http://localhost:5000/api/health >NUL
if %ERRORLEVEL% NEQ 0 (
  echo [%date% %time%] WARNING: API server may not be running properly >> %LOG_FILE%
  echo ========================================
  echo WARNING: API server may not be running properly!
  echo ========================================
  echo.
  echo Check the API server window for error messages.
  echo If the API server has not started, check the log at:
  echo %BASE_DIR%\logs\api_log.txt
  echo.
  echo Do you want to continue anyway? (y/n)
  set /p CONTINUE_ANYWAY=
  if /I not "!CONTINUE_ANYWAY!"=="y" (
    echo Exiting...
    echo [%date% %time%] Exiting due to API server not running properly >> %LOG_FILE%
    pause
    exit /b 1
  )
  echo [%date% %time%] User chose to continue despite API server issues >> %LOG_FILE%
) else (
  echo [%date% %time%] SUCCESS: API server is running >> %LOG_FILE%
  echo ========================================
  echo SUCCESS: API server is running!
  echo ========================================
  echo.
)

echo Step 7: Checking UI location...
echo [%date% %time%] Checking UI location >> %LOG_FILE%
set UI_DIR=%BASE_DIR%ui
if not exist "%UI_DIR%\package.json" (
  echo [%date% %time%] ERROR: UI not found at %UI_DIR%\package.json >> %LOG_FILE%
  echo ========================================
  echo ERROR: UI not found!
  echo ========================================
  echo Could not find UI at: %UI_DIR%\package.json
  echo.
  echo Make sure you're running this from the project root directory.
  echo.
  pause
  exit /b 1
)

echo Step 8: Starting UI...
echo [%date% %time%] Starting UI >> %LOG_FILE%

REM Create UI launch script
(
echo @echo off
echo cd /d "%UI_DIR%"
echo echo Starting UI...
echo npm run dev ^> "%BASE_DIR%\logs\ui_log.txt" 2^>^&1
echo if %%ERRORLEVEL%% NEQ 0 (
echo   echo.
echo   echo =========================================
echo   echo ERROR: UI failed to start!
echo   echo =========================================
echo   echo Error code: %%ERRORLEVEL%%
echo   echo.
echo   echo Check the log file at: "%BASE_DIR%\logs\ui_log.txt"
echo   echo.
echo   type "%BASE_DIR%\logs\ui_log.txt"
echo   echo.
echo   echo Press any key to exit...
echo   pause ^>NUL
echo )
) > run_ui.bat

start "UI Server" cmd /k "%BASE_DIR%\run_ui.bat"

echo Waiting for UI to start (15 seconds)...
echo [%date% %time%] Waiting for UI to start (15 seconds) >> %LOG_FILE%
timeout /t 15 >NUL

echo Step 9: Opening browser...
echo [%date% %time%] Opening browser >> %LOG_FILE%
start http://localhost:3000
echo [%date% %time%] Browser opened to http://localhost:3000 >> %LOG_FILE%

echo.
echo [%date% %time%] All components started >> %LOG_FILE%
echo ========================================
echo Find My Fund application started!
echo ========================================
echo.
echo All components have been started:
echo - Ollama: http://localhost:11434
echo - API server: http://localhost:5000
echo - UI: http://localhost:3000
echo.
echo Check individual windows for component-specific errors.
echo Logs are available in the logs directory:
echo - Ollama log: %BASE_DIR%\logs\ollama_log.txt
echo - API log: %BASE_DIR%\logs\api_log.txt
echo - UI log: %BASE_DIR%\logs\ui_log.txt
echo.
echo To stop the application, close all component windows.
echo.
echo Press any key to exit this launcher...
pause >NUL 