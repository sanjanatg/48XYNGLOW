@echo off
echo Starting Find My Fund application...

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Python is not installed or not in PATH. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Run the Python script with any passed arguments
python run.py %*

REM If script fails, wait for user input
if %ERRORLEVEL% neq 0 (
    echo.
    echo Script exited with an error. Please check the output above.
    pause
) 