@echo off
cd /d "%~dp0"
setlocal
echo ============================================================
echo Starting SECURE DATA WIPING SYSTEM - Enterprise Edition
echo ============================================================

:: Check for virtual environment
if not exist "venv" (
    echo [INFO] Creating isolated virtual environment...
    python -m venv venv
)

:: Activate environment
echo [INFO] Activating environment...
call venv\Scripts\activate.bat

:: Install/Update dependencies
echo [INFO] Synchronizing dependencies...
pip install -r requirements.txt -q

:: Launch application
echo [INFO] Launching Secure Data Wiping Protocol...
python app.py

:: Post-execution cleanup
echo.
echo [INFO] Finalizing session and cleaning up dependencies...
call deactivate
rd /s /q venv
echo [SUCCESS] Session closed securely.
echo ============================================================
pause