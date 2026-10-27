@echo off
setlocal
cd /d "%~dp0"
title Nyaya Saar - Legal Document Summarizer

if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found. Running setup first...
    echo.
    call "%~dp0setup.bat"
    if errorlevel 1 exit /b 1
)

if not exist "app.py" (
    echo ERROR: app.py was not found.
    echo Extract this file into the main legal-document-summarizer project folder.
    echo.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Project environment was not created. Run setup.bat again.
    echo.
    pause
    exit /b 1
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 (
    echo ERROR: Could not activate the virtual environment.
    pause
    exit /b 1
)

echo ======================================================
echo        Nyaya Saar - Legal Document Summarizer
echo ======================================================
echo.
echo Starting Flask application...
echo Keep this window open while using the app.
echo Browser address: http://127.0.0.1:5000
echo Press Ctrl+C in this window to stop the server.
echo.

REM Open the browser after the Flask server has had time to start.
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:5000'"
python app.py

if errorlevel 1 (
    echo.
    echo The application exited with an error. Review the messages above.
    pause
)
endlocal
