"""
Fix for Python import path issues
Import this at the top of any script that has import problems to ensure modules can be found
"""
import os
import sys

def add_project_root_to_path():
    """
    Add the project root directory to Python's sys.path to make all modules accessible
    regardless of which directory the script is run from
    """
    # Get the directory containing the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add the current directory to the Python path if not already there
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
        print(f"Added {current_dir} to Python path")
    
    # Also add the parent directory (project root) if needed
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
        print(f"Added {parent_dir} to Python path")

# Run when this module is imported
add_project_root_to_path() 