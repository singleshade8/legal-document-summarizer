@echo off
setlocal
cd /d "%~dp0"
title Nyaya Saar - Project Setup

echo ======================================================
echo        Nyaya Saar - Legal Document Summarizer
echo                    Setup
echo ======================================================
echo.

REM Check that Python 3.10 or newer is available.
set "PYTHON_COMMAND="
py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if not errorlevel 1 set "PYTHON_COMMAND=py -3"

if not defined PYTHON_COMMAND (
    python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
    if not errorlevel 1 set "PYTHON_COMMAND=python"
)

if not defined PYTHON_COMMAND (
    echo ERROR: Python 3.10 or newer was not found.
    echo Install Python 3.10+ from https://www.python.org/downloads/windows/
    echo During installation, select "Add python.exe to PATH".
    echo Then close and reopen this window and run setup.bat again.
    echo.
    pause
    exit /b 1
)

echo Python found. Creating the project virtual environment...
if not exist ".venv\Scripts\python.exe" (
    %PYTHON_COMMAND% -m venv .venv
    if errorlevel 1 goto :setup_failed
) else (
    echo Existing .venv detected; reusing it.
)

echo.
echo Updating pip inside the virtual environment...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :setup_failed

echo.
echo Installing project dependencies from requirements.txt...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :setup_failed

echo.
echo ======================================================
echo Setup completed successfully!
echo Next: double-click run.bat to start Nyaya Saar.
echo ======================================================
echo.
pause
exit /b 0

:setup_failed
echo.
echo ERROR: Setup did not finish successfully.
echo Check your internet connection and the error messages above.
echo Then run setup.bat again.
echo.
pause
exit /b 1
