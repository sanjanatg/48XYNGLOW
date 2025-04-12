@echo off
echo Starting Fund Search Application...

echo Starting API Server...
start cmd /k "python api_server.py"

echo Starting Streamlit UI...
timeout /t 3
start cmd /k "streamlit run streamlit_app.py"

echo Started both services in separate windows.
echo Press any key to exit this window.
pause > nul 