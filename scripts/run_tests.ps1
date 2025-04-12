# Find My Fund Test Runner PowerShell Script

Write-Host "Starting Find My Fund test runner..." -ForegroundColor Cyan

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

# Function to check if the API server is running
function Test-ApiServer {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000/api/health" -Method GET -TimeoutSec 5 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $json = $response.Content | ConvertFrom-Json
            if ($json.status -eq "ok") {
                return $true
            }
        }
    }
    catch {
        # API server is not running
    }
    return $false
}

# Function to start Ollama
function Start-Ollama {
    Write-Host "Starting Ollama..." -ForegroundColor Cyan
    
    # Check if Ollama is already running
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:11434/api/version" -Method GET -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Host "✓ Ollama is already running" -ForegroundColor Green
            return $true
        }
    }
    catch {
        # Ollama is not running, let's start it
    }
    
    # Try to find Ollama in the default installation path
    $ollamaPath = Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"
    
    if (-not (Test-Path $ollamaPath)) {
        Write-Host "Warning: Ollama not found at $ollamaPath" -ForegroundColor Yellow
        Write-Host "Trying to run 'ollama' from PATH" -ForegroundColor Yellow
        $ollamaPath = "ollama"
    }
    
    # Start Ollama
    try {
        Start-Process -FilePath $ollamaPath -ArgumentList "serve" -WindowStyle Minimized
        
        # Wait for Ollama to start (up to 30 seconds)
        for ($i = 0; $i -lt 30; $i++) {
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:11434/api/version" -Method GET -TimeoutSec 1 -ErrorAction SilentlyContinue
                if ($response.StatusCode -eq 200) {
                    Write-Host "✓ Ollama started successfully" -ForegroundColor Green
                    return $true
                }
            }
            catch {
                # Ollama not ready yet
            }
            Write-Host "." -NoNewline
            Start-Sleep -Seconds 1
        }
        
        Write-Host ""
        Write-Host "✗ Failed to start Ollama within 30 seconds" -ForegroundColor Red
        return $false
    }
    catch {
        Write-Host "✗ Error starting Ollama: $_" -ForegroundColor Red
        return $false
    }
}

# Function to start the API server
function Start-ApiServer {
    Write-Host "Starting API server..." -ForegroundColor Cyan
    
    # Check if API server is already running
    if (Test-ApiServer) {
        Write-Host "✓ API server is already running" -ForegroundColor Green
        return $true
    }
    
    # Get the path to the API server script
    $projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
    $apiServerPath = Join-Path $projectRoot "FINAL\api_server.py"
    
    # Start the API server
    try {
        $apiDir = Split-Path -Parent $apiServerPath
        Start-Process -FilePath "python" -ArgumentList $apiServerPath -WorkingDirectory $apiDir -WindowStyle Normal
        
        # Wait for the API server to start (up to 30 seconds)
        for ($i = 0; $i -lt 30; $i++) {
            if (Test-ApiServer) {
                Write-Host "✓ API server started successfully" -ForegroundColor Green
                return $true
            }
            Write-Host "." -NoNewline
            Start-Sleep -Seconds 1
        }
        
        Write-Host ""
        Write-Host "✗ Failed to start API server within 30 seconds" -ForegroundColor Red
        return $false
    }
    catch {
        Write-Host "✗ Error starting API server: $_" -ForegroundColor Red
        return $false
    }
}

# Function to run tests
function Start-Tests {
    Write-Host "Running tests..." -ForegroundColor Cyan
    
    # Get the path to the test runner script
    $projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
    $testRunnerPath = Join-Path $projectRoot "tests\test_runner.py"
    
    # Check if the test runner script exists
    if (-not (Test-Path $testRunnerPath)) {
        Write-Host "✗ Test runner not found at $testRunnerPath" -ForegroundColor Red
        return $false
    }
    
    # Run the test runner script
    try {
        $process = Start-Process -FilePath "python" -ArgumentList $testRunnerPath -NoNewWindow -PassThru -Wait
        
        if ($process.ExitCode -eq 0) {
            Write-Host "✓ Tests completed successfully" -ForegroundColor Green
            return $true
        }
        else {
            Write-Host "✗ Tests failed with return code $($process.ExitCode)" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "✗ Error running tests: $_" -ForegroundColor Red
        return $false
    }
}

# Main process
Write-Host "Checking for required services..." -ForegroundColor Cyan

# First check if API server is already running
if (-not (Test-ApiServer)) {
    Write-Host "API server is not running." -ForegroundColor Yellow
    
    # First start Ollama if it's not running
    $ollamaStarted = Start-Ollama
    
    # Then start the API server
    $apiStarted = Start-ApiServer
    
    if (-not $apiStarted) {
        Write-Host "Failed to start API server. Cannot run tests." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Finally, run the tests
Start-Tests

Read-Host "Press Enter to exit" 