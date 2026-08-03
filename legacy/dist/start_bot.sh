#!/bin/bash

echo "========================================"
echo "   Roboquant Market Maker Bot"
echo "   © 2025 Roboquant"
echo "   Professional Trading Solutions"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  macOS: brew install python3"
    echo ""
    exit 1
fi

# Check if config.json exists
if [ ! -f "config.json" ]; then
    echo "No configuration found. Launching Configuration Wizard..."
    echo ""
    python3 config_wizard.py
    if [ $? -ne 0 ]; then
        echo "Configuration wizard failed to run."
        exit 1
    fi
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import ccxt" &> /dev/null; then
    echo "Installing required dependencies..."
    echo ""
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Failed to install dependencies."
        exit 1
    fi
fi

echo ""
echo "Starting Roboquant Market Making Bot..."
echo "Press Ctrl+C to stop the bot"
echo ""
echo "========================================"
echo ""

python market_maker_bot.py

echo ""
echo "Bot stopped."
