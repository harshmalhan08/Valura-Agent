@echo off
REM Valura AI System - Status Script (Windows)
REM This script checks the status of the Valura AI server

REM Change to the script's directory
cd /d "%~dp0"

echo ========================================
echo    Valura AI System Status
echo ========================================
echo.

set SERVER_RUNNING=0

REM Check Valura AI Server (Port 9000)
echo [CHECK] Valura AI Server (Port 9000)...
netstat -aon | find ":9000" | find "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Server is running
    for /f "tokens=5" %%a in ('netstat -aon ^| find ":9000" ^| find "LISTENING"') do (
        echo    PID: %%a
    )
    echo    URL: http://localhost:9000
    echo    Docs: http://localhost:9000/docs
    echo    Metrics: http://localhost:9000/metrics
    set SERVER_RUNNING=1
) else (
    echo [ERROR] Server is not running
)
echo.

REM Overall status
echo ========================================
if %SERVER_RUNNING% equ 1 (
    echo [SUCCESS] System is operational!
    echo.
    echo Access Points:
    echo    UI Dashboard: http://localhost:9000
    echo    Backend API: http://localhost:9000/query
    echo    API Docs: http://localhost:9000/docs
    echo    Prometheus Metrics: http://localhost:9000/metrics
) else (
    echo [ERROR] System is not running
    echo    Run start.bat to start the system
)
echo ========================================
echo.

REM Show recent logs if they exist
if exist logs\backend.log (
    echo [INFO] Recent Server Logs:
    powershell -Command "Get-Content logs\backend.log -Tail 5"
    echo.
)

pause
