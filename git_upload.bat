@echo off
REM Git Upload Script for Windows
REM This script helps you upload your code to GitHub

echo ========================================
echo    Git Upload Helper
echo ========================================
echo.

REM Check if git is installed
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git is not installed!
    echo Please install Git from: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo [INFO] Git is installed
echo.

REM Check if already initialized
if exist ".git" (
    echo [INFO] Git repository already initialized
) else (
    echo [INFO] Initializing Git repository...
    git init
    echo [SUCCESS] Git repository initialized
)
echo.

REM Show current status
echo [INFO] Current Git status:
git status
echo.

REM Prompt for GitHub repository URL
echo ========================================
echo Please provide your GitHub repository URL
echo Example: https://github.com/username/repo-name.git
echo ========================================
set /p REPO_URL="Enter repository URL: "

if "%REPO_URL%"=="" (
    echo [ERROR] Repository URL cannot be empty!
    pause
    exit /b 1
)

echo.
echo [INFO] Adding files to Git...
git add .

echo [INFO] Creating commit...
git commit -m "Initial commit: Valura AI Agent Ecosystem with Prometheus monitoring"

echo [INFO] Adding remote repository...
git remote remove origin 2>nul
git remote add origin %REPO_URL%

echo [INFO] Pushing to GitHub...
git branch -M main
git push -u origin main

echo.
echo ========================================
echo [SUCCESS] Code uploaded to GitHub!
echo ========================================
echo.
echo Your repository: %REPO_URL%
echo.

pause
