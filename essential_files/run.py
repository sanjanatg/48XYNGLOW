#!/usr/bin/env python
"""
Find My Fund - All-in-One Launcher Script
This script launches all components of the Find My Fund application:
1. Ollama with Mistral
2. Flask Backend API
3. React Frontend UI
4. Test Runner (optional)
"""

import os
import sys
import time
import argparse
import subprocess
import webbrowser
from pathlib import Path
import signal
import json

# Get the base directory (where this script is located)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define component paths
OLLAMA_PATH = os.path.expanduser("~\\AppData\\Local\\Programs\\Ollama\\ollama.exe")
BACKEND_DIR = os.path.join(BASE_DIR, "FINAL")
BACKEND_SCRIPT = os.path.join(BACKEND_DIR, "api_server.py")
UI_DIR = os.path.join(BASE_DIR, "ui")
TESTS_DIR = os.path.join(BASE_DIR, "tests")
TEST_RUNNER = os.path.join(TESTS_DIR, "test_runner.py")

# Define ports
OLLAMA_PORT = 11434
API_PORT = 5000
UI_PORT = 3000  # May change to 3001 if 3000 is in use

# Define colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# Function to print colored messages
def print_colored(message, color=Colors.RESET, bold=False):
    if bold:
        print(f"{Colors.BOLD}{color}{message}{Colors.RESET}")
    else:
        print(f"{color}{message}{Colors.RESET}")

# Function to check if a port is in use
def is_port_in_use(port):
    """Check if a port is in use using PowerShell"""
    try:
        check_cmd = f'powershell -Command "Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count"'
        result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
        return int(result.stdout.strip()) > 0
    except:
        return False

# Function to check API health
def check_api_health():
    """Check if the API server is running and healthy"""
    try:
        check_cmd = 'powershell -Command "Invoke-RestMethod -Uri \'http://localhost:5000/api/health\' -Method GET -TimeoutSec 2 -ErrorAction SilentlyContinue | ConvertTo-Json"'
        result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            try:
                health_data = json.loads(result.stdout)
                if health_data.get("status") == "ok":
                    return True, health_data.get("ollama_available", False)
            except:
                pass
        return False, False
    except:
        return False, False

# Function to check Ollama status
def check_ollama():
    """Check if Ollama is running"""
    try:
        check_cmd = 'powershell -Command "Invoke-RestMethod -Uri \'http://localhost:11434/api/version\' -Method GET -TimeoutSec 2 -ErrorAction SilentlyContinue"'
        result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0 and result.stdout.strip()
    except:
        return False

