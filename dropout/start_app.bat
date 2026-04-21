@echo off
echo ==========================================
echo   Starting Dropout Risk Detection System
echo ==========================================
echo.
echo [STATUS] Activating Virtual Environment...
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found! 
    echo Please make sure you are in the project folder.
    pause
    exit /b
)

echo [STATUS] Starting Django Server...
echo [INFO] Once started, open: http://127.0.0.1:8000/
echo.
.\venv\Scripts\python.exe manage.py runserver
pause
