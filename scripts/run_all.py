#!/usr/bin/env python
import os
import sys
import time
import argparse
import subprocess
import psutil
import webbrowser
from colorama import init, Fore, Style

# Initialize colorama for colored terminal output
init()

def is_process_running(process_name):
    """Check if a process with the given name is running"""
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == process_name:
            return True
    return False

def is_port_in_use(port):
    """Check if a port is in use"""
    for conn in psutil.net_connections():
        if conn.laddr.port == port:
            return True
    return False

def start_ollama():
    """Start Ollama if not already running"""
    if is_process_running("ollama.exe"):
        print(f"{Fore.GREEN}✓ Ollama is already running{Style.RESET_ALL}")
        return True
    
    print(f"{Fore.CYAN}Starting Ollama...{Style.RESET_ALL}")
    try:
        # Try to find Ollama in the default installation path
        ollama_path = os.path.expanduser("~\\AppData\\Local\\Programs\\Ollama\\ollama.exe")
        
        if not os.path.exists(ollama_path):
            print(f"{Fore.YELLOW}Warning: Ollama not found at {ollama_path}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Trying to run 'ollama' from PATH{Style.RESET_ALL}")
            ollama_path = "ollama"
        
        # Start Ollama in a new PowerShell window
        powershell_cmd = [
            "powershell", 
            "-Command", 
            f"Start-Process -FilePath '{ollama_path}' -ArgumentList 'serve' -WindowStyle Minimized"
        ]
        subprocess.Popen(powershell_cmd, shell=True)
        
        # Wait for Ollama to start (up to 30 seconds)
        for i in range(30):
            if is_port_in_use(11434):
                print(f"{Fore.GREEN}✓ Ollama started successfully{Style.RESET_ALL}")
                return True
            time.sleep(1)
            print(".", end="", flush=True)
        
        print(f"\n{Fore.RED}✗ Failed to start Ollama within 30 seconds{Style.RESET_ALL}")
        return False
    except Exception as e:
        print(f"{Fore.RED}✗ Error starting Ollama: {str(e)}{Style.RESET_ALL}")
        return False

def start_api_server():
    """Start the Flask API server"""
    if is_port_in_use(5000):
        print(f"{Fore.GREEN}✓ API server is already running on port 5000{Style.RESET_ALL}")
        return True
    
    print(f"{Fore.CYAN}Starting API server...{Style.RESET_ALL}")
    try:
        # Get the absolute path to the API server script
        api_server_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "FINAL", "api_server.py"))
        
        # Start the API server in a new PowerShell window
        powershell_cmd = [
            "powershell", 
            "-Command", 
            f"Start-Process -FilePath 'python' -ArgumentList '{api_server_path}' -WorkingDirectory '{os.path.dirname(api_server_path)}' -WindowStyle Normal"
        ]
        subprocess.Popen(powershell_cmd, shell=True)
        
        # Wait for the API server to start (up to 30 seconds)
        for i in range(30):
            if is_port_in_use(5000):
                print(f"{Fore.GREEN}✓ API server started successfully{Style.RESET_ALL}")
                return True
            time.sleep(1)
            print(".", end="", flush=True)
        
        print(f"\n{Fore.RED}✗ Failed to start API server within 30 seconds{Style.RESET_ALL}")
        return False
    except Exception as e:
        print(f"{Fore.RED}✗ Error starting API server: {str(e)}{Style.RESET_ALL}")
        return False

def start_ui():
    """Start the React UI"""
    if is_port_in_use(3001):
        print(f"{Fore.GREEN}✓ UI is already running on port 3001{Style.RESET_ALL}")
        return True
    
    print(f"{Fore.CYAN}Starting UI...{Style.RESET_ALL}")
    try:
        # Get the absolute path to the UI directory
        ui_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ui"))
        
        # Start the UI in a new PowerShell window
        powershell_cmd = [
            "powershell", 
            "-Command", 
            f"Start-Process -FilePath 'cmd' -ArgumentList '/c cd {ui_dir} && npm run dev' -WindowStyle Normal"
        ]
        subprocess.Popen(powershell_cmd, shell=True)
        
        # Wait for the UI to start (up to 60 seconds)
        for i in range(60):
            if is_port_in_use(3001):
                print(f"{Fore.GREEN}✓ UI started successfully{Style.RESET_ALL}")
                return True
            time.sleep(1)
            print(".", end="", flush=True)
        
        print(f"\n{Fore.RED}✗ Failed to start UI within 60 seconds{Style.RESET_ALL}")
        return False
    except Exception as e:
        print(f"{Fore.RED}✗ Error starting UI: {str(e)}{Style.RESET_ALL}")
        return False

