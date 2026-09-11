@echo off
echo Starting Dad of Anton applications...

:: Setup and start backend
echo Setting up FastAPI backend...
cd backend
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install -q -r requirements.txt
start "Backend" cmd /c "uvicorn app.main:app --reload --port 8000"
cd ..

:: Setup and start frontend
echo Setting up Next.js frontend...
cd frontend
if not exist "node_modules" (
    echo Installing npm dependencies...
    call npm install
)
start "Frontend" cmd /c "npm run dev"
cd ..

echo.
echo Both applications started!
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Press any key to stop both servers...
pause >nul

:: Kill the server processes
taskkill /FI "WindowTitle eq Backend" /T /F >nul 2>&1
taskkill /FI "WindowTitle eq Frontend" /T /F >nul 2>&1
echo Servers stopped.
