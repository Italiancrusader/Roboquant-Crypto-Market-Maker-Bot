@echo off
echo ========================================
echo Universal Market Making Bot Launcher
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    echo.
    pause
    exit /b 1
)

REM Check if config.json exists
if not exist config.json (
    echo No configuration found. Launching Configuration Wizard...
    echo.
    python config_wizard.py
    if errorlevel 1 (
        echo Configuration wizard failed to run.
        pause
        exit /b 1
    )
)

REM Check if dependencies are installed
python -c "import ccxt" >nul 2>&1
if errorlevel 1 (
    echo Installing required dependencies...
    echo.
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Failed to install dependencies.
        pause
        exit /b 1
    )
)

echo.
echo Starting Market Making Bot...
echo Press Ctrl+C to stop the bot
echo.
echo ========================================
echo.

python market_maker_bot.py

echo.
echo Bot stopped.
pause
