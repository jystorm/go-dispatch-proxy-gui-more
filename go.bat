@echo off
cd /d "%~dp0"
echo Starting go-dispatch-proxy-gui-more...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Check if the main script exists
if not exist "go-dispatch-proxy-gui.py" (
    echo ERROR: go-dispatch-proxy-gui.py not found in current directory
    pause
    exit /b 1
)

REM Run the application
python go-dispatch-proxy-gui.py

REM Show exit message
echo.
echo Application closed.
pause
