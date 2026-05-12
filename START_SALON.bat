@echo off
title Newshades Family Salon - Billing System
color 0D

echo.
echo  ==========================================
echo    NEWSHADES FAMILY SALON - BILLING SYSTEM
echo  ==========================================
echo.
echo  Starting server, please wait...
echo.

:: Install dependencies silently
pip install flask werkzeug gunicorn -q

:: Get local IP
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    set IP=%%a
    goto :found
)
:found
set IP=%IP: =%

echo  ==========================================
echo   App is running!
echo.
echo   Open on THIS computer:
echo   http://localhost:8080
echo.
echo   Open on OTHER devices (WiFi):
echo   http://%IP%:8080
echo  ==========================================
echo.
echo  DO NOT close this window while using app.
echo.

:: Open browser automatically
start http://localhost:8080

:: Start Flask app
python app.py

pause
