@echo off
title Newshades Salon - Setup
color 0D

echo.
echo  ==========================================
echo    NEWSHADES FAMILY SALON - SETUP
echo  ==========================================
echo.

:: Install required packages
echo  [1/3] Installing dependencies...
pip install flask werkzeug pyinstaller -q

:: Build the exe
echo  [2/3] Building app, please wait (2-3 mins)...
pyinstaller --noconfirm --onefile ^
  --name "NewshadesSalon" ^
  --add-data "templates;templates" ^
  --add-data "static;static" ^
  --hidden-import flask ^
  --hidden-import werkzeug ^
  --hidden-import werkzeug.security ^
  --hidden-import jinja2 ^
  --hidden-import click ^
  --exclude-module PyQt5 ^
  --exclude-module PySide6 ^
  --exclude-module tkinter ^
  launcher.py

:: Create desktop shortcut
echo  [3/3] Creating desktop shortcut...

set SCRIPT="%TEMP%\CreateShortcut.vbs"
set TARGET="%CD%\dist\NewshadesSalon.exe"
set SHORTCUT="%USERPROFILE%\Desktop\Newshades Salon.lnk"
set ICON="%CD%\static\logo.jpeg"

echo Set oWS = WScript.CreateObject("WScript.Shell") > %SCRIPT%
echo sLinkFile = %SHORTCUT% >> %SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %SCRIPT%
echo oLink.TargetPath = %TARGET% >> %SCRIPT%
echo oLink.WorkingDirectory = "%CD%\dist" >> %SCRIPT%
echo oLink.Description = "Newshades Family Salon Billing" >> %SCRIPT%
echo oLink.Save >> %SCRIPT%
cscript /nologo %SCRIPT%
del %SCRIPT%

echo.
echo  ==========================================
echo   SETUP COMPLETE!
echo.
echo   A shortcut has been added to your Desktop
echo   named "Newshades Salon"
echo.
echo   Just double-click it every day to start!
echo  ==========================================
echo.
pause
