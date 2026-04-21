@echo off
echo ==========================================
echo   AI Model Training Generator
echo ==========================================
echo.
echo [STATUS] Starting Model Training Pipeline...
echo [INFO] This will analyze all 4400+ students and update predictions.
echo.
.\venv\Scripts\python.exe manage.py train_model
echo.
echo [COMPLETE] Model updated and saved in ml_models/
pause
