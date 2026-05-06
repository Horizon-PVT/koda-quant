@echo off
cd /d "%~dp0"
echo [KODA] Starting dashboard server...
python start_dashboard.py
pause
