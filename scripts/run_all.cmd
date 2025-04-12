@echo off
echo Starting Find My Fund application...

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Python is not installed or not in PATH. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Check if dependencies are installed
python -c "import psutil" >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Installing required dependencies...
    pip install psutil colorama
)

REM Get the directory of this script
set "SCRIPT_DIR=%~dp0"

REM Run the Python script with any passed arguments
python "%SCRIPT_DIR%run_all.py" %*

REM If there was an error, pause
if %ERRORLEVEL% neq 0 pause 