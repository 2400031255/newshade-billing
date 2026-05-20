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
echo   [1/5] Checking Python...

python --version >nul 2>&1
if %errorlevel% == 0 goto :python_found

py --version >nul 2>&1
if %errorlevel% == 0 goto :python_found

:: Python not found - download and install
echo.
echo   Python not found. Downloading Python 3.11...
echo   Please wait, this may take 2-3 minutes...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%temp%\pyinstall.exe' -UseBasicParsing"

if not exist "%temp%\pyinstall.exe" (
    color 0C
    echo.
    echo   ERROR: Could not download Python.
    echo   Check internet connection and try again.
    echo.
    pause
    exit /b
)

echo   Installing Python silently...
"%temp%\pyinstall.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 Include_launcher=0 Include_test=0
del "%temp%\pyinstall.exe" >nul 2>&1

echo   Python installed! Restarting setup...
echo.
start "Newshades Setup" cmd /k "%~f0"
exit /b

:python_found
echo   Python OK.
echo.

:: ── Step 2: Find exact python path ───────────────────────────────────────
set PYTHON=python
python --version >nul 2>&1
if %errorlevel% neq 0 set PYTHON=py

for /f "tokens=*" %%i in ('%PYTHON% -c "import sys; print(sys.executable)"') do set PYEXE=%%i
echo   Python path: %PYEXE%
echo.

:: ── Step 3: Install dependencies ─────────────────────────────────────────
echo   [2/5] Installing dependencies...
"%PYEXE%" -m pip install --upgrade pip -q
"%PYEXE%" -m pip install flask werkzeug reportlab -q

if %errorlevel% neq 0 (
    color 0C
    echo.
    echo   ERROR: Failed to install dependencies.
    echo   Check internet and try again.
    echo.
    pause
    exit /b
)
echo   Dependencies OK.
echo.

:: ── Step 4: Create data folder ───────────────────────────────────────────
echo   [3/5] Setting up data folder...
if not exist "%~dp0data" mkdir "%~dp0data"
if not exist "%~dp0data\bills.json"     echo {}> "%~dp0data\bills.json"
if not exist "%~dp0data\customers.json" echo {}> "%~dp0data\customers.json"
echo   Data folder OK.
echo.

:: ── Step 5: Write VBS launcher with exact python path ────────────────────
echo   [4/5] Creating launcher...
set APPDIR=%~dp0

(
echo Set WshShell = CreateObject^("WScript.Shell"^)
echo pyExe = "%PYEXE%"
echo appDir = "%APPDIR%"
echo.
echo ' Kill old server on port 8080
echo WshShell.Run "cmd /c for /f ""tokens=5"" %%a in ^('netstat -aon ^| find "":8080"" ^| find ""LISTENING""'^) do taskkill /f /pid %%a", 0, True
echo.
echo ' Start Flask silently
echo WshShell.Run """" ^& pyExe ^& """ """ ^& appDir ^& "app.py""", 0, False
echo.
echo ' Wait for server to start
echo WScript.Sleep 6000
echo.
echo ' Open browser
echo WshShell.Run "http://localhost:8080"
) > "%APPDIR%NewshadesSalon.vbs"

echo   Launcher OK.
echo.

:: ── Step 6: Desktop + Startup shortcuts ──────────────────────────────────
echo   [5/5] Creating shortcuts...
set VBS_PATH=%APPDIR%NewshadesSalon.vbs
set STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Newshades Salon.lnk'); $s.TargetPath = '%VBS_PATH%'; $s.WorkingDirectory = '%APPDIR%'; $s.Description = 'Newshades Family Salon'; $s.Save()"

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%STARTUP%\NewshadesSalon.lnk'); $s.TargetPath = '%VBS_PATH%'; $s.WorkingDirectory = '%APPDIR%'; $s.Description = 'Newshades Family Salon'; $s.Save()"

echo   Shortcuts OK.
echo.

:: ── Done ─────────────────────────────────────────────────────────────────
color 0A
echo ==========================================
echo   SETUP COMPLETE!
echo.
echo   - Desktop shortcut: "Newshades Salon"
echo   - App auto-starts on Windows boot
echo   - Data saved in: %APPDIR%data\
echo.
echo   Double-click "Newshades Salon" on Desktop
echo   to open the app now!
echo ==========================================
echo.
pause
