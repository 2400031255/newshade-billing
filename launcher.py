import threading
import webbrowser
import time
import sys
import os

# Fix paths for PyInstaller
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
    os.chdir(BASE_DIR)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Ensure data dir exists next to the exe
DATA_DIR = os.path.join(os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Patch storage paths before importing app
os.environ["SALON_DATA_DIR"] = DATA_DIR

def open_browser():
    time.sleep(2)
    webbrowser.open("http://localhost:8080")

threading.Thread(target=open_browser, daemon=True).start()

from app import app
app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)
