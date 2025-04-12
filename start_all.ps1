# Simple startup script without complex syntax
Write-Host "Starting Ollama..." -ForegroundColor Cyan
Start-Process -FilePath "C:\Users\sanja\AppData\Local\Programs\Ollama\ollama.exe" -ArgumentList "serve" -WindowStyle Minimized

# Wait for Ollama to start
Start-Sleep -Seconds 5

Write-Host "Starting API server..." -ForegroundColor Cyan
$apiPath = Join-Path -Path $PSScriptRoot -ChildPath "FINAL"
Start-Process -FilePath "powershell" -ArgumentList "-Command", "cd '$apiPath'; python api_server.py"

# Wait for API server to start
Start-Sleep -Seconds 5

Write-Host "Starting UI..." -ForegroundColor Cyan
$uiPath = Join-Path -Path $PSScriptRoot -ChildPath "ui"
Start-Process -FilePath "powershell" -ArgumentList "-Command", "cd '$uiPath'; npm run dev"

Write-Host "All components started!" -ForegroundColor Green 