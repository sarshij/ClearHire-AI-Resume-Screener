@echo off
echo =========================================
echo Starting ClearHire Resume Screener...
echo =========================================

echo.
echo Activating virtual environment...
call ..\venv\Scripts\activate.bat

echo.
echo Checking if PostgreSQL is running...
python -c "import socket; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); result = s.connect_ex(('127.0.0.1', 5432)); s.close(); exit(0 if result == 0 else 1)"
if %ERRORLEVEL% neq 0 (
    echo.
    echo ================================================================
    echo [ERROR] PostgreSQL Database is NOT running!
    echo Please make sure the PostgreSQL service is started on your laptop.
    echo You can start it from the 'Services' app in Windows.
    echo ================================================================
    echo.
    pause
    exit /b
)
echo [SUCCESS] PostgreSQL is running!

echo.
echo Checking AI models...
python -c "import spacy; spacy.load('en_core_web_md')" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [WARNING] spaCy model 'en_core_web_md' is missing.
    echo Downloading it now - this requires internet connection...
    python -m spacy download en_core_web_md
) else (
    echo [SUCCESS] AI Models are ready.
)

echo.
echo =========================================
echo Server is running! Open your browser at:
echo http://localhost:8000
echo http://127.0.0.1:8000
echo =========================================
echo.

echo Starting the application...
python app\main.py

pause
