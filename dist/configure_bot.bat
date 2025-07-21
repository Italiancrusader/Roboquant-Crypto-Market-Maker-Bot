@echo off
echo ========================================
echo    Roboquant Configuration Wizard
echo    (C) 2025 Roboquant
echo    Professional Trading Solutions
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

echo Launching Configuration Wizard...
echo.

python config_wizard.py

if errorlevel 1 (
    echo.
    echo Configuration wizard encountered an error.
    echo Please check that all files are present.
    pause
    exit /b 1
)

echo.
echo Configuration complete!
echo You can now run start_bot.bat to launch the bot.
echo.
pause
