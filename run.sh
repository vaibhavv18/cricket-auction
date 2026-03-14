#!/bin/bash
# Start script for the Auction Management System
# Only creates venv if it doesn't exist (much faster on subsequent runs)

echo "🏏 Halar Premier League Auction - Season 2026"
echo "=============================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "First run - setting up environment..."
    echo ""

    # Detect Python version
    PYTHON_CMD=""
    if command -v python3.12 &> /dev/null; then
        PYTHON_CMD="python3.12"
    elif command -v python3.11 &> /dev/null; then
        PYTHON_CMD="python3.11"
    elif command -v python3.10 &> /dev/null; then
        PYTHON_CMD="python3.10"
    elif command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    else
        echo "❌ Python 3 not found. Please install Python 3.10 or higher."
        exit 1
    fi

    echo "Using: $PYTHON_CMD"

    # Create virtual environment
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv venv

    # Activate and install
    source venv/bin/activate

    echo "Installing dependencies (this only happens once)..."
    pip install --upgrade pip setuptools wheel --quiet
    pip install --upgrade "streamlit>=1.31.0" "pandas>=2.0.0" "Pillow>=10.0.0" --quiet

    echo ""
    echo "✅ Setup complete!"
else
    # Just activate existing environment
    source venv/bin/activate
fi

echo ""
echo "Starting auction application..."
echo "Browser will open at http://localhost:8501"
echo "Press Ctrl+C to stop"
echo ""

streamlit run app.py
