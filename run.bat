@echo off
REM Quick start script for the Auction Management System (Windows)

echo 🏏 Cricket Auction Management System
echo ====================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo Installing dependencies...
python -m pip install -q --upgrade pip
pip install -q -r requirements.txt

echo.
echo Starting Streamlit application...
echo Browser will open automatically at http://localhost:8501
echo.
echo Press Ctrl+C to stop the server
echo.

REM Run the application
streamlit run app.py
