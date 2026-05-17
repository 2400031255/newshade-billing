@echo off
title Newshades - Add to Startup
cd /d "%~dp0"

:: Create shortcut in Windows Startup folder
set STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set VBS_PATH=%~dp0NewshadesSalon.vbs

powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%STARTUP%\NewshadesSalon.lnk'); $s.TargetPath = '%VBS_PATH%'; $s.WorkingDirectory = '%~dp0'; $s.Description = 'Newshades Family Salon'; $s.Save()"

:: Also create Desktop shortcut
set DESKTOP=%USERPROFILE%\Desktop
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%DESKTOP%\Newshades Salon.lnk'); $s.TargetPath = '%VBS_PATH%'; $s.WorkingDirectory = '%~dp0'; $s.Description = 'Newshades Family Salon'; $s.Save()"

echo.
echo ==========================================
echo   Done!
echo   - Shortcut added to Desktop
echo   - App will auto-start on Windows boot
echo ==========================================
echo.
pause
