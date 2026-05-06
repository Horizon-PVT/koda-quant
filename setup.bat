@echo off
echo ==========================================
echo   KODA QUANT V8 - SETUP & LAUNCH
echo ==========================================
echo.

echo [1/3] Installing dependencies...
pip install -r requirements.txt
echo.

echo [2/3] Preflight check...
python -c "from dotenv import load_dotenv; load_dotenv('.env'); import os; k=os.environ.get('QWEN_API_KEY',''); b=os.environ.get('BINANCE_API_KEY',''); print('[OK] QWEN_API_KEY' if k else '[MISSING] QWEN_API_KEY'); print('[OK] BINANCE_API_KEY' if b else '[MISSING] BINANCE_API_KEY (will run in SIMULATED mode)')"
echo.

echo [3/3] Launching...
echo Starting Dashboard on http://localhost:8001 ...
start /B python start_dashboard.py
timeout /t 2 >nul

echo Starting AI Brain (HFT Engine)...
python ai_brain.py
