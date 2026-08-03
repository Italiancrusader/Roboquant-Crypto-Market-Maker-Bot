@echo off
REM One-click launcher for the Hyperliquid A-S market maker (Windows).
cd /d "%~dp0"

echo ========================================
echo   Hyperliquid A-S Market Maker
echo ========================================

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Install it from https://python.org and tick "Add to PATH".
    pause
    exit /b 1
)

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate.bat

python -c "import ccxt, dotenv" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -q -r requirements.txt
)

if not exist config.json (
    copy config.example.json config.json >nul
    echo.
    echo Created config.json from the example ^(testnet mode, ETH/USDC^).
)

if not exist .env (
    copy .env.example .env >nul
    echo.
    echo Created .env — you MUST edit it with your wallet address and API
    echo wallet private key before the bot can trade.
    echo Tip: run "start_bot.bat --dry-run" first; it needs no credentials.
)

echo.
echo Starting bot (Ctrl+C to stop; it cancels its orders on exit)...
echo.
python run_bot.py %*
pause
