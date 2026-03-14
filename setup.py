"""
Setup script for the Auction Management System.

Run this script to verify your installation and setup.
"""

import sys
from pathlib import Path

from config import DATA_DIR, IMAGES_DIR, PLAYERS_CSV_PATH, TEAMS_CONFIG_PATH


def check_python_version():
    """Check if Python version is 3.8 or higher."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True


def check_dependencies():
    """Check if required packages are installed."""
    required_packages = ["streamlit", "pandas", "PIL"]
    missing_packages = []

    for package in required_packages:
        try:
            if package == "PIL":
                __import__("PIL")
            else:
                __import__(package)
            print(f"✅ {package} is installed")
        except ImportError:
            print(f"❌ {package} is not installed")
            missing_packages.append(package)

    if missing_packages:
        print(f"\nInstall missing packages with:")
        print(f"pip install -r requirements.txt")
        return False

    return True


def check_directories():
    """Check if required directories exist."""
    directories = [DATA_DIR, IMAGES_DIR]

    for directory in directories:
        if directory.exists():
            print(f"✅ Directory exists: {directory}")
        else:
            print(f"⚠️  Creating directory: {directory}")
            directory.mkdir(parents=True, exist_ok=True)

    return True


def check_data_files():
    """Check if data files exist."""
    if PLAYERS_CSV_PATH.exists():
        print(f"✅ Players CSV found: {PLAYERS_CSV_PATH}")

        # Count players
        try:
            import pandas as pd

            df = pd.read_csv(PLAYERS_CSV_PATH)
            print(f"   📊 {len(df)} players loaded")
        except Exception as e:
            print(f"   ⚠️  Error reading CSV: {e}")

    else:
        print(f"❌ Players CSV not found: {PLAYERS_CSV_PATH}")
        print(f"   Create this file or export from Google Sheets")

    if TEAMS_CONFIG_PATH.exists():
        print(f"✅ Teams config found: {TEAMS_CONFIG_PATH}")

        # Count teams
        try:
            import json

            with open(TEAMS_CONFIG_PATH, "r") as f:
                teams = json.load(f)
            print(f"   📊 {len(teams)} teams configured")
        except Exception as e:
            print(f"   ⚠️  Error reading config: {e}")

    else:
        print(f"⚠️  Teams config not found: {TEAMS_CONFIG_PATH}")
        print(f"   Default teams will be created on first run")


def check_images():
    """Check if player images exist."""
    image_files = list(IMAGES_DIR.glob("*.jpg")) + list(IMAGES_DIR.glob("*.png"))

    if image_files:
        print(f"✅ Found {len(image_files)} images in {IMAGES_DIR}")
    else:
        print(f"⚠️  No images found in {IMAGES_DIR}")
        print(f"   Add player photos to this directory")


def main():
    """Run all setup checks."""
    print("=" * 60)
    print("🏏 Cricket Auction Management System - Setup Check")
    print("=" * 60)
    print()

    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Directories", check_directories),
        ("Data Files", check_data_files),
        ("Images", check_images),
    ]

    results = []
    for name, check_func in checks:
        print(f"\n{name}:")
        print("-" * 40)
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Error during {name} check: {e}")
            results.append(False)

    print("\n" + "=" * 60)

    if all(r is not False for r in results):
        print("✅ Setup complete! Ready to run the auction.")
        print("\nStart the application with:")
        print("   streamlit run app.py")
    else:
        print("⚠️  Some issues need attention. Review the output above.")

    print("=" * 60)


if __name__ == "__main__":
    main()
