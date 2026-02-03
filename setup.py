#!/usr/bin/env python3
"""
Setup script for Centralized Trading Database
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e.stderr}")
        return False

def main():
    print("=== Centralized Trading Database Setup ===\n")
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("Error: Python 3.7 or higher is required")
        sys.exit(1)
    
    print(f"✓ Python {sys.version.split()[0]} detected")
    
    # Create virtual environment
    if not os.path.exists("venv"):
        if not run_command("python -m venv venv", "Creating virtual environment"):
            sys.exit(1)
    
    # Activate virtual environment and install dependencies
    if os.name == 'nt':  # Windows
        activate_cmd = "venv\\Scripts\\activate && "
    else:  # Unix/Linux/macOS
        activate_cmd = "source venv/bin/activate && "
    
    if not run_command(f"{activate_cmd}pip install -r requirements.txt", "Installing dependencies"):
        sys.exit(1)
    
    # Create .env file if it doesn't exist
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            if os.name == 'nt':
                run_command("copy .env.example .env", "Creating .env file")
            else:
                run_command("cp .env.example .env", "Creating .env file")
            print("⚠️  Please edit .env file with your database credentials")
        else:
            print("⚠️  Please create .env file with your configuration")
    
    # Create backups directory
    os.makedirs("backups", exist_ok=True)
    print("✓ Backups directory created")
    
    print("\n=== Setup Complete ===")
    print("Next steps:")
    print("1. Edit .env file with your database credentials")
    print("2. Ensure PostgreSQL is running")
    print("3. Run: python app.py")
    print("\nFor Windows: venv\\Scripts\\activate")
    print("For Unix/Linux/macOS: source venv/bin/activate")

if __name__ == "__main__":
    main()