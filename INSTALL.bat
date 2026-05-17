@echo off
title Newshades Salon - One Time Setup
color 0A

echo.
echo ==========================================
echo   NEWSHADES FAMILY SALON - SETUP
echo ==========================================
echo.

cd /d "%~dp0"

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   Installing Python, please wait...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%temp%\python_installer.exe'"
    "%temp%\python_installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 Include_launcher=0
    del "%temp%\python_installer.exe" >nul 2>&1
    for /f "tokens=*" %%i in ('powershell -Command "[System.Environment]::GetEnvironmentVariable(\"PATH\",\"User\")"') do set "PATH=%%i;%PATH%"
)

:: Install dependencies
echo   Installing dependencies...
python -m pip install flask werkzeug reportlab -q

:: Desktop shortcut
echo   Creating Desktop shortcut...
set VBS_PATH=%~dp0NewshadesSalon.vbs
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Newshades Salon.lnk'); $s.TargetPath = '%VBS_PATH%'; $s.WorkingDirectory = '%~dp0'; $s.Description = 'Newshades Family Salon'; $s.Save()"

:: Auto-start on boot
echo   Adding to startup...
set STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%STARTUP%\NewshadesSalon.lnk'); $s.TargetPath = '%VBS_PATH%'; $s.WorkingDirectory = '%~dp0'; $s.Description = 'Newshades Family Salon'; $s.Save()"

echo.
color 0A
echo ==========================================
echo   SETUP COMPLETE!
echo.
echo   - Desktop shortcut created
echo   - App will auto-open on Windows startup
echo   - Double-click "Newshades Salon" on Desktop
echo ==========================================
echo.
pause
