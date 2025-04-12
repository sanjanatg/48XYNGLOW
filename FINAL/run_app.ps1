Write-Host "Starting Fund Search Application..." -ForegroundColor Green

# Start API server in a separate window
Write-Host "Starting API Server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; python api_server.py"

# Wait a moment before starting Streamlit
Write-Host "Waiting for API server to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Start Streamlit in a separate window
Write-Host "Starting Streamlit UI..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; python -m streamlit run streamlit_app.py"

Write-Host "`nStarted both services in separate windows." -ForegroundColor Green
Write-Host "- API Server: http://localhost:5000" -ForegroundColor Magenta
Write-Host "- Streamlit UI: http://localhost:8501" -ForegroundColor Magenta
Write-Host "`nKeep the terminal windows open while using the application." -ForegroundColor Yellow 