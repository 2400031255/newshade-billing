#!/bin/bash

echo ""
echo "=========================================="
echo "  NEWSHADES FAMILY SALON - BILLING SYSTEM"
echo "=========================================="
echo ""
echo "  Starting server, please wait..."
echo ""

# Install dependencies
pip install flask werkzeug gunicorn -q

# Get local IP
IP=$(ipconfig getifaddr en0 2>/dev/null || hostname -I 2>/dev/null | awk '{print $1}')

echo "=========================================="
echo "  App is running!"
echo ""
echo "  Open on THIS computer:"
echo "  http://localhost:8080"
echo ""
echo "  Open on OTHER devices (WiFi):"
echo "  http://$IP:8080"
echo "=========================================="
echo ""
echo "  DO NOT close this window while using app."
echo ""

# Open browser automatically
open http://localhost:8080 2>/dev/null || xdg-open http://localhost:8080 2>/dev/null

# Start Flask app
python app.py
