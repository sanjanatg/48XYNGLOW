@echo off
echo Starting Ollama...
start /min "Ollama" "C:\Users\sanja\AppData\Local\Programs\Ollama\ollama.exe" serve

timeout /t 5 /nobreak > nul

echo Starting API server...
start "API Server" cmd /k "cd FINAL & python api_server.py"

timeout /t 5 /nobreak > nul

echo Starting UI...
start "UI" cmd /k "cd ui & npm run dev"

echo All components started!
echo - Ollama: http://localhost:11434
echo - API: http://localhost:5000
echo - UI: http://localhost:3001 