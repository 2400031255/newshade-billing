@echo off
title Newshades Family Salon
color 0A

echo.
echo ==========================================
echo   NEWSHADES FAMILY SALON - BILLING SYSTEM
echo ==========================================
echo.

cd /d "%~dp0"

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo   ERROR: Python is not installed!
    echo   Please run INSTALL.bat first.
    echo.
    pause
    exit
)

:: Install dependencies (show errors if any)
echo   Checking dependencies...
python -m pip install flask werkzeug reportlab -q
if %errorlevel% neq 0 (
    color 0C
    echo   ERROR: Failed to install dependencies.
    echo   Check your internet connection and try again.
    pause
    exit
)

:: Kill anything on port 8080
echo   Clearing port 8080...
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| find ":8080" ^| find "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)
timeout /t 1 /nobreak >nul

:: Start Flask visibly so errors show
echo   Starting server...
start "Newshades Server" /min python app.py

:: Wait longer for server to be ready
echo   Waiting for server to start...
timeout /t 5 /nobreak >nul

:: Check if server actually started
netstat -aon | find ":8080" | find "LISTENING" >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo.
    echo   ERROR: Server failed to start!
    echo   Close this window, then run START_SALON.bat again.
    echo   If problem persists, run INSTALL.bat again.
    echo.
    pause
    exit
)

:: Open browser
echo   Opening browser...
start http://localhost:8080

echo.
echo ==========================================
echo   App is running at http://localhost:8080
echo   DO NOT close this window!
echo ==========================================
echo.
pause
