@echo off
title FloodGuard India – API Server
color 0B
echo.
echo  ==========================================
echo    FloodGuard India - Starting API Server
echo  ==========================================
echo.
echo  Loading ML model and CSV datasets...
echo  (This may take 30-60 seconds on first run)
echo.

set PYTHON="C:\Users\Atharva More\AppData\Local\Python\bin\python3.exe"

:: Check if python exists at that path
if not exist %PYTHON% (
    echo  [ERROR] Python not found at expected path.
    echo  Trying python3...
    set PYTHON=python3
)

echo  Starting Flask server at http://127.0.0.1:5000
echo  Keep this window open while using the frontend!
echo.
echo  Open frontend\index.html in Chrome after server starts.
echo  Press Ctrl+C to stop the server.
echo.
echo  ==========================================
echo.

%PYTHON% api.py

echo.
echo  Server stopped. Press any key to exit.
pause
