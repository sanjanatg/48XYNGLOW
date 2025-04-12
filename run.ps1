# Find My Fund - Launcher
Write-Host "Starting Find My Fund application..." -ForegroundColor Cyan

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
}
catch {
    Write-Host "Python is not installed or not in PATH. Please install Python 3.8 or higher." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Run the Python script with all arguments passed to this script
try {
    & python run.py $args
}
catch {
    Write-Host "Error running the script: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# If script exits with an error code, wait for user input
if ($LASTEXITCODE -ne 0) {
    Write-Host "Script exited with code $LASTEXITCODE" -ForegroundColor Red
    Read-Host "Press Enter to exit"
} 