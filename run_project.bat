@echo off
echo =========================================
echo  Manuscript Formatting Agent
echo =========================================
echo.

REM ── Dynamic path: works no matter where the folder is ─────────────────────
set "ROOT=%~dp0"
REM Remove trailing backslash
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

REM ── Check Python is installed ─────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8+ and add it to PATH.
    pause
    exit /b 1
)

REM ── Check Node/npm is installed ───────────────────────────────────────────
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found. Please install Node.js from https://nodejs.org
    pause
    exit /b 1
)

REM ── Check GROQ_API_KEY is set ─────────────────────────────────────────────
if "%GROQ_API_KEY%"=="" (
    REM Try loading from .env file if it exists
    if exist "%ROOT%\.env" (
        for /f "usebackq tokens=1,* delims==" %%A in ("%ROOT%\.env") do (
            if "%%A"=="GROQ_API_KEY" set "GROQ_API_KEY=%%B"
        )
    )
)

if "%GROQ_API_KEY%"=="" (
    echo [ERROR] GROQ_API_KEY is not set.
    echo.
    echo Please do ONE of the following:
    echo   1. Create a .env file in the project root with:
    echo         GROQ_API_KEY=your_key_here
    echo   2. Or set it manually in this terminal:
    echo         set GROQ_API_KEY=your_key_here
    echo.
    echo Get your free API key at: https://console.groq.com
    pause
    exit /b 1
)
echo [OK] GROQ_API_KEY found.
echo.

REM ── Kill any old processes on port 8001 ───────────────────────────────────
echo Killing any old processes on port 8001...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001 ^| findstr LISTENING') do (
    taskkill /PID %%a /F >nul 2>&1
)
echo Done.
echo.

REM ── Install Python dependencies ───────────────────────────────────────────
echo Installing Python dependencies...
cd /d "%ROOT%"
python -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install Python dependencies.
    pause
    exit /b 1
)
echo Done.
echo.

REM ── Start backend ─────────────────────────────────────────────────────────
echo Starting backend on http://localhost:8001 ...
start "Backend - Manuscript Agent" cmd /k "cd /d "%ROOT%\backend" && set PYTHONPATH=%ROOT% && set GROQ_API_KEY=%GROQ_API_KEY% && python -m uvicorn main:app --port 8001 --reload"

REM ── Wait for backend to be ready ──────────────────────────────────────────
echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

REM ── Install frontend deps only if node_modules missing ────────────────────
echo Checking frontend dependencies...
if not exist "%ROOT%\frontend\node_modules" (
    echo node_modules not found. Running npm install ^(first time only^)...
    cd /d "%ROOT%\frontend"
    npm.cmd install
    if errorlevel 1 (
        echo [ERROR] npm install failed.
        pause
        exit /b 1
    )
) else (
    echo node_modules already exists. Skipping npm install.
)
echo Done.
echo.

REM ── Start frontend ────────────────────────────────────────────────────────
echo Starting frontend on http://localhost:3000 ...
start "Frontend - Manuscript Agent" cmd /k "cd /d "%ROOT%\frontend" && npm.cmd start"

echo.
echo =========================================
echo  Both servers are starting...
echo  Backend:  http://localhost:8001
echo  Frontend: http://localhost:3000
echo  API Docs: http://localhost:8001/docs
echo =========================================
echo.
echo Press any key to close this window.
echo ^(The backend and frontend will keep running in their own windows^)
pause >nul