# Function to start Ollama
def start_ollama(mistral=True):
    """Start Ollama server and optionally load Mistral model"""
    if check_ollama():
        print_colored("✅ Ollama is already running", Colors.GREEN)
        # Check if Mistral model is available
        if mistral:
            check_model_cmd = 'powershell -Command "Invoke-RestMethod -Uri \'http://localhost:11434/api/tags\' -Method GET -TimeoutSec 2 -ErrorAction SilentlyContinue | ConvertTo-Json -Depth 10"'
            result = subprocess.run(check_model_cmd, shell=True, capture_output=True, text=True)
            has_mistral = False
            if result.returncode == 0 and result.stdout.strip():
                try:
                    models_data = json.loads(result.stdout)
                    if "models" in models_data:
                        for model in models_data["models"]:
                            if "mistral" in model.get("name", "").lower():
                                has_mistral = True
                                print_colored(f"✅ Mistral model is available: {model.get('name')}", Colors.GREEN)
                                break
                except:
                    pass
            
            if not has_mistral:
                print_colored("⚠️ Mistral model might not be available. Attempting to pull it...", Colors.YELLOW)
                pull_cmd = 'powershell -Command "Start-Process -FilePath \'ollama\' -ArgumentList \'pull mistral\' -WindowStyle Normal"'
                print_colored(f"📋 Executing: {pull_cmd}", Colors.BLUE)
                subprocess.run(pull_cmd, shell=True)
        return True
    
    print_colored("🚀 Starting Ollama...", Colors.CYAN)
    
    # Check if Ollama exists at the default path
    if not os.path.exists(OLLAMA_PATH):
        print_colored(f"⚠️ Ollama not found at {OLLAMA_PATH}", Colors.YELLOW)
        print_colored("⚠️ Trying 'ollama' from PATH", Colors.YELLOW)
        ollama_cmd = "ollama"
    else:
        ollama_cmd = OLLAMA_PATH
    
    # Check if Ollama is installed
    try:
        version_cmd = f'powershell -Command "& \'{ollama_cmd}\' -v"'
        version_result = subprocess.run(version_cmd, shell=True, capture_output=True, text=True)
        if version_result.returncode != 0:
            print_colored("❌ Ollama is not installed or not in PATH", Colors.RED)
            print_colored("⚠️ Please install Ollama from https://ollama.ai/download", Colors.YELLOW)
            print_colored("⚠️ Continuing without Ollama (some features may not work)", Colors.YELLOW)
            return False
    except:
        print_colored("⚠️ Could not verify Ollama installation", Colors.YELLOW)
    
    # First, check if a process is already running but not responding
    try:
        # Use tasklist instead of PowerShell for better reliability
        process_cmd = 'tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe"'
        process_result = subprocess.run(process_cmd, shell=True, capture_output=True, text=True)
        
        if "ollama.exe" in process_result.stdout:
            print_colored("⚠️ Ollama process detected but API not responding", Colors.YELLOW)
            print_colored("⚠️ Attempting to stop existing process...", Colors.YELLOW)
            
            # Use taskkill instead of PowerShell for better reliability
            kill_cmd = 'taskkill /F /IM ollama.exe >NUL 2>&1'
            subprocess.run(kill_cmd, shell=True)
            time.sleep(3)  # Wait longer for process to terminate
    except:
        pass
    
    # Create and use a temporary batch file (most reliable method)
    temp_batch_path = os.path.join(BASE_DIR, "temp_start_ollama.bat")
    try:
        with open(temp_batch_path, "w") as batch_file:
            batch_file.write("@echo off\n")
            batch_file.write(f"cd /d %USERPROFILE%\n")
            batch_file.write(f"start \"Ollama Server\" cmd /c \"{ollama_cmd}\" serve\n")
        
        print_colored(f"📋 Executing batch file to start Ollama", Colors.BLUE)
        subprocess.run(temp_batch_path, shell=True)
    except Exception as e:
        print_colored(f"⚠️ Error with batch file method: {str(e)}", Colors.YELLOW)
        # Fallback to direct command if batch file fails
        try:
            direct_cmd = f'start "Ollama Server" cmd /c "cd /d %USERPROFILE% && "{ollama_cmd}" serve"'
            print_colored(f"📋 Executing direct command: {direct_cmd}", Colors.BLUE)
            subprocess.run(direct_cmd, shell=True)
        except Exception as e:
            print_colored(f"⚠️ Error with direct command: {str(e)}", Colors.YELLOW)
    
    # Wait for Ollama to start
    print_colored("⏳ Waiting for Ollama to start...", Colors.CYAN)
    for i in range(90):  # Increased timeout to 90 seconds
        if check_ollama():
            print_colored("✅ Ollama started successfully", Colors.GREEN)
            
            # Load Mistral model if requested
            if mistral:
                print_colored("🧠 Loading Mistral model...", Colors.CYAN)
                print_colored("⏳ Checking if Mistral model is already available...", Colors.CYAN)
                
                check_model_cmd = 'powershell -Command "Invoke-RestMethod -Uri \'http://localhost:11434/api/tags\' -Method GET -TimeoutSec 2 -ErrorAction SilentlyContinue | ConvertTo-Json -Depth 10"'
                result = subprocess.run(check_model_cmd, shell=True, capture_output=True, text=True)
                has_mistral = False
                
                if result.returncode == 0 and result.stdout.strip():
                    try:
                        models_data = json.loads(result.stdout)
                        if "models" in models_data:
                            for model in models_data["models"]:
                                if "mistral" in model.get("name", "").lower():
                                    has_mistral = True
                                    print_colored(f"✅ Mistral model is available: {model.get('name')}", Colors.GREEN)
                                    break
                    except:
                        pass
                
                if not has_mistral:
                    print_colored("⚠️ Mistral model not found. Pulling from Ollama library...", Colors.YELLOW)
                    # Use the direct command approach that's most reliable
                    pull_cmd = f'start "Ollama Pull" cmd /c "cd /d %USERPROFILE% && "{ollama_cmd}" pull mistral"'
                    print_colored(f"📋 Executing: {pull_cmd}", Colors.BLUE)
                    try:
                        subprocess.Popen(pull_cmd, shell=True)
                    except Exception as e:
                        print_colored(f"⚠️ Error pulling model: {str(e)}", Colors.YELLOW)
                    
                    # Wait for a few seconds to let the pull start
                    time.sleep(5)
                    print_colored("⏳ Model download started. This may take several minutes in the background.", Colors.CYAN)
                    print_colored("⏳ Continuing with application startup...", Colors.CYAN)
                else:
                    # Run the model using direct command approach
                    run_cmd = f'start "Ollama Run" cmd /c "cd /d %USERPROFILE% && "{ollama_cmd}" run mistral"'
                    print_colored(f"📋 Executing: {run_cmd}", Colors.BLUE)
                    try:
                        subprocess.run(run_cmd, shell=True)
                    except Exception as e:
                        print_colored(f"⚠️ Error running model: {str(e)}", Colors.YELLOW)
                    
                    print_colored("✅ Mistral model loading initiated", Colors.GREEN)
            
            # Clean up temp batch file if it exists
            try:
                if os.path.exists(temp_batch_path):
                    os.remove(temp_batch_path)
            except:
                pass
                
            return True
        
        if i % 5 == 0:  # Show progress indicator every 5 seconds
            print(f"{i}s...", end="", flush=True)
        else:
            print(".", end="", flush=True)
        time.sleep(1)
    
    print()  # New line after dots
    print_colored("❌ Failed to start Ollama within 90 seconds", Colors.RED)
    
    # Fallback to using START_OLLAMA.bat if it exists
    start_ollama_bat = os.path.join(BASE_DIR, "START_OLLAMA.bat")
    if os.path.exists(start_ollama_bat):
        print_colored("⚠️ Attempting to start Ollama using START_OLLAMA.bat...", Colors.YELLOW)
        try:
            subprocess.Popen(start_ollama_bat, shell=True)
            print_colored("✅ START_OLLAMA.bat launched. Please wait for Ollama to start.", Colors.GREEN)
            print_colored("⚠️ Once Ollama is running, restart this application.", Colors.YELLOW)
        except Exception as e:
            print_colored(f"❌ Error launching START_OLLAMA.bat: {str(e)}", Colors.RED)
    else:
        print_colored("⚠️ START_OLLAMA.bat not found. Please start Ollama manually.", Colors.YELLOW)
    
    # Clean up temp batch file if it exists
    try:
        if os.path.exists(temp_batch_path):
            os.remove(temp_batch_path)
    except:
        pass
    
    print_colored("⚠️ Please check if Ollama is installed correctly", Colors.YELLOW)
    print_colored("⚠️ You can download it from https://ollama.ai/download", Colors.YELLOW)
    
    print_colored("\n📋 You can try to start Ollama manually:", Colors.CYAN)
    print_colored("1. Open a new Command Prompt window", Colors.CYAN)
    print_colored("2. Run the following commands:", Colors.CYAN)
    print_colored(f"   cd %USERPROFILE%", Colors.CYAN)
    print_colored(f"   \"{ollama_cmd}\" serve", Colors.CYAN)
    print_colored("3. Once Ollama is running, restart this application", Colors.CYAN)
    
    print_colored("\n⚠️ Continuing without Ollama (some features may not work)", Colors.YELLOW)
    return False

