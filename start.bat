@echo off
echo ========================================
echo STARTING SIH26073 PROTOTYPE
echo ========================================

echo.
echo [1/2] Starting Backend Server (FastAPI)...
start cmd /c "python -m backend.main_api"

echo.
echo [2/2] Starting Frontend Server (Vite)...
cd frontend
start cmd /c "npm run dev"
cd ..

echo.
echo System is launching.
echo Backend API: http://localhost:8000/api
echo Frontend Dashboard: http://localhost:5173
echo.
echo Press any key to run system check...
pause > nul
python system_check.py
