@echo off
setlocal
title FloodGuard India - API Server
cd /d "%~dp0"

echo Starting FloodGuard India API at http://127.0.0.1:5000
echo Press Ctrl+C to stop the server.
echo.

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" api.py
) else if exist "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" api.py
) else (
    py -3 api.py 2>nul || python api.py
)

if errorlevel 1 (
    echo.
    echo API stopped with an error. Install dependencies with:
    echo   python -m pip install -r requirements.txt
)
pause