# Function to start the backend API server
def start_backend():
    """Start the Flask API server"""
    api_running, ollama_available = check_api_health()
    
    if api_running:
        print_colored("✅ API server is already running on port 5000", Colors.GREEN)
        if not ollama_available:
            print_colored("⚠️ API server reports Ollama is not available", Colors.YELLOW)
            print_colored("⚠️ Some features may not work properly", Colors.YELLOW)
        return True
    
    print_colored("🚀 Starting API server...", Colors.CYAN)
    
    # Check if backend directory exists
    if not os.path.exists(BACKEND_DIR):
        print_colored(f"❌ Backend directory not found at {BACKEND_DIR}", Colors.RED)
        return False
    
    # Check if api_server.py exists
    if not os.path.exists(BACKEND_SCRIPT):
        print_colored(f"❌ API server script not found at {BACKEND_SCRIPT}", Colors.RED)
        return False
    
    # Check if required dependencies are installed
    print_colored("📋 Checking if required Python packages are installed...", Colors.CYAN)
    try:
        # Check if requirements.txt exists
        requirements_file = os.path.join(BACKEND_DIR, "requirements.txt")
        if os.path.exists(requirements_file):
            # Check if major dependencies are installed
            check_deps_cmd = 'python -c "import flask, flask_cors, pandas, numpy; print(\'OK\')"'
            result = subprocess.run(check_deps_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0 or "OK" not in result.stdout:
                print_colored("⚠️ Some Python dependencies are missing", Colors.YELLOW)
                print_colored("📋 Installing required packages...", Colors.CYAN)
                
                install_cmd = f'powershell -Command "pip install -r {requirements_file}"'
                print_colored(f"📋 Executing: {install_cmd}", Colors.BLUE)
                subprocess.run(install_cmd, shell=True)
            else:
                print_colored("✅ Required Python packages are installed", Colors.GREEN)
    except Exception as e:
        print_colored(f"⚠️ Error checking dependencies: {str(e)}", Colors.YELLOW)
    
    # Check if there's already a process using port 5000
    if is_port_in_use(API_PORT):
        print_colored(f"⚠️ Port {API_PORT} is already in use, but the API is not responding", Colors.YELLOW)
        print_colored("⚠️ Attempting to free the port...", Colors.YELLOW)
        
        # Try to find and kill the process using port 5000
        try:
            kill_cmd = f'powershell -Command "Get-NetTCPConnection -LocalPort {API_PORT} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess | ForEach-Object {{ Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }}"'
            subprocess.run(kill_cmd, shell=True)
            time.sleep(2)  # Wait for the port to be freed
            
            if is_port_in_use(API_PORT):
                print_colored(f"⚠️ Could not free port {API_PORT}. Try restarting your computer.", Colors.YELLOW)
                return False
        except:
            print_colored(f"⚠️ Could not free port {API_PORT}", Colors.YELLOW)
    
    # PowerShell command to start the API server in a new window
    ps_cmd = f'powershell -Command "Start-Process -FilePath \'python\' -ArgumentList \'{BACKEND_SCRIPT}\' -WorkingDirectory \'{BACKEND_DIR}\' -WindowStyle Normal"'
    print_colored(f"📋 Executing: {ps_cmd}", Colors.BLUE)
    subprocess.run(ps_cmd, shell=True)
    
    # Wait for the API server to start
    print_colored("⏳ Waiting for API server to start...", Colors.CYAN)
    for i in range(60):  # Increased timeout to 60 seconds
        api_running, ollama_available = check_api_health()
        if api_running:
            print_colored("✅ API server started successfully on port 5000", Colors.GREEN)
            if not ollama_available:
                print_colored("⚠️ API server reports Ollama is not available", Colors.YELLOW)
                print_colored("⚠️ Some features may not work properly", Colors.YELLOW)
            return True
        
        if i % 5 == 0:  # Show progress indicator every 5 seconds
            print(f"{i}s...", end="", flush=True)
        else:
            print(".", end="", flush=True)
        time.sleep(1)
    
    print()  # New line after dots
    print_colored("❌ Failed to start API server within 60 seconds", Colors.RED)
    
    # Try to diagnose the issue
    print_colored("🔍 Diagnosing API server startup issue...", Colors.CYAN)
    
    # Check if port 5000 is in use
    if is_port_in_use(API_PORT):
        print_colored(f"⚠️ Port {API_PORT} is in use, but the API server is not responding", Colors.YELLOW)
        print_colored("⚠️ Try restarting your computer to free up the port", Colors.YELLOW)
    
    # Check if we can run the API server manually for more error info
    print_colored("📋 Attempting to run API server manually to get error information...", Colors.CYAN)
    try:
        debug_cmd = f'powershell -Command "cd {BACKEND_DIR}; python {BACKEND_SCRIPT} --debug"'
        debug_result = subprocess.run(debug_cmd, shell=True, capture_output=True, text=True)
        
        if debug_result.stderr and len(debug_result.stderr) > 0:
            print_colored("⚠️ API server error output:", Colors.YELLOW)
            print(debug_result.stderr[:500] + "..." if len(debug_result.stderr) > 500 else debug_result.stderr)
    except:
        pass
    
    return False

# Function to start the frontend UI
def start_frontend():
    """Start the React frontend UI"""
    global UI_PORT
    
    if is_port_in_use(UI_PORT) or is_port_in_use(UI_PORT + 1):
        port = UI_PORT if is_port_in_use(UI_PORT) else UI_PORT + 1
        print_colored(f"✅ UI is already running on port {port}", Colors.GREEN)
        UI_PORT = port
        return True
    
    print_colored("🚀 Starting Frontend UI...", Colors.CYAN)
    
    # Check if UI directory exists
    if not os.path.exists(UI_DIR):
        print_colored(f"❌ UI directory not found at {UI_DIR}", Colors.RED)
        return False
    
    # Check for package.json to confirm it's a Node.js project
    package_json = os.path.join(UI_DIR, "package.json")
    if not os.path.exists(package_json):
        print_colored(f"❌ package.json not found in UI directory", Colors.RED)
        print_colored("⚠️ The UI directory does not appear to be a valid React project", Colors.YELLOW)
        return False
    
    # Check if Node.js and npm are installed
    print_colored("📋 Checking if Node.js and npm are installed...", Colors.CYAN)
    try:
        node_cmd = 'powershell -Command "node --version"'
        node_result = subprocess.run(node_cmd, shell=True, capture_output=True, text=True)
        
        npm_cmd = 'powershell -Command "npm --version"'
        npm_result = subprocess.run(npm_cmd, shell=True, capture_output=True, text=True)
        
        if node_result.returncode != 0 or npm_result.returncode != 0:
            print_colored("❌ Node.js or npm is not installed", Colors.RED)
            print_colored("⚠️ Please install Node.js and npm from https://nodejs.org/", Colors.YELLOW)
            return False
        
        node_version = node_result.stdout.strip()
        npm_version = npm_result.stdout.strip()
        print_colored(f"✅ Node.js version: {node_version}", Colors.GREEN)
        print_colored(f"✅ npm version: {npm_version}", Colors.GREEN)
    except:
        print_colored("⚠️ Could not verify Node.js and npm installation", Colors.YELLOW)
    
    # Check if node_modules exists, if not, run npm install
    node_modules = os.path.join(UI_DIR, "node_modules")
    if not os.path.exists(node_modules):
        print_colored("📋 node_modules not found, running npm install...", Colors.CYAN)
        
        install_cmd = f'powershell -Command "cd {UI_DIR}; npm install"'
        print_colored(f"📋 Executing: {install_cmd}", Colors.BLUE)
        
        try:
            install_process = subprocess.Popen(install_cmd, shell=True)
            print_colored("⏳ Installing npm dependencies. This may take a few minutes...", Colors.CYAN)
            
            # Wait for a maximum of 5 minutes for npm install to complete
            for i in range(300):
                if install_process.poll() is not None:
                    if install_process.returncode == 0:
                        print_colored("✅ npm dependencies installed successfully", Colors.GREEN)
                        break
                    else:
                        print_colored("❌ Failed to install npm dependencies", Colors.RED)
                        return False
                
                if i % 10 == 0:  # Show progress message every 10 seconds
                    print(f"{i}s...", end="", flush=True)
                time.sleep(1)
                
            if install_process.poll() is None:
                print_colored("⚠️ npm install is taking too long, continuing anyway...", Colors.YELLOW)
        except Exception as e:
            print_colored(f"❌ Error running npm install: {str(e)}", Colors.RED)
            return False
    
    # Before starting UI, check if ports 3000 and 3001 are in use by other processes
    if is_port_in_use(UI_PORT) and not is_port_in_use(UI_PORT + 1):
        print_colored(f"⚠️ Port {UI_PORT} is already in use, will try to use port {UI_PORT + 1}", Colors.YELLOW)
        UI_PORT = UI_PORT + 1
    elif is_port_in_use(UI_PORT + 1) and not is_port_in_use(UI_PORT):
        print_colored(f"⚠️ Port {UI_PORT + 1} is already in use, will use port {UI_PORT}", Colors.YELLOW)
    elif is_port_in_use(UI_PORT) and is_port_in_use(UI_PORT + 1):
        print_colored(f"⚠️ Both ports {UI_PORT} and {UI_PORT + 1} are in use", Colors.YELLOW)
        print_colored("⚠️ Attempting to free the ports...", Colors.YELLOW)
        
        try:
            for port in [UI_PORT, UI_PORT + 1]:
                kill_cmd = f'powershell -Command "Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess | ForEach-Object {{ Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }}"'
                subprocess.run(kill_cmd, shell=True)
            
            time.sleep(2)  # Wait for the ports to be freed
            
            if is_port_in_use(UI_PORT) and is_port_in_use(UI_PORT + 1):
                print_colored("⚠️ Could not free the ports. Try restarting your computer.", Colors.YELLOW)
                return False
        except:
            print_colored("⚠️ Could not free the ports", Colors.YELLOW)
    
    # PowerShell command to start the UI in a new window
    ps_cmd = f'powershell -Command "Start-Process -FilePath \'cmd\' -ArgumentList \'/c cd {UI_DIR} && npm run dev\' -WindowStyle Normal"'
    print_colored(f"📋 Executing: {ps_cmd}", Colors.BLUE)
    subprocess.run(ps_cmd, shell=True)
    
    # Wait for the UI to start on either port 3000 or 3001
    print_colored("⏳ Waiting for UI to start...", Colors.CYAN)
    for i in range(90):  # Increased timeout to 90 seconds
        if is_port_in_use(UI_PORT):
            print_colored(f"✅ UI started successfully on port {UI_PORT}", Colors.GREEN)
            return True
        elif is_port_in_use(UI_PORT + 1):
            print_colored(f"✅ UI started successfully on port {UI_PORT + 1}", Colors.GREEN)
            UI_PORT = UI_PORT + 1
            return True
        
        if i % 5 == 0:  # Show progress indicator every 5 seconds
            print(f"{i}s...", end="", flush=True)
        else:
            print(".", end="", flush=True)
        time.sleep(1)
    
    print()  # New line after dots
    print_colored("❌ Failed to start UI within 90 seconds", Colors.RED)
    
    # Try to diagnose the issue
    print_colored("🔍 Diagnosing UI startup issue...", Colors.CYAN)
    
    # Check if we can run npm run dev manually for more error info
    print_colored("📋 Attempting to run UI manually to get error information...", Colors.CYAN)
    try:
        debug_cmd = f'powershell -Command "cd {UI_DIR}; npm run dev"'
        debug_result = subprocess.run(debug_cmd, shell=True, capture_output=True, text=True)
        
        if debug_result.stderr and len(debug_result.stderr) > 0:
            print_colored("⚠️ UI startup error output:", Colors.YELLOW)
            print(debug_result.stderr[:500] + "..." if len(debug_result.stderr) > 500 else debug_result.stderr)
    except:
        pass
    
    return False

# Function to run tests
def run_tests():
    """Run the test suite"""
    print_colored("🧪 Running tests...", Colors.CYAN)
    
    # Check if test runner exists
    if not os.path.exists(TEST_RUNNER):
        print_colored(f"❌ Test runner not found at {TEST_RUNNER}", Colors.RED)
        return False
    
    # Run the test runner
    cmd = f"python {TEST_RUNNER}"
    print_colored(f"Executing: {cmd}", Colors.BLUE)
    process = subprocess.Popen(cmd, shell=True, cwd=TESTS_DIR)
    process.wait()
    
    if process.returncode == 0:
        print_colored("✅ Tests completed successfully", Colors.GREEN)
        return True
    else:
        print_colored(f"❌ Tests failed with code {process.returncode}", Colors.RED)
        return False

# Function to open the browser
def open_browser():
    """Open the browser to the UI"""
    print_colored("🌐 Opening browser...", Colors.CYAN)
    try:
        url = f"http://localhost:{UI_PORT}"
        webbrowser.open(url)
        print_colored(f"✅ Browser opened to {url}", Colors.GREEN)
        return True
    except Exception as e:
        print_colored(f"❌ Error opening browser: {str(e)}", Colors.RED)
        return False

# Function to check system compatibility
def check_system_compatibility():
    """Check if the system meets the requirements to run the application"""
    print_colored("🔍 Checking system compatibility...", Colors.CYAN)
    
    # Check Windows version
    try:
        os_check_cmd = 'powershell -Command "Get-WmiObject -Class Win32_OperatingSystem | Select-Object -ExpandProperty Caption"'
        os_result = subprocess.run(os_check_cmd, shell=True, capture_output=True, text=True)
        
        if os_result.returncode == 0 and "Windows" in os_result.stdout:
            windows_version = os_result.stdout.strip()
            print_colored(f"✅ Operating System: {windows_version}", Colors.GREEN)
        else:
            print_colored("⚠️ Could not detect Windows version", Colors.YELLOW)
    except:
        print_colored("⚠️ Could not check operating system version", Colors.YELLOW)
    
    # Check Python version
    try:
        import platform
        python_version = platform.python_version()
        if python_version >= "3.8":
            print_colored(f"✅ Python version: {python_version}", Colors.GREEN)
        else:
            print_colored(f"⚠️ Python version {python_version} is below recommended version 3.8", Colors.YELLOW)
            print_colored("⚠️ Some features may not work properly", Colors.YELLOW)
    except:
        print_colored("⚠️ Could not check Python version", Colors.YELLOW)
    
    # Check firewall status for required ports
    try:
        fw_check_cmd = f'powershell -Command "Get-NetFirewallRule -DisplayName \'*\' | Where-Object {{ $_.Action -eq \'Allow\' -and ($_.LocalPort -eq {OLLAMA_PORT} -or $_.LocalPort -eq {API_PORT} -or $_.LocalPort -eq {UI_PORT} -or $_.LocalPort -eq \'{UI_PORT + 1}\') }} | Measure-Object | Select-Object -ExpandProperty Count"'
        fw_result = subprocess.run(fw_check_cmd, shell=True, capture_output=True, text=True)
        
        if fw_result.returncode == 0:
            fw_count = int(fw_result.stdout.strip() or "0")
            if fw_count >= 3:
                print_colored("✅ Firewall: Required ports appear to be open", Colors.GREEN)
            else:
                print_colored("⚠️ Firewall: Some required ports may be blocked", Colors.YELLOW)
                print_colored(f"⚠️ Please ensure ports {OLLAMA_PORT}, {API_PORT}, {UI_PORT}, and {UI_PORT + 1} are allowed", Colors.YELLOW)
    except:
        print_colored("⚠️ Could not check firewall status", Colors.YELLOW)
    
    print_colored("✅ System compatibility check completed", Colors.GREEN)
    return True

# Main function
def main():
    """Main function to start all components"""
    parser = argparse.ArgumentParser(description="Find My Fund - All-in-One Launcher")
    parser.add_argument("--no-ollama", action="store_true", help="Don't start Ollama")
    parser.add_argument("--no-api", action="store_true", help="Don't start the API server")
    parser.add_argument("--no-ui", action="store_true", help="Don't start the UI")
    parser.add_argument("--no-browser", action="store_true", help="Don't open the browser")
    parser.add_argument("--skip-compatibility", action="store_true", help="Skip system compatibility check")
    parser.add_argument("--tests", action="store_true", help="Run tests after starting components")
    args = parser.parse_args()
    
    print_colored("========================================", Colors.BLUE, bold=True)
    print_colored("  Find My Fund - All-in-One Launcher", Colors.BLUE, bold=True)
    print_colored("========================================", Colors.BLUE, bold=True)
    
    # Check system compatibility
    if not args.skip_compatibility:
        check_system_compatibility()
    
    # Start components
    component_status = {
        "ollama": False,
        "api": False,
        "ui": False
    }
    
    if not args.no_ollama:
        print_colored("\n📌 STEP 1: Starting Ollama", Colors.CYAN, bold=True)
        ollama_success = start_ollama()
        component_status["ollama"] = ollama_success
        if not ollama_success:
            print_colored("⚠️ Continuing without Ollama...", Colors.YELLOW)
            print_colored("⚠️ Some features may not work properly", Colors.YELLOW)
    else:
        print_colored("\n⏭️ Skipping Ollama startup (--no-ollama flag)", Colors.YELLOW)
    
    if not args.no_api:
        print_colored("\n📌 STEP 2: Starting API Server", Colors.CYAN, bold=True)
        api_success = start_backend()
        component_status["api"] = api_success
        if not api_success:
            print_colored("❌ Failed to start API server", Colors.RED)
            print_colored("⚠️ The application may not function properly without the API server", Colors.YELLOW)
            print_colored("⚠️ Do you want to continue anyway? (y/n)", Colors.YELLOW)
            
            try:
                choice = input().lower()
                if choice != 'y' and choice != 'yes':
                    print_colored("❌ Exiting as requested", Colors.RED)
                    return 1
            except:
                print_colored("❌ No input received, exiting", Colors.RED)
                return 1
    else:
        print_colored("\n⏭️ Skipping API server startup (--no-api flag)", Colors.YELLOW)
    
    if not args.no_ui:
        print_colored("\n📌 STEP 3: Starting Frontend UI", Colors.CYAN, bold=True)
        ui_success = start_frontend()
        component_status["ui"] = ui_success
        if not ui_success:
            print_colored("❌ Failed to start UI", Colors.RED)
            print_colored("⚠️ The application may not function properly without the UI", Colors.YELLOW)
            print_colored("⚠️ Do you want to continue anyway? (y/n)", Colors.YELLOW)
            
            try:
                choice = input().lower()
                if choice != 'y' and choice != 'yes':
                    print_colored("❌ Exiting as requested", Colors.RED)
                    return 1
            except:
                print_colored("❌ No input received, exiting", Colors.RED)
                return 1
    else:
        print_colored("\n⏭️ Skipping UI startup (--no-ui flag)", Colors.YELLOW)
    
    # Wait for everything to stabilize
    if any(component_status.values()):
        print_colored("\n⏳ Waiting for all components to stabilize...", Colors.CYAN)
        time.sleep(5)
        print_colored("✅ All systems stabilized", Colors.GREEN)
    
    # Open browser if requested and UI is running
    if not args.no_browser and component_status["ui"]:
        print_colored("\n📌 STEP 4: Opening Browser", Colors.CYAN, bold=True)
        open_browser()
    elif not args.no_browser and not component_status["ui"]:
        print_colored("\n⏭️ Skipping browser launch as UI is not running", Colors.YELLOW)
    else:
        print_colored("\n⏭️ Skipping browser launch (--no-browser flag)", Colors.YELLOW)
    
    # Run tests if requested
    if args.tests:
        print_colored("\n📌 STEP 5: Running Tests", Colors.CYAN, bold=True)
        run_tests()
    
    # Print summary of startup
    print_colored("\n📊 Startup Summary:", Colors.BLUE, bold=True)
    for component, status in component_status.items():
        if status:
            print_colored(f"  ✅ {component.capitalize()}: Running", Colors.GREEN)
        else:
            print_colored(f"  ❌ {component.capitalize()}: Not running", Colors.RED)
    
    if component_status["ollama"] and component_status["api"] and component_status["ui"]:
        print_colored("\n✅ All components started successfully!", Colors.GREEN, bold=True)
    else:
        print_colored("\n⚠️ Some components failed to start", Colors.YELLOW, bold=True)
        print_colored("⚠️ The application may not function properly", Colors.YELLOW)
    
    print_colored("\n📋 Application URLs:", Colors.CYAN, bold=True)
    if component_status["ollama"]:
        print_colored(f"  Ollama API: http://localhost:{OLLAMA_PORT}", Colors.CYAN)
    if component_status["api"]:
        print_colored(f"  Backend API: http://localhost:{API_PORT}", Colors.CYAN)
    if component_status["ui"]:
        print_colored(f"  Frontend UI: http://localhost:{UI_PORT}", Colors.CYAN)
    
    print_colored("\n💻 How to use:", Colors.CYAN, bold=True)
    print_colored("  1. Wait for all components to fully load", Colors.CYAN)
    if not args.no_browser and component_status["ui"]:
        print_colored("  2. The browser should open automatically to the UI", Colors.CYAN)
    else:
        print_colored(f"  2. Open a browser to http://localhost:{UI_PORT}", Colors.CYAN)
    print_colored("  3. Search for mutual funds using natural language", Colors.CYAN)
    print_colored("  4. Click on funds to view detailed analysis", Colors.CYAN)
    
    print_colored("\n🔄 Process status:", Colors.YELLOW, bold=True)
    if component_status["ollama"]:
        print_colored("  • Ollama is running in the background", Colors.YELLOW)
    if component_status["api"]:
        print_colored("  • API server is running in its own window", Colors.YELLOW)
    if component_status["ui"]:
        print_colored("  • UI server is running in its own window", Colors.YELLOW)
    
    print_colored("\n🛑 To stop the application:", Colors.YELLOW, bold=True)
    print_colored("  • Close each component window", Colors.YELLOW)
    print_colored("  • Or press Ctrl+C here to exit (components will continue running)", Colors.YELLOW)
    
    try:
        # Keep the script running so user can see the output
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print_colored("\n👋 Exiting launcher. Services will continue running.", Colors.YELLOW)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 