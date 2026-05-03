@echo off
REM Valura AI System - Stop Script (Windows)
REM This script stops the Valura AI server

REM Change to the script's directory
cd /d "%~dp0"

echo ========================================
echo    Valura AI System Shutdown
echo ========================================
echo.

REM Stop Valura AI Server (Port 9000)
echo [INFO] Stopping Valura AI Server...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":9000" ^| find "LISTENING"') do (
    echo [INFO] Killing process on port 9000 (PID: %%a)
    taskkill /F /PID %%a >nul 2>&1
)

REM Also kill any Python processes running uvicorn
echo [INFO] Cleaning up Python processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq uvicorn*" >nul 2>&1

REM Clean up PID directory
if exist .pids rmdir /s /q .pids >nul 2>&1

echo.
echo [SUCCESS] Server stopped successfully!
echo.
echo [INFO] Logs are preserved in:
echo    logs\backend.log
echo.
echo [INFO] To start the system again, run: start.bat
echo.

pause
