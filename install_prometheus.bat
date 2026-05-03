@echo off
REM Install Prometheus Client Package
REM This script installs the prometheus-client package in the Valura virtual environment

echo ========================================
echo    Installing Prometheus Client
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "Valura\Scripts\activate.bat" (
    echo [ERROR] Virtual environment 'Valura' not found!
    echo Please create it first: python -m venv Valura
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call Valura\Scripts\activate.bat

REM Install prometheus-client
echo [INFO] Installing prometheus-client...
pip install prometheus-client>=0.20.0

REM Verify installation
echo.
echo [INFO] Verifying installation...
python -c "import prometheus_client; print('[SUCCESS] prometheus-client installed successfully!')" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Installation verification failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo [SUCCESS] Installation complete!
echo ========================================
echo.
echo You can now start the server with: start.bat
echo.

pause
