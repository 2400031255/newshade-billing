@echo off
title Newshades Salon - Setup
color 0A

echo.
echo ==========================================
echo   NEWSHADES FAMILY SALON - SETUP
echo ==========================================
echo.

cd /d "%~dp0"

:: ── Step 1: Check Python ──────────────────────────────────────────────────
echo   Checking Python...
python --version >nul 2>&1
if %errorlevel% == 0 goto :python_found

py --version >nul 2>&1
if %errorlevel% == 0 goto :python_found

:: Python not found - download and install
echo   Python not found. Downloading Python 3.11...
echo   Please wait, this may take 2-3 minutes...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%temp%\pyinstall.exe' -UseBasicParsing"

if not exist "%temp%\pyinstall.exe" (
    color 0C
    echo   ERROR: Could not download Python.
    echo   Please check internet and try again.
    pause
    exit /b
)

echo   Installing Python...
"%temp%\pyinstall.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 Include_launcher=0 Include_test=0
del "%temp%\pyinstall.exe" >nul 2>&1

echo   Python installed! Restarting setup with new PATH...
echo.

:: Re-launch this script in a new cmd so PATH is refreshed
start "Newshades Setup" cmd /c "%~f0"
exit /b

:python_found
echo   Python found OK.
echo.

:: ── Step 2: Find correct python command ──────────────────────────────────
set PYTHON=python
python --version >nul 2>&1
if %errorlevel% neq 0 set PYTHON=py

:: ── Step 3: Install dependencies ─────────────────────────────────────────
echo   Installing dependencies...
%PYTHON% -m pip install --upgrade pip -q
%PYTHON% -m pip install flask werkzeug reportlab -q

if %errorlevel% neq 0 (
    color 0C
    echo   ERROR: Failed to install dependencies.
    echo   Check internet connection and try again.
    pause
    exit /b
)
echo   Dependencies installed OK.
echo.

:: ── Step 4: Write correct python path into VBS launcher ──────────────────
echo   Configuring launcher...
for /f "tokens=*" %%i in ('%PYTHON% -c "import sys; print(sys.executable)"') do set PYEXE=%%i

:: Rewrite NewshadesSalon.vbs with the exact python path
set APPDIR=%~dp0
(
echo Set WshShell = CreateObject^("WScript.Shell"^)
echo appDir = "%APPDIR%"
echo pyExe = "%PYEXE%"
echo WshShell.Run "cmd /c for /f ""tokens=5"" %%a in ^('netstat -aon ^| find "":8080"" ^| find ""LISTENING""'^) do taskkill /f /pid %%a", 0, True
echo WshShell.Run """" ^& pyExe ^& """ """ ^& appDir ^& "app.py""", 0, False
echo WScript.Sleep 5000
echo WshShell.Run "http://localhost:8080"
) > "%APPDIR%NewshadesSalon.vbs"

:: ── Step 5: Desktop shortcut ─────────────────────────────────────────────
echo   Creating Desktop shortcut...
set VBS_PATH=%APPDIR%NewshadesSalon.vbs
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Newshades Salon.lnk'); $s.TargetPath = '%VBS_PATH%'; $s.WorkingDirectory = '%APPDIR%'; $s.Description = 'Newshades Family Salon'; $s.Save()"

:: ── Step 6: Startup entry ────────────────────────────────────────────────
echo   Adding to Windows startup...
set STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%STARTUP%\NewshadesSalon.lnk'); $s.TargetPath = '%VBS_PATH%'; $s.WorkingDirectory = '%APPDIR%'; $s.Description = 'Newshades Family Salon'; $s.Save()"

echo.
color 0A
echo ==========================================
echo   SETUP COMPLETE!
echo.
echo   Desktop shortcut created.
echo   App will auto-start on Windows boot.
echo.
echo   Double-click "Newshades Salon" on Desktop
echo   to open the app anytime.
echo ==========================================
echo.
pause
