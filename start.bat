@echo off
REM Valura AI System - Start Script (Windows)
REM This script starts both the backend API server and the UI server

REM Change to the script's directory
cd /d "%~dp0"

echo ========================================
echo    Valura AI System Startup
echo ========================================
echo.
echo [INFO] Working directory: %CD%
echo.

REM Check if .env file exists
if not exist .env (
    echo [ERROR] .env file not found in current directory!
    echo Current directory: %CD%
    echo.
    echo Please create a .env file with your OPENAI_API_KEY
    echo You can copy .env.example to .env and add your API key
    echo.
    echo Or run this script from the correct directory:
    echo    cd valura-ai-ai-engineer-assignment-harshmalhan08-main\valura-ai-ai-engineer-assignment-harshmalhan08-main
    echo    start.bat
    echo.
    pause
    exit /b 1
)

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    pause
    exit /b 1
)

REM Create Valura virtual environment if it doesn't exist
if not exist Valura (
    echo [INFO] Creating Valura virtual environment...
    python -m venv Valura
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo [SUCCESS] Valura virtual environment created!
    echo.
)

REM Activate Valura virtual environment
echo [INFO] Activating Valura virtual environment...
call Valura\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment!
    pause
    exit /b 1
)
echo [SUCCESS] Valura environment activated!
echo.

REM Check and install dependencies
echo [INFO] Checking dependencies...
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies!
        pause
        exit /b 1
    )
    echo [SUCCESS] Dependencies installed!
    echo.
)

REM Create logs directory if it doesn't exist
if not exist logs mkdir logs

REM Create PID directory
if not exist .pids mkdir .pids

REM Kill any existing processes on the ports
echo [INFO] Cleaning up existing processes...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":9000" ^| find "LISTENING"') do taskkill /F /PID %%a >nul 2>&1

REM Start Backend API Server (Port 9000) - serves both API and UI
echo [INFO] Starting Backend API Server on port 9000...
start /B python -m uvicorn src.api.app:app --host 0.0.0.0 --port 9000 --reload > logs\backend.log 2>&1

REM Wait a moment for backend to start
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo    System Started Successfully!
echo ========================================
echo.
echo [INFO] Backend API: http://localhost:9000
echo [INFO] UI Dashboard: http://localhost:9000
echo [INFO] API Docs: http://localhost:9000/docs
echo.
echo [INFO] Logs:
echo    Backend: logs\backend.log
echo.
echo [INFO] To stop the system, run: stop.bat
echo.

REM Optional: Open browser
REM timeout /t 1 /nobreak >nul
REM start http://localhost:3000

pause
