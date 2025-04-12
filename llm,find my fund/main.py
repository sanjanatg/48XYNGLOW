#!/usr/bin/env python
"""
LLM, Find My Fund - Main entry point
====================================

This is the main entry point for the application. It allows launching any of the interfaces:
- CLI using Typer
- Web interface using Streamlit
- API server using FastAPI

"""

import os
import sys
import argparse
from pathlib import Path

# Add the project root to sys.path
sys.path.append(str(Path(__file__).parent))

def launch_cli():
    """Launch the CLI interface using Typer."""
    from src.cli.cli_app import app
    app()

def launch_web():
    """Launch the web interface using Streamlit."""
    import streamlit.web.bootstrap
    streamlit.web.bootstrap.run("src/web/streamlit_app.py", "", [], [])

def launch_api():
    """Launch the API server using FastAPI and Uvicorn."""
    from src.api.api_server import start_server
    start_server()

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="LLM, Find My Fund - Financial fund search engine"
    )
    
    # Define interface options
    interface_group = parser.add_mutually_exclusive_group(required=True)
    interface_group.add_argument(
        "--cli", action="store_true", help="Launch the CLI interface"
    )
    interface_group.add_argument(
        "--web", action="store_true", help="Launch the web interface (Streamlit)"
    )
    interface_group.add_argument(
        "--api", action="store_true", help="Launch the API server (FastAPI)"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Launch the chosen interface
    try:
        if args.cli:
            print("Launching CLI interface...")
            launch_cli()
        elif args.web:
            print("Launching web interface (Streamlit)...")
            launch_web()
        elif args.api:
            print("Launching API server (FastAPI)...")
            launch_api()
    except KeyboardInterrupt:
        print("\nApplication terminated by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Error launching application: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 