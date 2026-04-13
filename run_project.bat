@echo off
cd /d "%~dp0"

echo Starting MySQL service (if installed)...
set DB_STARTED=0

sc query MySQL80 | findstr /I "RUNNING" >nul 2>&1
if %errorlevel%==0 (
    echo MySQL80 is already running.
    set DB_STARTED=1
) else (
    net start MySQL80 >nul 2>&1
    if %errorlevel%==0 (
        echo MySQL80 started.
        set DB_STARTED=1
    )
)

if %DB_STARTED%==0 (
    sc query MySQL | findstr /I "RUNNING" >nul 2>&1
    if %errorlevel%==0 (
        echo MySQL is already running.
        set DB_STARTED=1
    ) else (
        net start MySQL >nul 2>&1
        if %errorlevel%==0 (
            echo MySQL started.
            set DB_STARTED=1
        )
    )
)

if %DB_STARTED%==0 (
    echo [WARN] Could not start MySQL service from batch.
    echo        Run this terminal as Administrator and start MySQL80 manually if needed.
)

powershell -ExecutionPolicy Bypass -File "%~dp0run_project.ps1"
