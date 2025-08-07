#!/usr/bin/env python3
"""
Quick setup script for AI Job Finder
Run this to set up the project quickly
"""

import os
import subprocess
import sys

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def main():
    print("🚀 AI Job Finder Setup")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version.split()[0]} detected")
    
    # Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing dependencies"):
        print("💡 Try: python -m pip install -r requirements.txt")
        sys.exit(1)
    
    # Create .env file if it doesn't exist
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            run_command("cp .env.example .env", "Creating .env file from template")
            print("📝 Please edit .env file with your API keys:")
            print("   - GOOGLE_API_KEY: Get from https://makersuite.google.com/app/apikey")
            print("   - RAPIDAPI_KEY: Get from https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch")
        else:
            print("⚠️  .env.example not found, please create .env manually")
    else:
        print("✅ .env file already exists")
    
    # Run tests
    print("\n🧪 Running tests...")
    if run_command("python final_test.py", "Testing application"):
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Edit .env file with your API keys")
        print("2. Run: python app.py")
        print("3. Open: http://localhost:5000")
    else:
        print("\n⚠️  Tests failed - please check your API keys in .env")
        print("You can still run the app with: python app.py")

if __name__ == "__main__":
    main()