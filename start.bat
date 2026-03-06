@echo off
REM Start Manuscript Formatting Agent on Windows

echo =========================================
echo Manuscript Formatting Agent
echo =========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

REM Check if dependencies are installed
echo Checking dependencies...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo.
echo Starting API Server...
echo =========================================
echo.
echo API Available at: http://localhost:8001
echo.
echo Swagger Docs:     http://localhost:8001/docs
echo ReDoc:            http://localhost:8001/redoc
echo.
echo Press CTRL+C to stop the server
echo =========================================
echo.

cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001

pause
