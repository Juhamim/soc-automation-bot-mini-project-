@echo off
set PYTHONPATH=%cd%
echo Starting SOC Automation Backend (FastAPI)...
start "SOC FastAPI Backend" .\venv\Scripts\python.exe -m uvicorn app.api.main:app --port 8000

echo Starting SOC Celery Worker...
start "SOC Celery Worker" .\venv\Scripts\celery.exe -A app.core.celery_app worker -l info --pool=solo -Q alerts,celery

echo Both services launched in new terminal windows! You can now run the live demo.