def run_tests():
    """Run the test_runner.py script"""
    print(f"{Fore.CYAN}Running tests...{Style.RESET_ALL}")
    try:
        # Get the absolute path to the test_runner.py script
        test_runner_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tests", "test_runner.py"))
        
        # Check if the test_runner.py file exists
        if not os.path.exists(test_runner_path):
            print(f"{Fore.RED}✗ Test runner not found at {test_runner_path}{Style.RESET_ALL}")
            return False
        
        # Run the test_runner.py script
        process = subprocess.Popen(
            f"python {test_runner_path}", 
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Print the output of the test_runner.py script
        for line in process.stdout:
            print(line, end="")
        
        # Wait for the process to complete
        process.wait()
        
        if process.returncode == 0:
            print(f"{Fore.GREEN}✓ Tests completed successfully{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}✗ Tests failed with return code {process.returncode}{Style.RESET_ALL}")
            return False
    except Exception as e:
        print(f"{Fore.RED}✗ Error running tests: {str(e)}{Style.RESET_ALL}")
        return False

def open_browser():
    """Open the browser to the UI"""
    print(f"{Fore.CYAN}Opening browser...{Style.RESET_ALL}")
    try:
        webbrowser.open("http://localhost:3001")
        print(f"{Fore.GREEN}✓ Browser opened successfully{Style.RESET_ALL}")
        return True
    except Exception as e:
        print(f"{Fore.RED}✗ Error opening browser: {str(e)}{Style.RESET_ALL}")
        return False

def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description="Start the Find My Fund application")
    parser.add_argument("--no-ollama", action="store_true", help="Don't start Ollama")
    parser.add_argument("--no-api", action="store_true", help="Don't start the API server")
    parser.add_argument("--no-ui", action="store_true", help="Don't start the UI")
    parser.add_argument("--no-browser", action="store_true", help="Don't open the browser")
    parser.add_argument("--run-tests", action="store_true", help="Run tests after starting the services")
    return parser.parse_args()

def main():
    """Main function to start all components"""
    print(f"{Fore.CYAN}==============================================={Style.RESET_ALL}")
    print(f"{Fore.CYAN}Find My Fund - Application Launcher{Style.RESET_ALL}")
    print(f"{Fore.CYAN}==============================================={Style.RESET_ALL}")
    
    # Check if required dependencies are installed
    missing_deps = []
    try:
        import psutil
    except ImportError:
        missing_deps.append("psutil")
    
    try:
        import colorama
    except ImportError:
        missing_deps.append("colorama")
    
    if missing_deps:
        print(f"{Fore.RED}Missing dependencies: {', '.join(missing_deps)}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Please install them with: pip install {' '.join(missing_deps)}{Style.RESET_ALL}")
        return
    
    # Parse command-line arguments
    args = parse_arguments()
    
    # Start Ollama
    if not args.no_ollama:
        ollama_success = start_ollama()
        if not ollama_success:
            print(f"{Fore.YELLOW}Continuing without Ollama...{Style.RESET_ALL}")
    
    # Start API server
    if not args.no_api:
        api_success = start_api_server()
        if not api_success:
            print(f"{Fore.RED}Failed to start API server. Exiting.{Style.RESET_ALL}")
            return
    
    # Start UI
    if not args.no_ui:
        ui_success = start_ui()
        if not ui_success:
            print(f"{Fore.RED}Failed to start UI. Exiting.{Style.RESET_ALL}")
            return
    
    # Open browser
    if not args.no_browser and not args.no_ui:
        # Wait a bit for the UI to fully initialize
        time.sleep(5)
        open_browser()
    
    # Run tests if requested
    if args.run_tests:
        # Make sure API server is running before running tests
        if args.no_api:
            print(f"{Fore.YELLOW}Warning: Cannot run tests without API server{Style.RESET_ALL}")
        else:
            run_tests()
    
    print(f"{Fore.GREEN}All components started successfully!{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Services:{Style.RESET_ALL}")
    print(f"  - Ollama: http://localhost:11434")
    print(f"  - API: http://localhost:5000")
    print(f"  - UI: http://localhost:3001")
    print(f"{Fore.CYAN}Press Ctrl+C to exit (services will continue running in their windows){Style.RESET_ALL}")
    
    # Keep the script running until interrupted
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"{Fore.CYAN}Script interrupted. Services will continue running.{Style.RESET_ALL}")

if __name__ == "__main__":
    main() 