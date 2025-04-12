#!/usr/bin/env python
"""
Find My Fund - Simple Diagnostic Launcher
This script launches all components with detailed error reporting
"""

import os
import sys
import time
import subprocess
import webbrowser
import platform
import shutil

# Get the base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FINAL_DIR = os.path.join(BASE_DIR, "FINAL")
UI_DIR = os.path.join(BASE_DIR, "ui")

# Port configuration
OLLAMA_PORT = 11434
API_PORT = 5000
UI_PORT = 3000

# Styling for console output
class Style:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"{Style.BLUE}{Style.BOLD}{'='*50}{Style.RESET}")
    print(f"{Style.BLUE}{Style.BOLD}{text.center(50)}{Style.RESET}")
    print(f"{Style.BLUE}{Style.BOLD}{'='*50}{Style.RESET}")

def print_step(step, status="", color=Style.BLUE):
    if status:
        print(f"{color}[{step}]{Style.RESET} {status}")
    else:
        print(f"{color}[{step}]{Style.RESET}")

def print_success(message):
    print(f"{Style.GREEN}✓ {message}{Style.RESET}")

def print_error(message):
    print(f"{Style.RED}✗ {message}{Style.RESET}")

def print_warning(message):
    print(f"{Style.YELLOW}! {message}{Style.RESET}")

def check_port(port):
    """Check if a port is in use"""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(("localhost", port))
        s.shutdown(socket.SHUT_RDWR)
        return True
    except:
        return False
    finally:
        s.close()

def wait_for_port(port, timeout=30, step_name="Service"):
    """Wait for a port to become available"""
    print_step(step_name, f"Waiting for port {port} to be ready...")
    
    for i in range(timeout):
        if check_port(port):
            print_success(f"{step_name} is ready on port {port}")
            return True
        print(".", end="", flush=True)
        time.sleep(1)
    
    print()
    print_error(f"{step_name} did not respond on port {port} within {timeout} seconds")
    return False

