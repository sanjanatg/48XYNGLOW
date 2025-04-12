#!/usr/bin/env python3
"""
FundAI Runner Script

This script makes it easier to run both the backend API and frontend UI.
"""

import os
import sys
import subprocess
import argparse
import time
import webbrowser
from threading import Thread

def run_backend(port):
    """Run the backend Flask API"""
    print(f"[*] Starting backend on port {port}...")
    backend_cmd = [sys.executable, "FINAL/rag_ui_bridge.py", "--port", str(port), "--debug"]
    
    try:
        subprocess.run(backend_cmd, check=True)
    except KeyboardInterrupt:
        print("[*] Backend stopped")
    except Exception as e:
        print(f"[!] Error running backend: {str(e)}")
        return False
    
    return True

def run_frontend(port):
    """Run the frontend React app"""
    print(f"[*] Starting frontend on port {port}...")
    
    if not os.path.exists("ui/node_modules"):
        print("[*] Installing frontend dependencies (this may take a while)...")
        subprocess.run(["npm", "install"], cwd="ui", check=True)
    
    # Set environment variables for the frontend
    env = os.environ.copy()
    env["VITE_API_URL"] = f"http://localhost:5000/api"  # Backend API URL
    env["PORT"] = str(port)
    
    frontend_cmd = ["npm", "run", "dev", "--", "--port", str(port)]
    
    try:
        subprocess.run(frontend_cmd, cwd="ui", env=env, check=True)
    except KeyboardInterrupt:
        print("[*] Frontend stopped")
    except Exception as e:
        print(f"[!] Error running frontend: {str(e)}")
        return False
    
    return True

def open_browser(url, delay=2):
    """Open the browser after a delay"""
    time.sleep(delay)
    print(f"[*] Opening browser at {url}")
    webbrowser.open(url)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="FundAI Runner")
    parser.add_argument("--backend-only", action="store_true", help="Run only the backend API")
    parser.add_argument("--frontend-only", action="store_true", help="Run only the frontend UI")
    parser.add_argument("--backend-port", type=int, default=5000, help="Backend port (default: 5000)")
    parser.add_argument("--frontend-port", type=int, default=3000, help="Frontend port (default: 3000)")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    args = parser.parse_args()
    
    # Validate arguments
    if args.backend_only and args.frontend_only:
        print("[!] Error: Cannot use both --backend-only and --frontend-only")
        return 1
    
    try:
        if args.backend_only:
            # Run only the backend
            run_backend(args.backend_port)
        elif args.frontend_only:
            # Run only the frontend
            run_frontend(args.frontend_port)
        else:
            # Run both backend and frontend in separate threads
            backend_thread = Thread(target=run_backend, args=(args.backend_port,))
            backend_thread.daemon = True
            backend_thread.start()
            
            # Wait for backend to start
            time.sleep(2)
            
            # Open browser after a delay
            if not args.no_browser:
                browser_thread = Thread(target=open_browser, args=(f"http://localhost:{args.frontend_port}",))
                browser_thread.daemon = True
                browser_thread.start()
            
            # Run frontend in the main thread
            run_frontend(args.frontend_port)
    except KeyboardInterrupt:
        print("[*] Shutting down FundAI...")
    except Exception as e:
        print(f"[!] Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 