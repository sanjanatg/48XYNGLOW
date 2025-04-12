#!/usr/bin/env python
"""
Find My Fund - All-in-One Launcher Script (Optimized Version)
This script launches all components of the Find My Fund application:
1. Ollama with Mistral
2. Flask Backend API
3. React Frontend UI
"""

import os
import sys
import time
import subprocess
import webbrowser
import argparse
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
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_colored(message, color=Colors.RESET, bold=False):
    """Print colored message to console"""
    if bold:
        print(f"{Colors.BOLD}{color}{message}{Colors.RESET}")
    else:
        print(f"{color}{message}{Colors.RESET}")

def is_process_running(name):
    """Check if a process with the given name is running"""
    try:
        cmd = f'powershell -Command "Get-Process -Name {name} -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return int(result.stdout.strip()) > 0
    except:
        return False

def is_port_in_use(port):
    """Check if a port is in use"""
    try:
        cmd = f'powershell -Command "Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return int(result.stdout.strip()) > 0
    except:
        return False

def check_api_health():
    """Check if the API server is running and healthy"""
    try:
        cmd = f'powershell -Command "try {{ $result = Invoke-RestMethod -Uri \'http://localhost:{API_PORT}/api/health\' -Method GET -TimeoutSec 2 -ErrorAction Stop; $result | ConvertTo-Json }} catch {{ Write-Output \'\' }}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
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

def start_ollama():
    """Start Ollama server (without checking if it's running)"""
    print_colored("🚀 Starting Ollama...", Colors.CYAN)
    
    # Check Ollama process first
    if is_process_running("ollama"):
        print_colored("✅ Ollama process is already running", Colors.GREEN)
        return True
    
    # Check if Ollama exists at the default path
    if not os.path.exists(OLLAMA_PATH):
        print_colored(f"⚠️ Ollama not found at {OLLAMA_PATH}", Colors.YELLOW)
        print_colored("⚠️ Trying 'ollama' from PATH", Colors.YELLOW)
        ollama_cmd = "ollama"
    else:
        ollama_cmd = OLLAMA_PATH
    
    # Start Ollama directly (not in a new window to avoid issues)
    try:
        subprocess.Popen([ollama_cmd, "serve"], 
                        creationflags=subprocess.CREATE_NEW_CONSOLE, 
                        close_fds=True)
        
        print_colored("✅ Ollama started", Colors.GREEN)
        print_colored("⚠️ It may take a moment to initialize...", Colors.YELLOW)
        
        # Wait a bit for Ollama to start
        time.sleep(5)
        return True
    except Exception as e:
        print_colored(f"❌ Error starting Ollama: {str(e)}", Colors.RED)
        return False

def start_backend():
    """Start the Flask API server"""
    api_running, _ = check_api_health()
    
    if api_running:
        print_colored(f"✅ API server is already running on port {API_PORT}", Colors.GREEN)
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
    
    # Start the API server
    try:
        api_process = subprocess.Popen(
            ["python", BACKEND_SCRIPT],
            cwd=BACKEND_DIR,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            close_fds=True
        )
        
        # Wait for the API server to start
        print_colored("⏳ Waiting for API server to start...", Colors.CYAN)
        for i in range(30):
            api_running, _ = check_api_health()
            if api_running:
                print_colored(f"✅ API server started successfully on port {API_PORT}", Colors.GREEN)
                return True
            
            print(".", end="", flush=True)
            time.sleep(1)
        
        print()  # New line after dots
        print_colored(f"❌ API server did not respond within 30 seconds", Colors.RED)
        print_colored(f"⚠️ Check the API server window for errors", Colors.YELLOW)
        
        # Continue anyway
        return True
    except Exception as e:
        print_colored(f"❌ Error starting API server: {str(e)}", Colors.RED)
        return False