def check_ollama():
    """Check if Ollama is installed and running"""
    print_header("CHECKING OLLAMA")
    
    # Find Ollama executable
    ollama_path = None
    
    # Windows default path
    windows_path = os.path.expanduser("~\\AppData\\Local\\Programs\\Ollama\\ollama.exe")
    if os.path.exists(windows_path):
        ollama_path = windows_path
        print_success(f"Found Ollama at: {ollama_path}")
    else:
        # Try to find in PATH
        ollama_cmd = "ollama.exe" if platform.system() == "Windows" else "ollama"
        ollama_in_path = shutil.which(ollama_cmd)
        
        if ollama_in_path:
            ollama_path = ollama_in_path
            print_success(f"Found Ollama in PATH: {ollama_path}")
        else:
            print_error("Ollama not found. Please install Ollama from https://ollama.ai")
            return False
    
    # Check if Ollama is running
    print_step("Ollama", "Checking if running...")
    
    if check_port(OLLAMA_PORT):
        print_success("Ollama is already running")
    else:
        print_warning("Ollama is not running. Starting Ollama...")
        
        # Start Ollama
        try:
            if platform.system() == "Windows":
                # Start Ollama in a new window
                subprocess.Popen(
                    [ollama_path, "serve"],
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                    close_fds=True
                )
            else:
                # For non-Windows platforms
                subprocess.Popen(
                    [ollama_path, "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
            
            # Wait for Ollama to start
            if not wait_for_port(OLLAMA_PORT, timeout=30, step_name="Ollama"):
                print_error("Failed to start Ollama. Please start it manually and try again.")
                return False
        except Exception as e:
            print_error(f"Error starting Ollama: {str(e)}")
            return False
    
    return True

def check_dependencies():
    """Check Python dependencies"""
    print_header("CHECKING DEPENDENCIES")
    
    # Required packages
    required_packages = ["flask", "flask_cors", "pandas", "numpy", "sentence_transformers"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print_success(f"Found package: {package}")
        except ImportError:
            missing_packages.append(package)
            print_error(f"Missing package: {package}")
    
    if missing_packages:
        print_warning("Installing missing packages...")
        for package in missing_packages:
            print_step("pip", f"Installing {package}")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print_success(f"Installed {package}")
            except subprocess.CalledProcessError as e:
                print_error(f"Failed to install {package}: {str(e)}")
                return False
    
    return True

def start_api_server():
    """Start the API server"""
    print_header("STARTING API SERVER")
    
    api_server_path = os.path.join(FINAL_DIR, "api_server.py")
    
    # Check if API server file exists
    if not os.path.exists(api_server_path):
        print_error(f"API server script not found at {api_server_path}")
        return False
    
    # Check if API server is already running
    if check_port(API_PORT):
        print_success(f"API server is already running on port {API_PORT}")
        return True
    
    # Start API server
    print_step("API", "Starting server...")
    
    try:
        if platform.system() == "Windows":
            api_process = subprocess.Popen(
                [sys.executable, api_server_path],
                cwd=FINAL_DIR,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                close_fds=True
            )
        else:
            # For non-Windows platforms
            api_process = subprocess.Popen(
                [sys.executable, api_server_path],
                cwd=FINAL_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
        
        # Wait for API server to start
        if not wait_for_port(API_PORT, timeout=30, step_name="API Server"):
            print_error("API server failed to start. Check the API window for errors.")
            return False
        
        return True
    except Exception as e:
        print_error(f"Error starting API server: {str(e)}")
        return False

def start_ui():
    """Start the React UI"""
    print_header("STARTING UI")
    
    # Check if UI directory exists
    if not os.path.exists(UI_DIR):
        print_error(f"UI directory not found at {UI_DIR}")
        return False
    
    # Check if UI is already running
    if check_port(UI_PORT) or check_port(UI_PORT + 1):
        ui_port = UI_PORT if check_port(UI_PORT) else UI_PORT + 1
        print_success(f"UI is already running on port {ui_port}")
        return True
    
    # Check if npm is installed
    if shutil.which("npm") is None:
        print_error("npm not found. Please install Node.js and npm.")
        return False
    
    # Start UI
    print_step("UI", "Starting React frontend...")
    
    try:
        ui_cmd = "npm run dev"
        
        if platform.system() == "Windows":
            # Start in a new window
            subprocess.Popen(
                f"cmd /c {ui_cmd}",
                cwd=UI_DIR,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                close_fds=True,
                shell=True
            )
        else:
            # For non-Windows platforms
            subprocess.Popen(
                ui_cmd,
                cwd=UI_DIR,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=True,
                start_new_session=True
            )
        
        # Wait for UI to start
        for port in [UI_PORT, UI_PORT + 1]:
            if wait_for_port(port, timeout=60, step_name=f"UI (port {port})"):
                return True
        
        print_error("UI failed to start. Check the UI window for errors.")
        return False
    except Exception as e:
        print_error(f"Error starting UI: {str(e)}")
        return False

def open_browser_to_ui():
    """Open browser to UI"""
    print_header("OPENING BROWSER")
    
    # Determine which port the UI is running on
    ui_port = UI_PORT if check_port(UI_PORT) else UI_PORT + 1
    
    if not check_port(ui_port):
        print_error("UI is not running. Cannot open browser.")
        return False
    
    url = f"http://localhost:{ui_port}"
    print_step("Browser", f"Opening {url}")
    
    try:
        webbrowser.open(url)
        print_success(f"Browser opened to {url}")
        return True
    except Exception as e:
        print_error(f"Error opening browser: {str(e)}")
        return False

def main():
    """Main function"""
    print_header("FIND MY FUND - DIAGNOSTIC LAUNCHER")
    
    # Check if Ollama is available
    ollama_available = check_ollama()
    if not ollama_available:
        print_warning("Continuing without Ollama...")
    
    # Check dependencies
    dependencies_ok = check_dependencies()
    if not dependencies_ok:
        print_error("Missing dependencies. Please install them and try again.")
        return 1
    
    # Start API server
    api_ok = start_api_server()
    if not api_ok:
        print_error("Failed to start API server. Exiting.")
        return 1
    
    # Start UI
    ui_ok = start_ui()
    if not ui_ok:
        print_warning("Failed to start UI. The API server is still running.")
        return 1
    
    # Open browser
    open_browser_to_ui()
    
    print_header("ALL COMPONENTS STARTED")
    print("\nPress Ctrl+C to exit this launcher. Components will continue running.")
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting launcher. Components will continue running.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 