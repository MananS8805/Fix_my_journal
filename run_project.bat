@echo off
echo =========================================
echo  Manuscript Formatting Agent
echo =========================================
echo.

REM Kill any old processes on port 8001
echo Killing any old processes on port 8001...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001 ^| findstr LISTENING') do (
    taskkill /PID %%a /F >nul 2>&1
)
echo Done.
echo.

REM Install Python dependencies
echo Installing Python dependencies...
cd /d "c:\Users\manan\Desktop\New folder"
python -m pip install -r requirements.txt --quiet
echo Done.
echo.

REM Start backend with PYTHONPATH set correctly
echo Starting backend on http://localhost:8001 ...
start "Backend - Manuscript Agent" cmd /k "cd /d c:\Users\manan\Desktop\New folder\backend && set PYTHONPATH=c:\Users\manan\Desktop\New folder && python -m uvicorn main:app --port 8001"

REM Wait 3 seconds for backend to start before launching frontend
timeout /t 3 /nobreak >nul

REM Start frontend
echo Starting frontend on http://localhost:3000 ...
start "Frontend - Manuscript Agent" cmd /k "cd /d c:\Users\manan\Desktop\New folder\frontend && npm.cmd install && npm.cmd start"

echo.
echo =========================================
echo  Both servers are starting...
echo  Backend:  http://localhost:8001
echo  Frontend: http://localhost:3000
echo  API Docs: http://localhost:8001/docs
echo =========================================