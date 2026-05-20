@echo off
title Newshades Family Salon
color 0A

echo.
echo ==========================================
echo   NEWSHADES FAMILY SALON
echo ==========================================
echo.

cd /d "%~dp0"

:: Find python
set PYTHON=
python --version >nul 2>&1
if %errorlevel% == 0 set PYTHON=python

if "%PYTHON%"=="" (
    py --version >nul 2>&1
    if %errorlevel% == 0 set PYTHON=py
)

if "%PYTHON%"=="" (
    color 0C
    echo   ERROR: Python not found!
    echo   Please run INSTALL.bat first.
    pause
    exit /b
)

:: Install/check dependencies silently
%PYTHON% -m pip install flask werkzeug reportlab -q 2>nul

:: Kill old process on port 8080
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| find ":8080" ^| find "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)
timeout /t 1 /nobreak >nul

:: Start Flask
echo   Starting app...
start "Newshades Server" /min cmd /c "%PYTHON% app.py"

:: Wait for server
echo   Please wait...
timeout /t 6 /nobreak >nul

:: Verify server started
netstat -aon 2>nul | find ":8080" | find "LISTENING" >nul
if %errorlevel% neq 0 (
    color 0C
    echo.
    echo   ERROR: App failed to start.
    echo   Run INSTALL.bat again and retry.
    pause
    exit /b
)

:: Open browser
start http://localhost:8080

echo.
echo ==========================================
echo   App is running!
echo   DO NOT close this window.
echo ==========================================
echo.
pause
