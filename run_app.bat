@echo off
echo ====================================
echo    WNS Vox BOT - Quick Start
echo ====================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo [1/4] Checking Python installation...
python --version

echo [2/4] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
)

echo [3/4] Activating virtual environment...
call venv\Scripts\activate.bat

echo [4/4] Installing dependencies...
pip install -r requirements.txt

echo.
echo ====================================
echo   Setup Complete! Starting App...
echo ====================================
echo.
echo The app will open in your browser at:
echo http://localhost:8501
echo.
echo Press Ctrl+C to stop the application
echo.

REM Start the application
streamlit run app_production.py --server.port 8501

pause