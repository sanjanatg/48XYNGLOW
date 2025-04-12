# Find My Fund - PowerShell Launcher
$host.UI.RawUI.WindowTitle = "Find My Fund - Launcher"

# Define colors
$colors = @{
    Green = [ConsoleColor]::Green
    Cyan = [ConsoleColor]::Cyan
    Yellow = [ConsoleColor]::Yellow
    Red = [ConsoleColor]::Red
    Blue = [ConsoleColor]::Blue
}

# Function to write colored text
function Write-ColoredText {
    param (
        [string]$Message,
        [ConsoleColor]$Color = [ConsoleColor]::White
    )
    
    Write-Host $Message -ForegroundColor $Color
}

# Draw header
Write-ColoredText "========================================" -Color $colors.Blue
Write-ColoredText "  Find My Fund - PowerShell Launcher" -Color $colors.Blue
Write-ColoredText "========================================" -Color $colors.Blue
Write-Host ""

Write-Host "This script will launch all components of the Find My Fund application:"
Write-ColoredText "1. Ollama with Mistral model" -Color $colors.Cyan
Write-ColoredText "2. Flask Backend API" -Color $colors.Cyan
Write-ColoredText "3. React Frontend UI" -Color $colors.Cyan
Write-Host ""

# Check for Administrator rights
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-ColoredText "Note: This script is not running with Administrator privileges." -Color $colors.Yellow
    Write-ColoredText "Some operations may require elevated privileges." -Color $colors.Yellow
    Write-Host ""
}

# Check if Python is installed
Write-Host "Checking dependencies..." -NoNewline
try {
    $pythonVersion = (python --version 2>&1).ToString()
    Write-ColoredText " ✓ Python detected: $pythonVersion" -Color $colors.Green
}
catch {
    Write-ColoredText " ✗ Python not found!" -Color $colors.Red
    Write-Host "Please install Python from https://www.python.org/downloads/"
    Read-Host "Press Enter to exit"
    exit 1
}

# Check for Ollama
Write-Host "Checking for Ollama..." -NoNewline
$ollamaPath = "$env:USERPROFILE\AppData\Local\Programs\Ollama\ollama.exe"
if (Test-Path $ollamaPath) {
    Write-ColoredText " ✓ Ollama detected at $ollamaPath" -Color $colors.Green
} else {
    try {
        $ollamaVersion = (ollama -v 2>&1).ToString()
        Write-ColoredText " ✓ Ollama detected in PATH: $ollamaVersion" -Color $colors.Green
    }
    catch {
        Write-ColoredText " ✗ Ollama not found!" -Color $colors.Yellow
        Write-Host "You can download Ollama from https://ollama.ai/download"
        Write-Host "The application will attempt to continue, but some features may not work."
        Write-Host ""
    }
}

# Check project structure
Write-Host "Checking project structure..." -NoNewline
$apiServerPath = "FINAL\api_server.py"
$uiPackagePath = "ui\package.json"

if (-not (Test-Path $apiServerPath)) {
    Write-ColoredText " ✗ API server not found at $apiServerPath" -Color $colors.Red
    Write-Host "Please make sure you're running this script from the project root directory."
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Test-Path $uiPackagePath)) {
    Write-ColoredText " ✗ UI package.json not found at $uiPackagePath" -Color $colors.Red
    Write-Host "Please make sure you're running this script from the project root directory."
    Read-Host "Press Enter to exit"
    exit 1
}

Write-ColoredText " ✓ Project structure looks good" -Color $colors.Green

# Check port availability
Write-Host "Checking port availability..." -NoNewline
$port5000InUse = $false
$port3000InUse = $false
$port11434InUse = $false

try {
    $port5000InUse = [bool](Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue)
    $port3000InUse = [bool](Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue)
    $port11434InUse = [bool](Get-NetTCPConnection -LocalPort 11434 -ErrorAction SilentlyContinue)
    
    if ($port5000InUse -or $port3000InUse -or $port11434InUse) {
        Write-ColoredText " ⚠ Some ports are already in use:" -Color $colors.Yellow
        if ($port5000InUse) { Write-ColoredText "   - Port 5000 (API Server) is in use" -Color $colors.Yellow }
        if ($port3000InUse) { Write-ColoredText "   - Port 3000 (UI) is in use" -Color $colors.Yellow }
        if ($port11434InUse) { Write-ColoredText "   - Port 11434 (Ollama) is in use" -Color $colors.Yellow }
    } else {
        Write-ColoredText " ✓ Required ports are available" -Color $colors.Green
    }
}
catch {
    Write-ColoredText " ⚠ Could not check port availability" -Color $colors.Yellow
}

# Launch the application
Write-Host ""
Write-ColoredText "Starting application..." -Color $colors.Yellow
Write-Host ""

# Run the Python script
$result = $null
try {
    $result = python run.py
    $exitCode = $LASTEXITCODE
    
    if ($exitCode -ne 0) {
        Write-ColoredText "Application exited with error code: $exitCode" -Color $colors.Red
        Write-Host ""
        Write-ColoredText "Troubleshooting steps:" -Color $colors.Yellow
        Write-Host "1. Make sure Ollama is installed and running"
        Write-Host "2. Check if ports 5000, 3000, and 11434 are available"
        Write-Host "3. Ensure all dependencies are installed"
        Write-Host "4. Try running 'python run.py' directly from a command prompt for more detailed error messages"
        Write-Host ""
        Write-Host "See LAUNCH_INSTRUCTIONS.md for more information."
    }
}
catch {
    Write-ColoredText "Error running the application: $_" -Color $colors.Red
}

# Keep console open after script completes
Write-Host ""
if ($exitCode -eq 0) {
    Write-ColoredText "Application startup has completed successfully." -Color $colors.Green
} else {
    Write-ColoredText "Application startup process has completed with issues." -Color $colors.Yellow
}
Write-Host "You can close this window, but the application components will continue running."
Write-Host "To fully stop the application, close each component window."
Read-Host "Press Enter to exit" 