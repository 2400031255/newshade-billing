@echo off
title Building Newshades Salon App...
color 0D

echo.
echo  ==========================================
echo    NEWSHADES SALON - Building Windows App
echo  ==========================================
echo.

:: Install required packages
echo  Installing dependencies...
pip install flask werkzeug pyinstaller -q

:: Build the exe
echo  Building EXE, please wait (2-3 mins)...
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

echo.
echo  ==========================================
echo   DONE! Your app is ready at:
echo   dist\NewshadesSalon.exe
echo  ==========================================
echo.
pause
