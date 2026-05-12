#!/bin/bash
echo "Installing PyInstaller..."
pip install pyinstaller -q

echo "Building app..."
pyinstaller --noconfirm --onefile --windowed \
  --name "NewshadesSalon" \
  --add-data "templates:templates" \
  --add-data "static:static" \
  --hidden-import flask \
  --hidden-import werkzeug \
  --hidden-import jinja2 \
  --hidden-import click \
  launcher.py

echo ""
echo "✅ Done! Find your app in the 'dist' folder"
echo "   dist/NewshadesSalon  ← share this file"