def start_frontend():
    """Start the React frontend UI"""
    global UI_PORT
    
    if is_port_in_use(UI_PORT):
        print_colored(f"✅ UI is already running on port {UI_PORT}", Colors.GREEN)
        return True
    elif is_port_in_use(UI_PORT + 1):
        UI_PORT = UI_PORT + 1
        print_colored(f"✅ UI is already running on port {UI_PORT}", Colors.GREEN)
        return True
    
    print_colored("🚀 Starting Frontend UI...", Colors.CYAN)
    
    # Check if UI directory exists
    if not os.path.exists(UI_DIR):
        print_colored(f"❌ UI directory not found at {UI_DIR}", Colors.RED)
        return False
    
    # Start the UI
    try:
        cmd = f"cd {UI_DIR} && npm run dev"
        ui_process = subprocess.Popen(
            cmd,
            shell=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            close_fds=True
        )
        
        print_colored("✅ UI startup process initiated", Colors.GREEN)
        print_colored("⚠️ The UI may take a moment to initialize...", Colors.YELLOW)
        
        # Wait a bit before continuing
        time.sleep(5)
        return True
    except Exception as e:
        print_colored(f"❌ Error starting UI: {str(e)}", Colors.RED)
        return False

def run_tests():
    """Run the test suite"""
    print_colored("🧪 Running tests...", Colors.CYAN)
    
    # Check if test runner exists
    if not os.path.exists(TEST_RUNNER):
        print_colored(f"❌ Test runner not found at {TEST_RUNNER}", Colors.RED)
        return False
    
    # Run the test runner
    try:
        cmd = ["python", TEST_RUNNER]
        print_colored(f"Executing: {' '.join(cmd)}", Colors.BLUE)
        process = subprocess.Popen(
            cmd, 
            cwd=TESTS_DIR,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            close_fds=True
        )
        
        print_colored("✅ Test runner started", Colors.GREEN)
        return True
    except Exception as e:
        print_colored(f"❌ Error running tests: {str(e)}", Colors.RED)
        return False

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

def main():
    """Main function to start all components"""
    parser = argparse.ArgumentParser(description="Find My Fund - All-in-One Launcher")
    parser.add_argument("--no-ollama", action="store_true", help="Don't start Ollama")
    parser.add_argument("--no-api", action="store_true", help="Don't start the API server")
    parser.add_argument("--no-ui", action="store_true", help="Don't start the UI")
    parser.add_argument("--no-browser", action="store_true", help="Don't open the browser")
    parser.add_argument("--tests", action="store_true", help="Run tests after starting components")
    args = parser.parse_args()
    
    print_colored("========================================", Colors.BLUE, bold=True)
    print_colored("  Find My Fund - All-in-One Launcher", Colors.BLUE, bold=True)
    print_colored("========================================", Colors.BLUE, bold=True)
    
    # Start components
    if not args.no_ollama:
        start_ollama()
    
    if not args.no_api:
        start_backend()
    
    if not args.no_ui:
        start_frontend()
    
    # Wait for everything to stabilize
    time.sleep(2)
    
    # Open browser if requested
    if not args.no_browser and not args.no_ui:
        open_browser()
    
    # Run tests if requested
    if args.tests:
        run_tests()
    
    print_colored("\n✅ All components started!", Colors.GREEN, bold=True)
    print_colored("\n📋 Component Information:", Colors.CYAN, bold=True)
    print_colored(f"  Ollama: http://localhost:{OLLAMA_PORT}", Colors.CYAN)
    print_colored(f"  API: http://localhost:{API_PORT}", Colors.CYAN)
    print_colored(f"  UI: http://localhost:{UI_PORT}", Colors.CYAN)
    
    print_colored("\n🔷 What's Next?", Colors.BLUE, bold=True)
    print_colored("  1. Check each component window for progress or errors", Colors.BLUE)
    print_colored("  2. Use the browser to interact with the application", Colors.BLUE)
    print_colored("  3. The application should be available once all components load", Colors.BLUE)
    
    print_colored("\n👋 Script execution complete - each component will continue running in its own window", Colors.GREEN)
    return 0

if __name__ == "__main__":
    sys.exit(main()) 