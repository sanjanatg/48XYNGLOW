import os
import importlib.util
import sys
import requests

def check_package(package_name):
    """Check if a Python package is installed"""
    spec = importlib.util.find_spec(package_name)
    if spec is None:
        print(f"❌ {package_name} is NOT installed")
        return False
    else:
        print(f"✓ {package_name} is installed")
        return True

def check_ollama():
    """Check if Ollama is running and accessible"""
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            print("✓ Ollama is running")
            
            # Check if mistral model is available
            models = response.json().get("models", [])
            if any(model.get("name") == "mistral" for model in models):
                print("✓ Mistral model is available")
                return True
            else:
                print("❌ Mistral model is NOT available. Please run 'ollama pull mistral'")
                return False
        else:
            print(f"❌ Ollama returned status code {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Ollama is NOT running. Please start Ollama service")
        return False
    except Exception as e:
        print(f"❌ Error checking Ollama: {e}")
        return False

def check_files():
    """Check if all required files are present"""
    required_files = [
        "query_parser.py",
        "lexical_search.py",
        "semantic_search.py",
        "metadata_filter.py",
        "score_fusion.py",
        "rag_prompt.py",
        "ollama_client.py",
        "rag_ui_bridge.py",
        "simple_test.py",
        "requirements.txt",
        "README.md"
    ]
    
    all_present = True
    for file in required_files:
        if os.path.isfile(file):
            print(f"✓ {file} is present")
        else:
            print(f"❌ {file} is missing")
            all_present = False
    
    return all_present

def main():
    """Main function to check installation"""
    print("=========================================")
    print("Checking RAG Fund Search System Installation")
    print("=========================================")
    
    # Check Python version
    python_version = sys.version.split()[0]
    print(f"Python version: {python_version}")
    if int(python_version.split('.')[0]) < 3 or (int(python_version.split('.')[0]) == 3 and int(python_version.split('.')[1]) < 8):
        print("❌ Python 3.8+ is required")
    else:
        print("✓ Python version is sufficient")
    
    print("\nChecking required files:")
    files_ok = check_files()
    
    print("\nChecking required packages:")
    packages_ok = True
    for package in ["numpy", "pandas", "nltk", "requests", "faiss", "sentence_transformers", "rank_bm25"]:
        if not check_package(package):
            packages_ok = False
    
    print("\nChecking Ollama:")
    ollama_ok = check_ollama()
    
    print("\n=========================================")
    print("Installation Check Summary")
    print("=========================================")
    
    if files_ok and packages_ok and ollama_ok:
        print("✅ All checks passed! The system is ready to use.")
        print("\nYou can now run 'python simple_test.py' to test the system.")
    else:
        print("❌ Some checks failed. Please fix the issues above before using the system.")
        
        if not files_ok:
            print("- Make sure all required files are in the current directory")
        
        if not packages_ok:
            print("- Install missing packages with 'pip install -r requirements.txt'")
        
        if not ollama_ok:
            print("- Make sure Ollama is installed and running")
            print("- Install the Mistral model with 'ollama pull mistral'")
    
    print("=========================================")

if __name__ == "__main__":
    main() 