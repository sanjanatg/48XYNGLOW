#!/usr/bin/env python
"""
Start Script for LLM, Find My Fund
==================================

This script starts both the FastAPI backend server and the Next.js frontend simultaneously.
"""

import os
import sys
import subprocess
import threading
from pathlib import Path
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def start_fastapi_server():
    """Start the FastAPI server."""
    print("Starting FastAPI Fund Search server...")
    
    # Add current directory to sys.path to fix imports
    current_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(current_dir, "venv", "Scripts")
    
    api_process = subprocess.Popen(
        [sys.executable, "main.py", "--api"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1,
        env={**os.environ, "PYTHONPATH": current_dir}
    )
    
    # Monitor the output
    for line in api_process.stdout:
        print(f"[API] {line.strip()}")
    
    api_process.wait()
    print("API server stopped.")

def start_nextjs_server():
    """Start the Next.js chatbot server."""
    print("Starting Next.js Chatbot server...")
    
    # Change to the chatbot directory
    os.chdir(Path(__file__).parent / "chatbot")
    
    # Check if npm is available and install packages if needed
    try:
        subprocess.run(["npm", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Install dependencies if not already installed
        if not os.path.exists("node_modules"):
            print("[CHAT] Installing Node.js dependencies...")
            subprocess.run(["npm", "install"], check=True)
        
        # Start Next.js
        chat_process = subprocess.Popen(
            ["npm", "run", "dev"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Monitor the output
        for line in chat_process.stdout:
            print(f"[CHAT] {line.strip()}")
        
        chat_process.wait()
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[CHAT] Error: npm not found. Please install Node.js and npm.")
    
    print("Chatbot server stopped.")

def main():
    """Main entry point that starts both servers."""
    print("Starting LLM, Find My Fund components...")
    
    # Start the API server in a separate thread
    api_thread = threading.Thread(target=start_fastapi_server)
    api_thread.daemon = True
    api_thread.start()
    
    # Wait a bit for the API to start
    time.sleep(2)
    
    # Start the Next.js server in the main thread
    start_nextjs_server()
    
    # When Next.js exits, wait for the API thread to finish
    api_thread.join(timeout=5)
    
    print("All servers stopped.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nShutting down all services...")
        sys.exit(0) 