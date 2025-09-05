#!/usr/bin/env python3
"""Environment setup script for story-curator project.

This script handles the installation and setup of all dependencies
needed for development and testing, including:
- Python package dependencies
- NLTK data downloads
- spaCy model downloads
- Environment validation

Can be run locally or in CI environments.
"""

import sys
import subprocess
import os
from pathlib import Path


def run_command(command, description, required=True, shell=False):
    """Run a command and handle errors appropriately."""
    print(f"🔄 {description}...")
    try:
        if shell:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        else:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        if required:
            print(f"❌ {description} failed: {e}")
            if e.stdout:
                print(f"STDOUT: {e.stdout}")
            if e.stderr:
                print(f"STDERR: {e.stderr}")
            return False
        else:
            print(f"⚠️  {description} failed (optional): {e}")
            return True


def install_python_dependencies():
    """Install Python package dependencies."""
    print("\n📦 Installing Python dependencies...")
    
    # Upgrade pip first
    if not run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                      "Upgrading pip"):
        return False
    
    # Install main dependencies
    if not run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      "Installing main dependencies"):
        return False
    
    # Install development dependencies
    if not run_command([sys.executable, "-m", "pip", "install", "-r", "requirements-dev.txt"], 
                      "Installing development dependencies"):
        return False
    
    # Install package in development mode
    if not run_command([sys.executable, "-m", "pip", "install", "-e", "."], 
                      "Installing package in development mode"):
        return False
    
    return True


def verify_critical_imports():
    """Verify that critical dependencies can be imported."""
    print("\n🔍 Verifying critical dependencies...")
    
    critical_imports = [
        ("ffmpeg", "ffmpeg-python"),
        ("pytest_asyncio", "pytest-asyncio"),
        ("nltk", "NLTK"),
        ("spacy", "spaCy")
    ]
    
    for module, description in critical_imports:
        try:
            __import__(module)
            print(f"✅ {description} import successful")
        except ImportError as e:
            print(f"❌ {description} import failed: {e}")
            return False
    
    return True


def download_nltk_data():
    """Download required NLTK data packages."""
    print("\n📚 Downloading NLTK data...")
    
    nltk_packages = [
        ("stopwords", "English stopwords"),
        ("punkt", "Punkt tokenizer"),
        ("wordnet", "WordNet lexical database"),
        ("averaged_perceptron_tagger", "POS tagger"),
        ("omw-1.4", "Open Multilingual Wordnet")  # Often needed with wordnet
    ]
    
    try:
        import nltk
        for package, description in nltk_packages:
            try:
                nltk.data.find(f'tokenizers/{package}' if package == 'punkt' 
                              else f'corpora/{package}' if package in ['stopwords', 'wordnet', 'omw-1.4']
                              else f'taggers/{package}')
                print(f"✅ {description} already available")
            except LookupError:
                print(f"⬇️  Downloading {description}...")
                try:
                    nltk.download(package, quiet=True)
                    print(f"✅ {description} downloaded successfully")
                except Exception as e:
                    print(f"⚠️  Failed to download {description}: {e}")
        return True
    except ImportError:
        print("❌ NLTK not available, skipping data downloads")
        return False


def download_spacy_model():
    """Download required spaCy model."""
    print("\n🧠 Setting up spaCy model...")
    
    model_name = "en_core_web_sm"
    
    # Check if model is already installed
    try:
        import spacy
        spacy.load(model_name)
        print(f"✅ spaCy model '{model_name}' already available")
        return True
    except (ImportError, OSError):
        pass
    
    # Try to download the model
    return run_command([sys.executable, "-m", "spacy", "download", model_name], 
                      f"Downloading spaCy model '{model_name}'", 
                      required=True)


def setup_environment_variables():
    """Set up development environment variables."""
    print("\n🔧 Setting up environment variables...")
    
    env_vars = {
        "TESTING": "true",
        "WHISPER_MODEL": "tiny",
        "PYTHONPATH": str(Path.cwd() / "src")
    }
    
    for var, value in env_vars.items():
        os.environ[var] = value
        print(f"✅ Set {var}={value}")
    
    return True


def main():
    """Main setup function."""
    print("🚀 Starting story-curator environment setup...")
    print(f"📍 Working directory: {Path.cwd()}")
    print(f"🐍 Python version: {sys.version}")
    
    # Change to project root if we're in scripts directory
    if Path.cwd().name == "scripts":
        os.chdir(Path.cwd().parent)
        print(f"📂 Changed to project root: {Path.cwd()}")
    
    # Verify we're in the right directory
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt not found. Are you in the project root?")
        return 1
    
    success = True
    
    # Run setup steps
    if not install_python_dependencies():
        success = False
    
    if not verify_critical_imports():
        success = False
    
    if not download_nltk_data():
        print("⚠️  NLTK data setup had issues, but continuing...")
    
    if not download_spacy_model():
        print("❌ spaCy model setup failed - this is required for the application")
        success = False
    
    setup_environment_variables()
    
    if success:
        print("\n🎉 Environment setup completed successfully!")
        print("\n📋 Next steps:")
        print("   • Run tests: pytest src/")
        print("   • Run unit tests only: pytest src/ -m 'not integration'")
        print("   • Run integration tests: pytest src/ -m 'integration'")
        return 0
    else:
        print("\n💥 Environment setup encountered errors!")
        print("   Check the error messages above and resolve issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
