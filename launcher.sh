#!/bin/bash

# Find python
PYTHON=$(which python3 || which python)
DIR="$(cd "$(dirname "$0")" && pwd)"

# Install deps silently if needed
$PYTHON -m pip install flask werkzeug reportlab -q 2>/dev/null

# Kill any old instance on port 8080
lsof -ti:8080 | xargs kill -9 2>/dev/null

# Start Flask in background
cd "$DIR"
$PYTHON app.py &
SERVER_PID=$!

# Wait for server to start
sleep 2

# Open in browser
open http://localhost:8080

# Keep running until browser/window closes
wait $SERVER_PID
